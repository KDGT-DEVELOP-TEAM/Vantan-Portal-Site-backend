from django.db import transaction
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from .models import News, NewsAttachment, ALLOWED_FILE_EXTENSIONS, validate_file_size


class NewsAttachmentSerializer(serializers.ModelSerializer):
    attached_file_url = serializers.SerializerMethodField()

    class Meta:
        model = NewsAttachment
        # セキュリティのため、元ファイル名は返さず URL のみ返す
        fields = ["id", "attached_file_url"]
        read_only_fields = ["id", "attached_file_url"]

    def get_attached_file_url(self, obj):
        if not obj.attached_file:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.attached_file.url)
        return obj.attached_file.url


class NewsListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.user_name", read_only=True)
    is_read = serializers.SerializerMethodField(help_text="ログインユーザーの既読状態")

    class Meta:
        model = News
        fields = [
            "id",
            "school",
            "user_name",
            "title",
            "content",
            "importance",
            "created_at",
            "updated_at",
            "is_read",
        ]
        read_only_fields = [
            "id",
            "user_name",
            "created_at",
            "updated_at",
            "is_read",
        ]

    def get_is_read(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.read_statuses.filter(user=request.user).exists()


class NewsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.user_name", read_only=True)

    # 複数添付の一覧（ReadOnly）
    attachments = NewsAttachmentSerializer(many=True, read_only=True)

    # 単一アップロード用のフィールド
    attached_file = serializers.FileField(
        max_length=100000,
        allow_empty_file=False,
        required=False,
        write_only=True,
        validators=[
            FileExtensionValidator(ALLOWED_FILE_EXTENSIONS),
            validate_file_size,
        ],
    )

    is_read = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "id",
            "user",
            "school",
            "user_name",
            "title",
            "content",
            "importance",
            "created_at",
            "updated_at",
            "attachments",
            "attached_file",
            "is_read",
        ]
        read_only_fields = [
            "id",
            "user_name",
            "created_at",
            "updated_at",
            "is_read",
            "user",
            "school",
        ]

    def get_is_read(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.read_statuses.filter(user=request.user).exists()

    # -----------------------------
    # create：user / school を自動設定 + 添付１件
    # -----------------------------
    @transaction.atomic
    def create(self, validated_data):
        uploaded_file = validated_data.pop("attached_file", None)

        user = self.context["request"].user

        validated_data["user"] = user
        validated_data["school"] = getattr(user, "school", None)

        news = News.objects.create(**validated_data)

        if uploaded_file:
            NewsAttachment.objects.create(
                news=news,
                attached_file=uploaded_file,
            )

        return news

    # -----------------------------
    # update：News 本体更新 + 添付ファイル１件だけに置き換え
    # -----------------------------
    @transaction.atomic
    def update(self, instance, validated_data):
        uploaded_file = validated_data.pop("attached_file", None)

        # user / school を勝手に書き換えられないように
        validated_data.pop("user", None)
        validated_data.pop("school", None)

        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.importance = validated_data.get("importance", instance.importance)
        instance.save()

        if uploaded_file:
            # 既存の添付を削除して単一ファイルに制限
            instance.attachments.all().delete()
            NewsAttachment.objects.create(
                news=instance,
                attached_file=uploaded_file,
            )

        return instance