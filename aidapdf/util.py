import subprocess
import os
from typing import Optional

from aidapdf.config import Config


def repr_password(passwd: Optional[str]) -> str:
    return repr('*' * 8) if passwd else 'None'


def open_file_with_default_program(filepath: str | os.PathLike):
    if Config.PLATFORM == 'macOS':
        subprocess.call(('open', filepath))
    elif Config.PLATFORM == 'Windows':
        os.startfile(filepath)
    else:  # Linux
        subprocess.call(('xdg-open', filepath))


def pluralize(n: int, noun: str) -> str:
    return f"{n} {noun}" + ("s" if n > 1 else "")
