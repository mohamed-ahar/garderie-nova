import email
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import DirectorProfile, OwnerProfile, ParentProfile, User
from core.models import Center
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
    # Hna mli l-base.html at-chof user.role_type == 'owner', at-tl3 lih navbar d l-owner
    return render(request, "owner_dashboard.html")


@login_required
def director_dashboard(request):
    # Idem pour le directeur
    return render(request, "director_dashboard.html")


@login_required
def educator_dashboard(request):
    return render(request, "educator_dashboard.html")


@login_required
def parent_dashboard(request):
    return render(request, "parent_dashboard.html")


@login_required
def personal_profile(request):
    user = request.user
    role_info = None

    # Check l-role (khass t-koun lower case 'owner' hit hka dertiha f models)
    if user.role_type == "owner":
        role_info = OwnerProfile.objects.filter(user=user).first()
    elif user.role_type == "director":
        role_info = DirectorProfile.objects.filter(user=user).first()
    elif user.role_type == "parent":
        role_info = ParentProfile.objects.filter(user=user).first()

    context = {
        "user": user,
        "role_info": role_info,
        "page_title": "Identity Console",
    }

    return render(request, "profile.html", context)


# ownner li imken li i crerr director
"""
def is_owner(user):
   return user.role_type == 'owner'

@login_required
@user_passes_test(is_owner)
def create_director(request):
    
    if request.method == 'POST':
        form = DirectorCreationForm(request.POST) # type: ignore
        if form.is_valid():
            # 1. Creer l-User account
            user = form.save(commit=False)
            user.role_type = 'director'
            user.save()
            
            # 2. Creer l-profile Director
            Director.objects.create(
                user=user,
                qualification_cert=form.cleaned_data['qualification_cert'],
                hired_at=form.cleaned_data['hired_at']
            )
            
            # 3. Link Center to Director
            center_id = form.cleaned_data['center_id']
            center = get_object_or_404(Center, center_id=center_id)
            center.director = user.director
            center.save()
            
            return redirect('owner_dashboard')
    else:
        form = DirectorCreationForm()
    
    return render(request, 'accounts/create_director.html', {'form': form})
"""


"""
@login_required
def director_dashboard(request):
    
    center = getattr(request.user.director, 'center', None)
    
    context = {
        'center': center,
        'educators': center.educators.all() if center else [],
        'groups': center.group_set.all() if center else []
    }
    return render(request, 'accounts/director_dashboard.html', context)
"""
