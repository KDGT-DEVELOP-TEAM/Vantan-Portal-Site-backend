from rest_framework import serializers
from django.core.validators import FileExtensionValidator
import magic

from .models import Gallery, GalleryImage, validate_file_size, ALLOWED_IMAGE_EXTENSIONS


class GalleryImageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryImage
        fields = ["id", "attached_file", "file_url"]
        read_only_fields = ["id", "file_url"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.attached_file.url)
        return obj.attached_file.url


class GallerySerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)

    image_files = serializers.ListField(
        child=serializers.FileField(
            validators=[
                FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
                validate_file_size,
            ]
        ),
        write_only=True,
        required=False,
    )

    delete_file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Gallery
        fields = [
            "id",
            "title",
            "content",
            "images",
            "image_files",
            "delete_file_ids",
            "created_at",
            "updated_at",
            "author",
            "school",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "author", "school"]

    # MIME / 拡張子チェック専用
    def validate_image_files(self, files):
        for file in files:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)
            if not (mime_type.startswith("image/") or mime_type == "application/pdf"):
                raise serializers.ValidationError(
                    f"{file.name} は許可されていない形式です"
                )
        return files

    # 枚数チェック（create / update 両対応）
    def validate(self, attrs):
        MAX_IMAGES = 5
        new_files = attrs.get("image_files", [])

        if self.instance:
            existing_count = self.instance.images.count()
        else:
            existing_count = 0

        if existing_count + len(new_files) > MAX_IMAGES:
            raise serializers.ValidationError(
                f"画像は最大{MAX_IMAGES}枚までです"
            )

        return attrs