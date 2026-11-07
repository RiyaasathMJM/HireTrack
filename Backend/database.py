# ── database.py ───────────────────────────────────────────────────────────────
# HireTrack — PostgreSQL (Supabase) Database layer
# Handles: connection pool, schema creation, per-request connection via Flask g
# ──────────────────────────────────────────────────────────────────────────────

import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from flask import g

# ── Connection pool (created once when module is imported) ─────────────────────
_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """
    Lazily initialise the connection pool on first use.
    Reads credentials from environment variables (loaded from .env by app.py).
    Supports both individual params and a full DATABASE_URL.
    """
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL", "")
        if database_url:
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=database_url,
            )
        else:
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                host     = os.getenv("PG_HOST",     "localhost"),
                port     = int(os.getenv("PG_PORT",  "5432")),
                user     = os.getenv("PG_USER",     "postgres"),
                password = os.getenv("PG_PASSWORD", ""),
                dbname   = os.getenv("PG_DATABASE", "postgres"),
                sslmode  = os.getenv("PG_SSLMODE",  "require"),
            )
    return _pool


# ── Per-request connection ─────────────────────────────────────────────────────

def get_db():
    """
    Borrow a connection from the pool for this request.
    Stored on Flask's g object so it's shared within one request
    and returned to the pool after the request ends.
    """
    conn = getattr(g, "_db_conn", None)
    if conn is None or conn.closed:
        conn = _get_pool().getconn()
        g._db_conn = conn
    return conn


def get_cursor(conn=None):
    """
    Return a RealDictCursor (rows returned as dicts, not tuples).
    If no connection is provided, gets one from the pool via get_db().
    """
    if conn is None:
        conn = get_db()
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def close_db(exc=None):
    """
    Return the borrowed connection back to the pool.
    Called automatically via app.teardown_appcontext after every request.
    """
    conn = getattr(g, "_db_conn", None)
    if conn is not None:
        try:
            if exc is None:
                conn.commit()       # commit any uncommitted work
            else:
                conn.rollback()     # rollback on error
        finally:
            _get_pool().putconn(conn)   # returns connection to pool
            g._db_conn = None


# ── Schema ─────────────────────────────────────────────────────────────────────

_CREATE_JOB_DESCRIPTIONS = """
CREATE TABLE IF NOT EXISTS job_descriptions (
    id          SERIAL       NOT NULL,
    title       VARCHAR(255) NOT NULL,
    description TEXT         NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id)
);
"""

_CREATE_CANDIDATES = """
CREATE TABLE IF NOT EXISTS candidates (
    id          SERIAL        NOT NULL,

    -- Extracted from resume
    name        VARCHAR(255)  NOT NULL DEFAULT '',
    email       VARCHAR(255)           DEFAULT '',
    phone       VARCHAR(64)            DEFAULT '',
    skills      JSONB                  DEFAULT '[]'::jsonb,

    -- Recruiter-managed
    stage       VARCHAR(32)   NOT NULL DEFAULT 'applied',
    star_rating SMALLINT               DEFAULT 0,
    notes       TEXT                   DEFAULT NULL,

    -- Resume content
    resume_text TEXT                   DEFAULT NULL,
    file_name   VARCHAR(255)           DEFAULT '',

    -- Match score vs a Job Description (0.0 – 100.0)
    match_score DOUBLE PRECISION       DEFAULT 0.0,
    jd_id       INT                    DEFAULT NULL,

    -- Timestamps
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP     NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id),
    CONSTRAINT fk_candidate_jd
        FOREIGN KEY (jd_id)
        REFERENCES job_descriptions(id)
        ON DELETE SET NULL
);
"""

# Trigger to auto-update updated_at on candidates
_CREATE_UPDATE_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';
"""

_CREATE_CANDIDATES_TRIGGER = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_candidates_updated_at'
  ) THEN
    CREATE TRIGGER set_candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
  END IF;
END;
$$;
"""

_CREATE_JD_TRIGGER = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_jd_updated_at'
  ) THEN
    CREATE TRIGGER set_jd_updated_at
    BEFORE UPDATE ON job_descriptions
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
  END IF;
END;
$$;
"""

_SCHEMA_STATEMENTS = [
    _CREATE_JOB_DESCRIPTIONS,
    _CREATE_CANDIDATES,
    _CREATE_UPDATE_TRIGGER_FN,
    _CREATE_CANDIDATES_TRIGGER,
    _CREATE_JD_TRIGGER,
]


# ── Database initialisation ────────────────────────────────────────────────────

def init_db(app):
    """
    Create all tables (safe — uses CREATE TABLE IF NOT EXISTS).
    Called once on server startup from app.py.
    For PostgreSQL/Supabase, the database already exists.
    """
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        for statement in _SCHEMA_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
        cursor.close()
