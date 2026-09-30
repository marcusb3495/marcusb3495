from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..scraper import download_cover, get_provider

router = APIRouter(prefix="/api/games", tags=["scrape"])


@router.get("/{game_id}/scrape/search", response_model=list[schemas.ScrapeCandidate])
def scrape_search(game_id: int, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    provider = get_provider(db)
    if not provider.is_configured():
        raise HTTPException(
            status_code=400,
            detail=(
                "No metadata provider configured. Add ScreenScraper or IGDB "
                "credentials in Settings (see README for how to get them)."
            ),
        )

    try:
        candidates = provider.search(
            game.title, game.platform.name, game.platform.screenscraper_system_id
        )
    except Exception as exc:  # noqa: BLE001 - surface provider errors to the UI
        raise HTTPException(status_code=502, detail=f"Scrape search failed: {exc}")

    return candidates


@router.post("/{game_id}/scrape/apply", response_model=schemas.GameOut)
def scrape_apply(game_id: int, payload: schemas.ScrapeApply, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    provider = get_provider(db)
    if not provider.is_configured():
        raise HTTPException(
            status_code=400,
            detail="No metadata provider configured. Add ScreenScraper or IGDB credentials in Settings.",
        )

    try:
        details = provider.get_details(payload.provider_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Scrape fetch failed: {exc}")

    game.title = details["title"] or game.title
    game.description = details.get("description")
    game.release_date = details.get("release_date")
    game.genre = details.get("genre")
    game.developer = details.get("developer")
    game.publisher = details.get("publisher")
    game.rating = details.get("rating")

    if details.get("cover_url"):
        try:
            game.cover_path = download_cover(details["cover_url"], game.id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Cover download failed: {exc}")

    db.commit()
    db.refresh(game)
    return game
