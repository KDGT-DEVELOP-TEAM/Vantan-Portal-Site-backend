from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User

# --- UC08: ログイン用 ---
# authenticate を使わない → TokenObtainPairView を使用するため削除済
# LoginSerializer は不要

# --- UC08: ユーザー管理 ---
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "password", "role", "is_active", "is_superuser", "created_at"]
        read_only_fields = ["id", "created_at", "is_superuser"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.password = make_password(password)
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