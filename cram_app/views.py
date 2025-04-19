from openai import OpenAI
import os
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.storage import default_storage
from django.utils.text import slugify

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
def generate_questions(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)

    if request.method == "POST":
        prompt = f"""
        Generate 5 multiple-choice quiz questions based on the following cram sheet. 
        Each question should have a "question", a "correct_answer", and a list of exactly three "wrong_answers".

        Return the questions in JSON format like this:
        [
          {{
            "question": "What does CPU stand for?",
            "correct_answer": "Central Processing Unit",
            "wrong_answers": ["Computer Performance Unit", "Central Performance Utility", "Compute Processor Unit"]
          }},
          ...
        ]

        Cram Sheet:
        {sheet.content}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a quiz generator AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()

            # Remove ```json or ``` if present
            if content.startswith("```"):
                content = content.strip("`")
                content = content.replace("json", "", 1).strip()

            questions = json.loads(content)

            for q in questions:
                if not TestQuestion.objects.filter(cram_sheet=sheet, question_text=q["question"]).exists():
                    TestQuestion.objects.create(
                        cram_sheet=sheet,
                        question_text=q["question"],
                        correct_answer=q["correct_answer"],
                        wrong_answers=q["wrong_answers"]
                    )

            return redirect("view_questions", sheet_id=sheet.id)

        except json.JSONDecodeError:
            return HttpResponseBadRequest("Failed to parse question JSON.")
        except Exception as e:
            return HttpResponseBadRequest(f"Something went wrong: {e}")

    return redirect("view_questions", sheet_id=sheet.id)