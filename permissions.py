from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        # ログイン確認
        if not request.user.is_authenticated:
            return False

        # 読み取り操作 (GET, HEAD, OPTIONS) なら全て許可
        if request.method in SAFE_METHODS:
            return True

        # 書き込み操作 (POST, DELETE) は管理者 (is_staff) のみ許可
        return request.user.is_staff