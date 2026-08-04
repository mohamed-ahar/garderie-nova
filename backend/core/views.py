from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from django.db.models import Prefetch
from .models import Group, Room, Child, EducatorProfile, StaffAssignment, User, Center


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(
                request,
                "core/login.html",
                {"error": "Invalid credentials. Please try again."},
            )

    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


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
    return render(request, "core/group_list.html", context)


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
            educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
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
            educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
            # Remove all children assigned to this educator
            children = Child.objects.filter(assigned_educator=educator, assigned_group=group)
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
                    educator = get_object_or_404(
                        EducatorProfile, user__user_id=educator_id
                    )
                    child.assigned_educator = educator
                    child.save()
                    educator.recalculate_compliance()
                else:
                    child.save()
                
                group.recalculate_ratios()

        return redirect("group_edit", group_id=group_id)

    assigned_educators = EducatorProfile.objects.filter(
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
        EducatorProfile.objects.filter(center=group.center)
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
    }
    return render(request, "core/group_manage.html", context)


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
        group.delete()
        return redirect("group_list")

    return render(request, "core/403.html", status=403)


@login_required(login_url="login")
def educator_list_view(request):
    user = request.user
    educators = EducatorProfile.objects.none()
    centers = []

    if user.role_type == "owner":
        educators = EducatorProfile.objects.all().select_related("user", "center")
        centers = Center.objects.all()
    elif user.role_type in ["director", "vice_director"]:
        if user.role_type == "director" and hasattr(user, "director_profile"):
            center = user.director_profile.managed_center
            if center:
                educators = EducatorProfile.objects.filter(
                    center=center
                ).select_related("user")
        elif user.role_type == "vice_director" and hasattr(
            user, "vice_director_profile"
        ):
            center = user.vice_director_profile.center
            if center:
                educators = EducatorProfile.objects.filter(
                    center=center
                ).select_related("user")

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

        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', '')

        # Validation (simplistic)
        if User.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Email already exists."}, status=400)
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
                email=email, password=password, full_name=full_name, role_type="educator"
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
                EducatorProfile.objects.create(user=new_user, center=target_center)
                if is_ajax:
                    return JsonResponse({"status": "success", "message": "Educator added successfully."})
                return redirect("educator_list")
            else:
                # Rollback user creation if center issue? Or just show error.
                new_user.delete()
                if is_ajax:
                    return JsonResponse({"status": "error", "message": "Center not found for assignment."}, status=400)
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
    educator_profile = get_object_or_404(EducatorProfile, user__user_id=user_id)

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
    educator_profile = get_object_or_404(EducatorProfile, user__user_id=user_id)
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
    educator_profile = get_object_or_404(EducatorProfile, user__user_id=user_id)

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
