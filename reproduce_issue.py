import os
import sys
import django
from datetime import date, timedelta
import uuid

sys.path.append(os.path.join(os.getcwd(), 'backend'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from core.models import User, Center, Organization, EducatorProfile, Child, Group, Room, OwnerProfile

def test_educator_compliance():
    # Setup
    owner_user = User.objects.create_user(email=f"owner_{uuid.uuid4()}@example.com", password="pass", full_name="Owner", role_type="owner")
    owner_profile = OwnerProfile.objects.create(user=owner_user)
    
    org = Organization.objects.create(name="Test Org", owner=owner_profile)
    center = Center.objects.create(organization=org, name="Test Center", address="123 Test St")
    room = Room.objects.create(center=center, name="Test Room", fire_capacity=20)
    
    # Create Educator
    user = User.objects.create_user(email=f"test_edu_{uuid.uuid4()}@example.com", password="pass", full_name="Test Edu", role_type="educator")
    educator = EducatorProfile.objects.create(user=user, center=center)
    
    # Create Group
    group = Group.objects.create(center=center, room=room, name="Test Group")
    
    # Create incompatible children for educator mixing check
    # Child 1: < 24 months (e.g., 12 months)
    dob_baby = date.today() - timedelta(days=365)
    baby = Child.objects.create(center=center, first_name="Baby", last_name="One", birth_date=dob_baby, assigned_group=group, assigned_educator=educator)
    
    # Child 2: > 24 months (e.g., 4 years)
    dob_kid = date.today() - timedelta(days=4*365)
    kid = Child.objects.create(center=center, first_name="Kid", last_name="Two", birth_date=dob_kid, assigned_group=group, assigned_educator=educator)
    
    print("Mixed age children assigned to educator.")
    
    # Trigger group recalculation
    group.recalculate_ratios()
    
    print(f"Group Compliant (Mixing check at group level): {group.is_compliant}")
    
    # Check if educator has any compliance info (should be none or not yet implemented)
    has_is_compliant = hasattr(educator, 'is_compliant')
    print(f"Educator has is_compliant field: {has_is_compliant}")
    if has_is_compliant:
        print(f"Educator is_compliant: {educator.is_compliant}")

if __name__ == "__main__":
    test_educator_compliance()