from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from django.db.models import Prefetch
from .models import (
    Group,
    Room,
    Child,
    Educator,
    StaffAssignment,
    User,
    Center,
    ParentProfile,
    Notification
)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Organization, Center
from .forms import (
    CenterCreationForm,
    DirectorCreationForm,
    AssignDirectorForm,
    RoomForm,
)
from django.shortcuts import render, get_object_or_404
from .models import Center, Organization
from accounts.models import Educator, Director, User
from reports.models import EnrollmentForm
from django.core.mail import send_mail  # hadi mzal mkhdemti biha
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date

from accounts.models import User, ParentProfile
from dashboard.models import Center, Group, Child, ParentChildRelationship







@login_required
def get_notifications_api(request):
    notifications = request.user.notifications.all().order_by("-created_at")[:10]
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    data = {
        "count": unread_count,
        "notifications": [
            {
                "id": n.notif_id,
                "title": n.title,
                "message": n.message,
                "action_url": n.action_url,
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%b %d, %H:%M"),
            }
            for n in notifications
        ],
    }
    return JsonResponse(data)


@login_required
def mark_notification_read_api(request, notif_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, notif_id=notif_id, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required

from accounts.models import User, ParentProfile
from dashboard.models import Center, Child, ParentChildRelationship

@login_required
def import_children_csv(request, center_id):
    # Jbd l-center
    center = get_object_or_404(Center, pk=center_id)

    if request.method == "POST" and request.FILES.get("csv_file"):
        file = request.FILES["csv_file"]

        if not file.name.endswith(".csv"):
            messages.error(request, "Hada machi fichier CSV ❌")
            return redirect(request.path)

        try:
            decoded_file = file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded_file))

            # Normalize headers
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]

            success_count = 0

            with transaction.atomic():
                for row in reader:
                    # Parent User
                    parent_user, created = User.objects.get_or_create(
                        email=row["parent_email"].strip(),
                        defaults={
                            "full_name": row["parent_name"].strip(),
                            "role_type": "parent",
                            "phone_number": row.get("parent_phone", ""),
                            "is_active": True,
                        },
                    )
                    if created:
                        parent_user.set_password("Parent@123")
                        parent_user.save()

                    # Parent Profile
                    parent_profile, _ = ParentProfile.objects.get_or_create(
                        user=parent_user,
                        defaults={"home_address": row.get("address", "Not Provided")},
                    )

                    # Child (direct active, mab9ach waitlist)
                    child = Child.objects.create(
                        first_name=row["first_name"].strip(),
                        last_name=row["last_name"].strip(),
                        birth_date=parse_date(row["birth_date"].strip()),
                        center=center,
                        address=row.get("address", ""),
                        status="active",  # <--- daba ghadi ykoun active direct
                    )

                    # Relationship
                    ParentChildRelationship.objects.get_or_create(
                        parent=parent_profile,
                        child=child,
                        defaults={"relationship_type": row.get("relation", "Parent")},
                    )

                    success_count += 1

            messages.success(
                request,
                f"{success_count} children imported successfully ✅"
            )
            return redirect("director_dashboard")  # ola page li bghiti

        except Exception as e:
            messages.error(request, f"Import error: {str(e)} ❌")

    return render(request, "import_csv.html", {"center": center})


