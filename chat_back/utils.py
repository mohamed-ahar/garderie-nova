from django.db.models import Q
from accounts.models import User, Educator, Director
from dashboard.models import Child, ParentChildRelationship
from communication.models import DirectorConnection
from .models import ChatInvitation


def get_allowed_contact_ids(user):
    role = user.role_type
    allowed_user_ids = set()

    if role == "parent":
        # 1. Educators assigned to their children
        children = Child.objects.filter(parent_relationships__parent__user=user)
        educator_user_ids = (
            Educator.objects.filter(assigned_children__in=children)
            .values_list("user_id", flat=True)
            .distinct()
        )
        allowed_user_ids.update(educator_user_ids)

        # 2. Other parents who have children in the same center(s)
        # Note: Parents in the same center can see and talk to each other directly
        centers = children.values_list("center_id", flat=True).distinct()
        peer_parent_ids = (
            ParentChildRelationship.objects.filter(child__center_id__in=centers)
            .exclude(parent__user=user)
            .values_list("parent_id", flat=True)
            .distinct()
        )
        allowed_user_ids.update(peer_parent_ids)

    elif role in ["director", "vice_director"]:
        # Allow speaking with ALL other directors
        all_directors = (
            User.objects.filter(role_type="director")
            .exclude(user_id=user.user_id)
            .values_list("user_id", flat=True)
        )
        allowed_user_ids.update(all_directors)

        # Get the center (different profile names for director and vice_director)
        center = None
        if role == "director":
            profile = getattr(user, "director_profile", None)
            center = getattr(profile, "managed_center", None) if profile else None
        else: # vice_director
            profile = getattr(user, "vice_director_profile", None)
            center = profile.center if profile else None

        if center:
            # Educators in the center
            educator_user_ids = center.educators.values_list("user_id", flat=True)
            allowed_user_ids.update(educator_user_ids)

            # Only show parents who have children in this center
            parent_user_ids = (
                ParentChildRelationship.objects.filter(child__center=center)
                .values_list("parent_id", flat=True)
                .distinct()
            )
            allowed_user_ids.update(parent_user_ids)

    elif role == "educator":
        educator_profile = getattr(user, "educator_profile", None)
        if educator_profile:
            # 1. Director of their center
            if educator_profile.center and educator_profile.center.director:
                allowed_user_ids.add(educator_profile.center.director.user_id)

            # 2. Parents of children assigned to them
            parent_user_ids = (
                ParentChildRelationship.objects.filter(
                    child__assigned_educator=educator_profile
                )
                .values_list("parent_id", flat=True)
                .distinct()
            )
            allowed_user_ids.update(parent_user_ids)

            # Note: Peer educators in the same center are NOT added here automatically
            # because they require an invitation to speak (as per initial rules).
            # They will be added via the 'accepted_invites' logic below.

    elif role == "owner":
        owner_profile = getattr(user, "owner_profile", None)
        if owner_profile:
            org = getattr(owner_profile, "owned_organization", None)
            if org:
                # Directors in org
                org_directors = User.objects.filter(role_type="director", director_profile__organization=org).values_list("user_id", flat=True)
                allowed_user_ids.update(org_directors)
                # Educators in org
                org_educators = User.objects.filter(role_type="educator", educator_profile__center__organization=org).values_list("user_id", flat=True)
                allowed_user_ids.update(org_educators)
                # Parents in org
                org_parents = ParentChildRelationship.objects.filter(child__center__organization=org).values_list("parent_id", flat=True).distinct()
                allowed_user_ids.update(org_parents)

    # For 'admin' or if somehow role is not handled above, we can decide.
    # If the user is an admin (is_staff/is_superuser), they should see everyone.
    if user.is_staff or user.is_superuser:
        all_users = User.objects.exclude(user_id=user.user_id).values_list("user_id", flat=True)
        allowed_user_ids.update(all_users)

    # Add accepted invitations (this allows cross-role/cross-center talk if manually invited)
    # This covers Educators inviting peer Educators.
    accepted_invites = ChatInvitation.objects.filter(
        (Q(sender=user) | Q(recipient=user)), status="accepted"
    ).values_list("sender_id", "recipient_id")

    for s_id, r_id in accepted_invites:
        if s_id != user.user_id:
            allowed_user_ids.add(s_id)
        if r_id != user.user_id:
            allowed_user_ids.add(r_id)

    return allowed_user_ids
