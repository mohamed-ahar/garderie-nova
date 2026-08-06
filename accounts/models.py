import uuid
import math
from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


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

    username = None
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="core_user_set",
        blank=True,
        verbose_name="groups",
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="core_user_set",
        blank=True,
        verbose_name="user permissions",
        help_text="Specific permissions for this user.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone_number"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.get_role_type_display()})"

    @property
    def id(self):
        return self.user_id


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
        "core.Center", on_delete=models.CASCADE, related_name="vice_directors"
    )

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
        "core.Center", on_delete=models.CASCADE, related_name="educators"
    )
    is_active_in_ratio = models.BooleanField(default=True)
    is_compliant = models.BooleanField(default=True)
    compliance_errors = models.JSONField(default=list, blank=True)

    def get_age_group_errors(self):
        """
        Check if educator has children from multiple age groups.
        Returns list of error messages if validation fails.
        """
        children = self.assigned_children.all()
        errors = []
        
        if not children.exists():
            return errors
        
        has_under_24m = False
        has_over_24m = False
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

        if has_under_24m and has_over_24m:
            errors.append("Educator cannot supervise both children under 24 months and older children.")
        
        return errors

    def get_ratio_errors(self):
        """
        Check if educator ratio is compliant.
        Returns list of error messages if validation fails.
        """
        children = self.assigned_children.all()
        errors = []
        
        if not children.exists():
            return errors

        total_factor = 0.0
        today = date.today()

        for child in children:
            age_months = (
                (today.year - child.birth_date.year) * 12
                + today.month
                - child.birth_date.month
            )
            if today.day < child.birth_date.day:
                age_months -= 1

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
            
            total_factor += factor

        if total_factor > 1.05:
            errors.append(f"Ratio exceeded for this educator (Points: {total_factor:.3f} / 1.05 max).")

        return errors

    def recalculate_compliance(self):
        children = self.assigned_children.all()
        errors = []
        
        if not children.exists():
            self.is_compliant = True
            self.compliance_errors = []
            self.save()
            return True

        # Get validation errors from both checks
        errors.extend(self.get_age_group_errors())
        errors.extend(self.get_ratio_errors())

        self.is_compliant = len(errors) == 0
        self.compliance_errors = errors
        self.save()
        print(errors)
        return self.is_compliant

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
