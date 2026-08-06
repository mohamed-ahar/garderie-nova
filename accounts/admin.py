from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role_type", "is_active", "is_staff")
    list_filter = ("role_type", "is_active")
    search_fields = ("email", "full_name")
    ordering = ("email",)


admin.site.register(User, UserAdmin)
