from django import forms
from .models import DailyActivityLog, Attendance

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['arrival_time', 'departure_time', 'is_absent', 'absence_reason_code', 'absence_reason_notes']
        widgets = {
            'arrival_time': forms.TimeInput(attrs={'type': 'time'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time'}),
            'absence_reason_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_absent = cleaned_data.get('is_absent')
        arrival_time = cleaned_data.get('arrival_time')
        departure_time = cleaned_data.get('departure_time')

        if not is_absent:
            if not arrival_time:
                self.add_error('arrival_time', "Arrival time is required if the child is not absent.")
            
            if arrival_time and departure_time and departure_time <= arrival_time:
                self.add_error('departure_time', "Departure time must be after arrival time.")
        
        return cleaned_data

class DailyCheckupForm(forms.ModelForm):
    # Food fields (to match template)
    snack_am_amount = forms.ChoiceField(choices=DailyActivityLog.Amount.choices, required=False)
    snack_am_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    lunch_amount = forms.ChoiceField(choices=DailyActivityLog.Amount.choices, required=False)
    lunch_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    snack_pm_amount = forms.ChoiceField(choices=DailyActivityLog.Amount.choices, required=False)
    snack_pm_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)

    # Bottle fields
    bottle_am_amount = forms.ChoiceField(choices=DailyActivityLog.Amount.choices, required=False)
    bottle_am_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    bottle_lunch_amount = forms.ChoiceField(choices=DailyActivityLog.Amount.choices, required=False)
    bottle_lunch_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    bottle_pm_amount = forms.ChoiceField(choices=DailyActivityLog.Amount.choices, required=False)
    bottle_pm_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)

    # Nap fields
    nap_start = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    nap_end = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)

    # Diaper Change 1
    diaper_1_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    diaper_1_sec = forms.BooleanField(required=False)
    diaper_1_mouille = forms.BooleanField(required=False)
    diaper_1_toilette = forms.BooleanField(required=False)
    diaper_1_selles = forms.BooleanField(required=False)
    diaper_1_consistency = forms.CharField(max_length=100, required=False)

    # Diaper Change 2
    diaper_2_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    diaper_2_sec = forms.BooleanField(required=False)
    diaper_2_mouille = forms.BooleanField(required=False)
    diaper_2_toilette = forms.BooleanField(required=False)
    diaper_2_selles = forms.BooleanField(required=False)
    diaper_2_consistency = forms.CharField(max_length=100, required=False)

    # Diaper Change 3
    diaper_3_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    diaper_3_sec = forms.BooleanField(required=False)
    diaper_3_mouille = forms.BooleanField(required=False)
    diaper_3_toilette = forms.BooleanField(required=False)
    diaper_3_selles = forms.BooleanField(required=False)
    diaper_3_consistency = forms.CharField(max_length=100, required=False)

    # Diaper Change 4
    diaper_4_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    diaper_4_sec = forms.BooleanField(required=False)
    diaper_4_mouille = forms.BooleanField(required=False)
    diaper_4_toilette = forms.BooleanField(required=False)
    diaper_4_selles = forms.BooleanField(required=False)
    diaper_4_consistency = forms.CharField(max_length=100, required=False)

    class Meta:
        model = DailyActivityLog
        exclude = ['report', 'date', 'day_name', 'signed_by', 'signed_at', 'diaper_logs', 'bottles_tracking', 'nap_tracking']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 3}),
            'symptoms_desc': forms.Textarea(attrs={'rows': 2}),
            'mood_autre_desc': forms.TextInput(attrs={'placeholder': 'Specify...'}),
            'signature_data': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Unpack diaper logs
            logs = self.instance.diaper_logs
            for i, log in enumerate(logs[:4], 1):
                self.initial[f'diaper_{i}_time'] = log.get('time')
                self.initial[f'diaper_{i}_sec'] = log.get('is_sec', False)
                self.initial[f'diaper_{i}_mouille'] = log.get('is_mouille', False)
                self.initial[f'diaper_{i}_toilette'] = log.get('is_toilette', False)
                self.initial[f'diaper_{i}_selles'] = log.get('is_selles', False)
                self.initial[f'diaper_{i}_consistency'] = log.get('consistency', '')

            # Unpack food
            food = self.instance.food_tracking
            for entry in food:
                name = entry.get('name')
                if name in ['snack_am', 'lunch', 'snack_pm']:
                    self.initial[f'{name}_amount'] = entry.get('amount')
                    self.initial[f'{name}_time'] = entry.get('time')

            # Unpack bottles
            bottles = self.instance.bottles_tracking
            if len(bottles) > 0:
                self.initial['bottle_am_time'] = bottles[0].get('time')
                self.initial['bottle_am_amount'] = bottles[0].get('amount')
            if len(bottles) > 1:
                self.initial['bottle_lunch_time'] = bottles[1].get('time')
                self.initial['bottle_lunch_amount'] = bottles[1].get('amount')
            if len(bottles) > 2:
                self.initial['bottle_pm_time'] = bottles[2].get('time')
                self.initial['bottle_pm_amount'] = bottles[2].get('amount')

            # Unpack naps
            naps = self.instance.nap_tracking
            if naps:
                self.initial['nap_start'] = naps[0].get('start')
                self.initial['nap_end'] = naps[0].get('end')

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Pack food tracking
        food_tracking = []
        for name in ['snack_am', 'lunch', 'snack_pm']:
            amount = self.cleaned_data.get(f'{name}_amount')
            time = self.cleaned_data.get(f'{name}_time')
            if amount or time:
                food_tracking.append({
                    'name': name,
                    'amount': amount,
                    'time': time.strftime('%H:%M') if hasattr(time, 'strftime') else time,
                })
        instance.food_tracking = food_tracking

        # Pack diaper logs
        diaper_logs = []
        for i in range(1, 5):
            time = self.cleaned_data.get(f'diaper_{i}_time')
            if time:
                diaper_logs.append({
                    'time': time.strftime('%H:%M') if hasattr(time, 'strftime') else time,
                    'is_sec': self.cleaned_data.get(f'diaper_{i}_sec'),
                    'is_mouille': self.cleaned_data.get(f'diaper_{i}_mouille'),
                    'is_toilette': self.cleaned_data.get(f'diaper_{i}_toilette'),
                    'is_selles': self.cleaned_data.get(f'diaper_{i}_selles'),
                    'consistency': self.cleaned_data.get(f'diaper_{i}_consistency'),
                })
        instance.diaper_logs = diaper_logs

        # Pack bottles
        bottles_tracking = []
        for prefix in ['am', 'lunch', 'pm']:
            time = self.cleaned_data.get(f'bottle_{prefix}_time')
            amount = self.cleaned_data.get(f'bottle_{prefix}_amount')
            if time or amount:
                bottles_tracking.append({
                    'time': time.strftime('%H:%M') if hasattr(time, 'strftime') else time,
                    'amount': amount
                })
        instance.bottles_tracking = bottles_tracking

        # Pack naps
        nap_start = self.cleaned_data.get('nap_start')
        nap_end = self.cleaned_data.get('nap_end')
        if nap_start or nap_end:
            instance.nap_tracking = [{
                'start': nap_start.strftime('%H:%M') if hasattr(nap_start, 'strftime') else nap_start,
                'end': nap_end.strftime('%H:%M') if hasattr(nap_end, 'strftime') else nap_end,
            }]

        if commit:
            instance.save()
        return instance
