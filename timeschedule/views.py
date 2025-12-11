from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse
import os

from .models import Timeschedule
from .serializers import TimescheduleSerializer
from .permissions import IsAdminOrAuthenticatedReadOnly


class TimescheduleViewSet(viewsets.ModelViewSet):
    """
    UC-07 時間割管理
    - 一般ユーザー：自分の school の時間割を閲覧
    - 管理者：自 school の時間割CRUD
    """

    queryset = Timeschedule.objects.all().select_related("school").order_by("-created_at")
    serializer_class = TimescheduleSerializer

    # 権限設定
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

    # ファイルアップロード処理のためのパーサー
    parser_classes = [MultiPartParser, FormParser]

    # 全一致検索
    filter_backends = [SearchFilter]
    # 部分一致検索
    search_fields = ["title"]

    def get_queryset(self):
        """
        School があるユーザーは自分の学校の時間割だけ表示
        superuser は全 school を閲覧可
        """
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        if user.is_superuser:
            return qs

        if getattr(user, "school", None):
            return qs.filter(school=user.school)

        return qs.none()

    def perform_create(self, serializer):
        """
        user と school を正式にここで設定する
        """
        user = self.request.user
        serializer.save(
            user=user,
            school=getattr(user, "school", None)
        )

    # ----- ダウンロード処理 -----
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        download = request.query_params.get("download", "false").lower() == "true"

        image_instance = instance.images.first()

        if download and image_instance:
            filename = os.path.basename(image_instance.attached_file.name)
            return FileResponse(
                image_instance.attached_file.open(),
                as_attachment=True,
                filename=filename
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)