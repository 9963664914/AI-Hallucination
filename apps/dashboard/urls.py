from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index_view, name='index'),
    path('question/<int:response_id>/', views.question_analysis_view, name='question_analysis'),
]
