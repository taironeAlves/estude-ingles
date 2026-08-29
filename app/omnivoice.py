import asyncio
import os
import shutil
from pathlib import Path

from gradio_client import Client

from .config import AUDIO_DIR

# Space público (comunidade k2-fsa) rodando o modelo OmniVoice em GPU
# compartilhada (Hugging Face ZeroGPU). Não é uma API oficial/estável: pode
# ficar lento, enfileirado ou fora do ar sem aviso. Usado só como fonte
# opcional de áudio mais "humanizado" para a frase de exemplo — a pronúncia
# da palavra em si continua vindo do edge-tts (rápido e confiável).
SPACE_ID = "k2-fsa/OmniVoice"

# A cota anônima do ZeroGPU se esgota rápido (poucas chamadas). Definir
# HF_TOKEN (gratuito, https://huggingface.co/settings/tokens) aumenta a cota.
HF_TOKEN = os.environ.get("HF_TOKEN")

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(SPACE_ID, hf_token=HF_TOKEN)
    return _client


def _generate_sync(text: str, dest_path: Path) -> None:
    client = _get_client()
    audio_path, _status = client.predict(
        text=text,
        lang="English",
        ns=24,
        gs=2.0,
        dn=True,
        sp=1.0,
        du=None,
        pp=True,
        po=True,
        param_9="Auto",
        param_10="Auto",
        param_11="Auto",
        param_12="Auto",
        param_13="American Accent / 美式口音",
        param_14="Auto",
        api_name="/_design_fn",
    )
    shutil.copy(audio_path, dest_path)


async def generate_phrase_audio(word_id: int, text: str) -> str:
    """Gera (via OmniVoice) o áudio humanizado de uma frase e retorna o filename salvo."""
    filename = f"{word_id}_example.wav"
    dest_path = AUDIO_DIR / filename
    await asyncio.to_thread(_generate_sync, text, dest_path)
    return filename
