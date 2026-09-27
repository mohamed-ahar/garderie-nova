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
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="enrollment_forms")
    submission_date = models.DateField(default=timezone.now)
    is_fully_signed = models.BooleanField(default=False)
    locked_for_editing = models.BooleanField(default=False, help_text="Whether the form is locked from further editing by parents")
    is_active = models.BooleanField(default=True, help_text="Whether this is the current active form")
    
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

class EnrollmentSignature(models.Model):
    """
    Stores parent signatures for the enrollment form.
    """
    signature_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment_form = models.ForeignKey(EnrollmentForm, on_delete=models.CASCADE, related_name='signatures')
    parent = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    signature_data = models.TextField(help_text="Base64 encoded signature image")
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('enrollment_form', 'parent')

    def __str__(self):
        return f"Signature by {self.parent.full_name} for {self.enrollment_form.child}"

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

class IllnessReport(models.Model):
    """
    Represents 'Annexe 11 - Formulaire de signalement de maladie possible'
    """
    SYMPTOM_CHOICES = [
        ('diarrhea', 'Diarrhée'),
        ('fever', 'Fièvre'),
        ('cold_symptoms', 'Symptômes de rhume'),
        ('skin_problems', 'Troubles de la peau'),
        ('vomiting', 'Vomissements'),
        ('others', 'Autres'),
    ]

    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="illness_reports")
    date = models.DateField(default=timezone.now)

    # Symptoms
    symptoms = models.JSONField(default=list, help_text="Liste des codes de symptômes sélectionnés")
    explanation = models.TextField(blank=True)

    # Vital signs / Meds
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    time_taken = models.TimeField(null=True, blank=True)
    medication_administered = models.BooleanField(default=False)
    medication_details = models.TextField(blank=True, help_text="Médicament et dose administrée")

    # Public Health
    reported_to_public_health = models.BooleanField(default=False)
    public_health_communication_date = models.DateField(null=True, blank=True)
    recent_illness_report_exists = models.BooleanField(default=False, help_text="Formulaire rempli dans les 24h précédentes?")

    # Parent notification & Pickup
    parent_notified_at = models.TimeField(null=True, blank=True, help_text="Heure à laquelle le parent a été avisé")
    departure_time = models.TimeField(null=True, blank=True, help_text="Heure de départ")

    # Signatures
    staff_member = models.ForeignKey("accounts.Educator", on_delete=models.PROTECT, related_name="filed_illness_reports")
    staff_signature_data = models.TextField(blank=True, help_text="Base64 encoded staff signature")

    parent_signature_data = models.TextField(blank=True, help_text="Base64 encoded parent signature")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Illness Report: {self.child} - {self.date}"

class ReintegrationForm(models.Model):
    """
    Represents 'Annexe 12 - Formulaire de réintégration après exclusion'
    """
    form_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey("dashboard.Center", on_delete=models.CASCADE, related_name="reintegration_forms")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="reintegration_forms")
    date = models.DateField(default=timezone.now)

    # Section B - Child Info
    illness_name = models.CharField(max_length=255)
    illness_start_date = models.DateField()
    diagnosis_date = models.DateField(null=True, blank=True)
    treatment_start_date = models.DateField(null=True, blank=True)

    # Section C - Confirmation of Exclusion (General)
    staff_member = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="signed_reintegration_staff", null=True, blank=True)
    staff_signature_data = models.TextField(blank=True, help_text="Base64 encoded staff signature")
    staff_signature_date = models.DateField(null=True, blank=True)

    parent = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="signed_reintegration_parent", null=True, blank=True)
    parent_signature_data = models.TextField(blank=True, help_text="Base64 encoded parent signature")
    parent_signature_date = models.DateField(null=True, blank=True)

    # Section D - Public Health Confirmation
    is_public_health_required = models.BooleanField(default=False, help_text="Required for E. coli, Shigella, or Salmonella typhi")
    ph_ecoli_shigella_negative = models.BooleanField(default=False, help_text="Negative results of two stool samples 24h apart")
    ph_salmonella_negative = models.BooleanField(default=False, help_text="Negative results of multiple stool samples")
    
    ph_representative_name = models.CharField(max_length=255, blank=True)
    ph_signature_data = models.TextField(blank=True, help_text="Base64 encoded Public Health signature")
    ph_signature_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reintegration Form: {self.child} - {self.date}"