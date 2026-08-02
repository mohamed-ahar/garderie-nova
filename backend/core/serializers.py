from rest_framework import serializers
from .models import User, Group, Room, Center, Child, EducatorProfile, StaffAssignment

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = ('user_id', 'email', 'full_name', 'role_type', 'role_display')

class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    ratio_category_display = serializers.CharField(source='get_ratio_category_display', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    center = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Group
        fields = '__all__'

class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = ['child_id', 'first_name', 'last_name', 'birth_date', 'profile_photo_url', 'assigned_group']

class EducatorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    
    class Meta:
        model = EducatorProfile
        fields = ['user_id', 'full_name', 'qualification_level', 'color_code']

class StaffAssignmentSerializer(serializers.ModelSerializer):
    educator_name = serializers.CharField(source='educator.user.full_name', read_only=True)
    
    class Meta:
        model = StaffAssignment
        fields = ['assignment_id', 'educator', 'educator_name', 'group', 'check_in_time', 'check_out_time', 'is_active']

