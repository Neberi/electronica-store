
from django.contrib import admin
from django.urls import path, include
from feedback.views import FeedbackView

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('contacts/', FeedbackView.as_view(), name='contacts'),  # сначала наша форма
    path('', include('main.urls')),  # потом остальные URL из main
    path('users/', include('users.urls')),
]