from openai import OpenAI
import os
import markdown
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CramSheet, TestQuestion
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder
from .forms import TestQuestionForm, EditTestQuestionForm

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

def cram_sheet(request):
    summary = None

    if request.method == "POST":
        raw_text = request.POST.get("text")

        if raw_text:
            prompt = f"""
            You are a helpful study assistant. Summarize the following study material into a 1-page cram sheet:

            - Be concise and avoid repeating the same points.
            - Use short, information-dense bullet points or headers.
            - Avoid extra newlines or large gaps.
            - Keep it clean, readable, and to the point.
            - Use a compact structure that fits well on a single printed page.

            Study material:
            {raw_text}
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful study assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            # Convert Markdown → HTML
            summary_raw = response.choices[0].message.content
            summary = markdown.markdown(summary_raw)

    return render(request, "cram_app/cram_sheet.html", {
        "summary": summary
    })

@login_required
def save_cram_sheet(request):
    if request.method == "POST":
        title = request.POST.get("title", "Untitled")
        content = request.POST.get("content")
        CramSheet.objects.create(user=request.user, title=title, content=content)
        return redirect('my_cram_sheets')

@login_required
def my_cram_sheets(request):
    cram_sheets = CramSheet.objects.filter(user=request.user)
    return render(request, 'cram_app/my_cram_sheets.html', {
        'cram_sheets': cram_sheets
    })

@login_required
def cram_sheet_detail(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)
    return render(request, "cram_app/cram_sheet_detail.html", {
        "sheet": sheet
    })

@login_required
def delete_cram_sheet(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)

    if request.method == "POST":
        sheet.delete()
        return redirect('my_cram_sheets')

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


@login_required
def view_questions(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)
    questions = sheet.questions.all()

    return render(request, "cram_app/view_questions.html", {
        "sheet": sheet,
        "questions": questions
    })

@login_required
def take_quiz(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)
    questions = sheet.questions.all()

    question_data = []
    for q in questions:
        question_data.append({
            "question_text": q.question_text,
            "correct_answer": q.correct_answer,
            "wrong_answers": q.wrong_answers,
        })

    return render(request, "cram_app/quiz.html", {
        "cram_sheet": sheet,
        "questions": question_data  # ✅ serialized
    })

@login_required
def edit_question(request, question_id):
    question = get_object_or_404(TestQuestion, id=question_id, cram_sheet__user=request.user)

    if request.method == "POST":
        form = EditTestQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("view_questions", sheet_id=question.cram_sheet.id)
    else:
        form = EditTestQuestionForm(instance=question)

    return render(request, "cram_app/edit_question.html", {
        "form": form,
        "question": question
    })

@login_required
def add_question(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)

    if request.method == "POST":
        form = TestQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.cram_sheet = sheet

            # Generate wrong answers using GPT
            prompt = f"""
            Generate 3 wrong multiple-choice answers for the following question and its correct answer.
            Do not include the correct answer in the list.

            Question: {question.question_text}
            Correct Answer: {question.correct_answer}

            Return just a JSON list, e.g.:
            ["Wrong Answer 1", "Wrong Answer 2", "Wrong Answer 3"]
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful quiz assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )

                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.strip("```")
                    content = content.replace("json", "", 1).strip()

                question.wrong_answers = json.loads(content)
                question.save()
                return redirect("view_questions", sheet_id=sheet.id)

            except Exception as e:
                return HttpResponseBadRequest(f"Failed to generate wrong answers: {e}")

    else:
        form = TestQuestionForm()

    return render(request, "cram_app/add_question.html", {
        "form": form,
        "sheet": sheet
    })
