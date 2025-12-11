from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse, Http404
import os

from .models import TimeSchedule
from .serializers import TimeScheduleSerializer
from user_management.models import Role


class TimeScheduleViewSet(viewsets.ModelViewSet):
    """
    UC-07 時間割管理
    - 一般ユーザー：自分の school の時間割を閲覧
    - 管理者：自 school の時間割CRUD
    """
    # 権限設定
    queryset = TimeSchedule.objects.all().select_related("school").order_by("-created_at")
    serializer_class = TimeScheduleSerializer
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

        # 管理者
        if user.role == Role.ADMIN:
            return qs

        # 自校のみ
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

    # ダウンロード処理
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        download = request.query_params.get("download", "").lower() == "true"

        if not download:
            return Response(self.get_serializer(instance).data)

        image = instance.images.first()
        if not image:
            raise Http404("画像が存在しません")

        try:
            filename = os.path.basename(image.attached_file.name)
            return FileResponse(
                image.attached_file.open(),
                as_attachment=True,
                filename=filename,
            )
        except Exception:
            raise Http404("ファイルを開けませんでした")