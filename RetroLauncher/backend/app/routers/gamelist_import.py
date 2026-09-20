from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import gamelist_import, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/platforms", tags=["gamelist-import"])


@router.post("/{platform_id}/import-gamelist", response_model=schemas.GamelistImportResult)
def import_gamelist(
    platform_id: int, payload: schemas.GamelistImportRequest, db: Session = Depends(get_db)
):
    platform = db.get(models.Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    try:
        return gamelist_import.import_gamelist(db, platform, payload.gamelist_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
