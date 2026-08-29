import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import edge_tts

from .audio_utils import build_repeated_audio
from .config import AUDIO_DIR

VOICE = "en-US-JennyNeural"


def slugify(word: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", word.lower()).strip("_")
    return slug or "word"


async def _synthesize_once(word: str, path: Path) -> None:
    communicate = edge_tts.Communicate(word, VOICE)
    await communicate.save(str(path))


async def ensure_audio(word_id: int, word: str, existing_filename: Optional[str]) -> str:
    """Returns the audio filename for a word, generating it (21 repetições) if missing."""
    if existing_filename:
        path = AUDIO_DIR / existing_filename
        if path.exists():
            return existing_filename

    filename = f"{word_id}_{slugify(word)}.mp3"
    final_path = AUDIO_DIR / filename

    fd, raw_path_str = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    raw_path = Path(raw_path_str)
    try:
        await _synthesize_once(word, raw_path)
        # codec="mp3" faz o pydub pular a checagem via ffprobe (não temos
        # esse binário disponível, só o ffmpeg embutido pelo imageio-ffmpeg)
        # já que sabemos de antemão que o arquivo de origem é mp3.
        build_repeated_audio(raw_path, final_path, format="mp3", codec="mp3")
    finally:
        # No Windows o ffmpeg pode manter o arquivo temporário brevemente
        # travado logo após o uso; ignorar falha de limpeza é seguro aqui.
        try:
            raw_path.unlink(missing_ok=True)
        except OSError:
            pass

    return filename
