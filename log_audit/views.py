from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import csv

from .models import AuditLog
from .serializers import AuditLogSerializer


class IsAdminUserForLogs(permissions.BasePermission):
    """
    AuditLog は管理者のみ閲覧可能
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    UC10: AuditLog 一覧・詳細（閲覧専用）
    GET /api/logs/   → 一覧
    GET /api/logs/<id>/ → 詳細
    GET /api/logs/export/ → CSV エクスポート
    """
    
    queryset = AuditLog.objects.all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserForLogs]

    def get_queryset(self):
        """
        管理者の school の監査ログだけ返す。
        school が None（全校管理者）の場合は全件返す。
        """
        user = self.request.user

        if not user.is_authenticated:
            return AuditLog.objects.none()

        if getattr(user, "school", None):
            return AuditLog.objects.filter(school=user.school).order_by("-created_at")

        # school が無い管理者 → 全校対象
        return AuditLog.objects.all().order_by("-created_at")

    # -------------------------------------------------------------
    #  ★ ここが新しく追加した CSV エクスポート機能（UC10-02）
    # -------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        """
        監査ログを CSV 形式でダウンロードするエンドポイント（UC10-02）
        CSV の内容は get_queryset() の結果に準拠
        """
        logs = self.get_queryset()

        # CSV レスポンス準備
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=audit_logs.csv"

        writer = csv.writer(response)
        writer.writerow([
            "created_at",
            "action",
            "operator_email",
            "target_email",
            "school_name",
            "action_detail",
            "ip_address",
            "user_agent",
        ])

        for log in logs:
            writer.writerow([
                log.created_at,
                log.action,
                log.operator_user.email if log.operator_user else "",
                log.target_user.email if log.target_user else "",
                log.school.name if log.school else "",
                log.action_detail,
                log.ip_address,
                log.user_agent,
            ])

        return response