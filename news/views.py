# news/views.py
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction

from .models import News, NewsReadStatus
from .serializers import NewsSerializer, NewsListSerializer
from permissions import IsAdminOrAuthenticatedReadOnly
from user_management.models import Role


class NewsViewSet(viewsets.ModelViewSet):
    """
    ニュース一覧・詳細
    GET /api/news/   → 一覧
    GET /api/news/<id>/ → 詳細
    """
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["title", "content"]

    def get_serializer_class(self):
        if self.action == "list":
            return NewsListSerializer
        return NewsSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return News.objects.none()

        # select_relatedでschool情報をまとめて取得
        qs = News.objects.select_related("school").order_by("-created_at")

        if user.role == Role.ADMIN:
            return qs

        if getattr(user, "school", None):
            return qs.filter(school=user.school)

        return News.objects.none()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # 複数アクセス時も安全に NewsReadStatus 更新
        with transaction.atomic():
            NewsReadStatus.objects.update_or_create(
                news=instance,
                user=request.user,
                defaults={"read_at": timezone.now()},
            )

        return super().retrieve(request, *args, **kwargs)
