from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.decorators import action
from django.contrib.auth import get_user_model

from .serializers import UserSerializer
from log_audit.models import AuditLog

from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import AllowAny
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .tokens import reset_password_token


# ------------------------------------
# ログアウトAPI（JWTトークン無効化）
# ------------------------------------
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "リフレッシュトークンが必要です。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "無効なリフレッシュトークンです。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"detail": "ログアウトに成功しました"}, status=status.HTTP_200_OK)


# ====================================
# UC08: ユーザー管理 ViewSet
# ====================================
User = get_user_model()

# TODO: 本番ドメインが決まり次第ここを書き換える
FRONTEND_DOMAIN = "https://example.com"  # 仮置き


class UserViewSet(viewsets.ModelViewSet):
    """
    UC08 ユーザー管理
    - 管理者のみ create / update / delete / set_active_status を実行できる
    - 一般ユーザーは閲覧のみ
    - school ベースでの絞り込み対応
    """
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        管理者のみが create / update / delete / set_active_status を実行可能
        """
        if self.action in ["create", "update", "partial_update", "destroy", "set_active_status"]:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    # ------------------------------------
    # school 単位の絞り込み処理
    # ------------------------------------
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # superuser → 全件OK
        if user.is_superuser:
            return qs

        # 所属 school がある場合 → 同じ school のユーザーのみ
        if getattr(user, "school", None):
            return qs.filter(school=user.school)

        return qs.none()

    # ------------------------------------
    # ユーザー作成処理 ＋ 監査ログ
    # ------------------------------------
    def perform_create(self, serializer):
        """
        管理者がユーザーを作成した際に、監査ログ(user_create) を記録する。
        新規作成ユーザーの school は「作成した管理者の school」を自動設定。
        """
        operator = self.request.user
        school = operator.school

        new_user = serializer.save(school=school)

        AuditLog.objects.create(
            action="user_create",
            operator_user=operator,
            target_user=new_user,
            school=school,
            action_detail=f"ユーザー {new_user.email} を作成しました。",
        )

    # ------------------------------------
    # ユーザーの有効 / 無効化
    # ------------------------------------
    @action(detail=True, methods=["patch"], url_path="set_active_status")
    def set_active_status(self, request, pk=None):
        user = self.get_object()
        new_status = request.data.get("is_active")

        if new_status is None:
            return Response({"detail": "is_active フィールドが必要です。"}, status=400)

        user.is_active = new_status
        user.save()

        # ログ保存
        operator = request.user
        school = operator.school

        AuditLog.objects.create(
            action="user_status_change",
            operator_user=operator,
            target_user=user,
            school=school,
            action_detail=f"ユーザー {user.email} のアクティブ状態を {new_status} に変更しました。",
        )

        return Response({
            "message": f"ユーザーの状態を {'有効' if new_status else '無効'} に変更しました。"
        })
    


class AuthUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "school": str(user.school_id) if user.school else None,
            "school_name": user.school.name if user.school else None,
        }
        return Response(data)
    

    # ====================================
# パスワードリセット要求
# ====================================
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        # uid & token 生成
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = reset_password_token.make_token(user)

        # 仮ドメイン。後で実ドメインに差し替え
        reset_url = f"{FRONTEND_DOMAIN}/reset-password/{uid}/{token}"

        # シンプルなテキストメール（まずは動作優先）
        send_mail(
            subject="パスワードリセットのご案内",
            message=f"以下のURLからパスワードの再設定を行ってください。\n\n{reset_url}",
            from_email=None,  # settings.DEFAULT_FROM_EMAIL が使われる
            recipient_list=[email],
        )

        return Response(
            {"detail": "パスワードリセットメールを送信しました。"},
            status=status.HTTP_200_OK,
        )


# ====================================
# トークン検証
# ====================================
class PasswordResetVerifyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        uid = request.query_params.get("uid")
        token = request.query_params.get("token")

        if not uid or not token:
            return Response(
                {"detail": "uid と token が必要です。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid_str = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_str)
        except Exception:
            return Response({"detail": "無効なUIDです。"}, status=status.HTTP_400_BAD_REQUEST)

        if not reset_password_token.check_token(user, token):
            return Response(
                {"detail": "トークンが無効または期限切れです。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "有効なトークンです。"}, status=status.HTTP_200_OK)


# ====================================
# パスワードリセット確定
# ====================================
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid_str = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_str)
        except Exception:
            return Response({"detail": "無効なUIDです。"}, status=status.HTTP_400_BAD_REQUEST)

        if not reset_password_token.check_token(user, token):
            return Response(
                {"detail": "無効なトークンです。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({"detail": "パスワードを変更しました。"}, status=status.HTTP_200_OK)