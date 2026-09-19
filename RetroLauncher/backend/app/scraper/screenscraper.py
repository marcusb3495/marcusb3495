from typing import Any, Optional

import requests

from .base import MetadataProvider, ScrapeCandidate

_API_BASE = "https://www.screenscraper.fr/api2"
_SEARCH_URL = f"{_API_BASE}/jeuRecherche.php"
_INFO_URL = f"{_API_BASE}/jeuInfos.php"

# Preference order when a field is offered in multiple regions/languages.
_PREFERRED_REGIONS = ("wor", "us", "eu", "jp", "ss", "fr")
_PREFERRED_LANGS = ("en", "us")
_BOX_ART_TYPES = ("box-2D", "box-2d", "box2D", "box-2D-back")


def _text_field(value: Any) -> Optional[str]:
    """ScreenScraper sometimes nests a scalar as {"text": "..."} - unwrap either shape."""
    if isinstance(value, dict):
        return value.get("text")
    return value


def _pick_localized(items: Any, key: str, preferred: tuple[str, ...]) -> Optional[dict]:
    if not isinstance(items, list) or not items:
        return None
    by_key = {item.get(key): item for item in items if isinstance(item, dict)}
    for candidate in preferred:
        if candidate in by_key:
            return by_key[candidate]
    return items[0] if isinstance(items[0], dict) else None


class ScreenScraperProvider(MetadataProvider):
    """Metadata + box art via ScreenScraper.fr (https://www.screenscraper.fr/api2/).

    Requires a developer account - request one from the ScreenScraper team via
    their Discord/forum (this isn't an instant self-serve signup like IGDB's
    Twitch app) to get a devid/devpassword, plus a `softname` identifying this
    app. A personal ScreenScraper account (ssid/sspassword) is optional but
    strongly recommended: without one, anonymous API calls are throttled very
    aggressively.
    """

    name = "screenscraper"

    def __init__(
        self,
        devid: Optional[str],
        devpassword: Optional[str],
        softname: Optional[str],
        ssid: Optional[str] = None,
        sspassword: Optional[str] = None,
    ):
        self.devid = devid
        self.devpassword = devpassword
        self.softname = softname or "RetroLauncher"
        self.ssid = ssid
        self.sspassword = sspassword

    def is_configured(self) -> bool:
        return bool(self.devid and self.devpassword)

    def _auth_params(self) -> dict:
        params = {
            "devid": self.devid,
            "devpassword": self.devpassword,
            "softname": self.softname,
            "output": "json",
        }
        if self.ssid:
            params["ssid"] = self.ssid
        if self.sspassword:
            params["sspassword"] = self.sspassword
        return params

    def _row_to_candidate(self, row: dict) -> ScrapeCandidate:
        name_entry = _pick_localized(row.get("noms"), "region", _PREFERRED_REGIONS)
        title = (name_entry.get("text") if name_entry else None) or row.get("nom") or ""

        synopsis_entry = _pick_localized(row.get("synopsis"), "langue", _PREFERRED_LANGS)
        description = synopsis_entry.get("text") if synopsis_entry else None

        date_entry = _pick_localized(row.get("dates"), "region", _PREFERRED_REGIONS)
        release_date = date_entry.get("text") if date_entry else None

        genre_names = []
        for g in row.get("genres") or []:
            if not isinstance(g, dict):
                continue
            entry = _pick_localized(g.get("noms"), "langue", _PREFERRED_LANGS)
            if entry and entry.get("text"):
                genre_names.append(entry["text"])
        genre = ", ".join(genre_names) if genre_names else None

        developer = _text_field(row.get("developpeur"))
        publisher = _text_field(row.get("editeur"))

        note_raw = _text_field(row.get("note"))
        rating = None
        if note_raw not in (None, ""):
            try:
                # ScreenScraper rates out of 20; normalize to a 0-100 scale
                # to match this app's other providers.
                rating = float(note_raw) * 5
            except (TypeError, ValueError):
                rating = None

        cover_url = None
        media_list = row.get("medias") or []
        box_media = [
            m for m in media_list if isinstance(m, dict) and m.get("type") in _BOX_ART_TYPES
        ]
        chosen_media = _pick_localized(box_media, "region", _PREFERRED_REGIONS) or (
            box_media[0] if box_media else None
        )
        if chosen_media:
            cover_url = chosen_media.get("url")

        return ScrapeCandidate(
            provider_id=str(row.get("id")),
            title=title,
            release_date=release_date,
            platform_name=None,
            cover_url=cover_url,
            description=description,
            genre=genre,
            developer=developer,
            publisher=publisher,
            rating=rating,
        )

    def search(
        self,
        title: str,
        platform_name: Optional[str] = None,
        system_id: Optional[str] = None,
    ) -> list[ScrapeCandidate]:
        params = {**self._auth_params(), "recherche": title}
        if system_id:
            params["systemeid"] = system_id

        resp = requests.get(_SEARCH_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        jeux = ((data.get("response") or {}).get("jeux")) or []
        return [self._row_to_candidate(row) for row in jeux]

    def get_details(self, provider_id: str) -> ScrapeCandidate:
        params = {**self._auth_params(), "gameid": provider_id}
        resp = requests.get(_INFO_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        jeu = (data.get("response") or {}).get("jeu")
        if not jeu:
            raise ValueError(f"No ScreenScraper game found for id {provider_id}")
        return self._row_to_candidate(jeu)
