# HireTrack


A lightweight applicant tracking system for recruiters sorting through hundreds
of applications. Upload resumes, auto-extract candidate details, search/filter,
move candidates through a pipeline, and optionally get AI summaries and JD match
scores.

**Stack:** Flask (Python) · React + TypeScript (Vite) · SQLite · optional OpenAI

---

## Features

- Bulk upload resumes (PDF / DOCX / TXT)
- Auto-extract name, email, phone, skills
- Search across name, email, skills, resume text
- Filter by pipeline stage
- Pipeline: applied → screening → interview → offer → rejected
- Star rating + free-text notes per candidate
- JD match score (deterministic, no AI required)
- Optional AI summarize per candidate (falls back to heuristic if no API key)

---


