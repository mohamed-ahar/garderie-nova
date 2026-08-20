import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Kan-importiw l-models mn accounts bach n-derou bihom l-ilaqat
# Note: Ila derti circular import, tqder t-stkhdem 'accounts.Director' f l-ForeignKey
from accounts.models import Director

User = settings.AUTH_USER_MODEL

class DirectorConnection(models.Model):
    """
    Had l-model houwa l-marja3 dial 'After Confirmation'.
    Kay-fard anan l-Directors mn organizations khrine khasshoum i-tkoun 
    3ndhoum connection 'is_confirmed' bach i-dwiw binathoum.
    """
    from_director = models.ForeignKey(
        Director, 
        on_delete=models.CASCADE, 
        related_name="connections_initiated"
    )
    to_director = models.ForeignKey(
        Director, 
        on_delete=models.CASCADE, 
        related_name="connections_received"
    )
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Bach may-kounouch 2 connections bin nefs l-directors
        unique_together = ('from_director', 'to_director')
        verbose_name = "Director Connection"
        verbose_name_plural = "Director Connections"

    def clean(self):
        # Bach l-Director may-siftch connection l-rassou
        if self.from_director == self.to_director:
            raise ValidationError("You cannot connect with yourself.")

    def __str__(self):
        status = "Confirmed" if self.is_confirmed else "Pending"
        return f"{self.from_director.user.full_name} ➜ {self.to_director.user.full_name} ({status})"


class Message(models.Model):
    """
    L-model l-asasi dial les messages.
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="received_messages"
    )
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    
    # Trackers
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From: {self.sender.full_name} | Subject: {self.subject or 'No Subject'}"