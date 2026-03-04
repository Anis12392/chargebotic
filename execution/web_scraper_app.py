#!/usr/bin/env python3
"""
Content Scripting Tool — Web App.
Scrape Instagram reels, analyze frameworks, generate video scripts.

Usage:
    python3 -m uvicorn execution.web_scraper_app:app --reload --port 8000
"""

import json
import os
import subprocess
import threading
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import anthropic
import instaloader
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from execution.analyze_framework import analyze_transcripts, score_script

app = FastAPI(title="Content Scripting Tool")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
REELS_DIR = TMP_DIR / "reels"
PROGRESS_FILE = TMP_DIR / "transcribe_progress.json"
TRANSCRIPTS_FILE = TMP_DIR / "transcripts.md"
ANALYSIS_FILE = TMP_DIR / "analysis.json"
NICHE_FILE = TMP_DIR / "niche_config.json"
SCRIPTS_DIR = TMP_DIR / "scripts"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Global state for tracking background jobs
job_state = {
    "scraping": False,
    "transcribing": False,
    "analyzing": False,
    "scrape_profile": "",
    "scrape_count": 0,
    "scrape_done": False,
    "transcribe_done": False,
    "error": None,
}


def _count_mp4s():
    if not REELS_DIR.exists():
        return 0
    return len(list(REELS_DIR.glob("*.mp4")))


def _count_transcribed():
    if not PROGRESS_FILE.exists():
        return 0
    try:
        return len(json.loads(PROGRESS_FILE.read_text()))
    except Exception:
        return 0


def _run_scrape(profile: str):
    try:
        job_state["scraping"] = True
        job_state["scrape_done"] = False
        job_state["error"] = None
        REELS_DIR.mkdir(parents=True, exist_ok=True)

        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
        )

        ig_profile = instaloader.Profile.from_username(L.context, profile)
        for post in ig_profile.get_posts():
            if not post.is_video:
                continue
            L.download_post(post, target=REELS_DIR)
            for f in REELS_DIR.iterdir():
                if f.suffix not in (".mp4", ".wav", ".md", ".json"):
                    f.unlink()
            job_state["scrape_count"] = _count_mp4s()

        job_state["scrape_done"] = True
    except Exception as e:
        job_state["error"] = str(e)
    finally:
        job_state["scraping"] = False


def _run_transcribe():
    try:
        job_state["transcribing"] = True
        job_state["transcribe_done"] = False
        job_state["error"] = None

        subprocess.run(
            ["python3", str(PROJECT_ROOT / "execution" / "transcribe_reels.py")],
            cwd=str(PROJECT_ROOT),
            check=True,
        )
        job_state["transcribe_done"] = True
    except Exception as e:
        job_state["error"] = str(e)
    finally:
        job_state["transcribing"] = False


def _build_script_prompt(analysis: dict, niche: dict, topic: str, trend: str) -> str:
    """Build the Claude prompt for script generation."""

    # Summarize the framework
    top_hooks = [h for h in analysis["hooks"] if h["percentage"] > 3][:6]
    top_middles = [m for m in analysis["middles"] if m["percentage"] > 3][:5]
    top_closings = [c for c in analysis["closings"] if c["percentage"] > 3][:4]

    hook_lines = "\n".join(
        f"- {h['id']} ({h['percentage']}%): \"{h['name']}\" — e.g. \"{h['examples'][0]['text'][:100]}\"" if h['examples'] else f"- {h['id']} ({h['percentage']}%): \"{h['name']}\""
        for h in top_hooks
    )
    middle_lines = "\n".join(
        f"- {m['id']} ({m['percentage']}%): \"{m['name']}\""
        for m in top_middles
    )
    closing_lines = "\n".join(
        f"- {c['id']} ({c['percentage']}%): \"{c['name']}\""
        for c in top_closings
    )

    return f"""You are a video script writer for short-form social media content (Instagram Reels, TikTok).

## FRAMEWORK (extracted from {analysis['total_transcripts']} viral scripts)

### Hook formulas (opening line):
{hook_lines}

### Middle pivots (transition phrases to use):
{middle_lines}

### Closing formulas (last line):
{closing_lines}

### Full structure:
Most scripts follow: BOLD CLAIM > EXPLAIN WHY > TAKEAWAY (50% of scripts)
Or: PERSONAL STORY > INSIGHT (21%)
Or: MYTH > BUST > REALITY (8%)

## RULES
- Each script must be 140-170 words (about 60 seconds spoken)
- Use SHORT sentences. Simple words. Like someone talking to a friend
- No jargon. No corporate speak. No AI-sounding phrases
- Each script uses a DIFFERENT hook formula — label which one (e.g. "Hook: H1")
- Include the structure type used (e.g. "Structure: Bold Claim > Explain > Takeaway")
- The closing should be a strong final statement, NOT a call-to-action (72% of viral scripts end this way)
- Write in the same language as the niche description below

## NICHE CONTEXT
Company: {niche.get('company', 'N/A')}
Industry: {niche.get('industry', 'N/A')}
Description: {niche.get('description', 'N/A')}
Key talking points: {niche.get('talking_points', 'N/A')}

## TASK
Topic for this batch: {topic}
{"Trending news to react to: " + trend if trend else "No specific trend — use general industry insights."}

Generate exactly 3 scripts. For each script, output:
1. The hook formula used (e.g. "Hook: H3")
2. The structure used (e.g. "Structure: Personal Story > Insight")
3. The script text (140-170 words)

Format each script as:
### Script 1
**Hook:** H1 — [Topic], it's [bold take]
**Structure:** Bold Claim > Explain > Takeaway
**Word count:** XXX

[script text here]

---"""


# ===== EXISTING ENDPOINTS =====

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = TEMPLATES_DIR / "scraper.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/scrape")
async def scrape(request: Request):
    body = await request.json()
    profile = body.get("profile", "").strip().lstrip("@")
    if not profile:
        return JSONResponse({"error": "Profile is required"}, status_code=400)
    if job_state["scraping"]:
        return JSONResponse({"error": "Scraping already in progress"}, status_code=409)

    job_state["scrape_profile"] = profile
    job_state["scrape_count"] = _count_mp4s()
    threading.Thread(target=_run_scrape, args=(profile,), daemon=True).start()
    return {"message": f"Started scraping @{profile}", "status": "started"}


@app.post("/transcribe")
async def transcribe():
    if job_state["transcribing"]:
        return JSONResponse({"error": "Transcription already in progress"}, status_code=409)
    threading.Thread(target=_run_transcribe, daemon=True).start()
    return {"message": "Started transcription", "status": "started"}


@app.post("/stop-scrape")
async def stop_scrape():
    job_state["scraping"] = False
    job_state["scrape_done"] = True
    return {"message": "Scrape marked as stopped"}


@app.get("/status")
async def status():
    return {
        "scraping": job_state["scraping"],
        "transcribing": job_state["transcribing"],
        "analyzing": job_state["analyzing"],
        "scrape_profile": job_state["scrape_profile"],
        "scrape_count": _count_mp4s(),
        "transcribed_count": _count_transcribed(),
        "scrape_done": job_state["scrape_done"],
        "transcribe_done": job_state["transcribe_done"],
        "error": job_state["error"],
    }


@app.get("/transcripts/search")
async def search_transcripts(q: str = ""):
    if not PROGRESS_FILE.exists():
        return {"results": []}
    data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    if not q:
        return {"results": [{"name": k, "text": v[:200]} for k, v in list(data.items())[:50]]}
    results = []
    q_lower = q.lower()
    for name, text in data.items():
        if q_lower in text.lower():
            idx = text.lower().index(q_lower)
            start = max(0, idx - 80)
            end = min(len(text), idx + len(q) + 80)
            snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
            results.append({"name": name, "snippet": snippet})
    return {"query": q, "count": len(results), "results": results}


# ===== NEW ENDPOINTS: ANALYZE =====

@app.post("/analyze")
async def run_analysis():
    if not PROGRESS_FILE.exists():
        return JSONResponse({"error": "No transcripts to analyze. Transcribe first."}, status_code=400)

    job_state["analyzing"] = True
    try:
        result = analyze_transcripts(PROGRESS_FILE)
        ANALYSIS_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        job_state["analyzing"] = False


@app.get("/analysis")
async def get_analysis():
    if not ANALYSIS_FILE.exists():
        return JSONResponse({"error": "No analysis yet. Click Analyze first."}, status_code=404)
    return json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))


# ===== NEW ENDPOINTS: NICHE =====

@app.get("/niche")
async def get_niche():
    if not NICHE_FILE.exists():
        return {"company": "", "industry": "", "description": "", "talking_points": ""}
    return json.loads(NICHE_FILE.read_text(encoding="utf-8"))


@app.post("/niche")
async def save_niche(request: Request):
    body = await request.json()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    NICHE_FILE.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"message": "Niche saved", "niche": body}


# ===== NEW ENDPOINTS: GENERATE SCRIPTS =====

@app.post("/generate-scripts")
async def generate_scripts(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    trend = body.get("trend", "").strip()

    if not topic:
        return JSONResponse({"error": "Topic is required"}, status_code=400)

    # Load analysis
    if not ANALYSIS_FILE.exists():
        return JSONResponse({"error": "Run analysis first (Tab 2)"}, status_code=400)
    analysis = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))

    # Load niche
    if not NICHE_FILE.exists():
        return JSONResponse({"error": "Set up your niche first (Tab 4)"}, status_code=400)
    niche = json.loads(NICHE_FILE.read_text(encoding="utf-8"))

    # Build prompt
    prompt = _build_script_prompt(analysis, niche, topic, trend)

    # Call Claude
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not set. Export it in your shell."}, status_code=500)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text

        # Parse individual scripts and score them
        import re as _re
        import time
        script_blocks = _re.split(r'###\s*Script\s*\d+', response_text)
        script_blocks = [b.strip() for b in script_blocks if b.strip()]

        parsed_scripts = []
        for i, block in enumerate(script_blocks):
            # Extract metadata lines and script body
            lines = block.split("\n")
            hook_label = ""
            structure_label = ""
            word_count_label = ""
            body_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("**Hook:**") or stripped.startswith("**Hook :**"):
                    hook_label = stripped.replace("**Hook:**", "").replace("**Hook :**", "").strip()
                elif stripped.startswith("**Structure:**") or stripped.startswith("**Structure :**"):
                    structure_label = stripped.replace("**Structure:**", "").replace("**Structure :**", "").strip()
                elif stripped.startswith("**Word count:**") or stripped.startswith("**Word count :**"):
                    word_count_label = stripped.replace("**Word count:**", "").replace("**Word count :**", "").strip()
                elif stripped == "---":
                    continue
                elif stripped:
                    body_lines.append(line)
            script_body = "\n".join(body_lines).strip()

            # Score the script
            script_score = score_script(script_body, analysis) if script_body else {"score": 0, "max": 100, "breakdown": {}}

            parsed_scripts.append({
                "index": i + 1,
                "hook": hook_label,
                "structure": structure_label,
                "word_count": word_count_label,
                "body": script_body,
                "score": script_score,
                "first_line": script_body.split("\n")[0][:120] if script_body else "",
            })

        # Save to history
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        batch_id = str(int(time.time()))
        batch = {
            "id": batch_id,
            "topic": topic,
            "trend": trend,
            "scripts": response_text,
            "parsed_scripts": parsed_scripts,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        }
        (SCRIPTS_DIR / f"{batch_id}.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return batch
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/regenerate-script")
async def regenerate_script(request: Request):
    body = await request.json()
    topic = body.get("topic", "")
    trend = body.get("trend", "")
    script_number = body.get("script_number", 1)
    feedback = body.get("feedback", "")

    if not ANALYSIS_FILE.exists() or not NICHE_FILE.exists():
        return JSONResponse({"error": "Analysis and niche config required"}, status_code=400)

    analysis = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))
    niche = json.loads(NICHE_FILE.read_text(encoding="utf-8"))

    prompt = _build_script_prompt(analysis, niche, topic, trend)
    prompt += f"\n\nREGENERATE ONLY Script {script_number}. Make it different from the previous version."
    if feedback:
        prompt += f"\nUser feedback: {feedback}"
    prompt += "\nOutput ONLY 1 script."

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not set"}, status_code=500)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return {"script": message.content[0].text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scripts-history")
async def scripts_history():
    if not SCRIPTS_DIR.exists():
        return {"batches": []}
    batches = []
    for f in sorted(SCRIPTS_DIR.glob("*.json"), reverse=True):
        try:
            batches.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return {"batches": batches[:20]}


# ===== NEW ENDPOINTS: SCORE =====

@app.post("/score-script")
async def score_script_endpoint(request: Request):
    body = await request.json()
    script_text = body.get("script", "").strip()
    if not script_text:
        return JSONResponse({"error": "Script text is required"}, status_code=400)
    if not ANALYSIS_FILE.exists():
        return JSONResponse({"error": "Run analysis first"}, status_code=400)
    analysis = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))
    result = score_script(script_text, analysis)
    return result


# ===== NEW ENDPOINTS: NICHE CHAT AGENT =====

NICHE_QUESTIONS = [
    "What's your company name and what do you do in one sentence?",
    "Who is your target customer? Who buys from you?",
    "What's the #1 problem you solve that nobody else is solving?",
    "What's your unfair advantage — what makes you different from competitors?",
    "What are 2-3 key stats or facts you love to mention in your content?",
]


@app.post("/niche-chat")
async def niche_chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    # Count user messages to determine which question to ask next
    user_msgs = [m for m in messages if m.get("role") == "user"]
    q_index = len(user_msgs)

    # If fewer than 5 answers, return next question
    if q_index < len(NICHE_QUESTIONS):
        return {
            "reply": NICHE_QUESTIONS[q_index],
            "done": False,
            "question_index": q_index,
        }

    # All 5 answered — extract niche config via Claude
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not set"}, status_code=500)

    # Build extraction prompt
    conversation_text = ""
    for i, q in enumerate(NICHE_QUESTIONS):
        answer = user_msgs[i]["content"] if i < len(user_msgs) else ""
        conversation_text += f"Q: {q}\nA: {answer}\n\n"

    extraction_prompt = f"""From this conversation, extract a structured niche profile for content creation.

{conversation_text}

Return ONLY valid JSON (no markdown, no explanation) with these fields:
{{
  "company": "company name",
  "industry": "industry/vertical",
  "description": "2-3 sentence description of what they do and for whom",
  "talking_points": "comma-separated key facts, stats, and differentiators to use in scripts",
  "target_customer": "who they sell to",
  "unique_advantage": "their unfair advantage"
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": extraction_prompt}],
        )
        response_text = message.content[0].text.strip()
        # Parse JSON from response
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        niche_data = json.loads(response_text)

        # Save
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        NICHE_FILE.write_text(json.dumps(niche_data, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "reply": "Perfect! I've built your niche profile. Here's what I extracted:",
            "done": True,
            "niche": niche_data,
        }
    except json.JSONDecodeError:
        return JSONResponse({"error": "Failed to parse niche data from AI response"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
