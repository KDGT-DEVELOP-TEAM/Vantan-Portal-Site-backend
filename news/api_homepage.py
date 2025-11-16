from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import News, NewsReadStatus
from django.conf import settings
from django.db.models import OuterRef, Exists, F

class HomePageAPIView(APIView):

    """
    ===============================
    ホームページ用のお知らせ一覧API
    - UC-02 ホームページ
    - UC-02-01 新着お知らせの閲覧
    - UC-02-02 重要お知らせの閲覧
    - UC-02-03 今月のカレンダーの閲覧
    ===============================
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        read_status_subquery = NewsReadStatus.objects.filter(
            news_id=OuterRef('pk'),
            user=user
        )

        # 2. ベースとなるクエリセットを準備し、既読状態をアノテート
        base_qs = News.objects.all().order_by('-updated_at')
        
        # UC-05: ログインユーザーの所属スクールに一致するお知らせのみをフィルタリング
        if user.is_authenticated and hasattr(user, 'school') and user.school:
            base_qs = base_qs.filter(school=user.school)
        else:
            # スクール情報がないユーザーは、NewsViewSetのロジックに倣い空のクエリセットを返すのが安全
            base_qs = News.objects.none()

        # 3. フィルタリングされたクエリセットに is_read フラグをアノテート
        # is_read: 既読レコードが存在するかどうかを真偽値でアノテート
        annotated_qs = base_qs.annotate(
            is_read=Exists(read_status_subquery)
        )

        # UC-02-01: 新着お知らせ（過去3日以内）に修正
        new_news_qs = annotated_qs.filter(
            updated_at__gte=now - timedelta(days=3) # 3日に修正
        ).order_by('-updated_at')

        # UC-02-02: 重要お知らせ（importance=True）に修正
        important_news_qs = annotated_qs.filter(
            importance=True,
        ).order_by('-updated_at')

        # データ整形
        new_news = [
            {
                "id": str(news.id),
                "title": news.title,
                "content": news.content,
                "updated_at": news.updated_at,
                "importance": news.importance,
                "is_read": news.is_read,
            }
            for news in new_news_qs
        ]

        important_news = [
            {
                "id": str(news.id),
                "title": news.title,
                "content": news.content,
                "updated_at": news.updated_at,
                "importance": news.importance,
                "is_read": news.is_read,
            }
            for news in important_news_qs
        ]

        calendar_url = getattr(settings, 'GOOGLE_CALENDAR_EMBED_URL', 'Calendar URL Not Set')

        return Response({
            "new_news": new_news,
            "important_news": important_news,
            "calendar_url": calendar_url, # calendar_urlをレスポンスに含める
        })