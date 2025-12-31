import argparse
import platform
from typing import Optional, Literal


class Config:
    COLOR = False
    VERBOSITY_LEVEL = 2
    RAW_FILENAMES = False
    PLATFORM: Optional[Literal["macOS", "Windows"]] = None

    @staticmethod
    def load_from_args(args: argparse.Namespace) -> None:
        if args.platform != "auto":
            assert args.platform in ("macos", "windows", "other")

            if args.platform == "macos":
                Config.PLATFORM = "macOS"
            elif args.platform == "windows":
                Config.PLATFORM = "Windows"
            elif args.platform == "other":
                Config.PLATFORM = None
        else:
            if platform.system() == 'Darwin':
                Config.PLATFORM = "macOS"
            elif platform.system() == 'Windows':
                Config.PLATFORM = "Windows"
            else:
                Config.PLATFORM = None

        Config.COLOR = args.color
        Config.RAW_FILENAMES = args.raw_filenames

        if "verbose_level" in args and args.verbose_level is not None:
            Config.VERBOSITY_LEVEL = args.verbose_level

    @staticmethod
    def to_str() -> str:
        return (f"config.platform = {repr(Config.PLATFORM or 'other')}, config.color = {Config.COLOR}, "
                f"config.raw_filenames = {Config.RAW_FILENAMES}, config.verbosity_level = {Config.VERBOSITY_LEVEL}")
