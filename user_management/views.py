from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import LoginSerializer

class AuthAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
             # トークンの生成やセッションの設定など、ログイン後の処理をここに追加
            return Response({
                "message": "Login successful",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role
                },
                "token": "dummy-token"  # 実際にはJWTなどのトークンを返す。TODO: JWTに変更
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # ← これで無効化
        except TokenError:
            return Response({"detail": "invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "logout success"}, status=status.HTTP_200_OK)