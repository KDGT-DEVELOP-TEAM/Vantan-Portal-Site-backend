from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet

router = DefaultRouter()
router.register(r'', FileViewSet, basename='file') # /api/files/ にマップ

urlpatterns = [
    # ... 他のURL ...
    path('', include(router.urls)), 
]