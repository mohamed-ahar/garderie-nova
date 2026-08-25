from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from datetime import datetime
import os
import json
import glob

from dashboard.models import Child, ParentChildRelationship, Center
from accounts.models import ParentProfile
from .models import (
    EnrollmentForm, 
    AuthorizedPickup, 
    EmergencyContact, 
    UnauthorizedContact
)

def get_user_storage_path(user, child=None):
    """
    Returns the path to the user's personal storage directory.
    Creates it if it doesn't exist.
    If child is provided, returns the child-specific directory.
    """
    if child:
        user_dir = os.path.join(settings.MEDIA_ROOT, 'parents', str(user.id), 'enrollment_history', str(child.uuid))
    else:
        user_dir = os.path.join(settings.MEDIA_ROOT, 'parents', str(user.id), 'enrollment_history')
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def save_form_draft(user, post_data, child=None):
    """
    Helper to save form data as a JSON draft.
    """
    storage_path = get_user_storage_path(user, child)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    child_name = f"{post_data.get('child_first_name', 'unknown')}_{post_data.get('child_last_name', 'child')}"
    # Sanitize filename
    child_name = "".join([c for c in child_name if c.isalnum() or c in ('_', '-')])
    filename = f"draft_{child_name}_{timestamp}.json"

    data = {}
    for key in post_data:
        if key == 'csrfmiddlewaretoken': continue
        # Handle lists
        vals = post_data.getlist(key)
        if len(vals) > 1 or key.endswith('[]'):
            data[key] = vals
        else:
            data[key] = post_data[key]

    with open(os.path.join(storage_path, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return filename

@login_required
@transaction.atomic
def enrollment_profile_view(request, child_id=None):
    user = request.user
    
    # Ensure user is a parent (or handle permissions as needed)
    if user.role_type != 'parent' and not user.is_superuser :
        messages.error(request, "Access denied. Only parents can fill this form.")
        return render(request, "core/403.html", status=403)

    child = None
    enrollment_form = None
    
    # If editing an existing child
    if child_id:
        child = get_object_or_404(Child, pk=child_id)
        # Security check: Ensure this parent is related to this child
        if not child.parent_relationships.filter(parent__user=user).exists():
             messages.error(request, "You do not have permission to view this child.")
             return render(request, "core/403.html", status=403)
        
        # Try to get existing form, or create a temporary empty one for context
        try:
            enrollment_form = child.enrollment_profile
        except EnrollmentForm.DoesNotExist:
            enrollment_form = None

    if request.method == "POST":
        action = request.POST.get('action')
        
        # --- HANDLE SAVE DRAFT ---
        if action == 'save_draft':
            filename = save_form_draft(user, request.POST, child)
            messages.success(request, f"Brouillon sauvegardé: {filename}")
            return redirect(request.path)

        # --- 1. HANDLE CHILD CREATION/UPDATE ---
        if not child:
            # Create new Child
            default_center = Center.objects.first() 
            
            child = Child.objects.create(
                center=default_center,
                first_name=request.POST.get('child_first_name'),
                last_name=request.POST.get('child_last_name'),
                gender=request.POST.get('child_gender', ''),
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
                relationship_type="Parent",
                is_emergency_contact=True
            )
        else:
            # Update existing Child
            child.first_name = request.POST.get('child_first_name')
            child.last_name = request.POST.get('child_last_name')
            child.gender = request.POST.get('child_gender', '')
            child.birth_date = request.POST.get('birth_date')
            child.medicare_number = request.POST.get('medicare_number')
            date_exp = request.POST.get('medicare_expiry')
            if date_exp:
                child.medicare_expiry = date_exp
            child.address = f"{request.POST.get('addr_street')} {request.POST.get('addr_apt')} {request.POST.get('addr_city')}, {request.POST.get('addr_prov')} {request.POST.get('addr_zip')}"
            child.save()

        # --- 2. HANDLE ENROLLMENT FORM ---
        form_data = {
            'registration_date': request.POST.get('registration_date') or None,
            'start_date': request.POST.get('start_date') or None,
            
            'doctor_name': request.POST.get('doctor_name', ''),
            'doctor_phone': request.POST.get('doctor_phone', ''),
            'doctor_address': request.POST.get('doctor_address', ''),
            'allergies_severe': ", ".join([a for a in request.POST.getlist('allergies_severe') if a.strip()]),
            'non_fatal_allergies': request.POST.get('non_fatal_allergies', ''),
            
            'requires_epipen': request.POST.get('requires_epipen') == 'on',
            'routine_services_required': request.POST.get('routine_services_required') == 'on',
            'routine_services_details': request.POST.get('routine_services_details', ''),
            'continuous_medication': request.POST.get('continuous_medication', ''),
            'activity_restrictions': request.POST.get('activity_restrictions', ''),
            
            'dietary_restrictions': request.POST.get('dietary_restrictions', ''),
            'cultural_dietary_restrictions': request.POST.get('cultural_dietary_restrictions', ''),
            
            'immunization_provided': request.POST.get('immunization_provided') == 'on',
            'immunization_exemption': request.POST.get('immunization_exemption') == 'medical' or request.POST.get('immunization_exemption') == 'written', # Logic adaptation
            
            'preschool_history': request.POST.get('preschool_history', ''),
            'preschool_duration': request.POST.get('preschool_duration', ''),
            
            # Autonomy
            'autonomy_dressing': request.POST.get('autonomy_dressing', ''),
            'autonomy_eating': request.POST.get('autonomy_eating', ''),
            'autonomy_toilet': request.POST.get('autonomy_toilet', ''),
            'autonomy_hygiene': request.POST.get('autonomy_hygiene', ''),
            'autonomy_other': request.POST.get('autonomy_other', ''),
            'motor_skills': request.POST.get('motor_skills', ''),
            
            'transition_tips': request.POST.get('transition_tips', ''),
            'interests_hobbies': request.POST.get('interests_hobbies', ''),
            'additional_info': request.POST.get('additional_info', ''),
        }

        # Process Medical History Checkboxes
        diseases = ['measles', 'mumps', 'rubella', 'chickenpox', 'meningitis', 'whooping_cough', 'asthma', 'diabetes', 'epilepsy', 'eczema']
        medical_json = {}
        for d in diseases:
            val = request.POST.get(f'med_history_{d}')
            if val == 'yes':
                medical_json[d] = True
            elif val == 'no':
                medical_json[d] = False
        
        form_data['medical_history_flags'] = medical_json

        enrollment_obj, created = EnrollmentForm.objects.update_or_create(
            child=child,
            defaults=form_data
        )

        # --- 3. HANDLE RELATED LISTS (Pickups, Emergency, Unauthorized) ---
        
        # A. Authorized Pickups
        enrollment_obj.authorized_pickups.all().delete()
        pickup_names = request.POST.getlist('pickup_name[]')
        pickup_rels = request.POST.getlist('pickup_rel[]')
        pickup_addrs = request.POST.getlist('pickup_addr[]')
        pickup_phones = request.POST.getlist('pickup_phone[]')
        
        for i in range(len(pickup_names)):
            if pickup_names[i]:
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

        # Save a draft of the submitted version so auto-load works correctly
        save_form_draft(user, request.POST, child)

        messages.success(request, "Profil de l'enfant enregistré avec succès.")
        return redirect('dashboard_redirect')

    # --- GET REQUEST ---
    
    # 1. List available drafts
    draft_history = []
    storage_path = get_user_storage_path(user, child)
    files = glob.glob(os.path.join(storage_path, "*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    for f in files:
        draft_history.append({
            'filename': os.path.basename(f),
            'modified': datetime.fromtimestamp(os.path.getmtime(f))
        })

    # 2. Determine Draft to Load
    draft_data = None
    load_draft = request.GET.get('load_draft')
    
    if load_draft:
        target_file = load_draft
        user_msg = f"Brouillon chargé: {target_file}"
    elif draft_history:
        target_file = draft_history[0]['filename']
        user_msg = f"Dernier brouillon restauré: {target_file}"
    else:
        target_file = None

    # 3. Load the Data
    if target_file:
        try:
            with open(os.path.join(storage_path, target_file), 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
                messages.info(request, user_msg)
        except FileNotFoundError:
            if load_draft:
                messages.error(request, "Brouillon introuvable.")

    # Pre-fill address from logged-in parent if new child
    parent_address = {}
    if not child:
        try:
            p_profile = request.user.parent_profile
            parent_address['street'] = p_profile.home_address 
        except:
            pass

    # Prepare Lists for Template (Pad with None if fewer than required)
    emergency_contacts_list = []
    pickup_list = []
    
    if enrollment_form:
        emergency_contacts_list = list(enrollment_form.emergency_contacts.all())
        pickup_list = list(enrollment_form.authorized_pickups.all())
    
    # Pad Emergency Contacts to 2
    while len(emergency_contacts_list) < 2:
        emergency_contacts_list.append(None)
        
    # Pad Pickups to 4
    while len(pickup_list) < 4:
        pickup_list.append(None)

    context = {
        'child': child,
        'enrollment': enrollment_form,
        'draft_data': draft_data, # Pass loaded draft data to template
        'draft_history': draft_history,
        'parent_user': user,
        'parent_address': parent_address,
        'emergency_contacts_list': emergency_contacts_list,
        'pickup_list': pickup_list,
        'today': datetime.now().date(),
        'medical_history_diseases_left': ['Rougeole', 'Oreillons', 'Méningite'],
        'medical_history_diseases_right': ['Rubéole', 'Varicelle', 'Coqueluche'],
        'health_conditions_left': ['Asthme', 'Eczéma/Psoriasis'],
        'health_conditions_right': ['Diabète', 'Épilepsie']
    }
    return render(request, 'reports/enrollment_form.html', context)