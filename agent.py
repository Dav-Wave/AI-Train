"""
PM Brief Generator Agent — Session 2
--------------------------------------
Uses Google Gemini API (FREE — no credit card required).
Get your key at: https://aistudio.google.com → "Get API key"

Usage:
    python agent.py
    python agent.py --input "your feedback text here"
    python agent.py --file feedback.txt
    python agent.py --input "3 accounts complaining about SSO" --context "enterprise team"
"""

import json
import sys
import argparse
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini — reads GEMINI_API_KEY from .env
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────
# Versioned: v1.0 — initial build (workshop day)
SYSTEM_PROMPT = """You are a senior Product Manager at a B2B SaaS company.

When given raw stakeholder feedback — a Slack thread, meeting notes, customer
complaints, sales call summary, or any unstructured input — you extract the
core signal and return a structured PM brief.

RULES:
- Return ONLY valid JSON. No prose, no explanation, no markdown fences.
- Be direct and specific. No padding or hedge language.
- If information is genuinely missing, use null — do not invent.
- metrics must be measurable (include numbers or testable conditions).
- assumption must be something that, if wrong, would invalidate the approach.

JSON SCHEMA (return exactly this structure):
{
  "problem": "One sentence. What is broken or missing for whom.",
  "affected": "Who is affected and how. Be specific about user segment.",
  "metrics": [
    "First measurable success criterion (include baseline or target if inferable)",
    "Second measurable success criterion"
  ],
  "assumption": "The single most critical assumption to validate before building.",
  "confidence": "high | medium | low — your confidence given the input quality",
  "missing_context": "What would most improve this brief, or null if sufficient"
}"""

# ── MODEL SETUP ───────────────────────────────────────────────────────────
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=0.2,       # low temp = more consistent structured output
        max_output_tokens=800,
    ),
)

# ── CORE FUNCTION ─────────────────────────────────────────────────────────
def generate_brief(raw_input: str, context: str = "") -> dict:
    """
    Generate a structured PM brief from raw feedback.

    Args:
        raw_input: The raw feedback text (Slack thread, notes, complaints, etc.)
        context:   Optional product area, team, or relevant background

    Returns:
        dict: Structured brief matching the schema above
    """
    user_message = f"Input: {raw_input}"
    if context:
        user_message += f"\n\nContext: {context}"

    response = model.generate_content(user_message)
    raw_output = response.text.strip()

    # Strip markdown fences if model adds them despite instructions
    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
        raw_output = raw_output.strip()

    return json.loads(raw_output)


# ── CLI ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate a PM brief from raw feedback")
    parser.add_argument("--input",   "-i", type=str, help="Feedback text (inline)")
    parser.add_argument("--file",    "-f", type=str, help="Path to .txt file with feedback")
    parser.add_argument("--context", "-c", type=str, default="", help="Optional context")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as f:
            raw_input = f.read()
    elif args.input:
        raw_input = args.input
    else:
        # Default demo — works out of the box
        raw_input = (
            "Sarah from enterprise sales pinged me — Acme Corp is threatening to churn. "
            "They say onboarding took 3 weeks instead of the promised 1, their admin "
            "couldn't figure out how to set up SSO, and two of their power users say "
            "the bulk export feature is 'broken'. The CSM is flagging that we've had "
            "3 similar complaints this quarter from other mid-market accounts."
        )
        print("Running with demo input...\n")

    try:
        result = generate_brief(raw_input, context=args.context)
        print(json.dumps(result, indent=2))
    except json.JSONDecodeError as e:
        print(f"ERROR: Model returned non-JSON output: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
