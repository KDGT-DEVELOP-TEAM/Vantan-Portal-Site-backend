from rest_framework import serializers
from django.db import transaction
from .models import Gallery, GalleryImage, validate_file_size, ALLOWED_IMAGE_EXTENSIONS
from django.core.validators import FileExtensionValidator


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

    # 単体アップロード用
    image_file = serializers.FileField(
        max_length=100,
        write_only=True,
        required=False,
        validators=[
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
            validate_file_size,
        ]
    )

    class Meta:
        model = Gallery
        fields = [
            "id", "title", "content",
            "images", "image_file",
            "created_at", "updated_at",
            "author", "school",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "author", "school"
        ]

    # -----------------------------
    # create（安全版）
    # -----------------------------
    @transaction.atomic
    def create(self, validated_data):
        image_file = validated_data.pop("image_file", None)
        user = self.context["request"].user

        validated_data["author"] = user
        validated_data["school"] = getattr(user, "school", None)

        gallery = Gallery.objects.create(**validated_data)

        if image_file:
            GalleryImage.objects.create(
                gallery=gallery,
                attached_file=image_file
            )

        return gallery

    # -----------------------------
    # update（Tam 指摘の脆弱性修正）
    # -----------------------------
    @transaction.atomic
    def update(self, instance, validated_data):
        image_file = validated_data.pop("image_file", None)

        # user / school を勝手に変更させない
        validated_data.pop("author", None)
        validated_data.pop("school", None)

        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.save()

        # 新規ファイル追加（上書きはしない：複数画像対応）
        if image_file:
            GalleryImage.objects.create(
                gallery=instance,
                attached_file=image_file
            )

        return instance