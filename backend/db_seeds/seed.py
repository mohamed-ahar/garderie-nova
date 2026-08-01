import os
import django
import random
from datetime import timedelta, date
from django.utils import timezone
from core.models import (
    User, OwnerProfile, DirectorProfile, EducatorProfile, ParentProfile,
    Organization, Center, Room, Group, 
    Child, ParentChildRelationship, AttendanceLog
)

def clean_db():
    print("🧹 Cleaning old data...")
    # Delete in specific order to avoid foreign key errors
    AttendanceLog.objects.all().delete()
    ParentChildRelationship.objects.all().delete()
    Child.objects.all().delete()
    Group.objects.all().delete()
    Room.objects.all().delete()
    Center.objects.all().delete()
    Organization.objects.all().delete()
    User.objects.all().delete()
    print("✅ Database cleaned.")

def create_users():
    print("👥 Creating Users...")
    
    # 1. Network Owner
    owner_user = User.objects.create_user(
        email='owner@nova.com', 
        password='password123',
        full_name='Jean Owner',
        phone_number='555-0001',
        role_type='owner'
    )
    OwnerProfile.objects.create(user=owner_user, office_address="100 Main St")

    # 2. Director
    dir_user = User.objects.create_user(
        email='director@nova.com', 
        password='password123',
        full_name='Sarah Director',
        phone_number='555-0002',
        role_type='director'
    )
    DirectorProfile.objects.create(user=dir_user, qualification_cert="Master ECE", hired_at=date(2020, 1, 1))

    # 3. Educators
    edu1 = User.objects.create_user(
        email='emma@nova.com', password='password123', full_name='Emma Educator', role_type='educator', phone_number='555-1001'
    )
    edu2 = User.objects.create_user(
        email='lucas@nova.com', password='password123', full_name='Lucas Assistant', role_type='educator', phone_number='555-1002'
    )

    # 4. Parents
    par1 = User.objects.create_user(
        email='mom@gmail.com', password='password123', full_name='Sophie Parent', role_type='parent', phone_number='555-2001'
    )
    ParentProfile.objects.create(user=par1, home_address="123 Maple St")

    par2 = User.objects.create_user(
        email='dad@gmail.com', password='password123', full_name='Marc Parent', role_type='parent', phone_number='555-2002'
    )
    ParentProfile.objects.create(user=par2, home_address="456 Oak Ave")

    return owner_user, dir_user, [edu1, edu2], [par1, par2]

def run_seed():
    clean_db()
    owner, director, educators, parents = create_users()

    print("🏢 Creating Organization & Center...")
    # Create Org
    org = Organization.objects.create(name="Garderie Nova Inc.", owner=owner.owner_profile)

    # Create Center
    center = Center.objects.create(
        organization=org,
        name="Nova Downtown",
        address="500 King Street, Moncton, NB",
        director=director.director_profile
    )

    # Assign Educators to this center
    EducatorProfile.objects.create(user=educators[0], center=center, qualification_level="Level 2", color_code="#EF4444")
    EducatorProfile.objects.create(user=educators[1], center=center, qualification_level="Level 1", color_code="#3B82F6")

    print("🚪 Creating Rooms & Groups...")
    
    # Room 1: Infants
    r1 = Room.objects.create(center=center, name="Blue Room (Infants)", fire_capacity=10)
    g1 = Group.objects.create(
        center=center, room=r1, name="The Little Stars", 
        ratio_category='UNDER_24M'
    )

    # Room 2: Mixed
    r2 = Room.objects.create(center=center, name="Green Room (Mixed)", fire_capacity=20)
    g2 = Group.objects.create(
        center=center, room=r2, name="The Explorers", 
        ratio_category='MIXED_2_TO_4'
    )

    # Room 3: School Age
    r3 = Room.objects.create(center=center, name="Gymnasium", fire_capacity=30)
    g3 = Group.objects.create(
        center=center, room=r3, name="After School Club", 
        ratio_category='SCHOOL_AGE_5_PLUS'
    )

    print("👶 Creating Children with NB Ratio Points...")
    
    today = date.today()
    
    # Child 1: Baby (6 months old) -> 300 Points
    c1 = Child.objects.create(
        center=center, assigned_group=g1, first_name="Baby", last_name="Liam",
        birth_date=today - timedelta(days=180), current_ratio_weight=300
    )
    
    # Child 2: 2 Year Old -> 200 Points
    c2 = Child.objects.create(
        center=center, assigned_group=g2, first_name="Toddler", last_name="Noah",
        birth_date=today - timedelta(days=365*2 + 10), current_ratio_weight=200
    )

    # Child 3: 3 Year Old -> 125 Points
    c3 = Child.objects.create(
        center=center, assigned_group=g2, first_name="Kid", last_name="Emma",
        birth_date=today - timedelta(days=365*3 + 10), current_ratio_weight=125
    )

    # Child 4: 4 Year Old -> 100 Points
    c4 = Child.objects.create(
        center=center, assigned_group=g2, first_name="Big", last_name="Olivia",
        birth_date=today - timedelta(days=365*4 + 10), current_ratio_weight=100
    )

    # Child 5: School Age -> Count Based
    c5 = Child.objects.create(
        center=center, assigned_group=g3, first_name="Student", last_name="Lucas",
        birth_date=today - timedelta(days=365*7), current_ratio_weight=1
    )

    print("🔗 Linking Parents...")
    # Link Mom to Baby and Toddler
    ParentChildRelationship.objects.create(parent=parents[0].parent_profile, child=c1, relationship_type="Mother", is_emergency_contact=True)
    ParentChildRelationship.objects.create(parent=parents[0].parent_profile, child=c2, relationship_type="Mother", is_emergency_contact=True)
    
    # Link Dad to Kid Emma
    ParentChildRelationship.objects.create(parent=parents[1].parent_profile, child=c3, relationship_type="Father", is_emergency_contact=True)

    print("✅ SEEDING COMPLETE!")
    print("------------------------------------------------")
    print("Login Credentials:")
    print(f"Owner: owner@nova.com / password123")
    print(f"Director: director@nova.com / password123")
    print(f"Educator: emma@nova.com / password123")
    print(f"Parent: mom@gmail.com / password123")
    print("------------------------------------------------")

if __name__ == '__main__':
    run_seed()