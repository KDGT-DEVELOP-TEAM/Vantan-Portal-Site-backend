from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    管理者はフルアクセス (read/write)、その他認証ユーザーは読み取り専用。
    """

    def has_permission(self, request, view):
        # ログインしていることを前提条件とする
        if not request.user.is_authenticated:
            return False
            
        # 読み取り操作は認証された全てのユーザーに許可 (viewerも含む)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 書き込み操作は管理者のみに許可 (admin)
        return request.user.is_authenticated and request.user.role == 'admin'