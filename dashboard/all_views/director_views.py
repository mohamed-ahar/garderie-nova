from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
import csv
from datetime import datetime, date, timedelta
from django.utils import timezone

from ..models import (
    Room,
    Center,
    Organization,
    Child,
    ParentChildRelationship,
    CenterParentAccess,
    Notification,
    TransferRequest,
    TransferHistory,
    CenterPermit,
    Group,
)

from ..forms import (
    CenterCreationForm,
    DirectorCreationForm,
    AssignDirectorForm,
    RoomForm,
    CSVUploadForm,
)

from accounts.models import User, ParentProfile, Educator


# -----------------------------------------------dashboard---------------------------------------------------------------------------------
@login_required
def director_dashboard(request):
    user = request.user
    if user.role_type != "director":
        return redirect("dashboard_redirect")

    try:
        director = user.director_profile
        center = director.managed_center
    except AttributeError:
        center = None

    # Handle Attendance POST actions
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        action = request.POST.get('action')
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if child_id and action and center:
            child = get_object_or_404(Child, child_id=child_id, center=center)
            today = timezone.now().date()
            from children.models import Attendance
            
            message_text = ""
            message_tag = "success"

            if action == "quick_arrival":
                open_record = Attendance.objects.filter(child=child, date=today, departure_time__isnull=True, is_absent=False).exists()
                if open_record:
                    message_text = f"{child.first_name} is already marked as present."
                    message_tag = "warning"
                else:
                    absence_record = Attendance.objects.filter(child=child, date=today, is_absent=True).first()
                    if absence_record:
                        absence_record.is_absent = False
                        absence_record.arrival_time = timezone.now().time()
                        absence_record.save()
                        message_text = f"Arrival marked for {child.first_name} (updated from absence)."
                    else:
                        Attendance.objects.create(
                            child=child, 
                            date=today,
                            arrival_time=timezone.now().time(), 
                            is_absent=False
                        )
                        message_text = f"Arrival marked for {child.first_name}."
            
            elif action == "quick_departure":
                latest_open = Attendance.objects.filter(
                    child=child, 
                    date=today, 
                    departure_time__isnull=True, 
                    is_absent=False
                ).last()
                
                if latest_open:
                    latest_open.departure_time = timezone.now().time()
                    latest_open.save()
                    message_text = f"Departure marked for {child.first_name}."
                else:
                    message_text = f"No open attendance record found for {child.first_name}."
                    message_tag = "error"
            
            elif action == "mark_absent":
                 Attendance.objects.create(
                    child=child,
                    date=today,
                    is_absent=True,
                    absence_reason_code='8' # Default to non-illness
                )
                 message_text = f"{child.first_name} marked as absent."

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({"success": True, "message": message_text, "tag": message_tag})
            
            if message_tag == "success": messages.success(request, message_text)
            elif message_tag == "warning": messages.warning(request, message_text)
            else: messages.error(request, message_text)

            return redirect("director_dashboard")

    groups = []
    waitlist = []
    total_educators = 0
    active_children_count = 0
    open_alerts = 0
    overall_ratio = None
    total_required_educators = 0
    pending_access_count = 0
    pending_transfers_count = 0
    recent_notifications = []
    
    # New Intelligence Summary Data
    principal_educators = []
    delegated_educators = []
    attendance_summary = {
        'in': 0,
        'out': 0,
        'absent': 0,
        'not_arrived': 0
    }
    grouping_mode = request.GET.get('summary_by', 'group') # Default grouping
    intelligence_summary = []
    
    # Child Grid Filters
    grid_age_filter = request.GET.get('grid_age')
    grid_educator_filter = request.GET.get('grid_educator')
    child_grid_data = []
    available_educators_for_filter = []

    if center:
        # Optimization: prefetch related children and assignments
        groups = (
            center.groups.all()
            .order_by("name")
            .prefetch_related("enrolled_children", "staff_assignments")
        )

        # Recalculate ratios to ensure fresh data
        for group in groups:
            group.recalculate_ratios()

        waitlist = Child.objects.filter(center=center, status="waitlist").order_by(
            "created_at"
        )

        all_educators = Educator.objects.filter(center=center).select_related('user')
        total_educators = all_educators.count()
        available_educators_for_filter = all_educators
        
        # Identify special staff
        principal_educators = all_educators.filter(user__role_type='educator_principal')
        delegated_educators = all_educators.filter(has_dashboard_access=True)

        active_children = Child.objects.filter(center=center, status="active").select_related('assigned_group', 'assigned_educator', 'assigned_educator__user')
        active_children_count = active_children.count()
        open_alerts = sum(1 for g in groups if not g.is_compliant)

        # Attendance Calculation for today
        today = datetime.now().date()
        from children.models import Attendance
        # Order by arrival_time ascending so the loop ends with the latest record
        attendance_today = Attendance.objects.filter(child__center=center, date=today).order_by('arrival_time')
        
        # Map children to their latest attendance record
        child_attendance_map = {}
        for att in attendance_today:
            child_attendance_map[att.child_id] = att

        # --- Child Grid Logic ---
        grid_query = active_children
        
        # If age filtered, we must first filter the children, then find educators who have these children
        if grid_age_filter:
            today_date = date.today()
            age_query = Q()
            if grid_age_filter == '0-23M':
                cutoff = today_date - timedelta(days=24*30.44)
                age_query |= Q(birth_date__gt=cutoff)
            elif grid_age_filter == '2Y':
                c_start = today_date - timedelta(days=36*30.44)
                c_end = today_date - timedelta(days=24*30.44)
                age_query |= Q(birth_date__gt=c_start, birth_date__lte=c_end)
            elif grid_age_filter == '3Y':
                c_start = today_date - timedelta(days=48*30.44)
                c_end = today_date - timedelta(days=36*30.44)
                age_query |= Q(birth_date__gt=c_start, birth_date__lte=c_end)
            elif grid_age_filter == '4Y':
                c_start = today_date - timedelta(days=60*30.44)
                c_end = today_date - timedelta(days=48*30.44)
                age_query |= Q(birth_date__gt=c_start, birth_date__lte=c_end)
            elif grid_age_filter == '5Y+':
                cutoff = today_date - timedelta(days=60*30.44)
                age_query |= Q(birth_date__lte=cutoff)
            
            grid_query = grid_query.filter(age_query)
            
            # Update available educators based on the filtered children
            # Get distinct educators from the filtered children
            educator_ids = grid_query.values_list('assigned_educator__user__user_id', flat=True).distinct()
            available_educators_for_filter = available_educators_for_filter.filter(user__user_id__in=educator_ids)
        
        if grid_educator_filter:
            grid_query = grid_query.filter(assigned_educator__user__user_id=grid_educator_filter)

        # Populate child_grid_data with status
        for child in grid_query:
            att = child_attendance_map.get(child.child_id)
            status = 'not_arrived'
            if att:
                if att.is_absent: status = 'absent'
                elif att.departure_time: status = 'out'
                else: status = 'in'
            
            child_grid_data.append({
                'child': child,
                'status': status,
                'attendance_record': att
            })

        # Calculate overall center ratio and total required educators
        total_required_educators = sum(g.required_educators for g in groups)
        if total_educators > 0 and active_children_count > 0:
            overall_ratio = active_children_count // total_educators

        # Build intelligence summary based on grouping
        from ..utils import calculate_ratio_stats
        from django.urls import reverse
        from django.template.loader import render_to_string
        from django.http import JsonResponse
        
        if grouping_mode == 'age':
            # Categories matching our filter: 0-23M, 2Y, 3Y, 4Y, 5Y+
            age_groups = {
                '0-23M': {'label': '0-23 Months', 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []},
                '2Y': {'label': '2 Years', 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []},
                '3Y': {'label': '3 Years', 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []},
                '4Y': {'label': '4 Years', 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []},
                '5Y+': {'label': '5+ Years', 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []},
            }
            
            for child in active_children:
                age_months = (today.year - child.birth_date.year) * 12 + today.month - child.birth_date.month
                if today.day < child.birth_date.day: age_months -= 1
                
                cat = '5Y+'
                if age_months < 24: cat = '0-23M'
                elif 24 <= age_months < 36: cat = '2Y'
                elif 36 <= age_months < 48: cat = '3Y'
                elif 48 <= age_months < 60: cat = '4Y'
                
                age_groups[cat]['all_children'].append(child)
                att = child_attendance_map.get(child.child_id)
                status = 'not_arrived'
                if att:
                    if att.is_absent: status = 'absent'
                    elif att.departure_time: status = 'out'
                    else: 
                        status = 'in'
                        age_groups[cat]['children_in'].append(child)
                
                age_groups[cat][status] += 1
                age_groups[cat]['total'] += 1
                attendance_summary[status] += 1
            
            for cat, data in age_groups.items():
                if data['total'] > 0:
                    stats = calculate_ratio_stats(data['children_in'], data['all_children'])
                    data.update(stats)
                    url = f"{reverse('attendance_board')}?date={today}&age_group={cat}"
                    intelligence_summary.append({'key': cat, 'url': url, **data})

        elif grouping_mode == 'educator':
            educator_data = {}
            for child in active_children:
                # Use current educator (considering temp transfers)
                ed = child.get_current_educator
                ed_id = ed.user_id if ed else 'unassigned'
                ed_name = ed.user.full_name if ed else 'Unassigned'
                
                if ed_id not in educator_data:
                    educator_data[ed_id] = {'label': ed_name, 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []}
                
                educator_data[ed_id]['all_children'].append(child)
                att = child_attendance_map.get(child.child_id)
                status = 'not_arrived'
                if att:
                    if att.is_absent: status = 'absent'
                    elif att.departure_time: status = 'out'
                    else: 
                        status = 'in'
                        educator_data[ed_id]['children_in'].append(child)
                
                educator_data[ed_id][status] += 1
                educator_data[ed_id]['total'] += 1
                attendance_summary[status] += 1
            
            for ed_id, data in educator_data.items():
                stats = calculate_ratio_stats(data['children_in'], data['all_children'])
                data.update(stats)
                url = reverse('educator_detail', kwargs={'user_id': ed_id}) if ed_id != 'unassigned' else "#"
                intelligence_summary.append({'key': ed_id, 'url': url, **data})

        else: # Group grouping (default)
            group_presence = {} # group_id -> data dict
            
            for child in active_children:
                group = child.get_current_group
                group_id = group.group_id if group else 'unassigned'
                
                if group_id not in group_presence:
                    group_label = group.name if group else 'Unassigned'
                    group_presence[group_id] = {'label': group_label, 'in': 0, 'out': 0, 'absent': 0, 'not_arrived': 0, 'total': 0, 'children_in': [], 'all_children': []}
                
                group_presence[group_id]['all_children'].append(child)
                att = child_attendance_map.get(child.child_id)
                status = 'not_arrived'
                if att:
                    if att.is_absent: status = 'absent'
                    elif att.departure_time: status = 'out'
                    else: 
                        status = 'in'
                        group_presence[group_id]['children_in'].append(child)
                
                group_presence[group_id][status] += 1
                group_presence[group_id]['total'] += 1
                attendance_summary[status] += 1

            for g_id, data in group_presence.items():
                stats = calculate_ratio_stats(data['children_in'], data['all_children'])
                data.update(stats)
                url = reverse('group_edit', kwargs={'group_id': g_id}) if g_id != 'unassigned' else "#"
                intelligence_summary.append({'key': g_id, 'url': url, **data})

        # Enhanced context
        pending_access_count = CenterParentAccess.objects.filter(
            center=center, status="pending"
        ).count()

        pending_transfers_count = TransferRequest.objects.filter(
            Q(target_center=center, approved_by_incoming=None)
            | Q(child__center=center, approved_by_outgoing=None)
        ).exclude(status="rejected").count()

        recent_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).order_by("-created_at")[:5]

    context = {
        "center": center,
        "groups": groups,
        "waitlist": waitlist,
        "user": user,
        "total_educators": total_educators,
        "active_children": active_children_count,
        "open_alerts": open_alerts,
        "overall_ratio": overall_ratio,
        "total_required_educators": total_required_educators,
        "pending_access_count": pending_access_count,
        "pending_transfers_count": pending_transfers_count,
        "recent_notifications": recent_notifications,
        # New operational data
        "principal_educators": principal_educators,
        "delegated_educators": delegated_educators,
        "attendance_summary": attendance_summary,
        "intelligence_summary": intelligence_summary,
        "grouping_mode": grouping_mode,
        # Child Grid Data
        "child_grid_data": child_grid_data,
        "available_educators": available_educators_for_filter,
        "grid_age_filter": grid_age_filter,
        "grid_educator_filter": grid_educator_filter,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        section = request.GET.get('section')
        if section == 'child_grid':
            grid_html = render_to_string("core/director/includes/child_grid_partial.html", context, request)
            
            # Serialize educators for dropdown update
            educators_data = [
                {"id": str(ed.user.user_id), "name": ed.user.full_name} 
                for ed in available_educators_for_filter
            ]
            
            return JsonResponse({
                "html": grid_html,
                "educators": educators_data
            })
        return render(request, "core/director/includes/intelligence_table_partial.html", context)

    return render(request, "director_dashboard.html", context)


# -----------------------------------------------center__info---------------------------------------------------------------------------------
@login_required
def create_center(request):
    if request.user.role_type != "owner":
        return redirect("login")

    organization = get_object_or_404(Organization, owner__user=request.user)

    if request.method == "POST":
        form = CenterCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                center = form.save(commit=False)
                center.organization = organization
                center.save()
                
                # Save Permits
                for i in range(1, 4):
                    permit_num = form.cleaned_data.get(f'permit_{i}')
                    if permit_num:
                        CenterPermit.objects.create(
                            center=center,
                            permit_number=permit_num
                        )
            
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
    # Njibu l-Org dyal l-Owner
    owner_org = request.user.owner_profile.owned_organization

    if request.method == "POST":
        form = DirectorCreationForm(request.POST, user=request.user)
        if form.is_valid():
            director = form.save(commit=False)
            # FORCE l-organization bach t-ban f l-list
            director.organization = owner_org
            director.save()
            messages.success(request, f"Director {director.user.full_name} created successfully.")
            return redirect("list_directors") # Redirect l-list bach t-checkih
    else:
        form = DirectorCreationForm(user=request.user)

    return render(request, "core/owner/create_director.html", {"form": form})

@login_required
@transaction.atomic
def assign_director_to_center(request, center_id):
    # 1. Kantakdu belli l-Owner hoa li kaysayeb had l-center
    center = get_object_or_404(
        Center, center_id=center_id, organization__owner__user=request.user
    )

    if request.method == "POST":
        form = AssignDirectorForm(request.POST, instance=center, user=request.user)
        if form.is_valid():
            # Save l-center (bach l-FK dyal director f Center model t-zad)
            center = form.save()
            
            # 2. Hna l-muhim: Updati l-Profile dyal dik l-Director
            # Bach f l-base de données, l-Director i-walli "khdam" f had l-center
            if center.director:
                director_profile = center.director
                director_profile.center = center
                director_profile.save()

            messages.success(request, f"Director {center.director.user.full_name} assigned to {center.name}.")
            return redirect("owner_centers_list")
    else:
        form = AssignDirectorForm(instance=center, user=request.user)

    return render(
        request, "core/owner/assign_director.html", {"form": form, "center": center}
    )


@login_required(login_url="login")
def room_list_view(request):
    user = request.user
    rooms = Room.objects.all()
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
def director_add_child(request):
    """Director can add a child manually to their center"""
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

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        birth_date = request.POST.get("birth_date")
        status = request.POST.get("status", "active")
        parent_email = request.POST.get("parent_email")
        parent_name = request.POST.get("parent_name")
        
        if not first_name or not birth_date:
            messages.error(request, "First name and birth date are required.")
            return redirect("director_add_child")
        
        # Create or find parent user
        parent_user = None
        if parent_email:
            parent_user, created = User.objects.get_or_create(
                email=parent_email,
                defaults={
                    "full_name": parent_name or parent_email,
                    "role_type": "parent"
                }
            )
            if created:
                parent_user.set_unusable_password()
                parent_user.save()
                
                # Create parent profile
                ParentProfile.objects.create(user=parent_user)
        
        # Create child
        child = Child.objects.create(
            center=center,
            first_name=first_name,
            last_name=last_name or "",
            birth_date=birth_date,
            status=status
        )
        
        # Create parent relationship if parent exists
        if parent_user:
            try:
                parent_profile = parent_user.parent_profile
                ParentChildRelationship.objects.create(
                    parent=parent_profile,
                    child=child,
                    relationship_type="Parent",
                    is_emergency_contact=True
                )
            except ParentProfile.DoesNotExist:
                pass
        
        messages.success(request, f"Child {first_name} added successfully.")
        return redirect("child_list")

    return render(request, "core/director/add_child.html", {"center": center})


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


@login_required(login_url="login")
def transfer_history_view(request):
    """View transfer history for director's center"""
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
    
    # Get transfer history for this center (both incoming and outgoing)
    incoming_history = TransferHistory.objects.filter(to_center_id=center.center_id).order_by('-transfer_date')
    outgoing_history = TransferHistory.objects.filter(from_center_id=center.center_id).order_by('-transfer_date')
    
    context = {
        "center": center,
        "incoming_history": incoming_history,
        "outgoing_history": outgoing_history,
    }
    return render(request, "core/director/transfer_history.html", context)
