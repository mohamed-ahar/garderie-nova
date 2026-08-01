import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# ==========================================
# 1. AUTHENTICATION & BASE USER
# ==========================================


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role_type", "owner")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Base User Table. Handles Login (Email/Pass) and common contact info.
    """

    ROLE_CHOICES = (
        ("owner", "Network Owner"),
        ("director", "Director"),
        ("vice_director", "Vice Director"),
        ("educator", "Educator"),
        ("parent", "Parent"),
    )

    username = None  # We use email as ID
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="core_user_set",  # Unique related_name
        blank=True,
        verbose_name="groups",
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="core_user_set",  # Unique related_name
        blank=True,
        verbose_name="user permissions",
        help_text="Specific permissions for this user.",
    )
    # ---------------------------------

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone_number"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.get_role_type_display()})"
    @property
    def id(self):
        return self.user_id


# ==========================================
# 2. ORGANIZATION HIERARCHY
# ==========================================


class Organization(models.Model):
    org_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    # Linked via string to avoid circular definition issues
    owner = models.OneToOneField(
        "OwnerProfile", on_delete=models.PROTECT, related_name="owned_organization"
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

    # One Main Director per Center
    director = models.OneToOneField(
        "DirectorProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_center",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# ==========================================
# 3. EXPLICIT ROLES (INHERITANCE)
# ==========================================


class OwnerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="owner_profile"
    )
    office_address = models.TextField(blank=True)

    def __str__(self):
        return f"Owner: {self.user.full_name}"


class DirectorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="director_profile",
    )
    qualification_cert = models.CharField(max_length=100, blank=True)
    hired_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Director: {self.user.full_name}"


class ViceDirectorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="vice_director_profile",
    )
    center = models.ForeignKey(
        Center, on_delete=models.CASCADE, related_name="vice_directors"
    )

    # JSON Checkboxes for permissions (e.g., {'can_edit_ratios': True})
    specific_permissions = models.JSONField(default=dict)

    def __str__(self):
        return f"Vice Director: {self.user.full_name}"


class EducatorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="educator_profile",
    )
    center = models.ForeignKey(
        Center, on_delete=models.CASCADE, related_name="educators"
    )

    qualification_level = models.CharField(max_length=100)
    is_active_in_ratio = models.BooleanField(
        default=True
    )  # Counts towards legal limits
    color_code = models.CharField(max_length=7, default="#3B82F6")  # Hex Color for UI

    def __str__(self):
        return f"Educator: {self.user.full_name}"


class ParentProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="parent_profile"
    )
    home_address = models.TextField()
    billing_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Parent: {self.user.full_name}"


# ==========================================
# 4. SPACES & RATIO CONFIGURATION
# ==========================================


class Room(models.Model):
    room_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    fire_capacity = models.IntegerField(help_text="Strict legal fire limit")

    def __str__(self):
        return self.name


class Group(models.Model):
    """
    The logical group tracked for Ratios.
    """

    RATIO_CATEGORIES = (
        ("UNDER_24M", "Under 24 Months (1:3 / 900pts)"),
        ("MIXED_2_TO_4", "Mixed 2-4 Years (Cumulative 1050pts)"),
        ("SCHOOL_AGE_5_PLUS", "School Age 5+ (1:15 Count)"),
    )

    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="groups")
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, related_name="active_group"
    )
    name = models.CharField(max_length=100)

    ratio_category = models.CharField(max_length=50, choices=RATIO_CATEGORIES)

    # Real-time Status Cache
    current_occupancy = models.IntegerField(default=0)
    current_educators = models.IntegerField(default=0)

    # New Brunswick Specifics
    current_total_points = models.IntegerField(default=0)
    required_educators = models.IntegerField(default=0)
    is_compliant = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_ratio_category_display()})"


# ==========================================
# 5. CHILDREN & FAMILIES
# ==========================================


class Child(models.Model):
    child_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(
        Center, on_delete=models.CASCADE, related_name="children"
    )
    assigned_group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, related_name="enrolled_children"
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()

    # NB Ratio Weight: 300, 200, 125, 100, or 1
    current_ratio_weight = models.IntegerField(default=0)

    # JSON for flexibility
    medical_info = models.JSONField(
        default=dict, blank=True
    )  # { "allergies": [], "diet": "" }

    profile_photo_url = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default="active")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ParentChildRelationship(models.Model):
    parent = models.ForeignKey(
        ParentProfile, on_delete=models.CASCADE, related_name="children_relationships"
    )
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="parent_relationships"
    )
    relationship_type = models.CharField(max_length=50)  # Mother, Father, Guardian
    is_emergency_contact = models.BooleanField(default=False)

    class Meta:
        unique_together = ("parent", "child")


# ==========================================
# 6. PORTFOLIOS & ACTIVITIES
# ==========================================


class PortfolioActivity(models.Model):
    activity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="activities"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    activity_date = models.DateField(default=timezone.now)

    # Tags e.g., ["Motor Skills", "Social"]
    learning_domains = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} for {self.child.first_name}"


class ActivityEducator(models.Model):
    """
    Links educators who conducted the activity.
    """

    activity = models.ForeignKey(
        PortfolioActivity,
        on_delete=models.CASCADE,
        related_name="participating_educators",
    )
    educator = models.ForeignKey(EducatorProfile, on_delete=models.CASCADE)


class ActivityMedia(models.Model):
    """
    Multiple images/videos per activity.
    """

    media_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(
        PortfolioActivity, on_delete=models.CASCADE, related_name="media"
    )
    file_url = models.TextField()  # Or ImageField if using local storage
    media_type = models.CharField(
        max_length=20, choices=[("image", "Image"), ("video", "Video")]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)


# ==========================================
# 7. ATTENDANCE & OPERATIONS
# ==========================================


class AttendanceLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="attendance_logs"
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="attendance_logs"
    )

    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    # Store the point value at this specific moment for historical audit
    ratio_weight_snapshot = models.IntegerField(default=0)


class StaffAssignment(models.Model):
    assignment_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    educator = models.ForeignKey(
        EducatorProfile, on_delete=models.CASCADE, related_name="assignments"
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="staff_assignments"
    )

    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


# ==========================================
# 8. DYNAMIC SIGNED REPORTS
# ==========================================


class Report(models.Model):
    REPORT_TYPES = (
        ("incident", "Incident Report"),
        ("daily_log", "Daily Log"),
        ("injury", "Injury Report"),
    )
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="reports")

    # Can be linked to a child or generic
    child = models.ForeignKey(
        Child, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )

    title = models.CharField(max_length=200)
    type = models.CharField(max_length=50, choices=REPORT_TYPES)

    initiator = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="initiated_reports"
    )

    # Flexible Content
    data = models.JSONField(default=dict)

    status = models.CharField(
        max_length=30, default="pending_signatures"
    )  # completed, archived
    created_at = models.DateTimeField(auto_now_add=True)


class ReportSignature(models.Model):
    sig_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="signatures"
    )

    # The person who needs to sign
    signer_user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Role context: 'parent', 'director', 'witness'
    role_required = models.CharField(max_length=50)

    signed_at = models.DateTimeField(null=True, blank=True)
    signature_token = models.TextField(blank=True, null=True)


# ==========================================
# 9. SAFETY & COMMUNICATION
# ==========================================


class Notification(models.Model):
    notif_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


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
    status = models.CharField(max_length=50)  # 'safe', 'missing'
    checked_at = models.DateTimeField(auto_now_add=True)
