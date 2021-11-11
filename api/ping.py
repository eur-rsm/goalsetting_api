import os
import time
from pathlib import Path

from core import settings


def _get_dir() -> Path:
    base_dir = Path(os.path.dirname(__file__)).parents[0]
    return base_dir / '_data' / 'long'


def setup():
    os.makedirs(str(_get_dir()), exist_ok=True)


def add_web_ping(username: str):
    long_file = _get_dir() / username
    long_file.touch(exist_ok=True)


def has_web_ping(username: str) -> bool:
    long_file = _get_dir() / username
    wait = 0.1
    count = (5 if settings.DEBUG else 120) / wait
    while count > 0:
        try:
            long_file.unlink()
            return True
        except FileNotFoundError as _:
            pass
        count -= 1
        time.sleep(wait)
    return False
