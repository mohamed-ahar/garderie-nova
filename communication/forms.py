from django import forms
from .models import Message
from accounts.models import User, Educator, Director
from dashboard.models import Child 

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["receiver", "subject", "body"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")  # current logged in user
        super().__init__(*args, **kwargs)

        # 1. PARENT: isifet l les Educators dyal wlado
        if user.role_type == "parent":
            children = Child.objects.filter(parent_relationships__parent__user=user)
            educator_user_ids = Educator.objects.filter(
                assigned_children__in=children
            ).values_list("user_id", flat=True).distinct()
            
            self.fields["receiver"].queryset = User.objects.filter(user_id__in=educator_user_ids)

        # 2. DIRECTOR: isifet l les Educators dyal l'center dyalo + other Directors
        elif user.role_type == "director":
            center_profile = getattr(user, "director_profile", None)
            allowed_ids = []

            # Educators dyal l'center
            if center_profile and center_profile.managed_center:
                educator_ids = Educator.objects.filter(
                    center=center_profile.managed_center
                ).values_list("user_id", flat=True)
                allowed_ids.extend(list(educator_ids))

            # Les autres directors
            other_directors = User.objects.filter(role_type="director").exclude(user_id=user.user_id)
            allowed_ids.extend(list(other_directors.values_list("user_id", flat=True)))

            self.fields["receiver"].queryset = User.objects.filter(user_id__in=allowed_ids)

        # 3. EDUCATOR: isifet rir l Director dyal l'center dyalo
        elif user.role_type == "educator":
            educator_profile = getattr(user, "educator_profile", None)
            if educator_profile and educator_profile.center:
                # Kan-qalbo 3la l'Director li m-assigné l had l'center
                director_user_ids = Director.objects.filter(
                    managed_center=educator_profile.center
                ).values_list("user_id", flat=True)
                
                self.fields["receiver"].queryset = User.objects.filter(user_id__in=director_user_ids)
            else:
                # Ila l'educator ma-3ndoch center, ma-isifet l hed (queryset khawya)
                self.fields["receiver"].queryset = User.objects.none()

        # 4. DEFAULT: ay wahed akhor (owner, etc.)
        else:
            self.fields["receiver"].queryset = User.objects.filter(role_type="director")