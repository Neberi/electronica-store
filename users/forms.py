from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'example@email.com'
        }),
        label=_('Email адрес')
    )
    secret_question = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Например: Девичья фамилия матери?')
        }),
        help_text=_('Вопрос, на который только вы знаете ответ'),
        label=_('Секретный вопрос')
    )
    secret_answer = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Ответ на секретный вопрос')
        }),
        help_text=_('Ответ, который потребуется для восстановления пароля'),
        label=_('Ответ на вопрос')
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'secret_question', 'secret_answer', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Придумайте имя пользователя')
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError(_('Пользователь с таким именем уже существует.'))
        return username


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Введите ваше имя пользователя'),
            'autofocus': True
        }),
        label=_('Имя пользователя')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Введите ваш пароль')
        }),
        label=_('Пароль')
    )

    error_messages = {
        'invalid_login': _(
            "Пожалуйста, введите правильные имя пользователя и пароль. "
            "Оба поля могут быть чувствительны к регистру."
        ),
        'inactive': _("Этот аккаунт неактивен."),
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите email, указанный при регистрации',
            'id': 'reset-email'  # Задаем id вручную
        }),
        label='Email адрес'
    )
    secret_answer = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Сначала введите email',
            'id': 'reset-answer'  # Задаем id вручную
        }),
        label='Ответ на секретный вопрос'
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        secret_answer = cleaned_data.get('secret_answer')

        if email and secret_answer:
            email = email.strip().lower()
            try:
                user = CustomUser.objects.get(email=email)
                if user.secret_answer.lower() != secret_answer.strip().lower():
                    raise ValidationError('Неверный ответ на секретный вопрос.')
                # Сохраняем пользователя
                cleaned_data['user'] = user
            except CustomUser.DoesNotExist:
                raise ValidationError('Пользователь с таким email не найден.')

        return cleaned_data


class NewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Новый пароль (минимум 8 символов)')
        }),
        min_length=8,
        label=_('Новый пароль'),
        help_text=_('Минимум 8 символов')
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Подтверждение нового пароля')
        }),
        label=_('Подтверждение пароля')
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError(_('Пароли не совпадают.'))

        return cleaned_data