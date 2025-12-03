from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    管理者のみ書き込み許可。
    読み取り(GET, HEAD, OPTIONS)は全員OK。
    """

    def has_permission(self, request, view):
        # 読み取りだけなら誰でもOK（未ログイン含む）
        if request.method in SAFE_METHODS:
            return True
        # 書き込みは staff のみ
        return bool(request.user and request.user.is_staff)


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    """
    管理者 → 全操作可
    認証ユーザー → 読み取りのみ可
    未ログイン → 全不可
    """

    def has_permission(self, request, view):
        # 管理者は全許可
        if request.user and request.user.is_staff:
            return True

        # 認証済みなら読み取りのみ許可
        if request.user and request.user.is_authenticated:
            return request.method in SAFE_METHODS

        # 未ログインは全拒否
        return False