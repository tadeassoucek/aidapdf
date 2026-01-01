import argparse
import platform
import sys
from typing import Optional, Literal

import colors


class Config:
    COLOR = False

    COLOR_VALUE = 'cyan'

    VERBOSITY_LEVEL = 2
    RAW_FILENAMES = False
    PLATFORM: Optional[Literal["macOS", "Windows"]] = None

    @staticmethod
    def load_from_args(args: argparse.Namespace) -> None:
        if args.platform != "auto":
            assert args.platform in ("macos", "windows", "other")

            Config.Platform = {
                'macos': 'macOS',
                'windows': 'Windows',
                'other': None,
            }[args.platform]
        else:
            if platform.system() == 'Darwin':
                Config.PLATFORM = "macOS"
            elif platform.system() == 'Windows':
                Config.PLATFORM = "Windows"
            else:
                Config.PLATFORM = None

        Config.COLOR = args.color
        Config.RAW_FILENAMES = args.raw_filenames

        if "verbosity_level" in args and args.verbosity_level is not None:
            Config.VERBOSITY_LEVEL = args.verbosity_level

    @staticmethod
    def to_str() -> str:
        return (f"config.platform = {repr(Config.PLATFORM or 'other')}, config.color = {Config.COLOR}, "
                f"config.raw_filenames = {Config.RAW_FILENAMES}, config.verbosity_level = {Config.VERBOSITY_LEVEL}")


def ansicolor(text: str, stream=sys.stderr, *args, **kwargs) -> str:
    if Config.COLOR and stream.isatty():
        return colors.color(text, *args, **kwargs)
    else:
        return text
