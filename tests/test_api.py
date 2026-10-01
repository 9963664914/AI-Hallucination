from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from apps.datasets.models import Dataset, DatasetVersion

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='apiuser', password='Password123!')
        self.dataset = Dataset.objects.create(
            name="API Test Dataset",
            description="Testing API endpoints",
            category="general_knowledge",
            created_by=self.user
        )

    def test_datasets_api_list(self):
        response = self.client.get('/api/v1/datasets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_openapi_schema_endpoint(self):
        response = self.client.get('/api/v1/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_docs_endpoint(self):
        response = self.client.get('/api/v1/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
