from django.db import models
from django.conf import settings
import uuid


class AuditLog(models.Model):
    """
    UC10: 監査ログモデル

    - log_id: UUID
    - operator_user: 操作したユーザー
    - target_user: 対象ユーザー（いなければ null）
    - action: 操作種別（例: user_create / user_update / user_delete / login / logout / user_status_change）
    - action_detail: 操作内容の詳細（JSON文字列や人間向け説明テキスト）
    - ip_address: 操作者のIPアドレス
    - user_agent: ブラウザなどのユーザーエージェント
    - created_at: 操作日時
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    operator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_as_operator',
        help_text="操作を実行したユーザー",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_as_target',
        help_text="操作対象ユーザー（該当しない場合はNULL）",
    )

    action = models.CharField(max_length=100)
    action_detail = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at}] {self.action} by {self.operator_user} -> {self.target_user}"

    # UC10用の生成メソッド
    @classmethod
    def create_log(cls, *, action, operator_user=None, target_user=None, request=None, action_detail=""):
        """
        各ビューから呼び出してログを1件登録するユーティリティ。
        request からIPアドレス/UAも自動で拾う。
        """
        ip = None
        ua = ""
        if request is not None:
            ip = request.META.get("REMOTE_ADDR")
            ua = request.META.get("HTTP_USER_AGENT", "")

        return cls.objects.create(
            operator_user=operator_user,
            target_user=target_user,
            action=action,
            action_detail=action_detail,
            ip_address=ip,
            user_agent=ua,
        )