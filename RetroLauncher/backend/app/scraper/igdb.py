import time
from typing import Optional

import requests

from .base import MetadataProvider, ScrapeCandidate

_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_API_URL = "https://api.igdb.com/v4/games"
_COVER_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"

_SEARCH_FIELDS = (
    "name,first_release_date,summary,genres.name,"
    "involved_companies.company.name,involved_companies.developer,"
    "involved_companies.publisher,cover.image_id,rating,platforms.name"
)


class IGDBProvider(MetadataProvider):
    """Metadata + box art via IGDB (https://api-docs.igdb.com/).

    Requires a free Twitch developer application: create one at
    https://dev.twitch.tv/console/apps to obtain a client id + secret,
    then save them in Settings as `igdb_client_id` / `igdb_client_secret`.
    """

    name = "igdb"

    def __init__(self, client_id: Optional[str], client_secret: Optional[str]):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        resp = requests.post(
            _TOKEN_URL,
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        return self._token

    def _headers(self) -> dict:
        return {
            "Client-ID": self.client_id or "",
            "Authorization": f"Bearer {self._get_token()}",
        }

    def _row_to_candidate(self, row: dict) -> ScrapeCandidate:
        release_date = None
        if row.get("first_release_date"):
            release_date = time.strftime("%Y-%m-%d", time.gmtime(row["first_release_date"]))

        cover_url = None
        if row.get("cover", {}).get("image_id"):
            cover_url = _COVER_URL.format(image_id=row["cover"]["image_id"])

        developer = None
        publisher = None
        for company in row.get("involved_companies", []) or []:
            company_name = (company.get("company") or {}).get("name")
            if not company_name:
                continue
            if company.get("developer") and not developer:
                developer = company_name
            if company.get("publisher") and not publisher:
                publisher = company_name

        platform_name = None
        platforms = row.get("platforms") or []
        if platforms:
            platform_name = platforms[0].get("name")

        genre = None
        genres = row.get("genres") or []
        if genres:
            genre = ", ".join(g["name"] for g in genres if g.get("name"))

        return ScrapeCandidate(
            provider_id=str(row["id"]),
            title=row.get("name", ""),
            release_date=release_date,
            platform_name=platform_name,
            cover_url=cover_url,
            description=row.get("summary"),
            genre=genre,
            developer=developer,
            publisher=publisher,
            rating=row.get("rating"),
        )

    def search(
        self,
        title: str,
        platform_name: Optional[str] = None,
        system_id: Optional[str] = None,
    ) -> list[ScrapeCandidate]:
        safe_title = title.replace('"', '\\"')
        query = f'search "{safe_title}"; fields {_SEARCH_FIELDS}; limit 15;'
        resp = requests.post(_API_URL, headers=self._headers(), data=query, timeout=15)
        resp.raise_for_status()
        return [self._row_to_candidate(row) for row in resp.json()]

    def get_details(self, provider_id: str) -> ScrapeCandidate:
        query = f"fields {_SEARCH_FIELDS}; where id = {int(provider_id)};"
        resp = requests.post(_API_URL, headers=self._headers(), data=query, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            raise ValueError(f"No IGDB game found for id {provider_id}")
        return self._row_to_candidate(rows[0])
