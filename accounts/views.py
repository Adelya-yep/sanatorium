from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import GuestRegistrationForm  # Импорт
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .forms import BookingForm
from .models import Booking, GuestProfile
from django.shortcuts import render
from accounts.models import Room

class SignUpView(CreateView):
    form_class = GuestRegistrationForm  # Замена!
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

class BookingView(LoginRequiredMixin, TemplateView):
    template_name = 'booking.html'

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

class ProceduresView(LoginRequiredMixin, TemplateView):
    template_name = 'procedures.html'


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

def home(request):
    """Главная страница (анонимная, информационная)."""
    rooms = Room.objects.filter(is_available=True)[:6]  # Топ-6 номеров
    return render(request, 'home.html', {'rooms': rooms})


def landing(request):
    """Главная страница — каталог номеров (для всех)."""
    rooms = Room.objects.filter(is_active=True).order_by('type', 'name')
    featured_rooms = rooms.filter(type='lux')[:3]

    context = {
        'rooms': rooms,
        'featured_rooms': featured_rooms,
    }
    return render(request, 'landing.html', context)