from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from django.core.files.uploadedfile import UploadedFile
import magic

from .models import Gallery, GalleryImage, validate_file_size, ALLOWED_IMAGE_EXTENSIONS # バリデーターをインポート

class GalleryImageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryImage
        fields = ['id', 'attached_file', 'file_url']
        read_only_fields = ['id', 'file_url']

    def get_file_url(self, obj):
        # 添付ファイルの完全なURLを構築
        if obj.attached_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attached_file.url)
            return obj.attached_file.url
        return None


class GallerySerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    
    # ファイルアップロード用フィールド(複数ファイル対応に変更)
    image_files = serializers.ListField(
        child=serializers.FileField(
            # 修正: ファイル名 max_length を 255 に
            max_length=255, 
            allow_empty_file=False,
            # 修正: ファイル名向けのバリデーターを追加
            validators=[
                FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
                validate_file_size,
            ],
            help_text="アップロードする添付画像ファイル (単体) 10MB以下"
        ),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    # 既存ファイル削除用のフィールド(既存ファイルのIDを収容)
    delete_file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Gallery
        fields = [
            'id', 'title', 'content', 'images', 
            'image_files', 'delete_file_ids',
            'created_at', 'updated_at', 'author',
            # 'school'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'author',
                            #  'school'
                             ]

    # タイトル名のバリデーション
    def validate_title(self, value):
        MAX_TITLE_LENGTH = 255
        if len(value) > MAX_TITLE_LENGTH:
            raise serializers.ValidationError(
                f"タイトルは最大{MAX_TITLE_LENGTH}文字までです(現在 {len(value)} 文字)"
            )
        return value

    # 画像ファイルのバリデーション
    def validate_image_files(self, files):
        # 画像枚数チェック(一旦5枚に指定)
        MAX_IMAGES = 5
        if len(files) > MAX_IMAGES:
            raise serializers.ValidationError (f"最大{MAX_IMAGES} 枚までアップロード可能です。")

        for file in files:
            # ファイル名の長さチェック(modelに合わせて255文字)
            if len(file.name) > 255:
                raise serializers.ValidationError(f"ファイル名は255文字以内で指定してください(現在 {(len(file.name))}文字)")

            # 拡張子チェック
            ext = file.name.split('.')[-1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise serializers.ValidationError(f"{ext}形式は許可されていません")
            
            # ファイルサイズのチェック
            validate_file_size(file)

            # ファイル形式のチェック
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0) # 読んだ位置をリセット
            if not mime_type.startswith("image/"):
                raise serializers.ValidationError(f"{file.name} は画像ファイルではありません")
        
        return files

    def create(self, validated_data):
        # 添付ファイルを分離
        image_files = validated_data.pop('image_files', [])
        delete_file_ids = validated_data.pop('delete_file_ids', [])

        user = self.context['request'].user
        # SchoolはForeignKeyであり、ユーザーに紐づくSchoolを自動で設定
        # validated_data['school'] = user.school if hasattr(user, 'school') else None 
        validated_data['author'] = user
        
        gallery_instance = Gallery.objects.create(**validated_data)

        # ファイルをまとめて保存
        for img in image_files:
            GalleryImage.objects.create(
                gallery=gallery_instance,
                attached_file=img
            )
        return gallery_instance


    def update(self, instance, validated_data):
        image_files = validated_data.pop('image_files', None)
        delete_file_ids = validated_data.pop('delete_file_ids', None)

        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.save()

        # 注: S3などのストレージのファイル自体を削除するには、シグナルやカスタムロジックが必要です
        # 削除したいファイルがあれば削除
        if delete_file_ids:
            instance.images.filter(id__in=delete_file_ids).delete()
        
        # 新しいファイルを登録(既存ファイルは残す)
        if image_files:
            for img in image_files:
                GalleryImage.objects.create(
                    gallery=instance, 
                    attached_file=img,
                )
        return instance