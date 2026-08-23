from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Child
from datetime import date, timedelta
from children.models import WeeklyChildReport, DailyActivityLog
from children.forms import DailyCheckupForm

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
        
        child_list_data.append({
            'child': child,
            'log_exists': log_exists
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