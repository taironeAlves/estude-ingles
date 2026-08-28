from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "dictionary.db"
STATIC_DIR = BASE_DIR / "static"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
