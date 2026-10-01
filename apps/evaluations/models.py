from django.db import models

class ErrorCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Error Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class EvaluationResult(models.Model):
    model_response = models.OneToOneField(
        'benchmarks.ModelResponse',
        on_delete=models.CASCADE,
        related_name='evaluation'
    )
    exact_match_score = models.FloatField(default=0.0)
    semantic_similarity_score = models.FloatField(default=0.0)
    factuality_score = models.FloatField(default=0.0)
    citation_score = models.FloatField(default=0.0)
    composite_score = models.FloatField(default=0.0)
    
    is_hallucination = models.BooleanField(default=False)
    is_abstained = models.BooleanField(default=False)
    is_correct_abstention = models.BooleanField(default=False)
    
    evaluator_reasoning = models.TextField(blank=True, default='')
    error_categories = models.ManyToManyField(ErrorCategory, blank=True, related_name='evaluations')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "Hallucination" if self.is_hallucination else "Accurate"
        return f"Eval #{self.id} [{status}] - Score: {self.composite_score:.2f}"

class EvaluationEvidence(models.Model):
    STATUS_CHOICES = [
        ('supported', 'Supported by Reference'),
        ('unsupported', 'Unsupported Claim'),
        ('contradicted', 'Contradicts Reference'),
        ('unverifiable', 'Unverifiable / Citation Error'),
    ]

    evaluation_result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name='evidences')
    claim_text = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='supported')
    reasoning = models.TextField(blank=True, default='')
    confidence = models.FloatField(default=1.0)

    def __str__(self):
        return f"[{self.get_status_display()}] {self.claim_text[:50]}..."
