from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    SignUpView,
    AdminDashboardView, UserDashboardView, AdminCreateUserView, AdminUserProfileView,
    ProfileView, ProceduresView,
    BookingCreateView, UserBookingListView, AdminBookingListView,
    RoomListView, AdminRoomListView, AdminUserListView,
    ProfileUpdateView, booking_cancel, admin_change_booking_status,
    api_room_availability, api_room_busy_dates,
    admin_toggle_user_active, admin_delete_user,
    redirect_based_on_role,
    ProcedureListView,
    AppointmentCreateView,
    PatientAppointmentsView,
    MedicalRecordView,
    AdminProcedureListView,
    AdminDoctorsListView,
    AdminAppointmentsListView,
    AdminMedicalRecordsView,
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
    path('admin/users/<int:user_id>/toggle-active/', admin_toggle_user_active, name='admin_toggle_user_active'),
    path('admin/users/<int:user_id>/delete/', admin_delete_user, name='admin_delete_user'),
    path('admin/users/<int:pk>/profile/', AdminUserProfileView.as_view(), name='admin_user_profile'),

    path('admin/users/create/', AdminCreateUserView.as_view(), name='admin_user_create'),
    # Профиль (только для пользователей)
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),

    # Процедуры (только для пользователей)
    path('procedures/', ProcedureListView.as_view(), name='procedures_list'),
    path('procedures/appointment/create/', AppointmentCreateView.as_view(), name='appointment_create'),
    path('procedures/my-appointments/', PatientAppointmentsView.as_view(), name='patient_appointments'),
    path('procedures/medical-record/', MedicalRecordView.as_view(), name='patient_medical_record'),
    # Для админов
    path('admin/procedures/', AdminProcedureListView.as_view(), name='admin_procedures'),
    path('admin/procedures/doctors/', AdminDoctorsListView.as_view(), name='admin_doctors'),
    path('admin/procedures/appointments/', AdminAppointmentsListView.as_view(), name='admin_appointments'),
    path('admin/procedures/medical-records/', AdminMedicalRecordsView.as_view(), name='admin_medical_records'),

    # API endpoints
    path('api/room/availability/', api_room_availability, name='api_room_availability'),
    path('api/room/<int:room_id>/busy-dates/', api_room_busy_dates, name='api_room_busy_dates'),

]