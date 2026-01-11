from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import Gallery, GalleryImage
from .serializers import GallerySerializer
from permissions import IsAdminOrAuthenticatedReadOnly


class GalleryViewSet(viewsets.ModelViewSet):
    serializer_class = GallerySerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["title", "content"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not getattr(user, "school", None):
            return Gallery.objects.none()

        return (
            Gallery.objects.filter(school=user.school)
            .select_related("author", "school")
            .prefetch_related("images")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        user = self.request.user
        image_files = serializer.validated_data.pop("image_files", [])

        with transaction.atomic():
            gallery = serializer.save(
                author=user,
                school=getattr(user, "school", None),
            )

            GalleryImage.objects.bulk_create(
                [
                    GalleryImage(
                        gallery=gallery,
                        attached_file=file,
                    )
                    for file in image_files
                ]
            )

    def perform_update(self, serializer):
        image_files = serializer.validated_data.pop("image_files", [])

        # multipart 対策：validated_data ではなく request.data を参照
        raw_delete_ids = self.request.data.getlist("delete_file_ids")
        delete_file_ids = [int(i) for i in raw_delete_ids]

        with transaction.atomic():
            gallery = serializer.save()

            if delete_file_ids:
                gallery.images.filter(id__in=delete_file_ids).delete()

            GalleryImage.objects.bulk_create(
                [
                    GalleryImage(
                        gallery=gallery,
                        attached_file=file,
                    )
                    for file in image_files
                ]
            )

    @action(
        detail=True,
        methods=["delete"],
        url_path="images/(?P<image_pk>[^/.]+)",
    )
    def delete_image(self, request, pk=None, image_pk=None):
        try:
            image = GalleryImage.objects.get(
                pk=image_pk,
                gallery_id=pk,
            )
        except GalleryImage.DoesNotExist:
            return Response(
                {"detail": "Image not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)