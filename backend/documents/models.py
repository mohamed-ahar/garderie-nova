from django.db import models
from core.models import Center, Child, User
import uuid


class Report(models.Model):
    REPORT_TYPES = (
        ("incident", "Incident Report"),
        ("daily_log", "Daily Log"),
        ("injury", "Injury Report"),
    )
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="reports")

    child = models.ForeignKey(
        Child, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )

    title = models.CharField(max_length=200)
    type = models.CharField(max_length=50, choices=REPORT_TYPES)

    initiator = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="initiated_reports"
    )

    data = models.JSONField(default=dict)

    status = models.CharField(max_length=30, default="pending_signatures")
    created_at = models.DateTimeField(auto_now_add=True)


class ReportSignature(models.Model):
    sig_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="signatures"
    )

    signer_user = models.ForeignKey(User, on_delete=models.CASCADE)

    role_required = models.CharField(max_length=50)

    signed_at = models.DateTimeField(null=True, blank=True)
    signature_token = models.TextField(blank=True, null=True)
