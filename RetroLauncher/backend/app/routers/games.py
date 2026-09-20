import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=list[schemas.GameOut])
def list_games(
    platform_id: int | None = None,
    search: str | None = None,
    favorite: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Game)
    if platform_id is not None:
        query = query.filter(models.Game.platform_id == platform_id)
    if favorite is not None:
        query = query.filter(models.Game.favorite == favorite)
    if search:
        query = query.filter(models.Game.title.ilike(f"%{search}%"))
    return query.order_by(models.Game.sort_title).all()


@router.get("/{game_id}", response_model=schemas.GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.put("/{game_id}", response_model=schemas.GameOut)
def update_game(game_id: int, payload: schemas.GameUpdate, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(game, key, value)
    db.commit()
    db.refresh(game)
    return game


@router.delete("/{game_id}", status_code=204)
def delete_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    db.delete(game)
    db.commit()


@router.api_route("/{game_id}/rom/{filename}", methods=["GET", "HEAD"])
def get_game_rom(game_id: int, filename: str, db: Session = Depends(get_db)):
    # EmulatorJS sends a HEAD request first to read Content-Length for its
    # download progress bar, then a GET (often ranged) for the actual
    # bytes - a GET-only route 405s on that HEAD and the whole thing fails.
    # `filename` is not used to locate the file (game.rom_path already is
    # the full path) - it exists so the URL itself carries the real file
    # extension. EmulatorJS's loader inspects the extension in EJS_gameUrl
    # to decide how to handle the ROM (e.g. zip extraction); a URL with no
    # extension at all makes it fail to start.
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not os.path.isfile(game.rom_path):
        raise HTTPException(
            status_code=404, detail=f"ROM file not found on disk at {game.rom_path!r}"
        )
    return FileResponse(game.rom_path, filename=os.path.basename(game.rom_path))
