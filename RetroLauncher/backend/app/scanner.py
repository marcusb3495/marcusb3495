import os
import re

from sqlalchemy.orm import Session

from . import models

# Strips region/dump-quality tags commonly found in No-Intro / TOSEC / GoodTools
# style ROM filenames, e.g. "Super Game (USA) (Rev 1) [!].nes" -> "Super Game".
_BRACKET_TAG_RE = re.compile(r"\[[^\]]*\]")
_PAREN_TAG_RE = re.compile(r"\([^)]*\)")
_WHITESPACE_RE = re.compile(r"\s+")

_LEADING_ARTICLES = ("the ", "a ", "an ")


def clean_title(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = _BRACKET_TAG_RE.sub("", name)
    name = _PAREN_TAG_RE.sub("", name)
    name = name.replace("_", " ")
    name = _WHITESPACE_RE.sub(" ", name).strip(" -")
    return name or os.path.splitext(filename)[0]


def sort_title(title: str) -> str:
    lowered = title.lower()
    for article in _LEADING_ARTICLES:
        if lowered.startswith(article):
            return title[len(article):].strip() + ", " + title[: len(article) - 1]
    return title


def find_rom_files(folder_path: str, extensions: list[str]) -> list[str]:
    if not extensions:
        return []
    lowered_exts = {ext.lower().strip() for ext in extensions if ext.strip()}
    found = []
    for root, _dirs, files in os.walk(folder_path):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in lowered_exts:
                found.append(os.path.join(root, fname))
    return found


def scan_platform(db: Session, platform: models.Platform) -> dict:
    extensions = [e for e in platform.extensions.split(",") if e.strip()]
    rom_paths = find_rom_files(platform.folder_path, extensions)

    existing_paths = {
        g.rom_path
        for g in db.query(models.Game).filter(models.Game.platform_id == platform.id).all()
    }

    added = 0
    for rom_path in rom_paths:
        if rom_path in existing_paths:
            continue
        title = clean_title(os.path.basename(rom_path))
        game = models.Game(
            platform_id=platform.id,
            title=title,
            sort_title=sort_title(title),
            rom_path=rom_path,
        )
        db.add(game)
        added += 1

    db.commit()

    return {
        "platform_id": platform.id,
        "added": added,
        "skipped": len(rom_paths) - added,
        "total_roms_found": len(rom_paths),
    }
