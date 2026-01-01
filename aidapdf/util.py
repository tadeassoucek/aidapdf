import subprocess
import os
from datetime import datetime
from typing import Optional, Any

from aidapdf.config import Config


def str_password(passwd: Any) -> Any:
    if type(passwd) is str:
        return '*' * 8 if passwd else None
    return passwd


def repr_password(passwd: Any) -> str:
    return repr(str_password(passwd)) if passwd else 'None'


def open_file_with_default_program(filepath: str | os.PathLike):
    if Config.PLATFORM == 'macOS':
        subprocess.call(('open', filepath))
    elif Config.PLATFORM == 'Windows':
        os.startfile(filepath)
    else:  # Linux
        subprocess.call(('xdg-open', filepath))


def pluralize(n: int, noun: str) -> str:
    return f"{n} {noun}" + ("s" if n > 1 else "")


def format_date(date: datetime) -> str:
    return date.strftime('on %b %d %Y at %I:%M')
