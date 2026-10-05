from django.urls import path
from .views import (
    get_contacts, get_messages, mark_messages_as_read, 
    upload_file, search_users, send_invitation, 
    manage_invitation, get_invitations,
    get_feed, create_post, react_to_post, mark_post_seen,
    get_post_comments, add_comment, get_feed_metadata,
    delete_post, subscribe_push
)

app_name = "chat_back"

urlpatterns = [
    path("contacts/", get_contacts, name="get_contacts"),
    path("subscribe-push/", subscribe_push, name="subscribe_push"),
    path("messages/<uuid:recipient_id>/", get_messages, name="get_messages"),
    path("messages/<uuid:recipient_id>/read/", mark_messages_as_read, name="mark_messages_as_read"),
    path("upload/", upload_file, name="upload_file"),
    path("search-users/", search_users, name="search_users"),
    path("invitations/send/", send_invitation, name="send_invitation"),
    path("invitations/<int:invitation_id>/manage/", manage_invitation, name="manage_invitation"),
    path("invitations/", get_invitations, name="get_invitations"),
    
    # Feed URLs
    path("feed/", get_feed, name="get_feed"),
    path("feed/create/", create_post, name="create_post"),
    path("feed/<int:post_id>/delete/", delete_post, name="delete_post"),
    path("feed/<int:post_id>/react/", react_to_post, name="react_to_post"),
    path("feed/<int:post_id>/seen/", mark_post_seen, name="mark_post_seen"),
    path("feed/<int:post_id>/comments/", get_post_comments, name="get_post_comments"),
    path("feed/<int:post_id>/comments/add/", add_comment, name="add_comment"),
    path("feed/metadata/", get_feed_metadata, name="get_feed_metadata"),
]
