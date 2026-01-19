from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Count, Sum

# Импорт из datetime
from datetime import date, timedelta, datetime
import json

# Импорт из других модулей проекта
from .forms import GuestRegistrationForm, BookingForm, GuestProfileForm
from .models import Booking, Room, GuestProfile

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt


# ГЛАВНАЯ СТРАНИЦА (публичная)
def home(request):
    """Главная страница - информационная для всех."""
    rooms = Room.objects.filter(is_active=True).order_by('?')[:6]  # 6 случайных номеров
    return render(request, 'home.html', {'rooms': rooms})


# ЛИЧНЫЙ КАБИНЕТ
@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
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


# КАТАЛОГ НОМЕРОВ
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


# АУТЕНТИФИКАЦИЯ
class SignUpView(CreateView):
    form_class = GuestRegistrationForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'


# БРОНИРОВАНИЕ
class BookingCreateView(LoginRequiredMixin, CreateView):
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
        return reverse_lazy('booking_list')


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('room').order_by('-created_at')


# ОТМЕНА БРОНИРОВАНИЯ
@require_POST
@login_required
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

    return redirect('booking_list')


# ПРОСМОТР ПРОФИЛЯ
@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
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


# РЕДАКТИРОВАНИЕ ПРОФИЛЯ
@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = GuestProfile
    form_class = GuestProfileForm
    template_name = 'profile_edit.html'

    def get_object(self):
        return get_object_or_404(GuestProfile, user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return reverse_lazy('dashboard')

    def form_valid(self, form):
        # Пересчитываем процент заполнения
        profile = form.save(commit=False)
        profile.calculate_profile_completion()
        profile.save()
        return super().form_valid(form)


# ПРОЦЕДУРЫ
@method_decorator(login_required, name='dispatch')
class ProceduresView(TemplateView):
    template_name = 'procedures.html'


# API ФУНКЦИИ
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


@csrf_exempt  # Временно отключаем CSRF для API (для тестов)
@require_POST
@login_required
def api_create_booking(request):
    """API для создания бронирования через AJAX"""
    try:
        data = json.loads(request.body)

        # Проверяем обязательные поля
        required_fields = ['room_id', 'check_in', 'check_out', 'guests']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Отсутствует поле: {field}'
                }, status=400)

        # Получаем данные
        room = Room.objects.get(id=data['room_id'], is_active=True)
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        guests = int(data['guests'])
        notes = data.get('notes', '')

        # Проверяем доступность
        overlapping = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in
        ).exists()

        if overlapping:
            return JsonResponse({
                'success': False,
                'error': 'Номер занят на выбранные даты'
            }, status=400)

        # Проверяем вместимость
        if guests > room.capacity:
            return JsonResponse({
                'success': False,
                'error': f'В номере максимальная вместимость: {room.capacity} человека'
            }, status=400)

        # Создаем бронирование
        booking = Booking.objects.create(
            user=request.user,
            room=room,
            room_type=room.type,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            notes=notes,
            status='pending'
        )

        # Сохраняем для расчета цены
        booking.save()

        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'message': 'Бронирование успешно создано',
            'booking': {
                'id': booking.id,
                'room': room.name,
                'check_in': booking.check_in.isoformat(),
                'check_out': booking.check_out.isoformat(),
                'guests': booking.guests,
                'total_price': float(booking.total_price),
                'status': booking.status
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
    except Room.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Номер не найден'
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Неверные данные: {str(e)}'
        }, status=400)


@require_GET
@login_required
def check_availability(request):
    """AJAX проверка доступности (альтернатива для простой формы)"""
    room_id = request.GET.get('room_id')
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')

    if not all([room_id, check_in_str, check_out_str]):
        return JsonResponse({'available': False, 'error': 'Недостаточно данных'})

    try:
        room = Room.objects.get(id=room_id, is_active=True)
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

        # Проверяем доступность
        overlapping = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in
        ).exists()

        # Расчет стоимости
        days = (check_out - check_in).days
        total_price = room.price_per_day * days if days > 0 else 0

        return JsonResponse({
            'available': not overlapping,
            'room_id': room.id,
            'room_name': room.name,
            'check_in': check_in_str,
            'check_out': check_out_str,
            'days': days,
            'price_per_day': float(room.price_per_day),
            'total_price': float(total_price),
            'message': 'Доступен' if not overlapping else 'Занят'
        })

    except (Room.DoesNotExist, ValueError):
        return JsonResponse({'available': False, 'error': 'Ошибка данных'})


# ОБРАБОТЧИКИ ОШИБОК
def handler403(request, exception):
    return render(request, '403.html', status=403)


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)