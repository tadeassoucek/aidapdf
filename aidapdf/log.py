import pprint
import sys


class Logger:
    def __init__(self, name: str):
        self.name = name

    def _log(self, message: str, level: str, **kwargs) -> None:
        epilogue = ' ' + pprint.pformat(kwargs) if kwargs else ""
        print(f"[{level} {self.name}] " + message + epilogue, file=sys.stderr)

    def log(self, message: str, **kwargs) -> None:
        self._log(message, "LOG", **kwargs)

    def err(self, message: str, **kwargs) -> None:
        self._log(message, "ERR", **kwargs)
