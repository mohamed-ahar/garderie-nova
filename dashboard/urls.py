from django.urls import path

from accounts.views import owner_dashboard
from django.views.generic import RedirectView
from .views import *
from .all_views.parent_views import *
from .all_views.director_views import * 
from .all_views.owner_views import *

urlpatterns = [
    path("", RedirectView.as_view(url="dashboard/", permanent=False)),
    path("groups/", group_list_view, name="group_list"),
    path("groups/add/", group_add_view, name="group_add"),
    path("groups/<uuid:group_id>/edit/", group_edit_view, name="group_edit"),
    path("groups/<uuid:group_id>/delete/", group_delete_view, name="group_delete"),
    path("educators/", educator_list_view, name="educator_list"),
    path("educators/create/", educator_add_view, name="educator_add"),
    path("educators/<uuid:user_id>/", educator_detail_view, name="educator_detail"),
    path("educators/<uuid:user_id>/edit/", educator_edit_view, name="educator_edit"),
    path(
        "educators/<uuid:user_id>/delete/", educator_delete_view, name="educator_delete"
    ),
    path("parents/", parent_list_view, name="parent_list"),
    path("parents/add/", parent_add_view, name="parent_add"),
    path("parents/<uuid:user_id>/", parent_detail_view, name="parent_detail"),
    path("parents/<uuid:user_id>/edit/", parent_edit_view, name="parent_edit"),
    path("parents/<uuid:user_id>/delete/", parent_delete_view, name="parent_delete"),
    path("parents/register-child/", register_child_view, name="register_child"),
    path("waitlist/", waitlist_view, name="waitlist_manage"),
    
    # Notifications API
    path("api/notifications/", get_notifications_api, name="get_notifications"),
    path("api/notifications/<uuid:notif_id>/read/", mark_notification_read_api, name="mark_notification_read"),
    
    # owner
    path("owner/", owner_dashboard, name="owner_dashboard"),
    path("center/create/", create_center, name="create_center"),
    path("center/success/<uuid:center_id>/", center_success, name="center_success"),
    path("center/details/<uuid:center_id>/", center_info_view, name="center_details"),
    path("my-centers/", owner_centers_list, name="owner_centers_list"),
    path("add-director/", create_director_general, name="add_director_general"),
    path("center/<uuid:center_id>/assign-director/",
        assign_director_to_center,
        name="assign_director",
    ),
    path("rooms/", room_list_view, name="room_list"),
    path("rooms/create/", room_create_view, name="room_create"),
    path("rooms/<uuid:room_id>/edit/", room_edit_view, name="room_edit"),
    path("rooms/<uuid:room_id>/delete/", room_delete_view, name="room_delete"),
]
