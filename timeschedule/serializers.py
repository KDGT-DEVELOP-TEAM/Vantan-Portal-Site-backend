from rest_framework import serializers
from .models import Timeschedule, TimescheduleImage
import os

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 10 * 1024 * 1024
# 許可する拡張子(pngも入れるなら後で変更)
ALLOWED_EXTENSIONS = ['.pdf']

class TimescheduleImageSerializer(serializers.ModelSerializer):

    attached_file_url = serializers.SerializerMethodField()

    class Meta:
        model = TimescheduleImage
        fields = ['id', 'attached_file', 'attached_file_url']
        read_only_fields = ['id', 'attached_file_url']

    # ファイルの形式/サイズをチェック
    def validate_attached_file(self, value):

        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"ファイルサイズが大きすぎます。上限は {MAX_FILE_SIZE // 1024 // 1024}MB です。"
            )

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"許可されていないファイル形式です。許可されている形式: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        return value

    def get_attached_file_url(self, obj):
        if obj.attached_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attached_file.url)
            return obj.attached_file.url
        return None


class TimescheduleSerializer(serializers.ModelSerializer):

    # ----- GETの時 -----
    image = TimescheduleImageSerializer(
        source='images',
        many=True,
        read_only=True
    )

    # ----- POSTの時 -----
    image_file = serializers.FileField(
        max_length=100,
        # 時間割ファイルの添付必須にする
        required=True,
        write_only=True
    )

    class Meta:
        model = Timeschedule
        fields = [
            'id', 'grade', 'title', 'content', 'created_at',
            'user', 'school',
            'image', 'image_file'
        ]
        read_only_fields = ['id', 'created_at', 'user', 'school']

    # ----- POSTの時 -----
    def create(self, validated_data):
        image_file = validated_data.pop('image_file')
        user = self.context['request'].user

        # Schoolの正式FKを自動設定
        validated_data['school'] = getattr(user, 'school', None)

        # user を自動設定（user_id → user）
        validated_data['user'] = user

        # Timescheduleを作成
        timeschedule_instance = Timeschedule.objects.create(**validated_data)

        # TimescheduleImageを作成
        TimescheduleImage.objects.create(
            timeschedule=timeschedule_instance,
            attached_file=image_file,
        )
        return timeschedule_instance