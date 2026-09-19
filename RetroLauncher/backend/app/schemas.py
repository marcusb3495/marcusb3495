import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlatformBase(BaseModel):
    name: str
    folder_path: str
    extensions: str = ""
    browser_core: Optional[str] = None
    screenscraper_system_id: Optional[str] = None


class PlatformCreate(PlatformBase):
    pass


class PlatformUpdate(BaseModel):
    name: Optional[str] = None
    folder_path: Optional[str] = None
    extensions: Optional[str] = None
    browser_core: Optional[str] = None
    screenscraper_system_id: Optional[str] = None


class PlatformOut(PlatformBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    game_count: int = 0
    icon_path: Optional[str] = None


class EmulatorBase(BaseModel):
    name: str
    platform_id: int
    executable_path: str
    args_template: str = "{rom}"
    is_default: bool = True


class EmulatorCreate(EmulatorBase):
    pass


class EmulatorUpdate(BaseModel):
    name: Optional[str] = None
    executable_path: Optional[str] = None
    args_template: Optional[str] = None
    is_default: Optional[bool] = None


class EmulatorOut(EmulatorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform_id: int
    title: str
    sort_title: str
    rom_path: str
    description: Optional[str] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None
    rating: Optional[float] = None
    cover_path: Optional[str] = None
    favorite: bool = False
    play_count: int = 0
    last_played: Optional[datetime.datetime] = None


class GameUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None
    rating: Optional[float] = None
    favorite: Optional[bool] = None


class ScanResult(BaseModel):
    platform_id: int
    added: int
    skipped: int
    total_roms_found: int


class ScrapeCandidate(BaseModel):
    provider_id: str
    title: str
    release_date: Optional[str] = None
    platform_name: Optional[str] = None
    cover_url: Optional[str] = None


class ScrapeApply(BaseModel):
    provider_id: str


class SettingIn(BaseModel):
    key: str
    value: str


class SettingOut(BaseModel):
    key: str
    value: str
