from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm
from accounts.models import User
from dashboard.models import Child

@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by("-created_at")
    return render(request, "inbox.html", {"messages": messages})

@login_required
def sent_messages(request):
    # Kay-fetch-i l-messages li nta s-sefat-tihom
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
            return redirect("communication:sent_messages")
    else:
        form = MessageForm(user=request.user)

    return render(request, "send_message.html", {"form": form})


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
    
    
    return redirect(request.META.get('HTTP_REFERER', 'communication:inbox'))