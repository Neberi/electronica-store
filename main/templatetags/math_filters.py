# electronica_store/main/templatetags/math_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножение value на arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        try:
            return value * arg
        except Exception:
            return value

@register.filter
def divide(value, arg):
    """Деление value на arg"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Получение элемента из словаря по ключу"""
    try:
        return dictionary.get(key, 0)
    except AttributeError:
        return 0

@register.filter
def floatformat(value, decimal_places=0):
    """Форматирование числа с указанным количеством знаков после запятой"""
    try:
        if value is None:
            return 0
        return round(float(value), int(decimal_places))
    except (ValueError, TypeError):
        return value