from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from ..models import (
    Center,
    Child,
    ParentChildRelationship,
    ParentProfile,
    CenterParentAccess,
    Notification,
    User,
)


@login_required(login_url="login")
def request_center_access(request):
    user = request.user
    if user.role_type != "parent":
        return render(request, "core/403.html", status=403)

    try:
        parent_profile = user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, "Profil parent introuvable.")
        return redirect("dashboard_redirect")

    if request.method == "POST":
        center_id = request.POST.get("center_id")
        center = get_object_or_404(Center, center_id=center_id)

        # Check if request already exists
        existing_request = CenterParentAccess.objects.filter(
            center=center, parent=parent_profile
        ).first()

        if existing_request:
            if existing_request.status == "pending":
                messages.warning(
                    request,
                    f"Vous avez déjà une demande en attente pour {center.name}.",
                )
            elif existing_request.status == "accepted":
                messages.info(request, f"Vous avez déjà accès à {center.name}.")
            elif existing_request.status == "rejected":
                # Allow re-requesting if rejected
                existing_request.status = "pending"
                existing_request.created_at = timezone.now()  # Reset time to bump it up
                existing_request.save()

                # Notify Director(s) again
                if center.director:
                    Notification.objects.create(
                        user=center.director.user,
                        title="Parent Access Request Renewed",
                        message=(
                            f"A parent has renewed their access request for your center.\n\n"
                            f"Parent name: {user.full_name}\n"
                            f"Request type: Renewed parent access request\n"
                            f"Please review and take action from the access requests page."
                        ),
                        action_url="/access-requests/",
                    )
                messages.success(
                    request, f"Votre demande pour {center.name} a été renvoyée."
                )
        else:
            CenterParentAccess.objects.create(
                center=center, parent=parent_profile, status="pending"
            )

            # Notify Director(s)
            if center.director:
                Notification.objects.create(
                    user=center.director.user,
                    title="New Parent Access Request",
                    message=(
                        f"A parent has requested access to your center.\n\n"
                        f"Parent name: {user.full_name}\n"
                        f"Request type: Parent access to center\n"
                        f"Please review and respond to this request from the access requests page."
                    ),
                    action_url="/access-requests/",
                )

            messages.success(
                request, f"Demande envoyée à {center.name}. En attente d'approbation."
            )

        return redirect("request_center_access")

    # Show centers where the parent does NOT have an accepted request
    # Or just show all centers with their status
    all_centers = Center.objects.all()
    my_requests = CenterParentAccess.objects.filter(parent=parent_profile)
    request_map = {req.center_id: req.status for req in my_requests}

    centers_data = []
    for c in all_centers:
        status = request_map.get(c.center_id, None)
        centers_data.append({"center": c, "status": status})

    return render(
        request, "core/parents/request_access.html", {"centers_data": centers_data}
    )


@login_required(login_url="login")
def register_child_view(request):
    user = request.user
    if user.role_type != "parent":
        return render(request, "core/403.html", status=403)

    if request.method == "POST":
        child_name = request.POST.get("child_name")
        birth_date = request.POST.get("birth_date")
        contact_phone = request.POST.get("contact_phone")
        contact_email = request.POST.get("contact_email")
        center_id = request.POST.get("center_id")
        second_parent_email = request.POST.get("second_parent_email")

        # Determine Center
        center = None
        if center_id:
            # Security check: Ensure parent has access
            center = get_object_or_404(Center, center_id=center_id)
            has_access = CenterParentAccess.objects.filter(
                center=center, parent__user=user, status="accepted"
            ).exists()

            if not has_access:
                messages.error(
                    request,
                    "Vous n'avez pas la permission d'inscrire un enfant dans ce centre.",
                )
                return redirect("register_child")

        else:
            messages.error(request, "Veuillez sélectionner une garderie.")
            return redirect("register_child")

        if not center:
            messages.error(request, "Aucune garderie disponible.")
            return redirect("dashboard_redirect")
        
        # Verify Second Parent if provided
        second_parent_profile = None
        if second_parent_email:
            try:
                # Case insensitive email check? Standard Django is case sensitive usually, but emails should be treated carefully.
                # Assuming exact match for now as per "verified to check if that person exists"
                second_parent_user = User.objects.filter(email=second_parent_email).first()
                
                if not second_parent_user:
                     messages.error(request, f"Aucun utilisateur trouvé avec l'email : {second_parent_email}")
                     return redirect("register_child")
                
                if second_parent_user.role_type != 'parent':
                     messages.error(request, "L'email fourni pour le deuxième parent n'appartient pas à un compte parent.")
                     return redirect("register_child")
                
                if hasattr(second_parent_user, 'parent_profile'):
                     second_parent_profile = second_parent_user.parent_profile
                else:
                     messages.error(request, "Le compte du deuxième parent est incomplet (profil manquant).")
                     return redirect("register_child")
                     
                if second_parent_user == user:
                     messages.error(request, "Vous ne pouvez pas vous ajouter vous-même comme deuxième parent.")
                     return redirect("register_child")

            except Exception as e:
                messages.error(request, f"Erreur lors de la vérification du deuxième parent : {str(e)}")
                return redirect("register_child")

        # Split name
        parts = child_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        # Create Child
        # Store contact info in medical_info as a temporary storage or metadata since Child model lacks these fields
        extra_info = {
            "waitlist_contact_phone": contact_phone,
            "waitlist_contact_email": contact_email,
        }

        child = Child.objects.create(
            center=center,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            status="waitlist",
            medical_info=extra_info,
        )

        # Create Relationship for the registering parent
        parent_profile = get_object_or_404(ParentProfile, user=user)
        ParentChildRelationship.objects.create(
            parent=parent_profile,
            child=child,
            relationship_type="Parent",
            is_emergency_contact=True,
        )
        
        # Create Relationship for the second parent if applicable
        if second_parent_profile:
            ParentChildRelationship.objects.create(
                parent=second_parent_profile,
                child=child,
                relationship_type="Parent",
                is_emergency_contact=True, 
            )
            # Notify the second parent
            Notification.objects.create(
                user=second_parent_profile.user,
                title="Nouvel enfant ajouté",
                message=f"Vous avez été ajouté comme parent pour {child.first_name} {child.last_name} par {user.full_name}.",
                action_url="/parents/my-children/"
            )

        director_user = center.director.user
        Notification.objects.create(
            user=director_user,
            title="New Waitlist Registration",
            message=(
                "A child has been added to your center’s waitlist.\n\n"
                f"Child name: {child.first_name} {child.last_name}\n"
                f"Parent name: {user.get_full_name() or user.username}\n"
                f"Center: {center.name}\n"
                "You can review the waitlist for further details."
            ),
            action_url="/waitlist/",
        )

        messages.success(request, "Enfant inscrit sur la liste d'attente avec succès.")
        return redirect("dashboard_redirect")

    # Filter centers where parent is accepted
    centers = Center.objects.filter(
        parent_access_requests__parent__user=user,
        parent_access_requests__status="accepted",
    )
    print(
        "here is the centers that accepted this parent to register their child ",
        centers,
    )
    if not centers.exists():
        messages.warning(
            request,
            "Vous devez d'abord obtenir l'accès à un centre avant d'inscrire un enfant.",
        )
        return redirect("request_center_access")

    return render(request, "core/parents/register_child.html", {"centers": centers})


@login_required(login_url="login")
def parent_children_list(request):
    user = request.user
    if user.role_type != "parent":
        return render(request, "core/403.html", status=403)

    try:
        parent_profile = user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, "Profil parent introuvable.")
        return redirect("dashboard_redirect")

    # Get all relationships for this parent
    relationships = ParentChildRelationship.objects.filter(
        parent=parent_profile
    ).select_related("child", "child__center")

    # Extract children from relationships
    children = [rel.child for rel in relationships]

    return render(request, "core/parents/child_list.html", {"children": children})
