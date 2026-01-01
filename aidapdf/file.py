from datetime import datetime
import sys
from contextlib import contextmanager
from os import path, PathLike
from pathlib import Path
from typing import Iterator, Generator, Any, Optional, Literal

import pypdf
from pypdf import PdfReader, PageObject, PdfWriter
from pypdf.generic import IndirectObject

from aidapdf import util
from aidapdf.config import Config, ansicolor
from aidapdf.log import Logger
from aidapdf.pageselector import PageSelector
from aidapdf.util import repr_password

from getpass import getpass


_logger = Logger(__name__)


class InternalFileException(Exception):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, kwargs)


def check_filename(fp: str) -> str:
    if not Path(fp).is_file():
        raise FileNotFoundError(f"file {repr(fp)} not found")
    return fp


def parse_file_specifier(fsp: str) -> tuple[str, Optional[str], Optional[str]]:
    if Config.RAW_FILENAMES:
        return check_filename(fsp), None, None

    toks = fsp.split(':')

    # on windows, "C:\Users\...\Downloads\file.pdf" could be interpreted as a file name "C" with "\Users\..." being
    # interpreted as the page selector. to prevent this, we check if such a file exists in the CWD and if not,
    # we assume the "[a-zA-Z]:" prefix is actually part of the path
    if Config.PLATFORM == "Windows" and len(toks[0]) == 1 and len(toks) > 1:
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
                  f'password={repr_password(password)}')

    return check_filename(filename), selector, password


class PdfFile:
    def __init__(self, filename: str | PathLike,
                 selector: Optional[str | PageSelector] = None,
                 password: Optional[str] = None,
                 source_file: Optional['PdfFile'] = None):
        self.path = Path(filename)
        self.selector: Optional[PageSelector] = PageSelector.parse(selector) if type(selector) is str else selector or None
        self.source_file = source_file
        self.password = password

        self._reader: Optional[PdfReader] = None
        self._reader_open = False
        self._writer: Optional[PdfWriter] = None
        self._writer_open = False

        self.title: Optional[str] = None
        self.author: Optional[str] = None
        self.subject: Optional[str] = None
        self.keywords: Optional[list[str]] = None
        self.creator: Optional[str] = None
        """Program that created the document."""
        self.producer: Optional[str] = None
        """Program that converted the document to PDF."""
        self.creation_date: Optional[datetime] = None
        self.modified_date: Optional[datetime] = None

        self._logger = Logger(repr(self), parent=_logger)
        self._logger.debug("created")

    def _create_reader(self) -> None:
        # just making sure...
        assert self._reader is None and not self._reader_open

        self._reader = PdfReader(self.path)
        encrypted = self._reader.is_encrypted
        while encrypted:
            # try to decrypt
            res = self._reader.decrypt(self.password or "")
            if res == pypdf.PasswordType.NOT_DECRYPTED:
                # password is incorrect
                self._logger.err("incorrect password")
                # read password
                self.password = getpass(f"Password to read file {repr(str(self.path))}: ")
            else:
                # decrypted successfully
                encrypted = False
                self._logger.info("decrypted successfully")
        self._reader_open = True
        self._derive_basic_metadata()
        self._logger.debug("reader opened")

    @contextmanager
    def get_reader(self) -> Generator[PdfReader, None, None]:
        """
        Create a reader. Use with a `with` statement.
        :return: The created `PdfReader` object.
        """

        if self._reader_open: raise InternalFileException("reader already open")

        try:
            self._create_reader()
            yield self._reader
        finally:
            self.close_reader()

    def get_reader_unsafe(self) -> PdfReader:
        """
        If a reader already exists, return it. Otherwise, create a new one. Should only be used when you can't use
        `get_reader()`. Don't forget to call `close_reader()` after you're finished.
        :return: The already open or newly created `PdfReader` object.
        """

        if self._reader is not None:
            return self._reader
        self._create_reader()
        # useless, just here to apease the type checker
        assert self._reader is not None
        return self._reader

    @contextmanager
    def get_writer(self) -> Generator[PdfWriter, None, None]:
        """
        Create a reader. Use with a `with` statement.
        :return: The created `PdfReader` object.
        """

        if self._writer_open: raise InternalFileException("writer already open")

        try:
            self._writer = PdfWriter()
            self._writer_open = True
            self._logger.debug("writer opened")
            yield self._writer
        finally:
            self.close_writer()

    def get_writer_unsafe(self) -> PdfWriter:
        """
        If a writer already exists, return it. Otherwise, create a new one. Should only be used when you can't use
        `get_writer()`. Don't forget to call `close_writer()` after you're finished.
        :return: The already open or newly created `PdfReader` object.
        """

        if self._writer is not None:
            return self._writer
        self._writer = PdfWriter()
        self._writer_open = True
        self._logger.debug("writer opened")
        return self._writer

    def _ensure_reader_open(self) -> None:
        if self._reader is None or not self._reader_open:
            raise InternalFileException("reader not open",
                                        _reader=self._reader, _reader_open=self._reader_open)

    def _ensure_writer_open(self) -> None:
        if self._writer is None or not self._writer_open:
            raise InternalFileException("writer not open",
                                        _writer=self._writer, _writer_open=self._writer_open)

    def close_reader(self) -> None:
        """Closes and disposes of the reader if one is open."""

        if not self._reader_open:
            return
        self._reader.close()
        self._reader = None
        self._reader_open = False
        self._logger.debug("reader closed")
        self._reader = None

    def close_writer(self) -> None:
        """Closes and disposes of the writer if one is open."""

        if not self._writer_open:
            return
        self._writer.write(self.path)
        self._writer_open = False
        self._writer.close()
        self._logger.debug("writer closed")
        self._writer = None

    @staticmethod
    def _parse_datetime(key: str, raw: str) -> Optional[datetime]:
        if not raw: return None
        raw = raw.strip()
        timezone_stripped = False
        # strip timezone
        if raw.endswith("Z00'00'"):
            raw = raw[:-7]
            timezone_stripped = True
        try:
            return datetime.strptime(raw, "D:%Y%m%d%H%M%S" + ('%z' if not timezone_stripped else ''))
        except ValueError:
            _logger.warn(f"'{key}' is not a valid date: {repr(raw)}")

    def _derive_basic_metadata(self) -> None:
        self._ensure_reader_open()
        metadata = self.get_metadata(resolve=True)
        self.title = metadata.get('/Title', None)
        self.author = metadata.get('/Author', None)
        self.subject = metadata.get('/Subject', None)
        self.keywords = metadata.get('/Keywords', None)
        self.creator = metadata.get('/Creator', None)
        self.producer = metadata.get('/Producer', None)
        creation_date = metadata.get('/CreationDate', None)
        self.creation_date = self._parse_datetime('/CreationDate', creation_date)
        modified_date = metadata.get('/ModDate', None)
        self.modified_date = self._parse_datetime('/ModDate', modified_date)

    def copy_metadata_from_owner(self) -> None:
        """Copies metadata from the owner file. The writer has to be opened."""
        self._ensure_writer_open()
        metadata = self.source_file.get_metadata()
        self._writer.add_metadata(metadata)
        self._logger.info(f"copied metadata from {self.source_file}: {metadata}")

    def add_metadata(self, metadata: dict[str, Any]) -> None:
        """Add metadata. The writer has to be open."""
        self._ensure_writer_open()
        self._writer.add_metadata(metadata)
        self._logger.info(f"added metadata {metadata}")

    def add_blank_page(self) -> None:
        """Add a blank page to the end of the file. The writer has to be opened."""
        self._ensure_writer_open()
        self._writer.add_blank_page()
        self._logger.debug(f"added blank page")

    def insert_blank_page(self, index: int) -> None:
        """
        Insert a blank page at the given index. The writer has to be opened.
        :param index: Index to insert a blank page at. If >= the page count, behaves like `add_blank_page()`.
        :return:
        """

        self._ensure_writer_open()
        if index >= len(self._writer.pages):
            self._writer.add_blank_page()
        else:
            self._writer.insert_blank_page(None, None, index)
        self._logger.debug(f"inserted blank page @ {index}")

    def pad_pages(self, to: int, where: Literal['start', 'end'] = 'end') -> None:
        """
        Add blank pages until the file has `to` pages.
        :param to: Target number of pages.
        :param where: Where to add the blank pages. If `start`, they're added to the beginning, if `end` , they're
        appended to the end.
        """

        self._ensure_writer_open()
        diff = to - self.get_page_count()
        if diff > 0:
            for i in range(diff):
                if where == 'end':
                    self.add_blank_page()
                else:
                    self.insert_blank_page(0)
        self._logger.info(f"padded pages to {to}")

    def get_metadata(self, resolve = False) -> dict[str, Any]:
        """
        Return the metadata of the file. The writer has to be opened.
        :param resolve: If `True`, resolves indirect objects.
        """

        self._ensure_reader_open()
        meta_raw = self._reader.metadata
        if resolve:
            meta = {}
            for k, v in meta_raw.items():
                meta[k] = str(v) if isinstance(v, IndirectObject) else v
            return meta
        else:
            return meta_raw

    def get_permissions(self) -> Optional[dict[str, bool]]:
        """
        Return the permissions of the file as dictionary of {'permission_name': bool}. The reader has to be opened.
        """

        self._ensure_reader_open()
        permissions = self._reader.user_access_permissions
        if permissions is None: return None
        return permissions.to_dict()

    def encrypt(self, owner_password: str, password: Optional[str] = None) -> None:
        """
        Encrypts the file with the provided passwords. The writer has to be opened.
        :param owner_password: Password to change the encryption and permissions of the file.
        :param password: Password to access the file. If `None`, the value is taken from `self.password`.
        """

        self._ensure_writer_open()
        password = password or (self.source_file and self.source_file.password)
        # prompt for owner password if not provided
        if not owner_password:
            try:
                owner_password = getpass(f"Owner password to encrypt file {repr(str(self.path))}: ")
            except (EOFError, KeyboardInterrupt):
                self._logger.err("no owner password provided")
                sys.exit(1)

        self._writer.encrypt(password, owner_password)
        if password == self.source_file.password:
            self._logger.info(f"encrypted with password taken from {self.source_file} and provided owner_password "
                               f"({repr_password(owner_password)})")
        else:
            self._logger.info("encrypted with the provided passwords")

    def get_page_count(self) -> int:
        """
        Return number of pages in the file. Presupposes that the reader is open.
        """

        self._ensure_reader_open()
        return len(self._reader.pages)

    def get_pages(self, selector: Optional[PageSelector] = None) -> Iterator[PageObject]:
        """
        Iterates over selected pages. Presupposes that the reader is open.
        :param selector: Selector override.
        """

        self._ensure_reader_open()
        selector = selector or self.selector
        if selector is None:
            for page in self._reader.pages:
                yield page
        else:
            for i in selector.bake(self):
                yield self._reader.get_page(i)

    def __str__(self) -> str:
        color_value = lambda v: ansicolor(v, stream=sys.stdout, fg=Config.COLOR_VALUE)
        text = f"PDF file at {color_value(repr(str(self.path)))}"
        if self._reader_open:
            if self._reader.is_encrypted:
                text += " (encrypted)"
            else:
                text += " (unencrypted)"
        text += '.\n'
        if self.title:
            text += repr(self.title)
        if self.author:
            if self.title:
                text += ' by '
            else:
                text += 'By '
            text += color_value(self.author)
        if self.creator or self.creation_date or self.modified_date:
            if self.title or self.author:
                text += ' (created '
            else:
                text += 'Created '
            if self.creator:
                text += f'in {color_value(self.creator)} '
            if self.creation_date:
                text += f'{color_value(util.format_date(self.creation_date))}'
            if self.modified_date:
                text += f'; last modified {color_value(util.format_date(self.modified_date))}'
            if self.title or self.author:
                text += ')'
            text += '.'
        return text

    def __repr__(self) -> str:
        return f"PdfFile({repr(str(self.path))})"
