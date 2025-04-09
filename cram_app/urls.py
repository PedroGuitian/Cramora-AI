from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cram/', views.cram_sheet, name='cram_sheet'),
    path("signup/", views.signup_view, name="signup"),
    path('save/', views.save_cram_sheet, name='save_cram_sheet'),
    path('my-cram-sheets/', views.my_cram_sheets, name='my_cram_sheets')
]