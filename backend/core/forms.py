from django import forms
from .models import Group, Room, Center

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'room', 'center']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all dark:text-white',
                'placeholder': 'Enter group name'
            }),
            'room': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all dark:text-white'
            }),
            'center': forms.Select(attrs={
                'class': 'hidden' # Usually set automatically based on user context
            })
        }

    def __init__(self, *args, **kwargs):
        center = kwargs.pop('center', None)
        super(GroupForm, self).__init__(*args, **kwargs)
        if center:
            self.fields['room'].queryset = Room.objects.filter(center=center)
            self.fields['center'].initial = center
