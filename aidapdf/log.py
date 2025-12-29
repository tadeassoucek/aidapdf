import pprint
import sys
from typing import Optional

import colors

from aidapdf.config import Config


class Logger:
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

    def _log(self, message: str, level: int, **kwargs) -> None:
        if level <= Config.VERBOSITY_LEVEL:
            prefix = f"{Logger.LEVELS[level]}:{self._name}"
            suffix = ' ' + pprint.pformat(kwargs) if kwargs else ""
            print(Logger._color(prefix, fg=Logger.LEVEL_COLORS[level], style='bold') + '  ' +
                  Logger._color(message + suffix, fg='white'), file=sys.stderr)

    def debug(self, message: str, **kwargs) -> None:
        self._log(message, 3, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log(message, 2, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        self._log(message, 1, **kwargs)

    def err(self, message: str, **kwargs) -> None:
        self._log(message, 0, **kwargs)
