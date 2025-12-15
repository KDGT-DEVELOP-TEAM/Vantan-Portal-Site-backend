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
            max_length=255,
            validators=[
                FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
                validate_file_size,
            ],
        ),
        write_only=True,
        required=False,
        allow_empty=True,
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

    def validate_image_files(self, files):
        MAX_IMAGES = 5
        if len(files) > MAX_IMAGES:
            raise serializers.ValidationError(f"最大{MAX_IMAGES}枚までです")

        for file in files:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)
            if not mime_type.startswith("image/"):
                raise serializers.ValidationError(f"{file.name} は画像ではありません")

        return files

    def create(self, validated_data):
        image_files = validated_data.pop("image_files", [])
        user = self.context["request"].user

        validated_data["author"] = user
        validated_data["school"] = getattr(user, "school", None)

        gallery = Gallery.objects.create(**validated_data)

        for img in image_files:
            GalleryImage.objects.create(gallery=gallery, attached_file=img)

        return gallery

    def update(self, instance, validated_data):
        image_files = validated_data.pop("image_files", [])
        delete_file_ids = validated_data.pop("delete_file_ids", [])

        # user / school を勝手に変更させない
        validated_data.pop("author", None)
        validated_data.pop("school", None)

        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.save()

        if delete_file_ids:
            instance.images.filter(id__in=delete_file_ids).delete()

        for img in image_files:
            GalleryImage.objects.create(gallery=instance, attached_file=img)

        return instance