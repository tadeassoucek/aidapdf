from typing import Generator
from pathlib import Path
import os

import pypdf

from aidapdf.exceptions import AidaInternalException, AidaIoException
import aidapdf.page_range_parser as prp
from aidapdf.log import log_action
from aidapdf.config import Config


class PdfFile:
    @staticmethod
    def from_str(src: str) -> 'PdfFile':
        toks = src.split(';')
        if len(toks) == 1:
            return PdfFile(toks[0])
        else:
            return PdfFile(toks[0], toks[1])

    @staticmethod
    def from_list(src: list) -> list['PdfFile']:
        res: list[PdfFile] = []
        for s in src:
            res.append(PdfFile.from_str(s))
        return res

    def __init__(self, path: Path | str, page_ranges: list[prp.RangeStringToken] | str | None = None):
        self.path = Path(path) if type(path) is str else path

        if page_ranges is None:
            self.page_ranges = [prp.PageRange(1, -1)]
        elif type(page_ranges) is str:
            self.page_ranges = prp.parse_ranges(page_ranges)
        elif type(page_ranges) is list:
            self.page_ranges = page_ranges
        else:
            raise AidaInternalException(f"{page_ranges=} must be `None`, `str` or a parsed range")

        self._baked_range: list[int] | None = None
        self.interactor: pypdf.PdfWriter | pypdf.PdfReader | None = None

    def get_writer(self) -> pypdf.PdfWriter:
        self.interactor = pypdf.PdfWriter()
        return self.interactor

    def get_reader(self) -> pypdf.PdfReader:
        self.interactor = pypdf.PdfReader(self.path)
        return self.interactor

    def selected_pages(self, reverse=False) -> Generator[pypdf.PageObject]:
        if not self._baked_range:
            self._baked_range = prp.bake_range(self.page_ranges, len(self.interactor.pages))

        for p in reversed(self._baked_range) if reverse else self._baked_range:
            yield self.interactor.pages[p-1]

    def write(self) -> None:
        if not self.interactor or not isinstance(self.interactor, pypdf.PdfWriter):
            raise AidaInternalException("interactor either not instantiated or isn't a writer")
        log_action("emit " + str(self))
        if self.path.exists(follow_symlinks=True) and not Config.FORCE_OVERWRITE:
            action = input(repr(str(self.path)) + " already exists. [o]verwrite or [C]ancel? : ")
            if action.strip().lower() != 'o':
                raise AidaIoException(f"couldn't overwrite {repr(str(self.path))}; choose a different output file")
        self.interactor.write(self.path)
        self.interactor.close()

    def delete(self):
        log_action("delete " + str(self))
        os.remove(self.path)

    def __str__(self):
        page_string = ""
        if self.interactor:
            page_count = len(self.interactor.pages)
            page_string = " (" + str(page_count) + " page" + ('s' if page_count != 1 else '') + ")"
        return repr(str(self.path)) + page_string

    def __repr__(self):
        if len(self.page_ranges) == 1 and self.page_ranges[0] == prp.PageRange(1, -1):
            page_range_str = ""
        else:
            page_range_str = ';' + prp.range_to_str(self.page_ranges)

        return 'PdfFile(' + repr(str(self.path)) + page_range_str + ")"
