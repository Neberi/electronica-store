from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    PasswordResetForm,
    NewPasswordForm
)
from .models import CustomUser
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, _('Регистрация успешно завершена!'))
                return redirect('main:index')
            except Exception as e:
                messages.error(request, _('Ошибка при создании пользователя: %(error)s') % {'error': str(e)})
        else:
            # Показываем первую ошибку формы
            for field, errors in form.errors.items():
                if errors:
                    messages.error(request, f'{field}: {errors[0]}')
                    break
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                messages.success(request, _('Добро пожаловать, %(username)s!') % {'username': user.username})

                # Проверяем или создаем корзину для пользователя
                try:
                    from main.models import Cart
                    cart, created = Cart.objects.get_or_create(user=user)
                    if created:
                        print(f"Создана новая корзина для пользователя {user.username}")
                except Exception as e:
                    print(f"Ошибка при создании корзины: {e}")

                return redirect('main:index')
        else:
            # Показываем ошибку аутентификации
            messages.error(request, _('Неверное имя пользователя или пароль.'))
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = form.cleaned_data['user']  # Получаем пользователя из формы

            # Генерируем временный токен
            temp_token = get_random_string(length=32)
            request.session['password_reset_token'] = temp_token
            request.session['password_reset_user_id'] = user.id
            request.session['password_reset_expiry'] = 300  # 5 минут

            # Отправляем email
            reset_url = request.build_absolute_uri(
                reverse('users:password_reset_confirm', args=[temp_token])
            )

            subject = _('Восстановление пароля - Electronica Store')
            message = _('''
            Здравствуйте, %(username)s!

            Для восстановления пароля перейдите по ссылке:
            %(reset_url)s

            Ссылка действительна в течение 5 минут.

            Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.
            ''') % {'username': user.username, 'reset_url': reset_url}

            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            try:
                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )
                messages.success(request, _('Инструкции по восстановлению пароля отправлены на ваш email.'))
                return redirect('users:login')
            except Exception as e:
                messages.error(request, _('Ошибка при отправке email: %(error)s') % {'error': str(e)})
    else:
        form = PasswordResetForm()

    return render(request, 'users/password_reset.html', {'form': form})


def password_reset_confirm(request, token):
    # Проверяем токен
    if (request.session.get('password_reset_token') != token or
            not request.session.get('password_reset_user_id')):
        messages.error(request, _('Ссылка для восстановления пароля недействительна или истекла.'))
        return redirect('users:password_reset')

    user_id = request.session.get('password_reset_user_id')

    if request.method == 'POST':
        form = NewPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.get(id=user_id)
                new_password = form.cleaned_data['new_password1']
                user.set_password(new_password)
                user.save()

                # Очищаем сессию
                del request.session['password_reset_token']
                del request.session['password_reset_user_id']
                del request.session['password_reset_expiry']

                messages.success(request, _('Пароль успешно изменен. Теперь вы можете войти с новым паролем.'))
                return redirect('users:login')
            except CustomUser.DoesNotExist:
                messages.error(request, _('Пользователь не найден.'))
                return redirect('users:password_reset')
    else:
        form = NewPasswordForm()

    return render(request, 'users/password_reset_confirm.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def logout_view(request):
    """Выход из системы"""
    auth_logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('main:index')


@csrf_exempt
def get_secret_question(request):
    """AJAX-функция для получения секретного вопроса по email"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if email:
            try:
                user = CustomUser.objects.get(email=email)
                return JsonResponse({
                    'success': True,
                    'question': user.secret_question
                })
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Пользователь не найден'
                })

    return JsonResponse({'success': False, 'error': 'Неверный запрос'})