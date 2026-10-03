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
from accounts.models import Educator
from ..models import IllnessReport


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
        recent_illness_report_exists = request.POST.get('recent_illness_report_exists') == 'True'
        reported_to_public_health = request.POST.get('reported_to_public_health') == 'True'
        public_health_communication_date = request.POST.get('public_health_communication_date')
        staff_signature = request.POST.get('staff_signature_data')

        if not selected_symptoms or not staff_signature:
            messages.error(request, "Au moins un symptôme et la signature sont obligatoires.")
            return render(request, 'reports/illness_report_form.html', {'child': child, 'SYMPTOM_CHOICES': IllnessReport.SYMPTOM_CHOICES})

        now = timezone.now()
        report = IllnessReport.objects.create(
            child=child,
            staff_member=educator,
            symptoms=selected_symptoms,
            explanation=explanation,
            temperature=temperature if temperature else None,
            time_taken=time_taken if time_taken else None,
            medication_administered=medication_administered,
            medication_details=medication_details,
            recent_illness_report_exists=recent_illness_report_exists,
            reported_to_public_health=reported_to_public_health,
            public_health_communication_date=public_health_communication_date if public_health_communication_date else None,
            parent_notified_at=now.time(),
            staff_signature_data=staff_signature,
            date=now.date()
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
def download_illness_report_pdf(request, report_id):
    """
    Generate and download Annexe 11 (Illness Report) as PDF.
    Only accessible by director, owner, or educator.
    """
    user = request.user
    if user.role_type not in ['director', 'owner', 'educator'] and not user.is_superuser:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard_redirect')
    
    report = get_object_or_404(IllnessReport, pk=report_id)
    
    # Resolve symptom names
    symptom_labels = []
    choices_dict = dict(IllnessReport.SYMPTOM_CHOICES)
    for code in report.symptoms:
        if code in choices_dict:
            symptom_labels.append(choices_dict[code])
            
    context = {
        'report': report,
        'symptom_labels': symptom_labels,
        'center': report.child.center,
        'generated_date': datetime.now(),
    }
    
    html_string = render_to_string('reports/illness_report_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    filename = f"annexe11_{report.child.first_name}_{report.date.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
