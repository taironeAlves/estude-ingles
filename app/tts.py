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


async def _synthesize_once(text: str, path: Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(path))


async def _synthesize_repeated(text: str, final_path: Path) -> None:
    """Sintetiza o texto via edge-tts e salva em final_path já repetido
    21 vezes (regra das 21 vezes), com limpeza do arquivo temporário."""
    fd, raw_path_str = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    raw_path = Path(raw_path_str)
    try:
        await _synthesize_once(text, raw_path)
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


async def ensure_audio(word_id: int, word: str, existing_filename: Optional[str]) -> str:
    """Returns the audio filename for a word, generating it (21 repetições) if missing."""
    if existing_filename:
        path = AUDIO_DIR / existing_filename
        if path.exists():
            return existing_filename

    filename = f"{word_id}_{slugify(word)}.mp3"
    await _synthesize_repeated(word, AUDIO_DIR / filename)
    return filename


async def generate_phrase_fallback_audio(word_id: int, text: str) -> str:
    """Gera o áudio da frase de exemplo com o motor padrão (edge-tts, 21x)
    quando a fonte humanizada (OmniVoice) falha — para nunca deixar a
    frase sem áudio nenhum."""
    filename = f"{word_id}_example.mp3"
    await _synthesize_repeated(text, AUDIO_DIR / filename)
    return filename
