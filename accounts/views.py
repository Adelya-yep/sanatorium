from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Count, Sum, Avg, Q, Max  # Добавить Avg и Q

# Импорт из datetime
from datetime import date, timedelta, datetime
import json

# Импорт из других модулей проекта
from .forms import GuestRegistrationForm, BookingForm, GuestProfileForm
from .models import Booking, Room, GuestProfile

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
# Добавьте этот импорт в начало views.py, после других импортов
from .mixins import StaffRequiredMixin, NotStaffMixin

# ГЛАВНАЯ СТРАНИЦА (публичная)
def home(request):
    """Главная страница - информационная для всех."""
    rooms = Room.objects.filter(is_active=True).order_by('?')[:6]  # 6 случайных номеров
    return render(request, 'home.html', {'rooms': rooms})


# АДМИН ПАНЕЛЬ
@method_decorator(login_required, name='dispatch')
class AdminDashboardView(StaffRequiredMixin, TemplateView):
    """Панель администратора (только для персонала)"""
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика для админа
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        active_bookings = Booking.objects.filter(status='confirmed').count()
        total_guests = GuestProfile.objects.count()
        total_rooms = Room.objects.count()

        # Последние бронирования
        recent_bookings = Booking.objects.select_related('user', 'room').order_by('-created_at')[:10]

        # Статистика по доходам
        revenue_data = Booking.objects.filter(
            status='completed'
        ).aggregate(
            total_revenue=Sum('total_price'),
            avg_booking=Avg('total_price'),
            max_booking=Max('total_price')
        )

        context.update({
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'active_bookings': active_bookings,
            'total_guests': total_guests,
            'total_rooms': total_rooms,
            'recent_bookings': recent_bookings,
            'revenue': revenue_data['total_revenue'] or 0,
            'avg_revenue': revenue_data['avg_booking'] or 0,
        })
        return context


# ЛИЧНЫЙ КАБИНЕТ ПОЛЬЗОВАТЕЛЯ (НЕ для админов)
@method_decorator(login_required, name='dispatch')
class UserDashboardView(NotStaffMixin, TemplateView):
    """Личный кабинет пользователя (не для администраторов)"""
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Получаем или создаем профиль
        profile, created = GuestProfile.objects.get_or_create(user=user)

        # Активные брони
        active_bookings = Booking.objects.filter(
            user=user,
            status__in=['confirmed', 'pending'],
            check_out__gte=date.today()
        ).select_related('room').order_by('check_in')[:5]

        # Предстоящие брони (ближайшие 30 дней)
        upcoming_bookings = Booking.objects.filter(
            user=user,
            status='confirmed',
            check_in__gte=date.today(),
            check_in__lte=date.today() + timedelta(days=30)
        ).select_related('room').order_by('check_in')[:3]

        # Статистика
        total_bookings = Booking.objects.filter(user=user).count()
        completed_bookings = Booking.objects.filter(user=user, status='completed').count()
        total_spent = Booking.objects.filter(
            user=user,
            status='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # Процент заполнения профиля
        profile_completion = profile.calculate_profile_completion()

        context.update({
            'profile': profile,
            'active_bookings': active_bookings,
            'upcoming_bookings': upcoming_bookings,
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'total_spent': total_spent,
            'profile_completion': profile_completion,
        })
        return context


# КАТАЛОГ НОМЕРОВ (доступен всем)
class RoomListView(ListView):
    model = Room
    template_name = 'catalog/rooms.html'
    context_object_name = 'rooms'
    paginate_by = 6

    def get_queryset(self):
        queryset = Room.objects.filter(is_active=True)

        # Фильтр по типу
        room_type = self.request.GET.get('type')
        if room_type:
            queryset = queryset.filter(type=room_type)

        # Фильтр по вместимости
        capacity = self.request.GET.get('capacity')
        if capacity:
            if capacity == '4':
                queryset = queryset.filter(capacity__gte=4)
            else:
                queryset = queryset.filter(capacity=capacity)

        # Фильтр по максимальной цене
        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price_per_day__lte=float(max_price))
            except ValueError:
                pass

        return queryset.order_by('type', 'price_per_day')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем параметры фильтров в контекст для пагинации
        context['filter_params'] = self.request.GET.copy()
        if 'page' in context['filter_params']:
            del context['filter_params']['page']
        return context


# УПРАВЛЕНИЕ БРОНИРОВАНИЯМИ (админ)
@method_decorator(login_required, name='dispatch')
class AdminBookingListView(StaffRequiredMixin, ListView):
    """Список всех бронирований (только для админа)"""
    model = Booking
    template_name = 'admin/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20

    def get_queryset(self):
        queryset = Booking.objects.select_related('user', 'room').order_by('-created_at')

        # Фильтры
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        room_type = self.request.GET.get('room_type')
        if room_type:
            queryset = queryset.filter(room__type=room_type)

        date_from = self.request.GET.get('date_from')
        if date_from:
            try:
                queryset = queryset.filter(check_in__gte=date_from)
            except ValueError:
                pass

        date_to = self.request.GET.get('date_to')
        if date_to:
            try:
                queryset = queryset.filter(check_out__lte=date_to)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Booking.STATUS_CHOICES
        context['room_types'] = Room.TYPE_CHOICES
        return context


# АДМИН: УПРАВЛЕНИЕ НОМЕРАМИ
@method_decorator(login_required, name='dispatch')
class AdminRoomListView(StaffRequiredMixin, ListView):
    """Управление номерами (только для админа)"""
    model = Room
    template_name = 'admin/room_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.all().order_by('type', 'name')


# АДМИН: ИЗМЕНЕНИЕ СТАТУСА БРОНИРОВАНИЯ
@require_POST
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_change_booking_status(request):
    """Изменение статуса бронирования (только для админа)"""
    booking_id = request.POST.get('booking_id')
    new_status = request.POST.get('status')

    try:
        booking = Booking.objects.get(id=booking_id)
        old_status = booking.status
        booking.status = new_status
        booking.save()

        messages.success(request, f'Статус бронирования #{booking_id} изменен: {old_status} → {new_status}')
    except Booking.DoesNotExist:
        messages.error(request, 'Бронирование не найдено')

    return redirect('admin_booking_list')


# АДМИН: УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
@method_decorator(login_required, name='dispatch')
class AdminUserListView(StaffRequiredMixin, ListView):
    """Список пользователей (только для админа)"""
    template_name = 'admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')


# АУТЕНТИФИКАЦИЯ (доступна всем)
class SignUpView(CreateView):
    form_class = GuestRegistrationForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'


# БРОНИРОВАНИЕ (только для обычных пользователей)
@method_decorator(login_required, name='dispatch')
class BookingCreateView(NotStaffMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking_form.html'

    def get_form_kwargs(self):
        """Передаем пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        """Предзаполняем форму, если передан room_id в URL."""
        initial = super().get_initial()
        room_id = self.request.GET.get('room_id')
        if room_id:
            try:
                room = Room.objects.get(id=room_id, is_active=True)
                initial['room'] = room
            except Room.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Бронирование создано! Ожидает подтверждения.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('user_booking_list')


# СПИСОК БРОНИРОВАНИЙ ПОЛЬЗОВАТЕЛЯ (не для админов)
@method_decorator(login_required, name='dispatch')
class UserBookingListView(NotStaffMixin, ListView):
    model = Booking
    template_name = 'booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('room').order_by('-created_at')


# ОТМЕНА БРОНИРОВАНИЯ (только пользователи)
@require_POST
@login_required
@user_passes_test(lambda u: not u.is_staff)
def booking_cancel(request):
    booking_id = request.POST.get('booking_id')
    reason = request.POST.get('reason', '')

    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)

        # Можно отменять только ожидающие подтверждения брони
        if booking.status == 'pending':
            booking.status = 'cancelled'
            booking.notes = f"{booking.notes}\n\nОтменено пользователем. Причина: {reason}".strip()
            booking.save()

            messages.success(request, 'Бронирование успешно отменено.')
        else:
            messages.error(request, 'Можно отменять только брони, ожидающие подтверждения.')

    except Booking.DoesNotExist:
        messages.error(request, 'Бронирование не найдено.')

    return redirect('user_booking_list')


# ПРОСМОТР ПРОФИЛЯ (только пользователи)
@method_decorator(login_required, name='dispatch')
class ProfileView(NotStaffMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        profile = get_object_or_404(GuestProfile, user=user)
        profile_completion = profile.calculate_profile_completion()

        context.update({
            'profile': profile,
            'profile_completion': profile_completion,
        })
        return context


# РЕДАКТИРОВАНИЕ ПРОФИЛЯ (только пользователи)
@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(NotStaffMixin, UpdateView):
    model = GuestProfile
    form_class = GuestProfileForm
    template_name = 'profile_edit.html'

    def get_object(self):
        return get_object_or_404(GuestProfile, user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return reverse_lazy('user_dashboard')

    def form_valid(self, form):
        # Пересчитываем процент заполнения
        profile = form.save(commit=False)
        profile.calculate_profile_completion()
        profile.save()
        return super().form_valid(form)


# ПРОЦЕДУРЫ (только пользователи)
@method_decorator(login_required, name='dispatch')
class ProceduresView(NotStaffMixin, TemplateView):
    template_name = 'procedures.html'


# API ФУНКЦИИ (доступны всем авторизованным)
@require_GET
@login_required
def api_room_availability(request):
    """API для проверки доступности номера"""
    room_id = request.GET.get('room_id')
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')

    if not all([room_id, check_in_str, check_out_str]):
        return JsonResponse({
            'success': False,
            'error': 'Необходимы параметры: room_id, check_in, check_out'
        }, status=400)

    try:
        # Получаем номер
        room = Room.objects.get(id=room_id, is_active=True)

        # Парсим даты
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

        # Проверяем корректность дат
        if check_in >= check_out:
            return JsonResponse({
                'success': False,
                'error': 'Дата выезда должна быть позже даты заезда'
            })

        if check_in < datetime.now().date():
            return JsonResponse({
                'success': False,
                'error': 'Нельзя бронировать на прошедшую дату'
            })

        # Проверяем доступность
        overlapping_bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in
        )

        is_available = not overlapping_bookings.exists()

        # Рассчитываем стоимость
        days = (check_out - check_in).days
        total_price = room.price_per_day * days

        # Формируем ответ
        response_data = {
            'success': True,
            'room': {
                'id': room.id,
                'name': room.name,
                'type': room.get_type_display(),
                'capacity': room.capacity
            },
            'check_in': check_in_str,
            'check_out': check_out_str,
            'days': days,
            'price_per_day': float(room.price_per_day),
            'total_price': float(total_price),
            'available': is_available,
            'message': 'Номер доступен' if is_available else 'Номер занят на выбранные даты'
        }

        return JsonResponse(response_data)

    except Room.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Номер не найден'
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Неверный формат даты: {str(e)}'
        }, status=400)


@require_GET
def api_room_busy_dates(request, room_id):
    """API для получения занятых дат номера"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)

        # Получаем бронирования на ближайшие 3 месяца
        three_months_later = datetime.now().date() + timedelta(days=90)

        bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            check_out__gte=datetime.now().date(),
            check_in__lte=three_months_later
        ).order_by('check_in')

        # Формируем список занятых периодов
        busy_periods = []
        for booking in bookings:
            busy_periods.append({
                'start': booking.check_in.isoformat(),
                'end': booking.check_out.isoformat(),
                'status': booking.status,
                'guests': booking.guests
            })

        return JsonResponse({
            'success': True,
            'room_id': room.id,
            'room_name': room.name,
            'busy_periods': busy_periods,
            'period': {
                'from': datetime.now().date().isoformat(),
                'to': three_months_later.isoformat()
            }
        })

    except Room.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Номер не найден'
        }, status=404)


# ДЕКОРАТОР ДЛЯ ПЕРЕНАПРАВЛЕНИЯ АДМИНОВ
def redirect_based_on_role(view_func):
    """Декоратор для перенаправления пользователей на нужную dashboard"""

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('admin_dashboard')
            else:
                return view_func(request, *args, **kwargs)
        return view_func(request, *args, **kwargs)

    return wrapper