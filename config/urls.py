from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT 認証
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # メインアプリ
    path("api/", include("user_management.urls")),

    # HEAD 側: news ルーティング
    path('api/', include([
        path('', include('news.urls')),
    ])),
]