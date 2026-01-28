# accounts/models_encrypted.py
from django.db import models
from django.contrib.auth.models import User
from .encryption import EncryptionService
import json


class EncryptedDocument(models.Model):
    """Модель для хранения зашифрованных документов"""

    DOCUMENT_TYPES = [
        ('passport', 'Паспорт'),
        ('snils', 'СНИЛС'),
        ('oms', 'Полис ОМС'),
        ('medical', 'Медицинская книжка'),
        ('other', 'Другое'),
    ]

    profile = models.ForeignKey('GuestProfile', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)

    # Зашифрованные поля в JSON
    encrypted_data = models.TextField(verbose_name='Зашифрованные данные')

    # Метаданные (не шифруются)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='uploaded_documents')
    verified = models.BooleanField(default=False, verbose_name='Проверено')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата проверки')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='verified_documents')

    # Дата удаления (GDPR compliance)
    delete_after = models.DateField(null=True, blank=True, verbose_name='Удалить после')

    class Meta:
        verbose_name = 'Зашифрованный документ'
        verbose_name_plural = 'Зашифрованные документы'
        ordering = ['-uploaded_at']

    def set_data(self, data_dict):
        """Шифрует и сохраняет данные"""
        json_data = json.dumps(data_dict, ensure_ascii=False)
        self.encrypted_data = EncryptionService.encrypt(json_data)

    def get_data(self):
        """Дешифрует и возвращает данные"""
        if not self.encrypted_data:
            return {}
        try:
            decrypted = EncryptionService.decrypt(self.encrypted_data)
            return json.loads(decrypted)
        except:
            return {}

    def get_masked_display(self):
        """Возвращает маскированные данные для отображения"""
        data = self.get_data()

        if self.document_type == 'passport':
            series = data.get('series', '')
            number = data.get('number', '')
            if series and number:
                return f"{series[:2]}** ****{number[-2:]}"

        elif self.document_type == 'snils':
            snils = data.get('number', '')
            if snils and len(snils) >= 4:
                return f"***-***-*** {snils[-2:]}"

        return "***"