from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse
import os

from .models import File
from .serializers import FileSerializer
from user_management.models import Role
from user_management.permissions import IsAdminOrAuthenticatedReadOnly


class FileViewSet(viewsets.ModelViewSet):
    """
    UC-06 ファイル管理用 ViewSet
    - UC-06-01 ファイル閲覧
    - UC-06-02 ファイルダウンロード
    - UC-06-03 ファイル投稿(A)
    - UC-06-04 ファイル削除(A)
    - UC-06-05 ファイル検索

    """

    queryset = File.objects.all().select_related("school").order_by("-created_at")
    serializer_class = FileSerializer

    # 権限設定（他アプリと統一）
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

    # ファイルアップロード処理のためのパーサー
    parser_classes = [MultiPartParser, FormParser]

    # 全一致検索
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        # 管理者（superuser の代わりに role=admin）
        if user.role == Role.ADMIN:
            return qs

        # school が設定されている場合のみ絞る
        if getattr(user, "school", None):
            return qs.filter(school=user.school, consent_publication=True)

        # school のないユーザーは何も見せない
        return qs.none()

    # --- POST 制御（ADMIN のみ） ---
    def create(self, request, *args, **kwargs):
        if request.user.role != Role.ADMIN:
            return Response({"detail": "権限がありません(ADMIN 専用)"}, status=403)
        return super().create(request, *args, **kwargs)

    # --- DELETE 制御（ADMIN のみ） ---
    def destroy(self, request, *args, **kwargs):
        if request.user.role != Role.ADMIN:
            return Response({"detail": "権限がありません(ADMIN 専用)"}, status=403)
        return super().destroy(request, *args, **kwargs)

    # --- ファイルダウンロード ---
    def retrieve(self, request, *args, **kwargs):
        """
        詳細画面（UC-06-01）
        download=true の場合、ファイルをダウンロード返却。（UC-06-02）
        """
        instance = self.get_object()
        filename = os.path.basename(instance.attached_file.name)

        if request.query_params.get("download", "false").lower() == "true":
            return FileResponse(
                instance.attached_file.open(),
                as_attachment=True,
                filename=filename,
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # --- update 時の安全対策（serializer 側と整合性保持） ---
    def update(self, request, *args, **kwargs):
        request.data.pop("user", None)
        request.data.pop("school", None)
        return super().update(request, *args, **kwargs)