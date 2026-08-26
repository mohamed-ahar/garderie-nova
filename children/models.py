from django.db import models
import uuid
from dashboard.models import Child

class Attendance(models.Model):
    attendance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField()
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    is_absent = models.BooleanField(default=False)

    ABSENCE_REASON_CHOICES = [
        ("1", "Diarrhée"),
        ("2", "Fièvre"),
        ("3", "Symptômes du rhume (toux, otite, mal de gorge, écoulement oculaire)"),
        ("4", "Problèmes de peau"),
        ("5", "Vomissement"),
        ("6", "Changement de comportement sans aucun autre symptôme"),
        ("7", "Autre maladie (veuillez préciser au verso)"),
        ("8", "Absence non liée à une maladie"),
        ("9", "Autre (préciser)"), 
    ]
    absence_reason_code = models.CharField(
        max_length=2, choices=ABSENCE_REASON_CHOICES, blank=True, null=True
    )
    absence_reason_notes = models.TextField(
        blank=True,
        help_text="Detailed notes for absence reason, especially for 'Autre maladie' or 'Autre'."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        ordering = ["-date", "-arrival_time"]

    def __str__(self):
        status = "Present"
        if self.is_absent:
            status = "Absent"
            if self.absence_reason_code:
                status += f" ({self.get_absence_reason_code_display()})"
        return f"{self.child.first_name} {self.child.last_name} on {self.date}: {status}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_absent and not self.absence_reason_code:
            raise ValidationError(
                "An absence reason code is required if the child is marked as absent."
            )
        if not self.is_absent and self.arrival_time is None:
             raise ValidationError(
                "Arrival time is required if the child is present."
             )
        if not self.is_absent and self.absence_reason_code:
            raise ValidationError(
                "Cannot have an absence reason if the child is marked as present."
            )
        if self.arrival_time and self.departure_time and self.departure_time < self.arrival_time:
            raise ValidationError("Departure time cannot be before arrival time.")

class WeeklyChildReport(models.Model):
    """
    The container for the week. 
    One sheet of paper = One WeeklyChildReport.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    child = models.ForeignKey(
        "dashboard.Child", 
        on_delete=models.CASCADE, 
        related_name="weekly_reports"
    )
    
    # The date of the Monday for this week
    week_start_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('child', 'week_start_date')
        ordering = ['-week_start_date']

    def __str__(self):
        return f"Report {self.week_start_date} - {self.child}"


class DailyActivityLog(models.Model):
    """
    Represents one vertical column (Lundi, Mardi, etc.) in the PDF.
    """
    class DayOfWeek(models.TextChoices):
        MONDAY = 'LUNDI', 'Lundi'
        TUESDAY = 'MARDI', 'Mardi'
        WEDNESDAY = 'MERCREDI', 'Mercredi'
        THURSDAY = 'JEUDI', 'Jeudi'
        FRIDAY = 'VENDREDI', 'Vendredi'

    class Amount(models.TextChoices):
        NOTHING = 'RIEN', 'Rien'
        LITTLE = 'PEU', 'Un peu'
        MOST = 'TOUT', 'Presque tout' # "Presque tout" / "Tout"
        NA = 'SO', 'S.O.'

    report = models.ForeignKey(
        WeeklyChildReport, 
        on_delete=models.CASCADE, 
        related_name="daily_logs"
    )
    
    # We store the specific date to ensure uniqueness per child per day
    date = models.DateField()
    day_name = models.CharField(max_length=10, choices=DayOfWeek.choices)

    # ==========================
    # SECTION 1: ALIMENTS (Food)
    # ==========================
    # Schema: [{"name": "snack_am", "amount": "TOUT", "time": "10:00"}, ...]
    food_tracking = models.JSONField(default=list, blank=True)

    # ====================================
    # SECTION 1 (Right): BOISSONS (Drinks)
    # ====================================
    # Stores list of bottles. 
    # Schema: [{"time": "09:00", "amount": "TOUT"}]
    # Valid amounts: RIEN, PEU, TOUT
    bottles_tracking = models.JSONField(default=list, blank=True)

    # ==================
    # SECTION 2: SIESTE
    # ==================
    # Schema: [{"start": "12:30", "end": "14:00"}]
    # The PDF allows for 3 nap entries.
    nap_tracking = models.JSONField(default=list, blank=True)

    # ==================
    # SECTION 3: HUMEUR
    # ==================
    # Checkboxes from the form
    mood_content = models.BooleanField(default=False, verbose_name="Content")
    mood_amuse = models.BooleanField(default=False, verbose_name="Amusé")
    mood_affectueux = models.BooleanField(default=False, verbose_name="Affectueux")
    mood_exigeant = models.BooleanField(default=False, verbose_name="Exigeant")
    mood_pleurnicheur = models.BooleanField(default=False, verbose_name="Pleurnicheur")
    
    mood_malheureux = models.BooleanField(default=False, verbose_name="Malheureux")
    mood_tranquille = models.BooleanField(default=False, verbose_name="Tranquille")
    mood_collant = models.BooleanField(default=False, verbose_name="Collant")
    mood_fatigue = models.BooleanField(default=False, verbose_name="Fatigué")
    
    mood_autre = models.BooleanField(default=False, verbose_name="Autre")
    mood_autre_desc = models.CharField(max_length=100, blank=True, verbose_name="Autre Description")

    # ==================
    # SECTION 4: SANTÉ
    # ==================
    has_symptoms = models.BooleanField(default=False, verbose_name="Symptômes de maladie (Oui)")
    symptoms_desc = models.TextField(blank=True, verbose_name="Description des symptômes")

    # ============================
    # SECTION 5: COUCHE / TOILETTE
    # ============================
    # This handles the complex grid at the bottom.
    # Schema per entry:
    # {
    #   "time": "10:30",
    #   "is_sec": False,          # SEC
    #   "is_mouille": True,       # MOUILLE
    #   "is_toilette": False,     # TOILETTE (Did they sit on potty?)
    #   "is_selles": False,       # SELLES
    #   "consistency": "M"        # Only if SELLES is true. Values: N, M, A, S (from legend)
    # }
    diaper_logs = models.JSONField(default=list, blank=True)

    # ============================
    # SECTION 6: FOOTER (Daily)
    # ============================
    comments = models.TextField(blank=True, verbose_name="Commentaires")
    
    # Signature de l'employé (Per day, as shown by grid lines)
    signed_by = models.ForeignKey(
        "accounts.Educator", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="daily_signatures"
    )
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('report', 'date')

    def __str__(self):
        return f"{self.day_name} - {self.date}"