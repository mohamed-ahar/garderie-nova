import email
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Director, Owner, ParentProfile, User
from dashboard.models import Center, ParentChildRelationship, Child
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def login_view(request):
    if request.method == "POST":
        u_input = request.POST.get("email")
        p = request.POST.get("password")

        # 1. Nejbdou l-user men DB
        user_obj = User.objects.filter(Q(email=u_input)).first()
        print(User.objects.filter(email=u_input))
        if user_obj:
            # 2. Authenticate (Verify Password)
            user = authenticate(request, email=user_obj.email, password=p)

            if user is not None:
                login(request, user)
                print("hna 0")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect("dashboard_redirect")

            else:
                # Password ghalat
                print("hna 1")
                return render(
                    request,
                    "login.html",
                    {"error": "Invalid password. Please try again.", "type": "error"},
                )
        else:
            # Username/Email ghalat
            print("hna 2 ")
            return render(
                request,
                "login.html",
                {
                    "error": "No account found with this email/username.",
                    "type": "error",
                },
            )

    return render(
        request,
        "login.html",
    )


# --- 3. REDIRECTION LOGIC (The Traffic Controller) ---
@login_required
def dashboard_redirect(request):
    """Had l-view hiya li kat-décidi fin gha ymchi l-user melli y-login"""
    
    role = request.user.role_type

    if role == "owner":
        return redirect("owner_dashboard")
    elif role == "director":
        return redirect("director_dashboard")
    elif role == "educator":
        return redirect("educator_dashboard")
    elif role == "parent":
        return redirect("parent_dashboard")
    else:
        # Ila mafih hta chi role m3rouf
        logout(request)
        return redirect("login")


def logout_view(request):
    logout(request)

    return redirect("login")


@login_required
def owner_dashboard(request):
    centers = Center.objects.filter(
        organization__owner__user=request.user
    ).select_related("organization", "director", "director__user")
 
    centers_count=centers.count()
    return render(request, "owner_dashboard.html",{"centers": centers, "centers_count": centers_count})


@login_required
def director_dashboard(request):
    user = request.user
    if user.role_type != 'director':
        return redirect('dashboard_redirect')
        
    try:
        director = user.director_profile
        center = director.managed_center
    except:
        center = None
    
    groups = []
    waitlist = []
    total_educators = 0
    active_children = 0
    open_alerts = 0

    if center:
        groups = center.groups.all().order_by('name')
        # Recalculate ratios to ensure fresh data
        for group in groups:
            group.recalculate_ratios()
            
        waitlist = Child.objects.filter(center=center, status='waitlist').order_by('created_at')
        
        from .models import Educator
        total_educators = Educator.objects.filter(center=center).count()
        active_children = Child.objects.filter(center=center, status='active').count()
        open_alerts = groups.filter(is_compliant=False).count()

    context = {
        'center': center,
        'groups': groups,
        'waitlist': waitlist,
        'user': user,
        'total_educators': total_educators,
        'active_children': active_children,
        'open_alerts': open_alerts,
    }
    return render(request, "director_dashboard.html", context)



@login_required
def educator_dashboard(request):
    return render(request, "educator_dashboard.html")


@login_required
def parent_dashboard(request):
    user = request.user
    if user.role_type != 'parent':
        return redirect('dashboard_redirect')
        
    try:
        profile = user.parent_profile
    except ParentProfile.DoesNotExist:
        profile = None

    children = []
    if profile:
        relationships = ParentChildRelationship.objects.filter(parent=profile).select_related('child')
        children = [rel.child for rel in relationships]
    
    # Calculate waitlist position
    for child in children:
        if child.status == 'waitlist':
            pos = Child.objects.filter(
                center=child.center, 
                status='waitlist', 
                created_at__lt=child.created_at
            ).count() + 1
            child.waitlist_position = pos
        
        # Check enrollment safely
        try:
            _ = child.enrollment_profile
            child.has_enrollment_form = True
        except:
            child.has_enrollment_form = False

    return render(request, "parent_dashboard.html", {'children': children})


@login_required
def personal_profile(request):
    user = request.user
    role_info = None

    if request.method == 'POST' and request.FILES.get('profile_photo'):
        user.profile_photo = request.FILES['profile_photo']
        user.save()
        return redirect('personal_profile')

    # Check l-role (khass t-koun lower case 'owner' hit hka dertiha f models)
    if user.role_type == "owner":
        role_info = Owner.objects.filter(user=user).first()
    elif user.role_type == "director":
        role_info = Director.objects.filter(user=user).first()
    elif user.role_type == "parent":
        role_info = ParentProfile.objects.filter(user=user).first()

    context = {
        "user": user,
        "role_info": role_info,
        "page_title": "Identity Console",
    }

    return render(request, "profile.html", context)

