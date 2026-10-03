from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from datetime import datetime

from dashboard.models import Child, ParentChildRelationship, Notification
from ..models import IllnessReport, ReintegrationForm


@login_required
@transaction.atomic
def create_reintegration_form(request, child_id):
    """
    Step 1: Educator or Parent initiates reintegration form (Annexe 12).
    """
    user = request.user
    child = get_object_or_404(Child, pk=child_id)
    
    # Permission Check
    has_access = False
    if user.is_superuser:
        has_access = True
    elif user.role_type == 'educator':
        has_access = (child.assigned_educator and child.assigned_educator.user == user) or child.center.educators.filter(user=user).exists()
    elif user.role_type == 'parent':
        has_access = child.parent_relationships.filter(parent__user=user).exists()
    
    if not has_access:
        messages.error(request, "Vous n'avez pas la permission d'initier ce formulaire.")
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        # If educator, we ignore illnesses/dates (they can't even see them in the template)
        if user.role_type == 'educator' or user.is_superuser:
            selected_illnesses = []
            illness_start_date = None
            diagnosis_date = None
            treatment_start_date = None
            is_public_health_required = False
        else:
            # Parent initiating can fill info
            selected_illnesses = request.POST.getlist('illnesses')
            other_illnesses = request.POST.getlist('other_illnesses[]')
            illness_start_date = request.POST.get('illness_start_date')
            diagnosis_date = request.POST.get('diagnosis_date')
            treatment_start_date = request.POST.get('treatment_start_date')
            is_public_health_required = request.POST.get('is_public_health_required') == 'on'

            if not selected_illnesses or not illness_start_date:
                messages.error(request, "Au moins une maladie et la date du début sont obligatoires.")
                return render(request, 'reports/reintegration_form_form.html', {
                    'child': child,
                    'SYMPTOM_CHOICES': IllnessReport.SYMPTOM_CHOICES
                })
            
            # Merge illnesses
            final_illnesses = [i for i in selected_illnesses if i != 'others']
            for other in other_illnesses:
                if other.strip():
                    final_illnesses.append(other.strip())
            selected_illnesses = final_illnesses

        form = ReintegrationForm.objects.create(
            center=child.center,
            child=child,
            illnesses=selected_illnesses,
            illness_start_date=illness_start_date if illness_start_date else None,
            diagnosis_date=diagnosis_date if diagnosis_date else None,
            treatment_start_date=treatment_start_date if treatment_start_date else None,
            is_public_health_required=is_public_health_required,
            date=timezone.now().date()
        )

        # Notify the other party
        if user.role_type in ['educator', 'director', 'owner'] or user.is_superuser:
            # Staff initiated -> Notify Parents to fill/sign
            parents = ParentChildRelationship.objects.filter(child=child)
            for rel in parents:
                Notification.objects.create(
                    user=rel.parent.user,
                    title=f"Action requise : Réintégration de {child.first_name}",
                    message=f"L'établissement a initié un formulaire de réintégration. Veuillez remplir les détails et signer.",
                    action_url=reverse('view_reintegration_form', args=[form.form_id])
                )
        else:
            # Parent initiated -> Notify Educator/Director
            staff_to_notify = []
            if child.assigned_educator:
                staff_to_notify.append(child.assigned_educator.user)
            if child.center.director:
                staff_to_notify.append(child.center.director.user)
            
            # Also notify other educators in the center just in case
            for center_educator in child.center.educators.all():
                staff_to_notify.append(center_educator.user)
            
            for staff_user in set(staff_to_notify):
                Notification.objects.create(
                    user=staff_user,
                    title=f"Nouveau formulaire de réintégration : {child.first_name}",
                    message=f"Le parent de {child.first_name} a initié un formulaire de réintégration. Votre validation sera requise après leur signature.",
                    action_url=reverse('view_reintegration_form', args=[form.form_id])
                )

        messages.success(request, "Le formulaire de réintégration a été initié avec succès.")
        return redirect('view_reintegration_form', form_id=form.form_id)

    return render(request, 'reports/reintegration_form_form.html', {
        'child': child,
        'SYMPTOM_CHOICES': IllnessReport.SYMPTOM_CHOICES
    })

@login_required
@transaction.atomic
def sign_reintegration_form(request, form_id):
    """
    Step 2: Parent signs the form (and can update info).
    Step 3: Educator signs after Parent (final signature).
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
            
            # Parent can also update dates and illnesses if they weren't set correctly during initiation
            diagnosis_date = request.POST.get('diagnosis_date')
            treatment_start_date = request.POST.get('treatment_start_date')
            illness_start_date = request.POST.get('illness_start_date')
            selected_illnesses = request.POST.getlist('illnesses')
            other_illnesses = request.POST.getlist('other_illnesses[]')
            is_public_health_required = request.POST.get('is_public_health_required') == 'on'

            if not form_obj.illnesses and selected_illnesses:
                # Merge selected standard illnesses and custom ones
                final_illnesses = [i for i in selected_illnesses if i != 'others']
                for other in other_illnesses:
                    if other.strip():
                        final_illnesses.append(other.strip())
                form_obj.illnesses = final_illnesses

            if not form_obj.illness_start_date and illness_start_date:
                form_obj.illness_start_date = illness_start_date
                
            if diagnosis_date:
                form_obj.diagnosis_date = diagnosis_date
            if treatment_start_date:
                form_obj.treatment_start_date = treatment_start_date

            # Parent can also flag if PH is required
            form_obj.is_public_health_required = is_public_health_required

            # Final validation before allowing parent signature
            if not form_obj.illnesses or not form_obj.illness_start_date:
                messages.error(request, "La maladie et sa date de début sont requises pour signer.")
                return redirect('view_reintegration_form', form_id=form_obj.form_id)

            form_obj.parent = user
            form_obj.parent_signature_data = signature_data
            form_obj.parent_signature_date = timezone.now().date()
            form_obj.save()
            
            # Notify Educator that it's ready for final signature
            staff_to_notify = []
            if form_obj.child.assigned_educator:
                staff_to_notify.append(form_obj.child.assigned_educator.user)
            if form_obj.child.center.director:
                staff_to_notify.append(form_obj.child.center.director.user)
            
            for staff_user in set(staff_to_notify):
                Notification.objects.create(
                    user=staff_user,
                    title=f"Signature requise (Éducateur) : Réintégration {form_obj.child.first_name}",
                    message=f"Le parent a signé le formulaire. Votre signature finale est requise pour terminer le document.",
                    action_url=reverse('view_reintegration_form', args=[form_obj.form_id])
                )
            
            messages.success(request, "Votre signature a été enregistrée. L'éducateur doit maintenant valider le formulaire.")
            
        # Educator/Staff signing (Final Step)
        elif user.role_type in ['educator', 'director', 'owner', 'superuser']:
            # Validation: Ensure parent has signed first
            if not form_obj.parent_signature_data:
                messages.error(request, "Le parent doit signer le formulaire avant la validation finale de l'éducateur.")
                return redirect('view_reintegration_form', form_id=form_obj.form_id)

            form_obj.staff_member = user
            form_obj.staff_signature_data = signature_data
            form_obj.staff_signature_date = timezone.now().date()
            form_obj.save()
            
            # Notify Parents that it's finished
            parents = ParentChildRelationship.objects.filter(child=form_obj.child)
            for rel in parents:
                Notification.objects.create(
                    user=rel.parent.user,
                    title=f"Réintégration terminée : {form_obj.child.first_name}",
                    message=f"Le formulaire de réintégration pour {form_obj.child.first_name} est maintenant complété et validé.",
                    action_url=reverse('view_reintegration_form', args=[form_obj.form_id])
                )
            
            messages.success(request, "Le formulaire a été validé et est maintenant terminé.")
            
        # Public Health (Special Section D)
        elif request.POST.get('is_ph_update') == 'true':
            ecoli_shigella = request.POST.get('ph_ecoli_shigella_negative') == 'on'
            salmonella = request.POST.get('ph_salmonella_negative') == 'on'
            ph_rep_name = request.POST.get('ph_representative_name', '')
            if signature_data:
                form_obj.ph_ecoli_shigella_negative = ecoli_shigella
                form_obj.ph_salmonella_negative = salmonella
                form_obj.ph_representative_name = ph_rep_name
                form_obj.ph_signature_data = signature_data
                form_obj.ph_signature_date = timezone.now().date()
                form_obj.save()
                messages.success(request, "Informations de santé publique enregistrées.")

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

    # Resolve illness names for display
    illness_labels = []
    choices_dict = dict(IllnessReport.SYMPTOM_CHOICES)
    for code in form_obj.illnesses:
        if code in choices_dict:
            # Skip the generic 'others' code if we have custom ones, or just show it if nothing else
            if code == 'others' and len(form_obj.illnesses) > 1:
                continue
            illness_labels.append(choices_dict[code])
        else:
            # It's a custom illness name
            illness_labels.append(code)

    return render(request, 'reports/reintegration_form_detail.html', {
        'form': form_obj,
        'illness_labels': illness_labels,
        'SYMPTOM_CHOICES': IllnessReport.SYMPTOM_CHOICES
    })

@login_required
def download_reintegration_form_pdf(request, form_id):
    """
    Generate and download Annexe 12 (Reintegration Form) as PDF.
    Only accessible by director, owner, or educator.
    """
    user = request.user
    if user.role_type not in ['director', 'owner', 'educator'] and not user.is_superuser:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard_redirect')
    
    form_obj = get_object_or_404(ReintegrationForm, pk=form_id)
    
    # Resolve illness names
    illness_labels = []
    choices_dict = dict(IllnessReport.SYMPTOM_CHOICES)
    for code in form_obj.illnesses:
        if code in choices_dict:
            if code == 'others' and len(form_obj.illnesses) > 1:
                continue
            illness_labels.append(choices_dict[code])
        else:
            illness_labels.append(code)
            
    context = {
        'form': form_obj,
        'illness_labels': illness_labels,
        'center': form_obj.child.center,
        'generated_date': datetime.now(),
    }
    
    html_string = render_to_string('reports/reintegration_form_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    filename = f"annexe12_{form_obj.child.first_name}_{form_obj.date.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
