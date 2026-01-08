from rest_framework import serializers
from django.core.validators import FileExtensionValidator
import magic

from .models import (
    Gallery,
    GalleryImage,
    validate_file_size,
    ALLOWED_IMAGE_EXTENSIONS,
)


class GalleryImageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GalleryImage
        fields = ["id", "file_url"]
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
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "author",
            "school",
        ]

    # MIME タイプ検証
    def validate_image_files(self, files):
        for file in files:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)

            if not mime_type.startswith("image/"):
                raise serializers.ValidationError(
                    f"{file.name} は画像ファイルではありません"
                )
        return files

    # 枚数制限（create / update 両対応・削除考慮）
    def validate(self, attrs):
        MAX_IMAGES = 5
        new_files = attrs.get("image_files", [])

        # update 時
        if self.instance:
            raw_delete_ids = self.initial_data.get("delete_file_ids", [])
            delete_ids = [int(i) for i in raw_delete_ids]

            current_count = self.instance.images.count()
            total_after_update = (
                current_count
                - len(delete_ids)
                + len(new_files)
            )

            if total_after_update > MAX_IMAGES:
                raise serializers.ValidationError({
                    "image_files": (
                        f"画像の合計が最大{MAX_IMAGES}枚を超えています。"
                        f"(現在{current_count}枚 / 削除{len(delete_ids)}枚 / "
                        f"新規{len(new_files)}枚)"
                    )
                })

        # create 時
        else:
            if len(new_files) > MAX_IMAGES:
                raise serializers.ValidationError({
                    "image_files": f"最大{MAX_IMAGES}枚までアップロードできます"
                })

        return attrs