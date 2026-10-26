# ── app.py ────────────────────────────────────────────────────────────────────
# HireTrack — Flask application entry point  (Phase 1 · Step 1  — MySQL edition)
# ──────────────────────────────────────────────────────────────────────────────

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from database import get_db, close_db, init_db

# ── Load .env ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ── Optional dependency flags ──────────────────────────────────────────────────
try:
    from pypdf import PdfReader          # noqa: F401
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document            # noqa: F401
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import openai                        # noqa: F401
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ── Constants ──────────────────────────────────────────────────────────────────
PIPELINE_STAGES = ["applied", "screening", "interview", "offer", "rejected"]

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── App factory ────────────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)

    # Allow all origins for /api/* (React dev on :5173 + production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Return MySQL connection to pool after every request
    app.teardown_appcontext(close_db)

    # Shared config accessible to all route handlers
    app.config["PIPELINE_STAGES"] = PIPELINE_STAGES
    app.config["UPLOAD_DIR"]      = str(UPLOAD_DIR)
    app.config["BASE_DIR"]        = str(BASE_DIR)
    app.config["HAS_PYPDF"]       = HAS_PYPDF
    app.config["HAS_DOCX"]        = HAS_DOCX
    app.config["HAS_OPENAI"]      = HAS_OPENAI

    # Register informational routes
    register_meta_routes(app)

    return app


def register_meta_routes(app: Flask) -> None:
    """
    Lightweight endpoints that return server/DB status.
    No candidate or JD data is read here.
    """

    # ── GET /api/health ───────────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        """
        Health-check endpoint.

        Example response:
        {
            "status":       "ok",
            "database":     "mysql",
            "db_host":      "localhost",
            "ai_available": false,
            "pypdf":        true,
            "docx":         true
        }
        """
        db_ok = False
        db_error = None
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            db_ok = True
        except Exception as e:
            db_error = str(e)

        ai_available = bool(
            app.config["HAS_OPENAI"] and os.getenv("OPENAI_API_KEY", "")
        )

        response = {
            "status":       "ok" if db_ok else "degraded",
            "database":     "mysql",
            "db_host":      os.getenv("MYSQL_HOST", "localhost"),
            "db_name":      os.getenv("MYSQL_DATABASE", "hiretrack"),
            "ai_available": ai_available,
            "pypdf":        app.config["HAS_PYPDF"],
            "docx":         app.config["HAS_DOCX"],
        }

        if db_error:
            response["db_error"] = db_error

        return jsonify(response)

    # ── GET /api/stages ───────────────────────────────────────────────────────
    @app.route("/api/stages", methods=["GET"])
    def get_stages():
        """
        Returns the ordered pipeline stage list.
        Frontend uses this for dropdowns + kanban columns.

        Example response:
        ["applied", "screening", "interview", "offer", "rejected"]
        """
        return jsonify(app.config["PIPELINE_STAGES"])


# ── Module-level app (for flask run / gunicorn) ────────────────────────────────
app = create_app()

# ── Dev server entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Create DB + tables before accepting requests
    init_db(app)

    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print(f"\n[HireTrack] Backend (MySQL) starting on http://localhost:{port}")
    print(f"   DB host  : {os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}")
    print(f"   DB name  : {os.getenv('MYSQL_DATABASE', 'hiretrack')}")
    print(f"   pypdf    : {'OK' if HAS_PYPDF  else 'MISSING'}")
    print(f"   docx     : {'OK' if HAS_DOCX   else 'MISSING'}")
    print(f"   openai   : {'OK' if HAS_OPENAI  else 'MISSING'}")
    print(f"   AI key   : {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET (heuristic fallback)'}")
    print()

    app.run(debug=debug, port=port)
