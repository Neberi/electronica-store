from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem, Order, OrderItem
import json
import random
import string
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .forms import ProductReviewForm
from .models import ProductReview
from django.db import models

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .admin_utils import superuser_required, AdminContextMixin
from users.models import CustomUser

User = get_user_model()

def some_view(request):
    User = get_user_model()

# Функция для расчета скидки за количество
def calculate_quantity_discount(quantity):
    """Рассчитать скидку за количество товара"""
    if quantity >= 10:
        return 15
    elif quantity >= 7:
        return 10
    elif quantity >= 4:
        return 5
    return 0


# Функция для получения количества товаров в корзине
def get_cart_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            return 0
    else:
        return 0


# Данные о товарах
PRODUCTS_DATA = [
    {
        'id': 'core407v',
        'title': 'Core407V - Отладочная плата STM32F407VET6',
        'description': 'Отладочная плата на базе STM32F407VET6 с интерфейсами I/O, JTAG/SWD, богатым набором периферии и поддержкой различных протоколов связи для разработки встраиваемых систем.',
        'price': 4350,
        'image': 'core407v.jpg',
        'in_stock': 33,
        'url_name': 'product_core407v',
        'available': True
    },
    {
        'id': 'stlink-v2',
        'title': 'ST-LINK/V2 (mini) - Программатор/отладчик',
        'description': 'Внутрисхемный программатор/отладчик для микроконтроллеров STM8 и STM32 с поддержкой интерфейсов SWIM, JTAG и SWD, компактный размер и удобное подключение.',
        'price': 1850,
        'image': 'programmer.jpg',
        'in_stock': 25,
        'url_name': 'product_stlink',
        'available': True
    },
    {
        'id': 'arduino-uno',
        'title': 'Arduino Uno R3',
        'description': 'Популярная плата для начинающих и проектов прототипирования на базе микроконтроллера ATmega328P с цифровыми и аналоговыми входами/выходами, USB-интерфейсом и богатой экосистемой.',
        'price': 2500,
        'image': 'unoR3.jpg',
        'in_stock': 0,
        'url_name': 'product_arduino',
        'available': False
    }
]
# Словарь промокодов
PROMO_CODES = {
    'WELCOME5': 5,
    'ELECTRO10': 10,
    'TECH15': 15,
    'MEGA25': 25,
}


# Основные страницы
def index(request):
    context = {
        'cart_count': get_cart_count(request),
        'title': 'Магазин электронных компонентов - Главная',
        'promo_product': 'Core407V'
    }
    return render(request, 'index.html', context)


def about(request):
    context = {
        'cart_count': get_cart_count(request),
        'title': 'О проекте - Магазин электронных компонентов'
    }
    return render(request, 'about.html', context)


def catalog(request):
    products = [
        # Основные товары (оставляем как есть)
        {
            'id': 'core407v',
            'title': 'Core407V - Отладочная плата STM32F407VET6',
            'description': 'Мощная отладочная плата на базе STM32F407VET6 с поддержкой различных интерфейсов и периферии.',
            'price': 4350,
            'image': 'core407v.jpg',
            'available': True,  # В наличии
            'url_name': 'product_core407v'  # Активная ссылка
        },
        {
            'id': 'stlink-v2',
            'title': 'ST-LINK/V2 (mini) - Программатор/отладчик',
            'description': 'Компактный программатор и отладчик для микроконтроллеров STM32 с поддержкой SWD и JTAG.',
            'price': 1850,
            'image': 'programmer.jpg',
            'available': True,  # В наличии
            'url_name': 'product_stlink'  # Активная ссылка
        },
        {
            'id': 'arduino-uno',
            'title': 'Arduino Uno R3',
            'description': 'Классическая платформа для начинающих и профессионалов. Совместима с большинством шилдов и модулей.',
            'price': 2500,
            'image': 'unoR3.jpg',
            'available': False,  # Нет в наличии
            'url_name': 'product_arduino'  # Ссылка активная, но товар недоступен
        },
        # Новые товары - чередуем статус "в наличии"/"нет в наличии"
        {
            'id': 'raspberry-pi-4',
            'title': 'Raspberry Pi 4 Model B 4GB',
            'description': 'Одноплатный компьютер с процессором Broadcom BCM2711, 4 ГБ оперативной памяти.',
            'price': 7500,
            'image': '',
            'available': True,  # В наличии (больше товаров "в наличии")
            'url_name': None  # Пустая ссылка
        },
        {
            'id': 'esp32-devkit',
            'title': 'ESP32 DevKit C V4',
            'description': 'Плата разработки на базе ESP32 с WiFi и Bluetooth, 38 выводов, USB-C.',
            'price': 1200,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        },
        {
            'id': 'fpga-ice40',
            'title': 'iCE40 UltraPlus FPGA Board',
            'description': 'Плата для разработки на ПЛИС iCE40 с 5280 логическими элементами.',
            'price': 8900,
            'image': '',
            'available': False,  # Нет в наличии
            'url_name': None
        },
        {
            'id': 'logic-analyzer',
            'title': 'Logic Analyzer 24MHz 8-Channel',
            'description': '8-канальный логический анализатор с частотой 24 МГц для отладки цифровых схем.',
            'price': 3200,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        },
        {
            'id': 'oscilloscope-dso138',
            'title': 'DSO138 Мини осциллограф',
            'description': 'Портативный цифровой осциллограф с частотой 1 МГц, 2.4-дюймовым экраном.',
            'price': 2800,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        },
        {
            'id': 'power-supply-30v',
            'title': 'Блок питания 0-30V 5A',
            'description': 'Лабораторный источник питания с цифровым управлением, регулируемым напряжением и током.',
            'price': 5500,
            'image': '',
            'available': False,  # Нет в наличии
            'url_name': None
        },
        {
            'id': 'soldering-station',
            'title': 'Паяльная станция 60W',
            'description': 'Профессиональная паяльная станция с регулировкой температуры от 200 до 450°C.',
            'price': 3800,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        },
        {
            'id': 'multimeter-universal',
            'title': 'Мультиметр Uni-T UT61E',
            'description': 'Цифровой мультиметр с True RMS, измерением температуры и интерфейсом PC.',
            'price': 4200,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        },
        {
            'id': 'breadboard-kit',
            'title': 'Набор макетных плат',
            'description': 'Комплект из 3 макетных плат (400, 830 точек) с набором перемычек и проводов.',
            'price': 850,
            'image': '',
            'available': False,  # Нет в наличии
            'url_name': None
        },
        {
            'id': 'component-kit',
            'title': 'Набор электронных компонентов',
            'description': 'Базовый набор резисторов, конденсаторов, транзисторов, диодов и светодиодов.',
            'price': 1500,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        },
        {
            'id': 'sensor-kit',
            'title': 'Набор датчиков для Arduino',
            'description': 'Комплект из 37 различных датчиков: температуры, влажности, движения, газа и др.',
            'price': 2900,
            'image': '',
            'available': True,  # В наличии
            'url_name': None
        }
    ]

    context = {
        'title': 'Каталог товаров',
        'products': products
    }
    return render(request, 'catalog.html', context)


def contacts(request):
    # Получаем количество товаров в корзине
    cart_count = get_cart_count(request)

    # Если есть форма обратной связи в запросе POST
    if request.method == 'POST':
        # Обработка формы обратной связи
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Валидация данных
        if name and email and message:
            # Здесь можно добавить логику отправки email или сохранения в БД
            messages.success(request, 'Ваше сообщение успешно отправлено! Мы свяжемся с вами в ближайшее время.')
            # После успешной отправки перенаправляем на ту же страницу
            return redirect('main:contacts')
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')

    context = {
        'cart_count': cart_count,
        'title': 'Контакты - Магазин электронных компонентов'
    }
    return render(request, 'contacts.html', context)


def product_core407v(request):
    product = next((p for p in PRODUCTS_DATA if p['id'] == 'core407v'), None)

    # Получаем отзывы и рассчитываем рейтинг
    from .models import ProductReview
    reviews = ProductReview.objects.filter(product_id='core407v', is_approved=True).order_by('-created_at')[:10]
    total_reviews = ProductReview.objects.filter(product_id='core407v', is_approved=True).count()
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

    # Расчет скидки за количество (по умолчанию 1 штука)
    quantity = 1
    quantity_discount = calculate_quantity_discount(quantity)
    discounted_price = product['price'] * (1 - quantity_discount / 100) if quantity_discount > 0 else product['price']

    # Расчет распределения рейтингов
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in ProductReview.objects.filter(product_id='core407v', is_approved=True):
        if review.rating in rating_distribution:
            rating_distribution[review.rating] += 1

    # Добавьте дополнительные данные для шаблона
    product['subtitle'] = 'I/O, JTAG/SWD отладочный интерфейс (Cortex-M4)'
    product['features'] = [
        {'name': 'Cortex-M4', 'icon': '🚀'},
        {'name': 'JTAG/SWD', 'icon': '🔧'},
        {'name': 'USB', 'icon': '🔌'},
        {'name': '32-bit', 'icon': '💾'}
    ]
    product['specs'] = [
        {'label': 'Номенклатурный номер:', 'value': '9000485391'},
        {'label': 'Артикул:', 'value': 'Core407V'},
        {'label': 'PartNumber:', 'value': '5852'},
        {'label': 'Бренд:', 'value': 'Waveshare Electronics'},
        {'label': 'Ядро:', 'value': 'Cortex-M4'},
        {'label': 'Разрядность:', 'value': '32 бит'},
        {'label': 'USB интерфейс:', 'value': 'Да'},
        {'label': 'Макетная область:', 'value': 'Нет'}
    ]
    product['bulk_prices'] = [
        {'quantity': 'от 5 шт.', 'price': '4 070 ₽'},
        {'quantity': 'от 50 шт.', 'price': 'по запросу'}
    ]
    product['installment'] = '1 089'
    product['docs'] = '[ST-LINKV2 (mini)] pdf, 98 KB'

    # Дополнительная информация для отображения
    product['in_stock'] = 33
    product['stock_details'] = 'Доступен для заказа'
    product['delivery_info'] = [
        {'method': 'Почта России', 'term': '7-14 дней', 'price': 'бесплатно'},
        {'method': 'Курьерская служба', 'term': '3-7 дней', 'price': 'от 300 ₽'},
        {'method': 'Самовывоз', 'term': '1-2 дня', 'price': 'бесплатно'}
    ]
    product['delivery_region'] = 'Доставка по всей России'
    product['delivery_notes'] = '<p>* Сроки доставки указаны ориентировочно</p>'

    # Информация о применении
    product['application_areas'] = [
        'Разработка встраиваемых систем',
        'Отладка и программирование микроконтроллеров',
        'Образовательные проекты по электронике',
        'Промышленная автоматизация',
        'IoT проекты'
    ]

    # Информация о комплектации
    product['package_info'] = [
        'Плата Core407V - 1 шт.',
        'USB кабель - 1 шт.',
        'Документация на русском языке',
        'Гарантийный талон 12 месяцев'
    ]

    # Расчет процентов для диаграммы рейтингов
    rating_percentages = {}
    for rating in range(1, 6):
        count = rating_distribution.get(rating, 0)
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_percentages[rating] = round(percentage, 1)

    context = {
        'product': product,
        'cart_count': get_cart_count(request),
        'title': product['title'] if product else 'Core407V',
        'reviews': reviews,
        'total_reviews': total_reviews,
        'product_rating': {
            'avg': avg_rating,
            'count': total_reviews,
            'distribution': rating_distribution
        },
        'product_quantity_discount': quantity_discount,
        'discounted_price': discounted_price,
        'rating_percentages': rating_percentages
    }
    return render(request, 'product.html', context)


def product_stlink(request):
    product = next((p for p in PRODUCTS_DATA if p['id'] == 'stlink-v2'), None)

    # Получаем отзывы и рассчитываем рейтинг
    from .models import ProductReview
    reviews = ProductReview.objects.filter(product_id='stlink-v2', is_approved=True).order_by('-created_at')[:10]
    total_reviews = ProductReview.objects.filter(product_id='stlink-v2', is_approved=True).count()
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

    # Расчет скидки за количество (по умолчанию 1 штука)
    quantity = 1
    quantity_discount = calculate_quantity_discount(quantity)
    discounted_price = product['price'] * (1 - quantity_discount / 100) if quantity_discount > 0 else product['price']

    # Расчет распределения рейтингов
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in ProductReview.objects.filter(product_id='stlink-v2', is_approved=True):
        if review.rating in rating_distribution:
            rating_distribution[review.rating] += 1

    # Добавьте дополнительные данные для шаблона
    product['subtitle'] = 'JTAG/SWD для микроконтроллеров STM8 и STM32'
    product['features'] = [
        {'name': 'STM8/STM32', 'icon': '🔧'},
        {'name': 'JTAG/SWD', 'icon': '⚡'},
        {'name': 'USB', 'icon': '🔌'},
        {'name': 'Компактный', 'icon': '📦'}
    ]
    product['specs'] = [
        {'label': 'Номенклатурный номер:', 'value': '9000308060'},
        {'label': 'Артикул:', 'value': 'ST-LINK/V2 (mini)'},
        {'label': 'PartNumber:', 'value': '10053'},
        {'label': 'Бренд:', 'value': 'Waveshare Electronics'},
        {'label': 'Тип:', 'value': 'Программатор/отладчик'},
        {'label': 'Поддержка:', 'value': 'STM8, STM32'},
        {'label': 'Интерфейсы:', 'value': 'JTAG, SWD, SWIM'},
        {'label': 'Вес:', 'value': '80 г'}
    ]
    product['bulk_prices'] = [
        {'quantity': 'от 3 шт.', 'price': '1 650 ₽'},
        {'quantity': 'от 10 шт.', 'price': 'по запросу'}
    ]
    product['installment'] = '463'  # 1850 / 4

    # Дополнительная информация для отображения
    product['in_stock'] = 25
    product['stock_details'] = 'Доступен для заказа'
    product['delivery_info'] = [
        {'method': 'Почта России', 'term': '7-14 дней', 'price': 'бесплатно'},
        {'method': 'Курьерская служба', 'term': '3-7 дней', 'price': 'от 300 ₽'},
        {'method': 'Самовывоз', 'term': '1-2 дня', 'price': 'бесплатно'}
    ]
    product['delivery_region'] = 'Доставка по всей России'
    product['delivery_notes'] = '<p>* Сроки доставки указаны ориентировочно</p>'

    # Информация о комплектации
    product['package_info'] = [
        'ST-LINK/V2 (mini) - 1 шт.',
        '4-mini кабель - 1 шт.',
        'USB кабель - 1 шт.',
        'Документация и гарантия'
    ]

    # Информация о применении
    product['application_areas'] = [
        'Отладка и программирование микроконтроллеров STM',
        'Разработка встраиваемых систем',
        'Образовательные проекты по микроэлектронике',
        'Прототипирование электронных устройств',
        'Ремонт и обслуживание электронной техники'
    ]

    # Расчет процентов для диаграммы рейтингов
    rating_percentages = {}
    for rating in range(1, 6):
        count = rating_distribution.get(rating, 0)
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_percentages[rating] = round(percentage, 1)

    context = {
        'product': product,
        'cart_count': get_cart_count(request),
        'title': product['title'] if product else 'ST-LINK/V2',
        'reviews': reviews,
        'total_reviews': total_reviews,
        'product_rating': {
            'avg': avg_rating,
            'count': total_reviews,
            'distribution': rating_distribution
        },
        'product_quantity_discount': quantity_discount,
        'discounted_price': discounted_price,
        'rating_percentages': rating_percentages
    }
    return render(request, 'product.html', context)


def product_arduino(request):
    product = next((p for p in PRODUCTS_DATA if p['id'] == 'arduino-uno'), None)

    # Получаем отзывы и рассчитываем рейтинг
    from .models import ProductReview
    reviews = ProductReview.objects.filter(product_id='arduino-uno', is_approved=True).order_by('-created_at')[:10]
    total_reviews = ProductReview.objects.filter(product_id='arduino-uno', is_approved=True).count()
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

    # Расчет скидки за количество (по умолчанию 1 штука)
    quantity = 1
    quantity_discount = calculate_quantity_discount(quantity)
    discounted_price = product['price'] * (1 - quantity_discount / 100) if quantity_discount > 0 else product['price']

    # Расчет распределения рейтингов
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in ProductReview.objects.filter(product_id='arduino-uno', is_approved=True):
        if review.rating in rating_distribution:
            rating_distribution[review.rating] += 1

    # Добавьте дополнительные данные для шаблона
    product['subtitle'] = 'Плата для прототипирования на базе ATmega328P'
    product['features'] = [
        {'name': 'ATmega328P', 'icon': '🔌'},
        {'name': 'USB', 'icon': '💻'},
        {'name': 'Digital I/O', 'icon': '🔧'},
        {'name': 'Analog Inputs', 'icon': '📊'}
    ]
    product['specs'] = [
        {'label': 'Микроконтроллер:', 'value': 'ATmega328P'},
        {'label': 'Рабочее напряжение:', 'value': '5V'},
        {'label': 'Цифровые пины:', 'value': '14'},
        {'label': 'Аналоговые входы:', 'value': '6'},
        {'label': 'Тактовая частота:', 'value': '16 MHz'},
        {'label': 'Flash память:', 'value': '32 KB'},
        {'label': 'SRAM:', 'value': '2 KB'},
        {'label': 'EEPROM:', 'value': '1 KB'}
    ]
    product['bulk_prices'] = [
        {'quantity': 'от 5 шт.', 'price': '2 250 ₽'},
        {'quantity': 'от 20 шт.', 'price': 'по запросу'}
    ]

    # Дополнительная информация для отображения
    product['in_stock'] = 0  # Нет в наличии
    product['stock_details'] = 'Скоро будет новая поставка'
    product['delivery_info'] = [
        {'method': 'Почта России', 'term': '7-14 дней', 'price': 'бесплатно'},
        {'method': 'Курьерская служба', 'term': '3-7 дней', 'price': 'от 300 ₽'},
        {'method': 'Самовывоз', 'term': '1-2 дня', 'price': 'бесплатно'}
    ]
    product['delivery_region'] = 'Доставка по всей России'
    product['delivery_notes'] = '<p>* Товар временно отсутствует на складе</p>'

    # Информация о применении
    product['application_areas'] = [
        'Образовательные проекты и обучение программированию',
        'Прототипирование электронных устройств',
        'DIY проекты и умный дом',
        'Робототехника и автоматизация',
        'Интернет вещей (IoT)'
    ]

    # Информация о комплектации
    product['package_info'] = [
        'Плата Arduino Uno R3 - 1 шт.',
        'USB кабель - 1 шт.',
        'Документация на русском языке',
        'Гарантийный талон 12 месяцев'
    ]

    # Технические характеристики
    product['technical_specs'] = [
        {'name': 'Входное напряжение', 'value': '7-12V'},
        {'name': 'Выходное напряжение', 'value': '5V, 3.3V'},
        {'name': 'Цифровые пины I/O', 'value': '14 (6 PWM)'},
        {'name': 'Аналоговые входы', 'value': '6'},
        {'name': 'DC ток на пине', 'value': '40 mA'},
        {'name': 'DC ток на VCC/GND', 'value': '200 mA'},
        {'name': 'Флеш-память', 'value': '32 KB (0.5 KB загрузчик)'},
        {'name': 'SRAM', 'value': '2 KB'},
        {'name': 'EEPROM', 'value': '1 KB'},
        {'name': 'Тактовая частота', 'value': '16 MHz'},
        {'name': 'Длина', 'value': '68.6 mm'},
        {'name': 'Ширина', 'value': '53.4 mm'},
        {'name': 'Вес', 'value': '25 g'}
    ]

    # Расчет процентов для диаграммы рейтингов
    rating_percentages = {}
    for rating in range(1, 6):
        count = rating_distribution.get(rating, 0)
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_percentages[rating] = round(percentage, 1)

    context = {
        'product': product,
        'cart_count': get_cart_count(request),
        'title': product['title'] if product else 'Arduino Uno R3',
        'reviews': reviews,
        'total_reviews': total_reviews,
        'product_rating': {
            'avg': avg_rating,
            'count': total_reviews,
            'distribution': rating_distribution
        },
        'product_quantity_discount': quantity_discount,
        'discounted_price': discounted_price,
        'rating_percentages': rating_percentages
    }
    return render(request, 'product.html', context)

def get_rating_distribution(product_id):
    """Получить распределение рейтингов по товару"""
    from .models import ProductReview
    reviews = ProductReview.objects.filter(product_id=product_id, is_approved=True)
    distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        if review.rating in distribution:
            distribution[review.rating] += 1
    return distribution

def product(request, product_id):
    context = {
        'product_id': product_id,
        'cart_count': get_cart_count(request)
    }
    return render(request, 'product.html', context)


# Корзина - только для авторизованных пользователей
@csrf_exempt
@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))

            # Только для авторизованных пользователей
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=product_id,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            # ВАЖНО: Пересчитываем количество товаров в корзине
            cart_count = sum(item.quantity for item in cart.items.all())

            return JsonResponse({
                'success': True,
                'cart_count': cart_count,  # Это ключевое поле!
                'message': 'Товар добавлен в корзину'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})


@csrf_exempt
@login_required
def remove_from_cart(request, product_id):
    """Удаление товара из корзины"""
    try:
        # Только для авторизованных пользователей
        cart = Cart.objects.get(user=request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        cart_count = sum(item.quantity for item in cart.items.all())

        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'message': 'Товар удален из корзины'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})


@csrf_exempt
@login_required
def update_cart_quantity(request, product_id):
    """Обновление количества товара в корзине"""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))

            # Только для авторизованных пользователей
            cart = Cart.objects.get(user=request.user)
            if quantity <= 0:
                CartItem.objects.filter(cart=cart, product_id=product_id).delete()
            else:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product_id=product_id,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity = quantity
                    cart_item.save()

            cart_count = sum(item.quantity for item in cart.items.all())

            return JsonResponse({
                'success': True,
                'cart_count': cart_count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})


@login_required
def personal_cabinet(request):
    """Личный кабинет пользователя - только для авторизованных"""
    cart_items = []
    total_price = 0
    quantity_discount_total = 0

    # Получаем товары из корзины
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items_data = cart.items.all()
        # Преобразуем в формат для шаблона
        for item in cart_items_data:
            product_id = item.product_id
            quantity = item.quantity
            # Добавляем данные о товаре
            product_info = next((p for p in PRODUCTS_DATA if p['id'] == product_id), None)
            if product_info:
                quantity_discount = calculate_quantity_discount(quantity)
                discounted_price = product_info['price'] * (1 - quantity_discount / 100)
                item_total = discounted_price * quantity
                discount_savings = (product_info['price'] * quantity) - item_total

                cart_items.append({
                    'id': product_id,
                    'name': product_info['title'],
                    'price': product_info['price'],
                    'discounted_price': discounted_price,
                    'quantity': quantity,
                    'total': item_total,
                    'quantity_discount': quantity_discount,
                    'discount_savings': discount_savings,
                    'image': product_info['image'],
                    'url': f"/product/{product_id}/" if product_info.get('url_name') else '#'
                })
                total_price += item_total
                quantity_discount_total += discount_savings
    except Cart.DoesNotExist:
        pass

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'quantity_discount_total': quantity_discount_total,
        'cart_count': get_cart_count(request),
        'title': 'Личный кабинет - Магазин электронных компонентов'
    }
    return render(request, 'personal_cabinet.html', context)


@login_required
def checkout(request):
    """Оформление заказа"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()

        if not cart_items:
            messages.error(request, 'Ваша корзина пуста')
            return redirect('main:personal_cabinet')

        # Рассчитываем итоговую сумму
        total_price = 0
        for item in cart_items:
            product_info = next((p for p in PRODUCTS_DATA if p['id'] == item.product_id), None)
            if product_info:
                quantity_discount = calculate_quantity_discount(item.quantity)
                discounted_price = product_info['price'] * (1 - quantity_discount / 100)
                item_total = discounted_price * item.quantity
                total_price += item_total

        # Передаем промокоды в контекст
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'cart_count': get_cart_count(request),
            'title': 'Оформление заказа',
            'promo_codes': PROMO_CODES  # Добавляем промокоды
        }
        return render(request, 'checkout.html', context)

    except Cart.DoesNotExist:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('main:personal_cabinet')


@csrf_exempt
@login_required
def create_order(request):
    """Создание заказа"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Получаем данные из запроса
            region = data.get('region')
            address = data.get('address')
            phone = data.get('phone')
            payment_method = data.get('payment_method')
            promo_code = data.get('promo_code', '').strip().upper()

            # Валидация данных
            if not all([region, address, phone, payment_method]):
                return JsonResponse({
                    'success': False,
                    'message': 'Все поля обязательны для заполнения'
                })

            # Проверяем корзину
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()

            if not cart_items:
                return JsonResponse({
                    'success': False,
                    'message': 'Ваша корзина пуста'
                })

            # Рассчитываем стоимость товаров
            subtotal = 0
            order_items_data = []

            for item in cart_items:
                product_info = next((p for p in PRODUCTS_DATA if p['id'] == item.product_id), None)
                if product_info:
                    quantity_discount = calculate_quantity_discount(item.quantity)
                    discounted_price = product_info['price'] * (1 - quantity_discount / 100)
                    item_total = discounted_price * item.quantity
                    subtotal += item_total

                    order_items_data.append({
                        'product_id': item.product_id,
                        'product_name': product_info['title'],
                        'quantity': item.quantity,
                        'price': discounted_price,
                        'total': item_total
                    })

            # Рассчитываем стоимость доставки
            delivery_cost = calculate_delivery_cost(region)
            if delivery_cost is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Доставка в выбранный регион не осуществляется'
                })

            # Применяем промокод
            promo_discount = 0
            promo_discount_amount = 0
            valid_promo_code = None

            if promo_code:
                if promo_code in PROMO_CODES:
                    valid_promo_code = promo_code
                    promo_discount = PROMO_CODES[promo_code]
                    promo_discount_amount = subtotal * (promo_discount / 100)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Неверный промокод'
                    })

            # Рассчитываем финальную сумму
            final_amount = subtotal + delivery_cost - promo_discount_amount

            # Создаем номер заказа
            order_number = generate_order_number()

            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                order_number=order_number,
                total_amount=subtotal,
                delivery_cost=delivery_cost,
                final_amount=final_amount,
                region=region,
                address=address,
                phone=phone,
                payment_method=payment_method,
                promo_code=valid_promo_code,
                promo_discount=promo_discount,
                promo_discount_amount=promo_discount_amount,
                is_completed=True
            )

            # Создаем элементы заказа
            for item_data in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    product_id=item_data['product_id'],
                    product_name=item_data['product_name'],
                    quantity=item_data['quantity'],
                    price=item_data['price'],
                    total=item_data['total']
                )

            # Очищаем корзину
            cart.items.all().delete()

            return JsonResponse({
                'success': True,
                'order_number': order_number,
                'message': f'Заказ #{order_number} успешно оформлен!',
                'promo_applied': valid_promo_code is not None,
                'promo_discount': float(promo_discount_amount)
            })

        except Cart.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Корзина не найдена'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при создании заказа: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})


@csrf_exempt
@login_required
def check_promo_code(request):
    """Проверка промокода"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            promo_code = data.get('promo_code', '').strip().upper()

            if promo_code in PROMO_CODES:
                discount = PROMO_CODES[promo_code]
                return JsonResponse({
                    'success': True,
                    'discount': discount,
                    'message': f'Промокод "{promo_code}" действителен. Скидка {discount}%'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Неверный промокод'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при проверке промокода: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})


def calculate_delivery_cost(region):
    """Рассчитать стоимость доставки по региону"""
    delivery_costs = {
        'moscow_region': 0,  # Бесплатно
        'near_regions': 1000,  # 1000 руб
        'other_regions': 5000,  # 5000 руб
    }
    return delivery_costs.get(region)


def generate_order_number():
    """Генерация номера заказа"""
    return 'ORD' + ''.join(random.choices(string.digits, k=8))


@login_required
def order_list(request):
    """Список всех заказов пользователя (всех статусов)"""
    # Убираем фильтр по is_completed=True, показываем все заказы
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Используем 'order_list.html' вместо 'main/order_list.html'
    return render(request, 'order_list.html', {
        'orders': orders,
        'cart_count': get_cart_count(request),
        'title': 'Мои заказы'
    })


@login_required
def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()

    # Используем 'order_detail.html' вместо 'main/order_detail.html'
    return render(request, 'order_detail.html', {
        'order': order,
        'order_items': order_items,
        'cart_count': get_cart_count(request),
        'title': f'Заказ #{order.order_number}'
    })


@login_required
def order_detail(request, order_id):
    """Детали заказа"""
    # Получаем заказ только если он принадлежит текущему пользователю
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'cart_count': get_cart_count(request),
        'title': f'Заказ #{order.order_number}'
    }
    return render(request, 'order_detail.html', context)


@login_required
@csrf_exempt
def add_product_review(request, product_id):
    """Добавить отзыв к товару"""
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)

        if form.is_valid():
            # Проверяем, не оставлял ли уже пользователь отзыв
            existing_review = ProductReview.objects.filter(
                product_id=product_id,
                user=request.user
            ).first()

            if existing_review:
                return JsonResponse({
                    'success': False,
                    'message': 'Вы уже оставляли отзыв на этот товар'
                })

            # Сохраняем отзыв
            review = form.save(commit=False)
            review.product_id = product_id
            review.user = request.user
            review.save()

            # Получаем обновленную статистику
            reviews = ProductReview.objects.filter(product_id=product_id, is_approved=True)
            total_reviews = reviews.count()
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

            return JsonResponse({
                'success': True,
                'message': 'Спасибо за ваш отзыв!',
                'review': {
                    'id': review.id,
                    'user_name': review.user.username,
                    'rating': review.rating,
                    'title': review.title,
                    'text': review.text,
                    'created_at': review.created_at.strftime('%d.%m.%Y'),
                    'rating_stars': review.get_rating_stars(),
                    'rating_class': review.get_rating_class()
                },
                'stats': {
                    'total_reviews': total_reviews,
                    'avg_rating': round(avg_rating, 1)
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Пожалуйста, исправьте ошибки в форме',
                'errors': form.errors
            })

    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})


def get_product_reviews(request, product_id):
    """Получить отзывы о товаре"""
    reviews = ProductReview.objects.filter(
        product_id=product_id,
        is_approved=True
    ).order_by('-created_at')

    # Получаем статистику
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

    # Подготавливаем данные для JSON
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'user_name': review.user.username,
            'rating': review.rating,
            'rating_stars': review.get_rating_stars(),
            'rating_class': review.get_rating_class(),
            'title': review.title,
            'text': review.text,
            'created_at': review.created_at.strftime('%d.%m.%Y %H:%M'),
            'relative_time': get_relative_time(review.created_at)
        })

    return JsonResponse({
        'success': True,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'reviews': reviews_data
    })


def get_relative_time(date):
    """Получить относительное время (например, '2 дня назад')"""
    from django.utils import timezone
    now = timezone.now()
    diff = now - date

    if diff.days > 365:
        years = diff.days // 365
        return f'{years} год назад' if years == 1 else f'{years} лет назад'
    elif diff.days > 30:
        months = diff.days // 30
        return f'{months} месяц назад' if months == 1 else f'{months} месяцев назад'
    elif diff.days > 0:
        return f'{diff.days} день назад' if diff.days == 1 else f'{diff.days} дней назад'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} час назад' if hours == 1 else f'{hours} часов назад'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} минуту назад' if minutes == 1 else f'{minutes} минут назад'
    else:
        return 'только что'


# ===================== АДМИН-ПАНЕЛЬ =====================

@superuser_required
def admin_panel(request):
    """
    Главная страница админ-панели
    """
    # Статистика
    total_users = CustomUser.objects.count()
    total_orders = Order.objects.count()
    total_reviews = ProductReview.objects.count()
    total_carts = Cart.objects.count()

    # Недавние заказы
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    # Статистика по статусам заказов
    order_stats = Order.objects.values('status').annotate(count=Count('id')).order_by('status')

    # Конверсия (пользователи с заказами)
    users_with_orders = CustomUser.objects.filter(orders__isnull=False).distinct().count()
    conversion_rate = (users_with_orders / total_users * 100) if total_users > 0 else 0

    # Доход за последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_revenue = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('final_amount'))['total'] or 0

    context = {
        'page_title': 'Админ-панель - Главная',
        'active_section': 'dashboard',
        'total_users': total_users,
        'total_orders': total_orders,
        'total_reviews': total_reviews,
        'total_carts': total_carts,
        'recent_orders': recent_orders,
        'order_stats': order_stats,
        'conversion_rate': round(conversion_rate, 2),
        'recent_revenue': recent_revenue,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@superuser_required
def admin_orders(request):
    """
    Список всех заказов с фильтрацией
    """
    orders = Order.objects.select_related('user').prefetch_related('items').all()

    # Фильтрация
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('q')

    if status_filter:
        orders = orders.filter(status=status_filter)

    if date_from:
        orders = orders.filter(created_at__gte=date_from)

    if date_to:
        orders = orders.filter(created_at__lte=date_to)

    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # Сортировка
    sort_by = request.GET.get('sort_by', '-created_at')
    if sort_by in ['order_number', 'created_at', 'final_amount', 'status']:
        orders = orders.order_by(sort_by)

    # Пагинация
    paginator = Paginator(orders, 20)
    page = request.GET.get('page', 1)

    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    context = {
        'page_title': 'Админ-панель - Заказы',
        'active_section': 'orders',
        'orders': orders_page,
        'order_count': orders.count(),
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query or '',
        'sort_by': sort_by,
        'STATUS_CHOICES': Order.STATUS_CHOICES,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_panel/orders.html', context)


@superuser_required
def admin_order_detail(request, order_id):
    """
    Детальная информация о заказе
    """
    try:
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Заказ не найден.')
        return redirect('main:admin_orders')

    context = {
        'page_title': f'Админ-панель - Заказ #{order.order_number}',
        'active_section': 'orders',
        'order': order,
        'STATUS_CHOICES': Order.STATUS_CHOICES,
        'PAYMENT_CHOICES': Order.PAYMENT_CHOICES,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_panel/order_detail.html', context)


@superuser_required
@csrf_exempt
def update_order_status(request, order_id):
    """
    Обновление статуса заказа (AJAX)
    """
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.POST.get('status')

            if new_status in dict(Order.STATUS_CHOICES).keys():
                order.status = new_status
                order.save()
                messages.success(request, f'Статус заказа #{order.order_number} обновлен.')
                return JsonResponse({'success': True, 'new_status': order.get_status_display()})
            else:
                return JsonResponse({'success': False, 'error': 'Неверный статус.'})

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Заказ не найден.'})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса.'})


@superuser_required
def delete_order(request, order_id):
    """
    Удаление заказа
    """
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            order_number = order.order_number
            order.delete()
            messages.success(request, f'Заказ #{order_number} успешно удален.')
        except Order.DoesNotExist:
            messages.error(request, 'Заказ не найден.')

    return redirect('main:admin_orders')


@superuser_required
def admin_carts(request):
    """
    Управление корзинами пользователей
    """
    carts = Cart.objects.select_related('user').prefetch_related('items').all()

    # Фильтрация
    user_filter = request.GET.get('user')
    has_items = request.GET.get('has_items')

    if user_filter:
        carts = carts.filter(user__username__icontains=user_filter)

    if has_items == 'true':
        carts = carts.annotate(item_count=Count('items')).filter(item_count__gt=0)
    elif has_items == 'false':
        carts = carts.annotate(item_count=Count('items')).filter(item_count=0)

    # Сортировка
    sort_by = request.GET.get('sort_by', '-created_at')
    if sort_by in ['created_at', 'user__username']:
        carts = carts.order_by(sort_by)

    # Пагинация
    paginator = Paginator(carts, 20)
    page = request.GET.get('page', 1)

    try:
        carts_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        carts_page = paginator.page(1)

    # Подсчет товаров в каждой корзине
    for cart in carts_page:
        cart.item_count = cart.items.count()
        cart.total_items = cart.items.aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'page_title': 'Админ-панель - Корзины',
        'active_section': 'carts',
        'carts': carts_page,
        'cart_count': carts.count(),
        'user_filter': user_filter or '',
        'has_items': has_items,
        'sort_by': sort_by,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_panel/carts.html', context)


@superuser_required
def delete_cart(request, cart_id):
    """
    Удаление корзины пользователя
    """
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(id=cart_id)
            username = cart.user.username
            cart.delete()
            messages.success(request, f'Корзина пользователя {username} удалена.')
        except Cart.DoesNotExist:
            messages.error(request, 'Корзина не найдена.')

    return redirect('main:admin_carts')


@superuser_required
def admin_users(request):
    """
    Управление пользователями
    """
    users = CustomUser.objects.all()

    # Фильтрация
    search_query = request.GET.get('q')
    is_staff = request.GET.get('is_staff')
    is_active = request.GET.get('is_active')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if is_staff == 'true':
        users = users.filter(is_staff=True)
    elif is_staff == 'false':
        users = users.filter(is_staff=False)

    if is_active == 'true':
        users = users.filter(is_active=True)
    elif is_active == 'false':
        users = users.filter(is_active=False)

    # Сортировка
    sort_by = request.GET.get('sort_by', '-date_joined')
    if sort_by in ['username', 'email', 'date_joined', 'last_login']:
        users = users.order_by(sort_by)

    # Пагинация
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)

    try:
        users_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        users_page = paginator.page(1)

    # Статистика для каждого пользователя
    for user in users_page:
        user.order_count = user.orders.count()
        user.review_count = user.reviews.count()

    context = {
        'page_title': 'Админ-панель - Пользователи',
        'active_section': 'users',
        'users': users_page,
        'user_count': users.count(),
        'search_query': search_query or '',
        'is_staff': is_staff,
        'is_active': is_active,
        'sort_by': sort_by,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_panel/users.html', context)


@superuser_required
@csrf_exempt
def toggle_staff_status(request, user_id):
    """
    Включение/выключение статуса staff у пользователя (AJAX)
    """
    if request.method == 'POST':
        try:
            user = CustomUser.objects.get(id=user_id)
            user.is_staff = not user.is_staff
            user.save()

            status = 'назначен' if user.is_staff else 'снят'
            messages.success(request, f'Статус staff для пользователя {user.username} {status}.')

            return JsonResponse({
                'success': True,
                'is_staff': user.is_staff,
                'message': f'Статус staff: {"Да" if user.is_staff else "Нет"}'
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден.'})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса.'})


@superuser_required
def admin_reviews(request):
    """
    Управление отзывами
    """
    reviews = ProductReview.objects.select_related('user').all()

    # Фильтрация
    product_id = request.GET.get('product_id')
    user_filter = request.GET.get('user')
    rating_filter = request.GET.get('rating')
    is_approved = request.GET.get('is_approved')

    if product_id:
        reviews = reviews.filter(product_id__icontains=product_id)

    if user_filter:
        reviews = reviews.filter(user__username__icontains=user_filter)

    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)

    if is_approved == 'true':
        reviews = reviews.filter(is_approved=True)
    elif is_approved == 'false':
        reviews = reviews.filter(is_approved=False)

    # Сортировка
    sort_by = request.GET.get('sort_by', '-created_at')
    if sort_by in ['created_at', 'rating', 'product_id', 'user__username']:
        reviews = reviews.order_by(sort_by)

    # Пагинация
    paginator = Paginator(reviews, 20)
    page = request.GET.get('page', 1)

    try:
        reviews_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        reviews_page = paginator.page(1)

    context = {
        'page_title': 'Админ-панель - Отзывы',
        'active_section': 'reviews',
        'reviews': reviews_page,
        'review_count': reviews.count(),
        'product_id': product_id or '',
        'user_filter': user_filter or '',
        'rating_filter': rating_filter,
        'is_approved': is_approved,
        'sort_by': sort_by,
        'RATING_CHOICES': ProductReview.RATING_CHOICES,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_panel/reviews.html', context)


@superuser_required
@csrf_exempt
def delete_review(request, review_id):
    """
    Удаление отзыва (AJAX)
    """
    if request.method == 'POST':
        try:
            review = ProductReview.objects.get(id=review_id)
            product_id = review.product_id
            username = review.user.username
            review.delete()

            messages.success(request, f'Отзыв от {username} на товар {product_id} удален.')
            return JsonResponse({'success': True})
        except ProductReview.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Отзыв не найден.'})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса.'})


@superuser_required
@csrf_exempt
def toggle_review_approval(request, review_id):
    """
    Одобрение/запрет отзыва (AJAX)
    """
    if request.method == 'POST':
        try:
            review = ProductReview.objects.get(id=review_id)
            review.is_approved = not review.is_approved
            review.save()

            status = 'одобрен' if review.is_approved else 'скрыт'
            messages.success(request, f'Отзыв {status}.')

            return JsonResponse({
                'success': True,
                'is_approved': review.is_approved,
                'message': f'Статус: {"Одобрен" if review.is_approved else "Скрыт"}'
            })
        except ProductReview.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Отзыв не найден.'})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса.'})