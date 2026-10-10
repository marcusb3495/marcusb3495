import datetime
import os
import shutil
import xml.etree.ElementTree as ET
from typing import Optional

from sqlalchemy.orm import Session

from . import models
from .database import COVERS_DIR


def _resolve_relative(base_dir: str, raw_path: str) -> str:
    # gamelist.xml always writes forward slashes (e.g. "./Game.zip") even
    # when generated on Windows - normalize before joining with the OS path.
    normalized = raw_path.replace("\\", "/")
    return os.path.normpath(os.path.join(base_dir, normalized))


def _match_key(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _parse_release_date(raw: Optional[str]) -> Optional[str]:
    # EmulationStation stores dates as "YYYYMMDDTHHMMSS".
    if not raw or len(raw) < 8:
        return None
    try:
        parsed = datetime.datetime.strptime(raw[:8], "%Y%m%d")
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%d")


def _parse_rating(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    # EmulationStation stores ratings as a 0.0-1.0 fraction; normalize to 0-100
    # to match this app's other providers.
    return round(value * 100, 1)


def import_gamelist(db: Session, platform: models.Platform, gamelist_path: str) -> dict:
    """Imports metadata + box art from a RetroBat/Batocera/EmulationStation-style
    gamelist.xml, matching each <game> entry to an already-scanned Game row by
    resolving its <path> relative to the gamelist.xml's own directory. Run
    Scan on the platform first so there's something to match against.
    """
    if not os.path.isfile(gamelist_path):
        raise FileNotFoundError(f"gamelist.xml not found at {gamelist_path}")

    base_dir = os.path.dirname(os.path.abspath(gamelist_path))

    try:
        root = ET.parse(gamelist_path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Failed to parse gamelist.xml: {exc}") from exc

    games_by_path = {
        _match_key(g.rom_path): g
        for g in db.query(models.Game).filter(models.Game.platform_id == platform.id).all()
    }

    total_entries = 0
    matched = 0
    covers_imported = 0
    not_found = 0

    for entry in root.findall("game"):
        total_entries += 1
        path_el = entry.find("path")
        if path_el is None or not path_el.text:
            not_found += 1
            continue

        resolved = _resolve_relative(base_dir, path_el.text)
        game = games_by_path.get(_match_key(resolved))
        if not game:
            not_found += 1
            continue

        matched += 1

        def text(tag: str) -> Optional[str]:
            el = entry.find(tag)
            return el.text.strip() if el is not None and el.text else None

        name = text("name")
        if name:
            game.title = name
        game.description = text("desc")
        game.genre = text("genre")
        game.developer = text("developer")
        game.publisher = text("publisher")
        game.release_date = _parse_release_date(text("releasedate"))
        game.rating = _parse_rating(text("rating"))

        image_rel = text("image")
        if image_rel:
            image_path = _resolve_relative(base_dir, image_rel)
            if os.path.isfile(image_path):
                ext = os.path.splitext(image_path)[1] or ".jpg"
                filename = f"{game.id}{ext}"
                shutil.copyfile(image_path, os.path.join(COVERS_DIR, filename))
                game.cover_path = filename
                covers_imported += 1

    db.commit()

    return {
        "platform_id": platform.id,
        "total_entries": total_entries,
        "matched": matched,
        "covers_imported": covers_imported,
        "not_found": not_found,
    }
