from rest_framework import serializers
from .models import File
import os
import uuid
import re
import magic
from django.conf import settings

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 10 * 1024 * 1024
# 許可する拡張子
ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp"]
# MIMEタイプ対応
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/svg+xml",
    "image/bmp",
]

# タイトルの最大長（DB制約に合わせる）
MAX_TITLE_LENGTH = 100

class FileSerializer(serializers.ModelSerializer):
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

        # --- 拡張子チェック ---
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("許可されていないファイル形式です")

        # --- MIMEタイプチェック ---
        try:
            mime_type = magic.from_buffer(value.read(1024), mime=True)
            value.seek(0)  # ファイルポインタを先頭に戻す
        except Exception:
            raise serializers.ValidationError("ファイルの内容を確認できません")

        if mime_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(f"許可されていない MIMEタイプ: {mime_type}")

        return value

    def create(self, validated_data):
        user = self.context["request"].user

        if not user.school:
            raise serializers.ValidationError(
                {"detail": "school に所属していないユーザーはファイルを作成できません"}
            )

        # UUIDを事前に確定
        validated_data["id"] = str(uuid.uuid4())
        validated_data["user"] = user
        validated_data["school"] = user.school

        # タイトル自動設定かつバリデーションチェック
        if not validated_data.get("title"):
            name, _ = os.path.splitext(validated_data["attached_file"].name)
            # 特殊文字を置換
            name = re.sub(r"[\\/:*?\"<>|]", "_", name)
            # 長さ制限
            validated_data["title"] = name[:MAX_TITLE_LENGTH]

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """ user / school の更新を禁止（安全性向上） """
        validated_data.pop("user", None)
        validated_data.pop("school", None)
        return super().update(instance, validated_data)