from django.urls import path
from . import views

app_name = 'main'  # Добавляем namespace для приложения

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('catalog/', views.catalog, name='catalog'),
    path('contacts/', views.contacts, name='contacts'),
    path('personal/', views.personal_cabinet, name='personal_cabinet'),


    # Отдельные маршруты для конкретных продуктов
    path('product/core407v/', views.product_core407v, name='product_core407v'),
    path('product/stlink-v2/', views.product_stlink, name='product_stlink'),
    path('product/arduino-uno/', views.product_arduino, name='product_arduino'),

    # Шаблоны
    path('product/<str:product_id>/', views.product, name='product'),

    # Маршруты для корзины
    path('cart/add/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<str:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),

    # Оформление заказа
    path('checkout/', views.checkout, name='checkout'),
    path('order/create/', views.create_order, name='create_order'),
    path('check_promo/', views.check_promo_code, name='check_promo'),

    # Отзывы о товарах (ДОБАВЬТЕ ЭТИ СТРОКИ)
    path('product/review/add/<str:product_id>/', views.add_product_review, name='add_product_review'),
    path('product/reviews/<str:product_id>/', views.get_product_reviews, name='get_product_reviews'),

    # Заказы
    path('orders/', views.order_list, name='order_list'),

    # Админ-панель (только для суперпользователей)
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('admin-panel/orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('admin-panel/carts/', views.admin_carts, name='admin_carts'),
    path('admin-panel/carts/<int:cart_id>/delete/', views.delete_cart, name='delete_cart'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:user_id>/toggle-staff/', views.toggle_staff_status, name='toggle_staff_status'),
    path('admin-panel/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-panel/reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('admin-panel/reviews/<int:review_id>/toggle-approve/', views.toggle_review_approval,
         name='toggle_review_approval'),

]