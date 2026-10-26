# ── app.py ────────────────────────────────────────────────────────────────────
# HireTrack — Flask application  (Phase 1 · Step 2 — All routes)
# ──────────────────────────────────────────────────────────────────────────────

import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify, g
from flask_cors import CORS

from database import get_db, get_cursor, close_db, init_db
from parsers  import parse_resume
from matcher  import compute_match_score, compute_skill_gap
from summarizer import ai_summarize

# ── Load .env ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ── Optional dependency flags ──────────────────────────────────────────────────
try:
    from pypdf import PdfReader; HAS_PYPDF = True       # noqa: E702, F401
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document; HAS_DOCX = True          # noqa: E702, F401
except ImportError:
    HAS_DOCX = False

try:
    import openai; HAS_OPENAI = True                    # noqa: E702, F401
except ImportError:
    HAS_OPENAI = False

# ── Constants ──────────────────────────────────────────────────────────────────
PIPELINE_STAGES = ["applied", "screening", "interview", "offer", "rejected"]
UPLOAD_DIR      = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def now_iso() -> str:
    """Current UTC datetime as ISO-8601 string."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row: dict) -> dict:
    """
    Post-process a candidate row returned by MySQL dictionary cursor.
    Converts datetime objects → strings, JSON skills string → list.
    """
    d = dict(row)
    # MySQL returns datetime objects — convert to string
    for field in ("created_at", "updated_at"):
        if isinstance(d.get(field), datetime):
            d[field] = d[field].isoformat()
    # skills stored as JSON string in DB
    if isinstance(d.get("skills"), str):
        try:
            d["skills"] = json.loads(d["skills"])
        except Exception:
            d["skills"] = []
    elif d.get("skills") is None:
        d["skills"] = []
    return d


def jd_row_to_dict(row: dict) -> dict:
    """Post-process a job_descriptions row."""
    d = dict(row)
    for field in ("created_at", "updated_at"):
        if isinstance(d.get(field), datetime):
            d[field] = d[field].isoformat()
    return d


# ── App factory ────────────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.teardown_appcontext(close_db)

    app.config["PIPELINE_STAGES"] = PIPELINE_STAGES
    app.config["UPLOAD_DIR"]      = str(UPLOAD_DIR)
    app.config["HAS_PYPDF"]       = HAS_PYPDF
    app.config["HAS_DOCX"]        = HAS_DOCX
    app.config["HAS_OPENAI"]      = HAS_OPENAI

    register_meta_routes(app)
    register_candidate_routes(app)
    register_jd_routes(app)

    return app


# ══════════════════════════════════════════════════════════════════════════════
# META ROUTES
# ══════════════════════════════════════════════════════════════════════════════

def register_meta_routes(app: Flask) -> None:

    @app.route("/api/health", methods=["GET"])
    def health():
        db_ok, db_error = False, None
        try:
            conn   = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            db_ok = True
        except Exception as e:
            db_error = str(e)

        res = {
            "status":       "ok" if db_ok else "degraded",
            "database":     "mysql",
            "db_host":      os.getenv("MYSQL_HOST", "localhost"),
            "db_name":      os.getenv("MYSQL_DATABASE", "hiretrack"),
            "ai_available": bool(HAS_OPENAI and os.getenv("OPENAI_API_KEY", "")),
            "pypdf":        HAS_PYPDF,
            "docx":         HAS_DOCX,
        }
        if db_error:
            res["db_error"] = db_error
        return jsonify(res)

    @app.route("/api/stages", methods=["GET"])
    def get_stages():
        return jsonify(PIPELINE_STAGES)


# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

def register_candidate_routes(app: Flask) -> None:

    # ── POST /api/candidates  (upload one or many resumes) ────────────────────
    @app.route("/api/candidates", methods=["POST"])
    def create_candidates():
        """
        Accept multipart/form-data with field name 'resumes'.
        Parses each file, extracts fields, inserts a row per file.
        Returns list of created candidate objects.
        """
        files = request.files.getlist("resumes")
        if not files or all(f.filename == "" for f in files):
            return jsonify({"error": "No files uploaded"}), 400

        conn    = get_db()
        cursor  = get_cursor(conn)
        created = []

        for file in files:
            filename  = file.filename or "resume.txt"
            save_path = UPLOAD_DIR / filename

            # Avoid filename collisions
            stem, suffix, counter = Path(filename).stem, Path(filename).suffix, 1
            while save_path.exists():
                save_path = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
                counter  += 1

            file.save(str(save_path))

            # Parse the file
            parsed = parse_resume(str(save_path), filename)

            cursor.execute(
                """
                INSERT INTO candidates
                    (name, email, phone, skills, stage, star_rating,
                     notes, resume_text, file_name, match_score,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    parsed["name"],
                    parsed["email"],
                    parsed["phone"],
                    json.dumps(parsed["skills"]),  # store as JSON string
                    "applied",
                    0,
                    "",
                    parsed["resume_text"],
                    filename,
                    0.0,
                    now_iso(),
                    now_iso(),
                ),
            )
            new_id = cursor.lastrowid
            conn.commit()

            cursor.execute("SELECT * FROM candidates WHERE id = %s", (new_id,))
            created.append(row_to_dict(cursor.fetchone()))

        cursor.close()
        return jsonify(created), 201


    # ── GET /api/candidates  (list with optional filters) ─────────────────────
    @app.route("/api/candidates", methods=["GET"])
    def list_candidates():
        """
        Query params:
          ?stage=applied          filter by pipeline stage
          ?keyword=python         search name, email, skills, resume_text
          ?sort=match_score       sort field (default: created_at)
          ?order=desc             sort direction (default: desc)
        """
        stage   = request.args.get("stage",   "").strip()
        keyword = request.args.get("keyword", "").strip().lower()
        sort    = request.args.get("sort",    "created_at")
        order   = request.args.get("order",   "desc").upper()

        # Whitelist sort fields to prevent SQL injection
        allowed_sorts = {"created_at", "updated_at", "match_score",
                         "star_rating", "name", "stage"}
        if sort not in allowed_sorts:
            sort = "created_at"
        if order not in ("ASC", "DESC"):
            order = "DESC"

        sql    = "SELECT * FROM candidates WHERE 1=1"
        params = []

        if stage and stage in PIPELINE_STAGES:
            sql   += " AND stage = %s"
            params.append(stage)

        if keyword:
            sql   += (" AND (LOWER(name) LIKE %s"
                      " OR LOWER(email) LIKE %s"
                      " OR LOWER(skills) LIKE %s"
                      " OR LOWER(resume_text) LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw])

        sql += f" ORDER BY {sort} {order}"

        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()

        return jsonify([row_to_dict(r) for r in rows])


    # ── GET /api/candidates/:id ───────────────────────────────────────────────
    @app.route("/api/candidates/<int:cid>", methods=["GET"])
    def get_candidate(cid: int):
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute("SELECT * FROM candidates WHERE id = %s", (cid,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return jsonify({"error": "Candidate not found"}), 404
        return jsonify(row_to_dict(row))


    # ── PATCH /api/candidates/:id  (partial update) ───────────────────────────
    @app.route("/api/candidates/<int:cid>", methods=["PATCH"])
    def update_candidate(cid: int):
        """
        Update any subset of editable fields:
          name, email, phone, stage, star_rating, notes, skills, match_score, jd_id
        """
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute("SELECT id FROM candidates WHERE id = %s", (cid,))
        if cursor.fetchone() is None:
            cursor.close()
            return jsonify({"error": "Candidate not found"}), 404

        data    = request.get_json(force=True) or {}
        allowed = {"name", "email", "phone", "stage",
                   "star_rating", "notes", "skills", "match_score", "jd_id"}
        updates = {k: v for k, v in data.items() if k in allowed}

        if not updates:
            cursor.close()
            return jsonify({"error": "No valid fields to update"}), 400

        # Validate stage
        if "stage" in updates and updates["stage"] not in PIPELINE_STAGES:
            cursor.close()
            return jsonify({
                "error": f"Invalid stage. Choose from: {PIPELINE_STAGES}"
            }), 400

        # Validate star_rating
        if "star_rating" in updates:
            rating = int(updates["star_rating"])
            if not (0 <= rating <= 5):
                cursor.close()
                return jsonify({"error": "star_rating must be 0–5"}), 400
            updates["star_rating"] = rating

        # Serialize skills list → JSON string
        if "skills" in updates and isinstance(updates["skills"], list):
            updates["skills"] = json.dumps(updates["skills"])

        updates["updated_at"] = now_iso()
        set_clause = ", ".join(f"{col} = %s" for col in updates)
        values     = list(updates.values()) + [cid]

        cursor.execute(
            f"UPDATE candidates SET {set_clause} WHERE id = %s", values
        )
        conn.commit()

        cursor.execute("SELECT * FROM candidates WHERE id = %s", (cid,))
        updated = cursor.fetchone()
        cursor.close()
        return jsonify(row_to_dict(updated))


    # ── DELETE /api/candidates/:id ────────────────────────────────────────────
    @app.route("/api/candidates/<int:cid>", methods=["DELETE"])
    def delete_candidate(cid: int):
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute("SELECT id FROM candidates WHERE id = %s", (cid,))
        if cursor.fetchone() is None:
            cursor.close()
            return jsonify({"error": "Candidate not found"}), 404

        cursor.execute("DELETE FROM candidates WHERE id = %s", (cid,))
        conn.commit()
        cursor.close()
        return jsonify({"deleted": cid})


    # ── POST /api/candidates/:id/match  (score vs pasted JD) ─────────────────
    @app.route("/api/candidates/<int:cid>/match", methods=["POST"])
    def match_candidate(cid: int):
        """
        Score a single candidate against an ad-hoc pasted job description.
        Body: { "job_description": "..." }
        """
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute("SELECT resume_text FROM candidates WHERE id = %s", (cid,))
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            return jsonify({"error": "Candidate not found"}), 404

        jd = (request.get_json(force=True) or {}).get("job_description", "")
        if not jd.strip():
            cursor.close()
            return jsonify({"error": "job_description is required"}), 400

        gap   = compute_skill_gap(row["resume_text"] or "", jd)
        score = gap["score"]

        cursor.execute(
            "UPDATE candidates SET match_score = %s, updated_at = %s WHERE id = %s",
            (score, now_iso(), cid),
        )
        conn.commit()
        cursor.close()

        return jsonify(gap)


    # ── POST /api/candidates/:id/summarize ────────────────────────────────────
    @app.route("/api/candidates/<int:cid>/summarize", methods=["POST"])
    def summarize_candidate(cid: int):
        """
        Summarize a candidate's resume.
        Optional body: { "job_description": "..." }
        If jd_id is set on the candidate and no JD is provided in the body,
        the saved JD is fetched automatically.
        """
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT resume_text, jd_id FROM candidates WHERE id = %s", (cid,)
        )
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            return jsonify({"error": "Candidate not found"}), 404

        body = request.get_json(force=True) or {}
        jd   = body.get("job_description", "")

        # If no JD in body, try to load saved JD via jd_id
        if not jd.strip() and row["jd_id"]:
            cursor.execute(
                "SELECT description FROM job_descriptions WHERE id = %s",
                (row["jd_id"],)
            )
            jd_row = cursor.fetchone()
            if jd_row:
                jd = jd_row["description"]

        cursor.close()
        result = ai_summarize(row["resume_text"] or "", jd)
        return jsonify(result)


# ══════════════════════════════════════════════════════════════════════════════
# JOB DESCRIPTION ROUTES
# ══════════════════════════════════════════════════════════════════════════════

def register_jd_routes(app: Flask) -> None:

    # ── POST /api/jobs  (create a saved JD) ──────────────────────────────────
    @app.route("/api/jobs", methods=["POST"])
    def create_jd():
        """
        Body: { "title": "Senior Python Dev", "description": "We need..." }
        Sarah types her JD here and saves it for repeated use.
        """
        data  = request.get_json(force=True) or {}
        title = data.get("title", "").strip()
        desc  = data.get("description", "").strip()

        if not title:
            return jsonify({"error": "title is required"}), 400
        if not desc:
            return jsonify({"error": "description is required"}), 400

        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            """
            INSERT INTO job_descriptions (title, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            """,
            (title, desc, now_iso(), now_iso()),
        )
        new_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            "SELECT * FROM job_descriptions WHERE id = %s", (new_id,)
        )
        jd = cursor.fetchone()
        cursor.close()
        return jsonify(jd_row_to_dict(jd)), 201


    # ── GET /api/jobs  (list all saved JDs) ──────────────────────────────────
    @app.route("/api/jobs", methods=["GET"])
    def list_jds():
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT * FROM job_descriptions ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        cursor.close()
        return jsonify([jd_row_to_dict(r) for r in rows])


    # ── GET /api/jobs/:id ─────────────────────────────────────────────────────
    @app.route("/api/jobs/<int:jid>", methods=["GET"])
    def get_jd(jid: int):
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT * FROM job_descriptions WHERE id = %s", (jid,)
        )
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return jsonify({"error": "Job description not found"}), 404
        return jsonify(jd_row_to_dict(row))


    # ── PATCH /api/jobs/:id  (edit a saved JD) ───────────────────────────────
    @app.route("/api/jobs/<int:jid>", methods=["PATCH"])
    def update_jd(jid: int):
        """
        Sarah can update the title or description of any saved JD.
        Body: { "title": "...", "description": "..." }
        """
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT id FROM job_descriptions WHERE id = %s", (jid,)
        )
        if cursor.fetchone() is None:
            cursor.close()
            return jsonify({"error": "Job description not found"}), 404

        data    = request.get_json(force=True) or {}
        allowed = {"title", "description"}
        updates = {k: v.strip() for k, v in data.items()
                   if k in allowed and isinstance(v, str) and v.strip()}

        if not updates:
            cursor.close()
            return jsonify({"error": "Provide title or description to update"}), 400

        updates["updated_at"] = now_iso()
        set_clause = ", ".join(f"{col} = %s" for col in updates)
        values     = list(updates.values()) + [jid]

        cursor.execute(
            f"UPDATE job_descriptions SET {set_clause} WHERE id = %s", values
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM job_descriptions WHERE id = %s", (jid,)
        )
        updated = cursor.fetchone()
        cursor.close()
        return jsonify(jd_row_to_dict(updated))


    # ── DELETE /api/jobs/:id ──────────────────────────────────────────────────
    @app.route("/api/jobs/<int:jid>", methods=["DELETE"])
    def delete_jd(jid: int):
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT id FROM job_descriptions WHERE id = %s", (jid,)
        )
        if cursor.fetchone() is None:
            cursor.close()
            return jsonify({"error": "Job description not found"}), 404

        # FK ON DELETE SET NULL — candidates.jd_id becomes NULL automatically
        cursor.execute(
            "DELETE FROM job_descriptions WHERE id = %s", (jid,)
        )
        conn.commit()
        cursor.close()
        return jsonify({"deleted": jid})


    # ── POST /api/jobs/:id/match-all  (bulk score all candidates) ────────────
    @app.route("/api/jobs/<int:jid>/match-all", methods=["POST"])
    def match_all_against_jd(jid: int):
        """
        Score every candidate against the saved JD identified by jid.
        Updates match_score and jd_id on every candidate row.
        Returns list of { id, name, match_score, matched, missing }.
        """
        conn   = get_db()
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT id, description FROM job_descriptions WHERE id = %s", (jid,)
        )
        jd_row = cursor.fetchone()
        if jd_row is None:
            cursor.close()
            return jsonify({"error": "Job description not found"}), 404

        jd_text = jd_row["description"]

        cursor.execute("SELECT id, name, resume_text FROM candidates")
        candidates = cursor.fetchall()

        results  = []
        ts       = now_iso()

        for c in candidates:
            gap   = compute_skill_gap(c["resume_text"] or "", jd_text)
            score = gap["score"]

            cursor.execute(
                """
                UPDATE candidates
                SET match_score = %s, jd_id = %s, updated_at = %s
                WHERE id = %s
                """,
                (score, jid, ts, c["id"]),
            )
            results.append({
                "id":          c["id"],
                "name":        c["name"],
                "match_score": score,
                "matched":     gap["matched"],
                "missing":     gap["missing"],
            })

        conn.commit()
        cursor.close()

        # Return sorted best-first
        results.sort(key=lambda r: r["match_score"], reverse=True)
        return jsonify(results)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

app = create_app()

if __name__ == "__main__":
    init_db(app)

    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print(f"\n[HireTrack] Backend (MySQL) starting on http://localhost:{port}")
    print(f"   DB     : {os.getenv('MYSQL_USER','root')}@{os.getenv('MYSQL_HOST','localhost')}:{os.getenv('MYSQL_PORT','3306')}/{os.getenv('MYSQL_DATABASE','hiretrack')}")
    print(f"   pypdf  : {'OK' if HAS_PYPDF  else 'MISSING'}")
    print(f"   docx   : {'OK' if HAS_DOCX   else 'MISSING'}")
    print(f"   AI key : {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET (heuristic fallback)'}")
    print()

    app.run(debug=debug, port=port)
