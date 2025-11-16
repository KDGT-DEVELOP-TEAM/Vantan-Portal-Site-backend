from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # 既存API群
    path("api/", include("user_management.urls")),
    path("api/", include("news.urls")),
    # path("api/gallery/", include("gallery.urls")),
    #  user_management/permissions.py がプロジェクトに存在せず、テストが実行できないためコメントアウト
    # path("api/timeschedule/", include("timeschedule.urls")),
    # path("api/file/", include("file.urls")),
    # 上記三つコード欠損状態のため、一時的にコメントアウト

    # UC10（監査ログ）
    path("api/logs/", include("log_audit.urls")),
]