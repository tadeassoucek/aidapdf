import platform


class Config:
    COLOR = False
    VERBOSITY_LEVEL = 2
    RAW_FILENAMES = False
    WINDOWS = platform.system() == "Windows"
