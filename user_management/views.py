from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

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

# --- UC08: ユーザー管理 ---
User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "set_active_status"]:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=["patch"], url_path="set_active_status")
    def set_active_status(self, request, pk=None):
        user = self.get_object()
        new_status = request.data.get("is_active")
        if new_status is None:
            return Response({"detail": "is_active フィールドが必要です。"}, status=400)

        user.is_active = new_status
        user.save()

        return Response({"message": f"ユーザーの状態を {'有効' if user.is_active else '無効'} に変更しました。"})