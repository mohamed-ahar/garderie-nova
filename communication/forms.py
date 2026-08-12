from django import forms
from .models import Message
from accounts.models import User, ParentProfile, Educator, Director
from dashboard.models import Child 

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["receiver", "subject", "body"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")  # current logged in user
        super().__init__(*args, **kwargs)

        # Determine possible receivers based on user role
        if user.role_type == "parent":
            # parent can send only to educators of their children
            children = Child.objects.filter(parent_relationships__parent__user=user)
            educators = Educator.objects.filter(assigned_children__in=children).distinct()
            self.fields["receiver"].queryset = User.objects.filter(user_id__in=[e.user.user_id for e in educators])
        elif user.role_type == "director":
            # director can send to educators of their center OR other directors
            center = getattr(user, "director_profile", None)
            if center and center.managed_center:
                educators = Educator.objects.filter(center=center.managed_center)
                other_directors = User.objects.filter(role_type="director").exclude(user_id=user.user_id)
                allowed_users = list(educators.values_list("user__user_id", flat=True)) + list(other_directors.values_list("user_id", flat=True))
                self.fields["receiver"].queryset = User.objects.filter(user_id__in=allowed_users)
        else:
            # other roles can send to directors of their center
            self.fields["receiver"].queryset = User.objects.filter(role_type="director")
