import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    folder_path = Column(String, nullable=False)
    extensions = Column(String, nullable=False, default="")  # comma-separated, e.g. ".nes,.zip"
    icon_path = Column(String)  # filename under data/platform_icons, served at /media/platform_icons/...
    browser_core = Column(String)  # EmulatorJS core id (e.g. "nes", "snes", "gba") for in-browser play
    screenscraper_system_id = Column(String)  # ScreenScraper "systemeid" for this platform, narrows scrape search

    emulators = relationship(
        "Emulator", back_populates="platform", cascade="all, delete-orphan"
    )
    games = relationship("Game", back_populates="platform", cascade="all, delete-orphan")


class Emulator(Base):
    __tablename__ = "emulators"

    id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    name = Column(String, nullable=False)
    executable_path = Column(String, nullable=False)
    # "{rom}" is substituted with the absolute ROM path at launch time.
    args_template = Column(String, nullable=False, default="{rom}")
    is_default = Column(Boolean, default=True)

    platform = relationship("Platform", back_populates="emulators")


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (UniqueConstraint("rom_path", name="uq_game_rom_path"),)

    id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    title = Column(String, nullable=False)
    sort_title = Column(String, nullable=False)
    rom_path = Column(String, nullable=False)

    description = Column(Text)
    release_date = Column(String)
    genre = Column(String)
    developer = Column(String)
    publisher = Column(String)
    rating = Column(Float)
    cover_path = Column(String)  # relative path under data/covers, served at /media/covers/...

    favorite = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    last_played = Column(DateTime)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)

    platform = relationship("Platform", back_populates="games")


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String)
