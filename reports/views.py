from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML, CSS
from datetime import datetime
import os
import json
import glob

from dashboard.models import Child, ParentChildRelationship, Center, Notification
from accounts.models import ParentProfile, Educator, Director
from .models import (
    EnrollmentForm,
    AuthorizedPickup,
    EmergencyContact,
    UnauthorizedContact,
    EnrollmentSignature,
    IllnessReport,
    ReintegrationForm,
)


def get_user_storage_path(user, child=None):
    """
    Returns the path to the user's personal storage directory.
    Creates it if it doesn't exist.
    If child is provided, returns the child-specific directory (shared among all parents of the child).
    """
    if child:
        user_dir = os.path.join(
            settings.MEDIA_ROOT, "children", str(child.child_id), "enrollment_history"
        )
    else:
        user_dir = os.path.join(
            settings.MEDIA_ROOT, "parents", str(user.id), "enrollment_history"
        )
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def save_form_draft(user, post_data, child=None):
    """
    Helper to save form data as a JSON draft.
    """
    storage_path = get_user_storage_path(user, child)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    child_name = f"{post_data.get('child_first_name', 'unknown')}_{post_data.get('child_last_name', 'child')}"

    child_name = "".join([c for c in child_name if c.isalnum() or c in ("_", "-")])
    filename = f"draft_{child_name}_{timestamp}.json"

    data = {}
    for key in post_data:
        if key == "csrfmiddlewaretoken":
            continue
        # Handle lists
        vals = post_data.getlist(key)
        if len(vals) > 1 or key.endswith("[]"):
            data[key] = vals
        else:
            data[key] = post_data[key]

    with open(os.path.join(storage_path, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return filename


@login_required
@transaction.atomic
def enrollment_profile_view(request, child_id=None):
    user = request.user

    # Ensure user is a parent (or handle permissions as needed)
    if user.role_type != "parent" and not user.is_superuser:
        messages.error(request, "Access denied. Only parents can fill this form.")
        return render(request, "core/403.html", status=403)

    child = None
    enrollment_form = None

    # If editing an existing child
    if child_id:
        child = get_object_or_404(Child, pk=child_id)

        if not child.parent_relationships.filter(parent__user=user).exists():
            messages.error(request, "You do not have permission to view this child.")
            return render(request, "core/403.html", status=403)

        # Get the active enrollment form
        enrollment_form = child.enrollment_forms.filter(is_active=True).first()

    if request.method == "POST":
        action = request.POST.get("action")

        # Check if form is locked for editing by parents
        if child and enrollment_form and enrollment_form.locked_for_editing and not user.is_superuser:
            messages.error(request, "This enrollment form has been locked by a director and cannot be modified.")
            return redirect(request.path)

        # --- HANDLE SAVE DRAFT ---
        if action == "save_draft":
            filename = save_form_draft(user, request.POST, child)
            messages.success(request, f"Brouillon sauvegardé: {filename}")
            return redirect(request.path)

        # --- 1. HANDLE CHILD CREATION/UPDATE ---
        if not child:
            # Create new Child
            default_center = Center.objects.first()

            child = Child.objects.create(
                center=default_center,
                first_name=request.POST.get("child_first_name"),
                last_name=request.POST.get("child_last_name"),
                gender=request.POST.get("child_gender", ""),
                birth_date=request.POST.get("birth_date"),
                medicare_number=request.POST.get("medicare_number"),
                medicare_expiry=request.POST.get("medicare_expiry") or None,
                address=f"{request.POST.get('addr_street')} {request.POST.get('addr_apt')} {request.POST.get('addr_city')}, {request.POST.get('addr_prov')} {request.POST.get('addr_zip')}",
            )

            # Create Relationship with logged-in Parent
            parent_profile = get_object_or_404(ParentProfile, user=user)
            ParentChildRelationship.objects.create(
                parent=parent_profile,
                child=child,
                relationship_type="Parent",
                is_emergency_contact=True,
            )
        else:
            # Update existing Child
            child.first_name = request.POST.get("child_first_name")
            child.last_name = request.POST.get("child_last_name")
            child.gender = request.POST.get("child_gender", "")
            child.birth_date = request.POST.get("birth_date")
            child.medicare_number = request.POST.get("medicare_number")
            date_exp = request.POST.get("medicare_expiry")
            if date_exp:
                child.medicare_expiry = date_exp
            child.address = f"{request.POST.get('addr_street')} {request.POST.get('addr_apt')} {request.POST.get('addr_city')}, {request.POST.get('addr_prov')} {request.POST.get('addr_zip')}"
            child.save()

        # --- 2. HANDLE ENROLLMENT FORM ---
        form_data = {
            "registration_date": request.POST.get("registration_date") or None,
            "start_date": request.POST.get("start_date") or None,
            "doctor_name": request.POST.get("doctor_name", ""),
            "doctor_phone": request.POST.get("doctor_phone", ""),
            "doctor_address": request.POST.get("doctor_address", ""),
            "allergies_severe": ", ".join(
                [a for a in request.POST.getlist("allergies_severe") if a.strip()]
            ),
            "non_fatal_allergies": request.POST.get("non_fatal_allergies", ""),
            "requires_epipen": request.POST.get("requires_epipen") == "on",
            "routine_services_required": request.POST.get("routine_services_required")
            == "on",
            "routine_services_details": request.POST.get(
                "routine_services_details", ""
            ),
            "continuous_medication": request.POST.get("continuous_medication", ""),
            "activity_restrictions": request.POST.get("activity_restrictions", ""),
            "dietary_restrictions": request.POST.get("dietary_restrictions", ""),
            "cultural_dietary_restrictions": request.POST.get(
                "cultural_dietary_restrictions", ""
            ),
            "immunization_provided": request.POST.get("immunization_provided") == "on",
            "immunization_exemption": request.POST.get("immunization_exemption")
            == "medical"
            or request.POST.get("immunization_exemption")
            == "written",  # Logic adaptation
            "preschool_history": request.POST.get("preschool_history", ""),
            "preschool_duration": request.POST.get("preschool_duration", ""),
            # Autonomy
            "autonomy_dressing": request.POST.get("autonomy_dressing", ""),
            "autonomy_eating": request.POST.get("autonomy_eating", ""),
            "autonomy_toilet": request.POST.get("autonomy_toilet", ""),
            "autonomy_hygiene": request.POST.get("autonomy_hygiene", ""),
            "autonomy_other": request.POST.get("autonomy_other", ""),
            "motor_skills": request.POST.get("motor_skills", ""),
            "transition_tips": request.POST.get("transition_tips", ""),
            "interests_hobbies": request.POST.get("interests_hobbies", ""),
            "additional_info": request.POST.get("additional_info", ""),
        }

        # Process Medical History Checkboxes
        diseases = [
            "measles",
            "mumps",
            "rubella",
            "chickenpox",
            "meningitis",
            "whooping_cough",
            "asthma",
            "diabetes",
            "epilepsy",
            "eczema",
        ]
        medical_json = {}
        for d in diseases:
            val = request.POST.get(f"med_history_{d}")
            if val == "yes":
                medical_json[d] = True
            elif val == "no":
                medical_json[d] = False

        form_data["medical_history_flags"] = medical_json

        # If there's no active form, create one; otherwise, update the active form
        enrollment_obj = child.enrollment_forms.filter(is_active=True).first()
        if enrollment_obj:
            # Update the existing active form
            for attr, value in form_data.items():
                setattr(enrollment_obj, attr, value)
            enrollment_obj.save()
        else:
            # Deactivate any existing forms first (there shouldn't be any active ones, but just in case)
            child.enrollment_forms.update(is_active=False)
            # Create a new active form
            form_data['child'] = child
            enrollment_obj = EnrollmentForm.objects.create(**form_data, is_active=True)

        # --- 3. HANDLE RELATED LISTS (Pickups, Emergency, Unauthorized) ---

        # A. Authorized Pickups
        enrollment_obj.authorized_pickups.all().delete()
        pickup_names = request.POST.getlist("pickup_name[]")
        pickup_rels = request.POST.getlist("pickup_rel[]")
        pickup_addrs = request.POST.getlist("pickup_addr[]")
        pickup_phones = request.POST.getlist("pickup_phone[]")

        for i in range(len(pickup_names)):
            if pickup_names[i]:
                AuthorizedPickup.objects.create(
                    enrollment_form=enrollment_obj,
                    name=pickup_names[i],
                    relationship=pickup_rels[i] if i < len(pickup_rels) else "",
                    address=pickup_addrs[i] if i < len(pickup_addrs) else "",
                    phone_day=pickup_phones[i] if i < len(pickup_phones) else "",
                )

        # B. Emergency Contacts
        enrollment_obj.emergency_contacts.all().delete()
        emerg_names = request.POST.getlist("emerg_name[]")
        emerg_rels = request.POST.getlist("emerg_rel[]")
        emerg_addrs = request.POST.getlist("emerg_addr[]")
        emerg_phones = request.POST.getlist("emerg_phone[]")

        for i in range(len(emerg_names)):
            if emerg_names[i]:
                EmergencyContact.objects.create(
                    enrollment_form=enrollment_obj,
                    name=emerg_names[i],
                    relationship=emerg_rels[i] if i < len(emerg_rels) else "",
                    address=emerg_addrs[i] if i < len(emerg_addrs) else "",
                    phone_day=emerg_phones[i] if i < len(emerg_phones) else "",
                )

        # C. Unauthorized
        enrollment_obj.unauthorized_contacts.all().delete()
        unauth_names = request.POST.getlist("unauth_name[]")
        for name in unauth_names:
            if name:
                UnauthorizedContact.objects.create(
                    enrollment_form=enrollment_obj, name=name
                )

        # --- 4. HANDLE SIGNATURE ---
        signature_data = request.POST.get("signature_data")
        if signature_data:
            EnrollmentSignature.objects.update_or_create(
                enrollment_form=enrollment_obj,
                parent=user,
                defaults={"signature_data": signature_data},
            )

            # Check if all parents signed
            all_parent_rels = child.parent_relationships.all()
            total_parents = all_parent_rels.count()
            signed_parents_count = enrollment_obj.signatures.count()

            if signed_parents_count < total_parents:
                # Notify other parents
                signed_user_ids = enrollment_obj.signatures.values_list(
                    "parent_id", flat=True
                )
                other_parents = all_parent_rels.exclude(
                    parent__user_id__in=signed_user_ids
                )

                for p_rel in other_parents:
                    Notification.objects.create(
                        user=p_rel.parent.user,
                        title="Signature Required: Child Profile",
                        message=f"The profile for {child.first_name} has been updated by {user.full_name}. Your signature is required to finalize the enrollment.",
                        action_url=request.path,
                    )
            else:
                # All signed! Notify Director
                enrollment_obj.is_fully_signed = True
                enrollment_obj.save()

                center = child.center
                if center and center.director:
                    signed_parent_names = ", ".join(
                        [s.parent.full_name for s in enrollment_obj.signatures.all()]
                    )

                    message_text = f"The enrollment form for {child.first_name} has been signed by all parents ({signed_parent_names})."
                    title_text = f"Enrollment Form Completed: {child.first_name} {child.last_name}"

                    # Check if this form was created as a result of unlocking (has a previous version)
                    previous_forms_exist = child.enrollment_forms.filter(is_active=False).exists()
                    if previous_forms_exist:
                        message_text = f"The updated enrollment form for {child.first_name} has been signed by all parents ({signed_parent_names})."
                        title_text = f"Updated Form Completed: {child.first_name} {child.last_name}"

                    Notification.objects.create(
                        user=center.director.user,
                        title=title_text,
                        message=message_text,
                        action_url=f"/children/{child.child_id}/",  # Assuming this is the child profile URL
                    )

        # Save a draft of the submitted version so auto-load works correctly
        save_form_draft(user, request.POST, child)

        messages.success(request, "Profil de l'enfant enregistré avec succès.")
        return redirect("dashboard_redirect")

    # --- GET REQUEST ---

    # 1. List available drafts
    draft_history = []
    storage_path = get_user_storage_path(user, child)
    files = glob.glob(os.path.join(storage_path, "*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    for f in files:
        draft_history.append(
            {
                "filename": os.path.basename(f),
                "modified": datetime.fromtimestamp(os.path.getmtime(f)),
            }
        )

    # 2. Determine Draft to Load
    draft_data = None
    load_draft = request.GET.get("load_draft")

    if load_draft:
        target_file = load_draft
        user_msg = f"Brouillon chargé: {target_file}"
    elif draft_history:
        target_file = draft_history[0]["filename"]
        user_msg = f"Dernier brouillon restauré: {target_file}"
    else:
        target_file = None

    # 3. Load the Data
    if target_file:
        try:
            with open(
                os.path.join(storage_path, target_file), "r", encoding="utf-8"
            ) as f:
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
            parent_address["street"] = p_profile.home_address
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

    # Signature Status
    signatures_count = 0
    total_parents_needed = 0
    signed_parents = []
    user_has_signed = False

    if child:
        total_parents_needed = child.parent_relationships.count()
        if enrollment_form:
            signatures = enrollment_form.signatures.all()
            signatures_count = signatures.count()
            signed_parents = [s.parent for s in signatures]
            user_has_signed = any(s.parent == user for s in signatures)

    context = {
        "child": child,
        "enrollment": enrollment_form,
        "draft_data": draft_data,  # Pass loaded draft data to template
        "draft_history": draft_history,
        "parent_user": user,
        "parent_address": parent_address,
        "emergency_contacts_list": emergency_contacts_list,
        "pickup_list": pickup_list,
        "today": datetime.now().date(),
        "medical_history_diseases_left": ["Rougeole", "Oreillons", "Méningite"],
        "medical_history_diseases_right": ["Rubéole", "Varicelle", "Coqueluche"],
        "health_conditions_left": ["Asthme", "Eczéma/Psoriasis"],
        "health_conditions_right": ["Diabète", "Épilepsie"],
        "signatures_count": signatures_count,
        "total_parents_needed": total_parents_needed,
        "signed_parents": signed_parents,
        "user_has_signed": user_has_signed,
        "form_locked": enrollment_form.locked_for_editing if enrollment_form else False,
    }
    return render(request, "reports/enrollment_form.html", context)


@login_required
@transaction.atomic
def toggle_enrollment_lock(request, child_id):
    """Toggle the locked_for_editing status of an enrollment form"""
    user = request.user

    # Ensure user is a director or superuser
    if user.role_type != 'director' and not user.is_superuser:
        messages.error(request, "Access denied. Only directors can lock/unlock forms.")
        return redirect('dashboard_redirect')

    child = get_object_or_404(Child, pk=child_id)

    # Get the active enrollment form
    enrollment_form = child.enrollment_forms.filter(is_active=True).first()
    if not enrollment_form:
        messages.error(request, "Enrollment form does not exist for this child.")
        return redirect('dashboard_redirect')

    if enrollment_form:
        # Check if we're unlocking a previously locked form
        was_locked = enrollment_form.locked_for_editing
        is_now_locked = not enrollment_form.locked_for_editing  # What it will become after toggle

        if was_locked and not is_now_locked:  # We're unlocking a previously locked form
            # Deactivate the old form
            enrollment_form.is_active = False
            enrollment_form.save()

            # Create a new enrollment form with the same data
            new_enrollment_form = EnrollmentForm.objects.create(
                child=child,
                registration_date=enrollment_form.registration_date,
                start_date=enrollment_form.start_date,
                doctor_name=enrollment_form.doctor_name,
                doctor_phone=enrollment_form.doctor_phone,
                doctor_address=enrollment_form.doctor_address,
                allergies_severe=enrollment_form.allergies_severe,
                non_fatal_allergies=enrollment_form.non_fatal_allergies,
                requires_epipen=enrollment_form.requires_epipen,
                routine_services_required=enrollment_form.routine_services_required,
                routine_services_details=enrollment_form.routine_services_details,
                continuous_medication=enrollment_form.continuous_medication,
                activity_restrictions=enrollment_form.activity_restrictions,
                dietary_restrictions=enrollment_form.dietary_restrictions,
                cultural_dietary_restrictions=enrollment_form.cultural_dietary_restrictions,
                medical_history_flags=enrollment_form.medical_history_flags,
                immunization_provided=enrollment_form.immunization_provided,
                immunization_exemption=enrollment_form.immunization_exemption,
                preschool_history=enrollment_form.preschool_history,
                preschool_duration=enrollment_form.preschool_duration,
                autonomy_dressing=enrollment_form.autonomy_dressing,
                autonomy_eating=enrollment_form.autonomy_eating,
                autonomy_toilet=enrollment_form.autonomy_toilet,
                autonomy_hygiene=enrollment_form.autonomy_hygiene,
                autonomy_other=enrollment_form.autonomy_other,
                motor_skills=enrollment_form.motor_skills,
                transition_tips=enrollment_form.transition_tips,
                interests_hobbies=enrollment_form.interests_hobbies,
                additional_info=enrollment_form.additional_info,
                locked_for_editing=False,  # New form starts unlocked
                is_fully_signed=False,     # New form needs to be signed again
                is_active=True             # New form is active
            )

            # Copy related objects to the new form
            # Copy authorized pickups
            for pickup in enrollment_form.authorized_pickups.all():
                AuthorizedPickup.objects.create(
                    enrollment_form=new_enrollment_form,
                    name=pickup.name,
                    relationship=pickup.relationship,
                    address=pickup.address,
                    phone_day=pickup.phone_day
                )

            # Copy emergency contacts
            for emergency_contact in enrollment_form.emergency_contacts.all():
                EmergencyContact.objects.create(
                    enrollment_form=new_enrollment_form,
                    name=emergency_contact.name,
                    relationship=emergency_contact.relationship,
                    address=emergency_contact.address,
                    phone_day=emergency_contact.phone_day
                )

            # Copy unauthorized contacts
            for unauthorized_contact in enrollment_form.unauthorized_contacts.all():
                UnauthorizedContact.objects.create(
                    enrollment_form=new_enrollment_form,
                    name=unauthorized_contact.name
                )

            # The new form will need to be signed again, so no signatures are copied

            # Notify all parents about the new form that needs to be signed
            all_parent_rels = child.parent_relationships.all()
            for p_rel in all_parent_rels:
                Notification.objects.create(
                    user=p_rel.parent.user,
                    title="New Enrollment Form Requiring Signature",
                    message=f"A new enrollment form has been created for {child.first_name} {child.last_name}. Please review and sign again.",
                    action_url=reverse('enrollment_edit', kwargs={'child_id': child.child_id})
                )

            messages.success(request, f"A new enrollment form has been created with the previous data. Parents will need to sign it again.")
        else:
            # Regular toggle behavior for locking or for first-time unlocking
            enrollment_form.locked_for_editing = is_now_locked
            enrollment_form.save()

            status = "locked" if is_now_locked else "unlocked"
            messages.success(request, f"Enrollment form has been {status} for editing by parents.")
    else:
        messages.error(request, "Enrollment form does not exist for this child.")

    return redirect('child_list')  # Redirect back to the child list page


@login_required
def download_enrollment_pdf(request, child_id):
    """
    Generate and download enrollment form as PDF.
    Only accessible by directors and only when all parents have signed.
    """
    user = request.user
    
    # Permission check - only directors and superusers
    if user.role_type != 'director' and not user.is_superuser:
        messages.error(request, "Access denied. Only directors can download enrollment documents.")
        return redirect('dashboard_redirect')
    
    child = get_object_or_404(Child, pk=child_id)
    
    # Get the active enrollment form
    enrollment_form = child.enrollment_forms.filter(is_active=True).first()
    if not enrollment_form:
        messages.error(request, "No active enrollment form found for this child.")
        return redirect('child_list')
    
    # Check if all parents have signed
    total_parents = child.parent_relationships.count()
    signed_parents = enrollment_form.signatures.count()
    
    if signed_parents < total_parents:
        messages.error(request, f"Cannot download: Only {signed_parents} of {total_parents} parents have signed. All parents must sign before downloading.")
        return redirect('child_list')
    
    # Get all related data
    authorized_pickups = enrollment_form.authorized_pickups.all()
    emergency_contacts = enrollment_form.emergency_contacts.all()
    unauthorized_contacts = enrollment_form.unauthorized_contacts.all()
    signatures = enrollment_form.signatures.all().select_related('parent')
    
    # Get parents info
    parent_relationships = child.parent_relationships.all().select_related('parent__user')
    
    # Prepare context for PDF template
    context = {
        'child': child,
        'enrollment': enrollment_form,
        'authorized_pickups': authorized_pickups,
        'emergency_contacts': emergency_contacts,
        'unauthorized_contacts': unauthorized_contacts,
        'signatures': signatures,
        'parent_relationships': parent_relationships,
        'generated_date': datetime.now(),
        'center': child.center,
        'medical_history_diseases': [
            ('measles', 'Rougeole', 'rubella', 'Rubéole'),
            ('mumps', 'Oreillons', 'chickenpox', 'Varicelle'),
            ('meningitis', 'Méningite', 'whooping_cough', 'Coqueluche (toux coquelucheuse)'),
        ],
        'health_conditions': [
            ('asthma', 'Asthme', 'diabetes', 'Diabète'),
            ('eczema', 'Eczéma/Psoriasis', 'epilepsy', 'Épilepsie/Convulsions'),
        ]
    }
    
    # Render HTML template
    html_string = render_to_string('reports/enrollment_pdf.html', context)
    
    # Generate PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    
    # Create PDF with CSS
    pdf = html.write_pdf()
    
    # Create response
    filename = f"enrollment_{child.first_name}_{child.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@transaction.atomic
def create_illness_report(request, child_id):
    """
    Step 1: Educator identifies illness and creates the report (Annexe 11).
    """
    if request.user.role_type != 'educator' and not request.user.is_superuser:
        messages.error(request, "Seuls les éducateurs peuvent créer un signalement de maladie.")
        return redirect('dashboard_redirect')

    child = get_object_or_404(Child, pk=child_id)
    educator = get_object_or_404(Educator, user=request.user)

    if request.method == 'POST':
        selected_symptoms = request.POST.getlist('symptoms')
        explanation = request.POST.get('explanation', '')
        temperature = request.POST.get('temperature')
        time_taken = request.POST.get('time_taken')
        medication_administered = request.POST.get('medication_administered') == 'on'
        medication_details = request.POST.get('medication_details', '')
        staff_signature = request.POST.get('staff_signature_data')

        if not selected_symptoms or not staff_signature:
            messages.error(request, "Au moins un symptôme et la signature sont obligatoires.")
            return render(request, 'reports/illness_report_form.html', {'child': child, 'SYMPTOM_CHOICES': IllnessReport.SYMPTOM_CHOICES})

        report = IllnessReport.objects.create(
            child=child,
            staff_member=educator,
            symptoms=selected_symptoms,
            explanation=explanation,
            temperature=temperature if temperature else None,
            time_taken=time_taken if time_taken else None,
            medication_administered=medication_administered,
            medication_details=medication_details,
            staff_signature_data=staff_signature,
            date=timezone.now().date()
        )

        # Notify Parents
        parents = ParentChildRelationship.objects.filter(child=child)
        for rel in parents:
            Notification.objects.create(
                user=rel.parent.user,
                title=f"Signalement de maladie: {child.first_name}",
                message=f"Un signalement de maladie a été créé pour {child.first_name}. Veuillez consulter les détails et signer le formulaire lors de la récupération.",
                action_url=reverse('view_illness_report', args=[report.report_id])
            )

        messages.success(request, "Le signalement de maladie a été créé avec succès.")
        return redirect('view_illness_report', report_id=report.report_id)

    return render(request, 'reports/illness_report_form.html', {
        'child': child,
        'SYMPTOM_CHOICES': IllnessReport.SYMPTOM_CHOICES
    })

@login_required
@transaction.atomic
def sign_illness_report(request, report_id):
    """
    Step 2: Parent signs the report at pickup, or Director signs Public Health section.
    """
    report = get_object_or_404(IllnessReport, pk=report_id)
    user = request.user

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        departure_time = request.POST.get('departure_time')
        
        # Parent signing at pickup
        if user.role_type == 'parent':
            if not report.child.parent_relationships.filter(parent__user=user).exists():
                messages.error(request, "Accès refusé.")
                return redirect('dashboard_redirect')
            
            report.parent_signature_data = signature_data
            if departure_time:
                report.departure_time = departure_time
            report.save()
            messages.success(request, "Signature enregistrée avec succès.")
            
        # Director updating Public Health section
        elif user.role_type in ['director', 'owner']:
            reported = request.POST.get('reported_to_public_health') == 'on'
            comm_date = request.POST.get('public_health_communication_date')
            
            report.reported_to_public_health = reported
            if comm_date:
                report.public_health_communication_date = comm_date
            report.save()
            messages.success(request, "Informations de santé publique mises à jour.")

        return redirect('view_illness_report', report_id=report.report_id)

    return redirect('view_illness_report', report_id=report.report_id)

@login_required
def view_illness_report(request, report_id):
    report = get_object_or_404(IllnessReport, pk=report_id)
    # Check permissions (Educator of child, Parent of child, Director of center)
    can_view = False
    if request.user.is_superuser:
        can_view = True
    elif request.user.role_type == 'parent':
        can_view = report.child.parent_relationships.filter(parent__user=request.user).exists()
    elif request.user.role_type == 'educator':
        can_view = (report.child.assigned_educator and report.child.assigned_educator.user == request.user) or report.staff_member.user == request.user
    elif request.user.role_type == 'director':
        can_view = report.child.center.director and report.child.center.director.user == request.user

    if not can_view:
        messages.error(request, "Vous n'avez pas la permission de voir ce rapport.")
        return redirect('dashboard_redirect')

    # Resolve symptom names for display
    symptom_labels = []
    choices_dict = dict(IllnessReport.SYMPTOM_CHOICES)
    for code in report.symptoms:
        if code in choices_dict:
            symptom_labels.append(choices_dict[code])

    return render(request, 'reports/illness_report_detail.html', {
        'report': report,
        'symptom_labels': symptom_labels
    })

@login_required
@transaction.atomic
def create_reintegration_form(request, child_id):
    """
    Step 1: Educator initiates reintegration form (Annexe 12).
    Only educators can create the form. Parent will fill in their information later.
    """
    if request.user.role_type != 'educator' and not request.user.is_superuser:
        messages.error(request, "Seuls les éducateurs peuvent initier un formulaire de réintégration.")
        return redirect('dashboard_redirect')

    child = get_object_or_404(Child, pk=child_id)

    if request.method == 'POST':
        illness_name = request.POST.get('illness_name')
        illness_start_date = request.POST.get('illness_start_date')
        diagnosis_date = request.POST.get('diagnosis_date')
        treatment_start_date = request.POST.get('treatment_start_date')
        is_public_health_required = request.POST.get('is_public_health_required') == 'on'
        staff_signature = request.POST.get('staff_signature_data')

        if not illness_name or not illness_start_date or not staff_signature:
            messages.error(request, "Nom de la maladie, date du début et signature sont obligatoires.")
            return render(request, 'reports/reintegration_form_form.html', {'child': child})

        form = ReintegrationForm.objects.create(
            center=child.center,
            child=child,
            illness_name=illness_name,
            illness_start_date=illness_start_date,
            diagnosis_date=diagnosis_date if diagnosis_date else None,
            treatment_start_date=treatment_start_date if treatment_start_date else None,
            is_public_health_required=is_public_health_required,
            staff_member=request.user,
            staff_signature_data=staff_signature,
            staff_signature_date=timezone.now().date(),
            date=timezone.now().date()
        )

        # Notify Parents
        parents = ParentChildRelationship.objects.filter(child=child)
        for rel in parents:
            Notification.objects.create(
                user=rel.parent.user,
                title=f"Formulaire de réintégration: {child.first_name}",
                message=f"Un formulaire de réintégration a été créé pour {child.first_name}. Veuillez le signer pour confirmer le retour de l'enfant.",
                action_url=reverse('view_reintegration_form', args=[form.form_id])
            )

        messages.success(request, "Le formulaire de réintégration a été créé avec succès.")
        return redirect('view_reintegration_form', form_id=form.form_id)

    return render(request, 'reports/reintegration_form_form.html', {'child': child})

@login_required
@transaction.atomic
def sign_reintegration_form(request, form_id):
    """
    Step 2: Parent signs the form, or Public Health fills Section D.
    """
    form_obj = get_object_or_404(ReintegrationForm, pk=form_id)
    user = request.user

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        
        # Parent signing
        if user.role_type == 'parent':
            if not form_obj.child.parent_relationships.filter(parent__user=user).exists():
                messages.error(request, "Accès refusé.")
                return redirect('dashboard_redirect')
            
            form_obj.parent = user
            form_obj.parent_signature_data = signature_data
            form_obj.parent_signature_date = timezone.now().date()
            form_obj.save()
            messages.success(request, "Signature enregistrée avec succès.")
            
        # Director/Staff updating Public Health section (Section D)
        elif user.role_type in ['director', 'owner', 'educator']:
            ecoli_shigella = request.POST.get('ph_ecoli_shigella_negative') == 'on'
            salmonella = request.POST.get('ph_salmonella_negative') == 'on'
            ph_rep_name = request.POST.get('ph_representative_name', '')
            ph_signature = request.POST.get('ph_signature_data')
            
            if ph_signature:
                form_obj.ph_ecoli_shigella_negative = ecoli_shigella
                form_obj.ph_salmonella_negative = salmonella
                form_obj.ph_representative_name = ph_rep_name
                form_obj.ph_signature_data = ph_signature
                form_obj.ph_signature_date = timezone.now().date()
                form_obj.save()
                messages.success(request, "Informations de santé publique enregistrées.")
            else:
                messages.error(request, "La signature de santé publique est requise.")

        return redirect('view_reintegration_form', form_id=form_obj.form_id)

    return redirect('view_reintegration_form', form_id=form_obj.form_id)

@login_required
def view_reintegration_form(request, form_id):
    form_obj = get_object_or_404(ReintegrationForm, pk=form_id)
    # Permissions same as illness report
    can_view = False
    if request.user.is_superuser:
        can_view = True
    elif request.user.role_type == 'parent':
        can_view = form_obj.child.parent_relationships.filter(parent__user=request.user).exists()
    elif request.user.role_type == 'educator':
        can_view = (form_obj.child.assigned_educator and form_obj.child.assigned_educator.user == request.user) or form_obj.staff_member == request.user
    elif request.user.role_type in ['director', 'owner']:
        can_view = form_obj.child.center.director and form_obj.child.center.director.user == request.user

    if not can_view:
        messages.error(request, "Permission refusée.")
        return redirect('dashboard_redirect')

    return render(request, 'reports/reintegration_form_detail.html', {'form': form_obj})
