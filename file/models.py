import uuid
from django.db import models
from django.conf import settings
from user_management.models import School

def file_image_path(instance, filename):
    """
    添付ファイル保存パス
    必ず instance.id が存在するよう保険をかける
    """
    if not instance.id:
        instance.id = uuid.uuid4()

    return f"user_files/file/{instance.id}/{filename}"


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
        verbose_name="ID"
    )

    title = models.CharField(max_length=255, verbose_name="ファイル表示名")

    attached_file = models.FileField(
        upload_to=file_image_path,
        verbose_name="ファイル"
    )

    consent_publication = models.BooleanField(
        default=False,
        verbose_name="公開許可"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="作成者"
    )

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        verbose_name="対象スクール"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title