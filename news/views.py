from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import News, NewsReadStatus
from .serializers import NewsSerializer, NewsListSerializer
from permissions import IsAdminOrAuthenticatedReadOnly
from user_management.models import Role


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
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

        if user.role == Role.ADMIN:
            return News.objects.all()

        if getattr(user, "school", None):
            return News.objects.filter(school=user.school)

        return News.objects.none()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        NewsReadStatus.objects.update_or_create(
            news=instance,
            user=request.user,
            defaults={"read_at": timezone.now()},
        )

        return super().retrieve(request, *args, **kwargs)