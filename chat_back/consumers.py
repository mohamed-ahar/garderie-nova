import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from .models import Message, ChatInvitation
from .utils import get_allowed_contact_ids
from dashboard.models import Child

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        # Handle multiple tabs/connections
        user_id_str = str(self.user.user_id)
        connection_count = cache.get(f"user_conn_{user_id_str}", 0)
        cache.set(f"user_conn_{user_id_str}", connection_count + 1, 86400)

        # Mark user as online if this is the first connection
        if connection_count == 0:
            await self.set_user_online(True)
            await self.broadcast_status(True)

        # Group name for this user
        self.user_group_name = f"user_{user_id_str}"

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # Join status groups of all contacts to receive their updates
        contact_ids = await self.get_contact_ids()
        for contact_id in contact_ids:
            await self.channel_layer.group_add(
                f"status_{contact_id}",
                self.channel_name
            )

        # Also join own status group so others can find us if needed
        # (Actually others join OUR status group, so we send TO it)

        await self.accept()
        
        # Mark all received messages as delivered when user connects
        sender_ids = await self.mark_all_as_delivered()
        for sender_id in sender_ids:
            await self.channel_layer.group_send(
                f"user_{sender_id}",
                {
                    "type": "messages_delivered",
                    "recipient_id": user_id_str
                }
            )

    async def disconnect(self, close_code):
        if hasattr(self, 'user'):
            user_id_str = str(self.user.user_id)
            connection_count = cache.get(f"user_conn_{user_id_str}", 1)
            new_count = max(0, connection_count - 1)
            cache.set(f"user_conn_{user_id_str}", new_count, 86400)

            # Mark user as offline if this was the last connection
            if new_count == 0:
                await self.set_user_online(False)
                await self.broadcast_status(False)
        
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        # Clean up status group subscriptions if needed
        # (Channel layer usually handles this on disconnect)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "chat_message")

        # Get the host from the scope for URL building
        headers = dict(self.scope.get('headers', []))
        host = headers.get(b'host', b'localhost:8001').decode()

        if message_type == "chat_message":
            recipient_id = data.get("recipient_id")
            content = data.get("content")

            if not recipient_id or not content:
                return

            # CHECK PERMISSION
            can_message = await self.check_permission(recipient_id)
            if not can_message:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "You do not have permission to message this user."
                }))
                return

            # Save message to database
            message = await self.save_message(recipient_id, content)

            if message:
                recipient_group_name = f"user_{recipient_id}"
                sender_group_name = f"user_{self.user.user_id}"
                
                # Build attachment info with full URL
                attachment_url = None
                if message.attachment:
                    attachment_url = f"http://{host}/media/{message.attachment.name}"
                
                # Build profile photo URL
                profile_photo_url = None
                try:
                    if self.user.profile_photo:
                        profile_photo_url = f"http://{host}{self.user.profile_photo.url}"
                except:
                    pass
                
                message_data = {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "sender_id": str(self.user.user_id),
                        "recipient_id": str(recipient_id),
                        "sender_name": self.user.full_name,
                        "sender_profile_photo": profile_photo_url,
                        "content": content,
                        "attachment": attachment_url,
                        "attachment_type": message.attachment_type,
                        "timestamp": message.timestamp.isoformat(),
                        "is_delivered": message.is_delivered,
                        "is_read": message.is_read,
                    }
                }

                # Send to recipient
                await self.channel_layer.group_send(
                    recipient_group_name,
                    message_data
                )
                
                # Send to sender (all tabs)
                await self.channel_layer.group_send(
                    sender_group_name,
                    message_data
                )

        elif message_type == "mark_read":
            recipient_id = data.get("recipient_id")
            if recipient_id:
                await self.mark_as_read(recipient_id)

        elif message_type == "check_online":
            target_user_id = data.get("user_id")
            if target_user_id:
                status_data = await self.get_user_status(target_user_id)
                await self.send(text_data=json.dumps({
                    "type": "online_status",
                    "user_id": target_user_id,
                    "is_online": status_data["is_online"],
                    "last_seen": status_data["last_seen"]
                }))

    async def online_status(self, event):
        # This is called when someone we are 'subscribed' to changes status
        await self.send(text_data=json.dumps(event))

    async def broadcast_status(self, is_online):
        # Send our status to our own status group
        # Anyone who has us as a contact will be in this group
        await self.channel_layer.group_send(
            f"status_{self.user.user_id}",
            {
                "type": "online_status",
                "user_id": str(self.user.user_id),
                "is_online": is_online,
                "last_seen": timezone.now().isoformat() if not is_online else None
            }
        )

    @database_sync_to_async
    def get_contact_ids(self):
        return [str(uid) for uid in get_allowed_contact_ids(self.user)]

    @database_sync_to_async
    def get_user_status(self, user_id):
        try:
            u = User.objects.get(user_id=user_id)
            return {
                "is_online": u.is_online,
                "last_seen": u.last_seen.isoformat() if u.last_seen else None
            }
        except User.DoesNotExist:
            return {"is_online": False, "last_seen": None}

    async def chat_message(self, event):
        # If this is an incoming message (not sent by us in another tab)
        # mark it as delivered immediately
        msg_data = event.get("message", {})
        if msg_data.get("sender_id") != str(self.user.user_id):
            await self.mark_single_delivered(msg_data.get("id"))
            # Notify the sender that it was delivered
            await self.channel_layer.group_send(
                f"user_{msg_data.get('sender_id')}",
                {
                    "type": "messages_delivered",
                    "recipient_id": str(self.user.user_id)
                }
            )
        
        await self.send(text_data=json.dumps(event))

    async def messages_delivered(self, event):
        await self.send(text_data=json.dumps(event))

    async def messages_read(self, event):
        await self.send(text_data=json.dumps(event))

    async def ping(self, event):
        # Respond to ping with pong to keep connection alive
        await self.send(text_data=json.dumps({
            "type": "pong",
            "timestamp": timezone.now().isoformat()
        }))

    @database_sync_to_async
    def check_permission(self, recipient_id):
        try:
            recipient = User.objects.get(user_id=recipient_id)
            
            # 1. Admin/Owner/Directors
            if (
                self.user.role_type in ["admin", "owner"] or 
                recipient.role_type in ["admin", "owner"] or
                (self.user.role_type == "director" and recipient.role_type == "director")
            ):
                return True

            # 2. Accepted invitation
            if ChatInvitation.objects.filter(
                (Q(sender=self.user, recipient=recipient) | Q(sender=recipient, recipient=self.user)),
                status='accepted'
            ).exists():
                return True

            # 3. Contextual connections (Same center, assigned children, etc.)
            user = self.user
            if user.role_type == "parent" and recipient.role_type == "parent":
                user_centers = Child.objects.filter(parent_relationships__parent__user=user).values_list("center_id", flat=True)
                return Child.objects.filter(parent_relationships__parent__user=recipient, center_id__in=user_centers).exists()
            
            if user.role_type == "educator" and recipient.role_type == "director":
                u_prof = getattr(user, "educator_profile", None)
                r_prof = getattr(recipient, "director_profile", None)
                if u_prof and r_prof and r_prof.managed_center:
                    return str(u_prof.center_id) == str(r_prof.managed_center.center_id)
            
            if user.role_type == "director" and recipient.role_type == "educator":
                u_prof = getattr(user, "director_profile", None)
                r_prof = getattr(recipient, "educator_profile", None)
                if u_prof and r_prof and u_prof.managed_center:
                    return str(u_prof.managed_center.center_id) == str(r_prof.center_id)

            if user.role_type == "parent" and recipient.role_type == "educator":
                return Child.objects.filter(parent_relationships__parent__user=user, assigned_educator__user=recipient).exists()
            
            if user.role_type == "educator" and recipient.role_type == "parent":
                return Child.objects.filter(parent_relationships__parent__user=recipient, assigned_educator__user=user).exists()

            if user.role_type == "director" and recipient.role_type == "parent":
                u_prof = getattr(user, "director_profile", None)
                if u_prof and u_prof.managed_center:
                    return Child.objects.filter(parent_relationships__parent__user=recipient, center_id=u_prof.managed_center.center_id).exists()

            if user.role_type == "parent" and recipient.role_type == "director":
                r_prof = getattr(recipient, "director_profile", None)
                if r_prof and r_prof.managed_center:
                    return Child.objects.filter(parent_relationships__parent__user=user, center_id=r_prof.managed_center.center_id).exists()

            return False
        except User.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, recipient_id, content, attachment=None, attachment_type=None):
        try:
            recipient = User.objects.get(user_id=recipient_id)
            return Message.objects.create(
                sender=self.user,
                recipient=recipient,
                content=content,
                attachment=attachment,
                attachment_type=attachment_type
            )
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_all_as_delivered(self):
        messages = Message.objects.filter(recipient=self.user, is_delivered=False)
        sender_ids = list(set(messages.values_list('sender_id', flat=True)))
        messages.update(is_delivered=True)
        return sender_ids

    @database_sync_to_async
    def mark_single_delivered(self, message_id):
        if message_id:
            Message.objects.filter(id=message_id, recipient=self.user).update(is_delivered=True)

    @database_sync_to_async
    def mark_as_read(self, sender_id):
        Message.objects.filter(sender_id=sender_id, recipient=self.user, is_read=False).update(is_read=True, is_delivered=True)
        
        # Notify sender that their messages were read
        import asyncio
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{sender_id}",
            {
                "type": "messages_read",
                "recipient_id": str(self.user.user_id)
            }
        )

    @database_sync_to_async
    def set_user_online(self, is_online):
        User.objects.filter(user_id=self.user.user_id).update(
            is_online=is_online,
            last_seen=timezone.now() if not is_online else None
        )
