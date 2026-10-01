from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.datasets.views import DatasetViewSet, DatasetVersionViewSet, BenchmarkQuestionViewSet
from apps.models_registry.views import ModelProviderViewSet, AIModelViewSet
from apps.benchmarks.views import BenchmarkRunViewSet
from apps.evaluations.views import ErrorCategoryViewSet, EvaluationResultViewSet

router = DefaultRouter()
router.register(r'datasets', DatasetViewSet, basename='api-dataset')
router.register(r'dataset-versions', DatasetVersionViewSet, basename='api-dataset-version')
router.register(r'questions', BenchmarkQuestionViewSet, basename='api-question')
router.register(r'model-providers', ModelProviderViewSet, basename='api-model-provider')
router.register(r'models', AIModelViewSet, basename='api-model')
router.register(r'benchmark-runs', BenchmarkRunViewSet, basename='api-benchmark-run')
router.register(r'error-categories', ErrorCategoryViewSet, basename='api-error-category')
router.register(r'evaluation-results', EvaluationResultViewSet, basename='api-evaluation-result')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    
    # OpenAPI Schema & Interactive Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
]
