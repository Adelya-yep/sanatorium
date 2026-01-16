from django.urls import path
from . import views
from .views import (
    SignUpView, DashboardView, ProfileView, ProceduresView,
    BookingCreateView, BookingListView, RoomListView
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Главная страница (публичная) - вызываем функцию home
    path('', views.home, name='home'),

    # Личный кабинет (только для авторизованных)
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Аутентификация
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Каталог номеров
    path('rooms/', RoomListView.as_view(), name='rooms'),

    # Бронирование
    path('booking/create/', BookingCreateView.as_view(), name='booking_create'),
    path('booking/list/', BookingListView.as_view(), name='booking_list'),

    # Профиль и процедуры
    path('profile/', ProfileView.as_view(), name='profile'),
    path('procedures/', ProceduresView.as_view(), name='procedures'),
]