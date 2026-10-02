import email
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Director, Educator, EducatorPrincipal, Owner, ParentProfile, User
from dashboard.models import Center, ParentChildRelationship, Child
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.db import transaction


def login_view(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")
    
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
                    {"error": "Invalid email or password. Please try again.", "type": "error"},
                )
        else:
            # Username/Email ghalat
            print("hna 2 ")
            return render(
                request,
                "login.html",
                {
                    "error": "Invalid email or password. Please try again.",
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
    elif role == "educator" or role == "educator_principal":
        # هادي هي البلاصة فين زدنا educator_principal
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
    ).select_related("organization", "director", "director__user").prefetch_related("groups")
    
    # Calculate sum of ratios for each center
    centers_with_ratios = []
    for center in centers:
        # Sum all current_total_points from all groups in this center
        total_ratio_points = sum(
            group.current_total_points for group in center.groups.all()
        )
        # Convert back to actual ratio (stored as integer * 1000)
        total_ratio = total_ratio_points / 1000.0
        
        centers_with_ratios.append({
            "center": center,
            "director": center.director,
            "total_ratio": total_ratio,
            "total_ratio_points": total_ratio_points,
            "group_count": center.groups.count(),
        })
    
    centers_count = centers.count()
    return render(request, "owner_dashboard.html", {
        "centers": centers,
        "centers_count": centers_count,
        "centers_with_ratios": centers_with_ratios,
    })


@login_required
def educator_dashboard(request):
    user = request.user
    
    if user.role_type not in ["educator", "educator_principal"]:
        return render(request, "core/403.html", status=403)

    assigned_children_count = 0
    is_principal = (user.role_type == "educator_principal")

    try:
        if not is_principal:
            # حالة الأستاذ العادي
            educator_profile = user.educator_profile
            assigned_children_count = Child.objects.filter(assigned_educator=educator_profile).count()
        
        else:
            # حالة الـ Principal
            # تأكد أن اسم الـ related_name في الـ Model هو educator_principal_profile
            # أو استخدم user.educatorprincipal (بدون underscore إذا كان هذا هو الاسم الافتراضي)
            principal_profile = user.educatorprincipal 
            center = principal_profile.center
            
            # الآن نحن نفلتر الأطفال بناءً على كائن المركز (Center instance) مباشرة
            assigned_children_count = Child.objects.filter(center=center).count()
            
    except Exception as e:
        # إضافة print لطباعة الخطأ في الـ Terminal لمعرفة اسم الـ relation الصحيح
        print(f"Error in dashboard: {e}")
        assigned_children_count = 0

    context = {
        "assigned_children_count": assigned_children_count,
        "is_principal": is_principal,
    }
    
    return render(request, "educator_dashboard.html", context)
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
            _ = child.enrollment_forms.filter(is_active=True).first()
            child.has_enrollment_form = True
        except:
            child.has_enrollment_form = False

    return render(request, "parent_dashboard.html", {'children': children})


from django.http import JsonResponse

def get_me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)
    
    return JsonResponse({
        "user_id": str(request.user.user_id),
        "full_name": request.user.full_name,
        "email": request.user.email,
        "role_type": request.user.role_type,
        "profile_photo": request.user.profile_photo.url if request.user.profile_photo else None,
    })


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

@login_required
def manage_principal(request):
    # 1. التحقق من الصلاحية
    if request.user.role_type != 'director':
        return redirect('dashboard_redirect')
        
    director = request.user.director_profile
    center = director.organization.centers.first()
    
    # نجيبو الـ educators اللي تابعين لنفس المركز
    educators = Educator.objects.filter(center=center)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_promote = get_object_or_404(User, user_id=user_id)
        
        # 2. تحديث الـ role والـ Profile
        user_to_promote.role_type = 'educator_principal'
        user_to_promote.save()
        
        # التأكد من عدم تكرار الإنشاء إذا كان موجوداً مسبقاً
        EducatorPrincipal.objects.get_or_create(user=user_to_promote, center=center)
        
        # 3. البقاء في نفس الصفحة (Self-Redirect)
        messages.success(request, f"{user_to_promote.full_name} has been promoted successfully.")
        return redirect(request.path) 

    return render(request, 'manage_principal.html', {'educators': educators})
@login_required
def remove_principal(request):
    if request.user.role_type != 'director':
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(user_id=user_id)
        
        with transaction.atomic():
            # 1. رجعو educator عادي
            user.role_type = 'educator'
            user.save()
            
            # 2. مسح الـ profile ديال الـ Principal
            EducatorPrincipal.objects.filter(user=user).delete()
            
        return redirect('manage_principal')