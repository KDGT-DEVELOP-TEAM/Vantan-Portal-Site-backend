from rest_framework import viewsets, permissions, status, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

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

    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        """
        CUDは認証済み管理者。
        読み取りは将来の「一部オープン」も見据えて AllowAny + クエリで school 絞り込み。
        （ただし現状は get_queryset 側で user.school がない場合は空を返す）
        """
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]

        # 書き込み操作（POST, PUT, DELETE）の場合
        return [IsAuthenticated(), IsAdminOrReadOnly()]

    # 検索機能 (UC-03-05)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # title(見出しに含まれる)とcontent(本文)で検索可能
    search_fields = ["title", "content"]

    def get_queryset(self):
        """
        School があるユーザーは自分の学校のギャラリーだけ表示。
        superuser は全校分を閲覧可能。
        未ログインまたは school の無いユーザーは空。
        """
        qs = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            if user.is_superuser:
                return qs
            if getattr(user, "school", None):
                return qs.filter(school=user.school)

        return qs.none()

    def perform_create(self, serializer):
        """
        投稿者の school を自動的に紐付ける。
        """
        user = self.request.user
        school_instance = getattr(user, "school", None)
        serializer.save(
            author=user,
            school=school_instance,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path="images/(?P<image_pk>[^/.]+)",
        permission_classes=[IsAuthenticated, IsAdminOrReadOnly],
    )
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