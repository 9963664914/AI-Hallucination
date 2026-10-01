import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q
from apps.benchmarks.models import BenchmarkRun, BenchmarkRunModel, ModelResponse
from apps.datasets.models import Dataset, DatasetVersion, BenchmarkQuestion
from apps.models_registry.models import AIModel
from apps.evaluations.models import EvaluationResult, ErrorCategory

def landing_view(request):
    latest_runs = BenchmarkRun.objects.filter(status='completed').order_by('-created_at')[:5]
    total_runs = BenchmarkRun.objects.filter(status='completed').count()
    total_questions = BenchmarkQuestion.objects.count()
    total_models = AIModel.objects.filter(is_active=True).count()

    return render(request, 'landing.html', {
        'latest_runs': latest_runs,
        'total_runs': total_runs,
        'total_questions': total_questions,
        'total_models': total_models,
    })

def methodology_view(request):
    error_categories = ErrorCategory.objects.all()
    return render(request, 'methodology.html', {
        'error_categories': error_categories
    })

def dashboard_index_view(request):
    completed_runs = BenchmarkRun.objects.filter(status='completed')

    # Filter parameters
    dataset_id = request.GET.get('dataset')
    model_id = request.GET.get('model')
    category = request.GET.get('category')

    responses_qs = ModelResponse.objects.filter(benchmark_run__status='completed').select_related(
        'evaluation', 'model', 'question', 'benchmark_run'
    )

    if dataset_id:
        responses_qs = responses_qs.filter(question__dataset_version__dataset_id=dataset_id)
    if model_id:
        responses_qs = responses_qs.filter(model_id=model_id)
    if category:
        responses_qs = responses_qs.filter(question__category=category)

    total_evaluated = responses_qs.exclude(evaluation__isnull=True).count()
    
    if total_evaluated > 0:
        total_hallucinations = responses_qs.filter(evaluation__is_hallucination=True).count()
        hallucination_rate = round((total_hallucinations / total_evaluated) * 100, 2)
        factual_accuracy = round(100 - hallucination_rate, 2)
        avg_composite = responses_qs.aggregate(Avg('evaluation__composite_score'))['evaluation__composite_score__avg'] or 0.0
        avg_composite = round(avg_composite, 4)

        unanswerable_qs = responses_qs.filter(question__is_unanswerable=True)
        unanswerable_count = unanswerable_qs.count()
        if unanswerable_count > 0:
            correct_abstentions = unanswerable_qs.filter(evaluation__is_abstained=True).count()
            abstention_accuracy = round((correct_abstentions / unanswerable_count) * 100, 2)
        else:
            abstention_accuracy = 100.0
    else:
        hallucination_rate = 0.0
        factual_accuracy = 0.0
        avg_composite = 0.0
        abstention_accuracy = 0.0

    # Model comparison data for Chart.js
    active_models = AIModel.objects.filter(is_active=True)
    model_names = []
    model_hallucination_rates = []
    model_accuracy_rates = []
    model_composite_scores = []

    for m in active_models:
        m_responses = responses_qs.filter(model=m, evaluation__isnull=False)
        m_count = m_responses.count()
        if m_count > 0:
            m_h = m_responses.filter(evaluation__is_hallucination=True).count()
            m_hrate = round((m_h / m_count) * 100, 2)
            m_acc = round(100 - m_hrate, 2)
            m_comp = round(m_responses.aggregate(Avg('evaluation__composite_score'))['evaluation__composite_score__avg'] or 0.0, 3)
            
            model_names.append(m.name)
            model_hallucination_rates.append(m_hrate)
            model_accuracy_rates.append(m_acc)
            model_composite_scores.append(m_comp)

    # Error category distribution
    error_cats = ErrorCategory.objects.all()
    error_labels = []
    error_counts = []
    for cat in error_cats:
        c_count = responses_qs.filter(evaluation__error_categories=cat).count()
        if c_count > 0:
            error_labels.append(cat.name)
            error_counts.append(c_count)

    # Category performance breakdown
    categories_data = []
    for cat_code, cat_name in Dataset.CATEGORY_CHOICES:
        cat_resp = responses_qs.filter(question__category=cat_code, evaluation__isnull=False)
        c_tot = cat_resp.count()
        if c_tot > 0:
            c_hall = cat_resp.filter(evaluation__is_hallucination=True).count()
            c_hrate = round((c_hall / c_tot) * 100, 2)
            categories_data.append({'name': cat_name, 'count': c_tot, 'hallucination_rate': c_hrate})

    context = {
        'total_evaluated': total_evaluated,
        'hallucination_rate': hallucination_rate,
        'factual_accuracy': factual_accuracy,
        'avg_composite': avg_composite,
        'abstention_accuracy': abstention_accuracy,
        'latest_runs': completed_runs[:10],
        'datasets': Dataset.objects.filter(is_public=True),
        'models': active_models,
        'categories': Dataset.CATEGORY_CHOICES,
        'selected_dataset': dataset_id or '',
        'selected_model': model_id or '',
        'selected_category': category or '',
        'chart_data_json': json.dumps({
            'model_names': model_names,
            'model_hallucination_rates': model_hallucination_rates,
            'model_accuracy_rates': model_accuracy_rates,
            'model_composite_scores': model_composite_scores,
            'error_labels': error_labels,
            'error_counts': error_counts,
            'category_names': [c['name'] for c in categories_data],
            'category_hallucination_rates': [c['hallucination_rate'] for c in categories_data],
        })
    }
    return render(request, 'dashboard/index.html', context)

def question_analysis_view(request, response_id):
    model_response = get_object_or_404(
        ModelResponse.objects.select_related('model', 'question', 'benchmark_run', 'evaluation'),
        pk=response_id
    )

    evaluation = getattr(model_response, 'evaluation', None)
    evidences = evaluation.evidences.all() if evaluation else []
    error_categories = evaluation.error_categories.all() if evaluation else []

    return render(request, 'dashboard/question_analysis.html', {
        'response': model_response,
        'question': model_response.question,
        'evaluation': evaluation,
        'evidences': evidences,
        'error_categories': error_categories,
    })
