from openai import OpenAI
import os
from django.shortcuts import render
import markdown

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
                max_tokens=800
            )
            # Convert Markdown → HTML
            summary_raw = response.choices[0].message.content
            summary = markdown.markdown(summary_raw)

    return render(request, "cram_app/cram_sheet.html", {
        "summary": summary
    })