from django.contrib import admin
from django.urls import path, include
from apps.dashboard.views import landing_view, methodology_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Public & Research Pages
    path('', landing_view, name='landing'),
    path('methodology/', methodology_view, name='methodology'),
    
    # Core Application Modules
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('datasets/', include('apps.datasets.urls', namespace='datasets')),
    path('models/', include('apps.models_registry.urls', namespace='models_registry')),
    path('benchmarks/', include('apps.benchmarks.urls', namespace='benchmarks')),
    
    # REST API Endpoints & OpenAPI Docs
    path('api/v1/', include('apps.api.urls', namespace='api')),
]
