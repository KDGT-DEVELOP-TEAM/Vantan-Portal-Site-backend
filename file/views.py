from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from .models import File
from .serializers import FileSerializer
from .permissions import IsAdminOrAuthenticatedReadOnly

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all().order_by('-created_at')
    serializer_class = FileSerializer
    
    # 権限設定
    permission_classes = [IsAdminOrAuthenticatedReadOnly]
    
    # ファイルアップロード処理のためのパーサー
    parser_classes = [MultiPartParser, FormParser]

    # 全一致検索
    filter_backends = [SearchFilter]
    
    # 部分一致検索
    search_fields = ['title']