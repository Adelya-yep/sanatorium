from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    SignUpView, DashboardView, ProfileView, ProceduresView,
    BookingCreateView, BookingListView, RoomListView,
    ProfileUpdateView, booking_cancel,
    # API функции
    api_room_availability, api_room_busy_dates, api_create_booking,
    check_availability,
    # Обработчики ошибок
    handler403, handler404, handler500
)

urlpatterns = [
    # Главная страница
    path('', home, name='home'),

    # Личный кабинет
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
    path('booking/cancel/', booking_cancel, name='booking_cancel'),

    # API endpoints
    path('api/room/availability/', api_room_availability, name='api_room_availability'),
    path('api/room/<int:room_id>/busy-dates/', api_room_busy_dates, name='api_room_busy_dates'),
    path('api/booking/create/', api_create_booking, name='api_create_booking'),
    path('check_availability/', check_availability, name='check_availability'),

    # Профиль
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),

    # Процедуры
    path('procedures/', ProceduresView.as_view(), name='procedures'),
]

# Для обработки ошибок
handler403 = 'accounts.views.handler403'
handler404 = 'accounts.views.handler404'
handler500 = 'accounts.views.handler500'