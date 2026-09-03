from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Subquery, Count, Max
from django.core.paginator import Paginator
from accounts.models import User, Educator, Director
from dashboard.models import Child, ParentChildRelationship
from communication.models import DirectorConnection
from .models import Message

@login_required
def get_contacts(request):
    user = request.user
    role = user.role_type
    allowed_user_ids = set()

    # 1. PARENT: Educators of their children
    if role == "parent":
        children = Child.objects.filter(parent_relationships__parent__user=user)
        educator_user_ids = Educator.objects.filter(
            assigned_children__in=children
        ).values_list("user_id", flat=True).distinct()
        allowed_user_ids.update(educator_user_ids)

    # 2. DIRECTOR: Internal directors + confirmed external directors + Educators in their Center
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

    # 3. EDUCATOR: Director of their Center + Parents of their assigned children
    elif role == "educator":
        educator_profile = getattr(user, "educator_profile", None)
        if educator_profile:
            if educator_profile.center and educator_profile.center.director:
                allowed_user_ids.add(educator_profile.center.director.user_id)
            
            parent_user_ids = ParentChildRelationship.objects.filter(
                child__assigned_educator=educator_profile
            ).values_list("parent__user_id", flat=True).distinct()
            allowed_user_ids.update(parent_user_ids)

    # 4. OWNER/ADMIN: Can talk to everyone
    else:
        allowed_user_ids = set(User.objects.exclude(user_id=user.user_id).values_list("user_id", flat=True))

    # Fetch contacts with last message and unread count
    last_msg_subquery = Message.objects.filter(
        (Q(sender=OuterRef('pk')) & Q(recipient=user)) |
        (Q(sender=user) & Q(recipient=OuterRef('pk')))
    ).order_by('-timestamp')

    unread_count_subquery = Message.objects.filter(
        sender=OuterRef('pk'),
        recipient=user,
        is_read=False
    ).values('sender').annotate(cnt=Count('pk')).values('cnt')

    contacts_qs = User.objects.filter(user_id__in=allowed_user_ids).annotate(
        last_message_text=Subquery(last_msg_subquery.values('content')[:1]),
        unread_count=Subquery(unread_count_subquery),
        last_msg_time=Subquery(last_msg_subquery.values('timestamp')[:1])
    ).order_by('-last_msg_time', 'full_name')

    contacts = [
        {
            "id": str(u.user_id),
            "name": u.full_name,
            "role": u.role_type,
            "avatar": u.full_name[:2].upper() if u.full_name else "??",
            "lastMessage": u.last_message_text or "",
            "unreadCount": u.unread_count or 0,
        }
        for u in contacts_qs
    ]

    return JsonResponse({"contacts": contacts})

@login_required
def mark_messages_as_read(request, recipient_id):
    messages = Message.objects.filter(
        sender_id=recipient_id,
        recipient=request.user,
        is_read=False
    )
    if messages.exists():
        messages.update(is_read=True, is_delivered=True)
        
        # Notify sender via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{recipient_id}",
            {
                "type": "messages_read",
                "recipient_id": str(request.user.user_id)
            }
        )
        
    return JsonResponse({"status": "success"})

@login_required
def get_messages(request, recipient_id):
    user = request.user
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 50)

    messages_qs = Message.objects.filter(
        (Q(sender=user) & Q(recipient_id=recipient_id)) |
        (Q(sender_id=recipient_id) & Q(recipient=user))
    ).order_by('-timestamp')

    paginator = Paginator(messages_qs, page_size)
    page_obj = paginator.get_page(page_number)

    messages = [
        {
            "id": msg.id,
            "sender_id": str(msg.sender.user_id),
            "sender_name": msg.sender.full_name,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "is_delivered": msg.is_delivered,
            "is_read": msg.is_read,
        }
        for msg in reversed(page_obj.object_list)
    ]

    return JsonResponse({
        "messages": messages,
        "has_next": page_obj.has_next(),
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
        "total_pages": paginator.num_pages,
    })
