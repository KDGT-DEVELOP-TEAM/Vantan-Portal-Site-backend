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

class UserMeAPIView(APIView):
    # JWTトークンによる認証を必須とします
    permission_classes = [permissions.IsAuthenticated] 

    def get(self, request):
        # request.user は JWT によって認証されたユーザーオブジェクト
        # UserSerializer を使ってデータをシリアライズします
        serializer = UserSerializer(request.user) 
        
        # is_superuserを含むシリアライズされたユーザーデータをフロントエンドに返します
        return Response(serializer.data)
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated] # get_permissionsで上書きされるため、デフォルト値は省略可

    def get_permissions(self):
        # Admin権限が必須なアクション
        if self.action in ["create", "update", "partial_update", "destroy", "set_active_status"]:
            return [permissions.IsAdminUser()]
        
        # 【修正】それ以外のアクション（list, retrieve）は認証済みであれば許可
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["patch"], url_path="set_active_status")
    def set_active_status(self, request, pk=None):
        user = self.get_object()
        new_status = request.data.get("is_active")
        if new_status is None:
            return Response({"detail": "is_active フィールドが必要です。"}, status=400)

        user.is_active = new_status
        user.save()

        return Response({"message": f"ユーザーの状態を {'有効' if user.is_active else '無効'} に変更しました。"})