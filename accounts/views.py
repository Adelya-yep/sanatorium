from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.db.models import Count, Sum

# Импорт из datetime - ДОБАВЬТЕ timedelta
from datetime import date, timedelta

# Импорт из других модулей проекта
from .forms import GuestRegistrationForm, BookingForm, GuestProfileForm
from .models import Booking, Room, GuestProfile


# ГЛАВНАЯ СТРАНИЦА (публичная)
def home(request):
    """Главная страница - информационная для всех."""
    rooms = Room.objects.filter(is_active=True).order_by('?')[:6]  # 6 случайных номеров
    return render(request, 'home.html', {'rooms': rooms})


# ЛИЧНЫЙ КАБИНЕТ - обновленная версия
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
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request,
                         f'Бронь "{form.instance}" создана! Ожидает подтверждения.')
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
        ).select_related('user').order_by('-created_at')


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

@method_decorator(login_required, name='dispatch')
class ProceduresView(TemplateView):
    template_name = 'procedures.html'