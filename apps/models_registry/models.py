import os
from django.db import models

class ModelProvider(models.Model):
    PROVIDER_TYPES = [
        ('mock', 'Mock Provider (Offline Development & Testing)'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('google', 'Google Gemini'),
        ('custom', 'Custom HTTP Endpoint / Local Ollama'),
    ]

    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES, default='mock')
    base_url = models.CharField(max_length=255, blank=True, default='', help_text="API Endpoint URL (if applicable)")
    api_key_env_var = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Environment variable name storing secret API key (e.g. OPENAI_API_KEY)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_api_key(self):
        """Resolves secret API key safely from environment variable without saving raw keys in DB."""
        if not self.api_key_env_var:
            return None
        return os.environ.get(self.api_key_env_var, '')

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"

class AIModel(models.Model):
    provider = models.ForeignKey(ModelProvider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=150, help_text="Human readable model title")
    model_identifier = models.CharField(max_length=150, help_text="Exact API model string e.g. gpt-4o, mock-accurate-v1")
    description = models.TextField(blank=True, default='')
    temperature = models.FloatField(default=0.0)
    max_tokens = models.IntegerField(default=1024)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider', 'name']
        unique_together = ('provider', 'model_identifier')

    def __str__(self):
        return f"{self.name} [{self.model_identifier}]"
