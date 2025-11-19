import uuid
from django.db import models
from django.conf import settings 
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

# ファイルサイズバリデーター (10MB制限)
def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024: # 10MB
        raise ValidationError("添付ファイルのサイズは10MB以下である必要があります。")

# 許可するファイル拡張子
ALLOWED_IMAGE_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp']

class Gallery(models.Model):
    # 修正: idをUUIDに変更し、PKに設定
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False, 
        verbose_name="ID"
    )

    school = models.ForeignKey(
    "user_management.School",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='school_gallery',
    verbose_name='対象スクール'
)
    
    title = models.CharField(
        max_length=255, # フィードバック対応: 255文字
        verbose_name="見出し", 
        help_text="ギャラリー記事のタイトル"
    )
    content = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="本文",
        help_text="ギャラリー記事の本文 (任意)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        # 修正: PROTECTに変更し、null=Falseとの矛盾を解消
        on_delete=models.PROTECT, 
        null=False, # nullを許可しない設定を維持
        verbose_name="作成者"
    )

    class Meta:
        verbose_name = "ギャラリー記事"
        verbose_name_plural = "ギャラリー記事"
        # 新しい順に表示
        ordering = ['-created_at'] 

    def __str__(self):
        return self.title

def gallery_image_path(instance, filename):
    # ギャラリー記事のID（UUID）を使用してパスを構築
    return f'user_files/{instance.gallery.id}/{filename}' # 仮設定

class GalleryImage(models.Model):
    gallery = models.ForeignKey(
        Gallery, 
        related_name='images', 
        on_delete=models.CASCADE, 
        verbose_name="ギャラリー記事"
    )
    attached_file = models.FileField(
        upload_to=gallery_image_path, 
        verbose_name="添付画像",
        validators=[ # フィードバック対応: バリデーター追加
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
            validate_file_size,
        ],
        help_text="許可ファイル: pdf, jpg, jpeg, png, gif, svg, bmp (10MB以下)"
    )
    
    class Meta:
        verbose_name = "ギャラリー画像"
        verbose_name_plural = "ギャラリー画像"

    def __str__(self):
        return f"{self.gallery.title} - {self.attached_file.name}"