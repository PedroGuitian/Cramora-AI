from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('hubs/new/', views.create_cram_hub, name='create_cram_hub'),
    path("create-cram-hub/", views.create_cram_hub, name="create_cram_hub"),
    path("cram-hub/<int:hub_id>/", views.cram_hub_dashboard, name="cram_hub_dashboard"),
    path("cram-hub/<int:hub_id>/generate-cram-sheet/", views.generate_cram_sheet, name="generate_cram_sheet"),
    path("cram-hub/<int:hub_id>/generate-test-questions/", views.generate_test_questions, name="generate_test_questions")
]
