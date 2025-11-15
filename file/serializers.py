from rest_framework import serializers
from .models import File
import os

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 1000 * 1024 * 1024
# 許可する拡張子
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.png', '.gif', '.svg', '.bmp']

class FileSerializer(serializers.ModelSerializer):
    # 読み取り専用でアップロード者名を表示
    user_id_name = serializers.CharField(source='user_id.user_name', read_only=True)
    
    class Meta:
        model = File
        fields = ['id', 'title', 'attached_file', 'created_at', 'updated_at', 'user_id', 'school_id', 'user_id_name']
        read_only_fields = ['created_at', 'updated_at']

    def validate_attached_file(self, value):
        """ ファイル形式(E1)とファイルサイズ(E2)のバリデーション (UC-09-01) """
        
        # E2: ファイルサイズチェック (10MB)
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(f"ファイルサイズが大きすぎます。上限は {MAX_FILE_SIZE // 1024 // 1024}MB です。")

        # E1: ファイル形式チェック
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(f"許可されていないファイル形式です。許可されている形式: {', '.join(ALLOWED_EXTENSIONS)}")

        return value

    def create(self, validated_data):
        # 投稿者(uploaded_by)をリクエストユーザーに設定
        validated_data['user_id'] = self.context['request'].user
        
        # titleが未設定の場合、アップロードファイル名を設定
        if not validated_data.get('title'):
            validated_data['title'] = validated_data['attached_file'].name
            
        return super().create(validated_data)