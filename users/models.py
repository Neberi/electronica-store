from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким email уже существует.')
        }
    )
    secret_question = models.CharField(
        _('Секретный вопрос'),
        max_length=200,
        help_text=_('Вопрос для восстановления пароля')
    )
    secret_answer = models.CharField(
        _('Ответ на секретный вопрос'),
        max_length=200,
        help_text=_('Ответ для восстановления пароля')
    )

    # Решаем конфликт с reverse accessor
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='customuser_set',
        related_query_name='customuser',
    )

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'secret_question', 'secret_answer']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['date_joined']

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        if not self.email:
            raise ValidationError(_('Email обязателен.'))

        # Проверка уникальности email
        if CustomUser.objects.filter(email=self.email).exclude(id=self.id).exists():
            raise ValidationError({'email': _('Пользователь с таким email уже существует.')})

        # Проверка уникальности username
        if CustomUser.objects.filter(username=self.username).exclude(id=self.id).exists():
            raise ValidationError({'username': _('Пользователь с таким именем уже существует.')})

    def save(self, *args, **kwargs):
        # Нормализуем email
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)