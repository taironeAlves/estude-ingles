import random
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_connection

router = APIRouter(prefix="/api/training", tags=["training"])


class CheckIn(BaseModel):
    id: int
    answer: str


def _is_correct(answer: str, word: str) -> bool:
    return answer.strip().lower() == word.strip().lower()


def _blank_sentence(sentence: str, word: str) -> Optional[str]:
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    if not pattern.search(sentence):
        return None
    return pattern.sub("_____", sentence, count=1)


@router.get("/listen-and-type")
def new_listen_and_type():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, audio_filename FROM words WHERE audio_filename IS NOT NULL"
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(400, "Nenhuma palavra com áudio disponível ainda")
    chosen = random.choice(rows)
    return {"id": chosen["id"], "audio_url": f"/audio/{chosen['audio_filename']}"}


@router.post("/listen-and-type/check")
def check_listen_and_type(payload: CheckIn):
    conn = get_connection()
    row = conn.execute("SELECT * FROM words WHERE id = ?", (payload.id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Palavra não encontrada")
    return {
        "correct": _is_correct(payload.answer, row["word"]),
        "word": row["word"],
        "translation": row["translation"],
    }


@router.get("/fill-blank")
def new_fill_blank():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, word, example_sentence FROM words "
        "WHERE example_sentence IS NOT NULL AND example_sentence != ''"
    ).fetchall()
    conn.close()

    candidates = []
    for row in rows:
        blanked = _blank_sentence(row["example_sentence"], row["word"])
        if blanked:
            candidates.append({"id": row["id"], "sentence": blanked})

    if not candidates:
        raise HTTPException(400, "Nenhuma frase de exemplo disponível ainda")
    return random.choice(candidates)


@router.post("/fill-blank/check")
def check_fill_blank(payload: CheckIn):
    conn = get_connection()
    row = conn.execute("SELECT * FROM words WHERE id = ?", (payload.id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Palavra não encontrada")
    return {
        "correct": _is_correct(payload.answer, row["word"]),
        "word": row["word"],
        "translation": row["translation"],
        "example_sentence": row["example_sentence"],
    }
