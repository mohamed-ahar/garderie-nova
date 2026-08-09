# core/models.py
from django.db import models
import uuid

class FormDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200) # e.g., "Annexe 1 - Profil de l'enfant"
    slug = models.SlugField(unique=True)     # e.g., "annexe-1-profil"
    
    # This JSON holds the configuration: Field names, labels, types, options
    structure = models.JSONField(default=list) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class FormSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to the definition so we know which questions were asked
    form_definition = models.ForeignKey(FormDefinition, on_delete=models.CASCADE)
    
    # Link to the specific child (from your previous models)
    child = models.ForeignKey("core.Child", on_delete=models.CASCADE, related_name="forms_data")
    
    # This stores the answers: {"first_name": "Adam", "has_allergies": true}
    data = models.JSONField(default=dict)
    
    submitted_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.form_definition.title} for {self.child}"