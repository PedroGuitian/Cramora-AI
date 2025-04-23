import os, json
import tiktoken
import fitz
from .forms import TestQuestionForm, EditTestQuestionForm
from openai import OpenAI
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .models import CramHub, UploadedFile, CramSheet, TestQuestion

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CustomLoginView(LoginView):
    template_name = 'cram_app/login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'  # Redirect to login after logout

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "cram_app/signup.html", {"form": form})

def home(request):
    return render(request, "cram_app/home.html")

@login_required
def cram_hub_dashboard(request, hub_id):
    hub = get_object_or_404(CramHub, id=hub_id, user=request.user)
    return render(request, "cram_app/cram_hub_dashboard.html", {
        "hub": hub,
        "questions": hub.questions.all(),
        "show_questions": hub.questions.exists()
    })

@login_required
def create_cram_hub(request):
    if request.method == "POST":
        title = request.POST.get("title")
        files = request.FILES.getlist("files")

        if not title or not files:
            return render(request, "cram_app/create_cram_hub.html", {
                "error": "Please provide a title and upload at least one file."
            })

        hub = CramHub.objects.create(user=request.user, title=title)

        for f in files:
            filename = default_storage.save(f"uploaded_files/{slugify(f.name)}", f)
            UploadedFile.objects.create(
                cram_hub=hub,
                file=filename,
                original_filename=f.name
            )

        return redirect("cram_hub_dashboard", hub_id=hub.id)

    return render(request, "cram_app/create_cram_hub.html")

@login_required
def generate_cram_sheet(request, hub_id):
    hub = get_object_or_404(CramHub, id=hub_id, user=request.user)
    files = hub.files.all()
    full_text = ""

    for file in files:
        try:
            ext = os.path.splitext(file.original_filename)[1].lower()

            if ext == ".pdf":
                print(f"📄 Extracting from PDF: {file.original_filename}")
                with file.file.open("rb") as f:
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    for page in doc:
                        full_text += page.get_text()
            else:
                with file.file.open("rb") as f:
                    content = f.read()
                    full_text += content.decode("utf-8", errors="ignore") + "\n"

        except Exception as e:
            print(f"❌ Could not process {file.original_filename}: {e}")

    prompt = f"""
        You are a helpful study assistant. Summarize the following study material into a structured and compact 1-page cram sheet.

        Format:
        ## Overview
        ## Key Areas to Study
        ## Important Definitions
        ## Key Facts or Concepts
        ## Final Tips (Optional)

        Rules:
        - Do not use quotation marks
        - Avoid extra spacing or blank lines
        - Use markdown formatting only

        Study material:
        {full_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful study assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=700
    )

    content = response.choices[0].message.content.strip()
    cram_sheet = CramSheet.objects.create(
        cram_hub=hub,
        title=f"Cram Sheet - {hub.title}",
        content=content
    )

    return redirect("cram_hub_dashboard", hub_id=hub.id)

def estimate_tokens(text):
    try:
        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except Exception:
        return int(len(text) / 4)  # fallback

@login_required
def generate_test_questions(request, hub_id):
    hub = get_object_or_404(CramHub, id=hub_id, user=request.user)
    files = hub.files.all()
    full_text = ""

    for file in files:
        try:
            ext = os.path.splitext(file.original_filename)[1].lower()

            if ext == ".pdf":
                with file.file.open("rb") as f:
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    for page in doc:
                        full_text += page.get_text()
            else:
                with file.file.open("rb") as f:
                    content = f.read()
                    try:
                        full_text += content.decode("utf-8", errors="ignore") + "\n"
                    except UnicodeDecodeError:
                        full_text += content.decode("latin-1") + "\n"

        except Exception:
            continue  # skip unreadable files silently

    # ✅ Limit input to ~10k tokens
    max_tokens = 10000
    if estimate_tokens(full_text) > max_tokens:
        full_text = full_text[:40000]  # ~10k tokens (approx)

    prompt = f"""
        Generate 10 multiple-choice questions based on this study material.
        Each question should include:
        - question
        - correct_answer
        - wrong_answers (3 total)

        Return in JSON format like this:
        [
          {{
            "question": "...",
            "correct_answer": "...",
            "wrong_answers": ["...", "...", "..."]
          }},
          ...
        ]

        Study material:
        {full_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a quiz generator AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.strip("`").replace("json", "").strip()

        if not content or not content.startswith("["):
            return HttpResponseBadRequest("Invalid AI response. Please check your input files and try again.")

        questions = json.loads(content)

        existing_texts = set(hub.questions.values_list("question_text", flat=True))
        
        for q in questions:
            if q["question"] not in existing_texts:
                TestQuestion.objects.create(
                    cram_hub=hub,
                    question_text=q["question"],
                    correct_answer=q["correct_answer"],
                    wrong_answers=q["wrong_answers"]
                )

        return render(request, "cram_app/cram_hub_dashboard.html", {
            "hub": hub,
            "questions": hub.questions.all(),
            "show_questions": True
        })

    except Exception:
        return HttpResponseBadRequest("Something went wrong while generating test questions. Please try again.")

@login_required
def my_cram_hubs(request):
    hubs = CramHub.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'cram_app/my_cram_hubs.html', {
        'hubs': hubs
    })

@login_required
def add_files_to_hub(request, hub_id):
    hub = get_object_or_404(CramHub, id=hub_id, user=request.user)

    if request.method == "POST":
        files = request.FILES.getlist("files")
        for f in files:
            filename = default_storage.save(f"uploaded_files/{slugify(f.name)}", f)
            UploadedFile.objects.create(
                cram_hub=hub,
                file=filename,
                original_filename=f.name
            )
        return redirect("cram_hub_dashboard", hub_id=hub.id)

@login_required
def edit_question(request, question_id):
    question = get_object_or_404(TestQuestion, id=question_id, cram_hub__user=request.user)

    if request.method == "POST":
        form = EditTestQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("cram_hub_dashboard", hub_id=question.cram_hub.id)
    else:
        form = EditTestQuestionForm(instance=question)

    return render(request, "cram_app/edit_questions.html", {
        "form": form,
        "question": question
    })

@login_required
@require_POST
def delete_question(request, question_id):
    question = get_object_or_404(TestQuestion, id=question_id, cram_hub__user=request.user)
    hub_id = question.cram_hub.id
    question.delete()
    return redirect("cram_hub_dashboard", hub_id=hub_id)
