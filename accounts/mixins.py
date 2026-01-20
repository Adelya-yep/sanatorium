from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class StaffRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки, что пользователь является персоналом"""

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, 'Доступ только для администраторов.')
        return redirect('home')


class NotStaffMixin(UserPassesTestMixin):
    """Миксин для проверки, что пользователь НЕ персонал"""

    def test_func(self):
        return not self.request.user.is_staff

    def handle_no_permission(self):
        messages.info(self.request, 'Эта страница недоступна для администраторов.')
        return redirect('admin_dashboard')