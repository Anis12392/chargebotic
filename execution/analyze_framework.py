#!/usr/bin/env python3
"""
Analyze transcripts to extract content framework patterns.
Extracts hook templates, middle pivots, closing formulas, and full structures.

Usage:
    python3 execution/analyze_framework.py
    # Or import: from execution.analyze_framework import analyze_transcripts
"""

import json
import re
from collections import Counter
from pathlib import Path


# --- Pattern definitions ---

HOOK_PATTERNS = [
    {
        "id": "H1",
        "name": "[Topic], it's [bold take]",
        "name_fr": "[Sujet], c'est [affirmation]",
        "regex": r"^.{0,40},\s*c'est\s",
    },
    {
        "id": "H2",
        "name": "There's [something] that [revelation]",
        "name_fr": "Il y a [X] que/qui...",
        "regex": r"^il\s*y\s*a\s",
    },
    {
        "id": "H3",
        "name": "I [did/saw/discovered]",
        "name_fr": "J'ai [experience]",
        "regex": r"^j'ai\s",
    },
    {
        "id": "H4",
        "name": "[Group] [do/are/don't]...",
        "name_fr": "Les [X] [verbe]...",
        "regex": r"^les\s\w+",
    },
    {
        "id": "H5",
        "name": "I [will/can/verb]",
        "name_fr": "Je [vais/peux/verbe]",
        "regex": r"^je\s(vais|peux|suis|connais|vous|te)\s",
    },
    {
        "id": "H6",
        "name": "We [verb]",
        "name_fr": "On [verbe]",
        "regex": r"^on\s\w+",
    },
    {
        "id": "H7",
        "name": "The [X] [is/verb]",
        "name_fr": "Le/La [X] [verbe]",
        "regex": r"^(le|la|l')\s\w+",
    },
    {
        "id": "H8",
        "name": "[Question]?",
        "name_fr": "Pourquoi/Comment/Est-ce que...?",
        "regex": r"^(pourquoi|comment|est-ce que|est-ce qu)",
    },
    {
        "id": "H9",
        "name": "When you [situation]...",
        "name_fr": "Quand tu/on [fait X]...",
        "regex": r"^quand\s(tu|on|vous)\s",
    },
    {
        "id": "H10",
        "name": "If you [want/condition]...",
        "name_fr": "Si tu/on [veut X]...",
        "regex": r"^si\s(tu|on|vous)\s",
    },
]

MIDDLE_PATTERNS = [
    {
        "id": "M1",
        "name": "But actually... / The thing is...",
        "name_fr": "En fait...",
        "regex": r"en\s*fait",
    },
    {
        "id": "M2",
        "name": "Except that... / But here's the catch...",
        "name_fr": "Sauf que...",
        "regex": r"sauf\s*qu",
    },
    {
        "id": "M3",
        "name": "The problem is that...",
        "name_fr": "Le probleme c'est que...",
        "regex": r"le\s*probl[eè]me\s*(,\s*)?c'est\s*qu",
    },
    {
        "id": "M4",
        "name": "While... / Whereas...",
        "name_fr": "Alors que...",
        "regex": r"alors\s*que\s",
    },
    {
        "id": "M5",
        "name": "That's why...",
        "name_fr": "C'est pour ca que...",
        "regex": r"c'est\s*pour\s*[cç]a\s*qu",
    },
    {
        "id": "M6",
        "name": "And that... it [consequence]",
        "name_fr": "Et ca, ca [consequence]",
        "regex": r"et\s*[cç]a[,\s]*[cç]a\s",
    },
    {
        "id": "M7",
        "name": "However... / On the other hand...",
        "name_fr": "Par contre...",
        "regex": r"par\s*contre",
    },
    {
        "id": "M8",
        "name": "And yet...",
        "name_fr": "Et pourtant...",
        "regex": r"et\s*pourtant",
    },
    {
        "id": "M9",
        "name": "But in reality...",
        "name_fr": "Mais en realite...",
        "regex": r"mais\s*en\s*r[eé]alit[eé]",
    },
    {
        "id": "M10",
        "name": "And that's where...",
        "name_fr": "Et c'est la que/ou...",
        "regex": r"et\s*c'est\s*l[aà]\s*(que|o[uù])",
    },
]

CLOSING_PATTERNS = [
    {
        "id": "C1",
        "name": "And [final statement].",
        "name_fr": "Et [conclusion].",
        "regex": r"^et\s",
    },
    {
        "id": "C2",
        "name": "It's [affirmation].",
        "name_fr": "C'est [X].",
        "regex": r"^c'est\s",
    },
    {
        "id": "C3",
        "name": "We [verb].",
        "name_fr": "On [verbe].",
        "regex": r"^on\s",
    },
    {
        "id": "C4",
        "name": "So [conclusion].",
        "name_fr": "Donc [conclusion].",
        "regex": r"^donc\s",
    },
    {
        "id": "C5",
        "name": "You have to [imperative].",
        "name_fr": "Il faut [conseil].",
        "regex": r"^il\s*faut\s",
    },
    {
        "id": "C6",
        "name": "And that's what we [do].",
        "name_fr": "Et c'est ce que nous/on [fait].",
        "regex": r"c'est\s*(ce\s*que|exactement)",
    },
    {
        "id": "C7",
        "name": "That's why [lesson].",
        "name_fr": "C'est pour ca que [lecon].",
        "regex": r"c'est\s*pour\s*[cç]a",
    },
]


def _get_first_sentence(text: str) -> str:
    """Extract the first sentence from a transcript."""
    text = text.strip()
    # Split on sentence-ending punctuation
    match = re.search(r'[.!?]', text)
    if match and match.start() < 200:
        return text[:match.start() + 1].strip()
    # If no punctuation found, take first 150 chars
    if len(text) > 150:
        # Try to break at a comma
        comma = text.find(',', 40)
        if comma > 0 and comma < 150:
            return text[:comma + 1].strip()
    return text[:150].strip()


def _get_last_sentence(text: str) -> str:
    """Extract the last sentence from a transcript."""
    text = text.strip()
    # Find last sentence-ending punctuation before the end
    sentences = re.split(r'[.!?]\s+', text)
    if len(sentences) >= 2:
        return sentences[-1].strip()
    # Take last 150 chars
    return text[-150:].strip()


def _classify_hook(first_sentence: str) -> str:
    """Classify a hook into a pattern ID."""
    lower = first_sentence.lower().strip()
    for pattern in HOOK_PATTERNS:
        if re.search(pattern["regex"], lower, re.IGNORECASE):
            return pattern["id"]
    return "OTHER"


def _find_middle_patterns(text: str) -> list:
    """Find all middle transition patterns in a transcript."""
    found = []
    lower = text.lower()
    for pattern in MIDDLE_PATTERNS:
        if re.search(pattern["regex"], lower, re.IGNORECASE):
            found.append(pattern["id"])
    return found


def _classify_closing(last_sentence: str) -> str:
    """Classify a closing into a pattern ID."""
    lower = last_sentence.lower().strip()
    for pattern in CLOSING_PATTERNS:
        if re.search(pattern["regex"], lower, re.IGNORECASE):
            return pattern["id"]
    return "STATEMENT"  # Default: plain declarative statement


def analyze_transcripts(progress_file: Path) -> dict:
    """Run full framework analysis on transcripts. Returns structured JSON."""
    data = json.loads(progress_file.read_text(encoding="utf-8"))

    # Filter out errors
    transcripts = {k: v for k, v in data.items() if v and not v.startswith("[Error")}
    total = len(transcripts)

    hook_counts = Counter()
    middle_counts = Counter()
    closing_counts = Counter()
    hook_examples = {}
    middle_examples = {}
    closing_examples = {}

    for name, text in transcripts.items():
        first = _get_first_sentence(text)
        last = _get_last_sentence(text)

        # Hooks
        hook_id = _classify_hook(first)
        hook_counts[hook_id] += 1
        if hook_id not in hook_examples:
            hook_examples[hook_id] = []
        if len(hook_examples[hook_id]) < 3:
            hook_examples[hook_id].append({"name": name, "text": first})

        # Middles
        middles = _find_middle_patterns(text)
        for mid_id in middles:
            middle_counts[mid_id] += 1
            if mid_id not in middle_examples:
                middle_examples[mid_id] = []
            if len(middle_examples[mid_id]) < 3:
                # Extract the sentence containing the pattern
                pattern_def = next(p for p in MIDDLE_PATTERNS if p["id"] == mid_id)
                match = re.search(pattern_def["regex"], text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 100)
                    snippet = text[start:end].strip()
                    middle_examples[mid_id].append({"name": name, "text": f"...{snippet}..."})

        # Closings
        closing_id = _classify_closing(last)
        closing_counts[closing_id] += 1
        if closing_id not in closing_examples:
            closing_examples[closing_id] = []
        if len(closing_examples[closing_id]) < 3:
            closing_examples[closing_id].append({"name": name, "text": last})

    # Build results
    def build_section(patterns_def, counts, examples, total_count):
        results = []
        for p in patterns_def:
            pid = p["id"]
            count = counts.get(pid, 0)
            pct = round(count / total_count * 100, 1) if total_count > 0 else 0
            results.append({
                "id": pid,
                "name": p["name"],
                "name_fr": p.get("name_fr", ""),
                "count": count,
                "percentage": pct,
                "examples": examples.get(pid, []),
            })
        # Add OTHER/STATEMENT if exists
        for key in counts:
            if key not in [p["id"] for p in patterns_def]:
                count = counts[key]
                pct = round(count / total_count * 100, 1)
                results.append({
                    "id": key,
                    "name": "Other" if key == "OTHER" else "Plain statement",
                    "name_fr": "Autre" if key == "OTHER" else "Affirmation simple",
                    "count": count,
                    "percentage": pct,
                    "examples": examples.get(key, []),
                })
        results.sort(key=lambda x: x["count"], reverse=True)
        return results

    return {
        "total_transcripts": total,
        "hooks": build_section(HOOK_PATTERNS, hook_counts, hook_examples, total),
        "middles": build_section(MIDDLE_PATTERNS, middle_counts, middle_examples, total),
        "closings": build_section(CLOSING_PATTERNS, closing_counts, closing_examples, total),
    }


def score_script(script_text: str, analysis: dict) -> dict:
    """Score a script 0-100 based on how well it matches the extracted framework."""
    score = 0
    breakdown = {}

    # 1. Hook match (30 pts)
    first = _get_first_sentence(script_text)
    hook_id = _classify_hook(first)
    known_hooks = {h["id"] for h in analysis["hooks"] if h["percentage"] > 2}
    if hook_id in known_hooks:
        score += 30
        breakdown["hook"] = {"score": 30, "max": 30, "detail": f"Matches {hook_id}"}
    elif hook_id != "OTHER":
        score += 15
        breakdown["hook"] = {"score": 15, "max": 30, "detail": f"Weak match: {hook_id}"}
    else:
        breakdown["hook"] = {"score": 0, "max": 30, "detail": "No known hook pattern"}

    # 2. Word count (20 pts) — target 140-180
    words = len(script_text.split())
    if 140 <= words <= 180:
        score += 20
        breakdown["word_count"] = {"score": 20, "max": 20, "detail": f"{words} words (perfect)"}
    elif 120 <= words <= 200:
        score += 12
        breakdown["word_count"] = {"score": 12, "max": 20, "detail": f"{words} words (close)"}
    elif 100 <= words <= 220:
        score += 5
        breakdown["word_count"] = {"score": 5, "max": 20, "detail": f"{words} words (off target)"}
    else:
        breakdown["word_count"] = {"score": 0, "max": 20, "detail": f"{words} words (way off)"}

    # 3. Middle pivot (20 pts)
    middles_found = _find_middle_patterns(script_text)
    if len(middles_found) >= 2:
        score += 20
        breakdown["middle"] = {"score": 20, "max": 20, "detail": f"Found {len(middles_found)} pivots"}
    elif len(middles_found) == 1:
        score += 12
        breakdown["middle"] = {"score": 12, "max": 20, "detail": f"Found 1 pivot"}
    else:
        breakdown["middle"] = {"score": 0, "max": 20, "detail": "No pivot found"}

    # 4. Closing match (15 pts)
    last = _get_last_sentence(script_text)
    closing_id = _classify_closing(last)
    if closing_id == "STATEMENT":
        score += 15  # Plain statement is the dominant closing (72%)
        breakdown["closing"] = {"score": 15, "max": 15, "detail": "Strong declarative ending"}
    elif closing_id != "OTHER":
        score += 12
        breakdown["closing"] = {"score": 12, "max": 15, "detail": f"Matches {closing_id}"}
    else:
        breakdown["closing"] = {"score": 0, "max": 15, "detail": "Weak closing"}

    # 5. Simplicity (15 pts)
    sentences = re.split(r'[.!?]+', script_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_len <= 12:
            score += 15
            breakdown["simplicity"] = {"score": 15, "max": 15, "detail": f"Avg {avg_sentence_len:.0f} words/sentence (great)"}
        elif avg_sentence_len <= 18:
            score += 10
            breakdown["simplicity"] = {"score": 10, "max": 15, "detail": f"Avg {avg_sentence_len:.0f} words/sentence (ok)"}
        else:
            score += 3
            breakdown["simplicity"] = {"score": 3, "max": 15, "detail": f"Avg {avg_sentence_len:.0f} words/sentence (too complex)"}

    return {"score": score, "max": 100, "breakdown": breakdown}


def main():
    project_root = Path(__file__).resolve().parent.parent
    progress_file = project_root / ".tmp" / "transcribe_progress.json"
    output_file = project_root / ".tmp" / "analysis.json"

    if not progress_file.exists():
        print("No transcripts found. Run transcribe_reels.py first.")
        return

    print("Analyzing transcripts...")
    result = analyze_transcripts(progress_file)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nAnalysis complete: {result['total_transcripts']} transcripts")
    print(f"\nTop hooks:")
    for h in result["hooks"][:5]:
        print(f"  {h['id']} ({h['percentage']}%) — {h['name']}")
    print(f"\nTop middles:")
    for m in result["middles"][:5]:
        print(f"  {m['id']} ({m['percentage']}%) — {m['name']}")
    print(f"\nTop closings:")
    for c in result["closings"][:3]:
        print(f"  {c['id']} ({c['percentage']}%) — {c['name']}")
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
