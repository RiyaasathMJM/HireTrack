# ── matcher.py ────────────────────────────────────────────────────────────────
# HireTrack — Deterministic match score engine
# Computes a skill-overlap score between a resume and a job description.
# No AI, no randomness — same inputs always produce the same score.
# ──────────────────────────────────────────────────────────────────────────────

from parsers import extract_skills


def compute_match_score(resume_text: str, job_description: str) -> float:
    """
    Deterministic skill-overlap score in the range [0.0, 100.0].

    Algorithm:
        1. Extract skills from the job description  →  required_skills (set)
        2. Extract skills from the resume           →  candidate_skills (set)
        3. Compute overlap = required_skills ∩ candidate_skills
        4. Score = |overlap| / |required_skills| × 100

    Returns 0.0 if the job description contains no recognised skills.

    Examples:
        JD skills    = {python, docker, aws, fastapi, postgresql}  → 5 total
        Resume skills = {python, docker, aws, react}
        Overlap      = {python, docker, aws}                        → 3 matched
        Score        = 3 / 5 × 100 = 60.0
    """
    if not job_description.strip():
        return 0.0

    required_skills  = set(extract_skills(job_description))
    candidate_skills = set(extract_skills(resume_text))

    if not required_skills:
        return 0.0

    overlap = required_skills & candidate_skills
    score   = round(len(overlap) / len(required_skills) * 100, 1)
    return score


def compute_skill_gap(resume_text: str, job_description: str) -> dict:
    """
    Returns a breakdown of matched and missing skills.
    Used by the frontend to display a skill gap analysis per candidate.

    Returns:
    {
        "score":    60.0,
        "matched":  ["python", "docker", "aws"],
        "missing":  ["fastapi", "postgresql"],
        "total_required": 5
    }
    """
    required_skills  = set(extract_skills(job_description))
    candidate_skills = set(extract_skills(resume_text))

    matched = sorted(required_skills & candidate_skills)
    missing = sorted(required_skills - candidate_skills)

    score = (
        round(len(matched) / len(required_skills) * 100, 1)
        if required_skills else 0.0
    )

    return {
        "score":          score,
        "matched":        matched,
        "missing":        missing,
        "total_required": len(required_skills),
    }
