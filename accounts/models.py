from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class GuestProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]

    BLOOD_TYPE_CHOICES = [
        ('O+', 'O(I) Rh+'),
        ('O-', 'O(I) Rh-'),
        ('A+', 'A(II) Rh+'),
        ('A-', 'A(II) Rh-'),
        ('B+', 'B(III) Rh+'),
        ('B-', 'B(III) Rh-'),
        ('AB+', 'AB(IV) Rh+'),
        ('AB-', 'AB(IV) Rh-'),
    ]

    DIET_CHOICES = [
        ('standard', 'Общий стол'),
        ('dietary', 'Диетическое'),
        ('vegetarian', 'Вегетарианское'),
        ('diabetic', 'Диабетическое'),
        ('salt_free', 'Бессолевое'),
        ('gluten_free', 'Безглютеновое'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Личные данные
    first_name = models.CharField(max_length=30, verbose_name='Имя')
    last_name = models.CharField(max_length=30, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=30, blank=True, verbose_name='Отчество')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name='Пол')

    # Контактные данные
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(max_length=200, blank=True, verbose_name='Адрес проживания')

    # Документы
    passport_series = models.CharField(max_length=4, blank=True, verbose_name='Серия паспорта')
    passport_number = models.CharField(max_length=6, blank=True, verbose_name='Номер паспорта')
    passport_issued_by = models.TextField(max_length=200, blank=True, verbose_name='Кем выдан')
    passport_issue_date = models.DateField(null=True, blank=True, verbose_name='Дата выдачи')

    # Медицинские документы
    snils = models.CharField(max_length=14, blank=True, verbose_name='СНИЛС',
                             help_text='Формат: XXX-XXX-XXX XX')
    oms_policy = models.CharField(max_length=16, blank=True, verbose_name='Полис ОМС')
    medical_book_number = models.CharField(max_length=50, blank=True, verbose_name='Номер мед. книжки')

    # Медицинская информация
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True, verbose_name='Группа крови')
    chronic_diseases = models.TextField(max_length=500, blank=True, verbose_name='Хронические заболевания')
    allergies = models.TextField(max_length=500, blank=True, verbose_name='Аллергии')
    drug_intolerance = models.TextField(max_length=500, blank=True, verbose_name='Лекарственная непереносимость')
    contraindications = models.TextField(max_length=500, blank=True, verbose_name='Противопоказания к процедурам')

    # Данные для заселения
    preferred_diet = models.CharField(max_length=20, choices=DIET_CHOICES, default='standard',
                                      verbose_name='Предпочитаемое питание')
    special_requests = models.TextField(max_length=500, blank=True, verbose_name='Особые пожелания')
    need_transfer = models.BooleanField(default=False, verbose_name='Нужен трансфер')
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name='Контакт для экстренной связи')
    emergency_phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон экстренной связи')

    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_profile_complete = models.BooleanField(default=False, verbose_name='Профиль заполнен')

    class Meta:
        verbose_name = 'Профиль пациента'
        verbose_name_plural = 'Профили пациентов'

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                    (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    def calculate_profile_completion(self):
        """Рассчитывает процент заполнения профиля"""
        required_fields = ['first_name', 'last_name', 'phone', 'email',
                           'birth_date', 'passport_series', 'passport_number',
                           'snils', 'oms_policy']

        filled = 0
        for field in required_fields:
            value = getattr(self, field)
            if value and str(value).strip():
                filled += 1

        percentage = (filled / len(required_fields)) * 100
        self.is_profile_complete = percentage >= 70
        return percentage

class Room(models.Model):  # ПЕРЕМЕЩАЕМ Room ПЕРЕД Booking!
    """
    Номер санатория для каталога и бронирования.
    """
    TYPE_CHOICES = [
        ('standard', 'Стандартный'),
        ('comfort', 'Комфорт'),
        ('lux', 'Люкс'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField(default=2)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(max_length=500)
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Номер'
        verbose_name_plural = 'Номера'
        ordering = ['type', 'name']

    def __str__(self):
        return self.name

    @property
    def price_range(self):
        """Диапазон цен за номер."""
        return f"{self.price_per_day} ₽/сутки"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('cancelled', 'Отменена'),
        ('completed', 'Завершена'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    room_type = models.CharField(max_length=20, choices=Room.TYPE_CHOICES)  # Оставляем для обратной совместимости
    check_in = models.DateField('Дата заезда')
    check_out = models.DateField('Дата выезда')
    guests = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        if self.room:
            return f"{self.user.username}: {self.room.name}"
        return f"{self.user.username}: {self.get_room_type_display()}"

    @property
    def days(self):
        return (self.check_out - self.check_in).days

    def get_price_per_day(self):
        if self.room:
            return self.room.price_per_day
        # Запасной вариант для старых броней
        prices = {
            'standard': 5000,
            'comfort': 8000,
            'lux': 12000,
        }
        return prices.get(self.room_type, 0)

    def save(self, *args, **kwargs):
        self.total_price = self.get_price_per_day() * self.days
        super().save(*args, **kwargs)