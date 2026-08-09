from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from datetime import datetime
import os
import json
import glob

from core.models import Child, ParentChildRelationship, Center
from accounts.models import ParentProfile
from .models import (
    EnrollmentForm, 
    AuthorizedPickup, 
    EmergencyContact, 
    UnauthorizedContact
)

def get_user_storage_path(user):
    """
    Returns the path to the user's personal storage directory.
    Creates it if it doesn't exist.
    """
    user_dir = os.path.join(settings.MEDIA_ROOT, 'parents', str(user.id), 'enrollment_history')
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

@login_required
@transaction.atomic
def enrollment_profile_view(request, child_id=None):
    user = request.user
    
    # Ensure user is a parent (or handle permissions as needed)
    if user.role_type != 'parent' and not user.is_superuser and False:
        messages.error(request, "Access denied. Only parents can fill this form.")
        return redirect('home')

    child = None
    enrollment_form = None
    
    # If editing an existing child
    if child_id:
        child = get_object_or_404(Child, pk=child_id)
        # Security check: Ensure this parent is related to this child
        if not child.parent_relationships.filter(parent__user=user).exists():
             messages.error(request, "You do not have permission to view this child.")
             return redirect('home')
        
        # Try to get existing form, or create a temporary empty one for context
        try:
            enrollment_form = child.enrollment_profile
        except EnrollmentForm.DoesNotExist:
            enrollment_form = None

    if request.method == "POST":
        action = request.POST.get('action')
        
        # --- HANDLE SAVE DRAFT ---
        if action == 'save_draft':
            storage_path = get_user_storage_path(user)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            child_name = f"{request.POST.get('child_first_name', 'unknown')}_{request.POST.get('child_last_name', 'child')}"
            filename = f"draft_{child_name}_{timestamp}.json"
            
            # Serialize POST data
            data = {}
            for key in request.POST:
                if key == 'csrfmiddlewaretoken': continue
                # Handle lists (pickups, etc.)
                vals = request.POST.getlist(key)
                if len(vals) > 1 or key.endswith('[]'):
                    data[key] = vals
                else:
                    data[key] = request.POST[key]
            
            with open(os.path.join(storage_path, filename), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            messages.success(request, f"Brouillon sauvegardé: {filename}")
            return redirect(request.path)

        # --- 1. HANDLE CHILD CREATION/UPDATE ---
        if not child:
            # Create new Child
            # Note: You'll need logic to assign a Center. 
            # For now, I'm fetching the first center or you can pass it via hidden input.
            default_center = Center.objects.first() 
            
            child = Child.objects.create(
                center=default_center,
                first_name=request.POST.get('child_first_name'),
                last_name=request.POST.get('child_last_name'),
                birth_date=request.POST.get('birth_date'),
                medicare_number=request.POST.get('medicare_number'),
                medicare_expiry=request.POST.get('medicare_expiry') or None,
                address=f"{request.POST.get('addr_street')} {request.POST.get('addr_apt')} {request.POST.get('addr_city')}, {request.POST.get('addr_prov')} {request.POST.get('addr_zip')}"
            )
            
            # Create Relationship with logged-in Parent
            parent_profile = get_object_or_404(ParentProfile, user=user)
            ParentChildRelationship.objects.create(
                parent=parent_profile,
                child=child,
                relationship_type="Parent", # or prompt user
                is_emergency_contact=True
            )
        else:
            # Update existing Child
            child.first_name = request.POST.get('child_first_name')
            child.last_name = request.POST.get('child_last_name')
            child.birth_date = request.POST.get('birth_date')
            child.medicare_number = request.POST.get('medicare_number')
            date_exp = request.POST.get('medicare_expiry')
            if date_exp:
                child.medicare_expiry = date_exp
            child.address = f"{request.POST.get('addr_street')} {request.POST.get('addr_apt')} {request.POST.get('addr_city')}, {request.POST.get('addr_prov')} {request.POST.get('addr_zip')}"
            child.save()

        # --- 2. HANDLE ENROLLMENT FORM ---
        form_data = {
            'doctor_name': request.POST.get('doctor_name'),
            'doctor_phone': request.POST.get('doctor_phone'),
            'doctor_address': request.POST.get('doctor_address'),
            'allergies_severe': request.POST.get('allergies_severe'),
            'requires_epipen': request.POST.get('requires_epipen') == 'on',
            'dietary_restrictions': request.POST.get('dietary_restrictions'),
            'routine_services_required': request.POST.get('routine_services_required') == 'on',
            'immunization_provided': request.POST.get('immunization_provided') == 'on',
            'preschool_history': request.POST.get('preschool_history'),
            
            # Autonomy
            'autonomy_dressing': request.POST.get('autonomy_dressing'),
            'autonomy_eating': request.POST.get('autonomy_eating'),
            'autonomy_toilet': request.POST.get('autonomy_toilet'),
            'autonomy_hygiene': request.POST.get('autonomy_hygiene'),
            'autonomy_other': request.POST.get('autonomy_other'),
            'transition_tips': request.POST.get('transition_tips'),
            'interests_hobbies': request.POST.get('interests_hobbies'),
        }

        # Process Medical History Checkboxes into JSON
        # Assumes inputs like name="med_history_measles" value="yes"
        diseases = ['measles', 'mumps', 'rubella', 'chickenpox', 'meningitis', 'whooping_cough', 'asthma', 'diabetes', 'epilepsy', 'eczema']
        medical_json = {}
        for d in diseases:
            val = request.POST.get(f'med_history_{d}')
            if val == 'yes':
                medical_json[d] = True
            elif val == 'no':
                medical_json[d] = False
            # else: not answered
        
        form_data['medical_history_flags'] = medical_json

        enrollment_obj, created = EnrollmentForm.objects.update_or_create(
            child=child,
            defaults=form_data
        )

        # --- 3. HANDLE RELATED LISTS (Pickups, Emergency, Unauthorized) ---
        # Strategy: Delete existing and recreate. Simplifies logic vs matching IDs in HTML.
        
        # A. Authorized Pickups
        enrollment_obj.authorized_pickups.all().delete()
        pickup_names = request.POST.getlist('pickup_name[]')
        pickup_rels = request.POST.getlist('pickup_rel[]')
        pickup_addrs = request.POST.getlist('pickup_addr[]')
        pickup_phones = request.POST.getlist('pickup_phone[]')
        
        for i in range(len(pickup_names)):
            if pickup_names[i]: # Only save if name exists
                AuthorizedPickup.objects.create(
                    enrollment_form=enrollment_obj,
                    name=pickup_names[i],
                    relationship=pickup_rels[i] if i < len(pickup_rels) else "",
                    address=pickup_addrs[i] if i < len(pickup_addrs) else "",
                    phone_day=pickup_phones[i] if i < len(pickup_phones) else ""
                )

        # B. Emergency Contacts
        enrollment_obj.emergency_contacts.all().delete()
        emerg_names = request.POST.getlist('emerg_name[]')
        emerg_rels = request.POST.getlist('emerg_rel[]')
        emerg_addrs = request.POST.getlist('emerg_addr[]')
        emerg_phones = request.POST.getlist('emerg_phone[]')

        for i in range(len(emerg_names)):
            if emerg_names[i]:
                EmergencyContact.objects.create(
                    enrollment_form=enrollment_obj,
                    name=emerg_names[i],
                    relationship=emerg_rels[i] if i < len(emerg_rels) else "",
                    address=emerg_addrs[i] if i < len(emerg_addrs) else "",
                    phone_day=emerg_phones[i] if i < len(emerg_phones) else ""
                )
        
        # C. Unauthorized
        enrollment_obj.unauthorized_contacts.all().delete()
        unauth_names = request.POST.getlist('unauth_name[]')
        for name in unauth_names:
            if name:
                UnauthorizedContact.objects.create(
                    enrollment_form=enrollment_obj,
                    name=name
                )

        messages.success(request, "Profil de l'enfant enregistré avec succès.")
        return redirect('dashboard') # Change to your success URL

    # --- GET REQUEST ---
    
    # Check for Draft Load
    draft_data = None
    load_draft = request.GET.get('load_draft')
    if load_draft:
        storage_path = get_user_storage_path(user)
        try:
            with open(os.path.join(storage_path, load_draft), 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
                messages.info(request, f"Brouillon chargé: {load_draft}")
        except FileNotFoundError:
            messages.error(request, "Brouillon introuvable.")
    
    # List available drafts
    draft_history = []
    storage_path = get_user_storage_path(user)
    files = glob.glob(os.path.join(storage_path, "*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    for f in files:
        draft_history.append({
            'filename': os.path.basename(f),
            'modified': datetime.fromtimestamp(os.path.getmtime(f))
        })

    # Pre-fill address from logged-in parent if new child
    parent_address = {}
    if not child:
        try:
            p_profile = request.user.parent_profile
            # Assuming address is stored as text, simple split or just pass full
            # For this example, passing full string to street, user can edit
            parent_address['street'] = p_profile.home_address 
        except:
            pass

    context = {
        'child': child,
        'enrollment': enrollment_form,
        'draft_data': draft_data, # Pass loaded draft data to template
        'draft_history': draft_history,
        'parent_user': user,
        'parent_address': parent_address,
        'today': datetime.now().date(),
        'medical_history_diseases_left': ['Rougeole', 'Oreillons', 'Méningite'],
        'medical_history_diseases_right': ['Rubéole', 'Varicelle', 'Coqueluche'],
        'health_conditions_left': ['Asthme', 'Eczéma/Psoriasis'],
        'health_conditions_right': ['Diabète', 'Épilepsie']
    }
    return render(request, 'reports/enrollment_form.html', context)