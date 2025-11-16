from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GalleryViewSet 

router = DefaultRouter()

# 指示通り r'galleries' に設定し、リソース名（galleries）をURLに含める
router.register(r'galleries', GalleryViewSet, basename='gallery') 

urlpatterns = [
    # 親のurls.pyで /api/gallery/ が設定されているため、path('')でルーターをインクルードするのが正しいと思われます。
    # APIを使う上でルーターのパスを指示通り r'galleries' に修正しました。これにより、リソース名がURLに含まれます。
    # path()はpath('api/', ...)ではなく、path('', ...)のままにしています。
    # 理由: メインのurls.pyで既に /api/gallery/ が設定されているため、アプリ側で再度/api/を設定すると最終URLが /api/gallery/api/galleries/ となり、不正確になるためです。
    # 複数になる場合にメインのurls.pyで設定をするだけでこちら側の/api/を設定しなくて済むのでコードが見やすくなります。
    path('', include(router.urls)),
]