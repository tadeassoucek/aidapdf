import pprint
import sys


LOG_LEVEL = 2


class Logger:
    LEVELS = {
        0: "ERR!",
        1: "WARN",
        2: "INFO",
        3: "DBUG",
    }

    def __init__(self, name: str):
        self.name = name

    def _log(self, message: str, level: int, **kwargs) -> None:
        if level <= LOG_LEVEL:
            epilogue = ' ' + pprint.pformat(kwargs) if kwargs else ""
            print(f"[{Logger.LEVELS[level]} {self.name}] " + message + epilogue, file=sys.stderr)

    def dbug(self, message: str, **kwargs) -> None:
        self._log(message, 3, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log(message, 2, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        self._log(message, 1, **kwargs)

    def err(self, message: str, **kwargs) -> None:
        self._log(message, 0, **kwargs)
