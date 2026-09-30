import os

import requests
from sqlalchemy.orm import Session

from .. import models
from ..database import COVERS_DIR
from .base import MetadataProvider, ScrapeCandidate
from .igdb import IGDBProvider
from .screenscraper import ScreenScraperProvider

__all__ = ["MetadataProvider", "ScrapeCandidate", "get_provider", "download_cover"]


def _get_setting(db: Session, key: str) -> str | None:
    row = db.query(models.Setting).filter(models.Setting.key == key).first()
    return row.value if row else None


def _build_igdb(db: Session) -> IGDBProvider:
    return IGDBProvider(
        _get_setting(db, "igdb_client_id"),
        _get_setting(db, "igdb_client_secret"),
    )


def _build_screenscraper(db: Session) -> ScreenScraperProvider:
    return ScreenScraperProvider(
        _get_setting(db, "screenscraper_devid"),
        _get_setting(db, "screenscraper_devpassword"),
        _get_setting(db, "screenscraper_softname"),
        _get_setting(db, "screenscraper_ssid"),
        _get_setting(db, "screenscraper_sspassword"),
    )


_PROVIDER_BUILDERS = {
    "screenscraper": _build_screenscraper,
    "igdb": _build_igdb,
}


def get_provider(db: Session) -> MetadataProvider:
    """Returns the configured metadata provider, honoring the `metadata_provider`
    setting ("screenscraper" or "igdb"). Falls back to whichever provider is
    actually configured if the preferred one has no credentials, so switching
    the setting isn't required just because only one provider is set up.
    """
    preferred = _get_setting(db, "metadata_provider") or "screenscraper"
    builder = _PROVIDER_BUILDERS.get(preferred, _build_screenscraper)
    provider = builder(db)
    if provider.is_configured():
        return provider

    for key, other_builder in _PROVIDER_BUILDERS.items():
        if key == preferred:
            continue
        fallback = other_builder(db)
        if fallback.is_configured():
            return fallback

    return provider


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
