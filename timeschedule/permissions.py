from rest_framework.permissions import BasePermission, SAFE_METHODS
from user_management.models import Role


class IsAdminOrAuthenticatedReadOnly(BasePermission):

    def has_permission(self, request, view):

        # ロールで管理
        if request.user and getattr(request.user, "role", None) == Role.ADMIN:
            return True

        # 認証済は読み取りだけ許可
        if request.user and request.user.is_authenticated:
            return request.method in SAFE_METHODS

        return False