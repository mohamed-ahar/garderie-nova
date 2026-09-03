from django.urls import path

from accounts.views import owner_dashboard
from django.views.generic import RedirectView
from .views import *
from .all_views.parent_views import *
from .all_views.director_views import * 
from .all_views.owner_views import *
from .all_views.child_views import *
from .all_views.educator_views import *
from. import views

urlpatterns = [
    path(
        'parents/import-children/<uuid:center_id>/',
        views.import_children_csv,
        name='import_children_csv'
    ),
    path("children/", child_list_view, name="child_list"),
    path("educator/my-children/", educator_assigned_children, name="educator_assigned_children"),
    path("educator/daily-checkups/", daily_checkup_list, name="daily_checkup_list"),
    path("educator/attendance-board/", attendance_board, name="attendance_board"),
    path("educator/weekly-attendance/", weekly_attendance_report, name="weekly_attendance_report"),
    path("educator/weekly-attendance/export/", export_attendance_pdf, name="export_attendance_pdf"),
    path("educator/weekly-report/<uuid:child_id>/export/", export_weekly_daily_report_pdf, name="export_weekly_daily_report_pdf"),
    
    # Parent export URLs
    path("parent/weekly-report/<uuid:child_id>/export/", parent_export_weekly_report_pdf, name="parent_export_weekly_report_pdf"),
    path("parent/attendance/<uuid:child_id>/export/", parent_export_attendance_pdf, name="parent_export_attendance_pdf"),
    path("educator/daily-checkups/<uuid:child_id>/", daily_checkup_form, name="daily_checkup_form"),
    path("educator/attendance/<uuid:child_id>/", mark_attendance, name="mark_attendance"),
    path("children/<uuid:child_id>/", child_profile_view, name="child_profile"),
    
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
    path("parents/my-children/", parent_children_list, name="parent_children_list"),
    path("parents/<uuid:user_id>/", parent_detail_view, name="parent_detail"),
    path("parents/<uuid:user_id>/edit/", parent_edit_view, name="parent_edit"),
    path("parents/<uuid:user_id>/delete/", parent_delete_view, name="parent_delete"),
    path("parents/register-child/", register_child_view, name="register_child"),
    path("parents/request-access/", request_center_access, name="request_center_access"),
    path("parents/transfer-request/", transfer_request_view, name="transfer_request"),
    path("parents/transfer-request/<uuid:request_id>/sign/", sign_transfer_request, name="sign_transfer_request"),
    
    path("waitlist/", waitlist_view, name="waitlist_manage"),
    path("transfer-requests/", transfer_requests_list, name="transfer_requests_list"),
    path("transfer-requests/<uuid:request_id>/process/", process_transfer_request, name="process_transfer_request"),
    path("access-requests/", manage_parent_access_requests, name="manage_parent_access_requests"),
    path("access-requests/<int:request_id>/update/", update_parent_access, name="update_parent_access"),
    
    # Notifications API
    path("api/notifications/", get_notifications_api, name="get_notifications"),
    path("api/notifications/<uuid:notif_id>/read/", mark_notification_read_api, name="mark_notification_read"),
    
    # owner
    path("owner/", owner_dashboard, name="owner_dashboard"),
    path("center/create/", create_center, name="create_center"),
    path('centers/<uuid:center_id>/edit/', views.edit_center, name='edit_center'),
    path('centers/<uuid:center_id>/delete/', views.delete_center, name='delete_center'),
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
    path("directors/", list_directors, name="list_directors"),
    path("directors/<uuid:director_id>/profile/", views.director_profile, name="director_profile"),
    path("directors/<uuid:director_id>/delete/", delete_director, name="delete_director"),
    # --- Vice Director Management ---
    path('vice-directors/', views.list_vice_directors, name='list_vice_directors'),
    path('vice-directors/add/', views.add_vice_director, name='add_vice_director'),
    path('vice-directors/edit/<uuid:vice_id>/', views.edit_vice_director, name='edit_vice_director'),
    path('vice-directors/delete/<uuid:vice_id>/', views.delete_vice_director, name='delete_vice_director'),

    # --- Role Switching Logic (The Magic Button) ---
    # Had l-URL kikhdem l-Director o l-Vice Director f mara whda
    path('staff/switch-role/<uuid:user_id>/', views.switch_staff_role, name='switch_staff_role'),    
    
    
]
