# AI Startup Mentor — Starter

## Setup (do this first)

```bash
cd ai-startup-mentor
pip install -r requirements.txt
cp .env.example .env
# now open .env and paste your real Gemini API key
python app.py
```

Open http://127.0.0.1:5000 in your browser. Type a business idea, hit
"Generate Plan", and it should call Gemini and show a formatted plan.

If you get an error about the model name, go to
https://aistudio.google.com and check which free-tier model name is
currently available, then update `MODEL_NAME` in `app.py`.

## Suggested hackathon roadmap (compress/expand based on your deadline)

**Stage 1 — Get it running (do this today)**
- Get Gemini API key, run the starter app, confirm you get a real
  plan back for a test idea. This is your proof the core idea works.

**Stage 2 — Core feature polish**
- Improve the prompt in `build_prompt()` for better quality output
- Add loading state (spinner) while Gemini is generating
- Style the results page so each section (SWOT, Marketing, etc.) is
  visually separated, not just plain text

**Stage 3 — One or two "wow" extras (pick based on time left)**
- PDF export of the generated plan (easiest with `reportlab` or
  `xhtml2pdf`)
- Simple financial calculator (break-even, profit margin) using plain
  JS — no AI needed, judges like seeing real numbers
- AI-generated business name + slogan (just another Gemini prompt)

**Stage 4 — Demo prep**
- Prepare 2-3 example business ideas that give good-looking results
  (test them beforehand — don't discover a bad output live)
- Write a 60-90 second pitch: problem → solution → live demo → tech stack

## What NOT to build (given limited time)
- Skip user accounts/login unless a judge specifically asks
- Skip the database (SQLite) unless you need to save/list multiple
  plans — for a demo, showing one generated plan live is enough
- Skip React — plain HTML is faster to build and just as demo-able
