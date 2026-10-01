from rest_framework import serializers
from .models import Dataset, DatasetVersion, BenchmarkQuestion

class BenchmarkQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkQuestion
        fields = [
            'id', 'dataset_version', 'question_text', 'expected_answer',
            'reference_source', 'category', 'difficulty', 'tags',
            'is_factual', 'is_unanswerable', 'created_at', 'updated_at'
        ]

class DatasetVersionSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source='questions.count', read_only=True)
    
    class Meta:
        model = DatasetVersion
        fields = ['id', 'dataset', 'version', 'changelog', 'is_active', 'question_count', 'created_at']

class DatasetSerializer(serializers.ModelSerializer):
    versions = DatasetVersionSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Dataset
        fields = [
            'id', 'name', 'slug', 'description', 'category',
            'is_public', 'created_by', 'created_by_username',
            'versions', 'created_at', 'updated_at'
        ]
