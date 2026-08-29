from pathlib import Path
from typing import Optional

import imageio_ffmpeg
from pydub import AudioSegment

# Regra das 21 vezes: o áudio final repete o conteúdo 21 vezes, com 1
# segundo de silêncio entre cada repetição, no mesmo arquivo — usado tanto
# para a pronúncia da palavra (edge-tts, mp3) quanto para o áudio
# humanizado da frase (OmniVoice, wav).
REPEAT_COUNT = 21
GAP_MS = 1000

# Só é usado quando format="mp3" (decodificação/encodificação via ffmpeg).
# Para wav, o pydub lê/escreve nativamente em Python puro, sem precisar
# disso.
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()


def build_repeated_audio(
    source_path: Path, dest_path: Path, *, format: str, codec: Optional[str] = None
) -> None:
    """Lê o áudio de origem e salva em dest_path com o conteúdo repetido
    REPEAT_COUNT vezes, separado por GAP_MS de silêncio."""
    single = AudioSegment.from_file(source_path, format=format, codec=codec)
    silence = AudioSegment.silent(duration=GAP_MS)
    repeated = single
    for _ in range(REPEAT_COUNT - 1):
        repeated += silence + single
    repeated.export(dest_path, format=format)
