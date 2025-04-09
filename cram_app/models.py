from django.db import models
from django.contrib.auth.models import User

class CramSheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    questions_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class TestQuestion(models.Model):
    cram_sheet = models.ForeignKey('CramSheet', on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q for: {self.cram_sheet.title}"