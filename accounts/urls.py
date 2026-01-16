from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('dashboard/', views.HomeView.as_view(), name='home'),

    # Бронирование
    path('booking/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/list/', views.BookingListView.as_view(), name='booking_list'),

    # Заглушки
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('procedures/', views.ProceduresView.as_view(), name='procedures'),
]
