
from rest_framework.routers import DefaultRouter
from .views import ArticleAPIView
from django.urls import path, include

from .views import (
    LikesAPIView, DislikesAPIView
)

app_name = "articles"
router = DefaultRouter()
router.register('articles', ArticleAPIView, base_name='articles')

urlpatterns = [
    path('', include(router.urls)),
    path('articles/<slug>/like/', LikesAPIView.as_view(), name="like"),
    path('articles/<slug>/dislike/', DislikesAPIView.as_view(), name="dislike")
]
