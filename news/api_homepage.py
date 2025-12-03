from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import OuterRef, Exists

from .models import News, NewsReadStatus


class HomePageAPIView(APIView):

    """
    ===============================
    ホームページ用のお知らせ一覧API
    - UC-02-01 新着お知らせの閲覧
    - UC-02-02 重要お知らせの閲覧
    ===============================
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # --- 既読状態を取得するサブクエリ ---
        read_status_subquery = NewsReadStatus.objects.filter(
            news_id=OuterRef('pk'),
            user=user
        )

        # --- ベースクエリを school の正式FK に合わせて制限 ---
        base_qs = News.objects.all().order_by('-updated_at')

        # UC-05: ログインユーザーの所属スクールに一致する記事のみ返す
        if user.is_authenticated and getattr(user, 'school', None):
            base_qs = base_qs.filter(school=user.school)
        else:
            # school が無いユーザーは空レスポンス（権限仕様に合わせる）
            base_qs = News.objects.none()

        # --- 既読状態のアノテーション ---
        annotated_qs = base_qs.annotate(
            is_read=Exists(read_status_subquery)
        )

        # === UC-02-01: 新着お知らせ（3日以内） ===
        new_news_qs = annotated_qs.filter(
            updated_at__gte=now - timedelta(days=3)
        ).order_by('-updated_at')

        # === UC-02-02: 重要お知らせ ===
        important_news_qs = annotated_qs.filter(
            importance=True
        ).order_by('-updated_at')

        # --- JSON 整形 ---
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

        # Google カレンダー埋め込み URL（settings から取得）
        calendar_url = getattr(settings, 'GOOGLE_CALENDAR_EMBED_URL', 'Calendar URL Not Set')

        return Response({
            "new_news": new_news,
            "important_news": important_news,
            "calendar_url": calendar_url,
        })