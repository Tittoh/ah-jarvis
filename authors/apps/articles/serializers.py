from rest_framework import serializers

from rest_framework.views import APIView

from authors.apps.profiles.serializers import ProfileSerializer

from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer to map the Model format to Json format
    """
    title = serializers.CharField(required=True)
    body = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    slug = serializers.SlugField(required=False)
    image_url = serializers.URLField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    author = ProfileSerializer(read_only=True)
    
    class Meta:
        model = Article
        fields = ['title', 'slug', 'body',
                  'description', 'image_url', 'created_at', 'updated_at', 'author']

    def create(self, validated_data):
        return Article.objects.create(**validated_data)

    def validate(self, data):
        # The `validate` method is used to validate the title,
        # description and body
        title = data.get('title', None)
        description = data.get('description', None)

        return data
