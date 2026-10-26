# ── parsers.py ────────────────────────────────────────────────────────────────
# HireTrack — Resume text extraction + field extraction
# Handles: PDF / DOCX / TXT → raw text → name, email, phone, skills
# ──────────────────────────────────────────────────────────────────────────────

import re
from pathlib import Path

# ── Optional deps (graceful fallback) ─────────────────────────────────────────

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text(file_path: str, filename: str) -> str:
    """
    Extract plain text from a resume file.
    Supports PDF, DOCX, and TXT. Falls back to plain read for unknown types.
    """
    ext = Path(filename).suffix.lower()
    try:
        if ext == ".pdf" and HAS_PYPDF:
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        elif ext in (".docx", ".doc") and HAS_DOCX:
            doc = DocxDocument(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        else:  # .txt or unknown — try UTF-8 plain read
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    except Exception as e:
        return f"[Error extracting text: {e}]"


# ── Regex patterns ─────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

_PHONE_RE = re.compile(
    r"(\+?\d[\d\s\-\(\)\.]{7,}\d)"
)

# ── Skills dictionary ──────────────────────────────────────────────────────────
# Matched against resume text using whole-word regex.

SKILLS_LIST = [
    # ── Programming Languages ──────────────────────────────────────────────────
    "python", "javascript", "typescript", "java", "c++", "c#", "ruby",
    "go", "rust", "swift", "kotlin", "php", "scala", "r", "matlab",
    "bash", "shell", "perl", "haskell", "lua", "dart", "elixir", "groovy",

    # ── Frontend ───────────────────────────────────────────────────────────────
    "react", "vue", "angular", "svelte", "html", "css", "sass", "less",
    "tailwind", "bootstrap", "next.js", "nuxt", "gatsby", "webpack",
    "vite", "redux", "mobx", "graphql", "jquery",

    # ── Backend ────────────────────────────────────────────────────────────────
    "node.js", "express", "django", "flask", "fastapi", "spring",
    "rails", "laravel", "gin", "actix", "nestjs", "asp.net",

    # ── Databases ──────────────────────────────────────────────────────────────
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis",
    "elasticsearch", "cassandra", "dynamodb", "firestore", "oracle",

    # ── Data / ML ──────────────────────────────────────────────────────────────
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "spark", "kafka", "hadoop", "airflow", "dbt", "tableau", "power bi",

    # ── Cloud / DevOps ─────────────────────────────────────────────────────────
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "github actions", "ci/cd", "linux",
    "nginx", "apache", "cloudflare",

    # ── Tools / Soft Skills ────────────────────────────────────────────────────
    "rest api", "microservices", "agile", "scrum", "git", "jira",
    "figma", "photoshop", "postman", "swagger",
]


# ── Field extractors ───────────────────────────────────────────────────────────

def extract_name(text: str) -> str:
    """
    Heuristic name extraction.
    Looks at the first 5 non-empty lines for a short line of 2-5 words
    containing only letters, spaces, dots, and hyphens.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 5 and re.match(r"^[A-Za-z\s\.\-]+$", line):
            return line
    return ""


def extract_email(text: str) -> str:
    """Extract first email address found in the text."""
    m = _EMAIL_RE.search(text)
    return m.group() if m else ""


def extract_phone(text: str) -> str:
    """Extract first phone number found in the text."""
    m = _PHONE_RE.search(text)
    return m.group().strip() if m else ""


def extract_skills(text: str) -> list[str]:
    """
    Match skills from SKILLS_LIST against the resume text.
    Uses whole-word regex so 'r' doesn't match inside 'ruby'.
    Returns deduplicated list preserving SKILLS_LIST order.
    """
    lower = text.lower()
    found = []
    for skill in SKILLS_LIST:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lower):
            found.append(skill)
    return found


def parse_resume(file_path: str, filename: str) -> dict:
    """
    Full pipeline: file → text → extracted fields.
    Returns a dict ready to INSERT into the candidates table.
    """
    text   = extract_text(file_path, filename)
    return {
        "resume_text": text,
        "name":        extract_name(text),
        "email":       extract_email(text),
        "phone":       extract_phone(text),
        "skills":      extract_skills(text),
    }
