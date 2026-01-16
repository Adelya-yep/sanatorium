from django.contrib import admin
from django.urls import path, include  # ← Полный импорт!
from django.shortcuts import redirect  # ← Для главной
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('accounts.urls')),  # signup/dashboard/booking
    path('', lambda request: redirect('home') if request.user.is_authenticated
          else redirect('login'), name='index'),
]
