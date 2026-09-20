from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Keys that hold secrets and should be masked when read back to the UI.
_SECRET_KEYS = {"igdb_client_secret", "screenscraper_devpassword", "screenscraper_sspassword"}


@router.get("", response_model=list[schemas.SettingOut])
def list_settings(db: Session = Depends(get_db)):
    rows = db.query(models.Setting).all()
    out = []
    for row in rows:
        value = "••••••••" if row.key in _SECRET_KEYS and row.value else row.value
        out.append(schemas.SettingOut(key=row.key, value=value))
    return out


@router.put("", response_model=schemas.SettingOut)
def set_setting(payload: schemas.SettingIn, db: Session = Depends(get_db)):
    row = db.get(models.Setting, payload.key)
    if row:
        row.value = payload.value
    else:
        row = models.Setting(key=payload.key, value=payload.value)
        db.add(row)
    db.commit()
    return schemas.SettingOut(key=row.key, value=row.value)
