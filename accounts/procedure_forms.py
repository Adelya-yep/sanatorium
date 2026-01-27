# accounts/procedure_forms.py
from django import forms
from .models import Procedure, Doctor, Appointment, ScheduleSlot, MedicalRecord


class AppointmentForm(forms.ModelForm):
    """Форма записи на процедуру"""

    class Meta:
        model = Appointment
        fields = ['procedure', 'doctor', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)

        # Фильтруем активные процедуры
        self.fields['procedure'].queryset = Procedure.objects.filter(is_active=True)

        # Врачи только активные
        self.fields['doctor'].queryset = Doctor.objects.filter(
            user__is_active=True
        )


class MedicalRecordForm(forms.ModelForm):
    """Форма медицинской карты"""

    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'treatment_plan', 'attending_doctor', 'recommendations']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'treatment_plan': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'recommendations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class ScheduleSlotForm(forms.ModelForm):
    """Форма создания слота расписания"""

    class Meta:
        model = ScheduleSlot
        fields = ['day_of_week', 'start_time', 'end_time', 'max_appointments']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }