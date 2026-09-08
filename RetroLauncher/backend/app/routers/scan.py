from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, scanner, schemas
from ..database import get_db

router = APIRouter(prefix="/api/platforms", tags=["scan"])


@router.post("/{platform_id}/scan", response_model=schemas.ScanResult)
def scan_platform(platform_id: int, db: Session = Depends(get_db)):
    platform = db.get(models.Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    try:
        result = scanner.scan_platform(db, platform)
    except FileNotFoundError:
        raise HTTPException(
            status_code=400, detail=f"ROM folder not found: {platform.folder_path}"
        )
    return result
