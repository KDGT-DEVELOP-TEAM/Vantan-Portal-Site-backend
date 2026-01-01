from rest_framework import serializers
import magic

from .models import (
    News,
    NewsAttachment,
    validate_file_size,
    ALLOWED_FILE_EXTENSIONS,
)


class NewsAttachmentSerializer(serializers.ModelSerializer):
    attached_file_url = serializers.SerializerMethodField()

    class Meta:
        model = NewsAttachment
        # attached_file 自体は返さず、URL のみを返却
        fields = ['id', 'attached_file_url']
        read_only_fields = ['id', 'attached_file_url']

    def get_attached_file_url(self, obj):
        if not obj.attached_file:
            return None

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.attached_file.url)
        return obj.attached_file.url


class NewsListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    is_read = serializers.SerializerMethodField(help_text="ログインユーザーの既読状態")

    class Meta:
        model = News
        fields = [
            'id',
            'school',
            'user_name',
            'title',
            'content',
            'importance',
            'created_at',
            'updated_at',
            'is_read',
        ]
        read_only_fields = [
            'id',
            'user_name',
            'created_at',
            'updated_at',
            'is_read',
        ]

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.read_statuses.filter(user=request.user).exists()


class NewsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)

    # 添付ファイル（読み取り専用）
    attachments = NewsAttachmentSerializer(many=True, read_only=True)

    # 新規アップロード用（複数ファイル対応）
    attachment_files = serializers.ListField(
        child=serializers.FileField(
            max_length=255,
            allow_empty_file=False,
            help_text="アップロードする添付ファイル（画像 / PDF、10MB以下・最大5件）",
        ),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    # 既存添付ファイル削除用（ID指定）
    delete_file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    is_read = serializers.SerializerMethodField(help_text="ログインユーザーの既読状態")

    class Meta:
        model = News
        fields = [
            'id',
            'title',
            'content',
            'attachments',
            'attachment_files',
            'delete_file_ids',
            'user',
            'user_name',
            'school',
            'importance',
            'is_read',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user_name',
            'created_at',
            'updated_at',
            'is_read',
        ]
        extra_kwargs = {
            'user': {'write_only': True, 'required': False},
        }

    # 添付ファイルのバリデーションを Serializer に集約
    def validate_attachment_files(self, files):
        MAX_FILES = 5

        # 枚数チェック
        if files and len(files) > MAX_FILES:
            raise serializers.ValidationError(
                f"最大{MAX_FILES}件までアップロード可能です"
            )

        for file in files:
            # ファイル名長チェック
            if len(file.name) > 255:
                raise serializers.ValidationError(
                    f"ファイル名は255文字以内で指定してください（現在 {len(file.name)}文字）"
                )

            # 拡張子チェック
            ext = file.name.split('.')[-1].lower()
            if ext not in ALLOWED_FILE_EXTENSIONS:
                raise serializers.ValidationError(
                    f"{ext}形式は許可されていません"
                )

            # ファイルサイズチェック
            validate_file_size(file)

            # MIMEタイプチェック
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)
            if not (
                mime_type.startswith("image/")
                or mime_type == "application/pdf"
            ):
                raise serializers.ValidationError(
                    f"{file.name} は許可されていないファイル形式です"
                )

        return files

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.read_statuses.filter(user=request.user).exists()

    # 新規作成（複数添付ファイル対応・user / school 自動設定）
    def create(self, validated_data):
        uploaded_files = validated_data.pop('attachment_files', [])
        validated_data.pop('delete_file_ids', None)

        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['school'] = user.school

        news = News.objects.create(**validated_data)

        # 添付ファイルを複数登録
        for file in uploaded_files:
            NewsAttachment.objects.create(
                news=news,
                attached_file=file,
            )

        return news

    # 更新
    def update(self, instance, validated_data):
        uploaded_files = validated_data.pop('attachment_files', [])
        delete_file_ids = validated_data.pop('delete_file_ids', [])

        # News本体の更新
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.importance = validated_data.get('importance', instance.importance)
        instance.save()

        # 添付ファイル削除（Newsに紐づくもののみ）
        if delete_file_ids:
            instance.attachments.filter(id__in=delete_file_ids).delete()

        # 新規添付ファイル追加（既存ファイルは保持）
        for file in uploaded_files:
            NewsAttachment.objects.create(
                news=instance,
                attached_file=file,
            )

        return instance