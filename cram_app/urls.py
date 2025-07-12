from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('cramora/', views.landing_page, name='landing_page'),
    path('signup/', views.signup_view, name='signup'),
    path("login/", CustomLoginView.as_view(), name="login"), 
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path('hubs/new/', views.create_cram_hub, name='create_cram_hub'),
    path("create-cram-hub/", views.create_cram_hub, name="create_cram_hub"),
    path('my-cram-hubs/', views.my_cram_hubs, name='my_cram_hubs'),
    path("cram-hub/<int:hub_id>/", views.cram_hub_dashboard, name="cram_hub_dashboard"),
    path("cram-hub/<int:hub_id>/generate-cram-sheet/", views.generate_cram_sheet, name="generate_cram_sheet"),
    path("cram-hub/<int:hub_id>/generate-test-questions/", views.generate_test_questions, name="generate_test_questions"),
    path('cram-hub/<int:hub_id>/add-files/', views.add_files_to_hub, name='add_files_to_hub'),
    path("question/<int:question_id>/edit/", views.edit_question, name="edit_question"),
    path("question/<int:question_id>/delete/", views.delete_question, name="delete_question"),
    path('cram-hub/<int:hub_id>/add-question/', views.add_question, name='add_question'),
    path("cram-hub/<int:hub_id>/quiz/", views.take_quiz, name="take_quiz"),
    path('cram_hub/<int:hub_id>/delete/', views.delete_cram_hub, name='delete_cram_hub'),
]
