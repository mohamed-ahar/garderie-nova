from django import forms
from django.contrib.auth import get_user_model
from accounts.models import Director, User
from dashboard.models import Center, Room, Organization
from accounts.models import ViceDirector

User = get_user_model()
class ViceDirectorCreationForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'premium-input'}))
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'premium-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'premium-input'}))

    class Meta:
        model = ViceDirector
        fields = [] # Khawi: hit center ma-bqash darouri f l-bedya

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
# 2. Form dyal l-Edit (Profile Update) - Center m-hyyed mn hna
class ViceDirectorForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'premium-input'})
    )
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'premium-input'})
    )

    class Meta:
        model = ViceDirector
        # Hiyydna 'center' mn hna: l-Owner ma-iqderch i-beddel l-node f l-edit
        fields = ['specific_permissions']

    def __init__(self, *args, **kwargs):
        # Ma-biqatsh hta logic dyal queryset d l-center hit field m-hyyed
        super().__init__(*args, **kwargs)

# -- Center Form
class CenterCreationForm(forms.ModelForm):
    class Meta:
        model = Center
        fields = ['name'] 
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all',
                'placeholder': 'Smiyt l-center (masalan: Center El Amal)'
            }),
        }
        labels = {
            'name': 'Center Name',
        }

class DirectorCreationForm(forms.ModelForm):
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
        self.user_owner = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        # 1. Create User account
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            full_name=self.cleaned_data['full_name'],
            role_type='director'
        )
        
        # 2. Create Director profile
        director = super().save(commit=False)
        director.user = user
        
        # 3. Link Director to Owner's Organization
        if self.user_owner:
            try:
                owner_org = Organization.objects.get(owner__user=self.user_owner)
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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # 1. Njibu l-Organization dyal l-Owner
            try:
                # Kandiru filter b l-User li dakhil (Owner)
                owner_org = Organization.objects.get(owner__user=user)
                
                # 2. Queryset: Kan-jibu ay Director taba3 l-had l-Org
                # AND mazzal ma m-assigni l-center (bach may-kounch double assignment)
                self.fields['director'].queryset = Director.objects.filter(
                    organization=owner_org, 
                    managed_center__isnull=True
                ).select_related('user') # Optimisation
                
            except Organization.DoesNotExist:
                self.fields['director'].queryset = Director.objects.none()
        
        self.fields['director'].label = "Available Directors (Promoted or Created)"

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

class CSVUploadForm(forms.Form):
    file = forms.FileField(
        label="Upload CSV",
        help_text="Upload a CSV file with parent and children info"
    )
