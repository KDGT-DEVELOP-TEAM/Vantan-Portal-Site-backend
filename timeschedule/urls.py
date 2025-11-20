from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimescheduleViewSet

router = DefaultRouter()
# /api/timeschedule/ にマップ
router.register(r'timeschedule', TimescheduleViewSet, basename='timeschedule') 

urlpatterns = [
    path('', include(router.urls)), 
]