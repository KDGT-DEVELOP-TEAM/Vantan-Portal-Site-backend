import uuid
from django.db import models
from django.conf import settings
from user_management.models import School

def file_image_path(instance, filename):
    """
    添付ファイルの保存パスを構築する。
    ギャラリー・ニュースと同様に user_files/{file_id}/filename の構造に統一。
    """
    return f"user_files/{instance.id}/{filename}"  # 仮設定（統一仕様）

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

    title = models.CharField(
        max_length=255,
        verbose_name="ファイル表示名",
        help_text="一覧に表示される名称"
    )

    attached_file = models.FileField(
        upload_to=file_image_path,
        verbose_name="ファイル"
    )

    consent_publication = models.BooleanField(
        default=False,
        verbose_name="公開許可",
        help_text="True の場合、一般ユーザーも閲覧可"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="アップロード日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    # user_id → user に統一
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=False,
        verbose_name="作成者"
    )

    # ★ School を FK 化（
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