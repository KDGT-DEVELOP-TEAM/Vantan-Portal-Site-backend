from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from news.api_homepage import HomePageAPIView
from user_management.views import AuthUserView

urlpatterns = [
    path("admin/", admin.site.urls),

    # 認証
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/user/", AuthUserView.as_view(), name="auth_user"), 

    # 各アプリ（prefix 付き）
    path("api/users/", include("user_management.urls")),
    path("api/timeschedule/", include("timeschedule.urls")),
    path("api/files/", include("file.urls")),
    path("api/news/", include("news.urls")),
    path("api/gallery/", include("gallery.urls")),

    # UC10（監査ログ）
    path("api/logs/", include("log_audit.urls")),

    # UC02 ホーム画面API
    path("api/homepage/", HomePageAPIView.as_view(), name="homepage"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)