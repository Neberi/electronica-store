from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('name', 'email')
        }),
        ('Сообщение', {
            'fields': ('message',)
        }),
        ('Дата', {
            'fields': ('created_at',)
        }),
    )