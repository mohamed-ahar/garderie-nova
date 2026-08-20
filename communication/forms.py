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
        user = kwargs.pop("user")  # User li m-connecter (request.user)
        super().__init__(*args, **kwargs)

        # 1. PARENT: I-sift ghir l-Educators dial wladou
        if user.role_type == "parent":
            children = Child.objects.filter(parent_relationships__parent__user=user)
            educator_user_ids = Educator.objects.filter(
                assigned_children__in=children
            ).values_list("user_id", flat=True).distinct()
            self.fields["receiver"].queryset = User.objects.filter(user_id__in=educator_user_ids)

        # 2. DIRECTOR: L-mou3adala dial l-Organization + Confirmation
        elif user.role_type == "director":
            director_profile = getattr(user, "director_profile", None)
            allowed_ids = []

            if director_profile and director_profile.organization:
                # A. Ga3 les Educators dial l-Org dyalou (mn ga3 les centers)
                educator_ids = Educator.objects.filter(
                    center__organization=director_profile.organization
                ).values_list("user_id", flat=True)
                allowed_ids.extend(list(educator_ids))

                # B. Directors f nefs l-Organization (Hado dima m-autorisiyin)
                internal_directors = Director.objects.filter(
                    organization=director_profile.organization
                ).exclude(user_id=user.user_id).values_list("user_id", flat=True)
                allowed_ids.extend(list(internal_directors))

                # C. Directors mn Organizations khrine (After Confirmation)
                # Kan-qalbou f table 'DirectorConnection' 3la l-khana 'is_confirmed=True'
                confirmed_connections = DirectorConnection.objects.filter(
                    (Q(from_director=director_profile) | Q(to_director=director_profile)),
                    is_confirmed=True
                ).values_list("from_director__user_id", "to_director__user_id")

                # Kan-kharjou l-IDs mn les tuples dial confirmed_connections
                for from_id, to_id in confirmed_connections:
                    if from_id != user.user_id: allowed_ids.append(from_id)
                    if to_id != user.user_id: allowed_ids.append(to_id)

            # Filtering final (Distinct bach may-kounch t-krar)
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

        # 4. DEFAULT (Owner): I-qder i-hder m3a koulchi
        else:
            self.fields["receiver"].queryset = User.objects.all().exclude(user_id=user.user_id)

        # Customization simple dial l-form design
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})