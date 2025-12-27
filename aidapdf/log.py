import pprint
import sys


class Logger:
    LEVELS = {
        0: "ERR!",
        1: "WARN",
        2: "INFO",
        3: "DBUG",
    }

    LOG_LEVEL = 2

    def __init__(self, name: str):
        self.name = name

    def _log(self, message: str, level: int, **kwargs) -> None:
        if level <= Logger.LOG_LEVEL:
            prefix = f"{Logger.LEVELS[level]}:{self.name}"
            suffix = ' ' + pprint.pformat(kwargs) if kwargs else ""
            print(prefix + '  ' + message + suffix, file=sys.stderr)

    def debug(self, message: str, **kwargs) -> None:
        self._log(message, 3, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log(message, 2, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        self._log(message, 1, **kwargs)

    def err(self, message: str, **kwargs) -> None:
        self._log(message, 0, **kwargs)
