from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrAuthenticatedReadOnly(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        # ログイン確認
        if not user.is_authenticated:
            return False
        
        # school が未設定のユーザーを拒否
        if not hasattr(user, "school") or user.school is None:
            return False
        
        # 管理者 (admin) は全て許可
        if user.role == 'admin':
            return True

        # それ以外も読み取り操作 (GET, HEAD, OPTIONS) なら許可
        if request.method in SAFE_METHODS:
            return True

        return False



# 未ログイン者でも見れる場合(今のところ未実装)
class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        # 管理者 (admin) は全て許可
        if request.user.role == 'admin':
            return True

        # それ以外も読み取り操作 (GET, HEAD, OPTIONS) なら許可
        if request.method in SAFE_METHODS:
            return True

        return False