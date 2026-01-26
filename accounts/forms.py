from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GuestProfile, Booking, Room
from django.core.exceptions import ValidationError
from datetime import date
import re


class GuestRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    middle_name = forms.CharField(max_length=30, required=False, label='Отчество')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    birth_date = forms.DateField(
        required=True,
        label='Дата рождения',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Формат: ДД.ММ.ГГГГ'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'middle_name',
                  'phone', 'birth_date', 'password1', 'password2']
        labels = {
            'username': 'Логин',
        }

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
                middle_name=self.cleaned_data.get('middle_name', ''),
                phone=self.cleaned_data['phone'],
                birth_date=self.cleaned_data['birth_date'],
                email=self.cleaned_data['email']
            )
        return user


class GuestProfileForm(forms.ModelForm):
    class Meta:
        model = GuestProfile
        exclude = ['user', 'created_at', 'updated_at', 'is_profile_complete']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'chronic_diseases': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'drug_intolerance': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'contraindications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'passport_issued_by': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
        labels = {
            'middle_name': 'Отчество',
            'birth_date': 'Дата рождения',
            'gender': 'Пол',
            'phone': 'Телефон',
            'email': 'Email',
            'address': 'Адрес проживания',
            'passport_series': 'Серия паспорта',
            'passport_number': 'Номер паспорта',
            'passport_issued_by': 'Кем выдан',
            'passport_issue_date': 'Дата выдачи',
            'snils': 'СНИЛС',
            'oms_policy': 'Полис ОМС',
            'medical_book_number': 'Номер медицинской книжки',
            'blood_type': 'Группа крови',
            'chronic_diseases': 'Хронические заболевания',
            'allergies': 'Аллергии',
            'drug_intolerance': 'Лекарственная непереносимость',
            'contraindications': 'Противопоказания к процедурам',
            'preferred_diet': 'Предпочитаемое питание',
            'special_requests': 'Особые пожелания',
            'need_transfer': 'Нужен трансфер',
            'emergency_contact': 'Контакт для экстренной связи',
            'emergency_phone': 'Телефон экстренной связи',
        }
        help_texts = {
            'snils': 'Формат: XXX-XXX-XXX XX',
            'oms_policy': '16 цифр',
        }

    def clean_snils(self):
        snils = self.cleaned_data.get('snils', '')
        if snils:
            # Простая валидация СНИЛС
            snils = re.sub(r'\D', '', snils)
            if len(snils) != 11:
                raise forms.ValidationError('СНИЛС должен содержать 11 цифр')
        return snils

    def clean_oms_policy(self):
        oms = self.cleaned_data.get('oms_policy', '')
        if oms:
            oms = re.sub(r'\D', '', oms)
            if len(oms) != 16:
                raise forms.ValidationError('Полис ОМС должен содержать 16 цифр')
        return oms

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


# Добавьте эти формы в конец forms.py

class AdminCreateUserForm(UserCreationForm):
    """Форма для создания пользователя администратором"""
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
            # Создаем профиль гостя
            GuestProfile.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=self.cleaned_data['phone'],
                email=user.email
            )
        return user