import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        # Group name for this user
        self.user_group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Mark all received messages as delivered when user connects
        sender_ids = await self.mark_all_as_delivered()
        for sender_id in sender_ids:
            await self.channel_layer.group_send(
                f"user_{sender_id}",
                {
                    "type": "messages_delivered",
                    "recipient_id": str(self.user.user_id)
                }
            )

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "chat_message")

        if message_type == "chat_message":
            recipient_id = data.get("recipient_id")
            content = data.get("content")

            if not recipient_id or not content:
                return

            # Save message to database
            message = await self.save_message(recipient_id, content)

            if message:
                recipient_group_name = f"user_{recipient_id}"
                sender_group_name = f"user_{self.user.id}"
                
                message_data = {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "sender_id": str(self.user.user_id),
                        "recipient_id": str(recipient_id),
                        "sender_name": self.user.full_name,
                        "content": content,
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

    @database_sync_to_async
    def save_message(self, recipient_id, content):
        try:
            recipient = User.objects.get(user_id=recipient_id)
            return Message.objects.create(
                sender=self.user,
                recipient=recipient,
                content=content
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
