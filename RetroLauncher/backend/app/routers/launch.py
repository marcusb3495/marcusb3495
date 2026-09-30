from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import launcher, models
from ..database import get_db

router = APIRouter(prefix="/api/games", tags=["launch"])


class LaunchRequest(BaseModel):
    emulator_id: int | None = None


class LaunchResponse(BaseModel):
    pid: int


@router.post("/{game_id}/launch", response_model=LaunchResponse)
def launch_game(game_id: int, payload: LaunchRequest = LaunchRequest(), db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if payload.emulator_id is not None:
        emulator = db.get(models.Emulator, payload.emulator_id)
    else:
        emulator = (
            db.query(models.Emulator)
            .filter(models.Emulator.platform_id == game.platform_id)
            .order_by(models.Emulator.is_default.desc())
            .first()
        )

    if not emulator:
        raise HTTPException(
            status_code=400, detail="No emulator configured for this game's platform"
        )

    try:
        pid = launcher.launch_game(db, game, emulator)
    except launcher.LaunchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return LaunchResponse(pid=pid)
