from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GalleryViewSet

router = DefaultRouter()

# 指示通り r'galleries' に設定
router.register(r'galleries', GalleryViewSet, basename='gallery')

urlpatterns = [
    path('', include(router.urls)),
]