from rest_framework.permissions import BasePermission, SAFE_METHODS
from user_management.models import Role


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    """
    管理者(role=admin)：全操作可
    認証済みユーザー：読み取りのみ可
    未認証 or school未設定：不可
    """

    def has_permission(self, request, view):
        user = request.user

        # 未ログインは拒否
        if not user or not user.is_authenticated:
            return False

        # school 未設定ユーザーは拒否
        if not getattr(user, "school", None):
            return False

        # 管理者は全許可
        if user.role == Role.ADMIN:
            return True

        # それ以外は読み取りのみ
        return request.method in SAFE_METHODS