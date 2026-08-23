from django import forms
from .models import DailyActivityLog

class DailyCheckupForm(forms.ModelForm):
    class Meta:
        model = DailyActivityLog
        exclude = ['report', 'date', 'day_name', 'signed_by', 'signed_at']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 3}),
            'symptoms_desc': forms.Textarea(attrs={'rows': 2}),
            'mood_autre_desc': forms.TextInput(attrs={'placeholder': 'Specify...'}),
        }
