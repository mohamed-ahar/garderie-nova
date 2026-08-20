from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q  # Darouri bach t-khdem biha f filter

from .models import Message, DirectorConnection
from .forms import MessageForm
from accounts.models import User, Director

# --- Views dial Messaging ---

@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by("-created_at")
    
    pending_requests = None
    if request.user.role_type == "director":
        pending_requests = DirectorConnection.objects.filter(
            to_director__user=request.user, 
            is_confirmed=False
        )
        
    return render(request, "inbox.html", {
        "messages": messages,
        "pending_requests": pending_requests
    })

@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by("-created_at")
    return render(request, "sent.html", {"messages": messages})

@login_required
def send_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            django_messages.success(request, "Message sent successfully!")
            return redirect("communication:sent_messages")
    else:
        form = MessageForm(user=request.user)

    return render(request, "send_message.html", {"form": form})

# --- Views dial Connections (Confirmation & Search) ---
def send_connection_request(request, director_id):
    # 1. Jib l-sender (Nta)
    sender = request.user.director_profile
    
    # 2. Jib l-receiver (L-director li cliquiti 3lih)
    target = get_object_or_404(Director, user_id=director_id)

    # 3. Create invitation (Hna fin k-tsift l-invit)
    # is_confirmed=False k-t3ni invitation baqa Pending
    DirectorConnection.objects.get_or_create(
        from_director=sender,
        to_director=target,
        defaults={'is_confirmed': False}
    )

    django_messages.success(request, f"Invitation sent to {target.user.full_name}!")
    return redirect('communication:search_directors')
@login_required
def connection_list(request):
    if request.user.role_type != "director":
        return redirect('dashboard:home')
    
    director_profile = request.user.director_profile
    
    pending_requests = DirectorConnection.objects.filter(
        to_director=director_profile, 
        is_confirmed=False
    )
    
    confirmed_connections = DirectorConnection.objects.filter(
        (Q(from_director=director_profile) | Q(to_director=director_profile)),
        is_confirmed=True
    )
    
    return render(request, "connections.html", {
        "pending_requests": pending_requests,
        "confirmed_connections": confirmed_connections
    })

@login_required
def approve_connection(request, connection_id):
    # Hna khdemna b pk hit DirectorConnection 3ndu auto-id m-Django (hit ma-dertich primary_key=True f connection)
    connection = get_object_or_404(DirectorConnection, id=connection_id, to_director=request.user.director_profile)
    connection.is_confirmed = True
    connection.save()
    django_messages.success(request, "Connection confirmed! You can now exchange messages.")
    return redirect("communication:connection_list")

@login_required
def search_directors(request):
    query = request.GET.get('q', '')
    profile = request.user.director_profile
    
    # List kkamla l-dropdown
    all_other_directors = Director.objects.exclude(user=request.user).order_by('user__full_name')

    # Filtering l-table 3la hsab chno t-khtar f dropdown
    directors = all_other_directors
    if query:
        directors = directors.filter(user__full_name=query)

    # Kan-jibu l-haalat dial l-invitations bach n-beddlo l-button f l-template
    sent_requests_ids = DirectorConnection.objects.filter(
        from_director=profile, is_confirmed=False
    ).values_list('to_director_id', flat=True)
    
    confirmed_sent_ids = DirectorConnection.objects.filter(
        from_director=profile, is_confirmed=True
    ).values_list('to_director_id', flat=True)
    
    confirmed_received_ids = DirectorConnection.objects.filter(
        to_director=profile, is_confirmed=True
    ).values_list('from_director_id', flat=True)

    return render(request, "search_directors.html", {
        "directors": directors,
        "directors_list_all": all_other_directors,
        "query": query,
        "sent_requests_ids": list(sent_requests_ids),
        "confirmed_ids": list(confirmed_sent_ids) + list(confirmed_received_ids),
    })

@login_required
def send_connection_request(request, director_id):
    # Sender
    try:
        sender_profile = request.user.director_profile
    except Director.DoesNotExist:
        django_messages.error(request, "Only directors can connect.")
        return redirect('dashboard:home')

    # Receiver (Using user_id because it's the PK in Director model)
    target_director = get_object_or_404(Director, user_id=director_id)
    
    if target_director.user == request.user:
        django_messages.warning(request, "You cannot connect with yourself.")
        return redirect('communication:search_directors')

    # Create connection with Pending status
    connection, created = DirectorConnection.objects.get_or_create(
        from_director=sender_profile,
        to_director=target_director
    )
    
    if created:
        django_messages.success(request, f"Request sent to {target_director.user.full_name}.")
    else:
        django_messages.info(request, "Request already exists.")
    
    return redirect('communication:connection_list')

# --- Management & API ---

@login_required
def read_message(request, message_id):
    message = get_object_or_404(Message, message_id=message_id)
    if message.receiver == request.user:
        message.is_read = True
        message.save()
    return render(request, "read_message.html", {"message": message})

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, message_id=message_id)
    if message.sender == request.user or message.receiver == request.user:
        message.delete()
        django_messages.success(request, "Message deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'communication:inbox'))

@login_required
def unread_count_api(request):
    count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})