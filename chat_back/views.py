from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Subquery, Count, Max
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from accounts.models import User, Educator, Director
from dashboard.models import Child, ParentChildRelationship, Group, Center
from communication.models import DirectorConnection
from .models import Message, ChatInvitation, FeedPost, PostReaction, Comment, CommentReaction, PostView, BookmarkedPost
from .utils import get_allowed_contact_ids
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
@csrf_exempt
def get_feed(request):
    user = request.user
    
    # Base filter: same center(s)
    user_centers = []
    if user.role_type == 'director':
        if hasattr(user, 'director_profile') and user.director_profile.managed_center:
            user_centers.append(user.director_profile.managed_center)
    elif user.role_type == 'vice_director':
        if hasattr(user, 'vice_director_profile') and user.vice_director_profile.center:
            user_centers.append(user.vice_director_profile.center)
    elif user.role_type == 'educator':
        if hasattr(user, 'educator_profile') and user.educator_profile.center:
            user_centers.append(user.educator_profile.center)
    elif user.role_type == 'parent':
        user_centers = list(Center.objects.filter(children__parent_relationships__parent__user=user).distinct())
    elif user.role_type == 'owner':
        if hasattr(user, 'owner_profile') and user.owner_profile.owned_organization:
            user_centers = list(user.owner_profile.owned_organization.centers.all())

    if not user_centers and not user.is_staff:
        return JsonResponse({"posts": []})

    # Posts from these centers
    posts_qs = FeedPost.objects.filter(center__in=user_centers).distinct()

    # Filter by author (for profile view)
    author_id = request.GET.get('author_id')
    if author_id:
        posts_qs = posts_qs.filter(author__user_id=author_id)

    # Filter by search query
    query = request.GET.get('q', '')
    if query:
        posts_qs = posts_qs.filter(
            Q(content__icontains=query) |
            Q(author__full_name__icontains=query) |
            Q(tags__icontains=query)
        )

    # Filter by visibility
    is_staff = user.role_type in ['director', 'vice_director', 'educator', 'owner'] or user.is_staff
    
    if not is_staff:
        parent_groups = Group.objects.filter(enrolled_children__parent_relationships__parent__user=user).distinct()
        posts_qs = posts_qs.filter(
            Q(visibility='all_parents') |
            Q(visibility='specific_groups', target_groups__in=parent_groups) |
            Q(visibility='specific_parents', target_parents=user) |
            Q(author=user)
        ).distinct()

    filter_type = request.GET.get('type', 'all')
    if filter_type != 'all':
        posts_qs = posts_qs.filter(tags__icontains=filter_type)

    posts_qs = posts_qs.order_by('-timestamp')
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(posts_qs, 10)
    page_obj = paginator.get_page(page_number)

    posts = []
    for post in page_obj:
        user_reaction = PostReaction.objects.filter(post=post, user=user).first()
        is_bookmarked = BookmarkedPost.objects.filter(post=post, user=user).exists()
        
        media_items = []
        if post.image:
            media_items.append({
                "url": request.build_absolute_uri(post.image.url),
                "type": "image"
            })
        for media in post.media_files.all():
            media_items.append({
                "url": request.build_absolute_uri(media.file.url),
                "type": media.media_type
            })
        
        post_data = {
            "id": post.id,
            "author": {
                "id": str(post.author.user_id),
                "name": post.author.full_name,
                "role": post.author.role_type,
                "profile_photo": request.build_absolute_uri(post.author.profile_photo.url) if post.author.profile_photo else None,
            },
            "content": post.content,
            "image": request.build_absolute_uri(post.image.url) if post.image else None,
            "media": media_items,
            "visibility": post.visibility,
            "tags": post.tags,
            "target_group_names": list(post.target_groups.values_list('name', flat=True)),
            "timestamp": post.timestamp.isoformat(),
            "reactions_count": post.reactions.count(),
            "comments_count": post.comments.filter(parent=None).count(), # Only top-level count
            "user_reaction": user_reaction.reaction_type if user_reaction else None,
            "is_bookmarked": is_bookmarked,
            "center_name": post.center.name
        }
        
        if is_staff:
            post_data["views_count"] = post.views.count()
            
        posts.append(post_data)

    return JsonResponse({
        "posts": posts,
        "has_next": page_obj.has_next(),
        "total_pages": paginator.num_pages
    })

@login_required
@csrf_exempt
def toggle_bookmark(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(FeedPost, id=post_id)
        bookmark, created = BookmarkedPost.objects.get_or_create(user=request.user, post=post)
        if not created:
            bookmark.delete()
            return JsonResponse({"status": "unbookmarked"})
        return JsonResponse({"status": "bookmarked"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def react_to_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment, 
            user=request.user,
            defaults={'reaction_type': 'like'}
        )
        if not created:
            reaction.delete()
            return JsonResponse({"status": "unreacted"})
        return JsonResponse({"status": "reacted"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def mark_post_seen(request, post_id):
    if request.method == 'POST':
        try:
            post = FeedPost.objects.get(id=post_id)
            PostView.objects.get_or_create(post=post, user=request.user)
            return JsonResponse({"status": "success"})
        except FeedPost.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def create_post(request):
    if request.user.role_type not in ['director', 'vice_director', 'educator', 'owner'] and not request.user.is_staff:
        return JsonResponse({"error": "Only staff can create posts"}, status=403)

    if request.method == 'POST':
        content = request.POST.get('content')
        visibility = request.POST.get('visibility', 'all_parents')
        tags = request.POST.getlist('tags')
        if not tags:
            tags = ['general']
            
        center_id = request.POST.get('center_id')
        image = request.FILES.get('image') # Kept for backwards compatibility
        media_files = request.FILES.getlist('media')
        
        target_groups_ids = request.POST.getlist('target_groups')
        target_parents_ids = request.POST.getlist('target_parents')

        if not center_id:
            return JsonResponse({"error": "center_id is required"}, status=400)

        try:
            center = Center.objects.get(center_id=center_id)
            
            post = FeedPost.objects.create(
                author=request.user,
                center=center,
                content=content,
                visibility=visibility,
                tags=tags,
                image=image
            )
            
            for file in media_files:
                media_type = 'video' if file.content_type.startswith('video/') else 'image'
                from .models import FeedPostMedia
                FeedPostMedia.objects.create(
                    post=post,
                    file=file,
                    media_type=media_type
                )
            
            if target_groups_ids:
                post.target_groups.set(target_groups_ids)
            if target_parents_ids:
                post.target_parents.set(target_parents_ids)
                
            return JsonResponse({
                "status": "success",
                "post_id": post.id
            })
        except Center.DoesNotExist:
            return JsonResponse({"error": "Center not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def delete_post(request, post_id):
    if request.method == 'DELETE' or request.method == 'POST':
        try:
            post = FeedPost.objects.get(id=post_id)
            if post.author == request.user or request.user.is_staff:
                post.delete()
                return JsonResponse({"status": "success"})
            return JsonResponse({"error": "Forbidden"}, status=403)
        except FeedPost.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def react_to_post(request, post_id):
    if request.method == 'POST':
        reaction_type = request.POST.get('type', 'like')
        try:
            post = FeedPost.objects.get(id=post_id)
            reaction, created = PostReaction.objects.get_or_create(
                post=post,
                user=request.user,
                defaults={'reaction_type': reaction_type}
            )
            if not created:
                if reaction.reaction_type == reaction_type:
                    reaction.delete()
                    return JsonResponse({"status": "removed"})
                else:
                    reaction.reaction_type = reaction_type
                    reaction.save()
            
            return JsonResponse({"status": "success", "type": reaction_type})
        except FeedPost.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def get_post_comments(request, post_id):
    # Only get top level comments
    comments_qs = Comment.objects.filter(post_id=post_id, parent=None).select_related('author').prefetch_related('replies', 'replies__author', 'reactions')
    
    comments = []
    for c in comments_qs:
        comment_data = {
            "id": c.id,
            "author": {
                "id": str(c.author.user_id),
                "name": c.author.full_name,
                "profile_photo": request.build_absolute_uri(c.author.profile_photo.url) if c.author.profile_photo else None,
            },
            "content": c.content,
            "timestamp": c.timestamp.isoformat(),
            "reactions_count": c.reactions.count(),
            "user_has_reacted": c.reactions.filter(user=request.user).exists(),
            "replies": [
                {
                    "id": r.id,
                    "author": {
                        "id": str(r.author.user_id),
                        "name": r.author.full_name,
                        "profile_photo": request.build_absolute_uri(r.author.profile_photo.url) if r.author.profile_photo else None,
                    },
                    "content": r.content,
                    "timestamp": r.timestamp.isoformat(),
                    "reactions_count": r.reactions.count(),
                    "user_has_reacted": r.reactions.filter(user=request.user).exists(),
                } for r in c.replies.all().order_by('timestamp')
            ]
        }
        comments.append(comment_data)
        
    return JsonResponse({"comments": comments})

@login_required
@csrf_exempt
def add_comment(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        tagged_users_ids = request.POST.getlist('tagged_users')
        
        try:
            post = FeedPost.objects.get(id=post_id)
            parent = None
            if parent_id:
                parent = Comment.objects.get(id=parent_id, post=post)

            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent=parent
            )
            if tagged_users_ids:
                comment.tagged_users.set(tagged_users_ids)
            
            return JsonResponse({
                "status": "success",
                "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "timestamp": comment.timestamp.isoformat(),
                    "parent_id": parent_id
                }
            })
        except (FeedPost.DoesNotExist, Comment.DoesNotExist):
            return JsonResponse({"error": "Post or parent comment not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def get_feed_metadata(request):
    """Returns centers, groups and parents for post creation filtering"""
    user = request.user
    if user.role_type not in ['director', 'vice_director', 'educator', 'owner'] and not user.is_staff:
        return JsonResponse({"error": "Forbidden"}, status=403)
    
    centers = []
    if user.role_type == 'director':
        if hasattr(user, 'director_profile') and user.director_profile.managed_center:
            centers.append(user.director_profile.managed_center)
    elif user.role_type == 'vice_director':
        if hasattr(user, 'vice_director_profile') and user.vice_director_profile.center:
            centers.append(user.vice_director_profile.center)
    elif user.role_type == 'educator':
        if hasattr(user, 'educator_profile') and user.educator_profile.center:
            centers.append(user.educator_profile.center)
    elif user.role_type == 'owner':
        if hasattr(user, 'owner_profile') and user.owner_profile.owned_organization:
            centers = list(user.owner_profile.owned_organization.centers.all())
    
    data = []
    for center in centers:
        groups = Group.objects.filter(center=center)
        parents = User.objects.filter(
            role_type='parent', 
            parent_profile__children_relationships__child__center=center
        ).distinct()
        
        data.append({
            "center_id": str(center.center_id),
            "center_name": center.name,
            "groups": [{"id": str(g.group_id), "name": g.name} for g in groups],
            "parents": [{"id": str(p.user_id), "name": p.full_name} for p in parents]
        })
        
    return JsonResponse({"metadata": data})

@login_required
@csrf_exempt
def get_contacts(request):
    user = request.user
    allowed_user_ids = get_allowed_contact_ids(user)
    
    query = request.GET.get('q', '')

    last_msg_subquery = Message.objects.filter(
        (Q(sender=OuterRef('pk')) & Q(recipient=user)) |
        (Q(sender=user) & Q(recipient=OuterRef('pk')))
    ).order_by('-timestamp')

    unread_count_subquery = Message.objects.filter(
        sender=OuterRef('pk'),
        recipient=user,
        is_read=False
    ).values('sender').annotate(cnt=Count('pk')).values('cnt')

    contacts_qs = User.objects.filter(user_id__in=allowed_user_ids)
    
    if query:
        contacts_qs = contacts_qs.filter(full_name__icontains=query)

    contacts_qs = contacts_qs.annotate(
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
            "lastMessage": u.last_message_text if u.last_message_text else ("Voice message" if u.last_message_type == 'audio' else (f"Sent an {u.last_message_type}" if u.last_message_type else "")),
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
def subscribe_push(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            from .models import PushSubscription
            PushSubscription.objects.update_or_create(
                endpoint=data['endpoint'],
                defaults={
                    'user': request.user,
                    'p256dh': data['p256dh'],
                    'auth': data['auth']
                }
            )
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

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
