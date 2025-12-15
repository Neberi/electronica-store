from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'final_amount', 'region', 'payment_method', 'created_at', 'is_completed']
    list_filter = ['region', 'payment_method', 'is_completed', 'created_at']
    search_fields = ['order_number', 'user__username', 'address']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'total']
    list_filter = ['order__created_at']

