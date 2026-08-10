from django.contrib import admin
from .models import (
    Organization,
    Center,
    Child,
    Group,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_id', 'owner')
    search_fields = ('name', 'owner__username')  # assuming Owner has username/email

admin.site.register(Center)
admin.site.register(Child)
admin.site.register(Group)
