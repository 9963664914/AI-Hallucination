import json
import csv
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, permissions
from .models import Dataset, DatasetVersion, BenchmarkQuestion
from .serializers import DatasetSerializer, DatasetVersionSerializer, BenchmarkQuestionSerializer

# DRF ViewSets
class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class DatasetVersionViewSet(viewsets.ModelViewSet):
    queryset = DatasetVersion.objects.all()
    serializer_class = DatasetVersionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class BenchmarkQuestionViewSet(viewsets.ModelViewSet):
    queryset = BenchmarkQuestion.objects.all()
    serializer_class = BenchmarkQuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['category', 'difficulty', 'is_factual', 'is_unanswerable', 'dataset_version']

# Web Template Views
def dataset_list_view(request):
    datasets = Dataset.objects.prefetch_related('versions').order_by('-created_at')
    category_filter = request.GET.get('category')
    if category_filter:
        datasets = datasets.filter(category=category_filter)
    
    categories = Dataset.CATEGORY_CHOICES
    return render(request, 'datasets/list.html', {
        'datasets': datasets,
        'categories': categories,
        'selected_category': category_filter,
    })

def dataset_detail_view(request, slug):
    dataset = get_object_or_404(Dataset.objects.prefetch_related('versions'), slug=slug)
    selected_version_id = request.GET.get('version')
    
    if selected_version_id:
        version = get_object_or_404(DatasetVersion, id=selected_version_id, dataset=dataset)
    else:
        version = dataset.versions.filter(is_active=True).first() or dataset.versions.first()
        
    questions = version.questions.all() if version else []
    
    # Question level search & category filters
    q_search = request.GET.get('q')
    category_filter = request.GET.get('category')
    difficulty_filter = request.GET.get('difficulty')
    
    if questions:
        if q_search:
            questions = questions.filter(question_text__icontains=q_search)
        if category_filter:
            questions = questions.filter(category=category_filter)
        if difficulty_filter:
            questions = questions.filter(difficulty=difficulty_filter)

    return render(request, 'datasets/detail.html', {
        'dataset': dataset,
        'active_version': version,
        'questions': questions,
        'categories': Dataset.CATEGORY_CHOICES,
        'difficulties': BenchmarkQuestion.DIFFICULTY_CHOICES,
        'q_search': q_search or '',
        'selected_category': category_filter or '',
        'selected_difficulty': difficulty_filter or '',
    })

@login_required
def dataset_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category = request.POST.get('category', 'general_knowledge')
        is_public = request.POST.get('is_public') == 'on'

        if Dataset.objects.filter(name=name).exists():
            messages.error(request, f"A dataset with name '{name}' already exists.")
            return redirect('datasets:create')

        dataset = Dataset.objects.create(
            name=name,
            description=description,
            category=category,
            is_public=is_public,
            created_by=request.user
        )

        version = DatasetVersion.objects.create(
            dataset=dataset,
            version="v1.0",
            changelog="Initial release"
        )

        # Process bulk dataset upload if provided (JSON or CSV)
        file_obj = request.FILES.get('dataset_file')
        if file_obj:
            try:
                content = file_obj.read().decode('utf-8')
                questions_created = 0

                if file_obj.name.endswith('.json'):
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            BenchmarkQuestion.objects.create(
                                dataset_version=version,
                                question_text=item.get('question_text', item.get('question', '')),
                                expected_answer=item.get('expected_answer', item.get('reference', '')),
                                reference_source=item.get('reference_source', item.get('source', '')),
                                category=item.get('category', dataset.category),
                                difficulty=item.get('difficulty', 'medium'),
                                is_factual=item.get('is_factual', True),
                                is_unanswerable=item.get('is_unanswerable', False),
                                tags=item.get('tags', [])
                            )
                            questions_created += 1

                elif file_obj.name.endswith('.csv'):
                    io_string = io.StringIO(content)
                    reader = csv.DictReader(io_string)
                    for row in reader:
                        BenchmarkQuestion.objects.create(
                            dataset_version=version,
                            question_text=row.get('question_text') or row.get('question', ''),
                            expected_answer=row.get('expected_answer') or row.get('reference', ''),
                            reference_source=row.get('reference_source') or row.get('source', ''),
                            category=row.get('category') or dataset.category,
                            difficulty=row.get('difficulty', 'medium'),
                            is_factual=row.get('is_factual', 'True').lower() in ('true', '1'),
                            is_unanswerable=row.get('is_unanswerable', 'False').lower() in ('true', '1'),
                        )
                        questions_created += 1
                
                messages.success(request, f"Dataset created with {questions_created} imported questions.")
            except Exception as e:
                messages.warning(request, f"Dataset created, but error parsing upload file: {str(e)}")
        else:
            messages.success(request, "Dataset created successfully. You can now add benchmark questions.")

        return redirect('datasets:detail', slug=dataset.slug)

    return render(request, 'datasets/form.html', {
        'categories': Dataset.CATEGORY_CHOICES
    })

def export_dataset_view(request, slug, version_id):
    dataset = get_object_or_404(Dataset, slug=slug)
    version = get_object_or_404(DatasetVersion, id=version_id, dataset=dataset)
    export_format = request.GET.get('format', 'json').lower()

    questions = version.questions.all()

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{dataset.slug}_{version.version}.csv"'
        writer = csv.writer(response)
        writer.writerow(['id', 'question_text', 'expected_answer', 'reference_source', 'category', 'difficulty', 'is_factual', 'is_unanswerable'])
        for q in questions:
            writer.writerow([q.id, q.question_text, q.expected_answer, q.reference_source, q.category, q.difficulty, q.is_factual, q.is_unanswerable])
        return response
    else:
        data = {
            'dataset_name': dataset.name,
            'version': version.version,
            'category': dataset.category,
            'questions': [
                {
                    'id': q.id,
                    'question_text': q.question_text,
                    'expected_answer': q.expected_answer,
                    'reference_source': q.reference_source,
                    'category': q.category,
                    'difficulty': q.difficulty,
                    'is_factual': q.is_factual,
                    'is_unanswerable': q.is_unanswerable,
                    'tags': q.tags
                } for q in questions
            ]
        }
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{dataset.slug}_{version.version}.json"'
        return response
