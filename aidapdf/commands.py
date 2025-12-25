import argparse

from pypdf.errors import FileNotDecryptedError, WrongPasswordError

from aidapdf.file import PdfOutFile, PdfFile, parse_file_specifier
from aidapdf.log import Logger
from aidapdf.pagespecparser import PageSpec


_logger = Logger(__name__)


def page_count(args: argparse.Namespace):
    print(args.terse, args.files)


def parse_page_spec(args: argparse.Namespace):
    pagespec = PageSpec.parse(args.spec)
    print(pagespec)


def copy(args: argparse.Namespace) -> bool:
    _logger.log(f"copy {repr(args.file)} to {repr(args.output_file)} " +
                f"(owner_password={repr(args.owner_password)})")

    (filename, page_spec, password) = parse_file_specifier(args.file)
    try:
        # open in file
        file = PdfFile(filename, page_spec, password)
        if args.pages: file.page_spec = PageSpec.parse(args.pages)
        # open out file
        out = PdfOutFile(args.output_file, file)
        # open writer
        with out.get_writer(file.get_metadata() if args.copy_metadata else None, args.owner_password) as writer:
            for page in file.get_pages():
                # copy every page
                writer.add_page(page)
    except WrongPasswordError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]} (password provided: {repr(password)})")
        return False
    except FileNotDecryptedError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]} (no password provided)")
        return False
    return True
