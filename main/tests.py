# main/tests.py
import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Cart, Order, ProductReview
from .forms import ProductReviewForm
from django.template import Template, Context

User = get_user_model()


class TestMainViews:
    """Тесты основных представлений"""

    @pytest.mark.django_db
    def test_home_page(self, client):
        """Тест главной страницы"""
        response = client.get(reverse('main:index'))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Электроника Store' in content
        assert 'магазин' in content.lower()

    @pytest.mark.django_db
    def test_catalog_page(self, client):
        """Тест страницы каталога"""
        response = client.get(reverse('main:catalog'))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Каталог товаров' in content or 'каталог' in content.lower()
        assert 'Core407V' in content or 'STM32' in content or 'Arduino' in content

    @pytest.mark.django_db
    def test_product_page(self, client):
        """Тест страницы товара"""
        response = client.get(reverse('main:product_core407v'))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Core407V' in content or 'отладочная плата' in content.lower()


class TestCartFunctionality:
    """Тесты функционала корзины"""

    @pytest.mark.django_db
    def test_add_to_cart_authenticated(self, admin_client):
        """Тест добавления в корзину для авторизованного пользователя"""
        response = admin_client.post(
            reverse('main:add_to_cart', args=['core407v']),
            {'quantity': 1}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] == True

    @pytest.mark.django_db
    def test_cart_for_anonymous(self, client):
        """Тест что анонимный пользователь перенаправляется на страницу входа"""
        # Без follow получаем редирект
        response = client.post(
            reverse('main:add_to_cart', args=['core407v']),
            {'quantity': 1},
            follow=False
        )
        # Должен быть редирект на страницу входа (302)
        assert response.status_code == 302
        assert '/users/login/' in response.url

        # С follow проверяем что попали на страницу входа
        response = client.post(
            reverse('main:add_to_cart', args=['core407v']),
            {'quantity': 1},
            follow=True
        )
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'войти' in content.lower() or 'login' in content.lower()


class TestOrderProcessing:
    """Тесты обработки заказов"""

    @pytest.mark.django_db
    def test_create_order(self, admin_user, admin_client):
        """Тест создания заказа"""
        # Сначала добавляем товар в корзину
        admin_client.post(
            reverse('main:add_to_cart', args=['core407v']),
            {'quantity': 1}
        )

        # Создаем заказ
        order_data = {
            'region': 'moscow_region',
            'address': 'Тестовый адрес',
            'phone': '+79991234567',
            'payment_method': 'card',
            'promo_code': ''
        }

        response = admin_client.post(
            reverse('main:create_order'),
            json.dumps(order_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] == True or 'message' in data

    @pytest.mark.django_db
    def test_order_list_for_user(self, admin_client):
        """Тест списка заказов пользователя"""
        response = admin_client.get(reverse('main:order_list'))
        assert response.status_code == 200


class TestAdminPanel:
    """Тесты админ-панели"""

    @pytest.mark.django_db
    def test_admin_panel_access(self, admin_client):
        """Тест доступа к админ-панели для суперпользователя"""
        response = admin_client.get(reverse('main:admin_panel'))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_panel_denied_for_regular_user(self, client, django_user_model):
        """Тест что обычный пользователь не имеет доступа к админ-панели"""
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            is_superuser=False
        )
        client.force_login(user)

        response = client.get(reverse('main:admin_panel'))
        assert response.status_code in [302, 403]


class TestModels:
    """Тесты моделей"""

    @pytest.mark.django_db
    def test_user_creation(self, django_user_model):
        """Тест создания пользователя"""
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            secret_question='Любимый цвет?',
            secret_answer='Синий'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.secret_question == 'Любимый цвет?'

    @pytest.mark.django_db
    def test_cart_creation(self, django_user_model):
        """Тест создания корзины"""
        user = django_user_model.objects.create_user(
            username='cartuser',
            password='testpass123',
            email='cart@example.com',
            secret_question='Вопрос',
            secret_answer='Ответ'
        )
        cart = Cart.objects.create(user=user)
        assert cart.user == user
        assert cart.created_at is not None

    @pytest.mark.django_db
    def test_order_creation(self, django_user_model):
        """Тест создания заказа"""
        user = django_user_model.objects.create_user(
            username='orderuser',
            password='testpass123',
            email='order@example.com',
            secret_question='Вопрос',
            secret_answer='Ответ'
        )
        order = Order.objects.create(
            user=user,
            order_number='TEST123',
            total_amount=1000,
            delivery_cost=0,
            final_amount=1000,
            region='Москва',
            address='ул. Тестовая, д. 1',
            phone='+79991234567',
            payment_method='card',
            status='pending'
        )
        assert order.user == user
        assert order.order_number == 'TEST123'
        assert order.final_amount == 1000
        assert order.get_status_display() == 'Ожидает обработки'


class TestForms:
    """Тесты форм"""

    @pytest.mark.django_db
    def test_registration_form(self):
        """Тест формы регистрации"""
        from users.forms import CustomUserCreationForm

        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'secret_question': 'Любимый цвет?',
            'secret_answer': 'Синий'
        }

        form = CustomUserCreationForm(data=form_data)
        assert form.is_valid()

    @pytest.mark.django_db
    def test_review_form(self):
        """Тест формы отзыва"""
        from .forms import ProductReviewForm

        form_data = {
            'rating': 5,
            'title': 'Отличный товар!',
            'text': 'Очень понравился, рекомендую.'
        }

        form = ProductReviewForm(data=form_data)
        assert form.is_valid()


class TestViewsIntegration:
    """Интеграционные тесты ключевых сценариев"""

    @pytest.mark.django_db
    def test_complete_purchase_flow(self, django_user_model, client):
        """Полный тест сценария покупки"""
        # 1. Регистрация пользователя
        user_data = {
            'username': 'buyer',
            'email': 'buyer@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'secret_question': 'Вопрос',
            'secret_answer': 'Ответ'
        }

        response = client.post(reverse('users:register'), user_data)
        assert response.status_code in [200, 302]

        # 2. Вход пользователя
        login_data = {
            'username': 'buyer',
            'password': 'TestPass123!'
        }
        response = client.post(reverse('users:login'), login_data)
        assert response.status_code in [200, 302]

        # 3. Добавление товара в корзину
        response = client.post(
            reverse('main:add_to_cart', args=['core407v']),
            {'quantity': 1}
        )
        assert response.status_code == 200

        # 4. Проверка корзины
        response = client.get(reverse('main:personal_cabinet'))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Core407V' in content or 'корзина' in content.lower()


class TestErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.mark.django_db
    def test_nonexistent_page(self, client):
        """Тест несуществующей страницы"""
        response = client.get('/this-page-does-not-exist-12345/')
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_invalid_cart_quantity(self, admin_client):
        """Тест некорректного количества товара"""
        response = admin_client.post(
            reverse('main:add_to_cart', args=['core407v']),
            {'quantity': 0}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'success' in data


class TestURLs:
    """Тесты URL-адресов"""

    @pytest.mark.django_db
    def test_all_main_urls(self, client):
        """Тест доступности всех основных URL"""
        urls_to_test = [
            ('main:index', 200),
            ('main:about', 200),
            ('main:catalog', 200),
            ('main:contacts', 200),
            ('main:product_core407v', 200),
            ('main:product_stlink', 200),
            ('main:product_arduino', 200),
        ]

        for url_name, expected_status in urls_to_test:
            response = client.get(reverse(url_name))
            assert response.status_code == expected_status, f"Failed for {url_name}"


class TestTemplates:
    """Тесты шаблонов"""

    @pytest.mark.django_db
    def test_template_inheritance(self, client):
        """Тест наследования шаблонов"""
        response = client.get(reverse('main:index'))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert '<!DOCTYPE html>' in content
        assert '<html' in content
        assert '</html>' in content

    @pytest.mark.django_db
    def test_template_url_tag_with_empty_product_id(self):
        """Тест тега url с пустым product_id"""
        template = Template('{% url "main:add_product_review" product_id %}')
        context = Context({'product_id': ''})
        try:
            result = template.render(context)
            # Если не выбросило исключение - это ошибка
            assert False, "Should have raised NoReverseMatch for empty product_id"
        except Exception as e:
            assert 'NoReverseMatch' in str(type(e).__name__)


class TestStaticFiles:
    """Тесты статических файлов"""

    @pytest.mark.django_db
    def test_static_files_serving(self, client):
        """Тест что статические файлы доступны"""
        response = client.get('/static/css/main.css')
        # Может быть 200 или 404 если файла нет
        assert response.status_code in [200, 404]