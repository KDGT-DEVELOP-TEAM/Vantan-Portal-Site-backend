import uuid
from django.db import models
from django.conf import settings 

def file_image_path(instance, filename):
    return f'user_files/{instance.id}/{filename}'


class File(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID"
    )

    title = models.CharField(max_length=255, verbose_name="ファイル表示名")

    attached_file = models.FileField(
        upload_to=file_image_path,
        verbose_name="ファイル",
        null=True,     # migration を通すため
        blank=True,    # migration を通すため
    )

    consent_publication = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="アップロード日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,     # migration を通すため
        blank=True,    # migration を通すため
        verbose_name="作成者",
    )

    school_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name="school"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title