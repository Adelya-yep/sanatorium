# accounts/encryption.py
class EncryptionService:
    """Простой сервис шифрования для тестирования"""

    @staticmethod
    def encrypt(data):
        """Заглушка для шифрования"""
        return f"ENCRYPTED:{data}" if data else None

    @staticmethod
    def decrypt(encrypted_data):
        """Заглушка для дешифрования"""
        if encrypted_data and encrypted_data.startswith("ENCRYPTED:"):
            return encrypted_data[10:]
        return encrypted_data