# ── summarizer.py ─────────────────────────────────────────────────────────────
# HireTrack — AI + heuristic resume summarizer
# Uses OpenAI GPT-3.5 if OPENAI_API_KEY is set, otherwise falls back to
# a deterministic heuristic that requires no internet connection.
# ──────────────────────────────────────────────────────────────────────────────

import os
from parsers import extract_skills

# ── Optional OpenAI import ─────────────────────────────────────────────────────

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ── Heuristic summary (always available, no API needed) ───────────────────────

def heuristic_summary(resume_text: str, job_description: str = "") -> str:
    """
    Build a summary from extracted fields — no AI, no internet.
    Optionally JD-aware: highlights matched and missing skills if JD is given.
    """
    skills = extract_skills(resume_text)
    skills_str = ", ".join(skills[:12]) if skills else "None detected"

    # Pull first few meaningful lines as a snippet
    lines   = [l.strip() for l in resume_text.splitlines() if len(l.strip()) > 25][:12]
    snippet = " ".join(lines)[:400]

    summary = (
        f"Key skills identified: {skills_str}.\n\n"
        f"Resume snippet: {snippet}..."
    )

    # JD-aware section
    if job_description.strip():
        from matcher import compute_skill_gap
        gap = compute_skill_gap(resume_text, job_description)
        matched_str = ", ".join(gap["matched"]) or "None"
        missing_str = ", ".join(gap["missing"]) or "None"
        summary += (
            f"\n\nMatch against Job Description: {gap['score']}%\n"
            f"  Matched skills : {matched_str}\n"
            f"  Missing skills : {missing_str}"
        )

    return summary


# ── AI summary (requires OPENAI_API_KEY) ──────────────────────────────────────

def ai_summarize(resume_text: str, job_description: str = "") -> dict:
    """
    Summarize a resume using OpenAI GPT-3.5-turbo if the API key is set.
    Falls back to heuristic_summary() gracefully.

    If a job_description is provided, the prompt asks GPT to evaluate fit
    against the JD (JD-aware mode).

    Returns:
    {
        "summary":    "...",
        "ai_powered": True / False
    }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    if HAS_OPENAI and api_key:
        try:
            client = openai.OpenAI(api_key=api_key)

            # ── Build prompt ──────────────────────────────────────────────────
            if job_description.strip():
                # JD-aware mode
                system_prompt = (
                    "You are an expert recruiting assistant. "
                    "Given a candidate's resume and a job description, "
                    "summarise in 4 bullet points: "
                    "1) candidate's experience level, "
                    "2) key matching skills, "
                    "3) skills missing from the JD, "
                    "4) overall fit verdict (Strong / Partial / Weak)."
                )
                user_content = (
                    f"JOB DESCRIPTION:\n{job_description[:1500]}\n\n"
                    f"RESUME:\n{resume_text[:2500]}"
                )
            else:
                # Generic resume summary
                system_prompt = (
                    "You are an expert recruiting assistant. "
                    "Summarise this resume in 3-4 bullet points covering: "
                    "experience, top skills, and one standout quality."
                )
                user_content = resume_text[:3000]

            response = client.chat.completions.create(
                model       = "gpt-3.5-turbo",
                messages    = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_content},
                ],
                max_tokens  = 350,
                temperature = 0.3,
            )

            return {
                "summary":    response.choices[0].message.content.strip(),
                "ai_powered": True,
            }

        except Exception as e:
            # API call failed — fall through to heuristic
            fallback = heuristic_summary(resume_text, job_description)
            return {
                "summary":    fallback + f"\n\n[AI error: {e}]",
                "ai_powered": False,
            }

    # No API key or openai not installed — use heuristic
    return {
        "summary":    heuristic_summary(resume_text, job_description),
        "ai_powered": False,
    }
