from django.urls import path
from .views import (
    CurrentUserView, GroupListCreateView, GroupDetailView, LinkChildToParentView, RoomListView, CenterListView,
    ChildListView, ChildDetailView, EducatorListView, AssignChildView, RemoveChildView,
        AssignEducatorView, RemoveEducatorView, GroupChildrenView, GroupEducatorsView, AssignChildEducatorView, UpdateGroupRoomView,
        EducatorDetailView, ParentListView, ParentDetailView
    )
    
urlpatterns = [
        path('me/', CurrentUserView.as_view(), name='current_user'),
        path('groups/', GroupListCreateView.as_view(), name='group_list_create'),
        path('groups/<uuid:group_id>/', GroupDetailView.as_view(), name='group_detail'),
        path('groups/<uuid:group_id>/update_room/', UpdateGroupRoomView.as_view(), name='update_group_room'),
        
        path('groups/<uuid:group_id>/children/', GroupChildrenView.as_view(), name='group_children'),
        path('groups/<uuid:group_id>/educators/', GroupEducatorsView.as_view(), name='group_educators'),
        
        path('groups/<uuid:group_id>/assign_child/', AssignChildView.as_view(), name='assign_child'),
        path('groups/<uuid:group_id>/remove_child/', RemoveChildView.as_view(), name='remove_child'),
        
        path('groups/<uuid:group_id>/assign_educator/', AssignEducatorView.as_view(), name='assign_educator'),
        path('groups/<uuid:group_id>/remove_educator/', RemoveEducatorView.as_view(), name='remove_educator'),
    
        path('groups/<uuid:group_id>/assign_educator_to_child/', AssignChildEducatorView.as_view(), name='assign_child_educator'),
        
        path('rooms/', RoomListView.as_view(), name='room_list'),
        path('centers/', CenterListView.as_view(), name='center_list'),
        
        path('children/available/', ChildListView.as_view(), name='child_list'), # Assuming all for now
        path('children/<uuid:child_id>/', ChildDetailView.as_view(), name='child_detail'),
        
        path('educators/available/', EducatorListView.as_view(), name='educator_list'),
        path('educators/<uuid:user__user_id>/', EducatorDetailView.as_view(), name='educator_detail'),
    
            path('parents/', ParentListView.as_view(), name='parent_list'),
            path('parents/<uuid:user__user_id>/', ParentDetailView.as_view(), name='parent_detail'),
            path('parents/<uuid:user__user_id>/link_child/', LinkChildToParentView.as_view(), name='link_child_to_parent'),
]
