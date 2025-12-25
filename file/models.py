import uuid
from django.db import models
from django.conf import settings
from user_management.models import School


# =============================
# 公開範囲（Enum）
# =============================
class PublicationScope(models.TextChoices):
    PRIVATE = "private", "非公開（自校のみ）"
    ADMIN_ONLY = "admin", "管理者のみ横断閲覧"


# =============================
# ファイル保存パス
# =============================
def file_upload_path(instance, filename):
    """
    ファイル保存パス
    school / file_id 単位で管理する
    """
    return (
        f"user_files/"
        f"school_{instance.school_id}/"
        f"file_{instance.id}/"
        f"{filename}"
    )


# =============================
# ファイルモデル
# =============================
class File(models.Model):
    """
    UC-06 ファイル管理モデル
    - UC-06-01: ファイル閲覧
    - UC-06-02: ファイルダウンロード
    - UC-06-03: ファイル投稿(A)
    - UC-06-04: ファイル削除(A)
    - UC-06-05: ファイル検索
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="ファイル表示名",
    )

    attached_file = models.FileField(
        upload_to=file_upload_path,
        max_length=255,
        verbose_name="ファイル",
    )

    publication_scope = models.CharField(
        max_length=20,
        choices=PublicationScope.choices,
        default=PublicationScope.PRIVATE,
        verbose_name="公開範囲",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_files",
        verbose_name="作成者",
    )

    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="files",
        verbose_name="対象スクール",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="作成日時",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新日時",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title