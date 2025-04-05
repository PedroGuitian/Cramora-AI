from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cram/', views.cram_sheet, name='cram_sheet')
]