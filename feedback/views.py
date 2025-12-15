# feedback/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from .forms import FeedbackForm
from .models import Feedback


class FeedbackView(View):
    def get(self, request):
        form = FeedbackForm()
        return render(request, 'contacts.html', {
            'form': form,
            'title': 'Контакты'
        })

    def post(self, request):
        print("=" * 60)
        print("🟡 POST ЗАПРОС НАЧАТ")
        print("=" * 60)

        # Выводим ВСЕ данные из запроса
        print("📨 ВСЕ POST данные:")
        for key, value in request.POST.items():
            print(f"   {key}: {value}")

        print("🔑 CSRF токен:", 'csrfmiddlewaretoken' in request.POST)
        print("👤 Поле 'name':", request.POST.get('name', 'НЕТ'))
        print("📧 Поле 'email':", request.POST.get('email', 'НЕТ'))
        print("💬 Поле 'message':", request.POST.get('message', 'НЕТ'))

        form = FeedbackForm(request.POST)
        print("📝 Форма создана")
        print("🔗 Форма привязана:", form.is_bound)

        # Проверяем каждое поле отдельно
        print("🔍 ПРОВЕРКА ПОЛЕЙ ФОРМЫ:")
        for field_name in ['name', 'email', 'message']:
            field = form.fields[field_name]
            value = form.data.get(field_name, 'НЕТ')
            print(f"   {field_name}: '{value}'")

        is_valid = form.is_valid()
        print("✅ Форма валидна:", is_valid)

        if not is_valid:
            print("❌ ОШИБКИ ВАЛИДАЦИИ:")
            print(form.errors.as_json())
            for field, errors in form.errors.items():
                print(f"   {field}: {list(errors)}")
        else:
            print("💾 Сохраняем форму...")
            try:
                feedback = form.save()
                print(f"🆕 УСПЕХ! Объект сохранен с ID: {feedback.id}")

                # Выводим данные
                print("=" * 50)
                print("НОВАЯ ФОРМА ОБРАТНОЙ СВЯЗИ")
                print("=" * 50)
                print(f"Имя: {feedback.name}")
                print(f"Email: {feedback.email}")
                print(f"Сообщение: {feedback.message}")
                print("=" * 50)

                messages.success(request, 'Сообщение отправлено!')
                return redirect('main:index')

            except Exception as e:
                print(f"💥 ОШИБКА: {e}")

        return render(request, 'contacts.html', {
            'form': form,
            'title': 'Контакты'
        })