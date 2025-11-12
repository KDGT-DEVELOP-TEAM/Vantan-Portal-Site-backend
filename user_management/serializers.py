from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from .models import User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("メールアドレスまたはパスワードが正しくありません")
        if not user.is_active:
            raise serializers.ValidationError("このアカウントは無効化されています")
        data["user"] = user
        return data
    

# --- UC08（ユーザー管理用） ---
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "password", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

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