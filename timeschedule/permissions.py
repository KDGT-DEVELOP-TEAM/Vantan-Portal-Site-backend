from rest_framework import permissions

class IsAdminOrAuthenticatedReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        # ログイン確認
        if not request.user or not request.user.is_authenticated:
            return False

        # 読み取り操作 (GET, HEAD, OPTIONS) は認証済みなら許可
        if request.method in permissions.SAFE_METHODS:
            return True

        # 書き込み操作 (POST, DELETE) は管理者 (is_staff) のみ許可
        return request.user.is_staff