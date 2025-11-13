from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import LoginSerializer


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response({
                "message": "ログインに成功しました",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role
                },
                "token": "dummy-token"  # JWTトークン返すよう改修予定
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ログアウトAPI（JWTトークン無効化）
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "リフレッシュトークンが必要です。"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "無効なリフレッシュトークンです。"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "ログアウトに成功しました"}, status=status.HTTP_200_OK)