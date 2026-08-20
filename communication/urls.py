from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    # --- Messaging ---
    path("inbox/", views.inbox, name="inbox"),
    path("sent/", views.sent_messages, name="sent_messages"),
    path("send/", views.send_message, name="send_message"),
    path("message/<uuid:message_id>/", views.read_message, name="read_message"),
    path("delete/<uuid:message_id>/", views.delete_message, name="delete_message"),
    
    # --- Network & Connections (Invitations) ---
    path("connections/", views.connection_list, name="connection_list"),
    path("connections/search/", views.search_directors, name="search_directors"), # <--- Bach i-searchi
    path("connections/approve/<int:connection_id>/", views.approve_connection, name="approve_connection"), # <--- Bach i-accepter
    path("connections/request/<uuid:director_id>/", views.send_connection_request, name="send_connection_request"),
    
    # --- API ---
    path("api/unread-count/", views.unread_count_api, name="unread_count_api"),
]