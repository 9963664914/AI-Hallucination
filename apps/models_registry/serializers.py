from rest_framework import serializers
from .models import ModelProvider, AIModel

class ModelProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProvider
        fields = ['id', 'name', 'provider_type', 'base_url', 'api_key_env_var', 'is_active', 'created_at']

class AIModelSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)

    class Meta:
        model = AIModel
        fields = [
            'id', 'provider', 'provider_name', 'provider_type',
            'name', 'model_identifier', 'description',
            'temperature', 'max_tokens', 'is_active', 'created_at'
        ]
