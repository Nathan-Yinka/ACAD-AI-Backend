"""
Admin configuration for the accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, BlacklistedToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model.
    """
    list_display = ('email', 'username', 'is_student', 'is_active', 'created_at')
    list_filter = ('is_student', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_student',)}),
    )


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for BlacklistedToken model.
    """
    list_display = ('token_preview', 'user', 'blacklisted_at')
    list_filter = ('blacklisted_at',)
    search_fields = ('token', 'user__email', 'user__username')
    ordering = ('-blacklisted_at',)
    readonly_fields = ('token', 'blacklisted_at')

    def token_preview(self, obj):
        """Show first 10 characters of token."""
        return f'{obj.token[:10]}...' if obj.token else ''
    token_preview.short_description = 'Token'

    def has_add_permission(self, request):
        """Disable adding blacklisted tokens manually."""
        return False

