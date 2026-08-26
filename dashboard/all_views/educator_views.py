from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from ..models import Child
from datetime import date, timedelta
from children.models import WeeklyChildReport, DailyActivityLog, Attendance
from children.forms import DailyCheckupForm, AttendanceForm

@login_required(login_url="login")
def attendance_board(request):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
    
    try:
        educator_profile = user.educator_profile
    except AttributeError:
        messages.error(request, "Educator profile not found.")
        return redirect("dashboard_redirect")

    today = date.today()
    
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        action = request.POST.get('action')
        child = get_object_or_404(Child, child_id=child_id, assigned_educator=educator_profile)
        
        if action == "quick_arrival":
            # Check if there's already an open record
            open_record = Attendance.objects.filter(child=child, date=today, departure_time__isnull=True, is_absent=False).exists()
            if open_record:
                messages.warning(request, f"{child.first_name} is already marked as present.")
            else:
                Attendance.objects.create(
                    child=child, 
                    date=today,
                    arrival_time=timezone.now().time(), 
                    is_absent=False
                )
                messages.success(request, f"Arrival marked for {child.first_name}.")
        
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
                messages.success(request, f"Departure marked for {child.first_name}.")
            else:
                messages.error(request, f"No open attendance record found for {child.first_name}.")
        
        return redirect("attendance_board")

    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')
    
    attendance_data = []
    for child in children:
        records = Attendance.objects.filter(child=child, date=today).order_by('arrival_time')
        is_absent = records.filter(is_absent=True).exists()
        current_record = records.filter(departure_time__isnull=True, is_absent=False).last()
        
        attendance_data.append({
            'child': child,
            'records': records,
            'is_currently_in': current_record is not None,
            'is_absent': is_absent,
            'latest_record': records.last()
        })

    context = {
        "attendance_data": attendance_data,
        "today": today
    }
    return render(request, "core/educators/attendance_board.html", context)

@login_required(login_url="login")
def educator_assigned_children(request):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
    
    try:
        educator_profile = user.educator_profile
    except AttributeError:
        messages.error(request, "Educator profile not found.")
        return redirect("dashboard_redirect")

    # Get children assigned to this educator
    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')

    context = {
        "children": children,
    }
    return render(request, "core/educators/assigned_children.html", context)

@login_required(login_url="login")
def mark_attendance(request, child_id):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
        
    child = get_object_or_404(Child, child_id=child_id)
    today = date.today()
    
    # If editing a specific record (optional enhancement, but let's keep it simple for now)
    attendance_id = request.GET.get('id')
    attendance = None
    if attendance_id:
        attendance = get_object_or_404(Attendance, attendance_id=attendance_id, child=child)
    
    if request.method == "POST":
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            att = form.save(commit=False)
            att.child = child
            att.date = today
            att.save()
            messages.success(request, f"Attendance for {child.first_name} updated.")
            return redirect("attendance_board")
    else:
        initial = {}
        if not attendance:
            is_absent = request.GET.get('absent') == '1'
            initial['is_absent'] = is_absent
            if not is_absent:
                initial['arrival_time'] = timezone.now().time().strftime('%H:%M')
        
        form = AttendanceForm(instance=attendance, initial=initial)
        
    today_records = Attendance.objects.filter(child=child, date=today).order_by('arrival_time')
        
    return render(request, "core/educators/attendance_form.html", {
        "form": form,
        "child": child,
        "today": today,
        "today_records": today_records
    })

@login_required(login_url="login")
def daily_checkup_list(request):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
    
    try:
        educator_profile = user.educator_profile
    except AttributeError:
        messages.error(request, "Educator profile not found.")
        return redirect("dashboard_redirect")

    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')
    today = date.today()
    
    child_list_data = []
    for child in children:
        log_exists = DailyActivityLog.objects.filter(
            report__child=child,
            date=today
        ).exists()
        
        # Any attendance today (present or absent)
        attendance = Attendance.objects.filter(child=child, date=today).first()
        is_present_today = Attendance.objects.filter(child=child, date=today, is_absent=False).exists()
        
        child_list_data.append({
            'child': child,
            'log_exists': log_exists,
            'attendance': attendance,
            'is_present_today': is_present_today
        })

    context = {
        "child_list_data": child_list_data,
        "today": today
    }
    return render(request, "core/educators/daily_checkup_list.html", context)


@login_required(login_url="login")
def daily_checkup_form(request, child_id):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
        
    child = get_object_or_404(Child, child_id=child_id)
    # Ensure child is assigned to this educator
    if child.assigned_educator != user.educator_profile:
         messages.error(request, "This child is not assigned to you.")
         return redirect("daily_checkup_list")
         
    today = date.today()
    # Calculate Monday of this week
    week_start = today - timedelta(days=today.weekday())
    
    # Get or Create Weekly Report
    weekly_report, _ = WeeklyChildReport.objects.get_or_create(
        child=child,
        week_start_date=week_start
    )
    
    # Get or Create Daily Log
    day_map = {
        0: 'LUNDI', 1: 'MARDI', 2: 'MERCREDI', 3: 'JEUDI', 4: 'VENDREDI', 5: 'SAMEDI', 6: 'DIMANCHE'
    }
    day_name = day_map.get(today.weekday(), 'LUNDI') 
    
    daily_log, created = DailyActivityLog.objects.get_or_create(
        report=weekly_report,
        date=today,
        defaults={'day_name': day_name}
    )
    
    if request.method == "POST":
        form = DailyCheckupForm(request.POST, instance=daily_log)
        if form.is_valid():
            log = form.save(commit=False)
            log.signed_by = user.educator_profile
            log.save()
            messages.success(request, f"Daily report for {child.first_name} saved.")
            return redirect("daily_checkup_list")
    else:
        form = DailyCheckupForm(instance=daily_log)
        
    return render(request, "core/educators/daily_checkup_form.html", {
        "form": form,
        "child": child,
        "daily_log": daily_log
    })