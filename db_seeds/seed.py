import os
import django
import random
from datetime import timedelta, date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from accounts.models import (
    User,
    Owner,
    Director,
    Educator,
    ParentProfile,
)
from dashboard.models import (
    Organization,
    Center,
    Room,
    Group,
    Child,
    ParentChildRelationship,
    AttendanceLog,
)

FIRST_NAMES = [
    "Liam",
    "Noah",
    "Oliver",
    "Elijah",
    "James",
    "William",
    "Benjamin",
    "Lucas",
    "Henry",
    "Theodore",
    "Olivia",
    "Emma",
    "Charlotte",
    "Amelia",
    "Sophia",
    "Isabella",
    "Ava",
    "Mia",
    "Evelyn",
    "Harper",
    "Ethan",
    "Mateo",
    "Daniel",
    "Jack",
    "Alexander",
    "Luna",
    "Camila",
    "Gianna",
    "Elizabeth",
    "Eleanor",
    "Mason",
    "Michael",
    "Silas",
    "Ezra",
    "Aiden",
    "Logan",
    "David",
    "Joseph",
    "Samuel",
    "Jackson",
    "Avery",
    "Ella",
    "Scarlett",
    "Grace",
    "Chloe",
    "Victoria",
    "Riley",
    "Aria",
    "Lily",
    "Zoey",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
]


def clean_db():
    print("Cleaning database...")
    AttendanceLog.objects.all().delete()
    ParentChildRelationship.objects.all().delete()
    Child.objects.all().delete()
    Group.objects.all().delete()
    Room.objects.all().delete()
    Educator.objects.all().delete()
    Center.objects.all().delete()
    Organization.objects.all().delete()
    User.objects.all().delete()


def run_seed():
    clean_db()

    print("Creating Owners...")
    owner_user_1 = User.objects.create_user(
        email="owner1@nova.com",
        password="password123",
        full_name="Jean Nova",
        phone_number="555-0101",
        role_type="owner",
    )
    op1 = Owner.objects.create(user=owner_user_1, office_address="100 Main St, Moncton")

    owner_user_2 = User.objects.create_user(
        email="owner2@star.com",
        password="password123",
        full_name="Mary Star",
        phone_number="555-0102",
        role_type="owner",
    )
    op2 = Owner.objects.create(user=owner_user_2, office_address="200 West Ave, Dieppe")

    print("Creating Organizations...")
    org1 = Organization.objects.create(name="Nova Group Inc.", owner=op1)
    org2 = Organization.objects.create(name="Little Stars Academy", owner=op2)

    print("Creating Directors...")
    directors = []
    for i in range(3):
        d_user = User.objects.create_user(
            email=f"director{i+1}@nova.com",
            password="password123",
            full_name=f"Director {LAST_NAMES[i]}",
            phone_number=f"555-020{i}",
            role_type="director",
        )
        dp = Director.objects.create(
            user=d_user, qualification_cert="Level 5 ECE", hired_at=date(2020, 1, 15)
        )
        directors.append(dp)

    print("Creating Centers...")
    center1 = Center.objects.create(
        organization=org1,
        name="Nova Downtown",
        address="500 King St",
        director=directors[0],
    )

    center2 = Center.objects.create(
        organization=org1,
        name="Nova North",
        address="100 Mountain Rd",
        director=directors[1],
    )

    center3 = Center.objects.create(
        organization=org2,
        name="Little Stars West",
        address="50 West Main St",
        director=directors[2],
    )

    centers = [center1, center2, center3]

    print("Creating Rooms and Educators...")
    edu_counter = 1
    for center in centers:
        room_types = [("Infants", 10), ("Toddlers", 15), ("Preschool", 20)]
        for r_name, capacity in room_types:
            Room.objects.create(
                center=center, name=r_name, max_capacity=capacity, room_surface=0
            )

        for _ in range(4):
            e_user = User.objects.create_user(
                email=f"educator{edu_counter}@nova.com",
                password="password123",
                full_name=f"Educator {FIRST_NAMES[edu_counter]}",
                phone_number=f"555-03{edu_counter:02d}",
                role_type="educator",
            )
            Educator.objects.create(
                user=e_user, center=center, is_active_in_ratio=True, is_compliant=True
            )
            edu_counter += 1

    print("Creating Parents...")
    parents = []
    for i in range(40):
        p_user = User.objects.create_user(
            email=f"parent{i+1}@test.com",
            password="password123",
            full_name=f"{random.choice(FIRST_NAMES)} {LAST_NAMES[i % len(LAST_NAMES)]}",
            phone_number=f"555-04{i:02d}",
            role_type="parent",
        )
        pp = ParentProfile.objects.create(
            user=p_user, home_address=f"{i*10} Maple Drive"
        )
        parents.append(pp)

    print("Creating Children and Relationships...")
    today = date.today()
    parent_index = 0

    for center in centers:
        for i in range(20):
            if parent_index >= len(parents):
                parent_index = 0

            parent = parents[parent_index]
            p_last_name = parent.user.full_name.split(" ")[-1]

            age_category = random.choices(
                ["infant", "toddler", "preschool"], weights=[20, 30, 50], k=1
            )[0]

            if age_category == "infant":
                months = random.randint(3, 17)
                dob = today - timedelta(days=months * 30)
            elif age_category == "toddler":
                months = random.randint(18, 35)
                dob = today - timedelta(days=months * 30)
            else:
                years = random.randint(3, 5)
                dob = today - timedelta(days=years * 365)

            child = Child.objects.create(
                center=center,
                first_name=random.choice(FIRST_NAMES),
                last_name=p_last_name,
                birth_date=dob,
                status="waitlist",
            )

            ParentChildRelationship.objects.create(
                parent=parent,
                child=child,
                relationship_type=random.choice(["Mother", "Father", "Guardian"]),
                is_emergency_contact=True,
            )

            parent_index += 1

    admin = User.objects.create_superuser(
        email="admin@nova.com",
        password="password123",
        full_name="Super Admin",
        phone_number="555-9999",
        role_type="admin",
    )

    print("------------------------------------------------")
    print(f"Seed Complete.")
    print(f"Org 1 (2 Centers): {org1.name} (Owner: {owner_user_1.email})")
    print(f"Org 2 (1 Center):  {org2.name} (Owner: {owner_user_2.email})")
    print(f"Total Children:    {Child.objects.count()}")
    print(f"Admin User:        {admin.email}")
    print("------------------------------------------------")


if __name__ == "__main__":
    run_seed()
