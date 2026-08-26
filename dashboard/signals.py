from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification

@receiver(post_save, sender=Notification)
def send_notification_websocket(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.user.id}"
        
        # Get unread count
        unread_count = instance.user.notifications.filter(is_read=False).count()
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "notification": {
                    "id": str(instance.notif_id),
                    "title": instance.title,
                    "message": instance.message,
                    "action_url": instance.action_url,
                    "is_read": instance.is_read,
                    "created_at": instance.created_at.strftime("%b %d, %H:%M"),
                },
                "unread_count": unread_count
            }
        )
