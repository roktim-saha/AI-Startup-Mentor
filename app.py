"""
AI Startup Mentor - v2 (UI improved + extra features)
--------------------------------------------------------
New in this version:
- Plan is parsed into sections so the UI can show them as cards
- /generate-names route: AI-generated business name + slogan ideas
- /export-pdf route: download the generated plan as a PDF

Setup:
1. pip install -r requirements.txt
2. Add your Gemini API key to a ".env" file (see .env.example)
3. python app.py
4. Open http://127.0.0.1:5000
"""

import os
import re
from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
import google.generativeai as genai
from fpdf import FPDF
import io

# --- Load API key ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found. Add it to a .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Change this if your account doesn't have quota for a given model
MODEL_NAME = "gemini-2.5-flash"

app = Flask(__name__)


# ---------- Helpers ----------

def build_prompt(idea: str, budget: str, location: str) -> str:
    return f"""
You are an expert startup mentor. A user wants to start this business:

Idea: {idea}
Location: {location}
Budget: {budget}

Generate a complete startup plan using EXACTLY these section headings
(so the output can be displayed in a structured way):

## Business Summary
## SWOT Analysis
## Target Customers
## Marketing Strategy
## Estimated Startup Costs
## Revenue and Profit Forecast
## Potential Risks and Solutions
## Step-by-Step Launch Roadmap

Keep each section concise (3-6 bullet points), practical, and specific to the
budget and location given. Use bullet points (start each line with "- "),
not long paragraphs. Do not add any text before "## Business Summary" or
after the last section.
"""


def parse_sections(plan_text: str) -> dict:
    """Splits the raw AI text into {section_title: section_body} using '## ' headings."""
    if not plan_text:
        return {}
    parts = re.split(r"\n?##\s+", plan_text)
    parts = [p.strip() for p in parts if p.strip()]
    sections = {}
    for part in parts:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections[title] = body
    return sections


def build_name_prompt(idea: str, location: str) -> str:
    return f"""
Suggest 5 creative business names with a short slogan for each, for this idea:

Idea: {idea}
Location: {location}

Format EXACTLY like this for each one (no extra text before or after):
1. Name: <name> | Slogan: <slogan>
2. Name: <name> | Slogan: <slogan>
(and so on for 5 total)
"""


def parse_names(text: str):
    """Parses '1. Name: X | Slogan: Y' lines into a list of dicts."""
    results = []
    for line in text.split("\n"):
        line = line.strip()
        match = re.match(r"\d+\.\s*Name:\s*(.+?)\s*\|\s*Slogan:\s*(.+)", line)
        if match:
            results.append({"name": match.group(1).strip(), "slogan": match.group(2).strip()})
    return results


# ---------- Routes ----------

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", sections=None)


@app.route("/generate", methods=["POST"])
def generate():
    idea = request.form.get("idea", "").strip()
    budget = request.form.get("budget", "").strip()
    location = request.form.get("location", "").strip()

    if not idea:
        return render_template("index.html", sections=None, error="Please describe your business idea.")

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(build_prompt(idea, budget, location))
        plan_text = response.text
    except Exception as e:
        return render_template("index.html", sections=None, error=f"AI generation failed: {e}")

    sections = parse_sections(plan_text)

    return render_template(
        "index.html",
        sections=sections,
        raw_plan=plan_text,
        idea=idea,
        budget=budget,
        location=location,
    )


@app.route("/generate-names", methods=["POST"])
def generate_names():
    idea = request.form.get("idea", "").strip()
    budget = request.form.get("budget", "").strip()
    location = request.form.get("location", "").strip()
    raw_plan = request.form.get("raw_plan", "")

    sections = parse_sections(raw_plan)

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(build_name_prompt(idea, location))
        names = parse_names(response.text)
    except Exception as e:
        return render_template(
            "index.html", sections=sections, raw_plan=raw_plan,
            idea=idea, budget=budget, location=location,
            error=f"Name generation failed: {e}"
        )

    return render_template(
        "index.html",
        sections=sections,
        raw_plan=raw_plan,
        idea=idea,
        budget=budget,
        location=location,
        names=names,
    )


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    idea = request.form.get("idea", "Business Plan")
    raw_plan = request.form.get("raw_plan", "")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, "AI Startup Mentor - Business Plan")
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 8, f"Idea: {idea}")
    pdf.ln(4)

    pdf.set_font("Helvetica", size=11)
    for line in raw_plan.split("\n"):
        clean_line = line.encode("latin-1", "replace").decode("latin-1")
        if clean_line.strip().startswith("##"):
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(3)
            pdf.multi_cell(0, 8, clean_line.replace("##", "").strip())
            pdf.set_font("Helvetica", size=11)
        else:
            pdf.multi_cell(0, 7, clean_line)

    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")

    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="startup-plan.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
