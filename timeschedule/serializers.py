from .models import Timeschedule, TimescheduleImage
import os

# ファイルサイズ10MBの上限
MAX_FILE_SIZE = 10 * 1024 * 1024
# 許可する拡張子(pngも入れたほうが良い？)
ALLOWED_EXTENSIONS = ['.pdf']

class TimescheduleImageSerializer(serializers.ModelSerializer): 

    attached_file_url = serializers.SerializerMethodField()

    class Meta:
        model = TimescheduleImage
        fields = ['id', 'attached_file', 'attached_file_url']
        read_only_fields = ['id', 'attached_file_url']

    # ファイルの形式/サイズをチェック
    def validate_attached_file(self, value):

        # ファイルサイズチェック
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"ファイルサイズが大きすぎます。上限は {MAX_FILE_SIZE // 1024 // 1024}MB です。"
            )

        # ファイル形式チェック(今の所pdfのみ)
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"許可されていないファイル形式です。許可されている形式: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        return value

    def get_attached_file_url(self, obj):
        # 添付ファイルの完全なURLを構築
        if obj.attached_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attached_file.url)
            return obj.attached_file.url
        return None


class TimescheduleSerializer(serializers.ModelSerializer):
# ----- GETの時 -----
    # read_onry=Trueで読み取り専用に
    # もし1つのTimescheduleに複数の時間割画像を追加する場合はmany=Trueを追加
    image = TimescheduleImageSerializer(
        source='images', 
        read_only=True
    )

# ----- POSTの時 -----
    # 投稿時専用のファイルフィールド
    image_file = serializers.FileField(
        max_length=100, 
        # 時間割ファイルの添付必須にする
        required=True,
        # write_only=Trueで書き込み専用に
        write_only=True
    )

# ------------------
    class Meta:
        model = Timeschedule
        fields = ['id', 'grade', 'title', 'content', 'created_at', 
                  'user_id', 'school_id', 
                  'image', 'image_file']
        read_only_fields = ['id', 'created_at', 'user_id', 'school_id']

# ----- POSTの時 -----
    def create(self, validated_data):
        image_file = validated_data.pop('image_file')
        user = self.context['request'].user

        validated_data['school_id'] = user.school if hasattr(user, 'school') else None 
        # (schoolがForeignKeyに対応した場合、以下に変更)
        # validated_data['school_id'] = getattr(user, 'school', None)

        validated_data['user_id'] = user

        # Timescheduleを作成
        timeschedule_instance = Timeschedule.objects.create(**validated_data)
        
        # TimescheduleImageを作成
        TimescheduleImage.objects.create(
            timeschedule=timeschedule_instance,
            attached_file=image_file,
        )
        return timeschedule_instance