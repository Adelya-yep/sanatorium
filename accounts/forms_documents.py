# accounts/forms_documents.py
from django import forms
import re


class DocumentUploadForm(forms.Form):
    """Упрощенная форма загрузки документов"""

    DOCUMENT_TYPES = [
        ('passport', 'Паспорт'),
        ('snils', 'СНИЛС'),
        ('oms', 'Полис ОМС'),
        ('medical', 'Медицинская книжка'),
    ]

    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPES,
        label='Тип документа',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Для паспорта
    passport_series = forms.CharField(
        max_length=4,
        required=False,
        label='Серия паспорта',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234'
        })
    )

    passport_number = forms.CharField(
        max_length=6,
        required=False,
        label='Номер паспорта',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '567890'
        })
    )

    # Для СНИЛС
    snils_number = forms.CharField(
        max_length=14,
        required=False,
        label='СНИЛС',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123-456-789 00'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        doc_type = cleaned_data.get('document_type')

        if doc_type == 'passport':
            series = cleaned_data.get('passport_series', '').strip()
            number = cleaned_data.get('passport_number', '').strip()

            if not series or not number:
                raise forms.ValidationError('Для паспорта необходимо указать серию и номер')

            if not re.match(r'^\d{4}$', series):
                raise forms.ValidationError('Серия паспорта должна содержать 4 цифры')

            if not re.match(r'^\d{6}$', number):
                raise forms.ValidationError('Номер паспорта должен содержать 6 цифр')

        elif doc_type == 'snils':
            snils = cleaned_data.get('snils_number', '').replace('-', '').replace(' ', '')
            if snils and not re.match(r'^\d{11}$', snils):
                raise forms.ValidationError('СНИЛС должен содержать 11 цифр')
            cleaned_data['snils_number'] = snils

        return cleaned_data