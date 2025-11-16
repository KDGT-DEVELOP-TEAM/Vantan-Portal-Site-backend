from django.contrib import admin
from .models import Gallery, GalleryImage

class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 1
    fields = ('attached_file',)
    
@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 
                    # 'school', 
                    'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'author')
    search_fields = ('title', 'content')
    inlines = [GalleryImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author')
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        if not obj.school_id and hasattr(request.user, 'school') and request.user.school:
            obj.school = request.user.school
        super().save_model(request, obj, form, change)

    readonly_fields = ('created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return self.readonly_fields + ('author',)
        return self.readonly_fields