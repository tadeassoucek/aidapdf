import os
import platform
import subprocess
from pathlib import Path


def format_path(fmt: str, input_path: str) -> str:
    path = Path(input_path)
    return fmt.format(
        dir=path.parent,
        name=path.stem,
        n=2
    )


def open_using_default_app(filepath: str):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':  # Windows
        os.startfile(filepath)
    else:  # linux variants
        subprocess.call(('xdg-open', filepath))
