from rest_framework.permissions import BasePermission

class IsUserAdmin(BasePermission):
        """
        UC08 ユーザー管理専用 Permission

    一般ユーザー:
    list (一覧)
    retrieve (詳細取得)
        のみ許可

    管理者 (is_staff=True):
    create
    update
    partial_update
    destroy
    set_active_status
    bulk_generate
    bulk_upload
        を含むすべての操作を許可

        ※ HTTPメソッドではなく、ViewSet の action で判定するのが重要
        """

        def has_permission(self, request, view):
            # 読み取り系アクションは全ユーザー許可
            if view.action in ["list", "retrieve"]:
                return True

            # それ以外（作成・変更・削除・一括登録等）は管理者のみ
            return request.user and request.user.is_staff