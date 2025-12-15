from django import forms
from .models import ProductReview


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'text']
        widgets = {
            'rating': forms.RadioSelect(choices=ProductReview.RATING_CHOICES),
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Краткий заголовок вашего отзыва',
                'maxlength': '200'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Подробно опишите ваши впечатления от товара...',
                'rows': '5'
            })
        }
        labels = {
            'rating': 'Ваша оценка',
            'title': 'Заголовок отзыва',
            'text': 'Текст отзыва'
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating not in [1, 2, 3, 4, 5]:
            raise forms.ValidationError('Пожалуйста, выберите оценку от 1 до 5')
        return rating