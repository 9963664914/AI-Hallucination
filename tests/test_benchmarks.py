from django.test import TestCase
from django.contrib.auth.models import User
from apps.datasets.models import Dataset, DatasetVersion, BenchmarkQuestion
from apps.models_registry.models import ModelProvider, AIModel
from apps.benchmarks.models import BenchmarkRun, BenchmarkRunModel, ModelResponse
from apps.benchmarks.tasks import run_benchmark_execution

class BenchmarksExecutionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='evaluer', password='Password123!')
        
        self.dataset = Dataset.objects.create(
            name="Bench Test Dataset",
            description="Testing execution",
            category="general_knowledge",
            created_by=self.user
        )
        self.version = DatasetVersion.objects.create(dataset=self.dataset, version="v1.0")
        
        self.question1 = BenchmarkQuestion.objects.create(
            dataset_version=self.version,
            question_text="What is the capital of Japan?",
            expected_answer="Tokyo",
            category="general_knowledge"
        )
        self.question2 = BenchmarkQuestion.objects.create(
            dataset_version=self.version,
            question_text="What happens in year 3000?",
            expected_answer="Unanswerable",
            is_unanswerable=True,
            category="unanswerable"
        )

        self.provider = ModelProvider.objects.create(name="Mock Test Provider", provider_type="mock")
        self.model = AIModel.objects.create(
            provider=self.provider,
            name="Mock Accurate Model",
            model_identifier="mock-accurate-v1"
        )

        self.run = BenchmarkRun.objects.create(
            title="TestCase Benchmark Run",
            user=self.user,
            dataset_version=self.version
        )
        BenchmarkRunModel.objects.create(benchmark_run=self.run, model=self.model)

    def test_benchmark_execution_end_to_end(self):
        run_benchmark_execution(self.run.id)
        
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, 'completed')
        self.assertEqual(self.run.completed_questions, 2)
        self.assertIn('hallucination_rate', self.run.overall_metrics)
        
        responses = ModelResponse.objects.filter(benchmark_run=self.run)
        self.assertEqual(responses.count(), 2)
        
        for r in responses:
            self.assertTrue(hasattr(r, 'evaluation'))
            self.assertIsNotNone(r.evaluation.composite_score)
