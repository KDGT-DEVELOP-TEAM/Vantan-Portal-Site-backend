from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter
from django.http import FileResponse
import os

from .models import Timeschedule, TimescheduleImage
from .serializers import TimescheduleSerializer
from permissions import IsAdminOrAuthenticatedReadOnly

class TimescheduleViewSet(viewsets.ModelViewSet):
    # 返す内容を定義（※デフォルトのquerysetはここでは不要になるため削除）
    # queryset = Timeschedule.objects.all().order_by('-created_at')

    # これがファイルの内容？
    serializer_class = TimescheduleSerializer

    # 権限設定
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

    # ファイルアップロード処理のためのパーサー
    parser_classes = [MultiPartParser, FormParser]

    # 全一致検索
    filter_backends = [SearchFilter]

    # 部分一致検索
    search_fields = ['title']

    # ★ フィルタリング処理を追加 ★
    def get_queryset(self):
        # 1. 基本のクエリセットを取得（作成日時降順）
        queryset = Timeschedule.objects.all().order_by('-created_at').prefetch_related('images')
        
        # 2. URLクエリパラメータから 'grade' を取得
        # 例: /api/timeschedule/?grade=2
        grade_param = self.request.query_params.get('grade')
        
        # 3. 'all' でない、かつ、値が存在する場合にフィルタリングを適用
        if grade_param and grade_param.lower() != 'all':
            try:
                # フロントから渡される値は文字列なので、整数に変換
                grade_int = int(grade_param)
                # 学年フィールドでフィルタリング
                queryset = queryset.filter(grade=grade_int)
            except ValueError:
                # 無効な grade 値の場合はフィルタリングをスキップ (安全策)
                # print(f"Warning: Invalid grade parameter received: {grade_param}")
                pass 
        
        return queryset

# ----- 詳細画面からのダウンロード処理 -----
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # ダウンロードリクエストか確認
        download = request.query_params.get('download', 'false').lower() == 'true'

        # 最初の画像だけ取得(1つのTimescheduleに複数の時間割画像を割り振る場合は要修正)
        image_instance = instance.images.first()

        # ダウンロードの処理
        if download and image_instance:
            filename = os.path.basename(image_instance.attached_file.name)
            # FileField からファイルを返す
            response = FileResponse(image_instance.attached_file.open(), as_attachment=True, filename=filename)
            return response

        # 詳細情報を返す
        serializer = self.get_serializer(instance)
        return Response(serializer.data)