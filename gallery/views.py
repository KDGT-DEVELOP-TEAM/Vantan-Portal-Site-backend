from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import Gallery, GalleryImage
from .serializers import GallerySerializer
from permissions import IsAdminOrAuthenticatedReadOnly 

# UC-05 ギャラリーViewSet
class GalleryViewSet(viewsets.ModelViewSet):
    """
    ギャラリー記事のCRUDと閲覧を提供するAPIエンドポイント
    """
    serializer_class = GallerySerializer
    
    parser_classes = (MultiPartParser, FormParser)

    # querysetのフィルタリング
    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or not hasattr(user, "school"):
            return Gallery.objects.none()
        return Gallery.objects.filter(school=user.school)
    
    def get_permissions(self):
        """
        CUDは認証済み管理者
        """
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAdminOrAuthenticatedReadOnly()]
        
        # 書き込み操作（POST, PUT, DELETE）の場合
        return [IsAdminOrAuthenticatedReadOnly()]
    
    # 検索機能 (UC-03-05) の設定
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # title(見出しに含まれる)とcontent(本文)で検索可能
    search_fields = ['title', 'content']
    
    def perform_create(self, serializer):
        school_instance = None
        if hasattr(self.request.user, 'school') and self.request.user.school:
            school_instance = self.request.user.school
        serializer.save(
            author=self.request.user,
            school=school_instance
        )

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_pk>[^/.]+)', 
            permission_classes=[IsAdminOrAuthenticatedReadOnly()])
    def delete_image(self, request, pk=None, image_pk=None):
        """特定のギャラリー記事に紐づく画像を個別に削除する"""
        if not image_pk:
            return Response({"detail": "Image ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image_instance = GalleryImage.objects.get(gallery_id=pk, pk=image_pk)
        except GalleryImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # 削除を実行
        image_instance.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


    # プレビュー機能
    @action(detail=False, methods=['post'], url_path='preview', 
        permission_classes=[IsAdminOrAuthenticatedReadOnly()])
    def preview(self, request):
        """
        新規投稿用プレビュー
        """
        serializer = self.get_serializer(data=request.data)
        # バリデーションチェック
        serializer.is_valid(raise_exception=True)

        # 記事部分(title,content)のデータ
        preview_data = dict(serializer.validated_data)
        # 画像のデータ
        images = request.FILES.getlist("image_files")
        preview_data["images"] = [
            {
                "name": img.name,
                "size": img.size,
                "content_type": img.content_type,
            }
            for img in images
        ]

        return Response(preview_data, status=status.HTTP_200_OK)

