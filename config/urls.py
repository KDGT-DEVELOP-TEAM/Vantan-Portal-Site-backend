from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # 既存API群
    path("api/", include("user_management.urls")),
    path("api/", include("news.urls")),
    path("api/gallery/", include("gallery.urls")),
    path("api/timeschedule/", include("timeschedule.urls")),
    path("api/file/", include("file.urls")),

    # UC10（監査ログ）
    path("api/logs/", include("log_audit.urls")),
]