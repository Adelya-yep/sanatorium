from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth.views import LoginView, LogoutView

class SignUpView(CreateView):
    form_class = UserCreationForm
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
