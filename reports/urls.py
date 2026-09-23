from django.urls import path
from . import views

urlpatterns = [
    path("enrollment/new/", views.enrollment_profile_view, name="enrollment_new"),
    path(
        "enrollment/<uuid:child_id>/",
        views.enrollment_profile_view,
        name="enrollment_edit",
    ),
    path(
        "enrollment/toggle-lock/<uuid:child_id>/",
        views.toggle_enrollment_lock,
        name="toggle_enrollment_lock",
    ),
    path(
        "enrollment/download/<uuid:child_id>/",
        views.download_enrollment_pdf,
        name="download_enrollment_pdf",
    ),
]
