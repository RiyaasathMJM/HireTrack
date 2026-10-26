# ── database.py ───────────────────────────────────────────────────────────────
# HireTrack — MySQL Database layer
# Handles: connection pool, schema creation, per-request connection via Flask g
# ──────────────────────────────────────────────────────────────────────────────

import os
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from flask import g

# ── Connection pool (created once when module is imported) ─────────────────────
# Pool keeps N connections open and reuses them across requests.
# Thread-safe — Flask dev server is multi-threaded.

_pool: pooling.MySQLConnectionPool | None = None


def _get_pool() -> pooling.MySQLConnectionPool:
    """
    Lazily initialise the connection pool on first use.
    Reads credentials from environment variables (loaded from .env by app.py).
    """
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="hiretrack_pool",
            pool_size=5,                        # max simultaneous connections
            pool_reset_session=True,
            host     = os.getenv("MYSQL_HOST",     "localhost"),
            port     = int(os.getenv("MYSQL_PORT", "3306")),
            user     = os.getenv("MYSQL_USER",     "root"),
            password = os.getenv("MYSQL_PASSWORD", ""),
            database = os.getenv("MYSQL_DATABASE", "hiretrack"),
            autocommit = False,
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
    if conn is None or not conn.is_connected():
        conn = _get_pool().get_connection()
        g._db_conn = conn
    return conn


def get_cursor(conn=None):
    """
    Return a dictionary cursor (rows returned as dicts, not tuples).
    If no connection is provided, gets one from the pool via get_db().
    """
    if conn is None:
        conn = get_db()
    return conn.cursor(dictionary=True)


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
            conn.close()            # returns connection to pool
            g._db_conn = None


# ── Schema ─────────────────────────────────────────────────────────────────────
# Split into individual statements — MySQL does not support executescript().

_CREATE_JOB_DESCRIPTIONS = """
CREATE TABLE IF NOT EXISTS job_descriptions (
    id          INT          NOT NULL AUTO_INCREMENT,
    title       VARCHAR(255) NOT NULL,
    description LONGTEXT     NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

_CREATE_CANDIDATES = """
CREATE TABLE IF NOT EXISTS candidates (
    id          INT           NOT NULL AUTO_INCREMENT,

    -- Extracted from resume
    name        VARCHAR(255)  NOT NULL DEFAULT '',
    email       VARCHAR(255)           DEFAULT '',
    phone       VARCHAR(64)            DEFAULT '',
    skills      JSON                   DEFAULT (JSON_ARRAY()),

    -- Recruiter-managed
    stage       ENUM(
                    'applied',
                    'screening',
                    'interview',
                    'offer',
                    'rejected'
                )             NOT NULL DEFAULT 'applied',
    star_rating TINYINT                DEFAULT 0,
    notes       TEXT                   DEFAULT NULL,

    -- Resume content
    resume_text LONGTEXT               DEFAULT NULL,
    file_name   VARCHAR(255)           DEFAULT '',

    -- Match score vs a Job Description (0.0 – 100.0)
    match_score DOUBLE                 DEFAULT 0.0,
    jd_id       INT                    DEFAULT NULL,

    -- Timestamps
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    CONSTRAINT fk_candidate_jd
        FOREIGN KEY (jd_id)
        REFERENCES job_descriptions(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

_SCHEMA_STATEMENTS = [
    _CREATE_JOB_DESCRIPTIONS,
    _CREATE_CANDIDATES,
]


# ── Database initialisation ────────────────────────────────────────────────────

def create_database_if_missing():
    """
    Connect WITHOUT specifying a database and create it if it doesn't exist.
    This is separate from the pool because the pool requires the DB to exist.
    """
    db_name = os.getenv("MYSQL_DATABASE", "hiretrack")
    conn = mysql.connector.connect(
        host     = os.getenv("MYSQL_HOST",     "localhost"),
        port     = int(os.getenv("MYSQL_PORT", "3306")),
        user     = os.getenv("MYSQL_USER",     "root"),
        password = os.getenv("MYSQL_PASSWORD", ""),
    )
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    cursor.close()
    conn.close()


def init_db(app):
    """
    1. Create the MySQL database if it doesn't exist.
    2. Create all tables (safe — uses CREATE TABLE IF NOT EXISTS).
    Called once on server startup from app.py.
    """
    create_database_if_missing()

    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        for statement in _SCHEMA_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
        cursor.close()
