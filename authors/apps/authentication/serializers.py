import re
from django.contrib.auth import authenticate

from rest_framework import serializers
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator

from django.contrib.auth.tokens import default_token_generator


from .models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializers registration requests and creates a new user."""

    password = serializers.CharField(
        max_length=128, write_only=True, allow_null=True, allow_blank=True)
    username = serializers.CharField(
        max_length=128, allow_null=True, allow_blank=True)
    email = serializers.EmailField(max_length=128,
                                   allow_null=True, allow_blank=True)
    # Ensure passwords are at least 8 characters long, no longer than 128
    # characters, and can not be read by the client.

    def validate_password(self, data):
        """Check that password is valid"""
        password = data
        if password == '':
            raise serializers.ValidationError('Password is required.')
        elif len(password) < 8:
            raise serializers.ValidationError(
                'Password should be atleats 8 characters.')
            # Validate the password has atleast one number
        elif not re.match(r"^(?=.*[0-9]).*", password):
            raise serializers.ValidationError(
                'A password must contain atleast one number.'
            )
            # Validate password has an uppercase
        elif not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?!.*\s).*", password):
            raise serializers.ValidationError("Password should have an "
                                              "uppercase")
            # Validate the password has a special character
        elif re.match(r"^[a-zA-Z0-9_]*$", password):
            raise serializers.ValidationError(
                "Password should have a special character.")

        return data

    def validate_username(self, data):
        """Check if username pass all the validation parameters."""
        username = data
        if username == '':
            raise serializers.ValidationError('Username is required.')
        elif User.objects.filter(username=username):
            raise serializers.ValidationError('Username is taken.')
        return data

    def validate_email(self, data):
        """Validate email"""
        email = data
        if email == '':
            raise serializers.ValidationError('Email is required.')
        elif User.objects.filter(email=email):
            raise serializers.ValidationError('Email is taken.')

        return data

    # The client should not be able to send a token along with a registration
    # request. Making `token` read-only handles that for us.
    token = serializers.CharField(max_length=128, read_only=True)

    class Meta:
        model = User
        # List all of the fields that could possibly be included in a request
        # or response, including fields specified explicitly above.
        fields = ['email', 'username', 'password', 'token']

    def create(self, validated_data):
        # Use the `create_user` method we wrote earlier to create a new user.
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=128, read_only=True)

    def validate(self, data):
        # The `validate` method is where we make sure that the current
        # instance of `LoginSerializer` has "valid". In the case of logging a
        # user in, this means validating that they've provided an email
        # and password and that this combination matches one of the users in
        # our database.
        email = data.get('email', None)
        password = data.get('password', None)

        # As mentioned above, an email is required. Raise an exception if an
        # email is not provided.
        if email is None:
            raise serializers.ValidationError(
                'An email address is required to log in.'
            )

        # As mentioned above, a password is required. Raise an exception if a
        # password is not provided.
        if password is None:
            raise serializers.ValidationError(
                'A password is required to log in.'
            )

        # The `authenticate` method is provided by Django and handles checking
        # for a user that matches this email/password combination. Notice how
        # we pass `email` as the `username` value. Remember that, in our User
        # model, we set `USERNAME_FIELD` as `email`.
        user = authenticate(username=email, password=password)

        # If no user was found matching this email/password combination then
        # `authenticate` will return `None`. Raise an exception in this case.
        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password was not found.'
            )

        # Django provides a flag on our `User` model called `is_active`. The
        # purpose of this flag to tell us whether the user has been banned
        # or otherwise deactivated. This will almost never be the case, but
        # it is worth checking for. Raise an exception in this case.
        if not user.is_active:
            raise serializers.ValidationError(
                'This user has been deactivated.'
            )

        # The `validate` method should return a dictionary of validated data.
        # This is the data that is passed to the `create` and `update` methods
        # that we will see later on.
        return {
            'email': user.email,
            'username': user.username,
            'token': user.token

        }


class UserSerializer(serializers.ModelSerializer):
    """Handles serialization and deserialization of User objects."""

    # Passwords must be at least 8 characters, but no more than 128
    # characters. These values are the default provided by Django. We could
    # change them, but that would create extra work while introducing no real
    # benefit, so let's just stick with the defaults.
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'password')

        # The `read_only_fields` option is an alternative for explicitly
        # specifying the field with `read_only=True` like we did for password
        # above. The reason we want to use `read_only_fields` here is because
        # we don't need to specify anything else about the field. For the
        # password field, we needed to specify the `min_length` and
        # `max_length` properties too, but that isn't the case for the token
        # field.

    def update(self, instance, validated_data):
        """Performs an update on a User."""

        # Passwords should not be handled with `setattr`, unlike other fields.
        # This is because Django provides a function that handles hashing and
        # salting passwords, which is important for security. What that means
        # here is that we need to remove the password field from the
        # `validated_data` dictionary before iterating over it.
        password = validated_data.pop('password', None)

        if password is not None:
            print("password only")
            # `.set_password()` is the method mentioned above. It handles all
            # of the security stuff that we shouldn't be concerned with.
            instance.set_password(password)

        else:
            print("others")
            for (key, value) in validated_data.items():
                # For the keys remaining in `validated_data`, we will set them on
                # the current `User` instance one at a time.
                setattr(instance, key, value)

        # Finally, after everything has been updated, we must explicitly save
        # the model. It's worth pointing out that `.set_password()` does not
        # save the model.
        instance.save()

        return instance


class EmailSerializer(serializers.Serializer):
    # Ensures that the email is not more than 255 characters long
    email = serializers.EmailField(max_length=255)
    token = serializers.CharField(max_length=225, required=False)
    username = serializers.CharField(
        max_length=225, required=False, read_only=True)
    # Validate that the email

    def validate(self, data):
        user = User.objects.filter(email=data.get('email', None)).first()

        # Check that the user exists
        if user is None:
            raise serializers.ValidationError(
                "User with this email doesn't exist"
            )
        token = default_token_generator.make_token(user)
        return {
            "email": data.get("email"),
            "token": token,
            'username': user.username,
        }


class ResetPasswordSerializer(serializers.Serializer):

    # Ensures that the email is not more than 128 characters long
    # Ensures that the user cannot read the password
    token = serializers.CharField(max_length=225)
    email = serializers.CharField(max_length=225)
    new_password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    def create(self, validated_data):
        user = User.objects.get(email=validated_data.get('email', None))
        return user

    def validate(self, data):
        user = User.objects.filter(email=data.get('email', None)).first()
        is_valid_token = default_token_generator.check_token(
            user, data.get('token'))

        if is_valid_token is not True:
            raise serializers.ValidationError(
                "Invalid token. Please generate another reset password email"
            )

        user.set_password(data.get('new_password', None))
        user.save()

        return data
