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
        # サイズチェック
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("ファイルサイズが大きすぎます（10MBまで）")

        # 拡張子チェック
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"許可されていない形式です: {ALLOWED_EXTENSIONS}"
            )

        return value

    def get_attached_file_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.attached_file.url)
        return obj.attached_file.url


class TimescheduleSerializer(serializers.ModelSerializer):

    # GET
    image = TimescheduleImageSerializer(source='images', many=True, read_only=True)

    # POST / PUT
    image_file = serializers.FileField(
        write_only=True,
        required=True
    )

    class Meta:
        model = Timeschedule
        fields = [
            'id', 'grade', 'title', 'content', 'created_at',
            'user', 'school',
            'image', 'image_file',
        ]
        read_only_fields = ['id', 'created_at', 'user', 'school']

    # image_file のバリデーション
    def validate_image_file(self, value):
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("ファイルサイズが大きすぎます（10MBまで）")

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"許可形式は: {', '.join(ALLOWED_EXTENSIONS)} のみです"
            )

        return value

    def create(self, validated_data):
        image_file = validated_data.pop('image_file')

        # Timeschedule を作成
        instance = Timeschedule.objects.create(**validated_data)

        # 添付画像作成
        TimescheduleImage.objects.create(
            timeschedule=instance,
            attached_file=image_file
        )

        return instance