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
from django.core.mail import send_mail  # hadi mzal mkhdemti biha
from django.conf import settings
from django.contrib import messages
from django.utils import timezone


@login_required(login_url="login")
def dashboard_view(request):
    context = {
        "total_attendance": 142,
        "capacity": 160,
        "occupancy_percentage": 88,
        "pending_signatures": 4,
        "compliance_rate": 92,
        "observations": 842,
    }
    return render(request, "core/dashboard.html", context)


@login_required(login_url="login")
def group_add_view(request):
    user = request.user

    # Basic permission check
    if user.role_type not in ["owner", "director"]:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        name = request.POST.get("name")
        room_id = request.POST.get("room_id")
        center_id = request.POST.get("center_id")

        # Determine Center
        target_center = None
        if user.role_type == "owner":
            if center_id:
                target_center = get_object_or_404(Center, center_id=center_id)
        elif user.role_type == "director":
            target_center = user.director_profile.managed_center

        if target_center:
            room = None
            if room_id:
                room = get_object_or_404(Room, room_id=room_id, center=target_center)

            Group.objects.create(name=name, room=room, center=target_center)
            return redirect("group_list")
        else:
            return render(
                request,
                "core/groups/group_form.html",
                {"error": "Center not found for assignment."},
            )

    # GET
    centers = []
    rooms = []
    if user.role_type == "owner":
        centers = Center.objects.all()
        # If owner, maybe we need to load rooms via AJAX or just show all for now?
        # Typically rooms depend on center.
        rooms = Room.objects.all()
    elif user.role_type == "director":
        target_center = user.director_profile.managed_center
        if target_center:
            rooms = Room.objects.filter(center=target_center)

    return render(
        request, "core/groups/group_form.html", {"centers": centers, "rooms": rooms}
    )


@login_required(login_url="login")
def group_list_view(request):
    user = request.user
    groups = Group.objects.none()

    if user.role_type == "owner":
        groups = Group.objects.all().select_related("room", "center")
    elif user.role_type == "director" and hasattr(user, "director_profile"):
        center = user.director_profile.managed_center
        if center:
            groups = Group.objects.filter(center=center).select_related("room")
    elif user.role_type == "educator" and hasattr(user, "educator_profile"):
        center = user.educator_profile.center
        if center:
            groups = Group.objects.filter(center=center).select_related("room")

    context = {"groups": groups}
    return render(request, "core/groups/group_list.html", context)


@login_required(login_url="login")
def group_edit_view(request, group_id):
    group = get_object_or_404(Group, group_id=group_id)
    user = request.user

    # Permission check
    if user.role_type == "director" and hasattr(user, "director_profile"):
        if group.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_details":
            name = request.POST.get("name")
            room_id = request.POST.get("room_id")
            if name:
                group.name = name
            if room_id:
                room = get_object_or_404(Room, room_id=room_id)
                if room.center == group.center:
                    group.room = room
            group.save()

        elif action == "assign_educator":
            user_id = request.POST.get("user_id")
            educator = get_object_or_404(Educator, user__user_id=user_id)
            StaffAssignment.objects.filter(educator=educator, is_active=True).update(
                is_active=False
            )
            StaffAssignment.objects.create(
                educator=educator, group=group, is_active=True
            )

            group.current_educators = StaffAssignment.objects.filter(
                group=group, is_active=True
            ).count()
            educator.recalculate_compliance()
            group.recalculate_ratios()

        elif action == "remove_educator":
            user_id = request.POST.get("user_id")
            educator = get_object_or_404(Educator, user__user_id=user_id)
            # Remove all children assigned to this educator
            children = Child.objects.filter(
                assigned_educator=educator, assigned_group=group
            )
            children.update(assigned_educator=None)
            # Remove educator from group
            StaffAssignment.objects.filter(
                group=group, educator=educator, is_active=True
            ).update(is_active=False)
            group.current_educators = StaffAssignment.objects.filter(
                group=group, is_active=True
            ).count()
            group.recalculate_ratios()

        elif action == "assign_child":
            child_id = request.POST.get("child_id")
            child = get_object_or_404(Child, child_id=child_id)
            old_group = child.assigned_group
            child.assigned_group = group
            child.save()
            group.recalculate_ratios()
            if old_group:
                old_group.recalculate_ratios()

        elif action == "remove_child":
            child_id = request.POST.get("child_id")
            child = get_object_or_404(Child, child_id=child_id)
            if child.assigned_group == group:
                child.assigned_group = None
                child.assigned_educator = None
                child.save()
                group.recalculate_ratios()

        elif action == "assign_child_educator":
            child_id = request.POST.get("child_id")
            educator_id = request.POST.get("educator_id")
            child = get_object_or_404(Child, child_id=child_id)
            if child.assigned_group == group:
                # Remove from old educator if any
                if child.assigned_educator:
                    old_educator = child.assigned_educator
                    child.assigned_educator = None
                    child.save()
                    old_educator.recalculate_compliance()

                # Assign to new educator if provided
                if educator_id:
                    educator = get_object_or_404(Educator, user__user_id=educator_id)
                    child.assigned_educator = educator
                    child.save()
                    educator.recalculate_compliance()
                else:
                    child.save()

                group.recalculate_ratios()

        return redirect("group_edit", group_id=group_id)

    assigned_educators = Educator.objects.filter(
        assignments__group=group, assignments__is_active=True
    ).select_related("user")

    # Recalculate compliance for all assigned educators
    for educator in assigned_educators:
        educator.recalculate_compliance()

    assigned_children = (
        group.enrolled_children.all()
        .select_related("assigned_educator__user")
        .order_by("first_name")
    )

    all_rooms = Room.objects.filter(center=group.center)

    # Educators not currently assigned to THIS group it could be in other groups
    other_educators = (
        Educator.objects.filter(center=group.center)
        .exclude(assignments__group=group, assignments__is_active=True)
        .select_related("user")
    )

    # Children not in this group
    other_children = (
        Child.objects.filter(center=group.center)
        .exclude(assigned_group=group)
        .order_by("first_name")
    )

    context = {
        "group": group,
        "rooms": all_rooms,
        "assigned_educators": assigned_educators,
        "assigned_children": assigned_children,
        "other_educators": other_educators,
        "other_children": other_children,
        "is_edit": True,
    }
    return render(request, "core/groups/group_manage.html", context)


@login_required(login_url="login")
def group_delete_view(request, group_id):
    group = get_object_or_404(Group, group_id=group_id)
    user = request.user

    # Permission check
    if user.role_type == "director" and hasattr(user, "director_profile"):
        if group.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        # Clear educator assignments for children in this group
        group.enrolled_children.all().update(assigned_educator=None)

        group.delete()
        return redirect("group_list")

    return render(request, "core/403.html", status=403)


@login_required(login_url="login")
def educator_list_view(request):
    user = request.user
    educators = Educator.objects.none()
    centers = []

    if user.role_type == "owner":
        educators = Educator.objects.all().select_related("user", "center")
        centers = Center.objects.all()
    elif user.role_type in ["director", "vice_director"]:
        if user.role_type == "director" and hasattr(user, "director_profile"):
            center = user.director_profile.managed_center
            if center:
                educators = Educator.objects.filter(center=center).select_related(
                    "user"
                )
        elif user.role_type == "vice_director" and hasattr(
            user, "vice_director_profile"
        ):
            center = user.vice_director_profile.center
            if center:
                educators = Educator.objects.filter(center=center).select_related(
                    "user"
                )

    # Recalculate compliance for all educators
    for educator in educators:
        educator.recalculate_compliance()

    context = {"educators": educators, "centers": centers}
    return render(request, "core/educators/educator_list.html", context)


@login_required(login_url="login")
def educator_add_view(request):
    user = request.user

    # Basic permission check
    if user.role_type not in ["owner", "director", "vice_director"]:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        password = request.POST.get(
            "password"
        )  # In a real app, generate or email set link
        center_id = request.POST.get("center_id")

        is_ajax = request.headers.get(
            "x-requested-with"
        ) == "XMLHttpRequest" or "application/json" in request.META.get(
            "HTTP_ACCEPT", ""
        )

        # Validation (simplistic)
        if User.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse(
                    {"status": "error", "message": "Email already exists."}, status=400
                )
            return render(
                request,
                "core/educators/educator_form.html",
                {
                    "error": "Email already exists.",
                    "centers": (
                        Center.objects.all() if user.role_type == "owner" else []
                    ),
                },
            )

        # Create User
        try:
            new_user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role_type="educator",
            )
            new_user.phone_number = phone_number
            new_user.save()

            # Determine Center
            target_center = None
            if user.role_type == "owner":
                target_center = get_object_or_404(Center, center_id=center_id)
            elif user.role_type == "director":
                target_center = user.director_profile.managed_center
            elif user.role_type == "vice_director":
                target_center = user.vice_director_profile.center

            if target_center:
                Educator.objects.create(user=new_user, center=target_center)
                if is_ajax:
                    return JsonResponse(
                        {"status": "success", "message": "Educator added successfully."}
                    )
                return redirect("educator_list")
            else:
                # Rollback user creation if center issue? Or just show error.
                new_user.delete()
                if is_ajax:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Center not found for assignment.",
                        },
                        status=400,
                    )
                return render(
                    request,
                    "core/educators/educator_form.html",
                    {"error": "Center not found for assignment."},
                )
        except Exception as e:
            if is_ajax:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
            raise e

    # GET
    centers = []
    if user.role_type == "owner":
        centers = Center.objects.all()

    return render(request, "core/educators/educator_form.html", {"centers": centers})


@login_required(login_url="login")
def educator_detail_view(request, user_id):
    user = request.user
    educator_profile = get_object_or_404(Educator, user__user_id=user_id)

    # Permission check
    if user.role_type == "director":
        if educator_profile.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    elif user.role_type == "vice_director":
        if educator_profile.center != user.vice_director_profile.center:
            return render(request, "core/403.html", status=403)
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    # Recalculate compliance for this educator
    educator_profile.recalculate_compliance()

    active_assignment = educator_profile.assignments.filter(is_active=True).first()
    assigned_children = educator_profile.assigned_children.all()

    context = {
        "educator": educator_profile,
        "active_assignment": active_assignment,
        "assigned_children": assigned_children,
    }
    return render(request, "core/educators/educator_detail.html", context)


@login_required(login_url="login")
def educator_edit_view(request, user_id):
    user = request.user
    educator_profile = get_object_or_404(Educator, user__user_id=user_id)
    educator_user = educator_profile.user

    # Permission check
    if user.role_type == "director":
        if educator_profile.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    elif user.role_type == "vice_director":
        if educator_profile.center != user.vice_director_profile.center:
            return render(request, "core/403.html", status=403)
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")

        educator_user.full_name = full_name
        educator_user.email = email
        educator_user.phone_number = phone_number
        educator_user.save()

        return redirect("educator_list")

    return render(
        request,
        "core/educators/educator_form.html",
        {"educator": educator_profile, "is_edit": True},
    )


@login_required(login_url="login")
def educator_delete_view(request, user_id):
    user = request.user
    educator_profile = get_object_or_404(Educator, user__user_id=user_id)

    if user.role_type == "director":
        if educator_profile.center != user.director_profile.managed_center:
            return render(request, "core/403.html", status=403)
    elif user.role_type == "vice_director":
        if educator_profile.center != user.vice_director_profile.center:
            return render(request, "core/403.html", status=403)
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        educator_profile.user.delete()
        return redirect("educator_list")

    return render(request, "core/403.html", status=403)


@login_required(login_url="login")
def parent_list_view(request):
    user = request.user
    parents = ParentProfile.objects.none()
    centers = []

    if user.role_type == "owner":
        parents = ParentProfile.objects.all().select_related("user")
        centers = Center.objects.all()
    elif user.role_type in ["director", "vice_director"]:
        if user.role_type == "director" and hasattr(user, "director_profile"):
            center = user.director_profile.managed_center
            if center:
                parents = (
                    ParentProfile.objects.filter(user__center_association__in=[center])
                    .select_related("user")
                    .distinct()
                    if hasattr(ParentProfile, "center")
                    else ParentProfile.objects.all().select_related("user")
                )
        elif user.role_type == "vice_director" and hasattr(
            user, "vice_director_profile"
        ):
            center = user.vice_director_profile.center
            if center:
                parents = (
                    ParentProfile.objects.filter(user__center_association__in=[center])
                    .select_related("user")
                    .distinct()
                    if hasattr(ParentProfile, "center")
                    else ParentProfile.objects.all().select_related("user")
                )

    context = {"parents": parents, "centers": centers}
    return render(request, "core/parents/parent_list.html", context)


@login_required(login_url="login")
def parent_add_view(request):
    user = request.user

    # Basic permission check
    if user.role_type not in ["owner", "director", "vice_director"]:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        home_address = request.POST.get("home_address")
        billing_reference = request.POST.get("billing_reference")
        password = request.POST.get("password")

        is_ajax = request.headers.get(
            "x-requested-with"
        ) == "XMLHttpRequest" or "application/json" in request.META.get(
            "HTTP_ACCEPT", ""
        )

        # Validation
        if User.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse(
                    {"status": "error", "message": "Email already exists."}, status=400
                )
            return render(
                request,
                "core/parents/parent_form.html",
                {
                    "error": "Email already exists.",
                    "centers": (
                        Center.objects.all() if user.role_type == "owner" else []
                    ),
                },
            )

        # Create User
        try:
            new_user = User.objects.create_user(
                email=email, password=password, full_name=full_name, role_type="parent"
            )
            new_user.phone_number = phone_number
            new_user.save()

            # Create Parent Profile
            parent_profile = ParentProfile.objects.create(
                user=new_user,
                home_address=home_address,
                billing_reference=billing_reference,
            )

            if is_ajax:
                return JsonResponse(
                    {"status": "success", "message": "Parent added successfully."}
                )
            return redirect("parent_list")
        except Exception as e:
            if is_ajax:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
            raise e

    # GET
    centers = []
    if user.role_type == "owner":
        centers = Center.objects.all()

    return render(request, "core/parents/parent_form.html", {"centers": centers})


from .models import (
    Group,
    Room,
    Child,
    Educator,
    StaffAssignment,
    User,
    Center,
    ParentProfile,
    ParentChildRelationship,
)


@login_required(login_url="login")
def parent_detail_view(request, user_id):
    user = request.user
    parent_profile = get_object_or_404(ParentProfile, user__user_id=user_id)

    # Permission check
    if user.role_type == "director":
        if (
            hasattr(parent_profile.user, "center_association")
            and parent_profile.user.center_association
            != user.director_profile.managed_center
        ):
            # This check is a bit weak if parent isn't explicitly linked to center in model,
            # but we'll assume director can only see parents effectively in their scope if we had stricter checks.
            # For now, relying on list filtering. Here we might want to be safer.
            pass
    elif user.role_type == "vice_director":
        pass
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "assign_child":
            child_id = request.POST.get("child_id")
            relationship_type = request.POST.get("relationship_type", "Parent")
            is_emergency = request.POST.get("is_emergency") == "on"

            child = get_object_or_404(Child, child_id=child_id)

            # Create relationship if it doesn't exist
            ParentChildRelationship.objects.get_or_create(
                parent=parent_profile,
                child=child,
                defaults={
                    "relationship_type": relationship_type,
                    "is_emergency_contact": is_emergency,
                },
            )
            return redirect("parent_detail", user_id=user_id)

        elif action == "remove_child":
            child_id = request.POST.get("child_id")
            child = get_object_or_404(Child, child_id=child_id)
            ParentChildRelationship.objects.filter(
                parent=parent_profile, child=child
            ).delete()
            return redirect("parent_detail", user_id=user_id)

    # Get children associated with this parent
    children_relationships = parent_profile.children_relationships.select_related(
        "child"
    ).all()
    assigned_child_ids = children_relationships.values_list(
        "child__child_id", flat=True
    )

    # Get available children based on user role
    available_children = Child.objects.none()
    if user.role_type == "owner":
        available_children = Child.objects.exclude(
            child_id__in=assigned_child_ids
        ).order_by("first_name")
    elif user.role_type == "director" and hasattr(user, "director_profile"):
        center = user.director_profile.managed_center
        if center:
            available_children = (
                Child.objects.filter(center=center)
                .exclude(child_id__in=assigned_child_ids)
                .order_by("first_name")
            )

    context = {
        "parent": parent_profile,
        "children_relationships": children_relationships,
        "available_children": available_children,
    }
    return render(request, "core/parents/parent_detail.html", context)


@login_required(login_url="login")
def parent_edit_view(request, user_id):
    user = request.user
    parent_profile = get_object_or_404(ParentProfile, user__user_id=user_id)
    parent_user = parent_profile.user

    # Permission check
    if user.role_type == "director":
        pass
    elif user.role_type == "vice_director":
        pass
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        home_address = request.POST.get("home_address")
        billing_reference = request.POST.get("billing_reference")

        parent_user.full_name = full_name
        parent_user.email = email
        parent_user.phone_number = phone_number
        parent_user.save()

        parent_profile.home_address = home_address
        parent_profile.billing_reference = billing_reference
        parent_profile.save()

        return redirect("parent_list")

    return render(
        request,
        "core/parents/parent_form.html",
        {"parent": parent_profile, "is_edit": True},
    )


@login_required(login_url="login")
def parent_delete_view(request, user_id):
    user = request.user
    parent_profile = get_object_or_404(ParentProfile, user__user_id=user_id)

    if user.role_type == "director":
        pass
    elif user.role_type == "vice_director":
        pass
    elif user.role_type != "owner":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        parent_profile.user.delete()
        return redirect("parent_list")

    return render(request, "core/403.html", status=403)


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
    print(rooms,user)
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


@login_required(login_url="login")
def waitlist_view(request):
    user = request.user
    
    # Permission Check
    center = None
    if user.role_type == 'director':
        try:
            center = user.director_profile.managed_center
        except:
            return render(request, "core/403.html", status=403)
    elif user.role_type == 'owner':
        # Simple fallback for owner to view specific center if provided
        center_id = request.GET.get('center_id')
        if center_id:
             center = get_object_or_404(Center, center_id=center_id)
        else:
             # Just pick first one for now or show error
             center = Center.objects.first()
    else:
        return render(request, "core/403.html", status=403)

    if not center:
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        action = request.POST.get('action')
        child_id = request.POST.get('child_id')
        child = get_object_or_404(Child, child_id=child_id, center=center)

        if action == 'admit':
            child.status = 'active'
            child.save()
            for parent_child in ParentChildRelationship.objects.filter(child=child):
                Notification.objects.create(
                    user=parent_child.parent.user,
                    title="Child Admitted",
                    message=f"{child.first_name} {child.last_name} has been successfully admitted from the waitlist.",
                    is_read=False
                )
                print("Notification is created")
            messages.success(request, f"{child.first_name} admitted successfully.")
        elif action == 'remove':
             child.delete() 
             messages.success(request, f"{child.first_name} removed from waitlist.")
        
        return redirect('waitlist_manage')

    waitlist_children = Child.objects.filter(center=center, status='waitlist').order_by('created_at')

    context = {
        'waitlist': waitlist_children,
        'center': center
    }
    return render(request, "core/director/waitlist_manage.html", context)


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


@login_required(login_url="login")
def dashboard_view(request):
    context = {
        "total_attendance": 142,
        "capacity": 160,
        "occupancy_percentage": 88,
        "pending_signatures": 4,
        "compliance_rate": 92,
        "observations": 842,
    }
    return render(request, "core/dashboard.html", context)

