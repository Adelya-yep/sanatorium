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


class ProcedureCategory(models.Model):
    """Категория процедур"""
    name = models.CharField(max_length=100, verbose_name='Название категории')
    description = models.TextField(max_length=500, verbose_name='Описание')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка')

    class Meta:
        verbose_name = 'Категория процедур'
        verbose_name_plural = 'Категории процедур'

    def __str__(self):
        return self.name


class Procedure(models.Model):
    """Процедура/услуга санатория"""
    name = models.CharField(max_length=200, verbose_name='Название процедуры')
    category = models.ForeignKey(ProcedureCategory, on_delete=models.CASCADE,
                                 verbose_name='Категория', related_name='procedures')
    description = models.TextField(max_length=1000, verbose_name='Описание')
    duration = models.PositiveIntegerField(verbose_name='Длительность (минут)')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Стоимость')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    contraindications = models.TextField(max_length=500, blank=True,
                                         verbose_name='Противопоказания')
    preparation = models.TextField(max_length=500, blank=True,
                                   verbose_name='Подготовка к процедуре')

    class Meta:
        verbose_name = 'Процедура'
        verbose_name_plural = 'Процедуры'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class Doctor(models.Model):
    """Врач/специалист"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    specialization = models.CharField(max_length=200, verbose_name='Специализация')
    qualification = models.CharField(max_length=200, verbose_name='Квалификация')
    experience = models.PositiveIntegerField(verbose_name='Стаж (лет)')
    bio = models.TextField(max_length=1000, blank=True, verbose_name='Биография')
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True, verbose_name='Фото')
    procedures = models.ManyToManyField(Procedure, verbose_name='Проводимые процедуры')

    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialization}"


class ScheduleSlot(models.Model):
    """Слот расписания врача"""
    DAY_CHOICES = [
        ('mon', 'Понедельник'),
        ('tue', 'Вторник'),
        ('wed', 'Среда'),
        ('thu', 'Четверг'),
        ('fri', 'Пятница'),
        ('sat', 'Суббота'),
        ('sun', 'Воскресенье'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE,
                               verbose_name='Врач', related_name='schedule_slots')
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    max_appointments = models.PositiveIntegerField(default=1, verbose_name='Максимум записей')

    class Meta:
        verbose_name = 'Слот расписания'
        verbose_name_plural = 'Слоты расписания'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """Запись на процедуру"""
    STATUS_CHOICES = [
        ('scheduled', 'Запланирована'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена'),
        ('no_show', 'Не явился'),
    ]

    patient = models.ForeignKey(GuestProfile, on_delete=models.CASCADE,
                                verbose_name='Пациент', related_name='appointments')
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE,
                                  verbose_name='Процедура')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE,
                               verbose_name='Врач', related_name='appointments')
    schedule_slot = models.ForeignKey(ScheduleSlot, on_delete=models.CASCADE,
                                      verbose_name='Временной слот')
    appointment_date = models.DateField(verbose_name='Дата приема')
    appointment_time = models.TimeField(verbose_name='Время приема')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='scheduled', verbose_name='Статус')
    notes = models.TextField(max_length=500, blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Запись на процедуру'
        verbose_name_plural = 'Записи на процедуры'
        ordering = ['appointment_date', 'appointment_time']

    def __str__(self):
        return f"{self.patient} - {self.procedure} ({self.appointment_date})"


class MedicalRecord(models.Model):
    """Медицинская карта пребывания"""
    patient = models.ForeignKey(GuestProfile, on_delete=models.CASCADE,
                                verbose_name='Пациент', related_name='medical_records')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                verbose_name='Бронирование', related_name='medical_records')
    admission_date = models.DateField(verbose_name='Дата поступления')
    discharge_date = models.DateField(verbose_name='Дата выписки', null=True, blank=True)
    diagnosis = models.TextField(max_length=1000, verbose_name='Диагноз')
    treatment_plan = models.TextField(max_length=2000, verbose_name='План лечения')
    recommendations = models.TextField(max_length=1000, blank=True, verbose_name='Рекомендации')
    attending_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL,
                                         null=True, verbose_name='Лечащий врач')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Медицинская карта'
        verbose_name_plural = 'Медицинские карты'

    def __str__(self):
        return f"Карта: {self.patient} ({self.admission_date})"


class TreatmentEntry(models.Model):
    """Запись о проведенной процедуре в карте"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE,
                                       verbose_name='Медицинская карта',
                                       related_name='treatment_entries')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE,
                                    verbose_name='Запись на процедуру')
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выполнения')
    result = models.TextField(max_length=500, verbose_name='Результат/наблюдения')
    doctor_notes = models.TextField(max_length=500, blank=True, verbose_name='Заметки врача')
    next_date = models.DateField(null=True, blank=True, verbose_name='Следующая дата')

    class Meta:
        verbose_name = 'Запись о лечении'
        verbose_name_plural = 'Записи о лечении'
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.appointment.procedure} - {self.performed_at.date()}"