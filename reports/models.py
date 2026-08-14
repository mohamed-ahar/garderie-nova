from django.db import models
from django.utils import timezone
import uuid

# Import Child from core
from dashboard.models import Child

class EnrollmentForm(models.Model):
    """
    Represents the 'Annexe 1 - Profil de l\'enfant' form.
    """
    form_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name="enrollment_profile")
    submission_date = models.DateField(default=timezone.now)
    
    # Dates
    registration_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)

    # --- Health & Safety Section ---
    doctor_name = models.CharField(max_length=255, blank=True)
    doctor_phone = models.CharField(max_length=50, blank=True)
    doctor_address = models.TextField(blank=True)
    
    allergies_severe = models.TextField(blank=True, help_text="Allergies graves")
    non_fatal_allergies = models.TextField(blank=True, help_text="Allergies non mortelles (médicaments, contact)")
    requires_epipen = models.BooleanField(default=False)
    
    routine_services_required = models.BooleanField(default=False, help_text="Catheter, diabetes, etc.")
    routine_services_details = models.TextField(blank=True, help_text="Details of routine services")
    
    continuous_medication = models.TextField(blank=True, help_text="Long-term medication")
    activity_restrictions = models.TextField(blank=True, help_text="Medical restrictions on activities")

    # Specific restrictions (Medical, Cultural, Religious)
    dietary_restrictions = models.TextField(blank=True, help_text="Restrictions alimentaires médicales")
    cultural_dietary_restrictions = models.TextField(blank=True, help_text="Restrictions culturelles/religieuses")

    # --- Medical History (Checkbox approximations) ---
    # Store these as JSON to avoid 50 boolean columns. 
    # Structure: {"measles": true, "mumps": false, "asthma": true ...}
    medical_history_flags = models.JSONField(default=dict)
    
    immunization_provided = models.BooleanField(default=False, help_text="Proof of immunization provided")
    immunization_exemption = models.BooleanField(default=False, help_text="Medical or religious exemption provided")

    # --- Development & History Section ---
    preschool_history = models.TextField(blank=True, help_text="Previous daycare experience")
    preschool_duration = models.CharField(max_length=100, blank=True, help_text="Duration of previous experience")
    
    # Autonomy Questions
    autonomy_dressing = models.CharField(max_length=255, blank=True)
    autonomy_eating = models.CharField(max_length=255, blank=True)
    autonomy_toilet = models.CharField(max_length=255, blank=True)
    autonomy_hygiene = models.CharField(max_length=255, blank=True) # Washing hands/brushing teeth
    autonomy_other = models.CharField(max_length=255, blank=True)
    motor_skills = models.TextField(blank=True, help_text="Motricité")
    
    transition_tips = models.TextField(blank=True, help_text="Suggestions for positive transition")
    interests_hobbies = models.TextField(blank=True, help_text="What the child likes to do")
    additional_info = models.TextField(blank=True)

    def __str__(self):
        return f"Profil: {self.child}"

class AuthorizedPickup(models.Model):
    """
    People authorized to pick up the child (Page 1).
    """
    enrollment_form = models.ForeignKey(EnrollmentForm, on_delete=models.CASCADE, related_name="authorized_pickups")
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone_day = models.CharField(max_length=50)

class EmergencyContact(models.Model):
    """
    Contacts for emergencies if parents cannot be reached (Page 2).
    """
    enrollment_form = models.ForeignKey(EnrollmentForm, on_delete=models.CASCADE, related_name="emergency_contacts")
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone_day = models.CharField(max_length=50)

class UnauthorizedContact(models.Model):
    """
    People explicitly NOT allowed to pick up the child (Page 2).
    """
    enrollment_form = models.ForeignKey(EnrollmentForm, on_delete=models.CASCADE, related_name="unauthorized_contacts")
    name = models.CharField(max_length=255)