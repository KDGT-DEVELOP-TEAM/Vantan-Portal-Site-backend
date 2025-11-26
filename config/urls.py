from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from news.api_homepage import HomePageAPIView

urlpatterns = [
    path("admin/", admin.site.urls),

    # 認証
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 各アプリ
    path("api/", include("user_management.urls")),
    path("api/", include("timeschedule.urls")),
    path("api/", include("file.urls")),
    path("api/", include("news.urls")),
    path("api/", include("gallery.urls")),

    # UC10（監査ログ）
    path("api/logs/", include("log_audit.urls")),

    # UC02 ホーム画面API
    path("api/homepage/", HomePageAPIView.as_view(), name="homepage"),
]