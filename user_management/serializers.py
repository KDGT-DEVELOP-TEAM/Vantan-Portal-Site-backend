from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


# --- UC08: ユーザー管理 ---
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    # school は作成した管理者の school を自動付与するので read_only
    school = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "user_name",
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
            # Django 標準推奨メソッドでハッシュ化
            user.set_password(password)
        else:
            # パスワード未設定の場合は unusable にする
            user.set_unusable_password()

        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            # 更新時も set_password を使用
            instance.set_password(password)

        instance.save()
        return instance


# --- パスワードリセット要求 ---
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    # validate_email は何もせず常に成功（存在確認は View 側で対応）
    def validate_email(self, value):
        return value


# --- パスワードリセット確定 ---
class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    re_new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError("パスワードが一致しません。")
        return attrs