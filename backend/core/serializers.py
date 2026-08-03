from rest_framework import serializers
from datetime import date
from .models import User, Group, Room, Center, Child, EducatorProfile, StaffAssignment


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_type_display", read_only=True)

    class Meta:
        model = User
        fields = ("user_id", "email", "full_name", "role_type", "role_display")


class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    assigned_group_id = serializers.SerializerMethodField()
    assigned_group_name = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = "__all__"
    
    def get_assigned_group_id(self, obj):
        # Assumption: A room has one active group at a time usually, or we take the first one
        group = obj.active_group.first()
        return group.group_id if group else None

    def get_assigned_group_name(self, obj):
        group = obj.active_group.first()
        return group.name if group else None


class GroupSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.name", read_only=True)
    center = serializers.PrimaryKeyRelatedField(read_only=True)
    children_ages = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = "__all__"

    def get_children_ages(self, obj):
        ages = []
        today = date.today()
        for child in obj.enrolled_children.all():
            age_months = (
                (today.year - child.birth_date.year) * 12
                + today.month
                - child.birth_date.month
            )
            if age_months < 24:
                ages.append(f"{age_months}m")
            else:
                years = age_months // 12
                rem_months = age_months % 12
                if rem_months > 0:
                    ages.append(f"{years}y {rem_months}m")
                else:
                    ages.append(f"{years}y")
        return ages


class ChildSerializer(serializers.ModelSerializer):
    age_label = serializers.SerializerMethodField()
    group_name = serializers.CharField(source="assigned_group.name", read_only=True)
    educator_name = serializers.CharField(
        source="assigned_educator.user.full_name", read_only=True
    )
    parents = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = [
            "child_id",
            "first_name",
            "last_name",
            "birth_date",
            "profile_photo_url",
            "assigned_group",
            "assigned_educator",
            "group_name",
            "educator_name",
            "age_label",
            "medical_info",
            "status",
            "parents",
        ]

    def get_age_label(self, obj):
        today = date.today()
        age_months = (
            (today.year - obj.birth_date.year) * 12 + today.month - obj.birth_date.month
        )
        if age_months < 24:
            return f"{age_months}m"
        else:
            years = age_months // 12
            rem_months = age_months % 12
            if rem_months > 0:
                return f"{years}y {rem_months}m"
            else:
                return f"{years}y"

    def get_parents(self, obj):
        relationships = obj.parent_relationships.all()
        parents_data = []
        for rel in relationships:
            parents_data.append({
                "full_name": rel.parent.user.full_name,
                "relationship_type": rel.relationship_type,
                "is_emergency_contact": rel.is_emergency_contact,
                "phone": rel.parent.user.phone_number
            })
        return parents_data


class EducatorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_id = serializers.UUIDField(source="user.user_id", read_only=True)
    
    current_group_id = serializers.SerializerMethodField()
    current_group_name = serializers.SerializerMethodField()

    class Meta:
        model = EducatorProfile
        fields = ["user_id", "full_name", "color_code", "current_group_id", "current_group_name"]

    def get_current_group_id(self, obj):
        # Fetch the active assignment
        assignment = obj.assignments.filter(is_active=True).first()
        return assignment.group.group_id if assignment else None

    def get_current_group_name(self, obj):
        assignment = obj.assignments.filter(is_active=True).first()
        return assignment.group.name if assignment else None


class StaffAssignmentSerializer(serializers.ModelSerializer):
    educator_name = serializers.CharField(
        source="educator.user.full_name", read_only=True
    )

    class Meta:
        model = StaffAssignment
        fields = [
            "assignment_id",
            "educator",
            "educator_name",
            "group",
            "check_in_time",
            "check_out_time",
            "is_active",
        ]
