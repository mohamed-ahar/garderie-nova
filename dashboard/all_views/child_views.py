from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from dashboard.models import Child
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
    try:
        enrollment = child.enrollment_profile
    except EnrollmentForm.DoesNotExist:
        enrollment = None

    context = {
        'child': child,
        'enrollment': enrollment,
        'today': timezone.now().date(),
    }
    
    return render(request, 'core/children/child_profile.html', context)
