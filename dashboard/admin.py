from django.contrib import admin
from .models import (
    Organization,
    Center,
    Child,
    Group,
    TransferHistory,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_id', 'owner')
    search_fields = ('name', 'owner__username')  # assuming Owner has username/email


@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):
    list_display = ('child_full_name', 'from_center_name', 'to_center_name', 'transfer_date', 'outgoing_director_name', 'incoming_director_name')
    list_filter = ('transfer_date', 'from_center_name', 'to_center_name')
    search_fields = ('child_first_name', 'child_last_name', 'from_center_name', 'to_center_name')
    readonly_fields = ('history_id', 'transfer_date', 'child_full_name')
    ordering = ('-transfer_date',)
    
    fieldsets = (
        ('Child Information', {
            'fields': ('history_id', 'child_first_name', 'child_last_name', 'child_birth_date', 'child_id_reference')
        }),
        ('Transfer Details', {
            'fields': ('from_center_name', 'from_center_id', 'to_center_name', 'to_center_id', 'transfer_date', 'reason')
        }),
        ('Approval Information', {
            'fields': ('outgoing_director_name', 'incoming_director_name', 'parent_signatures', 'original_request_id')
        }),
    )


admin.site.register(Center)
admin.site.register(Child)
admin.site.register(Group)
