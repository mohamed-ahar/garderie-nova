from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail  # hadi mzal mkhdemti biha
from django.db import models
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import Director, Educator, User
from reports.models import EnrollmentForm

from .forms import (AssignDirectorForm, CenterCreationForm,
                    DirectorCreationForm, RoomForm)
from .models import (Center, Child, Educator, Group, Notification,
                     Organization, ParentChildRelationship, ParentProfile,
                     Room, StaffAssignment, User)


@login_required(login_url="login")
def register_child_view(request):
    user = request.user
    if user.role_type != "parent":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        child_name = request.POST.get("child_name")
        birth_date = request.POST.get("birth_date")
        contact_phone = request.POST.get("contact_phone")
        contact_email = request.POST.get("contact_email")
        center_id = request.POST.get("center_id")

        # Determine Center
        center = None
        if center_id:
             center = Center.objects.filter(center_id=center_id).first()
        else:
             center = Center.objects.first()
        
        if not center:
             messages.error(request, "Aucune garderie disponible.")
             return redirect("dashboard_redirect")

        # Split name
        parts = child_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        # Create Child
        # Store contact info in medical_info as a temporary storage or metadata since Child model lacks these fields
        extra_info = {
            "waitlist_contact_phone": contact_phone,
            "waitlist_contact_email": contact_email
        }

        child = Child.objects.create(
            center=center,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            status="waitlist",
            medical_info=extra_info
        )

        # Create Relationship
        parent_profile = get_object_or_404(ParentProfile, user=user)
        ParentChildRelationship.objects.create(
            parent=parent_profile,
            child=child,
            relationship_type="Parent", 
            is_emergency_contact=True 
        )

        messages.success(request, "Enfant inscrit sur la liste d'attente avec succès.")
        return redirect("dashboard_redirect")

    centers = Center.objects.all()
    return render(request, "core/parents/register_child.html", {"centers": centers})

