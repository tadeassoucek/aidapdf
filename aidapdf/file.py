from argparse import ArgumentError
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from typing import Iterator, Generator, Tuple, Any, Optional

from pypdf import PdfReader, PageObject, PdfWriter
from pypdf.generic import IndirectObject

from aidapdf.log import Logger
from aidapdf.pagespecparser import PageSpec


_logger = Logger(__name__)


def parse_file_specifier(fsp: str) -> Tuple[str, str, str]:
    toks = fsp.split(':')
    filename: str | None = toks[0]
    page_range: str | None = None
    password: str | None = None
    if len(toks) >= 2:
        page_range = toks[1] or None
    if len(toks) >= 3:
        password = toks[2] or None
    return filename, page_range, password


class PdfFile:
    def __init__(self, filename: str | PathLike,
                 page_spec: Optional[str | PageSpec] = None,
                 password: Optional[str] = None,
                 owner: Optional['PdfFile'] = None):
        self.path = Path(filename)
        self.page_spec: Optional[PageSpec] = PageSpec.parse(page_spec) if type(page_spec) is str else page_spec or None
        self.owner = owner
        self.password = owner.password if owner and not password else password

        self._reader: Optional[PdfReader] = None
        self._reader_open = False
        self._writer: Optional[PdfWriter] = None
        self._writer_open = False
        _logger.debug(f"{self}: created")

    @contextmanager
    def get_reader(self) -> Generator[PdfReader, None, None]:
        try:
            self._reader = PdfReader(self.path)
            self._reader_open = True
            _logger.debug(f"{self}: reader opened")
            yield self._reader
        finally:
            self.finalize()

    def get_reader_unsafe(self) -> PdfReader:
        if self._reader is not None:
            return self._reader
        self._reader = PdfReader(self.path)
        self._reader_open = True
        _logger.debug(f"{self}: reader opened")
        return self._reader

    # Generator[yield_type, send_type, return_type]
    @contextmanager
    def get_writer(self) -> Generator[PdfWriter, None, None]:
        try:
            self._writer = PdfWriter()
            self._writer_open = True
            _logger.debug(f"{self}: writer opened")
            yield self._writer
        finally:
            self.finalize()

    def get_writer_unsafe(self) -> PdfWriter:
        if self._writer is not None:
            return self._writer
        self._writer = PdfWriter()
        self._writer_open = True
        _logger.debug(f"{self}: writer opened")
        return self._writer

    def finalize(self) -> None:
        if self._writer is None and self._reader is None:
            _logger.debug(f"{self}.finalize() called but no reader or writer is open")
        elif self._reader is not None:
            self._reader.close()
            self._reader_open = False
            _logger.debug(f"{self}: reader closed")
            self._reader = None
        elif self._writer is not None:
            self._writer.write(self.path)
            self._writer_open = False
            self._writer.close()
            _logger.debug(f"{self}: writer closed")
            self._writer = None

    def copy_metadata_from_owner(self) -> None:
        if not self._writer_open: raise ValueError("writer closed")
        self._writer.add_metadata(self.owner.get_metadata())
        _logger.debug(f"{self}: copied metadata from {self.owner}")

    def add_metadata(self, metadata: dict[str, Any]) -> None:
        if not self._writer_open: raise ValueError("writer closed")
        self._writer.add_metadata(metadata)
        _logger.debug(f"{self}: added metadata {metadata}")

    def insert_blank_page(self, index: int) -> None:
        if not self._writer_open: raise ValueError("writer closed")
        if index >= len(self._writer.pages):
            self._writer.add_blank_page()
        else:
            self._writer.insert_blank_page(None, None, index)
        _logger.debug(f"{self}: inserted blank page @ {index}")

    def get_metadata(self, printable = False) -> dict[str, Any]:
        if not self._reader_open: raise ValueError("reader closed")
        meta_raw = self._reader.metadata
        if printable:
            meta = {}
            for k, v in meta_raw.items():
                if k.startswith('/'):
                    k = k[1:]
                meta[k] = str(v) if isinstance(v, IndirectObject) else v
            return meta
        else:
            return meta_raw

    def encrypt(self, password: Optional[str], owner_password: str):
        if not self._writer_open: raise ValueError("writer closed")
        if not password and (not self.owner or not self.owner.password): raise ValueError("no password provided")
        if not owner_password: raise ValueError("no owner password provided")
        self._writer.encrypt(password or self.owner.password, owner_password)
        if self.owner.password:
            _logger.debug(f"{self}: encrypted with password taken from {self.owner} and provided owner_password (*****)")
        else:
            _logger.debug(f"{self}: encrypted with the provided passwords")

    def get_page_count(self) -> int:
        if not self._reader_open: raise ValueError("reader closed")
        return len(self._reader.pages)

    def get_pages(self) -> Iterator[PageObject]:
        if not self._reader_open: raise ValueError("reader closed")
        if self.page_spec is None:
            for page in self._reader.pages:
                yield page
        else:
            for i in self.page_spec.bake(self):
                yield self._reader.get_page(i)

    def __repr__(self) -> str:
        return f"PdfFile({repr(str(self.path))})"
