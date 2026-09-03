from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Subquery, Count, Max
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from accounts.models import User, Educator, Director
from dashboard.models import Child, ParentChildRelationship
from communication.models import DirectorConnection
from .models import Message, ChatInvitation, Block
from .utils import get_allowed_contact_ids
from django.views.decorators.csrf import csrf_exempt

@login_required
def block_user(request, user_id):
    try:
        user_to_block = User.objects.get(user_id=user_id)
        Block.objects.get_or_create(blocker=request.user, blocked=user_to_block)
        ChatInvitation.objects.filter(
            (Q(sender=request.user) & Q(recipient=user_to_block)) |
            (Q(sender=user_to_block) & Q(recipient=request.user))
        ).delete()
        return JsonResponse({"status": "success"})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

@login_required
def unblock_user(request, user_id):
    try:
        user_to_unblock = User.objects.get(user_id=user_id)
        Block.objects.filter(blocker=request.user, blocked=user_to_unblock).delete()
        return JsonResponse({"status": "success"})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

@login_required
def get_blocked_users(request):
    blocked_rels = Block.objects.filter(blocker=request.user).select_related('blocked')
    return JsonResponse({
        "blocked_users": [
            {
                "id": str(b.blocked.user_id),
                "name": b.blocked.full_name,
                "email": b.blocked.email,
                "role": b.blocked.role_type
            } for b in blocked_rels
        ]
    })

@login_required
def get_contacts(request):
    user = request.user
    allowed_user_ids = get_allowed_contact_ids(user)

    blocked_by_me = list(Block.objects.filter(blocker=user).values_list('blocked_id', flat=True))

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
            "lastMessage": u.last_message_text if u.last_message_text else (f"Sent an {u.last_message_type}" if u.last_message_type else ""),
            "unreadCount": u.unread_count if u.unread_count else 0,
            "is_blocked": str(u.user_id) in blocked_by_me,
            "is_online": u.is_online
        }
        for u in contacts_qs
    ]

    return JsonResponse({"contacts": contacts})

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({"users": []})
    
    users = User.objects.filter(
        Q(full_name__icontains=query) | Q(email__icontains=query)
    ).exclude(user_id=request.user.user_id)[:10]
    
    sent_invites = {i.recipient_id: i.status for i in request.user.sent_invitations.all()}
    received_invites = {i.sender_id: i.status for i in request.user.received_invitations.all()}
    
    results = []
    for u in users:
        status = "none"
        if u.id in sent_invites:
            status = f"sent_{sent_invites[u.id]}"
        elif u.id in received_invites:
            status = f"received_{received_invites[u.id]}"
            
        results.append({
            "id": str(u.user_id),
            "name": u.full_name,
            "email": u.email,
            "role": u.role_type,
            "invitation_status": status
        })
        
    return JsonResponse({"users": results})

@login_required
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
            
            is_blocked = Block.objects.filter(
                (Q(blocker=request.user, blocked=recipient)) |
                (Q(blocker=recipient, blocked=request.user))
            ).exists()
            
            is_connected = ChatInvitation.objects.filter(
                (Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user)),
                status='accepted'
            ).exists() or request.user.role_type in ["admin", "owner"] or recipient.role_type in ["admin", "owner"]

            if is_blocked or not is_connected:
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
