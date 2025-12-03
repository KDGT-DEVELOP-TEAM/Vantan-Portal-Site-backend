import uuid
from django.db import models
from django.conf import settings
from django.core import validators
from user_management.models import School

class Timeschedule(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID"
    )

    grade = models.IntegerField(
        verbose_name="学年",
        # 学年の上限/下限を定義　とりあえず1~5年生を想定
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(5)
        ]
    )

    title = models.CharField(
        max_length=255,
        verbose_name="時間割表示名"
    )

    content = models.TextField(
        blank=True,
        null=True,
        verbose_name="本文",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="アップロード日時"
    )

    # --- 外部キー ---
    # user_id → user に正式統一（RenameField予定）
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=False,
        verbose_name="作成者",
    )


    # 仮のスクールID（UUID） → school（FK）に正式移行
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeschedules',
        verbose_name="対象スクール"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ----- timescheduleの画像のパスを作る関数 -----
def timeschedule_image_path(instance, filename):
    return f'user_files/{instance.timeschedule.id}/{filename}'


# ----- Timescheduleと時間割画像を繋ぐmodel -----
class TimescheduleImage(models.Model):

    timeschedule = models.ForeignKey(
        Timeschedule,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name="時間割情報"
    )

    attached_file = models.FileField(
        upload_to=timeschedule_image_path,
        verbose_name="時間割画像",
    )