from rest_framework import serializers
from .models import ErrorCategory, EvaluationResult, EvaluationEvidence

class ErrorCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorCategory
        fields = ['id', 'name', 'code', 'description']

class EvaluationEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationEvidence
        fields = ['id', 'claim_text', 'status', 'reasoning', 'confidence']

class EvaluationResultSerializer(serializers.ModelSerializer):
    error_categories = ErrorCategorySerializer(many=True, read_only=True)
    evidences = EvaluationEvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationResult
        fields = [
            'id', 'model_response', 'exact_match_score', 'semantic_similarity_score',
            'factuality_score', 'citation_score', 'composite_score',
            'is_hallucination', 'is_abstained', 'is_correct_abstention',
            'evaluator_reasoning', 'error_categories', 'evidences', 'created_at'
        ]
