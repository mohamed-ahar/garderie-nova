from django.urls import path
from .views import (
<<<<<<< HEAD
    CurrentUserView, GroupListCreateView, GroupDetailView, RoomListView, CenterListView,
    ChildListView, ChildDetailView, EducatorListView, AssignChildView, RemoveChildView,
    AssignEducatorView, RemoveEducatorView, GroupChildrenView, GroupEducatorsView,
    dashboard, student_info
=======
    login_view,
    logout_view,
    dashboard_view,
    group_list_view,
    group_edit_view,
    group_delete_view,
>>>>>>> next-v
)
from django.views.generic import RedirectView

urlpatterns = [
<<<<<<< HEAD
    path('dashboard/', dashboard, name='dashboard'),
    path('student-info/', student_info, name='student_info'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('groups/', GroupListCreateView.as_view(), name='group_list_create'),
    path('groups/<uuid:group_id>/', GroupDetailView.as_view(), name='group_detail'),
    
    path('groups/<uuid:group_id>/children/', GroupChildrenView.as_view(), name='group_children'),
    path('groups/<uuid:group_id>/educators/', GroupEducatorsView.as_view(), name='group_educators'),
    
    path('groups/<uuid:group_id>/assign_child/', AssignChildView.as_view(), name='assign_child'),
    path('groups/<uuid:group_id>/remove_child/', RemoveChildView.as_view(), name='remove_child'),
    
    path('groups/<uuid:group_id>/assign_educator/', AssignEducatorView.as_view(), name='assign_educator'),
    path('groups/<uuid:group_id>/remove_educator/', RemoveEducatorView.as_view(), name='remove_educator'),
    
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('centers/', CenterListView.as_view(), name='center_list'),
    
    path('children/available/', ChildListView.as_view(), name='child_list'), # Assuming all for now
    path('children/<uuid:child_id>/', ChildDetailView.as_view(), name='child_detail'),
    path('educators/available/', EducatorListView.as_view(), name='educator_list'),
=======
    path("", RedirectView.as_view(url="dashboard/", permanent=False)),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("groups/", group_list_view, name="group_list"),
    path("groups/<uuid:group_id>/edit/", group_edit_view, name="group_edit"),
    path("groups/<uuid:group_id>/delete/", group_delete_view, name="group_delete"),
>>>>>>> next-v
]
