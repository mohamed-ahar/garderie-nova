from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = ('user_id', 'email', 'full_name', 'role_type', 'role_display')