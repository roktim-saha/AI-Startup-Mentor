"""
AI Startup Mentor - v3 (UI improved + extra features)
--------------------------------------------------------
Features:
- Plan is parsed into sections so the UI can show them as cards
- /generate-names route: AI-generated business name + slogan ideas
- /generate-inventory route: AI-suggested inventory budget split
- /chat route: AI mentor chat with conversation memory
- Pricing & Margin Calculator and Cash Flow Planner (client-side JS)

Setup:
1. pip install -r requirements.txt
2. Add your Gemini API key to a ".env" file (see .env.example)
3. python app.py
4. Open http://127.0.0.1:5000
"""

import os
import re
import json
from flask import Flask, render_template, request
from dotenv import load_dotenv
import google.generativeai as genai

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


def build_inventory_prompt(idea: str, budget: str, categories: str) -> str:
    return f"""
A user is starting this business:
Idea: {idea}
Budget: {budget}
Inventory categories they want to stock: {categories}

Suggest how to split the budget across these categories. For each category,
give a percentage of the budget, the approximate amount, and a one-sentence
reason. Format EXACTLY like this (no extra text before or after, one line per category):

1. Category: <name> | Percent: <number>% | Amount: <number> | Note: <short reason>
2. Category: <name> | Percent: <number>% | Amount: <number> | Note: <short reason>
(continue for all categories given, percentages should add up to about 100%)
"""


def parse_inventory(text: str):
    """Parses '1. Category: X | Percent: Y% | Amount: Z | Note: W' lines."""
    results = []
    pattern = r"\d+\.\s*Category:\s*(.+?)\s*\|\s*Percent:\s*(.+?)\s*\|\s*Amount:\s*(.+?)\s*\|\s*Note:\s*(.+)"
    for line in text.split("\n"):
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            results.append({
                "category": match.group(1).strip(),
                "percent": match.group(2).strip(),
                "amount": match.group(3).strip(),
                "note": match.group(4).strip(),
            })
    return results


def build_chat_prompt(idea: str, budget: str, location: str, raw_plan: str, question: str, history: list) -> str:
    history_text = ""
    for turn in history[-5:]:  # keep last 5 exchanges to stay concise
        history_text += f"\nUser asked: {turn.get('q','')}\nYou answered: {turn.get('a','')}\n"

    return f"""
You are an AI startup mentor helping a user with this business:

Idea: {idea}
Location: {location}
Budget: {budget}

Here is the startup plan you already gave them:
{raw_plan}

Previous conversation with this user:
{history_text if history_text else "(no previous questions yet)"}

Now answer this new question from the user. Be practical, specific to their
idea and budget, and concise (under 150 words). Use plain text, short
paragraphs or bullet points, no markdown headings.

User's question: {question}
"""


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


@app.route("/generate-inventory", methods=["POST"])
def generate_inventory():
    idea = request.form.get("idea", "").strip()
    budget = request.form.get("budget", "").strip()
    location = request.form.get("location", "").strip()
    raw_plan = request.form.get("raw_plan", "")
    categories = request.form.get("categories", "").strip()

    sections = parse_sections(raw_plan)

    if not categories:
        return render_template(
            "index.html", sections=sections, raw_plan=raw_plan,
            idea=idea, budget=budget, location=location,
            error="Please list at least one inventory category (e.g. phones, accessories)."
        )

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(build_inventory_prompt(idea, budget, categories))
        inventory = parse_inventory(response.text)
    except Exception as e:
        return render_template(
            "index.html", sections=sections, raw_plan=raw_plan,
            idea=idea, budget=budget, location=location,
            error=f"Inventory suggestion failed: {e}"
        )

    return render_template(
        "index.html",
        sections=sections,
        raw_plan=raw_plan,
        idea=idea,
        budget=budget,
        location=location,
        inventory=inventory,
        categories_input=categories,
    )


@app.route("/chat", methods=["POST"])
def chat():
    idea = request.form.get("idea", "").strip()
    budget = request.form.get("budget", "").strip()
    location = request.form.get("location", "").strip()
    raw_plan = request.form.get("raw_plan", "")
    question = request.form.get("question", "").strip()
    chat_history_raw = request.form.get("chat_history", "[]")

    sections = parse_sections(raw_plan)

    try:
        history = json.loads(chat_history_raw)
    except Exception:
        history = []

    if not question:
        return render_template(
            "index.html", sections=sections, raw_plan=raw_plan,
            idea=idea, budget=budget, location=location,
            chat_history=history, chat_history_json=json.dumps(history),
            error="Please type a question for the AI mentor."
        )

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = build_chat_prompt(idea, budget, location, raw_plan, question, history)
        response = model.generate_content(prompt)
        answer = response.text.strip()
        history.append({"q": question, "a": answer})
    except Exception as e:
        return render_template(
            "index.html", sections=sections, raw_plan=raw_plan,
            idea=idea, budget=budget, location=location,
            chat_history=history, chat_history_json=json.dumps(history),
            error=f"Chat failed: {e}"
        )

    return render_template(
        "index.html",
        sections=sections,
        raw_plan=raw_plan,
        idea=idea,
        budget=budget,
        location=location,
        chat_history=history,
        chat_history_json=json.dumps(history),
    )


if __name__ == "__main__":
    app.run(debug=True)