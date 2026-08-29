from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import AUDIO_DIR
from ..database import get_connection
from ..omnivoice import generate_phrase_audio
from ..tts import ensure_audio, generate_phrase_fallback_audio

router = APIRouter(prefix="/api/words", tags=["words"])

# Sem termo de busca, mostramos só as últimas cadastradas para manter a
# lista leve; ao buscar, retornamos todos os resultados que baterem.
DEFAULT_LIST_LIMIT = 10


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
    example_audio_filename: Optional[str] = None
    example_audio_source: Optional[str] = None
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
        rows = conn.execute(
            "SELECT * FROM words ORDER BY created_at DESC LIMIT ?", (DEFAULT_LIST_LIMIT,)
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/count")
def count_words():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) AS total FROM words").fetchone()["total"]
    conn.close()
    return {"total": total}


async def _sync_audio(word_id: int, word: str, audio_filename: Optional[str]) -> str:
    """Generates audio for the word if it's missing and persists the filename."""
    new_filename = await ensure_audio(word_id, word, audio_filename)
    if new_filename != audio_filename:
        conn = get_connection()
        conn.execute("UPDATE words SET audio_filename = ? WHERE id = ?", (new_filename, word_id))
        conn.commit()
        conn.close()
    return new_filename


def _clean_payload(payload: WordIn) -> tuple[str, str, Optional[str]]:
    word = payload.word.strip()
    if not word:
        raise HTTPException(400, "A palavra não pode ser vazia")
    translation = payload.translation.strip()
    if not translation:
        raise HTTPException(400, "A tradução não pode ser vazia")
    example = payload.example_sentence.strip() if payload.example_sentence else None
    return word, translation, example


@router.post("", response_model=WordOut)
async def add_word(payload: WordIn):
    word, translation, example = _clean_payload(payload)

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

    result = dict(row)
    result["audio_filename"] = await _sync_audio(word_id, result["word"], result["audio_filename"])
    return result


@router.put("/{word_id}", response_model=WordOut)
async def update_word(word_id: int, payload: WordIn):
    word, translation, example = _clean_payload(payload)

    conn = get_connection()
    existing = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Palavra não encontrada")

    duplicate = conn.execute(
        "SELECT id FROM words WHERE word = ? COLLATE NOCASE AND id != ?", (word, word_id)
    ).fetchone()
    if duplicate:
        conn.close()
        raise HTTPException(400, "Já existe outra palavra cadastrada com esse texto")

    audio_filename = existing["audio_filename"]
    word_changed = word.lower() != existing["word"].lower()
    if word_changed and audio_filename:
        old_path = AUDIO_DIR / audio_filename
        if old_path.exists():
            old_path.unlink()
        audio_filename = None

    # A frase mudou: o áudio humanizado antigo não corresponde mais ao texto.
    example_audio_filename = existing["example_audio_filename"]
    example_changed = (example or "") != (existing["example_sentence"] or "")
    if example_changed and example_audio_filename:
        old_example_path = AUDIO_DIR / example_audio_filename
        if old_example_path.exists():
            old_example_path.unlink()
        example_audio_filename = None

    conn.execute(
        "UPDATE words SET word = ?, translation = ?, example_sentence = ?, "
        "audio_filename = ?, example_audio_filename = ? WHERE id = ?",
        (word, translation, example, audio_filename, example_audio_filename, word_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    conn.close()

    result = dict(row)
    result["audio_filename"] = await _sync_audio(word_id, result["word"], result["audio_filename"])
    return result


@router.post("/{word_id}/example-audio", response_model=WordOut)
async def generate_example_audio(word_id: int):
    """Gera (ou regenera) o áudio da frase de exemplo.

    Tenta o OmniVoice (voz humanizada) primeiro; se o serviço externo
    falhar por qualquer motivo (fora do ar, cota excedida, etc.), cai para
    o motor padrão (edge-tts) em vez de deixar a frase sem áudio nenhum.
    O botão na interface continua disponível para tentar o OmniVoice de
    novo mais tarde.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Palavra não encontrada")
    if not row["example_sentence"]:
        raise HTTPException(400, "Essa palavra não tem frase de exemplo cadastrada")

    old_filename = row["example_audio_filename"]
    try:
        filename = await generate_phrase_audio(word_id, row["example_sentence"])
        source = "omnivoice"
    except Exception as exc:
        print(f"[omnivoice] falhou para a palavra {word_id}, usando fallback edge-tts: {exc}")
        filename = await generate_phrase_fallback_audio(word_id, row["example_sentence"])
        source = "edge-tts"

    if old_filename and old_filename != filename:
        old_path = AUDIO_DIR / old_filename
        if old_path.exists():
            old_path.unlink()

    conn = get_connection()
    conn.execute(
        "UPDATE words SET example_audio_filename = ?, example_audio_source = ? WHERE id = ?",
        (filename, source, word_id),
    )
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

    if row["example_audio_filename"]:
        example_audio_path = AUDIO_DIR / row["example_audio_filename"]
        if example_audio_path.exists():
            example_audio_path.unlink()

    return {"ok": True}
