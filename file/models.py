import uuid
from django.db import models
from django.conf import settings 

# def validate_file_size(value):
#     filesize = value.size
#     if filesize > 10 * 1024 * 1024: # 10MB
#         raise ValidationError("添付ファイルのサイズは10MB以下である必要があります。")

def file_image_path(instance, filename):
    # ギャラリー記事のID（UUID）を使用してパスを構築
    return f'user_files/{instance.file.id}/{filename}' # 仮設定


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
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="アップロード日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    

    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        null=False, 
        verbose_name="作成者",
    )

    # 将来的にこうなる
    # school_id = models.ForeignKey(
    #     # School,
    #     on_delete=models.SET_NULL, 
    #     null=True,
    #     blank=True,
    #     related_name='school_file', 
    #     verbose_name='対象スクール'
    # )

    # 仮のスクールID
    school_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        verbose_name="school"
    )


    class Meta:
        ordering = ['-created_at'] 

    def __str__(self):
        return self.title