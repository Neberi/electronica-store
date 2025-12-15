# main/admin_utils.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def superuser_required(view_func):
    """
    Декоратор для проверки, что пользователь является суперпользователем
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Для доступа к админ-панели необходимо войти в систему.')
            return redirect('users:login')

        if not request.user.is_superuser:
            messages.error(request, 'Доступ запрещен. Требуются права суперпользователя.')
            return redirect('main:index')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


class AdminContextMixin:
    """
    Миксин для добавления стандартного контекста в админ-панель
    """

    def get_admin_context(self, **kwargs):
        context = {
            'page_title': 'Админ-панель',
            'active_section': 'dashboard',
            'is_superuser': True,
            **kwargs
        }
        return context