from django.urls import path
from . import views

app_name = 'models_registry'

urlpatterns = [
    path('', views.model_list_view, name='list'),
    path('create/', views.model_create_view, name='create'),
]
