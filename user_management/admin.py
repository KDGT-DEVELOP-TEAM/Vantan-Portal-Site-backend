from django.contrib import admin
from .models import User, School
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ('email', 'role', 'school', 'is_active', 'is_staff', 'created_at',)
    list_filter = ('role', 'is_active', 'is_staff',)
    ordering = ("created_at",)
    search_fields = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('School', {'fields': ('school',)}),  # ← FK をここで見せても良い
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'school', 'is_active', 'is_staff')}
        ),
    )

admin.site.register(User, UserAdmin)
admin.site.register(School)