from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import (
    Room,
    Center,
    Organization,
)

from ..forms import (
    CenterCreationForm,
    DirectorCreationForm,
    AssignDirectorForm,
    RoomForm,
)


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
            center.orginisation = organization
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

    # Hna n-qdrou n-7sbo ch7al men center 3ando
    centers_count = centers.count()

    return render(
        request,
        "core/owner/centers_list.html",
        {"centers": centers, "centers_count": centers_count},
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
