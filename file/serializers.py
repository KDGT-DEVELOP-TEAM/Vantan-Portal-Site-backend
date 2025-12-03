from rest_framework import serializers
from .models import File
import os

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 10 * 1024 * 1024
# 許可する拡張子
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.png', '.gif', '.svg', '.bmp']


class FileSerializer(serializers.ModelSerializer):
    # 読み取り専用でアップロード者の名前を返す
    user_name = serializers.CharField(source="user.user_name", read_only=True)

    class Meta:
        model = File
        fields = [
            "id",
            "title",
            "attached_file",
            "consent_publication",
            "created_at",
            "updated_at",
            "user",
            "school",
            "user_name",
        ]
        read_only_fields = ["created_at", "updated_at", "user", "school"]

    def validate_attached_file(self, value):
        """
        ファイル形式(E1)とファイルサイズ(E2)のバリデーション
        UC-06-03 (A) でのチェック
        """

        # サイズチェック
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"ファイルサイズが大きすぎます。上限は {MAX_FILE_SIZE // 1024 // 1024}MB です。"
            )

        # 拡張子チェック
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"許可されていないファイル形式です。許可形式: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        return value

    def create(self, validated_data):
        """
        作成者(user) と school を自動設定。
        News / Gallery と揃えた設計。
        """
        request_user = self.context["request"].user

        validated_data["user"] = request_user
        validated_data["school"] = getattr(request_user, "school", None)

        # title が無ければファイル名をそのまま使う
        if not validated_data.get("title"):
            validated_data["title"] = validated_data["attached_file"].name

        return super().create(validated_data)