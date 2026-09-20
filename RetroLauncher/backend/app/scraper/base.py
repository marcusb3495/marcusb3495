from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class ScrapeCandidate(TypedDict):
    provider_id: str
    title: str
    release_date: Optional[str]
    platform_name: Optional[str]
    cover_url: Optional[str]
    description: Optional[str]
    genre: Optional[str]
    developer: Optional[str]
    publisher: Optional[str]
    rating: Optional[float]


class MetadataProvider(ABC):
    """A source of game metadata + box art (e.g. IGDB, ScreenScraper, TheGamesDB).

    Implementations are configured from key/value pairs in the `settings` table
    (API keys, etc) so users can plug in whichever provider they have an account
    with, without changing any other code.
    """

    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the required credentials are present."""

    @abstractmethod
    def search(
        self,
        title: str,
        platform_name: Optional[str] = None,
        system_id: Optional[str] = None,
    ) -> list[ScrapeCandidate]:
        """Return candidate matches for a game title, best match first.

        `system_id` is a provider-specific platform identifier (e.g. a
        ScreenScraper "systemeid") used to narrow results when the caller has
        one on hand; providers that don't use one should just ignore it.
        """

    @abstractmethod
    def get_details(self, provider_id: str) -> ScrapeCandidate:
        """Fetch full details (including cover_url) for a specific candidate."""
