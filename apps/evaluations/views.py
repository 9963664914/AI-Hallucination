from rest_framework import viewsets, permissions
from .models import ErrorCategory, EvaluationResult
from .serializers import ErrorCategorySerializer, EvaluationResultSerializer

class ErrorCategoryViewSet(viewsets.ModelViewSet):
    queryset = ErrorCategory.objects.all()
    serializer_class = ErrorCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class EvaluationResultViewSet(viewsets.ModelViewSet):
    queryset = EvaluationResult.objects.select_related('model_response').prefetch_related('error_categories', 'evidences').all()
    serializer_class = EvaluationResultSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['is_hallucination', 'is_abstained']
