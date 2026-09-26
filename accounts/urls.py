from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    login_view,
    dashboard_redirect,
    owner_dashboard,
    director_dashboard,
    educator_dashboard,
    parent_dashboard,
    personal_profile,
    get_me,
)
from accounts import views

urlpatterns = [
    # 1. Login Page (kat-asta3mel template login.html li sayebna)
    path("", login_view, name="login"),
    # 2. Logout Action
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # 3. L-Controller (Redirection Logic)
    # Hada hwa l-url li khass t-dir f LOGIN_REDIRECT_URL f settings.py
    path("dashboard/redirect/", dashboard_redirect, name="dashboard_redirect"),
    path("dashboard/owner/", owner_dashboard, name="owner_dashboard"),
    path("dashboard/director/", director_dashboard, name="director_dashboard"),
    path("dashboard/educator/", educator_dashboard, name="educator_dashboard"),
    path("dashboard/parent/", parent_dashboard, name="parent_dashboard"),
    path("profile/", personal_profile, name="personal_profile"),
    path("me/", get_me, name="get_me"),
    path('manage-principal/', views.manage_principal, name='manage_principal'),
    path('remove-principal/', views.remove_principal, name='remove_principal'),
]
