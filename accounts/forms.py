from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GuestProfile, Booking, Room
from django.core.exceptions import ValidationError
from datetime import date


class GuestRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            GuestProfile.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone']
            )
        return user


class BookingForm(forms.ModelForm):
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        label='Выберите номер',
        empty_label="-- Выберите номер --",
        widget=forms.Select(attrs={'class': 'form-control form-input'})
    )

    class Meta:
        model = Booking
        fields = ['room', 'check_in', 'check_out', 'guests', 'notes']
        widgets = {
            'check_in': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-input',
                'min': date.today().isoformat()
            }),
            'check_out': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-input',
                'min': date.today().isoformat()
            }),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control form-input',
                'min': 1,
                'max': 4
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-input',
                'rows': 3,
                'placeholder': 'Дополнительные пожелания...'
            }),
        }
        labels = {
            'check_in': 'Дата заезда',
            'check_out': 'Дата выезда',
            'guests': 'Количество гостей',
            'notes': 'Примечания',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Устанавливаем минимальную дату для полей ввода
        today = date.today().isoformat()
        self.fields['check_in'].widget.attrs['min'] = today
        self.fields['check_out'].widget.attrs['min'] = today

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        room = cleaned_data.get('room')
        guests = cleaned_data.get('guests')

        if check_in and check_out:
            if check_in >= check_out:
                raise ValidationError('Дата выезда должна быть позже даты заезда')

            if check_in < date.today():
                raise ValidationError('Нельзя бронировать на прошедшую дату')

            # Проверка доступности номера
            if room:
                overlapping_bookings = Booking.objects.filter(
                    room=room,
                    status__in=['pending', 'confirmed'],
                    check_in__lt=check_out,
                    check_out__gt=check_in
                ).exclude(id=self.instance.id if self.instance.id else None)

                if overlapping_bookings.exists():
                    raise ValidationError(
                        f'Номер "{room.name}" уже занят на выбранные даты. '
                        f'Пожалуйста, выберите другие даты или другой номер.'
                    )

                # Проверка вместимости
                if guests and guests > room.capacity:
                    raise ValidationError(
                        f'В номере "{room.name}" максимальная вместимость: {room.capacity} человека(ей)'
                    )

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.user = self.user
        booking.room_type = booking.room.type if booking.room else 'standard'

        if commit:
            booking.save()
        return booking