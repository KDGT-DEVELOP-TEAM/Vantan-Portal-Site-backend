# log_audit/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from django.http import StreamingHttpResponse
from django.utils.encoding import smart_str
import csv

from .models import AuditLog
from .serializers import AuditLogSerializer
from user_management.models import Role


class IsAdminUserForLogs(permissions.BasePermission):
    """
    AuditLog は管理者のみ閲覧可能
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    UC10: AuditLog 一覧・詳細（閲覧専用）
    GET /api/logs/   → 一覧
    GET /api/logs/<id>/ → 詳細
    GET /api/logs/export/ → CSV エクスポート
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserForLogs]

    def get_queryset(self):
        """
        管理者の school の監査ログだけ返す。
        school が None（全校管理者）の場合は全件返す。
        select_related を利用して関連オブジェクトをまとめて取得
        """
        user = self.request.user
        if not user.is_authenticated:
            return AuditLog.objects.none()

        qs = AuditLog.objects.select_related(
            "operator_user", "target_user", "school"
        ).order_by("-created_at")

        if getattr(user, "school", None):
            qs = qs.filter(school=user.school)

        return qs

    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        """
        監査ログを CSV 形式でストリーミングダウンロード
        """
        logs = self.get_queryset()

        # CSV 行を生成するジェネレータ
        def row_generator():
            header = [
                "created_at",
                "action",
                "operator_email",
                "target_email",
                "school_name",
                "action_detail",
                "ip_address",
                "user_agent",
            ]
            yield header
            for log in logs.iterator():  # iterator()でメモリ負荷軽減
                yield [
                    smart_str(log.created_at),
                    smart_str(log.action),
                    smart_str(log.operator_user.email if log.operator_user else ""),
                    smart_str(log.target_user.email if log.target_user else ""),
                    smart_str(log.school.name if log.school else ""),
                    smart_str(log.action_detail),
                    smart_str(log.ip_address),
                    smart_str(log.user_agent),
                ]

        # 1行ずつ CSV 形式に変換するジェネレータ
        def csv_generator():
            for row in row_generator():
                yield ",".join(row) + "\n"

        response = StreamingHttpResponse(
            csv_generator(), content_type="text/csv"
        )
        response["Content-Disposition"] = "attachment; filename=audit_logs.csv"
        return response

