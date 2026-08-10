from django import forms
from accounts.models import Director
from dashboard.models import Center, Room
from accounts.models import User
from django import forms
from django.contrib.auth import get_user_model
from accounts.models import Director
#--center form hadi xof il briti tzid xi haja 
class CenterCreationForm(forms.ModelForm):
    class Meta:
        model = Center
        # Ghadi n-asta3mlo ghir 'name' 7it l-fields khorin ma-kayninsh f model Center
        fields = ['name'] 
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all',
                'placeholder': 'Smiyt l-center (masalan: Center El Amal)'
            }),
        }
        labels = {
            'name': 'center name',
        }


User = get_user_model()
class DirectorCreationForm(forms.ModelForm):
    # Field dyal User model (ma-m-rbotinsh b models.py nichan hna)
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'director@example.com', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    class Meta:
        model = Director
        fields = ['qualification_cert', 'hired_at']
        widgets = {
            'hired_at': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-lg'}),
            'qualification_cert': forms.TextInput(attrs={'placeholder': 'e.g. Master in Education', 'class': 'w-full px-4 py-2 border rounded-lg'}),
        }

    def __init__(self, *args, **kwargs):
        # Kan-akhdou l-user owner men l-view bach n-qalbo 3la l-Org dyalo
        self.user_owner = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        from dashboard.models import Organization
        
        # 1. Creer l-User account (Ghir l-Auth data)
        # Hna HIYEDNA 'organization' bash mat-tla3sh l-erreur
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            full_name=self.cleaned_data['full_name'],
            role_type='director'
        )
        
        # 2. Creer l-Director profile (li howa model dyal had l-form)
        director = super().save(commit=False)
        director.user = user
        
        # 3. Rbet l-Director b l-Organization dyal l-Owner nichan
        if self.user_owner:
            try:
                # Kan-jibu l-org li tab3a l l-owner li m-connecti daba
                owner_org = Organization.objects.get(owner__user=self.user_owner)
                # Daba had l-field 'organization' khass ikoun f model 'Director'
                director.organization = owner_org 
            except (Organization.DoesNotExist, AttributeError):
                pass
        
        if commit:
            director.save()
        return director
class AssignDirectorForm(forms.ModelForm):
    director = forms.ModelChoiceField(
        queryset=Director.objects.none(),
        required=True,
        empty_label="Select a Director",
        widget=forms.Select(attrs={
            'class': 'premium-input w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all'
        })
    )

    class Meta:
        model = Center
        fields = ['director']

    def __init__(self, *args, **kwargs):
        # 1. Nakhdou l-user (Owner) men l-view
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # 2. Njibou l-org dyal had l-owner
            # 3. Filtrer l-directeurs: 
            #    - Li tab3in l had l-org (li creeyahom l-owner)
            #    - O li center dyalhom IS NULL (baqi khawyin)
            self.fields['director'].queryset = Director.objects.filter(
                organization__owner__user=user, 
                center__isnull=True
            )
        
        self.fields['director'].label = "Available Directors (Created by you)"


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'room_surface','max_capacity','age_group']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none transition-all',
                'placeholder': 'Room name (e.g., Room A)'
            }),
            'room_surface': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 outline-none transition-all',
                'placeholder': 'Room surface area in m²',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'name': 'Room Name',
            'room_surface': 'Room Surface (m²)',
        }
    