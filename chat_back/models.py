from django.db import models
from django.conf import settings

class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription for {self.user}"

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_received_messages'
    )
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    attachment_type = models.CharField(max_length=20, null=True, blank=True) # 'image', 'video', 'file', 'audio'
    timestamp = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.recipient} at {self.timestamp}"

class ChatInvitation(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'recipient')

    def __str__(self):
        return f"From {self.sender} to {self.recipient} ({self.status})"

class FeedPost(models.Model):
    VISIBILITY_CHOICES = [
        ('all_parents', 'All Parents'),
        ('specific_groups', 'Specific Groups'),
        ('specific_parents', 'Specific Parents'),
    ]
    POST_TYPES = [
        ('general', 'General'),
        ('announcements', 'Announcement'),
        ('photos', 'Photo'),
        ('videos', 'Video'),
        ('events', 'Event'),
    ]
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='feed_posts'
    )
    center = models.ForeignKey(
        'dashboard.Center', 
        on_delete=models.CASCADE, 
        related_name='center_feed_posts'
    )
    content = models.TextField()
    image = models.ImageField(upload_to='feed_posts/', null=True, blank=True)
    visibility = models.CharField(
        max_length=20, 
        choices=VISIBILITY_CHOICES, 
        default='all_parents'
    )
    tags = models.JSONField(default=list, blank=True)
    
    # Filtering fields
    target_groups = models.ManyToManyField(
        'dashboard.Group', 
        blank=True, 
        related_name='group_feed_posts'
    )
    target_parents = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        related_name='targeted_feed_posts'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Post by {self.author} at {self.timestamp}"

class FeedPostMedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    post = models.ForeignKey(FeedPost, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='feed_media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} for Post {self.post.id}"

class PostReaction(models.Model):
    REACTION_TYPES = [
        ('like', 'Like'),
        ('love', 'Love'),
        ('haha', 'Haha'),
        ('wow', 'Wow'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
    ]
    post = models.ForeignKey(
        FeedPost, 
        on_delete=models.CASCADE, 
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    reaction_type = models.CharField(
        max_length=10, 
        choices=REACTION_TYPES, 
        default='like'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

class Comment(models.Model):
    post = models.ForeignKey(
        FeedPost, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='feed_comments'
    )
    content = models.TextField()
    tagged_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        related_name='comment_mentions'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

class CommentReaction(models.Model):
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    reaction_type = models.CharField(
        max_length=10, 
        default='like'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

class PostView(models.Model):
    post = models.ForeignKey(
        FeedPost, 
        on_delete=models.CASCADE, 
        related_name='views'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
