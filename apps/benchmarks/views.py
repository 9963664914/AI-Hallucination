import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BenchmarkRun, BenchmarkRunModel, ModelResponse
from .serializers import BenchmarkRunSerializer, ModelResponseSerializer
from .tasks import run_benchmark_execution, execute_benchmark_run_task
from apps.datasets.models import Dataset, DatasetVersion, BenchmarkQuestion
from apps.models_registry.models import AIModel

# DRF ViewSet
class BenchmarkRunViewSet(viewsets.ModelViewSet):
    queryset = BenchmarkRun.objects.all()
    serializer_class = BenchmarkRunSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        run = self.get_object()
        if run.status in ['running', 'completed']:
            return Response({'error': f'Run is already in status: {run.status}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trigger background task or eager execution
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', True):
            run_benchmark_execution(run.id)
        else:
            execute_benchmark_run_task.delay(run.id)
            
        return Response({'status': 'started', 'run_id': run.id})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        run = self.get_object()
        if run.status == 'running':
            run.status = 'cancelled'
            run.save()
            return Response({'status': 'cancelled'})
        return Response({'error': f'Cannot cancel run with status {run.status}'}, status=status.HTTP_400_BAD_REQUEST)

# Template Views
@login_required
def benchmark_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        version_id = request.POST.get('dataset_version')
        model_ids = request.POST.getlist('models')

        if not title or not version_id or not model_ids:
            messages.error(request, "Please provide a title, select a dataset version, and pick at least one model.")
            return redirect('benchmarks:create')

        dataset_version = get_object_or_404(DatasetVersion, id=version_id)
        selected_models = AIModel.objects.filter(id__in=model_ids, is_active=True)

        if not selected_models.exists():
            messages.error(request, "No active models were selected.")
            return redirect('benchmarks:create')

        run = BenchmarkRun.objects.create(
            title=title,
            user=request.user,
            dataset_version=dataset_version,
            status='pending'
        )

        for model in selected_models:
            BenchmarkRunModel.objects.create(benchmark_run=run, model=model)

        # Trigger execution (Eager or async worker)
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', True):
            run_benchmark_execution(run.id)
            messages.success(request, f"Benchmark run '{run.title}' started and executed successfully.")
        else:
            execute_benchmark_run_task.delay(run.id)
            messages.success(request, f"Benchmark run '{run.title}' queued for async background execution.")

        return redirect('benchmarks:detail', pk=run.id)

    datasets = Dataset.objects.prefetch_related('versions').filter(is_public=True)
    models_list = AIModel.objects.select_related('provider').filter(is_active=True)

    return render(request, 'benchmarks/create.html', {
        'datasets': datasets,
        'models_list': models_list,
    })

def benchmark_list_view(request):
    runs = BenchmarkRun.objects.select_related('user', 'dataset_version__dataset').prefetch_related('target_models').order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        runs = runs.filter(status=status_filter)

    return render(request, 'benchmarks/list.html', {
        'runs': runs,
        'status_filter': status_filter or '',
        'status_choices': BenchmarkRun.STATUS_CHOICES,
    })

def benchmark_detail_view(request, pk):
    run = get_object_or_404(
        BenchmarkRun.objects.select_related('user', 'dataset_version__dataset').prefetch_related('run_models__model'),
        pk=pk
    )

    responses = ModelResponse.objects.filter(benchmark_run=run).select_related(
        'model', 'question', 'evaluation'
    ).prefetch_related('evaluation__error_categories')

    # Category & Question filter
    cat_filter = request.GET.get('category')
    hallucination_only = request.GET.get('hallucinated') == 'true'

    if cat_filter:
        responses = responses.filter(question__category=cat_filter)
    if hallucination_only:
        responses = responses.filter(evaluation__is_hallucination=True)

    context = {
        'run': run,
        'responses': responses[:100],  # paginated view
        'run_models': run.run_models.all(),
        'categories': Dataset.CATEGORY_CHOICES,
        'selected_category': cat_filter or '',
        'hallucination_only': hallucination_only,
    }
    return render(request, 'benchmarks/detail.html', context)

@login_required
def benchmark_cancel_view(request, pk):
    run = get_object_or_404(BenchmarkRun, pk=pk, user=request.user)
    if run.status == 'running':
        run.status = 'cancelled'
        run.save()
        messages.info(request, "Benchmark run cancellation requested.")
    return redirect('benchmarks:detail', pk=run.id)

def benchmark_progress_api(request, pk):
    run = get_object_or_404(BenchmarkRun, pk=pk)
    return JsonResponse({
        'id': run.id,
        'status': run.status,
        'completed_questions': run.completed_questions,
        'total_questions': run.total_questions,
        'progress_percentage': run.progress_percentage,
        'error_count': run.error_count,
        'overall_metrics': run.overall_metrics,
    })

def benchmark_compare_view(request):
    run_ids = request.GET.getlist('run_id')
    if not run_ids:
        # Default select latest 2 completed runs
        run_ids = list(BenchmarkRun.objects.filter(status='completed').order_by('-created_at').values_list('id', flat=True)[:3])

    runs = BenchmarkRun.objects.filter(id__in=run_ids).select_related('dataset_version__dataset').prefetch_related('run_models__model')

    return render(request, 'benchmarks/compare.html', {
        'runs': runs,
        'all_runs': BenchmarkRun.objects.filter(status='completed').order_by('-created_at')[:20],
        'selected_ids': [int(i) for i in run_ids if str(i).isdigit()]
    })
