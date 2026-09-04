from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Subquery, Count, Max
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from accounts.models import User, Educator, Director
from dashboard.models import Child, ParentChildRelationship
from communication.models import DirectorConnection
from .models import Message, ChatInvitation
from .utils import get_allowed_contact_ids
from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt
def get_contacts(request):
    user = request.user
    allowed_user_ids = get_allowed_contact_ids(user)

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
        last_message_type=Subquery(last_msg_subquery.values('attachment_type')[:1]),
        unread_count=Coalesce(Subquery(unread_count_subquery), 0),
        last_msg_time=Subquery(last_msg_subquery.values('timestamp')[:1])
    ).order_by('-last_msg_time', 'full_name')

    # Mark current user as online if they are fetching contacts
    if not user.is_online:
        user.is_online = True
        user.save(update_fields=['is_online'])

    contacts = [
        {
            "id": str(u.user_id),
            "name": u.full_name,
            "role": u.role_type,
            "avatar": u.full_name[:2].upper() if u.full_name else "??",
            "profile_photo": request.build_absolute_uri(u.profile_photo.url) if u.profile_photo else None,
            "lastMessage": u.last_message_text if u.last_message_text else (f"Sent an {u.last_message_type}" if u.last_message_type else ""),
            "unreadCount": u.unread_count if u.unread_count else 0,
            "is_online": u.is_online
        }
        for u in contacts_qs
    ]

    return JsonResponse({"contacts": contacts})

@login_required
@csrf_exempt
def search_users(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({"users": []})
    
    user = request.user
    users_qs = User.objects.filter(
        Q(full_name__icontains=query) | Q(email__icontains=query)
    ).exclude(user_id=user.user_id)

    if user.role_type == 'educator':
        educator_profile = getattr(user, 'educator_profile', None)
        if educator_profile and educator_profile.center:
            users_qs = users_qs.filter(
                role_type='educator',
                educator_profile__center=educator_profile.center
            )
        else:
            users_qs = users_qs.none()
    elif user.role_type == 'parent':
        parent_profile = getattr(user, 'parent_profile', None)
        if parent_profile:
            # Find all centers where this parent has children
            centers = Child.objects.filter(parent_relationships__parent=parent_profile).values_list('center', flat=True).distinct()
            users_qs = users_qs.filter(
                role_type='parent',
                parent_profile__children_relationships__child__center__in=centers
            ).distinct()
        else:
            users_qs = users_qs.none()
    elif user.role_type in ['director', 'vice_director']:
        # Directors can find ALL other directors
        # PLUS educators and parents in their center
        center = None
        if user.role_type == "director":
            profile = getattr(user, "director_profile", None)
            center = getattr(profile, "managed_center", None) if profile else None
        else: # vice_director
            profile = getattr(user, "vice_director_profile", None)
            center = profile.center if profile else None
        
        if center:
            users_qs = users_qs.filter(
                Q(role_type='director') | 
                Q(role_type='educator', educator_profile__center=center) |
                Q(role_type='parent', parent_profile__children_relationships__child__center=center)
            ).distinct()
        else:
            users_qs = users_qs.filter(role_type='director')
    elif user.role_type == 'owner':
        owner_profile = getattr(user, "owner_profile", None)
        org = getattr(owner_profile, "owned_organization", None) if owner_profile else None
        if org:
            users_qs = users_qs.filter(
                Q(role_type='director', director_profile__organization=org) |
                Q(role_type='educator', educator_profile__center__organization=org) |
                Q(role_type='parent', parent_profile__children_relationships__child__center__organization=org)
            ).distinct()
        else:
            users_qs = users_qs.none()
    
    users = users_qs[:10]
    
    sent_invites = {}
    received_invites = {}
    if user.role_type == 'educator':
        sent_invites = {i.recipient_id: i.status for i in request.user.sent_invitations.all()}
        received_invites = {i.sender_id: i.status for i in request.user.received_invitations.all()}
    
    results = []
    for u in users:
        status = "none"
        if user.role_type == 'educator':
            if u.user_id in sent_invites:
                status = f"sent_{sent_invites[u.user_id]}"
            elif u.user_id in received_invites:
                status = f"received_{received_invites[u.user_id]}"
            
        results.append({
            "id": str(u.user_id),
            "name": u.full_name,
            "email": u.email,
            "role": u.role_type,
            "profile_photo": request.build_absolute_uri(u.profile_photo.url) if u.profile_photo else None,
            "invitation_status": status
        })
        
    return JsonResponse({"users": results})

@login_required
@csrf_exempt
def send_invitation(request):
    recipient_id = request.POST.get('recipient_id')
    if not recipient_id:
        return JsonResponse({"error": "recipient_id is required"}, status=400)
    
    try:
        recipient = User.objects.get(user_id=recipient_id)
        invite, created = ChatInvitation.objects.get_or_create(
            sender=request.user,
            recipient=recipient,
            defaults={'status': 'pending'}
        )
        if not created and invite.status != 'pending':
            invite.status = 'pending'
            invite.save()
            
        return JsonResponse({"status": "success", "invitation_id": invite.id})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

@login_required
@csrf_exempt
def manage_invitation(request, invitation_id):
    action = request.POST.get('action')
    try:
        if action == 'revoke':
            invite = ChatInvitation.objects.get(id=invitation_id, sender=request.user)
            invite.delete()
        else:
            invite = ChatInvitation.objects.get(id=invitation_id, recipient=request.user)
            if action == 'accept':
                invite.status = 'accepted'
                invite.save()
            elif action == 'reject':
                invite.status = 'rejected'
                invite.save()
        return JsonResponse({"status": "success"})
    except ChatInvitation.DoesNotExist:
        return JsonResponse({"error": "Invitation not found"}, status=404)

@login_required
@csrf_exempt
def get_invitations(request):
    received = request.user.received_invitations.filter(status='pending')
    sent = request.user.sent_invitations.filter(status='pending')
    
    return JsonResponse({
        "received": [
            {
                "id": i.id,
                "sender_name": i.sender.full_name,
                "sender_id": str(i.sender.user_id),
                "created_at": i.created_at.isoformat()
            } for i in received
        ],
        "sent": [
            {
                "id": i.id,
                "recipient_name": i.recipient.full_name,
                "recipient_id": str(i.recipient.user_id),
                "created_at": i.created_at.isoformat()
            } for i in sent
        ]
    })

@login_required
@csrf_exempt
def mark_messages_as_read(request, recipient_id):
    messages = Message.objects.filter(
        sender_id=recipient_id,
        recipient=request.user,
        is_read=False
    )
    if messages.exists():
        messages.update(is_read=True, is_delivered=True)
        
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
@csrf_exempt
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
            "sender_profile_photo": request.build_absolute_uri(msg.sender.profile_photo.url) if msg.sender.profile_photo else None,
            "content": msg.content,
            "attachment": request.build_absolute_uri(msg.attachment.url) if msg.attachment else None,
            "attachment_type": msg.attachment_type,
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

@login_required
@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content', '')
        attachment_type = request.POST.get('attachment_type', 'file')

        if not recipient_id:
            return JsonResponse({"error": "recipient_id is required"}, status=400)

        try:
            recipient = User.objects.get(user_id=recipient_id)
            
            # Allow messaging if:
            # 1. Either is an admin/owner
            # 2. Both are directors
            # 3. They have an accepted invitation
            # 4. Peer Parents in the same center
            # 5. Peer Educators in the same center
            # 6. Educator <-> Director of same center
            # 7. Educator <-> Parent of assigned child
            
            is_connected = (
                request.user.role_type in ["admin", "owner"] or 
                recipient.role_type in ["admin", "owner"] or
                (request.user.role_type == "director" and recipient.role_type == "director") or
                ChatInvitation.objects.filter(
                    (Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user)),
                    status='accepted'
                ).exists()
            )

            if not is_connected:
                # Check contextual connections
                user = request.user
                if user.role_type == "parent" and recipient.role_type == "parent":
                    user_centers = Child.objects.filter(parent_relationships__parent__user=user).values_list("center_id", flat=True)
                    is_connected = Child.objects.filter(parent_relationships__parent__user=recipient, center_id__in=user_centers).exists()
                
                elif user.role_type == "educator" and recipient.role_type == "director":
                    u_prof = getattr(user, "educator_profile", None)
                    r_prof = getattr(recipient, "director_profile", None)
                    is_connected = u_prof and r_prof and u_prof.center_id == getattr(r_prof.managed_center, "center_id", None)
                
                elif user.role_type == "director" and recipient.role_type == "educator":
                    u_prof = getattr(user, "director_profile", None)
                    r_prof = getattr(recipient, "educator_profile", None)
                    is_connected = u_prof and r_prof and getattr(u_prof.managed_center, "center_id", None) == r_prof.center_id

                elif user.role_type == "parent" and recipient.role_type == "educator":
                    is_connected = Child.objects.filter(parent_relationships__parent__user=user, assigned_educator__user=recipient).exists()
                
                elif user.role_type == "educator" and recipient.role_type == "parent":
                    is_connected = Child.objects.filter(parent_relationships__parent__user=recipient, assigned_educator__user=user).exists()

            if not is_connected:
                return JsonResponse({"error": "No permission to message this user"}, status=403)

            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                attachment=uploaded_file,
                attachment_type=attachment_type
            )
            
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            
            message_data = {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "sender_id": str(request.user.user_id),
                    "recipient_id": str(recipient_id),
                    "sender_name": request.user.full_name,
                    "sender_profile_photo": request.build_absolute_uri(request.user.profile_photo.url) if request.user.profile_photo else None,
                    "content": content,
                    "attachment": request.build_absolute_uri(message.attachment.url),
                    "attachment_type": attachment_type,
                    "timestamp": message.timestamp.isoformat(),
                    "is_delivered": message.is_delivered,
                    "is_read": message.is_read,
                }
            }
            
            async_to_sync(channel_layer.group_send)(f"user_{recipient_id}", message_data)
            async_to_sync(channel_layer.group_send)(f"user_{request.user.id}", message_data)

            return JsonResponse({
                "status": "success",
                "message": message_data["message"]
            })
        except User.DoesNotExist:
            return JsonResponse({"error": "Recipient not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)
