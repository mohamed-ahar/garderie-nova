from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Group, Room, Center, Child, EducatorProfile, StaffAssignment
from .serializers import (
    UserSerializer,
    GroupSerializer,
    RoomSerializer,
    CenterSerializer,
    ChildSerializer,
    EducatorSerializer,
    StaffAssignmentSerializer,
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
        if user.role_type == "director":
            if (
                hasattr(user, "director_profile")
                and user.director_profile.managed_center
            ):
                return Group.objects.filter(center=user.director_profile.managed_center)
        if user.role_type == "owner":
            return Group.objects.all()
        return Group.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if (
            user.role_type == "director"
            and hasattr(user, "director_profile")
            and user.director_profile.managed_center
        ):
            serializer.save(center=user.director_profile.managed_center)
        else:
            serializer.save()


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "group_id"


class RoomListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if (
            user.role_type == "director"
            and hasattr(user, "director_profile")
            and user.director_profile.managed_center
        ):
            return Room.objects.filter(center=user.director_profile.managed_center)
        if user.role_type == "owner":
            return Room.objects.all()
        return Room.objects.none()


class CenterListView(generics.ListAPIView):
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]
    queryset = Center.objects.all()


class ChildListView(generics.ListCreateAPIView):
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
            queryset = Child.objects.filter(center=center)
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            return queryset
        return Child.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role_type == 'director' and hasattr(user, 'director_profile') and user.director_profile.managed_center:
             serializer.save(center=user.director_profile.managed_center)
        else:
             # If owner, might need to provide center in request data, but for now fallback or error
             serializer.save()


class ChildDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChildSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "child_id"

    def get_queryset(self):
        # Allow access to children in the user's scope
        user = self.request.user
        if user.role_type == "owner":
            return Child.objects.all()
        elif user.role_type == "director" and hasattr(user, "director_profile"):
            return Child.objects.filter(center=user.director_profile.managed_center)
        # TODO: Add logic for educators/parents
        return Child.objects.none()


class EducatorListView(generics.ListAPIView):
    serializer_class = EducatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        center = None
        if user.role_type == "director" and hasattr(user, "director_profile"):
            center = user.director_profile.managed_center

        if center:
            # Return ALL educators in center
            return EducatorProfile.objects.filter(center=center)
        return EducatorProfile.objects.none()


class AssignChildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        child_id = request.data.get("child_id")
        child = get_object_or_404(Child, child_id=child_id)

        # If child was in another group, logic handles it implicitly by overwriting assigned_group
        # But we should probably recalculate ratios for the OLD group if it exists
        old_group = child.assigned_group

        child.assigned_group = group
        child.save()

        group.recalculate_ratios()

        if old_group and old_group != group:
            old_group.recalculate_ratios()

        return Response({"status": "assigned"}, status=status.HTTP_200_OK)


class RemoveChildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        child_id = request.data.get("child_id")
        child = get_object_or_404(Child, child_id=child_id)

        if child.assigned_group and str(child.assigned_group.group_id) == str(group_id):
            child.assigned_group = None
            child.assigned_educator = (
                None  # Clear educator assignment if removed from group
            )
            child.save()

            # Update group occupancy
            group = get_object_or_404(Group, group_id=group_id)
            group.recalculate_ratios()

            return Response({"status": "removed"}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Child not in this group"}, status=status.HTTP_400_BAD_REQUEST
        )


class AssignEducatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        user_id = request.data.get("user_id")  # Educator's User ID
        educator = get_object_or_404(EducatorProfile, user__user_id=user_id)

        # Close ANY existing active assignments for this educator
        existing_assignments = StaffAssignment.objects.filter(
            educator=educator, is_active=True
        )
        old_groups = set()
        for assignment in existing_assignments:
            assignment.is_active = False
            assignment.save()
            old_groups.add(assignment.group)

        # Create active assignment
        StaffAssignment.objects.create(educator=educator, group=group, is_active=True)

        # Update group educator count
        group.current_educators = StaffAssignment.objects.filter(
            group=group, is_active=True
        ).count()
        group.recalculate_ratios()

        # Recalculate for old groups
        for og in old_groups:
            if og != group:
                og.current_educators = StaffAssignment.objects.filter(
                    group=og, is_active=True
                ).count()
                og.recalculate_ratios()

        return Response({"status": "assigned"}, status=status.HTTP_200_OK)


class UpdateGroupRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        room_id = request.data.get("room_id")

        if not room_id:
            return Response(
                {"error": "Room ID required"}, status=status.HTTP_400_BAD_REQUEST
            )

        room = get_object_or_404(Room, room_id=room_id)

        # Logic: If another group uses this room, we might need to kick them out or warn?
        # Requirement: "distinct between rooms that are assigned and empty ones"
        # We will allow "stealing" the room, or just assigning.
        # But for data integrity, if 1-to-1 is desired, we should nullify the other group's room

        current_occupant = room.active_group.first()
        if current_occupant and current_occupant != group:
            # Steal the room? Or Error? User asked to "change... and distinct"
            # Let's assume we can reassign.
            current_occupant.room = None
            current_occupant.save()

        group.room = room
        group.save()

        return Response({"status": "updated"}, status=status.HTTP_200_OK)


class RemoveEducatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, group_id=group_id)
        user_id = request.data.get("user_id")
        educator = get_object_or_404(EducatorProfile, user__user_id=user_id)

        assignments = StaffAssignment.objects.filter(
            group=group, educator=educator, is_active=True
        )
        for assignment in assignments:
            assignment.is_active = False
            assignment.save()

        # Update group educator count
        group.current_educators = StaffAssignment.objects.filter(
            group=group, is_active=True
        ).count()
        group.recalculate_ratios()

        return Response({"status": "removed"}, status=status.HTTP_200_OK)


class GroupChildrenView(generics.ListAPIView):
    serializer_class = ChildSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs["group_id"]
        return Child.objects.filter(assigned_group__group_id=group_id)


class GroupEducatorsView(generics.ListAPIView):
    serializer_class = EducatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs["group_id"]
        # Return educators who have an ACTIVE assignment in this group
        return EducatorProfile.objects.filter(
            assignments__group__group_id=group_id, assignments__is_active=True
        ).distinct()


class AssignChildEducatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        child_id = request.data.get("child_id")
        user_id = request.data.get("user_id")  # Educator's User ID

        child = get_object_or_404(Child, child_id=child_id)

        # Security check: ensure child is in the group?
        if str(child.assigned_group.group_id) != str(group_id):
            return Response(
                {"error": "Child not in this group"}, status=status.HTTP_400_BAD_REQUEST
            )

        if user_id:
            educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
            child.assigned_educator = educator
        else:
            child.assigned_educator = None

        child.save()
        return Response({"status": "updated"}, status=status.HTTP_200_OK)
