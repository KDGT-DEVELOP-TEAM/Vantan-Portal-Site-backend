from rest_framework import serializers
from .models import File
import os

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 10 * 1024 * 1024
# 許可する拡張子
ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp"]


class FileSerializer(serializers.ModelSerializer):
    # 読み取り専用でアップロード者の名前を返す
    user_name = serializers.CharField(source="user.user_name", read_only=True)

    class Meta:
        model = File
        fields = [
            "id",
            "title",
            "attached_file",
            "publication_scope",
            "created_at",
            "updated_at",
            "user",
            "school",
            "user_name",
        ]
        read_only_fields = ["user", "school", "created_at", "updated_at"]

    def validate_attached_file(self, value):
        """拡張子・MIME・ファイルサイズの検証"""

        # --- サイズチェック ---
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("ファイルサイズは10MB以下です")

        # 拡張子チェック
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("許可されていないファイル形式です")

        return value

    def create(self, validated_data):
        user = self.context["request"].user

        if not user.school:
            raise serializers.ValidationError(
                {"detail": "school に所属していないユーザーはファイルを作成できません"}
            )

        validated_data["user"] = user
        validated_data["school"] = user.school

        if not validated_data.get("title"):
            name, _ = os.path.splitext(validated_data["attached_file"].name)
            validated_data["title"] = name

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """ user / school の更新を禁止（安全性向上） """
        validated_data.pop("user", None)
        validated_data.pop("school", None)
        return super().update(instance, validated_data)