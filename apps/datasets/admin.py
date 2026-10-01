from django.contrib import admin
from .models import Dataset, DatasetVersion, BenchmarkQuestion

class DatasetVersionInline(admin.TabularInline):
    model = DatasetVersion
    extra = 1

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_public', 'created_by', 'created_at')
    list_filter = ('category', 'is_public', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [DatasetVersionInline]

@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'version', 'is_active', 'created_at', 'get_question_count')
    list_filter = ('is_active', 'dataset')
    search_fields = ('version', 'dataset__name')

    def get_question_count(self, obj):
        return obj.questions.count()
    get_question_count.short_description = 'Questions'

@admin.register(BenchmarkQuestion)
class BenchmarkQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_preview', 'category', 'difficulty', 'is_factual', 'is_unanswerable', 'dataset_version')
    list_filter = ('category', 'difficulty', 'is_factual', 'is_unanswerable', 'dataset_version')
    search_fields = ('question_text', 'expected_answer', 'reference_source')

    def question_preview(self, obj):
        return obj.question_text[:80]
    question_preview.short_description = 'Question'
