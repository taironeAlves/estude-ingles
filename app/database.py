import sqlite3

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE COLLATE NOCASE,
            translation TEXT NOT NULL,
            example_sentence TEXT,
            audio_filename TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # Migração aditiva: áudio humanizado (OmniVoice) da frase de exemplo,
    # opcional e separado do áudio da palavra (edge-tts).
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(words)")}
    if "example_audio_filename" not in existing_columns:
        conn.execute("ALTER TABLE words ADD COLUMN example_audio_filename TEXT")
    if "example_audio_source" not in existing_columns:
        # "omnivoice" (humanizado) ou "edge-tts" (fallback quando o OmniVoice falha)
        conn.execute("ALTER TABLE words ADD COLUMN example_audio_source TEXT")

    conn.commit()
    conn.close()
