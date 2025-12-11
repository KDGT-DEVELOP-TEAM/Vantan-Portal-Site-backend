from django.contrib import admin
from .models import Timeschedule, TimescheduleImage # 忘れずにインポート

# TimescheduleImageをTimescheduleの編集画面に組み込むための設定
class TimescheduleImageInline(admin.TabularInline):
    # どのモデルをインラインとして扱うか
    model = TimescheduleImage
    # 追加で空のフォームをいくつ表示するか
    extra = 1

# Timescheduleモデルを管理画面に登録
@admin.register(Timeschedule)
class TimescheduleAdmin(admin.ModelAdmin):
    # 一覧画面に表示するフィールド
    list_display = ('title', 'grade', 'user_id', 'created_at')
    # フィルタリング可能なフィールド
    list_filter = ('grade', 'created_at')
    # 検索可能なフィールド
    search_fields = ('title', 'content')
    # 編集画面でTimescheduleImageをインライン表示
    inlines = [TimescheduleImageInline]

# TimescheduleImageはTimescheduleの編集画面で管理できるため、
# 個別の admin.site.register(TimescheduleImage) は通常は不要です。