from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/emulators", tags=["emulators"])


@router.get("", response_model=list[schemas.EmulatorOut])
def list_emulators(platform_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Emulator)
    if platform_id is not None:
        query = query.filter(models.Emulator.platform_id == platform_id)
    return query.order_by(models.Emulator.name).all()


@router.post("", response_model=schemas.EmulatorOut, status_code=201)
def create_emulator(payload: schemas.EmulatorCreate, db: Session = Depends(get_db)):
    if not db.get(models.Platform, payload.platform_id):
        raise HTTPException(status_code=404, detail="Platform not found")
    emulator = models.Emulator(**payload.model_dump())
    db.add(emulator)
    db.commit()
    db.refresh(emulator)
    return emulator


@router.put("/{emulator_id}", response_model=schemas.EmulatorOut)
def update_emulator(
    emulator_id: int, payload: schemas.EmulatorUpdate, db: Session = Depends(get_db)
):
    emulator = db.get(models.Emulator, emulator_id)
    if not emulator:
        raise HTTPException(status_code=404, detail="Emulator not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(emulator, key, value)
    db.commit()
    db.refresh(emulator)
    return emulator


@router.delete("/{emulator_id}", status_code=204)
def delete_emulator(emulator_id: int, db: Session = Depends(get_db)):
    emulator = db.get(models.Emulator, emulator_id)
    if not emulator:
        raise HTTPException(status_code=404, detail="Emulator not found")
    db.delete(emulator)
    db.commit()
