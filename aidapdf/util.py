import random
import subprocess
import platform
import os


def repr_password() -> str:
    return repr('*' * random.randint(4, 10))


def open_file(filepath: str | os.PathLike):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':  # Windows
        os.startfile(filepath)
    else:  # linux variants
        subprocess.call(('xdg-open', filepath))
