import csv
import io
import secrets
import string

from log_audit.models import AuditLog
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, BulkParentUploadSerializer

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
# --- UC08: ユーザー管理 ---
User = get_user_model()


def generate_random_password(length: int = 10) -> str:
    """
    一括作成用のランダムパスワード生成
    - アルファベット大文字 / 小文字 / 数字 を混ぜる
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        管理者のみが create / update / delete / set_active_status / bulk_create_parents を実行可能
        """
        admin_only_actions = [
            "create",
            "update",
            "partial_update",
            "destroy",
            "set_active_status",
            "bulk_create_parents",
        ]

        if self.action in admin_only_actions:
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
    
        # ------------------------------------
    # 保護者アカウントの一括作成
    # ------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk_create_parents")
    def bulk_create_parents(self, request):
        """
        保護者アカウント一括作成エンドポイント
        - CSV ファイルを受け取り、メールアドレスごとに User を作成
        - 初期パスワードをランダム生成
        - 結果は CSV 形式で返却
        """
        serializer = BulkParentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload_file = serializer.validated_data["file"]
        role = serializer.validated_data.get("role", "viewer")

        operator = request.user
        school = getattr(operator, "school", None)

        # 当ブランチにスクールモデルが存在しないためコメントアウト。本番では有効にすること。
        if not school:
            return Response(
                {"detail": "操作ユーザーに school が設定されていません。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # CSV 読み込み準備
        try:
            decoded = upload_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return Response(
                {"detail": "CSV ファイルは UTF-8 でアップロードしてください。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.reader(io.StringIO(decoded))

        # 1行目がヘッダかどうか判定（先頭セルに "email" が含まれていればヘッダ扱い）
        rows = list(reader)
        if not rows:
            return Response(
                {"detail": "CSV にデータがありません。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_index = 0
        first_row = rows[0]
        if first_row and "email" in first_row[0].lower():
            start_index = 1  # 1行目はヘッダとしてスキップ

        # 出力用 CSV をメモリ上で構築
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["email", "initial_password", "status", "message"])

        created_count = 0

        with transaction.atomic():
            for row in rows[start_index:]:
                if not row:
                    continue

                email = row[0].strip()
                if not email:
                    writer.writerow(["", "", "skipped", "空行のためスキップ"])
                    continue

                # メール形式チェック
                try:
                    validate_email(email)
                except ValidationError:
                    writer.writerow([email, "", "invalid", "メール形式が不正です"])
                    continue

                # すでに存在する場合はスキップ
                if User.objects.filter(email=email).exists():
                    writer.writerow([email, "", "exists", "既にユーザーが存在します"])
                    continue

                # ランダムパスワード生成
                password = generate_random_password(10)

                # ユーザー作成
                user = User(
                    email=email,
                    role=role,
                    school=school,
                    is_active=True,
                )
                user.set_password(password)
                user.save()

                # 監査ログ
                AuditLog.objects.create(
                    action="user_create",
                    operator_user=operator,
                    target_user=user,
                    school=school,
                    action_detail=f"一括作成でユーザー {user.email} を作成しました。",
                )

                writer.writerow([email, password, "created", "作成完了"])
                created_count += 1

        output.seek(0)
        csv_data = output.getvalue()

        # DRF Response で CSV を返す
        response = Response(csv_data, status=status.HTTP_200_OK)
        response["Content-Type"] = "text/csv; charset=utf-8"
        response["Content-Disposition"] = 'attachment; filename="bulk_parent_result.csv"'

        return response