from django.urls import path
from .views import (
    login_view,
    logout_view,
    dashboard_view,
    group_list_view,
    group_edit_view,
    group_delete_view,
)
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="dashboard/", permanent=False)),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("groups/", group_list_view, name="group_list"),
    path("groups/<uuid:group_id>/edit/", group_edit_view, name="group_edit"),
    path("groups/<uuid:group_id>/delete/", group_delete_view, name="group_delete"),
]
