from django.db.models import Q
from accounts.models import User, Educator, Director
from dashboard.models import Child, ParentChildRelationship
from communication.models import DirectorConnection
from .models import ChatInvitation, Block

def get_allowed_contact_ids(user):
    role = user.role_type
    allowed_user_ids = set()

    if role == "parent":
        children = Child.objects.filter(parent_relationships__parent__user=user)
        educator_user_ids = Educator.objects.filter(
            assigned_children__in=children
        ).values_list("user_id", flat=True).distinct()
        allowed_user_ids.update(educator_user_ids)

    elif role == "director":
        director_profile = getattr(user, "director_profile", None)
        if director_profile:
            if director_profile.organization:
                internal_directors = Director.objects.filter(
                    organization=director_profile.organization
                ).exclude(user_id=user.user_id).values_list("user_id", flat=True)
                allowed_user_ids.update(internal_directors)

            confirmed_connections = DirectorConnection.objects.filter(
                (Q(from_director=director_profile) | Q(to_director=director_profile)),
                is_confirmed=True
            ).values_list("from_director__user_id", "to_director__user_id")

            for from_id, to_id in confirmed_connections:
                if from_id != user.user_id: allowed_user_ids.add(from_id)
                if to_id != user.user_id: allowed_user_ids.add(to_id)

            managed_center = getattr(director_profile, "managed_center", None)
            if managed_center:
                educator_user_ids = managed_center.educators.values_list("user_id", flat=True)
                allowed_user_ids.update(educator_user_ids)

    elif role == "educator":
        educator_profile = getattr(user, "educator_profile", None)
        if educator_profile:
            if educator_profile.center and educator_profile.center.director:
                allowed_user_ids.add(educator_profile.center.director.user_id)
            
            parent_user_ids = ParentChildRelationship.objects.filter(
                child__assigned_educator=educator_profile
            ).values_list("parent__user_id", flat=True).distinct()
            allowed_user_ids.update(parent_user_ids)

    else:
        # For other roles like admin/owner, they can talk to everyone
        allowed_user_ids = set(User.objects.exclude(user_id=user.user_id).values_list("user_id", flat=True))

    # Add accepted invitations
    accepted_invites = ChatInvitation.objects.filter(
        (Q(sender=user) | Q(recipient=user)),
        status='accepted'
    ).values_list('sender_id', 'recipient_id')
    
    for s_id, r_id in accepted_invites:
        if s_id != user.user_id: allowed_user_ids.add(s_id)
        if r_id != user.user_id: allowed_user_ids.add(r_id)

    # Remove blocked users
    blocked_by_me = Block.objects.filter(blocker=user).values_list('blocked_id', flat=True)
    i_am_blocked_by = Block.objects.filter(blocked=user).values_list('blocker_id', flat=True)
    all_blocked_ids = set(list(blocked_by_me) + list(i_am_blocked_by))
    
    allowed_user_ids = allowed_user_ids - all_blocked_ids
    
    return allowed_user_ids
