from contextlib import contextmanager
from os import PathLike
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
                 page_spec: Optional[str] = None,
                 password: Optional[str] = None,
                 owner: Optional['PdfFile'] = None):
        self.filename = filename
        self.page_spec: PageSpec | None = PageSpec.parse(page_spec) if page_spec else None
        self.owner = owner
        self.password = owner.password if owner and not password else password
        self._reader: Optional[PdfReader] = None
        self._writer: Optional[PdfWriter] = None
        _logger.debug(f"created {self}")

    @contextmanager
    def get_reader(self) -> Generator[PdfReader, None, None]:
        try:
            self._reader = PdfReader(self.filename)
            yield self._reader
        finally:
            self.finalize()

    def get_reader_unsafe(self) -> PdfReader:
        if self._reader is not None:
            return self._reader
        self._reader = PdfReader(self.filename)
        return self._reader

    # Generator[yield_type, send_type, return_type]
    @contextmanager
    def get_writer(self) -> Generator[PdfWriter, None, None]:
        try:
            self._writer = PdfWriter()
            yield self._writer
        finally:
            self.finalize()
            self._writer = None

    def get_writer_unsafe(self) -> PdfWriter:
        if self._writer is not None:
            return self._writer
        self._writer = PdfWriter()
        return self._writer

    def finalize(self) -> None:
        if self._writer is not None:
            self._writer.write(self.filename)
            self._writer.close()
            _logger.debug(f"closed {self}")
        elif self._reader is not None:
            self._reader.close()
            _logger.debug(f"closed {self}")
        else:
            _logger.err(f"{self}.finalize() called but no reader or writer is open")
            raise Exception(f"{self}.finalize() called but no reader or writer is open")

    def copy_metadata_from_owner(self) -> None:
        self._writer.add_metadata(self.owner.get_metadata())

    def add_metadata(self, metadata: dict[str, Any]) -> None:
        self._writer.add_metadata(metadata)

    def insert_blank_page(self, index: int) -> None:
        if index >= len(self._writer.pages):
            self._writer.add_blank_page()
        else:
            self._writer.insert_blank_page(None, None, index)
        _logger.debug(f"{self}: inserted blank page @ {index}")

    def get_metadata(self, printable = False) -> dict[str, Any]:
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

    def encrypt(self, owner_password: str):
        self._writer.encrypt(self.owner.password, owner_password)

    def get_page_count(self) -> int:
        return len(self._reader.pages)

    def get_pages(self) -> Iterator[PageObject]:
        if self.page_spec is None:
            for page in self._reader.pages:
                yield page
        else:
            for i in self.page_spec.bake(self):
                yield self._reader.get_page(i)

    def __repr__(self) -> str:
        return f"PdfFile({repr(self.filename)})"
