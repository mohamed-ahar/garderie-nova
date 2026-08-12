from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("sent/", views.sent_messages, name="sent_messages"),
    path("send/", views.send_message, name="send_message"),
    path("read/<uuid:message_id>/", views.read_message, name="read_message"),
    path('delete/<uuid:message_id>/', views.delete_message, name='delete_message'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
]
