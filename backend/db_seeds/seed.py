from multiprocessing import parent_process
import os
import django
import random
from datetime import timedelta, date
from django.utils import timezone
import random
from core.models import (
    User,
    OwnerProfile,
    DirectorProfile,
    EducatorProfile,
    ParentProfile,
    Organization,
    Center,
    Room,
    Group,
    Child,
    ParentChildRelationship,
    AttendanceLog,
)
from names_generator import generate_name

n_educators = 4
n_parents = 20
n_children = 20


def clean_db():
    print("🧹 Cleaning old data...")
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

    owner_user = User.objects.create_user(
        email="owner@nova.com",
        password="password123",
        full_name="Jean Owner",
        phone_number="555-0001",
        role_type="owner",
    )
    OwnerProfile.objects.create(user=owner_user, office_address="100 Main St")

    dir_user = User.objects.create_user(
        email="director@nova.com",
        password="password123",
        full_name="Sarah Director",
        phone_number="555-0002",
        role_type="director",
    )
    DirectorProfile.objects.create(
        user=dir_user, qualification_cert="Master ECE", hired_at=date(2020, 1, 1)
    )
    educators = []
    for i in range(n_educators):
        educators.append(
            User.objects.create_user(
                email=f"educator{i}@nova.com",
                password="password123",
                full_name=f"Educator {i}",
                role_type="educator",
                phone_number="555-1001",
            )
        )
    parents = []
    for i in range(n_parents):
        first_name = generate_name(style="capital").split(" ")[0]
        last_name = "Parent "+str(i)
        parents.append(
            User.objects.create_user(
                email=f"parent{i}@gmail.com",
                password="password123",
                full_name=f"{first_name} {last_name}",
                role_type="parent",
                phone_number="555-2001",
            )
        )
        ParentProfile.objects.create(user=parents[i], home_address="123 Maple St")

    return owner_user, dir_user, educators, parents


def run_seed():
    clean_db()
    owner, director, educators, parents = create_users()

    org = Organization.objects.create(
        name="Garderie Nova Inc.", owner=owner.owner_profile
    )

    center = Center.objects.create(
        organization=org,
        name="Nova Downtown",
        address="500 King Street, Moncton, NB",
        director=director.director_profile,
    )
    for i in range(n_educators):
        EducatorProfile.objects.create(
            user=educators[i],
            center=center,
        )
    rooms = [
        Room.objects.create(center=center, name=generate_name(), fire_capacity=10)
        for i in range(10)
    ]
    today = date.today()
    for i in range(n_children):
        first_name, _ = generate_name(style="capital").split(" ")
        last_name = f"Child {i}"
        c1 = Child.objects.create(
            center=center,
            assigned_group=None,
            first_name=first_name,
            last_name=last_name,
            birth_date=today - timedelta(days=180 * int(random.uniform(0, 20))),
        )
        print("🔗 Linking Parent : ", i)
        ParentChildRelationship.objects.create(
            parent=parents[i].parent_profile,
            child=c1,
            relationship_type="Mother",
            is_emergency_contact=True,
        )

    print("✅ SEEDING COMPLETE!")
    print("------------------------------------------------")
    print("Login Credentials:")
    print(f"Owner: owner@nova.com / password123")
    print(f"Director: director@nova.com / password123")
    print(f"Educator: emma@nova.com / password123")
    print(f"Parent: mom@gmail.com / password123")
    print("------------------------------------------------")


if __name__ == "__main__":
    run_seed()
