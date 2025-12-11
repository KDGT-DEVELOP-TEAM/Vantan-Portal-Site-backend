from rest_framework.permissions import BasePermission, SAFE_METHODS
from user_management.models import Role


class IsAdminOrReadOnly(BasePermission):
    """
    管理者（role=admin）のみ書き込み許可。
    読み取り(GET, HEAD, OPTIONS)は全員OK。
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == Role.ADMIN


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    """
    管理者 → 全操作可
    認証ユーザー → 読み取りのみ可
    未ログイン → 全不可
    """

    def has_permission(self, request, view):
        user = request.user

        # 管理者は全許可
        if user.is_authenticated and user.role == Role.ADMIN:
            return True

        # 認証済み → 読み取りのみ可
        if user.is_authenticated:
            return request.method in SAFE_METHODS

        # 未ログイン
        return False