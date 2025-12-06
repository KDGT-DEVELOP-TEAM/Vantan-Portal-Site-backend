from rest_framework import serializers
from .models import Gallery, GalleryImage, validate_file_size, ALLOWED_IMAGE_EXTENSIONS
from django.core.validators import FileExtensionValidator

class GalleryImageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryImage
        fields = ['id', 'attached_file', 'file_url']
        read_only_fields = ['id', 'file_url']

    def get_file_url(self, obj):
        # 添付ファイルの完全なURLを構築
        if obj.attached_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attached_file.url)
            return obj.attached_file.url
        return None


class GallerySerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)

    # 単体アップロード（元コメント残す）
    image_file = serializers.FileField(
        max_length=100,
        allow_empty_file=False,
        write_only=True,
        required=False,
        # 修正: ファイル名向けのバリデーターを追加
        validators=[
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
            validate_file_size,
        ],
        help_text="アップロードする添付画像ファイル (単体) 10MB以下"
    )

    class Meta:
        model = Gallery
        fields = [
            'id', 'title', 'content', 'images',
            'image_file',
            'created_at', 'updated_at', 'author',
            'school',  # school 正式対応
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'author', 'school']

    def create(self, validated_data):
        # 単一の添付ファイルを分離
        image_file = validated_data.pop('image_file', None)

        user = self.context['request'].user

        # School の自動設定
        validated_data['school'] = getattr(user, 'school', None)
        validated_data['author'] = user

        gallery_instance = Gallery.objects.create(**validated_data)

        if image_file:
            GalleryImage.objects.create(
                gallery=gallery_instance,
                attached_file=image_file,
            )

        return gallery_instance

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)

        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.save()

        if image_file:
            GalleryImage.objects.create(
                gallery=instance,
                attached_file=image_file,
            )

        return instance