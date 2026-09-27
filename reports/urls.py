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
    # Illness Reports (Annexe 11)
    path(
        "illness/create/<uuid:child_id>/",
        views.create_illness_report,
        name="create_illness_report",
    ),
    path(
        "illness/sign/<uuid:report_id>/",
        views.sign_illness_report,
        name="sign_illness_report",
    ),
    path(
        "illness/view/<uuid:report_id>/",
        views.view_illness_report,
        name="view_illness_report",
    ),
    # Reintegration Forms (Annexe 12)
    path(
        "reintegration/create/<uuid:child_id>/",
        views.create_reintegration_form,
        name="create_reintegration_form",
    ),
    path(
        "reintegration/sign/<uuid:form_id>/",
        views.sign_reintegration_form,
        name="sign_reintegration_form",
    ),
    path(
        "reintegration/view/<uuid:form_id>/",
        views.view_reintegration_form,
        name="view_reintegration_form",
    ),
]
