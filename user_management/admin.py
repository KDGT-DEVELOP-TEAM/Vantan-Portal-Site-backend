from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    model = User

    # user_name は削除、FK(将来想定)の school_id を追加
    list_display = ('email', 'role', 'school_id', 'is_active', 'is_staff', 'created_at',)
    list_filter = ('role', 'is_active', 'is_staff',)
    ordering = ("created_at",)
    search_fields = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'is_staff')}
        ),
    )

admin.site.register(User, UserAdmin)