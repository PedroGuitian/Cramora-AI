from django.db import models
import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashes password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # You can require first_name or last_name here if needed

    def __str__(self):
        return self.email

class CramSheet(models.Model):
    cram_hub = models.OneToOneField('CramHub', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    questions_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.email}"

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.email}"

class UploadedFile(models.Model):
    cram_hub = models.ForeignKey(CramHub, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploaded_files/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename
