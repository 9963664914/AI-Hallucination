from django.contrib import admin
from .models import ModelProvider, AIModel

class AIModelInline(admin.TabularInline):
    model = AIModel
    extra = 1

@admin.register(ModelProvider)
class ModelProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_type', 'api_key_env_var', 'is_active', 'created_at')
    list_filter = ('provider_type', 'is_active')
    search_fields = ('name', 'api_key_env_var')
    inlines = [AIModelInline]

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_identifier', 'provider', 'temperature', 'max_tokens', 'is_active')
    list_filter = ('provider', 'is_active')
    search_fields = ('name', 'model_identifier', 'description')
