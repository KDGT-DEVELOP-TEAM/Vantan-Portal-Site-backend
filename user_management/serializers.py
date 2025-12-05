from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User
from django.contrib.auth import get_user_model

# --- UC08: ユーザー管理 ---
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    school = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "role",
            "is_active",
            "created_at",
            "school",
        ]
        read_only_fields = ["id", "created_at", "school"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.password = make_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.password = make_password(password)
        instance.save()
        return instance


# ================================
# 一括作成用 CSV アップロード
# ================================
class BulkParentUploadSerializer(serializers.Serializer):
    """
    保護者アカウント一括作成用
    - CSV ファイルを受け取る
    - role は任意（指定がなければ viewer 固定）
    """
    file = serializers.FileField()
    role = serializers.CharField(
        required=False,
        default="viewer",
        help_text="作成するユーザーのロール（デフォルト: viewer）"
    )