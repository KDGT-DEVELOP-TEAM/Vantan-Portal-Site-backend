from rest_framework import serializers
from .models import News, NewsAttachment

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
            request = self.concontent.get('request')
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
    
    # 単一ファイルアップロード用フィールド
    attached_file = serializers.FileField( 
        max_length=100000, 
        allow_empty_file=False,
        required=False,
        help_text="アップロードする添付ファイル (単体)"
    )
    
    is_read = serializers.SerializerMethodField(help_text="ログインユーザーの既読状態")

    class Meta:
        model = News
        fields = [
            'id', 'user', 'school', 'user_name', 'title', 'content', 'importance', 
            'created_at', 'updated_at','attachments', 'attached_file', 'is_read'
        ]
        read_only_fields = ['id', 'user_name', 'created_at', 'updated_at', 'is_read']
        extra_kwargs = {
            'user': {'write_only': True, 'required': False}
        }

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
        uploaded_file = validated_data.pop('attached_file', None)
        
        user = self.context['request'].user
        
        # schoolの自動設定
        validated_data['school'] = user.school 
        # userの自動設定
        validated_data['user'] = user

        # Newsインスタンスを作成
        news = News.objects.create(**validated_data)
        
        # 添付ファイルがあれば、単体で作成
        if uploaded_file:
            NewsAttachment.objects.create(
                news=news, 
                attached_file=uploaded_file
            )
            
        return news

    # update メソッドで既存ファイルを削除し、新しい単一ファイルに置き換え
    def update(self, instance, validated_data):
        uploaded_file = validated_data.pop('attached_file', None)

        # News本体を更新
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.importance = validated_data.get('importance', instance.importance)
        instance.save()
        
        # 新しい添付ファイルがあれば、置き換え
        if uploaded_file:
            # 既存の添付ファイルをすべて削除して、単一ファイルに制限
            instance.attachments.all().delete()
            
            # 新しい単一ファイルを登録
            NewsAttachment.objects.create(
                news=instance, 
                attached_file=uploaded_file
            )
            
        return instance