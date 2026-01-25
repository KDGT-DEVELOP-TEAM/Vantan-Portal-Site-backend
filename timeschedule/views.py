from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse, Http404
import os
from .models import TimeSchedule
from .serializers import TimeScheduleSerializer
from permissions import IsAdminOrAuthenticatedReadOnly


class TimeScheduleViewSet(viewsets.ModelViewSet):
    queryset = (
        TimeSchedule.objects
        .all()
        .select_related("school")
        .order_by("-created_at")
    )
    serializer_class = TimeScheduleSerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        user = self.request.user

        # 1. 認証とSchoolの存在チェック（ガード句で先に返す）
        if not user.is_authenticated or not getattr(user, "school", None):
            return TimeSchedule.objects.none()

        qs = TimeSchedule.objects.filter(school=user.school)

        grade = self.request.query_params.get('grade')
        if grade and grade.lower() != 'all':
            if grade.isdigit():
                qs = qs.filter(grade=int(grade))
            else:
                return TimeSchedule.objects.none()

        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            school=getattr(self.request.user, "school", None),
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.query_params.get("download", "").lower() != "true":
            return Response(self.get_serializer(instance).data)

        image = instance.images.first()
        if not image:
            raise Http404("画像が存在しません")

        try:
            return FileResponse(
                image.attached_file.open(),
                as_attachment=True,
                filename=os.path.basename(image.attached_file.name),
            )
        except Exception:
            raise Http404("ファイルを開けませんでした")