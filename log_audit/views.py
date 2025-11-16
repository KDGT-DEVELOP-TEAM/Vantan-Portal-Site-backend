from datetime import datetime

from django.utils.dateparse import parse_date
from django.http import HttpResponse

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditLog
from .serializers import AuditLogSerializer


class IsAdminUser(permissions.IsAdminUser):
    pass


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    UC10-01: 監査ログの閲覧API
      - GET /api/audit/logs/
      - 絞り込み条件はクエリパラメータで指定:
        - ?operator_id=<UUID>
        - ?target_id=<UUID>
        - ?action=<文字列>
        - ?date_from=YYYY-MM-DD
        - ?date_to=YYYY-MM-DD
    UC10-02: CSV出力
      - GET /api/audit/logs/export/
    """

    queryset = AuditLog.objects.select_related("operator_user", "target_user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()

        operator_id = self.request.query_params.get("operator_id")
        target_id = self.request.query_params.get("target_id")
        action = self.request.query_params.get("action")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if operator_id:
            qs = qs.filter(operator_user_id=operator_id)
        if target_id:
            qs = qs.filter(target_user_id=target_id)
        if action:
            qs = qs.filter(action=action)

        if date_from:
            d_from = parse_date(date_from)
            if d_from:
                qs = qs.filter(created_at__date__gte=d_from)
        if date_to:
            d_to = parse_date(date_to)
            if d_to:
                qs = qs.filter(created_at__date__lte=d_to)

        return qs.order_by("-created_at")

    # UC10-02: CSV出力
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request, *args, **kwargs):
        logs = self.get_queryset()

        # CSVヘッダ
        header = [
            "log_id",
            "operator_user_id",
            "operator_email",
            "target_user_id",
            "target_email",
            "action",
            "action_detail",
            "ip_address",
            "user_agent",
            "created_at",
        ]

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = datetime.now().strftime("audit_logs_%Y%m%d_%H%M%S.csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'


        def to_csv_row(values):
            escaped = []
            for v in values:
                if v is None:
                    v = ""
                v = str(v).replace('"', '""')
                escaped.append(f'"{v}"')
            return ",".join(escaped) + "\n"

        response.write(to_csv_row(header))

        for log in logs:
            row = [
                log.id,
                log.operator_user_id,
                log.operator_user.email if log.operator_user else "",
                log.target_user_id,
                log.target_user.email if log.target_user else "",
                log.action,
                log.action_detail,
                log.ip_address,
                log.user_agent,
                log.created_at.isoformat(),
            ]
            response.write(to_csv_row(row))

        return response
    

