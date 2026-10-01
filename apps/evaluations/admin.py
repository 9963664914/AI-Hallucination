from django.contrib import admin
from .models import ErrorCategory, EvaluationResult, EvaluationEvidence

class EvaluationEvidenceInline(admin.TabularInline):
    model = EvaluationEvidence
    extra = 0

@admin.register(ErrorCategory)
class ErrorCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}

@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'model_response', 'composite_score', 'factuality_score',
        'semantic_similarity_score', 'is_hallucination', 'is_abstained', 'created_at'
    )
    list_filter = ('is_hallucination', 'is_abstained', 'error_categories')
    search_fields = ('evaluator_reasoning', 'model_response__response_text')
    inlines = [EvaluationEvidenceInline]

@admin.register(EvaluationEvidence)
class EvaluationEvidenceAdmin(admin.ModelAdmin):
    list_display = ('evaluation_result', 'status', 'confidence', 'claim_preview')
    list_filter = ('status',)

    def claim_preview(self, obj):
        return obj.claim_text[:60]
    claim_preview.short_description = 'Claim'
