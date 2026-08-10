from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ("avatar_display", "email", "full_name", "role_type", "is_active", "is_staff")
    list_filter = ("role_type", "is_active")
    search_fields = ("email", "full_name")
    ordering = ("email",)

    def avatar_display(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_photo.url
            )
        return format_html(
            '<div style="width: 30px; height: 30px; border-radius: 50%; background-color: #10b981; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-family: sans-serif;">{}</div>',
            obj.full_name[:1].upper() if obj.full_name else "?"
        )
    avatar_display.short_description = "Avatar"


admin.site.register(User, UserAdmin)
