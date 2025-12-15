from django.db import models
from django.conf import settings  # Импортируем settings
from django.contrib.auth.models import User


class Cart(models.Model):
    # Используем settings.AUTH_USER_MODEL вместо 'auth.User'
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # <-- ИЗМЕНИТЬ ТУТ
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product_id']

    def __str__(self):
        return f"{self.product_id} x {self.quantity}"


class Order(models.Model):
    # Используем settings.AUTH_USER_MODEL вместо 'auth.User'
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # <-- ИЗМЕНИТЬ ТУТ
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь'
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Номер заказа'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма товаров'
    )
    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Стоимость доставки'
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Итоговая сумма'
    )

    # Информация о доставке
    region = models.CharField(
        max_length=100,
        verbose_name='Регион'
    )
    address = models.TextField(
        verbose_name='Адрес доставки'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон'
    )

    # Оплата
    PAYMENT_CHOICES = [
        ('card', 'Картой онлайн'),
        ('cash', 'Наличными при получении'),
        ('bank', 'Банковский перевод'),
    ]
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        verbose_name='Способ оплаты'
    )

    # Промокоды
    promo_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Промокод'
    )
    promo_discount = models.IntegerField(
        default=0,
        verbose_name='Скидка по промокоду (%)'
    )
    promo_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Сумма скидки по промокоду'
    )

    # Статус
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Завершен'
    )

    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.order_number}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        import random
        import string
        return 'ORD' + ''.join(random.choices(string.digits, k=8))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class ProductReview(models.Model):
    """Модель отзыва о товаре"""
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ Отлично'),
        (4, '⭐⭐⭐⭐ Хорошо'),
        (3, '⭐⭐⭐ Удовлетворительно'),
        (2, '⭐⭐ Плохо'),
        (1, '⭐ Очень плохо'),
    ]

    product_id = models.CharField(
        max_length=50,
        verbose_name='ID товара'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='reviews'
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name='Оценка'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок отзыва'
    )
    text = models.TextField(
        verbose_name='Текст отзыва'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name='Одобрен'
    )

    class Meta:
        verbose_name = 'Отзыв о товаре'
        verbose_name_plural = 'Отзывы о товарах'
        ordering = ['-created_at']
        unique_together = ['product_id', 'user']  # Один отзыв от пользователя на товар

    def __str__(self):
        return f'Отзыв на {self.product_id} от {self.user.username}'

    def get_rating_stars(self):
        """Получить звезды рейтинга"""
        return '⭐' * self.rating

    def get_rating_class(self):
        """Получить CSS класс для рейтинга"""
        if self.rating >= 4:
            return 'rating-high'
        elif self.rating >= 3:
            return 'rating-medium'
        else:
            return 'rating-low'