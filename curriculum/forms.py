from django import forms
from django.apps import apps
from .models import Lesson

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'pdf_file', 'video_url', 'content_text', 'educator']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white/50 backdrop-blur-sm',
                'placeholder': 'Dert smiya dial dars...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white/50 backdrop-blur-sm',
                'rows': 3,
                'placeholder': 'Chi wssef sghir...'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white/50 backdrop-blur-sm',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'educator': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white/50 backdrop-blur-sm shadow-sm',
            }),
            'content_text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white/50 backdrop-blur-sm',
                'rows': 5,
                'placeholder': 'Kteb dars hna ila mafich PDF...'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Njibo l-user mn l-kwargs li siftna mn l-view
        user = kwargs.pop('user', None)
        super(LessonForm, self).__init__(*args, **kwargs)
        
        # Kandiro import hna west __init__ bach n-tfadaw "model not loaded" error
        # Hit l-models dyalk f 'accounts'
        Educator = apps.get_model('accounts', 'Educator')
        
        if user:
            # Ila kan Director: i-chouf ghir educators dial organization dyalo
            if user.role_type == 'director':
                try:
                    org = user.director_profile.organization
                    self.fields['educator'].queryset = Educator.objects.filter(center__organization=org)
                except Exception:
                    self.fields['educator'].queryset = Educator.objects.none()
            
            # Ila kan Vice Director: i-chouf ghir educators dial center dyalo
            elif user.role_type == 'vice_director':
                try:
                    center = user.vice_director_profile.center
                    self.fields['educator'].queryset = Educator.objects.filter(center=center)
                except Exception:
                    self.fields['educator'].queryset = Educator.objects.none()
            
            # Owner i-chouf kolchi
            elif user.role_type == 'owner':
                self.fields['educator'].queryset = Educator.objects.all()