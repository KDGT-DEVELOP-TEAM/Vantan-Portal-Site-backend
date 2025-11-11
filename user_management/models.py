from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)

class Role(models.TextChoices):
    VIEWER = "viewer", "Viewer"
    ADMIN = "admin", "Admin"

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    #実体モデルは未定
    school_id = models.ForeignKey(
        "self",                       # ← 自分自身への仮FK（参照先未確定）
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_users"
    )

    email = models.EmailField(unique=True)
    user_name = models.CharField(max_length=100)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    salt = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email