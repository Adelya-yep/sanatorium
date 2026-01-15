from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect  # ← Добавь импорт
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout/password_reset
    path('accounts/', include('accounts.urls')),             # signup/dashboard/...
    path('', lambda request: redirect('home') if request.user.is_authenticated else redirect('login'), name='index'),
]
