from django.contrib import admin
from .models import (
    Organization,
    Center,
    Child,
    Group,
)


admin.site.register(Organization)
admin.site.register(Center)
admin.site.register(Child)
admin.site.register(Group)
