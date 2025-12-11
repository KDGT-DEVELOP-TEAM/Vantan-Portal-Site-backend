import uuid
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from user_management.models import School


# ファイルサイズ 10MB 制限
def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024: # 10MB
        raise ValidationError("添付ファイルのサイズは10MB以下である必要があります。")


# 許可するファイル拡張子
ALLOWED_FILE_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "gif", "svg", "bmp"]


class News(models.Model):
    # UUID を主キー
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 作成者
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="news_posts",
        verbose_name="作成者",
    )

    # 対象スクール
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="school_news",
        verbose_name="対象スクール",
    )

    title = models.CharField(max_length=255, verbose_name="見出し")
    content = models.TextField(blank=True, default="", verbose_name="本文")

    # 重要フラグ
    importance = models.BooleanField(default=False, verbose_name="重要なお知らせ")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "お知らせ"
        verbose_name_plural = "お知らせ"
        # 新しい順に表示
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# 添付ファイルの保存パス（ファイル名は uuid に変換）
def news_file_path(instance, filename):
    ext = filename.split(".")[-1].lower()
    new_name = f"{uuid.uuid4()}.{ext}"
    news_id = instance.news_id or "temp"
    return f"user_files/news/{news_id}/{new_name}"


class NewsAttachment(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 外部キー: どのNewsレコードに紐づく (News削除時にファイル情報も削除される)
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="お知らせ本体",
    )
    
    # ファイルのアップロードとストレージパス管理を担うフィールド
    attached_file = models.FileField(
        upload_to=news_file_path,
        verbose_name="添付ファイル",
        validators=[
            FileExtensionValidator(ALLOWED_FILE_EXTENSIONS),
            validate_file_size,
        ],
        help_text="許可ファイル: pdf, jpg, jpeg, png, gif, svg, bmp (10MB以下)",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        verbose_name = "添付ファイル"
        verbose_name_plural = "添付ファイル"
        ordering = ["-created_at"]

    def __str__(self):
        return self.attached_file.name if self.attached_file else "ファイルなし"


class NewsReadStatus(models.Model):
    """
    お知らせの既読状態を管理するモデル。
    どのユーザーがどの記事を読んだかを追跡する。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 外部キー: どのNewsレコードに紐づく
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name="read_statuses",
        verbose_name="お知らせ本体",
    )
    
    # 外部キー: どのユーザーが読んだか
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="read_news",
        verbose_name="既読ユーザー",
    )

    read_at = models.DateTimeField(auto_now_add=True, verbose_name="既読日時")

    class Meta:
        verbose_name = "お知らせ既読状態"
        verbose_name_plural = "お知らせ既読状態"
        # 同一ユーザーが同一記事を複数回「既読」として記録しないための制約
        unique_together = ("news", "user")
        # 既読日時で新しい順にソート
        ordering = ["-read_at"]

    def __str__(self):
        # user_name フィールド前提
        return f"{self.user.user_name} が {self.news.title} を既読"