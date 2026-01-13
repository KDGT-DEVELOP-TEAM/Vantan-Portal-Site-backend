import csv
import io


from log_audit.models import AuditLog
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.decorators import action
from django.contrib.auth import get_user_model


from rest_framework.permissions import IsAuthenticated
from .permissions import IsUserAdmin

from rest_framework.permissions import AllowAny
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from .serializers import (
    UserSerializer,
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
管理者のみ create / update / delete / set_active_status / bulk 系を実行できる
一般ユーザーは閲覧のみ
school ベースでの絞り込み対応
    """
    serializer_class = UserSerializer
    permission_classes = [IsUserAdmin]

    # ------------------------------------
    # school 単位の絞り込み処理
    # ------------------------------------
    def get_queryset(self):
        user = self.request.user

        qs = (
            User.objects
            .select_related("school")
            .prefetch_related("groups", "user_permissions")
            .order_by("-created_at")
        )

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

        operator = request.user
        school = operator.school

        with transaction.atomic():
            user.is_active = new_status
            user.save()

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
    
    # ====================================
    # 一括生成・一括アップロードのエンドポイント
    # ====================================
    @action(detail=False, methods=["post"], url_path="bulk_generate")
    def bulk_generate(self, request):
        """
        連番ユーザー自動生成
        {
        "count": 20,
        "base_email": "user",
        "domain": "example.com",
        "role": "viewer"
        }
        """
        operator = request.user
        school = operator.school

        if not school:
            return Response(
                {"detail": "スクールに所属していないユーザーは実行できません。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = request.data.get("count")
        base_email = request.data.get("base_email")
        domain = request.data.get("domain")
        role = request.data.get("role")

        # ----------- バリデーション -----------
        try:
            count = int(count)
            if count <= 0 or count > 1000:
                raise ValueError()
        except Exception:
            return Response(
                {"detail": "count は 1〜1000 の整数で指定してください"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not base_email or not domain:
            return Response(
                {"detail": "base_email と domain は必須です"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ["viewer", "admin"]:
            return Response(
                {"detail": "role は viewer または admin のみ指定できます"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        skipped = []
        errors = []

        for i in range(1, count + 1):
            email = f"{base_email}{i}@{domain}"

            # 既存ユーザー
            if User.objects.filter(email=email).exists():
                skipped.append(email)
                continue

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=None,  # unusable_password
                        user_name=base_email + str(i),
                        role=role,
                        school=school,
                    )

                    AuditLog.objects.create(
                        action="user_create",
                        operator_user=operator,
                        target_user=user,
                        school=school,
                        action_detail=f"連番一括生成でユーザー {email} を作成",
                    )

                    created.append({
                        "email": email,
                        "id": str(user.id),
                    })

                try:
                    send_password_reset_email(user)
                except Exception as e:
                    AuditLog.objects.create(
                        action="mail_send_failed",
                        operator_user=operator,
                        target_user=user,
                        school=school,
                        action_detail=f"パスワードリセットメール送信失敗: {str(e)}",
                    )


            except Exception as e:
                errors.append({"email": email, "error": str(e)})

        return Response(
            {
                "created": created,
                "skipped": skipped,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="bulk_upload")
    def bulk_upload(self, request):
        """
        CSV によるユーザー一括登録
        - CSV: email,user_name,permission
        - permission: viewer / admin
        - 作成後はパスワードリセットメールを送信
        """
        operator = request.user
        school = operator.school

        if not school:
            return Response(
                {"detail": "スクールに所属していないユーザーは実行できません。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = request.FILES.get("file")
        if not file:
            return Response(
                {"detail": "CSVファイルが必要です。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded_file = file.read().decode("utf-8-sig")
        except Exception:
            return Response(
                {"detail": "CSVファイルを読み取れませんでした。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(decoded_file))

        required_columns = {"email", "user_name", "permission"}
        if set(reader.fieldnames) != required_columns:
            return Response(
                {
                    "detail": "CSVのヘッダは email,user_name,permission のみを指定してください。",
                    "headers": reader.fieldnames,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        skipped = []
        errors = []

        for idx, row in enumerate(reader, start=2):  # 2行目からデータ
            email = row.get("email", "").strip()
            user_name = row.get("user_name", "").strip()
            permission = row.get("permission", "").strip().lower()

            # ---------- バリデーション ----------
            try:
                validate_email(email)
            except ValidationError:
                errors.append({"row": idx, "email": email, "error": "メール形式が不正です"})
                continue

            if permission not in ["viewer", "admin"]:
                errors.append({
                    "row": idx,
                    "email": email,
                    "error": "permission は viewer または admin のみ指定できます",
                })
                continue

            # ---------- 既存ユーザー ----------
            if User.objects.filter(email=email).exists():
                skipped.append({"row": idx, "email": email, "reason": "既に存在します"})
                continue

            # ---------- 作成 ----------
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=None,  # unusable_password
                        user_name=user_name,
                        role=permission,
                        school=school,
                    )

                    AuditLog.objects.create(
                        action="user_create",
                        operator_user=operator,
                        target_user=user,
                        school=school,
                        action_detail=f"CSV一括登録でユーザー {email} を作成",
                    )

                    created.append({
                        "email": email,
                        "id": str(user.id),
                    })

                    # パスワードリセットメール送信
                try:
                    send_password_reset_email(user)
                except Exception as e:
                    AuditLog.objects.create(
                        action="mail_send_failed",
                        operator_user=operator,
                        target_user=user,
                        school=school,
                        action_detail=f"パスワードリセットメール送信失敗: {str(e)}",
                    )

            except Exception as e:
                errors.append({"row": idx, "email": email, "error": str(e)})

        return Response(
            {
                "created": created,
                "skipped": skipped,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )

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
def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = reset_password_token.make_token(user)
    reset_url = f"{FRONTEND_DOMAIN}/reset-password/{uid}/{token}"

    subject = "パスワードリセットのお知らせ"
    message = f"以下のURLからパスワード再設定を行ってください。\n\n{reset_url}"
    from_email = "no-reply@example.com"

    send_mail(subject, message, from_email, [user.email])

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # 存在している場合だけ内部処理をする
        try:
            user = User.objects.get(email=email)
            try:
                send_password_reset_email(user)
            except Exception as e:
                # メール送信失敗はログに記録
                AuditLog.objects.create(
                    action="mail_send_failed",
                    operator_user=None,
                    target_user=user,
                    school=user.school,
                    action_detail=f"パスワードリセットメール送信失敗: {str(e)}",
                )
        except User.DoesNotExist:
            pass  # 存在しない場合は無視
        
        return Response({"detail": "パスワードリセットメールを送信しました。"})


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
