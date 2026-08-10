from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from django.db.models import Prefetch
from .models import (
    Group,
    Room,
    Child,
    Educator,
    StaffAssignment,
    User,
    Center,
    ParentProfile,
    Notification
)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Organization, Center
from .forms import (
    CenterCreationForm,
    DirectorCreationForm,
    AssignDirectorForm,
    RoomForm,
)
from django.shortcuts import render, get_object_or_404
from .models import Center, Organization
from accounts.models import Educator, Director, User
from reports.models import EnrollmentForm
from django.core.mail import send_mail  # hadi mzal mkhdemti biha
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse







@login_required
def get_notifications_api(request):
    notifications = request.user.notifications.all().order_by("-created_at")[:10]
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    data = {
        "count": unread_count,
        "notifications": [
            {
                "id": n.notif_id,
                "title": n.title,
                "message": n.message,
                "action_url": n.action_url,
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%b %d, %H:%M"),
            }
            for n in notifications
        ],
    }
    return JsonResponse(data)


@login_required
def mark_notification_read_api(request, notif_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, notif_id=notif_id, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

