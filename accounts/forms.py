from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking
class GuestRegistrationForm(UserCreationForm):
    """
    Форма регистрации гостя санатория с полным профилем.
    """
    first_name = forms.CharField(
        max_length=30,
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Иван',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Иванов',
            'autocomplete': 'family-name'
        })
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'ivanov@mail.ru',
            'autocomplete': 'email'
        })
    )
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        help_text='Например: +7 (999) 123-45-67',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': '+7 (999) 123-45-67',
            'autocomplete': 'tel'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-input',
                'autocomplete': 'username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control form-input',
                'autocomplete': 'new-password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control form-input',
                'autocomplete': 'new-password'
            }),
        }

    def save(self, commit=True):
        """Сохраняет User. GuestProfile создаётся через signals."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()  # Signals сработает автоматически
        return user




class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room_type', 'check_in', 'check_out', 'guests', 'notes']
        widgets = {
            'room_type': forms.Select(attrs={'class': 'form-select form-input'}),
            'check_in': forms.DateInput(attrs={
                'class': 'form-control form-input',
                'type': 'date'
            }),
            'check_out': forms.DateInput(attrs={
                'class': 'form-control form-input',
                'type': 'date'
            }),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control form-input',
                'min': '1', 'max': '4'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-input',
                'rows': 3,
                'placeholder': 'Особые пожелания...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        booking = super().save(commit=False)
        if self.user:
            booking.user = self.user
        if commit:
            booking.save()
        return booking

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out and check_in >= check_out:
            raise forms.ValidationError('Дата выезда должна быть позже заезда')

        return cleaned_data





class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room_type', 'check_in', 'check_out', 'guests', 'notes']
        widgets = {
            'room_type': forms.Select(attrs={'class': 'form-select form-input'}),
            'check_in': forms.DateInput(attrs={'class': 'form-control form-input', 'type': 'date'}),
            'check_out': forms.DateInput(attrs={'class': 'form-control form-input', 'type': 'date'}),
            'guests': forms.NumberInput(attrs={'class': 'form-control form-input', 'min': 1, 'max': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-input', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.user = self.user
        if commit:
            booking.save()
        return booking
