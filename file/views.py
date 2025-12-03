from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse
import os

from .models import File
from .serializers import FileSerializer
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
        """
        school 単位での分離 ＋ 公開条件
        - superuser → 全件閲覧可
        - staff(管理者) → 自 school のファイル全件閲覧可
        - 一般ユーザー → 自 school かつ consent_publication=True のみ閲覧可
        """
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        # superuser → 全 school
        if user.is_superuser:
            return qs

        # school が設定されている場合のみ、school ベースで絞り込み
        if getattr(user, "school", None):
            qs = qs.filter(school=user.school)

            # 管理者は school 内の全件
            if user.is_staff:
                return qs

            # 一般ユーザーは公開許可のみ
            return qs.filter(consent_publication=True)

        # school のないユーザーは何も見せない
        return qs.none()

    def perform_create(self, serializer):
        """
        ファイル作成時に school を自動紐付け。
        """
        user = self.request.user
        serializer.save(school=getattr(user, "school", None))

    def retrieve(self, request, *args, **kwargs):
        """
        詳細画面（UC-06-01）
        download=true の場合、ファイルをダウンロード返却。（UC-06-02）
        """
        instance = self.get_object()
        filename = os.path.basename(instance.attached_file.name)

        # ?download=true
        download = request.query_params.get("download", "false").lower() == "true"

        if download:
            return FileResponse(
                instance.attached_file.open(),
                as_attachment=True,
                filename=filename,
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)