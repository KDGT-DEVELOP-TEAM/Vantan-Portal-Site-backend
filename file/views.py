from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse
import os

from .models import File
from .serializers import FileSerializer
from .permissions import IsAdminOrAuthenticatedReadOnly

class FileViewSet(viewsets.ModelViewSet):
    # 返す内容定義
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

    # consent_publicationのチェック
    def  get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_staff:
            return qs

        return qs.filter(consent_publication=True)

    # 詳細画面からのダウンロード処理
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        filename = os.path.basename(instance.attached_file.name)

        # ダウンロードリクエストか確認
        download = request.query_params.get('download', 'false').lower() == 'true'
        if download:
            # FileField からファイルを返す
            response = FileResponse(instance.attached_file.open(), as_attachment=True, filename=filename)
            return response

        # 通常は JSON で詳細情報を返す
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
