import datetime
import os
import shlex
import subprocess

from sqlalchemy.orm import Session

from . import models

_ROM_PLACEHOLDER = "{rom}"


class LaunchError(Exception):
    pass


def _build_args(args_template: str, rom_path: str) -> list[str]:
    # Split the template's static flags first, then substitute the ROM path
    # into the resulting tokens - never split the already-substituted string.
    # Splitting after substitution (the old approach) breaks ROM paths that
    # contain spaces, and on Windows also mangles backslashes, since
    # shlex's posix mode treats backslash as an escape character.
    if _ROM_PLACEHOLDER not in args_template:
        raise LaunchError(f"Launch arguments must include {_ROM_PLACEHOLDER}")

    try:
        parts = shlex.split(args_template, posix=os.name != "nt")
    except ValueError as exc:
        raise LaunchError(f"Invalid args template: {exc}") from exc

    return [part.replace(_ROM_PLACEHOLDER, rom_path) for part in parts]


def launch_game(db: Session, game: models.Game, emulator: models.Emulator) -> int:
    if not emulator.executable_path:
        raise LaunchError("Emulator has no executable configured")

    cmd = [emulator.executable_path, *_build_args(emulator.args_template, game.rom_path)]

    try:
        process = subprocess.Popen(cmd)
    except OSError as exc:
        raise LaunchError(f"Failed to launch emulator: {exc}") from exc

    game.play_count = (game.play_count or 0) + 1
    game.last_played = datetime.datetime.utcnow()
    db.commit()

    return process.pid
