from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListFileView.as_view(), name='list_file'),
    path('<uuid:pk>/', views.DownloadFileView.as_view(), name='download_file'),
    path('create/', views.UploadFileView.as_view(), name='uploard_file'),
    path('<uuid:pk>/delete/', views.DeleteFileView.as_view(), name='delete_file'),
]