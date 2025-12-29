import random
import subprocess
import platform
import os
from typing import Optional


def repr_password(passwd: Optional[str]) -> str:
    return repr('*' * 8) if passwd else 'None'


def open_file(filepath: str | os.PathLike):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':  # Windows
        os.startfile(filepath)
    else:  # linux variants
        subprocess.call(('xdg-open', filepath))
