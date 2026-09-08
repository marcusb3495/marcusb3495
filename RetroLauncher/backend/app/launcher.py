import datetime
import shlex
import subprocess

from sqlalchemy.orm import Session

from . import models


class LaunchError(Exception):
    pass


def launch_game(db: Session, game: models.Game, emulator: models.Emulator) -> int:
    if not emulator.executable_path:
        raise LaunchError("Emulator has no executable configured")

    try:
        args = emulator.args_template.format(rom=game.rom_path)
    except (KeyError, IndexError) as exc:
        raise LaunchError(f"Invalid args template: {exc}") from exc

    cmd = [emulator.executable_path, *shlex.split(args, posix=True)]

    try:
        process = subprocess.Popen(cmd)
    except OSError as exc:
        raise LaunchError(f"Failed to launch emulator: {exc}") from exc

    game.play_count = (game.play_count or 0) + 1
    game.last_played = datetime.datetime.utcnow()
    db.commit()

    return process.pid
