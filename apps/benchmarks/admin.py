from django.contrib import admin
from .models import BenchmarkRun, BenchmarkRunModel, ModelResponse

class BenchmarkRunModelInline(admin.TabularInline):
    model = BenchmarkRunModel
    extra = 1

@admin.register(BenchmarkRun)
class BenchmarkRunAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'dataset_version', 'status', 'total_questions', 'completed_questions', 'error_count', 'created_at')
    list_filter = ('status', 'dataset_version', 'created_at')
    search_fields = ('title', 'user__username')
    inlines = [BenchmarkRunModelInline]

@admin.register(ModelResponse)
class ModelResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'benchmark_run', 'model', 'question', 'latency_ms', 'is_error', 'created_at')
    list_filter = ('is_error', 'model', 'benchmark_run')
    search_fields = ('prompt', 'response_text', 'error_message')
