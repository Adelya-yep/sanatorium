from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class GuestProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


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