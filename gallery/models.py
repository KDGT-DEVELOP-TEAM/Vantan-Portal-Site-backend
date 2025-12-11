import uuid
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from user_management.models import School

# ファイルサイズバリデーター (10MB制限)
def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024:
        raise ValidationError("添付ファイルのサイズは10MB以下である必要があります。")

# 許可するファイル拡張子
ALLOWED_IMAGE_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp']

# -----------------------------
# アップロードパス（UUID化・安全版）
# -----------------------------
def gallery_image_path(instance, filename):
    ext = filename.split('.')[-1]
    new_name = f"{uuid.uuid4()}.{ext}"

    # instance.gallery_id は保存前 None になる可能性があるため安全策
    gallery_id = instance.gallery_id or "temp"

    return f"user_files/gallery/{gallery_id}/{new_name}"


# -----------------------------
# ギャラリーメインモデル
# -----------------------------
class Gallery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gallery_items',
    )

    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")  # null=True は非推奨 → default="" に統一

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=False,
        related_name="created_gallery",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# -----------------------------
# 添付画像モデル
# -----------------------------
class GalleryImage(models.Model):
    gallery = models.ForeignKey(
        Gallery,
        related_name='images',
        on_delete=models.CASCADE,
    )

    attached_file = models.FileField(
        upload_to=gallery_image_path,
        validators=[
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
            validate_file_size,
        ],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.gallery.title} - {self.attached_file.name}"