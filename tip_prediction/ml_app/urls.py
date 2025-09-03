from django.urls import path
from . import views

app_name = 'ml_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('predict/', views.predict_tip, name='predict_tip'),
]
