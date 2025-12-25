from contextlib import contextmanager
from os import PathLike
from typing import Iterator, Generator, Tuple, Any

from pypdf import PdfReader, PageObject, PdfWriter
from pypdf.generic import IndirectObject

from aidapdf.log import Logger
from aidapdf.pagespecparser import PageSpec


_logger = Logger(__name__)


def parse_file_specifier(fsp: str) -> Tuple[str, str, str]:
    toks = fsp.split(';')
    filename: str | None = toks[0]
    page_range: str | None = None
    password: str | None = None
    if len(toks) >= 2:
        page_range = toks[1] or None
    if len(toks) >= 3:
        password = toks[2] or None
    return filename, page_range, password


class PdfFile:
    def __init__(self, filename: str | PathLike, page_spec: str | None = None, password: str | None = None):
        self.filename = filename
        self.page_spec: PageSpec = PageSpec.parse(page_spec) if page_spec else PageSpec.ALL
        self.password = password
        self._reader = PdfReader(self.filename, password=self.password)
        _logger.dbug(f"created {self}")

    @contextmanager
    def get_reader(self) -> Generator[PdfReader, None, None]:
        try:
            yield self._reader
        finally:
            self.finalize()

    def finalize(self):
        self._reader.close()
        _logger.dbug(f"closed {self}")

    def get_metadata(self) -> dict[str, Any]:
        meta_raw = self._reader.metadata
        meta = {}
        for k, v in meta_raw.items():
            if k.startswith('/'):
                k = k[1:]
            meta[k] = str(v) if isinstance(v, IndirectObject) else v
        return meta

    def get_page_count(self) -> int:
        return len(self._reader.pages)

    def get_pages(self) -> Iterator[PageObject]:
        with self.get_reader() as reader:
            for i in self.page_spec.bake(self):
                yield reader.get_page(i)

    def __repr__(self) -> str:
        return f"PdfFile(filename={repr(self.filename)}, page_spec={self.page_spec}, password={repr(self.password)})"


class PdfOutFile:
    def __init__(self, filename: str | PathLike, owner: PdfFile):
        self.filename = filename
        self.owner = owner
        self._writer: PdfWriter | None = None
        _logger.dbug(f"created {self}")

    # Generator[yield_type, send_type, return_type]
    @contextmanager
    def get_writer(self, metadata: dict[str, Any] | None, owner_password: str | None = None) -> Generator[PdfWriter, None, None]:
        self._writer = PdfWriter()
        try:
            yield self._writer
        finally:
            self.finalize(metadata, owner_password)
            self._writer = None

    def get_writer_unsafe(self) -> PdfWriter:
        if self._writer is not None:
            return self._writer
        self._writer = PdfWriter()
        return self._writer

    def finalize(self, metadata: dict[str, Any] | None, owner_password: str | None = None) -> None:
        if owner_password or self.owner.password:
            self._writer.encrypt(owner_password or self.owner.password, self.owner.password)
        if metadata: self._writer.add_metadata(metadata)
        self._writer.write(self.filename)
        self._writer.close()
        _logger.dbug(f"closed {self}: owner_password={repr(owner_password)}")

    def __repr__(self) -> str:
        return f"PdfOutFile(filename={repr(self.filename)}, owner={self.owner})"
