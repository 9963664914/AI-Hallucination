from django.urls import path
from . import views

app_name = 'benchmarks'

urlpatterns = [
    path('', views.benchmark_list_view, name='list'),
    path('create/', views.benchmark_create_view, name='create'),
    path('compare/', views.benchmark_compare_view, name='compare'),
    path('<int:pk>/', views.benchmark_detail_view, name='detail'),
    path('<int:pk>/cancel/', views.benchmark_cancel_view, name='cancel'),
    path('<int:pk>/progress/', views.benchmark_progress_api, name='progress'),
]
