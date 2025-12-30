import pprint
import sys
from typing import Optional

import colors

from aidapdf.config import Config


class Logger:
    name: str

    LEVELS = {
        0: "ERR!",
        1: "WARN",
        2: "INFO",
        3: "DBUG",
    }

    LEVEL_COLORS = {
        0: "red",
        1: "yellow",
        2: "white",
        3: "gray",
    }

    @staticmethod
    def _color(text: str, *args, **kwargs) -> str:
        if Config.COLOR and sys.stderr.isatty():
            return colors.color(text, *args, **kwargs)
        else:
            return text

    def __init__(self, name: str, parent: Optional['Logger'] = None):
        self.name = name.replace('aidapdf.', '')
        self.parent = parent
        self._name = (self.parent.name + ':' if self.parent else "") + self.name

    def _log(self, message: str, level: int) -> None:
        if level <= Config.VERBOSITY_LEVEL:
            prefix = f"{Logger.LEVELS[level]}:{self._name}"
            print(Logger._color(prefix, fg=Logger.LEVEL_COLORS[level], style='bold') + '  ' +
                  Logger._color(message, fg='white'), file=sys.stderr)

    def debug(self, message: str) -> None:
        self._log(message, 3)

    def info(self, message: str) -> None:
        self._log(message, 2)

    def warn(self, message: str) -> None:
        self._log(message, 1)

    def err(self, message: str) -> None:
        self._log(message, 0)
