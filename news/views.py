from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import News, NewsReadStatus
from .serializers import NewsSerializer, NewsListSerializer
from user_management.permissions import IsAdminOrReadOnly


class NewsViewSet(viewsets.ModelViewSet):
    """
    UC-03 お知らせ管理
    - 一般ユーザー：自分の school のお知らせを閲覧
    - 管理者：自 school のお知らせ CRUD
    """

    queryset = (
        News.objects.all()
        .select_related("user", "school")
        .prefetch_related("attachments", "read_statuses")
        .order_by("-created_at")
    )

    # 検索機能 (UC-03-05) の設定
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # 'title'と'content'で検索可能
    search_fields = ["title", "content"]

    # -----------------------------
    # serializer 切り替え
    # -----------------------------
    def get_serializer_class(self):
        # リスト (一覧表示) の場合、軽量な NewsListSerializer を使用
        if self.action == "list":
            return NewsListSerializer

        # 詳細表示、作成、更新、削除、カスタムアクションの場合は標準の NewsSerializer を使用
        return NewsSerializer

    # -----------------------------
    # 権限
    # -----------------------------
    def get_permissions(self):
        # 読み取り系(GET系)も認証必須
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]

        # 書き込み系は管理者のみ
        return [IsAuthenticated(), IsAdminOrReadOnly()]

    # -----------------------------
    # school 絞り込み
    # -----------------------------
    def get_queryset(self):
        """
        UC-05: ログインユーザーの所属スクールに一致するお知らせのみをフィルタリングして表示する。
        デフォルトは作成日時降順。
        """
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        if user.is_superuser:
            return qs

        school = getattr(user, "school", None)
        if not school:
            return qs.none()

        return qs.filter(school=school)

    # create / update は serializer 側で user / school を固定しているので
    # perform_create/perform_update のオーバーライドは不要なはずだが、
    # 明示的にやるなら以下でもOK
    #
    # def perform_create(self, serializer):
    #     user = self.request.user
    #     serializer.save(
    #         user=user,
    #         school=getattr(user, "school", None),
    #     )

    # -----------------------------
    # 既読登録エンドポイント
    # POST /api/news/<pk>/read/
    # -----------------------------
    @action(detail=True, methods=["post"], url_path="read")
    @transaction.atomic
    def mark_as_read(self, request, pk=None):
        news = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "認証が必要です。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        NewsReadStatus.objects.get_or_create(news=news, user=user)
        return Response({"detail": "既読を登録しました。"}, status=status.HTTP_200_OK)