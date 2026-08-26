from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from ..models import Child
from datetime import date, timedelta, datetime
from children.models import WeeklyChildReport, DailyActivityLog, Attendance
from children.forms import DailyCheckupForm, AttendanceForm
from django.template.loader import render_to_string
from django.http import HttpResponse

@login_required(login_url="login")
def export_weekly_daily_report_pdf(request, child_id):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
    
    child = get_object_or_404(Child, child_id=child_id)
    
    date_str = request.GET.get('week_start')
    if date_str:
        start_of_week = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

    week_days = [start_of_week + timedelta(days=i) for i in range(5)]
    
    # Get the logs for these 5 days
    logs_map = {}
    logs = DailyActivityLog.objects.filter(
        report__child=child,
        date__range=[week_days[0], week_days[-1]]
    ).select_related('signed_by')
    
    for log in logs:
        logs_map[log.date] = log

    # Prepare data for each day, even if no log exists
    days_data = []
    for day in week_days:
        log = logs_map.get(day)
        
        # Process food tracking for easier template access
        food = {}
        if log:
            for entry in log.food_tracking:
                food[entry.get('name')] = entry.get('amount')
        
        # Ensure diaper logs has exactly 6 entries for the grid padding if needed, 
        # or handle in template. The form has 4, the PDF shows up to 7.
        diaper_entries = log.diaper_logs if log else []
        while len(diaper_entries) < 7:
            diaper_entries.append({})

        days_data.append({
            'date': day,
            'log': log,
            'food': food,
            'diapers': diaper_entries
        })

    context = {
        "child": child,
        "days_data": days_data,
        "start_of_week": start_of_week,
        "center": child.center,
        "request": request
    }

    html_string = render_to_string("core/educators/weekly_daily_report_pdf.html", context)
    
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"weekly_report_{child.first_name}_{start_of_week}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except ImportError:
        return HttpResponse("WeasyPrint not installed", status=500)

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

    # Date handling
    date_str = request.GET.get('date')
    today = date.today()
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = today
    else:
        view_date = today

    is_today = view_date == today
    
    if request.method == "POST":
        if not is_today:
            messages.error(request, "You cannot modify attendance for previous dates.")
            return redirect(f"/educator/attendance-board/?date={view_date}")

        child_id = request.POST.get('child_id')
        action = request.POST.get('action')
        child = get_object_or_404(Child, child_id=child_id, assigned_educator=educator_profile)
        
        if action == "quick_arrival":
            # Check if there's already an open record
            open_record = Attendance.objects.filter(child=child, date=view_date, departure_time__isnull=True, is_absent=False).exists()
            if open_record:
                messages.warning(request, f"{child.first_name} is already marked as present.")
            else:
                # If they were previously marked absent, we keep the record but they are now present
                Attendance.objects.create(
                    child=child, 
                    date=view_date,
                    arrival_time=timezone.now().time(), 
                    is_absent=False
                )
                messages.success(request, f"Arrival marked for {child.first_name}.")
        
        elif action == "quick_departure":
            latest_open = Attendance.objects.filter(
                child=child, 
                date=view_date, 
                departure_time__isnull=True, 
                is_absent=False
            ).last()
            
            if latest_open:
                latest_open.departure_time = timezone.now().time()
                latest_open.save()
                messages.success(request, f"Departure marked for {child.first_name}.")
            else:
                messages.error(request, f"No open attendance record found for {child.first_name}.")
        
        return redirect(f"/educator/attendance-board/?date={view_date}")

    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')
    
    attendance_data = []
    for child in children:
        records = Attendance.objects.filter(child=child, date=view_date).order_by('arrival_time')
        
        # A child is present if they have ANY record where is_absent=False
        has_present_record = records.filter(is_absent=False).exists()
        
        # A child is only truly absent if all records for the day say they are absent
        # OR if they have an absence record and NO presence records
        is_absent = records.filter(is_absent=True).exists() and not has_present_record
        
        current_record = records.filter(departure_time__isnull=True, is_absent=False).last()
        
        attendance_data.append({
            'child': child,
            'records': records.filter(is_absent=False),
            'is_currently_in': current_record is not None if is_today else False,
            'is_absent': is_absent,
            'absence_record': records.filter(is_absent=True).first() if is_absent else None,
            'latest_record': records.last()
        })

    context = {
        "attendance_data": attendance_data,
        "view_date": view_date,
        "today": today,
        "is_today": is_today,
        "prev_day": view_date - timedelta(days=1),
        "next_day": view_date + timedelta(days=1) if view_date < today else None,
    }
    return render(request, "core/educators/attendance_board.html", context)

@login_required(login_url="login")
def mark_attendance(request, child_id):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
        
    child = get_object_or_404(Child, child_id=child_id)
    
    # Date handling
    date_str = request.GET.get('date')
    today = date.today()
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = today
    else:
        view_date = today

    is_today = view_date == today
    
    attendance_id = request.GET.get('id')
    attendance = None
    if attendance_id:
        attendance = get_object_or_404(Attendance, attendance_id=attendance_id, child=child)
        if attendance.date != view_date:
             return redirect("attendance_board")
    
    if request.method == "POST":
        if not is_today:
            messages.error(request, "You cannot modify attendance for previous dates.")
            return redirect(f"/educator/attendance-board/?date={view_date}")

        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            att = form.save(commit=False)
            att.child = child
            att.date = view_date
            att.save()
            messages.success(request, f"Attendance for {child.first_name} updated.")
            return redirect(f"/educator/attendance-board/?date={view_date}")
    else:
        initial = {}
        if not attendance:
            is_absent = request.GET.get('absent') == '1'
            initial['is_absent'] = is_absent
            if not is_absent:
                initial['arrival_time'] = timezone.now().time().strftime('%H:%M')
        
        form = AttendanceForm(instance=attendance, initial=initial)
        
    today_records = Attendance.objects.filter(child=child, date=view_date).order_by('arrival_time')
        
    return render(request, "core/educators/attendance_form.html", {
        "form": form,
        "child": child,
        "view_date": view_date,
        "is_today": is_today,
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

    # Date handling
    date_str = request.GET.get('date')
    today = date.today()
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = today
    else:
        view_date = today

    is_today = view_date == today

    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')
    
    child_list_data = []
    for child in children:
        log = DailyActivityLog.objects.filter(
            report__child=child,
            date=view_date
        ).first()
        
        # A child is present today if they have ANY record where is_absent=False
        records = Attendance.objects.filter(child=child, date=view_date)
        is_present_on_date = records.filter(is_absent=False).exists()
        
        # Truly absent only if marked absent AND no presence records exist
        is_absent_on_date = records.filter(is_absent=True).exists() and not is_present_on_date
        
        child_list_data.append({
            'child': child,
            'log_exists': log is not None,
            'attendance': records.filter(is_absent=True).first() if is_absent_on_date else records.filter(is_absent=False).first(),
            'is_present_today': is_present_on_date,
            'is_absent_today': is_absent_on_date
        })

    context = {
        "child_list_data": child_list_data,
        "view_date": view_date,
        "today": today,
        "is_today": is_today,
        "prev_day": view_date - timedelta(days=1),
        "next_day": view_date + timedelta(days=1) if view_date < today else None,
    }
    return render(request, "core/educators/daily_checkup_list.html", context)

@login_required(login_url="login")
def daily_checkup_form(request, child_id):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
        
    child = get_object_or_404(Child, child_id=child_id)
    if child.assigned_educator != user.educator_profile:
         messages.error(request, "This child is not assigned to you.")
         return redirect("daily_checkup_list")
         
    # Date handling
    date_str = request.GET.get('date')
    today = date.today()
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            view_date = today
    else:
        view_date = today

    is_today = view_date == today
    week_start = view_date - timedelta(days=view_date.weekday())
    
    weekly_report, _ = WeeklyChildReport.objects.get_or_create(
        child=child,
        week_start_date=week_start
    )
    
    day_map = {0: 'LUNDI', 1: 'MARDI', 2: 'MERCREDI', 3: 'JEUDI', 4: 'VENDREDI', 5: 'SAMEDI', 6: 'DIMANCHE'}
    day_name = day_map.get(view_date.weekday(), 'LUNDI') 
    
    if is_today:
        daily_log, created = DailyActivityLog.objects.get_or_create(
            report=weekly_report,
            date=view_date,
            defaults={'day_name': day_name}
        )
    else:
        daily_log = DailyActivityLog.objects.filter(
            report=weekly_report,
            date=view_date
        ).first()
        
        if not daily_log:
            return render(request, "core/educators/daily_checkup_none.html", {
                "child": child,
                "view_date": view_date
            })
    
    if request.method == "POST":
        if not is_today:
            messages.error(request, "You cannot modify reports for previous dates.")
            return redirect(f"/educator/daily-checkups/?date={view_date}")

        form = DailyCheckupForm(request.POST, instance=daily_log)
        if form.is_valid():
            log = form.save(commit=False)
            log.signed_by = user.educator_profile
            if log.signature_data:
                log.signed_at = timezone.now()
            log.save()
            messages.success(request, f"Daily report for {child.first_name} saved.")
            return redirect(f"/educator/daily-checkups/?date={view_date}")
    else:
        form = DailyCheckupForm(instance=daily_log)
        
    return render(request, "core/educators/daily_checkup_form.html", {
        "form": form,
        "child": child,
        "daily_log": daily_log,
        "is_today": is_today,
        "view_date": view_date
    })

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

    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')

    context = {
        "children": children,
    }
    return render(request, "core/educators/assigned_children.html", context)

@login_required(login_url="login")
def weekly_attendance_report(request):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
    
    try:
        educator_profile = user.educator_profile
    except AttributeError:
        messages.error(request, "Educator profile not found.")
        return redirect("dashboard_redirect")

    # Week handling
    date_str = request.GET.get('week_start')
    today = date.today()
    if date_str:
        try:
            start_of_week = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            start_of_week = today - timedelta(days=today.weekday())
    else:
        start_of_week = today - timedelta(days=today.weekday())

    week_days = [start_of_week + timedelta(days=i) for i in range(5)]
    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')
    
    report_data = []
    for child in children:
        days_data = []
        for day in week_days:
            records = Attendance.objects.filter(child=child, date=day).order_by('arrival_time')
            has_presence = records.filter(is_absent=False).exists()
            is_absent = records.filter(is_absent=True).exists() and not has_presence
            
            days_data.append({
                'date': day,
                'records': records.filter(is_absent=False),
                'is_absent': records.filter(is_absent=True).first() if is_absent else None
            })
        report_data.append({
            'child': child,
            'days': days_data
        })

    context = {
        "report_data": report_data,
        "week_days": week_days,
        "start_of_week": start_of_week,
        "prev_week": start_of_week - timedelta(days=7),
        "next_week": start_of_week + timedelta(days=7),
        "center": educator_profile.center,
        "educator": educator_profile
    }
    return render(request, "core/educators/weekly_attendance_report.html", context)

@login_required(login_url="login")
def export_attendance_pdf(request):
    user = request.user
    if user.role_type != "educator":
        return render(request, "core/403.html", status=403)
    
    try:
        educator_profile = user.educator_profile
    except AttributeError:
        return redirect("dashboard_redirect")

    date_str = request.GET.get('week_start')
    if date_str:
        start_of_week = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

    week_days = [start_of_week + timedelta(days=i) for i in range(5)]
    children = Child.objects.filter(assigned_educator=educator_profile).select_related('center', 'assigned_group')
    
    report_data = []
    for child in children:
        days_data = []
        for day in week_days:
            records = Attendance.objects.filter(child=child, date=day).order_by('arrival_time')
            has_presence = records.filter(is_absent=False).exists()
            is_absent = records.filter(is_absent=True).exists() and not has_presence
            
            days_data.append({
                'date': day,
                'records': records.filter(is_absent=False),
                'is_absent': records.filter(is_absent=True).first() if is_absent else None
            })
        report_data.append({
            'child': child,
            'days': days_data
        })

    context = {
        "report_data": report_data,
        "week_days": week_days,
        "start_of_week": start_of_week,
        "center": educator_profile.center,
        "educator": educator_profile
    }

    html_string = render_to_string("core/educators/weekly_attendance_pdf.html", context)
    
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"attendance_{start_of_week}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except ImportError:
        return HttpResponse("WeasyPrint not installed", status=500)