from rest_framework import serializers
from django.core.validators import FileExtensionValidator
import magic

from .models import News, NewsAttachment, validate_file_size, ALLOWED_FILE_EXTENSIONS

class NewsAttachmentSerializer(serializers.ModelSerializer): 
    
    attached_file_url = serializers.SerializerMethodField()

    class Meta:
        model = NewsAttachment
        # attached_file自体はRead-onlyなので、URLのみ返す
        fields = ['id', 'attached_file_url']
        read_only_fields = ['id', 'attached_file_url']

    def get_attached_file_url(self, obj):
        # 添付ファイルの完全なURLを構築
        if obj.attached_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attached_file.url)
            return obj.attached_file.url
        return None

class NewsListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    is_read = serializers.SerializerMethodField(help_text="ログインユーザーの既読状態")

    class Meta:
        model = News
        fields = [
            'id', 'school', 'user_name', 'title', 'content', 'importance', 
            'created_at', 'updated_at', 'is_read'
            # ★ 'attachments' と 'attached_file' はリストから除外 ★
        ]
        read_only_fields = ['id', 'user_name', 'created_at', 'updated_at', 'is_read']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.read_statuses.filter(user=request.user).exists()

class NewsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    
    # 添付ファイルは読み取り専用でネストして表示
    attachments = NewsAttachmentSerializer(many=True, read_only=True)
    
    # ファイルアップロード用フィールド(複数ファイル対応に変更)
    attachment_files = serializers.ListField(
        child=serializers.FileField(
            # ファイル名 : 255文字まで
            max_length=255, 
            allow_empty_file=False,
            # ファイル名向けのバリデーターを追加
            validators=[
                FileExtensionValidator(ALLOWED_FILE_EXTENSIONS),
                validate_file_size,
            ],
            help_text="アップロードする添付画像ファイル (単体) 10MB以下"
        ),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    # 既存ファイル削除用のフィールド(既存ファイルのIDを収容)
    delete_file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    is_read = serializers.SerializerMethodField(help_text="ログインユーザーの既読状態")

    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'attachments', 
            'attachment_files', 'delete_file_ids', 
            'user', 'user_name', 'school', 
            'importance', 'is_read', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_name', 'created_at', 'updated_at', 'is_read']
        extra_kwargs = {
            'user': {'write_only': True, 'required': False}
        }

    # 画像ファイルのバリデーション
    def validate_attachment_files(self, files):
        # 枚数チェック
        MAX_FILES = 5
        if files and len(files) > MAX_FILES:
            raise serializers.ValidationError(
                f"最大{MAX_FILES}枚までアップロード可能です"
        )

        for file in files:
            # ファイル名の長さチェック(modelに合わせて255文字)
            if len(file.name) > 255:
                raise serializers.ValidationError(f"ファイル名は255文字以内で指定してください(現在 {(len(file.name))}文字)")

            # 拡張子チェック
            ext = file.name.split('.')[-1].lower()
            if ext not in ALLOWED_FILE_EXTENSIONS:
                raise serializers.ValidationError(f"{ext}形式は許可されていません")
            
            # ファイルサイズのチェック
            validate_file_size(file)

            # ファイル形式のチェック
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0) # 読んだ位置をリセット
            if not ( mime_type.startswith("image/") or mime_type == "application/pdf" ):
                raise serializers.ValidationError(f"{file.name} は画像ファイルではありません")
        
        return files

    def get_is_read(self, obj):
        # requestオブジェクトがcontext経由で渡されていることを確認
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
            
        # ログインユーザーがこのニュースを読んだ記録があるかを確認
        return obj.read_statuses.filter(user=request.user).exists()

    # create メソッドで単一ファイルを処理し、user/schoolを自動設定
    def create(self, validated_data):
        # 単一の添付ファイルを分離
        uploaded_file = validated_data.pop('attachment_files', [])
        delete_file_ids = validated_data.pop('delete_file_ids', [])
        
        user = self.context['request'].user
        
        # schoolの自動設定
        validated_data['school'] = user.school 
        # userの自動設定
        validated_data['user'] = user

        # Newsインスタンスを作成
        news = News.objects.create(**validated_data)
        
        # 添付ファイルがあれば、単体で作成
        # if uploaded_file:
        #     NewsAttachment.objects.create(
        #         news=news, 
        #         attached_file=uploaded_file
        #     )
        for file in uploaded_file:
            NewsAttachment.objects.create(
                news=news, 
                attached_file=file)
            
        return news

    # update メソッドで既存ファイルを削除し、新しい単一ファイルに置き換え
    def update(self, instance, validated_data):
        uploaded_file = validated_data.pop('attachment_files', None)
        delete_file_ids = validated_data.pop('delete_file_ids', None)

        # News本体を更新
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.importance = validated_data.get('importance', instance.importance)
        instance.save()
        
        # 注: S3などのストレージのファイル自体を削除するには、シグナルやカスタムロジックが必要です
        # 削除したいファイルがあれば削除
        if delete_file_ids:
            instance.attachments.filter(id__in=delete_file_ids).delete()
        
        # 新しいファイルを登録(既存ファイルは残す)
        if uploaded_file:
            for file in uploaded_file:
                NewsAttachment.objects.create(
                    news=instance, 
                    attached_file=file
                )
            
        return instance