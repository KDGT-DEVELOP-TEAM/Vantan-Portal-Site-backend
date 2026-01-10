from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    operator_email = serializers.SerializerMethodField()
    target_email = serializers.SerializerMethodField()
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "operator_user",
            "operator_email",
            "target_user",
            "target_email",
            "school",
            "school_name",
            "action",
            "action_detail",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = fields

    def get_operator_email(self, obj):
        if obj.operator_user:
            return obj.operator_user.email
        return None

    def get_target_email(self, obj):
        if obj.target_user:
            return obj.target_user.email
        return None