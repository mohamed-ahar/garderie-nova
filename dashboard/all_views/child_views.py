from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import date, timedelta, datetime
from dashboard.models import Child
from children.models import DailyActivityLog, Attendance
from reports.models import EnrollmentForm

@login_required
def child_profile_view(request, child_id):
    child = get_object_or_404(Child, pk=child_id)
    user = request.user
    
    # --- Permission Check ---
    has_access = False
    
    if user.is_superuser:
        has_access = True
    elif user.role_type == 'parent':
        if child.parent_relationships.filter(parent__user=user).exists():
            has_access = True
    elif user.role_type == 'director':
        # Check if director manages the child's center
        if hasattr(user, 'director_profile') and user.director_profile.managed_center == child.center:
            has_access = True
    elif user.role_type == 'educator':
        # Check if educator is assigned to the child or the child's group
        if hasattr(user, 'educator_profile'):
            educator = user.educator_profile
            # Direct assignment
            if child.assigned_educator == educator:
                has_access = True
            # Group assignment (if child is in a group and educator is assigned to that group)
            elif child.assigned_group and child.assigned_group.staff_assignments.filter(educator=educator, is_active=True).exists():
                has_access = True
    elif user.role_type == 'owner':
         if hasattr(user, 'owner_profile') and user.owner_profile.owned_organization == child.center.organization:
            has_access = True

    if not has_access:
        messages.error(request, "Vous n'avez pas la permission de voir ce profil.")
        raise PermissionDenied("Access Denied")

    # --- Fetch Enrollment Data ---
    enrollment = child.enrollment_forms.filter(is_active=True).first()

    # Calculate previous week for export links
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    prev_week = start_of_week - timedelta(days=7)

    # Calculate statistics for the reports tab (only for parents)
    stats = {}
    if user.role_type == 'parent':
        # Get attendance for current week
        week_days = [start_of_week + timedelta(days=i) for i in range(5)]
        
        # Days present this week
        present_days = 0
        total_days = 0
        arrival_times = []
        
        for day in week_days:
            records = Attendance.objects.filter(child=child, date=day)
            if records.exists():
                total_days += 1
                if records.filter(is_absent=False).exists():
                    present_days += 1
                    # Get arrival time
                    arrival_record = records.filter(is_absent=False, arrival_time__isnull=False).first()
                    if arrival_record and arrival_record.arrival_time:
                        arrival_times.append(arrival_record.arrival_time)
        
        # Calculate average arrival time
        avg_arrival = None
        if arrival_times:
            # Convert times to minutes from midnight
            total_minutes = sum(t.hour * 60 + t.minute for t in arrival_times)
            avg_minutes = total_minutes // len(arrival_times)
            avg_arrival = f"{avg_minutes // 60:02d}:{avg_minutes % 60:02d}"
        
        # Get nap duration from daily activity logs
        nap_durations = []
        logs = DailyActivityLog.objects.filter(
            report__child=child,
            date__range=[week_days[0], week_days[-1]],
            nap_tracking__isnull=False
        ).exclude(nap_tracking=[])
        
        for log in logs:
            if log.nap_tracking:
                for nap in log.nap_tracking:
                    if 'start' in nap and 'end' in nap:
                        try:
                            start = datetime.strptime(nap['start'], '%H:%M').time()
                            end = datetime.strptime(nap['end'], '%H:%M').time()
                            # Calculate duration in hours
                            start_minutes = start.hour * 60 + start.minute
                            end_minutes = end.hour * 60 + end.minute
                            if end_minutes > start_minutes:
                                nap_durations.append((end_minutes - start_minutes) / 60.0)
                        except:
                            pass
        
        avg_nap = None
        if nap_durations:
            avg_nap_hours = sum(nap_durations) / len(nap_durations)
            avg_nap = f"{avg_nap_hours:.1f} hrs"
        
        stats = {
            'present_days': present_days,
            'total_days': total_days,
            'avg_arrival': avg_arrival or '--:--',
            'avg_nap': avg_nap or 'N/A',
        }

    context = {
        'child': child,
        'enrollment': enrollment,
        'today': timezone.now().date(),
        'prev_week': prev_week.strftime('%Y-%m-%d'),
        'stats': stats,
    }
    
    return render(request, 'core/children/child_profile.html', context)
