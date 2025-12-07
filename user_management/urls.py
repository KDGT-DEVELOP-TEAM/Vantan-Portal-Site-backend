from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    LogoutView,
    UserViewSet,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetConfirmView,
)
router = DefaultRouter()
router.register(r'', UserViewSet, basename="user")

urlpatterns = [
    # JWT ログイン
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ログアウト
    path("auth/logout/", LogoutView.as_view(), name="logout"),

    # パスワードリセット系
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password/verify/", PasswordResetVerifyView.as_view(), name="password_verify"),
    path("password/confirm/", PasswordResetConfirmView.as_view(), name="password_confirm"),

    # ユーザー管理
    path("", include(router.urls)),
]