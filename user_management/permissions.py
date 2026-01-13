from rest_framework.permissions import BasePermission

class IsUserAdmin(BasePermission):
    """
    管理者は全操作許可
    一般ユーザーは読み取りのみ許可
    """

    def has_permission(self, request, view):
        # 読み取り系アクションは全ユーザー許可
        if view.action in ["list", "retrieve"]:
            return True

        # それ以外（作成・変更・削除・一括登録等）は管理者のみ
        return request.user and request.user.is_staff