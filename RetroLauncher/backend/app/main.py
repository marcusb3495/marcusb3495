import os
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from . import models
from .database import COVERS_DIR, PLATFORM_ICONS_DIR, engine
from .routers import emulators, games, gamelist_import, launch, platforms, scan, scrape, settings

models.Base.metadata.create_all(bind=engine)

# create_all() only creates missing tables, not columns added to a model
# after a database already exists - patch those in for existing installs.
with engine.begin() as conn:
    for ddl in (
        "ALTER TABLE platforms ADD COLUMN icon_path VARCHAR",
        "ALTER TABLE platforms ADD COLUMN browser_core VARCHAR",
        "ALTER TABLE platforms ADD COLUMN screenscraper_system_id VARCHAR",
    ):
        try:
            conn.execute(text(ddl))
        except OperationalError:
            pass  # column already exists

app = FastAPI(title="RetroLauncher")

app.include_router(platforms.router)
app.include_router(emulators.router)
app.include_router(games.router)
app.include_router(scan.router)
app.include_router(gamelist_import.router)
app.include_router(launch.router)
app.include_router(scrape.router)
app.include_router(settings.router)

app.mount("/media/covers", StaticFiles(directory=COVERS_DIR), name="covers")
app.mount("/media/platform_icons", StaticFiles(directory=PLATFORM_ICONS_DIR), name="platform_icons")

_FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
)
app.mount("/static", StaticFiles(directory=os.path.join(_FRONTEND_DIR, "static")), name="static")

# Each static file's own last-modified time is used as its cache-busting
# version, computed fresh on every page request - so `git pull` alone
# invalidates a browser's cache for exactly the files that changed, even
# if the server process itself isn't restarted (unlike a single version
# fixed at server start, which only busts the cache on restart).
def _versioned_url(match) -> str:
    attr, path = match.group(1), match.group(2)
    full = os.path.join(_FRONTEND_DIR, path.lstrip("/"))
    try:
        version = int(os.path.getmtime(full))
    except OSError:
        version = 0
    return f'{attr}="{path}?v={version}"'


def _serve_page(filename: str) -> HTMLResponse:
    with open(os.path.join(_FRONTEND_DIR, filename), encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r'(src|href)="(/static/[^"]+)"', _versioned_url, html)
    return HTMLResponse(html)


@app.get("/")
def index():
    return _serve_page("index.html")


@app.get("/settings.html")
def settings_page():
    return _serve_page("settings.html")


@app.get("/play.html")
def play_page():
    return _serve_page("play.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}
