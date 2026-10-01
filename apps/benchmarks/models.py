from django.db import models
from django.contrib.auth.models import User
from apps.datasets.models import DatasetVersion, BenchmarkQuestion
from apps.models_registry.models import AIModel

class BenchmarkRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dataset_version = models.ForeignKey(DatasetVersion, on_delete=models.CASCADE, related_name='benchmark_runs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    configuration = models.JSONField(default=dict, help_text="Evaluator selection & parameters")
    
    total_questions = models.IntegerField(default=0)
    completed_questions = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    overall_metrics = models.JSONField(default=dict, blank=True)

    target_models = models.ManyToManyField(AIModel, through='BenchmarkRunModel', related_name='benchmark_runs')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def progress_percentage(self):
        if self.total_questions == 0:
            return 0
        return int((self.completed_questions / self.total_questions) * 100)

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}] - {self.dataset_version}"

class BenchmarkRunModel(models.Model):
    benchmark_run = models.ForeignKey(BenchmarkRun, on_delete=models.CASCADE, related_name='run_models')
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('benchmark_run', 'model')

    def __str__(self):
        return f"{self.model.name} in {self.benchmark_run.title}"

class ModelResponse(models.Model):
    benchmark_run = models.ForeignKey(BenchmarkRun, on_delete=models.CASCADE, related_name='responses')
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    question = models.ForeignKey(BenchmarkQuestion, on_delete=models.CASCADE, related_name='responses')
    
    prompt = models.TextField()
    response_text = models.TextField()
    latency_ms = models.FloatField(default=0.0)
    token_count = models.IntegerField(default=0)
    
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_id', 'model_id']
        indexes = [
            models.Index(fields=['benchmark_run', 'model']),
            models.Index(fields=['question', 'is_error']),
        ]

    def __str__(self):
        return f"Response by {self.model.name} to Question #{self.question_id}"
