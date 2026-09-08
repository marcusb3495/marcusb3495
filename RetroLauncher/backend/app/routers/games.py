from fastapi import APIRouter, Depends, HTTPException
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
