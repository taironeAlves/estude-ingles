import re
from typing import Optional

import edge_tts

from .config import AUDIO_DIR

VOICE = "en-US-JennyNeural"


def slugify(word: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", word.lower()).strip("_")
    return slug or "word"


async def ensure_audio(word_id: int, word: str, existing_filename: Optional[str]) -> str:
    """Returns the audio filename for a word, generating it if missing."""
    if existing_filename:
        path = AUDIO_DIR / existing_filename
        if path.exists():
            return existing_filename

    filename = f"{word_id}_{slugify(word)}.mp3"
    path = AUDIO_DIR / filename
    communicate = edge_tts.Communicate(word, VOICE)
    await communicate.save(str(path))
    return filename
