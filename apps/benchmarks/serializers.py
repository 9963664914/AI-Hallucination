from rest_framework import serializers
from .models import BenchmarkRun, BenchmarkRunModel, ModelResponse
from apps.evaluations.serializers import EvaluationResultSerializer
from apps.models_registry.serializers import AIModelSerializer
from apps.datasets.serializers import DatasetVersionSerializer

class BenchmarkRunModelSerializer(serializers.ModelSerializer):
    model = AIModelSerializer(read_only=True)

    class Meta:
        model = BenchmarkRunModel
        fields = ['id', 'model', 'metrics']

class ModelResponseSerializer(serializers.ModelSerializer):
    evaluation = EvaluationResultSerializer(read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    expected_answer = serializers.CharField(source='question.expected_answer', read_only=True)

    class Meta:
        model = ModelResponse
        fields = [
            'id', 'benchmark_run', 'model', 'model_name', 'question',
            'question_text', 'expected_answer', 'prompt', 'response_text',
            'latency_ms', 'token_count', 'is_error', 'error_message',
            'evaluation', 'created_at'
        ]

class BenchmarkRunSerializer(serializers.ModelSerializer):
    run_models = BenchmarkRunModelSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = BenchmarkRun
        fields = [
            'id', 'title', 'user', 'user_username', 'dataset_version',
            'status', 'configuration', 'total_questions', 'completed_questions',
            'error_count', 'start_time', 'end_time', 'overall_metrics',
            'run_models', 'progress_percentage', 'created_at', 'updated_at'
        ]
