"""
db_manager.py — Todas las operaciones de base de datos SQLite.
Usa consultas parametrizadas para prevenir inyección SQL.
"""
from __future__ import annotations

import pickle
import sqlite3
from datetime import datetime
from typing import Optional

import numpy as np

from config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    """Crea todas las tablas y directorios necesarios si no existen."""
    from config import LOGS_DIR
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                department  TEXT    NOT NULL DEFAULT '',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                active      INTEGER  DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                embedding     BLOB    NOT NULL,
                quality_score REAL    NOT NULL DEFAULT 1.0,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS access_logs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                user_name  TEXT,
                department TEXT,
                timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL,
                status     TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_embeddings_user
                ON embeddings(user_id);

            CREATE INDEX IF NOT EXISTS idx_logs_timestamp
                ON access_logs(timestamp);
        """)


# ── Usuarios ──────────────────────────────────────────────────────────────────

def add_user(name: str, department: str) -> int:
    """Inserta un nuevo usuario. Retorna su id."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, department, created_at) VALUES (?, ?, ?)",
            (name.strip(), department.strip(), now),
        )
        return cur.lastrowid


def update_user(user_id: int, name: str, department: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET name=?, department=? WHERE id=?",
            (name.strip(), department.strip(), user_id),
        )


def delete_user(user_id: int) -> None:
    """Elimina el usuario y sus embeddings.
    Los registros de acceso se conservan con user_id=NULL para mantener el historial."""
    with _connect() as conn:
        # Desvincular logs (mantener historial, romper FK antes de borrar usuario)
        conn.execute(
            "UPDATE access_logs SET user_id = NULL WHERE user_id = ?",
            (user_id,),
        )
        # Borrar embeddings manualmente (por si el CASCADE no aplica en esta versión)
        conn.execute("DELETE FROM embeddings WHERE user_id = ?", (user_id,))
        # Borrar usuario
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def get_all_active_users() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, department, created_at FROM users WHERE active=1 ORDER BY name"
        ).fetchall()
    return [dict(r) for r in rows]


def get_user_by_id(user_id: int) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, name, department, created_at FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


# ── Embeddings ────────────────────────────────────────────────────────────────

def add_embedding(
    user_id: int, embedding: np.ndarray, quality_score: float = 1.0
) -> None:
    blob = pickle.dumps(embedding.astype(np.float32))
    with _connect() as conn:
        conn.execute(
            "INSERT INTO embeddings (user_id, embedding, quality_score) VALUES (?, ?, ?)",
            (user_id, blob, quality_score),
        )


def delete_embeddings_for_user(user_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM embeddings WHERE user_id=?", (user_id,))


def load_all_embeddings() -> list[dict]:
    """
    Carga todos los embeddings con datos del usuario asociado.
    Retorna lista de {user_id, name, department, embedding}.
    Usado para construir el caché en RAM.
    """
    with _connect() as conn:
        rows = conn.execute("""
            SELECT e.user_id, u.name, u.department, e.embedding
            FROM   embeddings e
            JOIN   users u ON u.id = e.user_id
            WHERE  u.active = 1
        """).fetchall()

    result = []
    for r in rows:
        try:
            emb = pickle.loads(r["embedding"])
            result.append({
                "user_id":    r["user_id"],
                "name":       r["name"],
                "department": r["department"],
                "embedding":  emb,
            })
        except Exception:
            continue
    return result


# ── Logs de acceso ────────────────────────────────────────────────────────────

def log_access(
    status: str,
    confidence: float = 0.0,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    department: Optional[str] = None,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        conn.execute(
            "INSERT INTO access_logs "
            "(user_id, user_name, department, confidence, status, timestamp) VALUES (?,?,?,?,?,?)",
            (user_id, user_name, department, round(confidence, 2), status, now),
        )


def get_recent_logs(limit: int = 300) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, user_name, department, timestamp, confidence, status
            FROM   access_logs
            ORDER  BY timestamp DESC
            LIMIT  ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]
