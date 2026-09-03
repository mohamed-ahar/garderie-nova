from django.urls import path
from .views import get_contacts, get_messages, mark_messages_as_read

app_name = "chat_back"

urlpatterns = [
    path("contacts/", get_contacts, name="get_contacts"),
    path("messages/<uuid:recipient_id>/", get_messages, name="get_messages"),
    path("messages/<uuid:recipient_id>/read/", mark_messages_as_read, name="mark_messages_as_read"),
]
