from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.datasets.models import Dataset, DatasetVersion, BenchmarkQuestion

class DatasetsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='datauser', password='Password123!')
        self.dataset = Dataset.objects.create(
            name="Test Science Dataset",
            description="Testing dataset creation",
            category="science",
            created_by=self.user
        )
        self.version = DatasetVersion.objects.create(
            dataset=self.dataset,
            version="v1.0"
        )
        self.question = BenchmarkQuestion.objects.create(
            dataset_version=self.version,
            question_text="What is H2O?",
            expected_answer="Water",
            category="science",
            difficulty="easy"
        )

    def test_dataset_list_view(self):
        response = self.client.get(reverse('datasets:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Science Dataset")

    def test_dataset_detail_view(self):
        response = self.client.get(reverse('datasets:detail', kwargs={'slug': self.dataset.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What is H2O?")

    def test_dataset_export_json(self):
        url = reverse('datasets:export', kwargs={'slug': self.dataset.slug, 'version_id': self.version.id})
        response = self.client.get(url + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_dataset_export_csv(self):
        url = reverse('datasets:export', kwargs={'slug': self.dataset.slug, 'version_id': self.version.id})
        response = self.client.get(url + '?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
