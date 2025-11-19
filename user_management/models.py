from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid


# ========================================================
# School モデル（新規作成）
# ========================================================
class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("スクール名", max_length=255)
    address = models.CharField("住所", max_length=255, blank=True, null=True)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)

    def __str__(self):
        return self.name


# ========================================================
# User Manager
# ========================================================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("メールアドレスは必須です。")
        if password is None:
            raise ValueError("パスワードは必須です。")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Django が salt を含めて保存
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # 権限付与
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        # 矛盾チェック
        if extra_fields.get("is_staff") is not True:
            raise ValueError("スーパーユーザーには is_staff=True が必要です。")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("スーパーユーザーには is_superuser=True が必要です。")

        return self.create_user(email, password, **extra_fields)


# ========================================================
# User モデル
# ========================================================
class Role(models.TextChoices):
    VIEWER = "viewer", "Viewer"
    ADMIN = "admin", "Admin"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # school_id → 外部キーに変更
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="所属スクール"
    )

    email = models.EmailField("メールアドレス", unique=True)
    user_name = models.CharField("ユーザー名", max_length=100, blank=True, null=True)

    role = models.CharField(
        "権限ロール",
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )

    is_active = models.BooleanField("有効フラグ", default=True)
    is_staff = models.BooleanField("管理サイト権限", default=False)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email のみ必須

    objects = UserManager()

    def __str__(self):
        return self.email