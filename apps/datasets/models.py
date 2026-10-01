from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Dataset(models.Model):
    CATEGORY_CHOICES = [
        ('general_knowledge', 'General Knowledge'),
        ('science', 'Science'),
        ('history', 'History'),
        ('geography', 'Geography'),
        ('mathematics', 'Mathematics'),
        ('medicine', 'Medicine'),
        ('law', 'Law'),
        ('technology', 'Technology'),
        ('current_events', 'Current Events'),
        ('unanswerable', 'Unanswerable / Insufficient Information'),
    ]

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general_knowledge')
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class DatasetVersion(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=50, help_text="e.g. v1.0, v1.1")
    changelog = models.TextField(blank=True, default="Initial version release.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('dataset', 'version')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dataset.name} ({self.version})"

class BenchmarkQuestion(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    dataset_version = models.ForeignKey(DatasetVersion, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    expected_answer = models.TextField()
    reference_source = models.TextField(blank=True, default="", help_text="Trusted source or citation URL")
    category = models.CharField(max_length=50, choices=Dataset.CATEGORY_CHOICES, default='general_knowledge')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True)
    is_factual = models.BooleanField(default=True, help_text="Whether this question has a verifiable factual answer")
    is_unanswerable = models.BooleanField(default=False, help_text="Tests if the model correctly abstains when information is missing")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['category', 'difficulty']),
            models.Index(fields=['is_factual', 'is_unanswerable']),
        ]

    def __str__(self):
        return f"[{self.category}] {self.question_text[:60]}..."
