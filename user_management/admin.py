from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, School

class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        'email',
        'user_name',
        'role',
        'school',
        'is_active',
        'is_staff',
        'created_at',
    )

    list_filter = ('role', 'is_active', 'is_staff', 'school')
    ordering = ("created_at",)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('School', {'fields': ('school',)}),
        ('Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'role',
                'school',           # ← 追加
                'is_active',
                'is_staff'
            )
        }),
    )

# User と School を admin に登録
admin.site.register(User, UserAdmin)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)