from django.db import models
from django.contrib.auth.models import User
import random

class CramSheet(models.Model):
    cram_hub = models.OneToOneField('CramHub', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    questions_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.cram_hub.user.username}"

class TestQuestion(models.Model):
    cram_hub = models.ForeignKey('CramHub', on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=255)
    wrong_answers = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def get_all_choices(self):
        choices = self.wrong_answers + [self.correct_answer]
        random.shuffle(choices)
        return choices

    def __str__(self):
        return f"Question for: {self.cram_hub.title}"

    class Meta:
        ordering = ['created_at']

class CramHub(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class UploadedFile(models.Model):
    cram_hub = models.ForeignKey(CramHub, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploaded_files/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename
