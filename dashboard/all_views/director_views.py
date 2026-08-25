from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
import csv
from datetime import datetime

from ..models import (
    Room,
    Center,
    Organization,
    Child,
    ParentChildRelationship,
    CenterParentAccess,
    Notification,
    TransferRequest,
)

from ..forms import (
    CenterCreationForm,
    DirectorCreationForm,
    AssignDirectorForm,
    RoomForm,
    CSVUploadForm,
)

from accounts.models import User, ParentProfile


# -----------------------------------------------center__info---------------------------------------------------------------------------------
@login_required
def create_center(request):
    if request.user.role_type != "owner":
        return redirect("login")

    organization = get_object_or_404(Organization, owner__user=request.user)

    if request.method == "POST":
        form = CenterCreationForm(request.POST)
        if form.is_valid():
            center = form.save(commit=False)
            center.organization = organization
            center.save()
            # Redirect to the success page instead of the dashboard
            return redirect("center_success", center_id=center.center_id)
    else:
        form = CenterCreationForm()

    return render(
        request,
        "core/owner/create_center.html",
        {"form": form, "organization": organization},
    )


@login_required
def center_success(request, center_id):
    # Fetch the newly created center to show its name
    center = get_object_or_404(
        Center, center_id=center_id, organization__owner__user=request.user
    )
    return render(request, "core/owner/center_congrats.html", {"center": center})


@login_required
def center_info_view(request, center_id):
    # Security Check: Njibou l-center b l-ID walakin khass darouri
    # ikoun taba3 l-organization dial dak l-user li m-connecti.
    center = get_object_or_404(
        Center, center_id=center_id, organization__owner__user=request.user
    )

    return render(request, "core/owner/center_info.html", {"center": center})


# Ila bghiti lista kamla dial les centers dial dak l-owner:
@login_required
def owner_centers_list(request):
    # 'select_related' kat-jib l-data dyal org u director f query whda (Performance)
    centers = Center.objects.filter(
        organization__owner__user=request.user
    ).select_related("organization", "director", "director__user")
    quick_assign_centers = Center.objects.filter(
        organization__owner__user=request.user, director__isnull=True
    )
    # Hna n-qdrou n-7sbo ch7al men center 3ando
    centers_count = centers.count()

    return render(
        request,
        "core/owner/centers_list.html",
        {"centers": centers, "centers_count": centers_count, "quick_assign_centers": quick_assign_centers},
    )



# ---------------------------------------------------------diractor__info-----------------------------------------------------------------------
# hna dyal send email sir setting 3endak tensa
@login_required
def create_director_general(request):
    if request.method == "POST":
        # Pass request.user bach n-rbeto l-director b l-owner
        form = DirectorCreationForm(request.POST, user=request.user)
        if form.is_valid():
            director = form.save()
            return redirect("owner_centers_list")
    else:
        form = DirectorCreationForm(user=request.user)

    return render(request, "core/owner/create_director.html", {"form": form})


def assign_director_to_center(request, center_id):
    # Kan-jibo l-center w t-akked m-rbot b l-org dyal had l-user
    center = get_object_or_404(
        Center, center_id=center_id, organization__owner__user=request.user
    )

    if request.method == "POST":
        # Pass user to form in POST
        form = AssignDirectorForm(request.POST, instance=center, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("owner_centers_list")
    else:
        # Pass user to form in GET zebi hna finkenti nasiha
        form = AssignDirectorForm(instance=center, user=request.user)

    return render(
        request, "core/owner/assign_director.html", {"form": form, "center": center}
    )


@login_required(login_url="login")
def room_list_view(request):
    user = request.user
    rooms = Room.objects.all()
    print(rooms, user)
    if user.role_type == "owner":
        rooms = Room.objects.all().select_related("center")
    elif user.role_type == "director" and hasattr(user, "director_profile"):
        center = user.director_profile.managed_center
        if center:
            rooms = Room.objects.filter(center=center)
    elif user.role_type == "educator" and hasattr(user, "educator_profile"):
        center = user.educator_profile.center
        if center:
            rooms = Room.objects.filter(center=center)

    context = {"rooms": rooms}
    return render(request, "core/rooms/room_list.html", context)


@login_required(login_url="login")
def room_create_view(request):
    user = request.user

    # 1. Strict Permission Check
    if user.role_type not in ["owner", "director"]:
        return render(request, "core/403.html", status=403)

    # 2. Logic to identify the Target Center (Context)
    # Used for read-only display or pre-filling
    preselected_center = None

    if user.role_type == "director":
        # Safety: Ensure director actually has a profile/center linked
        try:
            preselected_center = user.director_profile.managed_center
        except AttributeError:
            messages.error(request, "Your account is not linked to a center.")
            return redirect("dashboard_redirect")

    elif user.role_type == "owner":
        # If clicked from a "Center Detail" page, grabbing ID from URL
        # e.g., /rooms/create/?center_id=5
        cid_param = request.GET.get("center_id")
        if cid_param:
            preselected_center = get_object_or_404(Center, center_id=cid_param)

    # 3. Form Handling
    if request.method == "POST":
        form = RoomForm(request.POST)

        # Determine the Center being assigned during Save
        center_to_assign = None

        if user.role_type == "director":
            # Director: FORCE the center from their profile (ignore POST data manipulation)
            center_to_assign = preselected_center

        elif user.role_type == "owner":
            # Owner: Use the center from the dropdown selection in the POST
            selected_id = request.POST.get("center_id")
            if selected_id:
                center_to_assign = get_object_or_404(Center, center_id=selected_id)

        # Validation and Save
        if form.is_valid():
            if center_to_assign:
                room = form.save(commit=False)
                room.center = center_to_assign

                # Note: Model's .save() method will handle calculating
                # default capacity based on the Age Group if logic is in models.py
                room.save()

                messages.success(request, f"Room '{room.name}' created successfully.")
                return redirect("room_list")
            else:
                form.add_error(None, "You must select a valid Center.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request
        form = RoomForm()

    # 4. Context Data Preparation
    # Owners need a list of centers for the dropdown
    centers = Center.objects.all() if user.role_type == "owner" else []

    context = {
        "form": form,
        "centers": centers,  # For the <select> dropdown (Owners)
        "target_center": preselected_center,  # For the Read-Only text (Directors or Pre-filled)
        "room": None,  # Ensures template knows this is Create, not Edit
    }

    return render(request, "core/rooms/room_form.html", context)


@login_required(login_url="login")
def room_edit_view(request, room_id):
    user = request.user
    room = get_object_or_404(Room, room_id=room_id)

    # Permission check
    if user.role_type == "owner":
        pass  # Owners can edit any room
    elif user.role_type == "director" and hasattr(user, "director_profile"):
        if room.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    else:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect("room_list")
    else:
        form = RoomForm(instance=room)

    context = {"form": form, "room": room}
    return render(request, "core/rooms/room_form.html", context)


@login_required(login_url="login")
def room_delete_view(request, room_id):
    user = request.user
    room = get_object_or_404(Room, room_id=room_id)

    # Permission check
    if user.role_type == "owner":
        pass  # Owners can delete any room
    elif user.role_type == "director" and hasattr(user, "director_profile"):
        if room.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    else:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        room.delete()
        return redirect("room_list")

    return render(request, "core/rooms/room_confirm_delete.html", {"room": room})

@login_required(login_url="login")
def import_children_csv(request):
    if request.user.role_type != "director":
        return render(request, "core/403.html", status=403)

    try:
        center = request.user.director_profile.managed_center
        if not center:
             messages.error(request, "You are not assigned to any center.")
             return redirect("dashboard_redirect")
    except AttributeError:
        messages.error(request, "Director profile not found.")
        return redirect("dashboard_redirect")

    form = CSVUploadForm(request.POST or None, request.FILES or None)
    
    if request.method == "POST" and form.is_valid():
        csv_file = form.cleaned_data["file"]
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        errors = []
        added_children = 0

        try:
            with transaction.atomic():
                for i, row in enumerate(reader, start=2):
                    email = row.get("parent_email", "").strip()
                    if not email:
                        errors.append(f"Line {i}: Missing parent email")
                        continue

                    user, user_created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "email": email,
                            "full_name": row.get("parent_full_name", "No Name"),
                            "role_type": "parent"
                        }
                    )
                    
                    if user_created:
                        user.set_unusable_password()
                        user.save()

                    parent_profile, _ = ParentProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            "home_address": row.get("parent_home_address", ""),
                            "billing_reference": row.get("parent_billing_reference", "")
                        }
                    )

                    try:
                        date_str = row.get("child_birth_date", "")
                        birth_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        errors.append(f"Line {i}: Invalid birth date format ({date_str})")
                        continue

                    child = Child.objects.create(
                        center=center,
                        first_name=row.get("child_first_name", ""),
                        last_name=row.get("child_last_name", ""),
                        birth_date=birth_date
                    )
                    
                    ParentChildRelationship.objects.create(
                        parent=parent_profile,
                        child=child,
                        relationship_type="Parent",
                        is_emergency_contact=True 
                    )
                    
                    added_children += 1

        except Exception as e:
            messages.error(request, f"System Error: {str(e)}")
            return redirect("import_children_csv")

        if errors:
            for e in errors: messages.error(request, e)
        else:
            messages.success(request, f"Successfully imported {added_children} children.")

        return redirect("import_children_csv")

    return render(request, "core/director/import_children.html", {"form": form})


@login_required(login_url="login")
def manage_parent_access_requests(request):
    user = request.user
    if user.role_type != "director":
        return render(request, "core/403.html", status=403)
    
    try:
        center = user.director_profile.managed_center
        if not center:
             messages.error(request, "You are not assigned to any center.")
             return redirect("dashboard_redirect")
    except AttributeError:
        messages.error(request, "Director profile not found.")
        return redirect("dashboard_redirect")

    requests = CenterParentAccess.objects.filter(center=center).order_by('-created_at')
    
    return render(request, "core/director/manage_access_requests.html", {
        "access_requests": requests
    })

@login_required(login_url="login")
def update_parent_access(request, request_id):
    user = request.user
    if user.role_type != "director":
        return render(request, "core/403.html", status=403)
        
    access_request = get_object_or_404(CenterParentAccess, id=request_id)
    
    # Check if this request belongs to the director's center
    try:
        center = user.director_profile.managed_center
        if access_request.center != center:
             return render(request, "core/403.html", status=403)
    except AttributeError:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'accept':
            access_request.status = 'accepted'
            access_request.save()
            messages.success(request, f"Access granted to {access_request.parent.user.full_name}.")
            
            # Notify Parent
            Notification.objects.create(
                user=access_request.parent.user,
                title="Accès accordé",
                message=f"Votre demande d'accès au centre {center.name} a été acceptée.",
                action_url="/parents/register-child/" 
            )

        elif action == 'reject':
            access_request.status = 'rejected'
            access_request.save()
            messages.success(request, f"Access rejected for {access_request.parent.user.full_name}.")
            
            # Notify Parent
            Notification.objects.create(
                user=access_request.parent.user,
                title="Accès refusé",
                message=f"Votre demande d'accès au centre {center.name} a été refusée.",
                action_url="/parents/request-access/"
            )
            
        elif action == 'revoke':
             access_request.delete()
             messages.success(request, f"Access revoked for {access_request.parent.user.full_name}.")
             
    return redirect("manage_parent_access_requests")

@login_required(login_url="login")
def child_list_view(request):
    user = request.user
    if user.role_type != "director":
        return render(request, "core/403.html", status=403)
    
    try:
        center = user.director_profile.managed_center
        if not center:
             messages.error(request, "You are not assigned to any center.")
             return redirect("dashboard_redirect")
    except AttributeError:
        messages.error(request, "Director profile not found.")
        return redirect("dashboard_redirect")

    children = Child.objects.filter(center=center).exclude(status='waitlist').select_related('assigned_group', 'assigned_educator', 'assigned_educator__user').order_by('first_name')

    return render(request, "core/director/child_list.html", {
        "children": children,
        "center": center
    })


@login_required(login_url="login")
def transfer_requests_list(request):
    user = request.user
    if user.role_type != "director":
        return render(request, "core/403.html", status=403)
        
    try:
        center = user.director_profile.managed_center
    except AttributeError:
        messages.error(request, "Director profile not found or no center assigned.")
        return redirect("dashboard_redirect")
        
    if not center:
        messages.error(request, "No center assigned.")
        return redirect("dashboard_redirect")
        
    # Incoming: requests where target_center is this center
    incoming = TransferRequest.objects.filter(target_center=center).select_related('child', 'child__center').order_by('-requested_at')
    
    # Outgoing: requests where child.center is this center
    outgoing = TransferRequest.objects.filter(child__center=center).select_related('child', 'target_center').order_by('-requested_at')
    
    context = {
        "incoming_requests": incoming,
        "outgoing_requests": outgoing
    }
    return render(request, "core/director/transfer_requests_list.html", context)


@login_required(login_url="login")
def process_transfer_request(request, request_id):
    user = request.user
    if user.role_type != "director":
        return render(request, "core/403.html", status=403)
        
    transfer_req = get_object_or_404(TransferRequest, request_id=request_id)
    
    try:
        center = user.director_profile.managed_center
    except AttributeError:
         return render(request, "core/403.html", status=403)
         
    # Identify Role
    is_incoming = (transfer_req.target_center == center)
    is_outgoing = (transfer_req.child.center == center)
    
    if not is_incoming and not is_outgoing:
         messages.error(request, "You are not authorized to process this request.")
         return redirect("transfer_requests_list")
         
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "approve":
            with transaction.atomic():
                if is_incoming:
                    transfer_req.approved_by_incoming = True
                if is_outgoing:
                    transfer_req.approved_by_outgoing = True
                
                transfer_req.save()
                
                # Check if both approved
                if transfer_req.approved_by_incoming is True and transfer_req.approved_by_outgoing is True:
                    transfer_req.status = 'awaiting_signature'
                    transfer_req.save()
                    
                    # Notify All Parents to Sign
                    parents_rels = ParentChildRelationship.objects.filter(child=transfer_req.child).select_related('parent__user')
                    for rel in parents_rels:
                         Notification.objects.create(
                            user=rel.parent.user,
                            title="Transfer Approved - Signature Required",
                            message=f"Both directors have approved the transfer for {transfer_req.child.first_name}. Please sign the transfer document to finalize the move to {transfer_req.target_center.name}.",
                            action_url="/parents/transfer-request/"
                        )
                    messages.success(request, "Transfer approved by both directors. All parents have been notified to sign.")
                else:
                    messages.success(request, "Transfer approved from your side. Waiting for the other director's approval.")
            
        elif action == "reject":
            transfer_req.status = 'rejected'
            if is_incoming:
                transfer_req.approved_by_incoming = False
            elif is_outgoing:
                transfer_req.approved_by_outgoing = False
            
            transfer_req.save()
            
            # Notify All Parents
            parents_rels = ParentChildRelationship.objects.filter(child=transfer_req.child).select_related('parent__user')
            for rel in parents_rels:
                 Notification.objects.create(
                    user=rel.parent.user,
                    title="Transfer Rejected",
                    message=f"Your transfer request for {transfer_req.child.first_name} to {transfer_req.target_center.name} has been rejected.",
                    action_url="/parents/transfer-request/"
                )
            
            messages.success(request, "Transfer request rejected.")
            
    return redirect("transfer_requests_list")