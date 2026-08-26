import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        # Sanitize user ID to be safe for group name
        self.group_name = f"user_{self.user.id}"

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Receive message from room group
    async def send_notification(self, event):
        # event is the dictionary sent to the group
        # It expects 'message' or 'notification' key
        notification_data = event.get("notification", {})
        unread_count = event.get("unread_count", 0)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "notification",
            "notification": notification_data,
            "unread_count": unread_count
        }))
