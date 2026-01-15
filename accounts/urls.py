from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),     # /accounts/signup/
    path('dashboard/', views.HomeView.as_view(), name='home'),      # /accounts/dashboard/
    path('booking/', views.BookingView.as_view(), name='booking'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('procedures/', views.ProceduresView.as_view(), name='procedures'),
]
