from django import forms
from .models import Message, DirectorConnection
from accounts.models import User, Educator, Director
from dashboard.models import Child
from django.db.models import Q

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["receiver", "subject", "body"]

    def __init__(self, *args, **kwargs):
        # Kan-cheddo l-user li m-loggi bach n-filitriw 3lih
        user = kwargs.pop("user") 
        super().__init__(*args, **kwargs)

        # 1. PARENT: I-sift ghi l-Educators dial wladou
        if user.role_type == "parent":
            children = Child.objects.filter(parent_relationships__parent__user=user)
            educator_user_ids = Educator.objects.filter(
                assigned_children__in=children
            ).values_list("user_id", flat=True).distinct()
            
            self.fields["receiver"].queryset = User.objects.filter(user_id__in=educator_user_ids)

        # 2. DIRECTOR: I-sift ghi l-moudara' (Internal + External confirmed)
        elif user.role_type == "director":
            director_profile = getattr(user, "director_profile", None)
            allowed_ids = []

            if director_profile and director_profile.organization:
                # A. Directors f nefs l-Organization (Internal)
                internal_directors = Director.objects.filter(
                    organization=director_profile.organization
                ).exclude(user_id=user.user_id).values_list("user_id", flat=True)
                allowed_ids.extend(list(internal_directors))

                # B. Directors mn Organizations khrine (After Confirmation)
                confirmed_connections = DirectorConnection.objects.filter(
                    (Q(from_director=director_profile) | Q(to_director=director_profile)),
                    is_confirmed=True
                ).values_list("from_director__user_id", "to_director__user_id")

                for from_id, to_id in confirmed_connections:
                    if from_id != user.user_id: allowed_ids.append(from_id)
                    if to_id != user.user_id: allowed_ids.append(to_id)

            # Filtering l-field bach ibano ghi l-IDs li lqina
            self.fields["receiver"].queryset = User.objects.filter(
                user_id__in=set(allowed_ids)
            ).distinct()

        # 3. EDUCATOR: I-sift l-ga3 les Directors dial l-Organization dyalou
        elif user.role_type == "educator":
            educator_profile = getattr(user, "educator_profile", None)
            if educator_profile and educator_profile.center:
                director_user_ids = Director.objects.filter(
                    organization=educator_profile.center.organization
                ).values_list("user_id", flat=True)
                
                self.fields["receiver"].queryset = User.objects.filter(user_id__in=director_user_ids)
            else:
                self.fields["receiver"].queryset = User.objects.none()

        # 4. DEFAULT/OWNER: I-qder i-hder m3a koulchi
        else:
            self.fields["receiver"].queryset = User.objects.all().exclude(user_id=user.user_id)

        # Customization dial l-design (Bootstrap classes)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})