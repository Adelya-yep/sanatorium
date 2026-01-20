from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    SignUpView,
    AdminDashboardView, UserDashboardView,
    ProfileView, ProceduresView,
    BookingCreateView, UserBookingListView, AdminBookingListView,
    RoomListView, AdminRoomListView, AdminUserListView,
    ProfileUpdateView, booking_cancel, admin_change_booking_status,
    # API функции
    api_room_availability, api_room_busy_dates,
    # Декораторы
    redirect_based_on_role
)

urlpatterns = [
    # Главная страница (публичная)
    path('', home, name='home'),

    # Dashboard в зависимости от роли
    path('dashboard/', redirect_based_on_role(UserDashboardView.as_view()), name='dashboard'),
    path('user/dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

    # Аутентификация
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Каталог номеров (публичный)
    path('rooms/', RoomListView.as_view(), name='rooms'),

    # Бронирование (только для пользователей)
    path('booking/create/', BookingCreateView.as_view(), name='booking_create'),
    path('booking/list/', UserBookingListView.as_view(), name='user_booking_list'),
    path('booking/cancel/', booking_cancel, name='booking_cancel'),

    # Админ: управление бронированиями
    path('admin/bookings/', AdminBookingListView.as_view(), name='admin_booking_list'),
    path('admin/bookings/change-status/', admin_change_booking_status, name='admin_change_booking_status'),

    # Админ: управление номерами
    path('admin/rooms/', AdminRoomListView.as_view(), name='admin_room_list'),

    # Админ: управление пользователями
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),

    # Профиль (только для пользователей)
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),

    # Процедуры (только для пользователей)
    path('procedures/', ProceduresView.as_view(), name='procedures'),

    # API endpoints
    path('api/room/availability/', api_room_availability, name='api_room_availability'),
    path('api/room/<int:room_id>/busy-dates/', api_room_busy_dates, name='api_room_busy_dates'),
]