from django.urls import path
from . import views
from .views import RoomListView  # Добавьте этот импорт

urlpatterns = [
    # Аутентификация
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('dashboard/', views.HomeView.as_view(), name='home'),

    # Каталог номеров (ДОБАВЬТЕ ЭТУ СТРОКУ)
    path('rooms/', RoomListView.as_view(), name='rooms'),

    # Бронирование
    path('booking/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/list/', views.BookingListView.as_view(), name='booking_list'),

    # Заглушки
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('procedures/', views.ProceduresView.as_view(), name='procedures'),
]