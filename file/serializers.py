from rest_framework import serializers
from .models import File
import os

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 10 * 1024 * 1024
# 許可する拡張子
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp']


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
        """拡張子・MIME・ファイルサイズの検証"""

        # --- サイズチェック ---
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"ファイルサイズが大きすぎます。上限は {MAX_FILE_SIZE // 1024 // 1024}MB です。"
            )

        # 拡張子チェック
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"許可されていないファイル形式です。（許可: {', '.join(ALLOWED_EXTENSIONS)}）"
            )

        # --- MIME チェック ---
        if hasattr(value, "content_type"):
            if not value.content_type.startswith(("image/", "application/pdf")):
                raise serializers.ValidationError("画像 または PDF のみアップロードできます")

        return value

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        validated_data["school"] = getattr(user, "school", None)

        # タイトルが無い場合 → ファイル名（拡張子除去）をセット
        if not validated_data.get("title"):
            filename = validated_data["attached_file"].name
            validated_data["title"], _ = os.path.splitext(filename)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """ user / school の更新を禁止（安全性向上） """
        validated_data.pop("user", None)
        validated_data.pop("school", None)
        return super().update(instance, validated_data)