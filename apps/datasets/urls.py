from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('', views.dataset_list_view, name='list'),
    path('create/', views.dataset_create_view, name='create'),
    path('<slug:slug>/', views.dataset_detail_view, name='detail'),
    path('<slug:slug>/version/<int:version_id>/export/', views.export_dataset_view, name='export'),
]
