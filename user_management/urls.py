from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import LoginView, LogoutView

urlpatterns = [
    # カスタムログインAPI
    path("auth/login/custom/", LoginView.as_view(), name="custom_login"),

    # JWTログイン関連
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),  # JWTログイン
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),  # トークン更新

    # ログアウト
    path("auth/logout/", LogoutView.as_view(), name="logout"),
]