from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction # Zid had l-import l-foq
from django.contrib.auth.hashers import make_password
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
    ViceDirectorCreationForm,
    ViceDirectorForm,

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
from django.db import transaction
from django.contrib.auth.decorators import login_required
from accounts.models import User, ViceDirector, Director
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date

from accounts.models import User,Director, ViceDirector, ParentProfile
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


@login_required
def edit_center(request, center_id):
    # Security: Ensure center belongs to the owner
    center = get_object_or_404(
        Center, center_id=center_id, organization__owner__user=request.user
    )
    
    if request.method == "POST":
        # 'instance=center' tells Django to update this specific record
        form = CenterCreationForm(request.POST, instance=center)
        if form.is_valid():
            form.save()
            messages.success(request, f"Center '{center.name}' updated successfully!")
            return redirect("owner_centers_list")
    else:
        form = CenterCreationForm(instance=center)

    return render(
        request,
        "core/owner/edit_center.html", 
        {"form": form, "center": center}
    )

@login_required
def delete_center(request, center_id):
    # Security: Ensure center belongs to the owner
    center = get_object_or_404(
        Center, center_id=center_id, organization__owner__user=request.user
    )
    
    if request.method == "POST":
        center_name = center.name
        center.delete()
        messages.warning(request, f"Center '{center_name}' has been removed.")
        return redirect("owner_centers_list")
    
    # Optional: Render a confirmation page for GET requests
    return render(request, "core/owner/delete_confirm.html", {"center": center})
@login_required
def list_directors(request):
    # 1. Khass njibu l-Organization dyal had l-Owner
    owner_org = request.user.owner_profile.owned_organization 

    # 2. Njibu ay Director m-lyé m3a had l-org
    # Sawa2an kan Director mn l-bedya aw t-promota mn Vice
    directors = Director.objects.filter(
        organization=owner_org
    ).select_related('user', 'managed_center').order_by('-user__date_joined')

    # 3. Njibu l-Centers li mazzal ma 3ndhomch Director bach n-assigniw l-jdad
    from .models import Center
    available_centers = Center.objects.filter(
        organization=owner_org,
        director__isnull=True
    )

    context = {
        'directors': directors,
        'available_centers': available_centers
    }
    return render(request, 'core/owner/list_directors.html', context)

@login_required
def director_profile(request, director_id):
    """
    View bach l-owner y-chouf l-profile dyal wahed l-director kamil.
    """
    # Security: Kan-choufo ghi l-director li taba3 l-had l-owner
    director = get_object_or_404(
        Director.objects.select_related('user', 'managed_center', 'organization'),
        user_id=director_id,
        organization__owner__user=request.user
    )
    
    return render(request, 'core/owner/director_profile.html', {'director': director})

@login_required
def delete_director(request, director_id):
    director = get_object_or_404(
        Director, user_id=director_id, organization__owner__user=request.user
    )
    
    if request.method == "POST":
        user = director.user
        user_name = user.full_name
        user.delete() 
        messages.warning(request, f"The account for {user_name} has been removed.")
        return redirect("list_directors")
    
    return render(request, "core/owner/delete_director_confirm.html", {"director": director})
@login_required
def list_vice_directors(request):
    owner_profile = getattr(request.user, 'owner_profile', None)
    
    if not owner_profile:
        messages.error(request, "Access denied. Owner profile not found.")
        return redirect('login')

    # L-farq hna: Ghan-filteriw hta b l-user__role_type
    # Bach ila wella Director, wakha ybqa lih profile ViceDirector, may-ban-sh hna
    vice_directors = ViceDirector.objects.filter(
        organization=owner_profile.owned_organization,
        user__role_type='vice_director'  # <--- HAD l-filter howa li gha-y-ghaber l-promoted people
    ).select_related('user', 'center')
 
    return render(request, 'core/owner/list_vice_directors.html', {
        'vice_directors': vice_directors
    })
@login_required
def add_vice_director(request):
    owner_profile = getattr(request.user, 'owner_profile', None)
    org = owner_profile.owned_organization if owner_profile else None

    if not org:
        messages.error(request, "You must be linked to an organization to add staff.")
        return redirect('owner_dashboard')

    if request.method == 'POST':
        form = ViceDirectorCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the User
                    user = User.objects.create_user(
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        full_name=form.cleaned_data['full_name'],
                        role_type='vice_director'
                    )
                    
                    # Create ViceDirector profile linked to THIS organization
                    ViceDirector.objects.create(
                        user=user, 
                        organization=org, # Hna l-farq: dima m-lyé m3a l-Owner
                        center=None
                    )
                    
                messages.success(request, f"Vice Director {user.full_name} added to {org.name}.")
                return redirect('list_vice_directors')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = ViceDirectorCreationForm()
    
    return render(request, 'core/owner/add_vice_director.html', {'form': form})
@login_required
@transaction.atomic
def switch_staff_role(request, user_id):
    if request.method == "POST":
        target_user = get_object_or_404(User, user_id=user_id)
        owner_profile = getattr(request.user, 'owner_profile', None)
        owner_org = owner_profile.owned_organization if owner_profile else None
            
        if target_user.role_type == 'vice_director':
            # --- PROMOTE ---
            target_user.role_type = 'director' # Role f User model kiwelli Director
            target_user.save()

            # Mseh l-vice profile bach may-bqa t-wahed ychoufou
            ViceDirector.objects.filter(user=target_user).delete()
            
            # Crea Director profile
            Director.objects.update_or_create(
                user=target_user,
                defaults={'organization': owner_org}
            )
            
            messages.success(request, f"{target_user.full_name} is now a Director.")
            return redirect('list_directors')

        elif target_user.role_type == 'director':
            # --- DEMOTE ---
            target_user.role_type = 'vice_director'
            target_user.save()

            Director.objects.filter(user=target_user).delete()
            
            ViceDirector.objects.update_or_create(
                user=target_user, 
                defaults={'organization': owner_org}
            )

            messages.warning(request, f"{target_user.full_name} returned to Vice rank.")
            return redirect('list_vice_directors')

    return redirect('owner_dashboard')
@login_required
def edit_vice_director(request, vice_id):
    vd = get_object_or_404(ViceDirector, user_id=vice_id, center__organization__owner__user=request.user)
    user = vd.user
    
    if request.method == "POST":
        user.full_name = request.POST.get('full_name')
        user.phone_number = request.POST.get('phone_number')
        vd.center_id = request.POST.get('center')
        user.save()
        vd.save()
        messages.success(request, "Updated successfully!")
        return redirect('list_vice_directors')
    
    centers = request.user.owner_profile.owned_organization.centers.all()
    return render(request, 'core/owner/edit_vice_director.html', {'vd': vd, 'centers': centers})

@login_required
def delete_vice_director(request, vice_id):
    vd = get_object_or_404(ViceDirector, user_id=vice_id, center__organization__owner__user=request.user)
    if request.method == "POST":
        vd.user.delete() # CASCADE ghadi ymsah l-profile m3ah
        return redirect('list_vice_directors')
    return render(request, 'core/owner/delete_vice_confirm.html', {'vd': vd})
