from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de um .env local (gitignored) antes de qualquer módulo
# ler os.environ — usado, por exemplo, para HF_TOKEN (ver app/omnivoice.py).
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "dictionary.db"
STATIC_DIR = BASE_DIR / "static"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
