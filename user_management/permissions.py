from rest_framework.permissions import BasePermission

class IsAdminOrReadOnly(BasePermission):
    """
    管理者は全操作許可
    一般ユーザーは読み取りのみ許可
    """
    def has_permission(self, request, view):
        # 安全な HTTP メソッド（GET, HEAD, OPTIONS）は誰でもOK
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # それ以外は管理者のみ許可
        return request.user and request.user.is_staff