import uuid
from django.db import models
from user_management.models import School
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024: # 10MB
        raise ValidationError("添付ファイルのサイズは10MB以下である必要があります。")

# 許可するファイル拡張子
ALLOWED_IMAGE_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp']

class News(models.Model): 
    # UUIDを主キーとし、editable=Falseで自動生成
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 外部キー: settings.AUTH_USER_MODELを参照 (Usersテーブルに相当)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='news_posts',
        verbose_name='作成者'
    )

    school = models.ForeignKey(
        School, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='school_news', 
        verbose_name='対象スクール'
    )
    
    title = models.CharField(max_length=255, verbose_name='見出し')
    content = models.TextField(blank=True, null=True, verbose_name='本文')
    
    # 新着/重要なお知らせフラグ
    importance = models.BooleanField(default=False, verbose_name='重要なお知らせ')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = 'お知らせ'
        verbose_name_plural = 'お知らせ'
        # 新しい順に表示
        ordering = ['-created_at'] 

    def __str__(self):
        return self.title

def news_image_path(instance, filename):
    # ギャラリー記事のID（UUID）を使用してパスを構築
    return f'user_files/{instance.news.id}/{filename}'

class NewsAttachment(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 外部キー: どのNewsレコードに紐づく (News削除時にファイル情報も削除される)
    news = models.ForeignKey(
        News, 
        on_delete=models.CASCADE, 
        related_name='attachments', # Newsから添付ファイルを参照するための名前
        verbose_name='お知らせ本体'
    )
    
    # ファイルのアップロードとストレージパス管理を担うフィールド
    attached_file = models.FileField(
        upload_to=news_image_path, # ファイル保存先のパス (MEDIA_ROOTからの相対)
        verbose_name='添付ファイル',
        validators=[ # フィードバック対応: バリデーター追加
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
            validate_file_size,
        ],
        help_text="許可ファイル: pdf, jpg, jpeg, png, gif, svg, bmp (10MB以下)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    
    class Meta:
        verbose_name = '添付ファイル'
        verbose_name_plural = '添付ファイル'
    
    def __str__(self):
        # ファイル名が空でなければ、そのファイル名を表示
        return self.attached_file.name if self.attached_file else "ファイルなし"

class NewsReadStatus(models.Model):
    """
    お知らせの既読状態を管理するモデル。
    どのユーザーがどの記事を読んだかを追跡する。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 外部キー: どのNewsレコードに紐づく
    news = models.ForeignKey(
        'News', # Newsモデル
        on_delete=models.CASCADE, 
        related_name='read_statuses', 
        verbose_name='お知らせ本体'
    )
    
    # 外部キー: どのユーザーが読んだか
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='read_news', 
        verbose_name='既読ユーザー'
    )
    
    # 既読日時
    read_at = models.DateTimeField(auto_now_add=True, verbose_name='既読日時')

    class Meta:
        verbose_name = 'お知らせ既読状態'
        verbose_name_plural = 'お知らせ既読状態'
        # 同一ユーザーが同一記事を複数回「既読」として記録しないための制約
        unique_together = ('news', 'user')
        # 既読日時で新しい順にソート
        ordering = ['-read_at']
    
    def __str__(self):
        return f"{self.user.user_name} が {self.news.title} を既読"