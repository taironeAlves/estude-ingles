from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import AUDIO_DIR, STATIC_DIR
from .database import init_db
from .routers import training, words

app = FastAPI(title="Estude Inglês")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(words.router)
app.include_router(training.router)

app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
