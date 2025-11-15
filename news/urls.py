from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsViewSet
from .api_homepage import HomePageAPIView

router = DefaultRouter()
# /news/ および /news/{id}/ のURLを生成
# basename='news' はURL名（例: news-list, news-detail）のベース名を設定
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = [
    # config/urls.pyで設定された /api/news/ の後に、routerが生成するURLが続く
    # 結果: /api/news/一覧, /api/news/{id}/詳細 となる
    path('', include(router.urls)), 
    path('homepage/', HomePageAPIView.as_view(), name='homepage_api'),
]