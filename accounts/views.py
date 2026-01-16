from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator

# Импорт из datetime
from datetime import date

# Импорт из других модулей проекта
from .forms import GuestRegistrationForm, BookingForm
from .models import Booking, Room


# ГЛАВНАЯ СТРАНИЦА (публичная)
def home(request):
    """Главная страница - информационная для всех."""
    rooms = Room.objects.filter(is_active=True).order_by('?')[:6]  # 6 случайных номеров
    return render(request, 'home.html', {'rooms': rooms})


# ЛИЧНЫЙ КАБИНЕТ (только для авторизованных)
@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Активные брони (статус confirmed или pending)
        active_bookings = Booking.objects.filter(
            user=user,
            status__in=['confirmed', 'pending'],
            check_out__gte=date.today()
        ).order_by('check_in')[:5]

        # Последние бронирования
        recent_bookings = Booking.objects.filter(
            user=user
        ).order_by('-created_at')[:10]

        context.update({
            'active_bookings': active_bookings,
            'recent_bookings': recent_bookings,
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


# ПРОФИЛЬ И ПРОЦЕДУРЫ
@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Здесь можно добавить данные профиля
        return context


@method_decorator(login_required, name='dispatch')
class ProceduresView(TemplateView):
    template_name = 'procedures.html'