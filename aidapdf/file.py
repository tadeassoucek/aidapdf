import platform
from contextlib import contextmanager
from os import PathLike, path
from pathlib import Path
from typing import Iterator, Generator, Tuple, Any, Optional

from pypdf import PdfReader, PageObject, PdfWriter
from pypdf.generic import IndirectObject

from aidapdf.log import Logger
from aidapdf.pageselector import PageSelector
from aidapdf.util import repr_password

_logger = Logger(__name__)


def parse_file_specifier(fsp: str) -> Tuple[str, str, str]:
    toks = fsp.split(':')

    # on windows, "C:\Users\...\Downloads\file.pdf" could be interpreted as a file name "C" with "\Users\..." being
    # interpreted as the page selector. to prevent this, we check if such a file exists in the CWD and if not,
    # we assume the "[a-zA-Z]:" prefix is actually part of the path
    if platform.system() == 'Windows' and len(toks[0]) == 1 and len(toks) > 1:
        drive = toks[0]
        # just in case: what if the user is referring to a file named "C" in the CWD?
        if not path.exists(drive):
            toks = toks[1:]
            toks[0] = drive + ':' + toks[0]

    filename: str | None = toks[0]
    selector: str | None = None
    password: str | None = None
    if len(toks) >= 2:
        selector = toks[1] or None
    if len(toks) >= 3:
        password = toks[2] or None

    _logger.debug(f'file specifier parsed as {repr(filename)}; selector={repr(selector)}; '
                  f'password={repr_password() if password else ''}')

    return filename, selector, password


class PdfFile:
    def __init__(self, filename: str | PathLike,
                 selector: Optional[str | PageSelector] = None,
                 password: Optional[str] = None,
                 owner: Optional['PdfFile'] = None):
        self.path = Path(filename)
        self.selector: Optional[PageSelector] = PageSelector.parse(selector) if type(selector) is str else selector or None
        self.owner = owner
        self.password = password

        self._reader: Optional[PdfReader] = None
        self._reader_open = False
        self._writer: Optional[PdfWriter] = None
        self._writer_open = False

        _logger.debug(f"{self}: created")

    @contextmanager
    def get_reader(self) -> Generator[PdfReader, None, None]:
        """
        Creates a reader. Use with a `with` statement.
        :return: The created `PdfReader` object.
        """

        if self._reader_open: raise ValueError("reader already open")

        try:
            self._reader = PdfReader(self.path, password=self.password)
            self._reader_open = True
            _logger.debug(f"{self}: reader opened")
            yield self._reader
        finally:
            self.close_reader()

    def get_reader_unsafe(self) -> PdfReader:
        """
        If a reader already exists, returns it. Otherwise, creates a new one.
        Should only be used when you can't use `get_reader()`. Don't forget to call `close_reader()` after you're finished.
        :return: The already open or newly created `PdfReader` object.
        """

        if self._reader is not None:
            return self._reader
        self._reader = PdfReader(self.path, password=self.password)
        self._reader_open = True
        _logger.debug(f"{self}: reader opened")
        return self._reader

    @contextmanager
    def get_writer(self) -> Generator[PdfWriter, None, None]:
        if self._writer_open: raise ValueError("writer already open")

        try:
            self._writer = PdfWriter()
            self._writer_open = True
            _logger.debug(f"{self}: writer opened")
            yield self._writer
        finally:
            self.close_writer()

    def get_writer_unsafe(self) -> PdfWriter:
        if self._writer is not None:
            return self._writer
        self._writer = PdfWriter()
        self._writer_open = True
        _logger.debug(f"{self}: writer opened")
        return self._writer

    def close_reader(self) -> None:
        if self._reader is None or not self._reader_open:
            raise ValueError(f"{self}.close_reader() called but no reader is open")

        self._reader.close()
        self._reader = None
        self._reader_open = False
        _logger.debug(f"{self}: reader closed")
        self._reader = None

    def close_writer(self) -> None:
        if self._writer is None or not self._writer_open:
            raise ValueError(f"{self}.close_writer() called but no writer is open")

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
        password = password or (self.owner and self.owner.password)
        if not password: raise ValueError("no password provided")
        if not owner_password: raise ValueError("no owner password provided")
        self._writer.encrypt(password or self.owner.password, owner_password)
        if self.owner.password:
            _logger.debug(f"{self}: encrypted with password taken from {self.owner} and provided owner_password ({repr_password()})")
        else:
            _logger.debug(f"{self}: encrypted with the provided passwords")

    def get_page_count(self) -> int:
        if not self._reader_open: raise ValueError("reader closed")
        return len(self._reader.pages)

    def get_pages(self) -> Iterator[PageObject]:
        if not self._reader_open: raise ValueError("reader closed")
        if self.selector is None:
            for page in self._reader.pages:
                yield page
        else:
            for i in self.selector.bake(self):
                yield self._reader.get_page(i)

    def __repr__(self) -> str:
        return f"PdfFile({repr(str(self.path))})"
