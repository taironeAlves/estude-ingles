from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import AUDIO_DIR
from ..database import get_connection
from ..tts import ensure_audio

router = APIRouter(prefix="/api/words", tags=["words"])


class WordIn(BaseModel):
    word: str
    translation: str
    example_sentence: Optional[str] = None


class WordOut(BaseModel):
    id: int
    word: str
    translation: str
    example_sentence: Optional[str] = None
    audio_filename: Optional[str] = None
    created_at: str


@router.get("", response_model=list[WordOut])
def list_words(q: Optional[str] = None):
    conn = get_connection()
    if q:
        like = f"%{q}%"
        rows = conn.execute(
            "SELECT * FROM words WHERE word LIKE ? OR translation LIKE ? ORDER BY created_at DESC",
            (like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM words ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("", response_model=WordOut)
async def add_word(payload: WordIn):
    word = payload.word.strip()
    if not word:
        raise HTTPException(400, "A palavra não pode ser vazia")
    translation = payload.translation.strip()
    if not translation:
        raise HTTPException(400, "A tradução não pode ser vazia")
    example = payload.example_sentence.strip() if payload.example_sentence else None

    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM words WHERE word = ? COLLATE NOCASE", (word,)
    ).fetchone()

    if existing:
        word_id = existing["id"]
        new_translation = translation or existing["translation"]
        new_example = example if example is not None else existing["example_sentence"]
        conn.execute(
            "UPDATE words SET translation = ?, example_sentence = ? WHERE id = ?",
            (new_translation, new_example, word_id),
        )
        conn.commit()
    else:
        cursor = conn.execute(
            "INSERT INTO words (word, translation, example_sentence, audio_filename) VALUES (?, ?, ?, NULL)",
            (word, translation, example),
        )
        conn.commit()
        word_id = cursor.lastrowid

    row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    conn.close()

    audio_filename = await ensure_audio(word_id, row["word"], row["audio_filename"])
    if audio_filename != row["audio_filename"]:
        conn = get_connection()
        conn.execute("UPDATE words SET audio_filename = ? WHERE id = ?", (audio_filename, word_id))
        conn.commit()
        row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        conn.close()

    return dict(row)


@router.delete("/{word_id}")
def delete_word(word_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Palavra não encontrada")
    conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()

    if row["audio_filename"]:
        audio_path = AUDIO_DIR / row["audio_filename"]
        if audio_path.exists():
            audio_path.unlink()

    return {"ok": True}
