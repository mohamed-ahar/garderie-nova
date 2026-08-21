import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class Lesson(models.Model):
    """
    Model l-dourous: l-Director kighedemhom o l-Educator kishoufhom.
    """
    lesson_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    
    # --- Content Types ---
    # 1. PDF File
    pdf_file = models.FileField(
        upload_to='curriculum/pdfs/', 
        blank=True, 
        null=True,
        help_text=_("Upload a PDF document for the lesson")
    )
    
    # 2. YouTube / Video Link
    video_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text=_("Paste a YouTube or Vimeo link")
    )
    
    # 3. Rich Text Content (Optional)
    content_text = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Written instructions or lesson notes")
    )

    # --- Relations (Linked to 'accounts' app) ---
    # Creator: Director aw Owner mn l-app accounts
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="created_lessons"
    )
    
    # Assignee: L-Educator li ghadi i-viewi had dars
    educator = models.ForeignKey(
        'accounts.Educator', 
        on_delete=models.CASCADE, 
        related_name="assigned_lessons"
    )

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")

    def __str__(self):
        # Safely getting full_name from the linked Educator's User model
        return f"{self.title} - {self.educator.user.full_name}"