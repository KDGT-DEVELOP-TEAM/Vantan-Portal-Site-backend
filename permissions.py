from rest_framework.permissions import BasePermission, SAFE_METHODS
from user_management.models import Role


class IsAdminOrAuthenticatedReadOnly(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        # 未ログインは拒否
        if not user or not user.is_authenticated:
            return False


        # 管理者は全許可
        if user.role == Role.ADMIN:
            return True

        # それ以外は読み取りのみ
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == Role.ADMIN:
            return True

        # school を持つモデルだけ許可
        if hasattr(obj, "school"):
            return obj.school == user.school

        return False