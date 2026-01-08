<<<<<<< HEAD
# news/views.py
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend


=======
from rest_framework import viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
>>>>>>> origin/develop
from .models import News, NewsReadStatus
from .serializers import NewsSerializer, NewsListSerializer
from permissions import IsAdminOrAuthenticatedReadOnly
from user_management.models import Role

from django.db.models import Prefetch



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

        qs = (
            News.objects
            .select_related("school")
            .prefetch_related(
                Prefetch(
                    "read_statuses",
                    queryset=NewsReadStatus.objects.filter(user=user),
                    to_attr="user_read_status",
                )
            )
<<<<<<< HEAD
            .order_by("-created_at")
        )

        if user.role == Role.ADMIN:
            return qs

        if getattr(user, "school", None):
            return qs.filter(school=user.school)

        return News.objects.none()
=======
            
        # 詳細表示のレスポンスを返す
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAuthenticatedReadOnly])

    def unread(self, request, pk=None):
        """
        指定された記事を未読状態に戻す（ログインユーザー自身のみ）。
        ※ テスト・検証用途を想定
        """
        
        # 🔒 明示的な認証チェック
        if not request.user.is_authenticated:
            return Response(
                {"detail": "認証が必要です。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        news = self.get_object()

        # ログインユーザー自身の既読情報のみ削除
        NewsReadStatus.objects.filter(
            news=news,
            user=request.user,
        ).delete()

        serializer = self.get_serializer(news)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # プレビュー機能
    @action(detail=False, methods=['post'], url_path='preview', 
        permission_classes=[IsAdminOrAuthenticatedReadOnly])
    def preview(self, request):
        """
        新規投稿用プレビュー
        """
        serializer = self.get_serializer(data=request.data)
        # バリデーションチェック
        serializer.is_valid(raise_exception=True)

        # 記事部分(title,content)のデータ
        preview_data = dict(serializer.validated_data)
        # preview_dataからattachment_filesを削除
        preview_data.pop('attachment_files', None)

        # 画像のデータ
        images = request.FILES.getlist("attachment_files")

        preview_data["images"] = [
            {
                "name": img.name,
                "size": img.size,
                "content_type": img.content_type,
            }
            for img in images
        ]

        return Response(preview_data, status=status.HTTP_200_OK)

>>>>>>> origin/develop
