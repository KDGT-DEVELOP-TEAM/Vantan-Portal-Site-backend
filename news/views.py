from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import News, NewsReadStatus
from .serializers import NewsSerializer, NewsListSerializer
from permissions import IsAdminOrAuthenticatedReadOnly 
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

class NewsViewSet(viewsets.ModelViewSet):
    """
    お知らせ (News) のCRUD機能と一覧/検索機能を提供するAPIエンドポイント。
    """
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
    # 権限設定: 認証済みが必須、書き込みは管理者のみ
    permission_classes = [IsAdminOrAuthenticatedReadOnly]
    
    # 検索機能 (UC-03-05) の設定
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # 'title'と'content'で検索可能
    search_fields = ['title', 'content'] 
    # importanceフラグなどでフィルタリング可能
    filterset_fields = ['importance'] 

    # ファイルアップロード処理を許可
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        # リスト (一覧表示) の場合、軽量な NewsListSerializer を使用
        if self.action == 'list':
            return NewsListSerializer
        
        # 詳細表示、作成、更新、削除、カスタムアクションの場合は標準の NewsSerializer を使用
        return NewsSerializer

    def get_queryset(self):
        """
        ログインの有無に関わらず、全ての記事を返す。
        デフォルトは作成日時降順。
        """
        queryset = super().get_queryset().select_related('user').prefetch_related('attachments').order_by('-created_at')
        return queryset

    def perform_create(self, serializer):
        """
        お知らせ作成時、シリアライザーの create メソッドに制御を渡す。
        """
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """
        【修正】記事の詳細を取得し、既読フラグを記録後、即座にシリアライズしてレスポンスを返す。
        """
        instance = self.get_object()
        
        # 認証済みユーザーの場合のみ既読を記録
        if request.user.is_authenticated:
            # 既読ステータスの記録/更新
            NewsReadStatus.objects.update_or_create(
                news=instance,
                user=request.user,
                defaults={'read_at': timezone.now()} # 既読日時を更新
            )
            # データベースは更新されたが、in-memoryのinstanceのリレーションキャッシュは古いままの可能性がある。
            # しかし、手動でシリアライザを呼び出すことで、最新のDB状態が反映されることを期待する。
            
        # 詳細表示のレスポンスを返す
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrAuthenticatedReadOnly])
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