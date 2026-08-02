from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Group, Room, Center, Child, EducatorProfile, StaffAssignment
from .serializers import (
    UserSerializer, GroupSerializer, RoomSerializer, CenterSerializer,
    ChildSerializer, EducatorSerializer, StaffAssignmentSerializer
)

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class GroupListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role_type == 'director':
            if hasattr(user, 'director_profile') and user.director_profile.managed_center:
                return Group.objects.filter(center=user.director_profile.managed_center)
        if user.role_type == 'owner':
             return Group.objects.all()
        return Group.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role_type == 'director' and hasattr(user, 'director_profile') and user.director_profile.managed_center:
             serializer.save(center=user.director_profile.managed_center)
        else:
             serializer.save()

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'group_id'

class RoomListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role_type == 'director' and hasattr(user, 'director_profile') and user.director_profile.managed_center:
            return Room.objects.filter(center=user.director_profile.managed_center)
        if user.role_type == 'owner':
            return Room.objects.all()
        return Room.objects.none()

class CenterListView(generics.ListAPIView):
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]
    queryset = Center.objects.all()

class ChildListView(generics.ListAPIView):
    serializer_class = ChildSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        center = None
        if user.role_type == 'director' and hasattr(user, 'director_profile'):
            center = user.director_profile.managed_center
        elif user.role_type == 'owner':
            # Simplified for now, owners might need to filter by center param
            pass 
        
        if center:
            return Child.objects.filter(center=center)
        return Child.objects.none()

class EducatorListView(generics.ListAPIView):
    serializer_class = EducatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        center = None
        if user.role_type == 'director' and hasattr(user, 'director_profile'):
            center = user.director_profile.managed_center
        
        if center:
            return EducatorProfile.objects.filter(center=center)
        return EducatorProfile.objects.none()

class AssignChildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        child_id = request.data.get('child_id')
        child = get_object_or_404(Child, child_id=child_id)
        
        child.assigned_group = group
        child.save()
        
        group.recalculate_ratios()

        return Response({'status': 'assigned'}, status=status.HTTP_200_OK)

class RemoveChildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        child_id = request.data.get('child_id')
        child = get_object_or_404(Child, child_id=child_id)
        
        if child.assigned_group and str(child.assigned_group.group_id) == str(group_id):
            child.assigned_group = None
            child.save()
            
            # Update group occupancy
            group = get_object_or_404(Group, group_id=group_id)
            group.recalculate_ratios()
            
            return Response({'status': 'removed'}, status=status.HTTP_200_OK)
        return Response({'error': 'Child not in this group'}, status=status.HTTP_400_BAD_REQUEST)

class AssignEducatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        user_id = request.data.get('user_id') # Educator's User ID
        educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
        
        # Create active assignment
        StaffAssignment.objects.create(
            educator=educator,
            group=group,
            is_active=True
        )
        
        # Update group educator count
        group.current_educators = StaffAssignment.objects.filter(group=group, is_active=True).count()
        group.recalculate_ratios()

        return Response({'status': 'assigned'}, status=status.HTTP_200_OK)

class RemoveEducatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        user_id = request.data.get('user_id')
        educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
        
        assignments = StaffAssignment.objects.filter(group=group, educator=educator, is_active=True)
        for assignment in assignments:
            assignment.is_active = False
            assignment.save()
            
        # Update group educator count
        group.current_educators = StaffAssignment.objects.filter(group=group, is_active=True).count()
        group.recalculate_ratios()

        return Response({'status': 'removed'}, status=status.HTTP_200_OK)

class GroupChildrenView(generics.ListAPIView):
    serializer_class = ChildSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return Child.objects.filter(assigned_group__group_id=group_id)

class GroupEducatorsView(generics.ListAPIView):
    serializer_class = EducatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        # Return educators who have an ACTIVE assignment in this group
        return EducatorProfile.objects.filter(assignments__group__group_id=group_id, assignments__is_active=True).distinct()