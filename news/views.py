from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import News, NewsReadStatus
from .serializers import NewsSerializer, NewsListSerializer
from .permissions import IsAdminOrReadOnly


class NewsViewSet(viewsets.ModelViewSet):
    """
    お知らせ (News) のCRUD機能と一覧/検索機能を提供するAPIエンドポイント。
    """
    queryset = (
        News.objects
        .all()
        .select_related("user", "school")
        .prefetch_related("attachments")
        .order_by("-created_at")
    )
    serializer_class = NewsSerializer

    # 権限設定: 認証済みが必須、書き込みは管理者のみ
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    # 検索機能 (UC-03-05) の設定
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # 'title'と'content'で検索可能
    search_fields = ["title", "content"]
    # importanceフラグなどでフィルタリング可能
    filterset_fields = ["importance"]

    # ファイルアップロード処理を許可
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        # リスト (一覧表示) の場合、軽量な NewsListSerializer を使用
        if self.action == "list":
            return NewsListSerializer

        # 詳細表示、作成、更新、削除、カスタムアクションの場合は標準の NewsSerializer を使用
        return NewsSerializer

    def get_queryset(self):
        """
        UC-05: ログインユーザーの所属スクールに一致するお知らせのみをフィルタリングして表示する。
        デフォルトは作成日時降順。
        """
        qs = super().get_queryset()
        user = self.request.user

        # superuser → 全校分を閲覧可能
        if user.is_superuser:
            return qs

        # 認証済みかつ school を持っている場合のみ絞り込みを実施
        if user.is_authenticated and getattr(user, "school", None):
            return qs.filter(school=user.school)

        # それ以外の場合は空のクエリセットを返す（permissionsで弾かれるが安全策として作成）
        return qs.none()

    def perform_create(self, serializer):
        """
        お知らせ作成時、作成者と school を自動紐付けする。
        """
        user = self.request.user
        serializer.save(user=user, school=user.school)

    def retrieve(self, request, *args, **kwargs):
        """
        記事の詳細を取得し、同時に既読フラグを記録する。
        """
        instance = self.get_object()

        # 認証済みユーザーの場合のみ既読を記録
        if request.user.is_authenticated:
            NewsReadStatus.objects.update_or_create(
                news=instance,
                user=request.user,
                defaults={"read_at": timezone.now()},
            )

        # 詳細表示のレスポンスを返す
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def unread(self, request, pk=None):
        """
        指定された記事の既読フラグを削除し、未読状態に戻す。(テスト試行の為必要)
        """
        news = self.get_object()

        # 既読記録を削除
        NewsReadStatus.objects.filter(news=news, user=request.user).delete()

        # 更新後のニュース詳細を返す
        serializer = self.get_serializer(news)
        return Response(serializer.data)