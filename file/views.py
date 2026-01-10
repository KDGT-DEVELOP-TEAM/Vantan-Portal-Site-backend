from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse
import os

from .models import File, PublicationScope
from .serializers import FileSerializer
from user_management.models import Role
from permissions import IsAdminOrAuthenticatedReadOnly


class FileViewSet(viewsets.ModelViewSet):
    """
    UC-06 ファイル管理用 ViewSet
    - UC-06-01 ファイル閲覧
    - UC-06-02 ファイルダウンロード
    - UC-06-03 ファイル投稿(A)
    - UC-06-04 ファイル削除(A)
    - UC-06-05 ファイル検索

    """
    serializer_class = FileSerializer

    # 権限設定（他アプリと統一）
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

    # ファイルアップロード処理のためのパーサー
    parser_classes = [MultiPartParser, FormParser]

    # 全一致検索
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        user = self.request.user
        qs = File.objects.select_related("school")

        # 管理者（superuser の代わりに role=admin）
        if user.role == Role.ADMIN:
            return qs
        
        if not getattr(user, "school", None):
            return qs.none()

        return qs.filter(
            school=user.school,
            publication_scope=PublicationScope.PRIVATE
        )

    def retrieve(self, request, *args, **kwargs):
        """
        詳細画面（UC-06-01）
        download=true の場合、ファイルをダウンロード返却。（UC-06-02）
        """
        instance = self.get_object()

        if request.query_params.get("download") == "true":
            self.check_object_permissions(request, instance)
            return FileResponse(
                instance.attached_file.open(),
                as_attachment=True,
                filename=os.path.basename(instance.attached_file.name),
            )

        return Response(self.get_serializer(instance).data)