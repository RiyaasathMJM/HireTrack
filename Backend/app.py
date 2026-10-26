"""
HireTrack — Applicant Tracking System
Flask backend with SQLite storage
"""

import os
import re
import json
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, g
from flask_cors import CORS

# ── optional deps (graceful fallback) ─────────────────────────────────────────
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

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ── app setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "hiretrack.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

PIPELINE_STAGES = ["applied", "screening", "interview", "offer", "rejected"]

# ── database ───────────────────────────────────────────────────────────────────
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(str(DB_PATH))
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS candidates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL DEFAULT '',
                email       TEXT    DEFAULT '',
                phone       TEXT    DEFAULT '',
                skills      TEXT    DEFAULT '[]',
                stage       TEXT    NOT NULL DEFAULT 'applied',
                star_rating INTEGER DEFAULT 0,
                notes       TEXT    DEFAULT '',
                resume_text TEXT    DEFAULT '',
                file_name   TEXT    DEFAULT '',
                match_score REAL    DEFAULT 0,
                created_at  TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            );
        """)
        db.commit()

# ── text extraction ────────────────────────────────────────────────────────────
def extract_text_from_file(file_path: str, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    try:
        if ext == ".pdf" and HAS_PYPDF:
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext in (".docx", ".doc") and HAS_DOCX:
            doc = DocxDocument(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        else:  # .txt or fallback
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        return f"[Error extracting text: {e}]"

# ── extraction helpers ─────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(
    r"(\+?\d[\d\s\-\(\)]{7,}\d)"
)

COMMON_SKILLS = [
    # Languages
    "python","javascript","typescript","java","c++","c#","ruby","go","rust","swift","kotlin",
    "php","scala","r","matlab","bash","shell","perl","haskell","lua","dart","elixir",
    # Frontend
    "react","vue","angular","svelte","html","css","sass","less","tailwind","bootstrap",
    "next.js","nuxt","gatsby","webpack","vite","redux","mobx","graphql",
    # Backend
    "node.js","express","django","flask","fastapi","spring","rails","laravel","gin","actix",
    # Data / ML
    "sql","postgresql","mysql","sqlite","mongodb","redis","elasticsearch","cassandra",
    "pandas","numpy","scikit-learn","tensorflow","pytorch","keras","spark","kafka","hadoop",
    # Cloud / DevOps
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","jenkins","github actions",
    "ci/cd","linux","nginx","apache",
    # Other
    "rest api","microservices","agile","scrum","git","jira","figma","photoshop",
]

def extract_name(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:5]:
        # Heuristic: short line with mostly letters / spaces
        if 2 <= len(line.split()) <= 5 and re.match(r"^[A-Za-z\s\.\-]+$", line):
            return line
    return ""

def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text)
    return m.group() if m else ""

def extract_phone(text: str) -> str:
    m = PHONE_RE.search(text)
    return m.group().strip() if m else ""

def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lower):
            found.append(skill)
    return found

# ── match score ────────────────────────────────────────────────────────────────
def compute_match_score(resume_text: str, job_description: str) -> float:
    """Deterministic skill-overlap score in [0, 100]."""
    if not job_description.strip():
        return 0.0
    job_skills  = set(extract_skills(job_description))
    res_skills  = set(extract_skills(resume_text))
    if not job_skills:
        return 0.0
    overlap = job_skills & res_skills
    return round(len(overlap) / len(job_skills) * 100, 1)

# ── AI summarize ───────────────────────────────────────────────────────────────
def heuristic_summary(resume_text: str) -> str:
    lines = [l.strip() for l in resume_text.splitlines() if len(l.strip()) > 20][:15]
    snippet = " ".join(lines)[:800]
    skills  = extract_skills(resume_text)
    skills_str = ", ".join(skills[:10]) if skills else "N/A"
    return (
        f"Candidate profile extracted from resume.\n"
        f"Key skills identified: {skills_str}.\n"
        f"Resume snippet: {snippet[:300]}..."
    )

def ai_summarize(resume_text: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if HAS_OPENAI and api_key:
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": (
                        "You are a recruiting assistant. Summarize the candidate's resume "
                        "in 3-4 concise bullet points covering experience, skills, and standout qualities."
                    )},
                    {"role": "user", "content": resume_text[:3000]},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return heuristic_summary(resume_text) + f"\n\n[AI error: {e}]"
    return heuristic_summary(resume_text)

# ── API routes ──────────────────────────────────────────────────────────────────

def candidate_to_dict(row) -> dict:
    d = dict(row)
    try:
        d["skills"] = json.loads(d.get("skills") or "[]")
    except Exception:
        d["skills"] = []
    return d

# ---- Upload / create candidate -----------------------------------------------
@app.route("/api/candidates", methods=["POST"])
def create_candidate():
    files  = request.files.getlist("resumes")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    db  = get_db()
    now = datetime.utcnow().isoformat()
    created = []

    for file in files:
        filename  = file.filename or "resume.txt"
        save_path = UPLOAD_DIR / filename
        # avoid collisions
        counter = 1
        stem    = Path(filename).stem
        suffix  = Path(filename).suffix
        while save_path.exists():
            save_path = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
            counter += 1
        file.save(str(save_path))

        text   = extract_text_from_file(str(save_path), filename)
        name   = extract_name(text)
        email  = extract_email(text)
        phone  = extract_phone(text)
        skills = extract_skills(text)

        cur = db.execute(
            """INSERT INTO candidates
               (name, email, phone, skills, stage, star_rating, notes,
                resume_text, file_name, match_score, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (name, email, phone, json.dumps(skills), "applied", 0, "",
             text, filename, 0.0, now, now),
        )
        db.commit()
        row = db.execute("SELECT * FROM candidates WHERE id=?", (cur.lastrowid,)).fetchone()
        created.append(candidate_to_dict(row))

    return jsonify(created), 201


# ---- List candidates ---------------------------------------------------------
@app.route("/api/candidates", methods=["GET"])
def list_candidates():
    db      = get_db()
    stage   = request.args.get("stage", "")
    keyword = request.args.get("keyword", "").lower()

    query  = "SELECT * FROM candidates WHERE 1=1"
    params: list = []

    if stage and stage in PIPELINE_STAGES:
        query  += " AND stage=?"
        params.append(stage)

    if keyword:
        query  += " AND (LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(resume_text) LIKE ? OR LOWER(skills) LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw, kw])

    query += " ORDER BY created_at DESC"
    rows   = db.execute(query, params).fetchall()
    return jsonify([candidate_to_dict(r) for r in rows])


# ---- Get single candidate ---------------------------------------------------
@app.route("/api/candidates/<int:cid>", methods=["GET"])
def get_candidate(cid: int):
    db  = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(candidate_to_dict(row))


# ---- Update candidate -------------------------------------------------------
@app.route("/api/candidates/<int:cid>", methods=["PATCH"])
def update_candidate(cid: int):
    db   = get_db()
    row  = db.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    data    = request.get_json(force=True) or {}
    allowed = {"name", "email", "phone", "stage", "star_rating", "notes", "skills", "match_score"}
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return jsonify({"error": "Nothing to update"}), 400

    if "stage" in updates and updates["stage"] not in PIPELINE_STAGES:
        return jsonify({"error": f"Invalid stage. Must be one of {PIPELINE_STAGES}"}), 400

    if "skills" in updates and isinstance(updates["skills"], list):
        updates["skills"] = json.dumps(updates["skills"])

    updates["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    db.execute(
        f"UPDATE candidates SET {set_clause} WHERE id=?",
        list(updates.values()) + [cid],
    )
    db.commit()
    row = db.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    return jsonify(candidate_to_dict(row))


# ---- Delete candidate -------------------------------------------------------
@app.route("/api/candidates/<int:cid>", methods=["DELETE"])
def delete_candidate(cid: int):
    db  = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404
    db.execute("DELETE FROM candidates WHERE id=?", (cid,))
    db.commit()
    return jsonify({"deleted": cid})


# ---- Match score against JD -------------------------------------------------
@app.route("/api/candidates/<int:cid>/match", methods=["POST"])
def match_candidate(cid: int):
    db  = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    jd   = data.get("job_description", "")
    if not jd:
        return jsonify({"error": "job_description required"}), 400

    score = compute_match_score(row["resume_text"], jd)
    db.execute(
        "UPDATE candidates SET match_score=?, updated_at=? WHERE id=?",
        (score, datetime.utcnow().isoformat(), cid),
    )
    db.commit()
    return jsonify({"match_score": score})


# ---- Bulk match all candidates against JD -----------------------------------
@app.route("/api/match-all", methods=["POST"])
def match_all():
    data = request.get_json(force=True) or {}
    jd   = data.get("job_description", "")
    if not jd:
        return jsonify({"error": "job_description required"}), 400

    db   = get_db()
    rows = db.execute("SELECT id, resume_text FROM candidates").fetchall()
    now  = datetime.utcnow().isoformat()
    results = []
    for r in rows:
        score = compute_match_score(r["resume_text"], jd)
        db.execute("UPDATE candidates SET match_score=?, updated_at=? WHERE id=?",
                   (score, now, r["id"]))
        results.append({"id": r["id"], "match_score": score})
    db.commit()
    return jsonify(results)


# ---- AI Summarize -----------------------------------------------------------
@app.route("/api/candidates/<int:cid>/summarize", methods=["POST"])
def summarize_candidate(cid: int):
    db  = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    summary = ai_summarize(row["resume_text"])
    return jsonify({
        "summary": summary,
        "ai_powered": bool(HAS_OPENAI and os.getenv("OPENAI_API_KEY")),
    })


# ---- Pipeline stages (meta) ------------------------------------------------
@app.route("/api/stages", methods=["GET"])
def get_stages():
    return jsonify(PIPELINE_STAGES)


# ---- Health check -----------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "ai_available": bool(HAS_OPENAI and os.getenv("OPENAI_API_KEY")),
        "pypdf": HAS_PYPDF,
        "docx": HAS_DOCX,
    })


# ── main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, port=port)
