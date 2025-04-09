from openai import OpenAI
import os
import markdown
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CramSheet, TestQuestion
from django.contrib.auth.views import LoginView, LogoutView

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
        Based on the following cram sheet, generate 10 concise, challenging test questions (mix of multiple choice and short answer):

        {sheet.content}

        Format clearly like:
        1. What is...
        2. Explain...
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a quiz generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        questions_text = response.choices[0].message.content.strip().split('\n')
        questions = [q.strip() for q in questions_text if q.strip()]

        for q in questions:
            TestQuestion.objects.create(cram_sheet=sheet, question_text=q)

        sheet.questions_generated = True
        sheet.save()

        return redirect('view_questions', sheet_id=sheet.id)

@login_required
def view_questions(request, sheet_id):
    sheet = get_object_or_404(CramSheet, id=sheet_id, user=request.user)
    questions = sheet.questions.all()

    return render(request, "cram_app/view_questions.html", {
        "sheet": sheet,
        "questions": questions
    })
