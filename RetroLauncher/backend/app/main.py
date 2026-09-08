import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models
from .database import COVERS_DIR, engine
from .routers import emulators, games, launch, platforms, scan, scrape, settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RetroLauncher")

app.include_router(platforms.router)
app.include_router(emulators.router)
app.include_router(games.router)
app.include_router(scan.router)
app.include_router(launch.router)
app.include_router(scrape.router)
app.include_router(settings.router)

app.mount("/media/covers", StaticFiles(directory=COVERS_DIR), name="covers")

_FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
)
app.mount("/static", StaticFiles(directory=os.path.join(_FRONTEND_DIR, "static")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))


@app.get("/settings.html")
def settings_page():
    return FileResponse(os.path.join(_FRONTEND_DIR, "settings.html"))


@app.get("/api/health")
def health():
    return {"status": "ok"}
