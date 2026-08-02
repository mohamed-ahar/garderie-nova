from django.contrib import admin
from .models import (
    User,
    Organization,
    Center,
    OwnerProfile,
    DirectorProfile,
    ViceDirectorProfile,
    EducatorProfile,
    ParentProfile,
    Child,
    Group,
)


class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role_type", "is_active", "is_staff")
    list_filter = ("role_type", "is_active")
    search_fields = ("email", "full_name")
    ordering = ("email",)


admin.site.register(User, UserAdmin)
admin.site.register(Organization)
admin.site.register(Center)
admin.site.register(OwnerProfile)
admin.site.register(DirectorProfile)
admin.site.register(ViceDirectorProfile)
admin.site.register(EducatorProfile)
admin.site.register(ParentProfile)
admin.site.register(Child)
admin.site.register(Group)