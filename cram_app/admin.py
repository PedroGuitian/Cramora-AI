from django.contrib import admin
from .models import CramHub, CramSheet, UploadedFile, TestQuestion

admin.site.register(CramHub)
admin.site.register(CramSheet)
admin.site.register(UploadedFile)
admin.site.register(TestQuestion)

# Register your models here.
