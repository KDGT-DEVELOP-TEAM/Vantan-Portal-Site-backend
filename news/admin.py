from django.contrib import admin
from .models import News, NewsAttachment

# NewsAttachmentをNewsの詳細画面でインライン編集するためのクラス
class NewsAttachmentInline(admin.TabularInline):
    model = NewsAttachment 
    extra = 1 
    # idフィールドを含めることで削除チェックボックスが有効化されます
    fields = ('attached_file', 'id') 
    readonly_fields = ('id',) 
    
# お知らせモデルの管理サイト表示設定
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'user', 'importance','created_at', 'updated_at')
    list_filter = ('importance', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'user__user_name') # ユーザー名はuser_nameに合わせる
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'user', 'importance'), 
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [NewsAttachmentInline] 
    
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    # 作成者をログインユーザーに自動設定
    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        if not obj.school_id and hasattr(request.user, 'school') and request.user.school:
            obj.school = request.user.school
        super().save_model(request, obj, form, change)
    
    # ユーザー権限によるreadonly設定
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and not request.user.is_superuser:
            # 記事が存在する場合、スーパーユーザーでなければ作成者は変更不可
            readonly_fields.append('user') 
        return tuple(readonly_fields)