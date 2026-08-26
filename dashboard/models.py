import uuid
import math
from datetime import date
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User, ParentProfile, Educator


class Organization(models.Model):
    org_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    owner = models.OneToOneField(
        "accounts.Owner", on_delete=models.PROTECT, related_name="owned_organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Center(models.Model):
    center_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="centers"
    )

    name = models.CharField(max_length=255)
    address = models.TextField()
    timezone = models.CharField(max_length=50, default="America/Moncton")

    director = models.OneToOneField(
        "accounts.Director",
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_center",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class Room(models.Model):
    room_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    room_surface = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Room surface area in square meters"
    )
    max_capacity = models.IntegerField(
        help_text="Maximum capacity based on fire regulations"
    )
    age_group = models.CharField(
        max_length=100, blank=True, help_text="Intended age group for the room"
    )

    def __str__(self):
        return self.name


class Group(models.Model):
    """
    The logical group tracked for Ratios.
    """

    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="groups")
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, related_name="active_group"
    )
    name = models.CharField(max_length=100)

    current_occupancy = models.IntegerField(default=0)
    current_educators = models.IntegerField(default=0)

    current_total_points = models.IntegerField(default=0)
    required_educators = models.IntegerField(default=0)
    is_compliant = models.BooleanField(default=True)

    calculated_max_capacity = models.IntegerField(
        default=0, help_text="Legal limit based on mixed age composition"
    )

    def recalculate_ratios(self):
        children = self.enrolled_children.all()
        if not children.exists():
            # makayn 7ta child => kolchi mzyan
            self.current_occupancy = 0
            self.required_educators = 0
            self.is_compliant = True
            self.save()
            return

        total_educators_factor = 0.0
        # 2ila kan ghir deri 9el mn 24 months makhesnach nkheltohom m3a kbar f nafs l group
        has_under_24m = False
        has_over_24m = False

        highest_factor_in_group = 0.0

        today = date.today()

        for child in children:
            age_months = (
                (today.year - child.birth_date.year) * 12
                + today.month
                - child.birth_date.month
            )
            # 2ila kan deri 3endo nhar f had shhar mazal ma kmlch shhar
            if today.day < child.birth_date.day:
                age_months -= 1

            if age_months < 24:
                has_under_24m = True
            else:
                has_over_24m = True

            factor = 0.0
            if age_months < 24:
                factor = 0.333
            elif 24 <= age_months < 36:
                factor = 0.200
            elif 36 <= age_months < 48:
                factor = 0.125
            elif 48 <= age_months < 60:
                factor = 0.100
            else:
                factor = 0.067
            # galik khesna nchofo ratio kbir ga3 fgrp (dyal 2asghar child) bach n7esbo lmax dyal drari li ymkn yd5lo f grp
            if factor > highest_factor_in_group:
                highest_factor_in_group = factor

            total_educators_factor += factor

        if has_under_24m and has_over_24m:
            # kan fih 9el mn 24m w kbar f nafs l grp => violation
            self.is_compliant = False

            print("VIOLATION: Cannot mix <24m with older children.")

        integer_part = int(total_educators_factor)
        fractional_part = total_educators_factor - integer_part
        # khesn nchofo wach fat 1.05
        if fractional_part > 0.05:
            self.required_educators = integer_part + 1
        else:
            self.required_educators = integer_part

        self.current_total_points = int(total_educators_factor * 1000)

        if highest_factor_in_group > 0:
            # n7esbo l max capacity 3la hsab a3la ratio factor f grp
            self.calculated_max_capacity = int(2.0 / highest_factor_in_group)
        else:
            self.calculated_max_capacity = 30

        self.current_occupancy = children.count()
        # check dyal educators 7ta lmax cappacity w ratio mixing
        staff_check = self.current_educators >= self.required_educators
        size_check = self.current_occupancy <= self.calculated_max_capacity
        mixing_check = not (has_under_24m and has_over_24m)

        # Educator specific checks
        educator_assignments = self.staff_assignments.filter(is_active=True)
        all_educators_compliant = True
        for assignment in educator_assignments:
            if not assignment.educator.recalculate_compliance():
                all_educators_compliant = False

        self.is_compliant = (
            staff_check and size_check and mixing_check and all_educators_compliant
        )

        self.save()

    def get_compliance_errors(self):
        """
        Returns a list of compliance error messages for the group.
        """
        children = self.enrolled_children.all()
        errors = []

        if not children.exists():
            return errors

        total_educators_factor = 0.0
        has_under_24m = False
        has_over_24m = False
        highest_factor_in_group = 0.0
        today = date.today()

        for child in children:
            age_months = (
                (today.year - child.birth_date.year) * 12
                + today.month
                - child.birth_date.month
            )
            if today.day < child.birth_date.day:
                age_months -= 1

            if age_months < 24:
                has_under_24m = True
            else:
                has_over_24m = True

            factor = 0.0
            if age_months < 24:
                factor = 0.333
            elif 24 <= age_months < 36:
                factor = 0.200
            elif 36 <= age_months < 48:
                factor = 0.125
            elif 48 <= age_months < 60:
                factor = 0.100
            else:
                factor = 0.067

            if factor > highest_factor_in_group:
                highest_factor_in_group = factor

            total_educators_factor += factor

        # Check for age mixing violation
        if has_under_24m and has_over_24m:
            errors.append(
                "Cannot mix children under 24 months with older children in the same group."
            )

        # Check for staffing issues
        if self.current_educators < self.required_educators:
            errors.append(
                f"Insufficient staff: {self.current_educators} present but {self.required_educators} required."
            )

        # Check for capacity issues
        if self.current_occupancy > self.calculated_max_capacity:
            errors.append(
                f"Group capacity exceeded: {self.current_occupancy} children but max {self.calculated_max_capacity} allowed."
            )

        # Check for non-compliant educators
        educator_assignments = self.staff_assignments.filter(is_active=True)
        for assignment in educator_assignments:
            if not assignment.educator.is_compliant:
                errors.append(
                    f"Educator {assignment.educator.user.full_name} has compliance issues."
                )

        return errors

    @property
    def age_distribution(self):
        dist = {
            "De la naissance à 24 mois": 0,
            "Deux ans": 0,
            "Trois ans": 0,
            "Quatre ans et plus": 0,
            "Enfants d’âge scolaire": 0,
        }
        today = date.today()
        for child in self.enrolled_children.all():
            age_months = (
                (today.year - child.birth_date.year) * 12
                + today.month
                - child.birth_date.month
            )
            if today.day < child.birth_date.day:
                age_months -= 1

            if age_months <= 24:
                dist["De la naissance à 24 mois"] += 1
            elif 24 < age_months < 36:
                dist["Deux ans"] += 1
            elif 36 <= age_months < 48:
                dist["Trois ans"] += 1
            elif 48 <= age_months < 60:
                dist["Quatre ans et plus"] += 1
            else:
                dist["Enfants d’âge scolaire"] += 1

        return {k: v for k, v in dist.items() if v > 0}

    def __str__(self):
        return self.name


class Child(models.Model):
    child_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(
        Center, on_delete=models.CASCADE, related_name="children"
    )
    assigned_group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, related_name="enrolled_children"
    )

    assigned_educator = models.ForeignKey(
        "accounts.Educator",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_children",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[("masculin", "Masculin"), ("féminin", "Féminin")],
        blank=True,
    )
    birth_date = models.DateField()

    medical_info = models.JSONField(default=dict, blank=True)

    profile_photo = models.ImageField(
        upload_to="children_photos/", blank=True, null=True
    )
    status = models.CharField(max_length=20, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    address = models.TextField(blank=True, help_text="Child's residential address")
    medicare_number = models.CharField(max_length=50, blank=True)
    medicare_expiry = models.DateField(null=True, blank=True)

    @property
    def age_display(self):
        today = date.today()
        birth_date = self.birth_date

        years = today.year - birth_date.year
        months = today.month - birth_date.month
        days = today.day - birth_date.day

        if days < 0:
            months -= 1
            # Calculate days in previous month
            last_month = (today.month - 1) if today.month > 1 else 12
            last_month_year = today.year if today.month > 1 else today.year - 1
            import calendar

            _, days_in_last_month = calendar.monthrange(last_month_year, last_month)
            days += days_in_last_month

        if months < 0:
            years -= 1
            months += 12

        parts = []
        if years > 0:
            parts.append(f"{years}y")
        if months > 0:
            parts.append(f"{months}m")
        if days > 0:
            parts.append(f"{days}d")

        return ", ".join(parts) if parts else "0d"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ParentChildRelationship(models.Model):
    parent = models.ForeignKey(
        ParentProfile, on_delete=models.CASCADE, related_name="children_relationships"
    )
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="parent_relationships"
    )
    relationship_type = models.CharField(max_length=50)
    is_emergency_contact = models.BooleanField(default=False)

    class Meta:
        unique_together = ("parent", "child")


class StaffAssignment(models.Model):
    assignment_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    educator = models.ForeignKey(
        Educator, on_delete=models.CASCADE, related_name="assignments"
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="staff_assignments"
    )

    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class Notification(models.Model):
    notif_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}\n Content: {self.message}"


class EvacuationDrill(models.Model):
    drill_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="drills")
    type = models.CharField(max_length=50, default="fire")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)


class EvacuationCheck(models.Model):
    check_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drill = models.ForeignKey(
        EvacuationDrill, on_delete=models.CASCADE, related_name="checks"
    )
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    checked_at = models.DateTimeField(auto_now_add=True)


class CenterParentAccess(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    center = models.ForeignKey(
        Center, on_delete=models.CASCADE, related_name="parent_access_requests"
    )
    parent = models.ForeignKey(
        ParentProfile, on_delete=models.CASCADE, related_name="center_access_requests"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("center", "parent")

    def __str__(self):
        return f"{self.parent.user.full_name} -> {self.center.name} ({self.status})"


class TransferRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Directors Approval"),
        ("awaiting_signature", "Awaiting Parent Signature"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    )
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="transfer_requests"
    )
    target_center = models.ForeignKey(
        Center, on_delete=models.CASCADE, related_name="incoming_transfer_requests"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    # Director Approvals (None=Pending, True=Approved, False=Rejected)
    approved_by_outgoing = models.BooleanField(null=True, default=None)
    approved_by_incoming = models.BooleanField(null=True, default=None)

    def __str__(self):
        return f"Transfer {self.child} to {self.target_center.name}"


class TransferSignature(models.Model):
    signature_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    transfer_request = models.ForeignKey(
        TransferRequest, on_delete=models.CASCADE, related_name="signatures"
    )
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    signature_data = models.TextField()
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("transfer_request", "parent")

    def __str__(self):
        return f"Signature by {self.parent.full_name} for {self.transfer_request}"
