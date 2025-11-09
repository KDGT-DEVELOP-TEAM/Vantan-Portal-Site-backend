from rest_framework import serializers
from django.contrib.auth import authenticate
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
    

# 追加ファイル。