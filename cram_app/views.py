from openai import OpenAI
import os
from django.shortcuts import render
import markdown
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CramSheet

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    sheets = CramSheet.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "cram_app/my_cram_sheets.html", {"sheets": sheets})