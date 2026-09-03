from django.urls import path
from .views import (
    get_contacts, get_messages, mark_messages_as_read, 
    upload_file, search_users, send_invitation, 
    manage_invitation, get_invitations, block_user, unblock_user
)

app_name = "chat_back"

urlpatterns = [
    path("contacts/", get_contacts, name="get_contacts"),
    path("messages/<uuid:recipient_id>/", get_messages, name="get_messages"),
    path("messages/<uuid:recipient_id>/read/", mark_messages_as_read, name="mark_messages_as_read"),
    path("upload/", upload_file, name="upload_file"),
    path("search-users/", search_users, name="search_users"),
    path("invitations/send/", send_invitation, name="send_invitation"),
    path("invitations/<int:invitation_id>/manage/", manage_invitation, name="manage_invitation"),
    path("invitations/", get_invitations, name="get_invitations"),
    path("users/<uuid:user_id>/block/", block_user, name="block_user"),
    path("users/<uuid:user_id>/unblock/", unblock_user, name="unblock_user"),
]
