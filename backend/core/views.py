from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Group, Room, Child, EducatorProfile, StaffAssignment

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials. Please try again.'})
            
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    context = {
        'total_attendance': 142,
        'capacity': 160,
        'occupancy_percentage': 88,
        'pending_signatures': 4,
        'compliance_rate': 92,
        'observations': 842,
    }
    return render(request, 'core/dashboard.html', context)

@login_required(login_url='login')
def group_list_view(request):
    user = request.user
    groups = Group.objects.none()

    if user.role_type == 'owner':
        groups = Group.objects.all().select_related('room', 'center')
    elif user.role_type == 'director' and hasattr(user, 'director_profile'):
        center = user.director_profile.managed_center
        if center:
            groups = Group.objects.filter(center=center).select_related('room')
    elif user.role_type == 'educator' and hasattr(user, 'educator_profile'):
        center = user.educator_profile.center
        if center:
            groups = Group.objects.filter(center=center).select_related('room')
    
    context = {
        'groups': groups
    }
    return render(request, 'core/group_list.html', context)

@login_required(login_url='login')
def group_edit_view(request, group_id):
    group = get_object_or_404(Group, group_id=group_id)
    user = request.user

    # Permission check
    if user.role_type == 'director' and hasattr(user, 'director_profile'):
        if group.center != user.director_profile.managed_center:
             return render(request, 'core/403.html', status=403)
    elif user.role_type != 'owner':
         return render(request, 'core/403.html', status=403)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_details':
            name = request.POST.get('name')
            room_id = request.POST.get('room_id')
            if name: group.name = name
            if room_id:
                room = get_object_or_404(Room, room_id=room_id)
                if room.center == group.center:
                    group.room = room
            group.save()

        elif action == 'assign_educator':
            user_id = request.POST.get('user_id')
            educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
            StaffAssignment.objects.filter(educator=educator, is_active=True).update(is_active=False)
            StaffAssignment.objects.create(educator=educator, group=group, is_active=True)
            
            group.current_educators = StaffAssignment.objects.filter(group=group, is_active=True).count()
            group.recalculate_ratios()

        elif action == 'remove_educator':
            user_id = request.POST.get('user_id')
            educator = get_object_or_404(EducatorProfile, user__user_id=user_id)
            StaffAssignment.objects.filter(group=group, educator=educator, is_active=True).update(is_active=False)
            group.current_educators = StaffAssignment.objects.filter(group=group, is_active=True).count()
            group.recalculate_ratios()

        elif action == 'assign_child':
            child_id = request.POST.get('child_id')
            child = get_object_or_404(Child, child_id=child_id)
            old_group = child.assigned_group
            child.assigned_group = group
            child.save()
            group.recalculate_ratios()
            if old_group: old_group.recalculate_ratios()

        elif action == 'remove_child':
            child_id = request.POST.get('child_id')
            child = get_object_or_404(Child, child_id=child_id)
            if child.assigned_group == group:
                child.assigned_group = None
                child.assigned_educator = None
                child.save()
                group.recalculate_ratios()

        elif action == 'assign_child_educator':
            child_id = request.POST.get('child_id')
            educator_id = request.POST.get('educator_id')
            child = get_object_or_404(Child, child_id=child_id)
            if child.assigned_group == group:
                if educator_id:
                    educator = get_object_or_404(EducatorProfile, user__user_id=educator_id)
                    child.assigned_educator = educator
                else:
                    child.assigned_educator = None
                child.save()

        return redirect('group_edit', group_id=group_id)

    assigned_educators = EducatorProfile.objects.filter(assignments__group=group, assignments__is_active=True).select_related('user')
    assigned_children = group.enrolled_children.all().select_related('assigned_educator__user').order_by('first_name')
    
    all_rooms = Room.objects.filter(center=group.center)
    
    # Educators not currently assigned to THIS group it could be in other groups
    other_educators = EducatorProfile.objects.filter(center=group.center).exclude(assignments__group=group, assignments__is_active=True).select_related('user')
    
    # Children not in this group
    other_children = Child.objects.filter(center=group.center).exclude(assigned_group=group).order_by('first_name')

    context = {
        'group': group,
        'rooms': all_rooms,
        'assigned_educators': assigned_educators,
        'assigned_children': assigned_children,
        'other_educators': other_educators,
        'other_children': other_children,
    }
    return render(request, 'core/group_manage.html', context)

@login_required(login_url='login')
def group_delete_view(request, group_id):
    group = get_object_or_404(Group, group_id=group_id)
    user = request.user

    # Permission check
    if user.role_type == 'director' and hasattr(user, 'director_profile'):
        if group.center != user.director_profile.managed_center:
             return render(request, 'core/403.html', status=403)
    elif user.role_type != 'owner':
         return render(request, 'core/403.html', status=403)
         
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')
        
    return render(request, 'core/403.html', status=403)
