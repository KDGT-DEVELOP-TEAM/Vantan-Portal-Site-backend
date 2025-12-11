from rest_framework import viewsets, permissions, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Gallery, GalleryImage
from .serializers import GallerySerializer
from user_management.permissions import IsAdminOrReadOnly


# UC-05 ギャラリーViewSet
class GalleryViewSet(viewsets.ModelViewSet):
    """
    ギャラリー記事のCRUDと閲覧を提供するAPIエンドポイント
    """
    queryset = (
        Gallery.objects
        .all()
        .select_related("author", "school")
        .prefetch_related("images")
        .order_by("-created_at")
    )
    serializer_class = GallerySerializer

    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["title", "content"]

    # -----------------------------
    # permission 修正版
    # -----------------------------
    def get_permissions(self):
        # GET でも認証必須（未ログインは空返却）
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]

        # POST / PUT / DELETE は admin のみ
        return [IsAuthenticated(), IsAdminOrReadOnly()]

    # -----------------------------
    # school ベースの絞り込み
    # -----------------------------
    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Gallery.objects.none()

        if user.is_superuser:
            return super().get_queryset()

        # school が無いユーザは空
        if not getattr(user, "school", None):
            return Gallery.objects.none()

        return super().get_queryset().filter(school=user.school)

    # -----------------------------
    # 画像個別削除（安全版）
    # -----------------------------
    @action(
        detail=True,
        methods=["delete"],
        url_path="images/(?P<image_pk>[^/.]+)",
        permission_classes=[IsAuthenticated, IsAdminOrReadOnly],
    )
    def delete_image(self, request, pk=None, image_pk=None):
        try:
            image_instance = GalleryImage.objects.get(gallery_id=pk, pk=image_pk)
        except GalleryImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)

        # 削除を実行
        image_instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)