from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsViewSet
from .api_homepage import HomePageAPIView

router = DefaultRouter()
router.register(r'', NewsViewSet, basename='news')

urlpatterns = [
    path('', include(router.urls)),
    path('homepage/', HomePageAPIView.as_view(), name='homepage_api'),
]