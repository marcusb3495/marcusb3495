import os

import requests
from sqlalchemy.orm import Session

from .. import models
from ..database import COVERS_DIR
from .base import MetadataProvider, ScrapeCandidate
from .igdb import IGDBProvider

__all__ = ["MetadataProvider", "ScrapeCandidate", "get_provider", "download_cover"]


def _get_setting(db: Session, key: str) -> str | None:
    row = db.query(models.Setting).filter(models.Setting.key == key).first()
    return row.value if row else None


def get_provider(db: Session) -> MetadataProvider:
    client_id = _get_setting(db, "igdb_client_id")
    client_secret = _get_setting(db, "igdb_client_secret")
    return IGDBProvider(client_id, client_secret)


def download_cover(url: str, game_id: int) -> str:
    """Downloads a cover image and returns its path relative to COVERS_DIR."""
    ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
    if len(ext) > 5:
        ext = ".jpg"
    filename = f"{game_id}{ext}"
    dest = os.path.join(COVERS_DIR, filename)

    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        f.write(resp.content)

    return filename
