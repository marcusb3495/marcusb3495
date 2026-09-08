from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/platforms", tags=["platforms"])


@router.get("", response_model=list[schemas.PlatformOut])
def list_platforms(db: Session = Depends(get_db)):
    counts = dict(
        db.query(models.Game.platform_id, func.count(models.Game.id))
        .group_by(models.Game.platform_id)
        .all()
    )
    platforms = db.query(models.Platform).order_by(models.Platform.name).all()
    out = []
    for p in platforms:
        item = schemas.PlatformOut.model_validate(p)
        item.game_count = counts.get(p.id, 0)
        out.append(item)
    return out


@router.post("", response_model=schemas.PlatformOut, status_code=201)
def create_platform(payload: schemas.PlatformCreate, db: Session = Depends(get_db)):
    if db.query(models.Platform).filter(models.Platform.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Platform name already exists")
    platform = models.Platform(**payload.model_dump())
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return schemas.PlatformOut.model_validate(platform)


@router.get("/{platform_id}", response_model=schemas.PlatformOut)
def get_platform(platform_id: int, db: Session = Depends(get_db)):
    platform = db.get(models.Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    return schemas.PlatformOut.model_validate(platform)


@router.put("/{platform_id}", response_model=schemas.PlatformOut)
def update_platform(
    platform_id: int, payload: schemas.PlatformUpdate, db: Session = Depends(get_db)
):
    platform = db.get(models.Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(platform, key, value)
    db.commit()
    db.refresh(platform)
    return schemas.PlatformOut.model_validate(platform)


@router.delete("/{platform_id}", status_code=204)
def delete_platform(platform_id: int, db: Session = Depends(get_db)):
    platform = db.get(models.Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    db.delete(platform)
    db.commit()
