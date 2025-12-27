import argparse
import sys
from pathlib import Path
from pprint import pprint
from typing import Any

from pypdf.errors import FileNotDecryptedError, WrongPasswordError, PdfReadError

import aidapdf
from aidapdf import util
from aidapdf.file import PdfFile, parse_file_specifier
from aidapdf.log import Logger
from aidapdf.pageselector import PageSelector


_logger = Logger(__name__)


def version(args: argparse.Namespace):
    if args.terse:
        print(aidapdf.__version__)
    else:
        print(aidapdf.__name__, aidapdf.__version__)


def parse_page_spec(args: argparse.Namespace):
    bake_file: PdfFile | None = None
    if args.file:
        (filename, _, password) = parse_file_specifier(args.file)
        bake_file = PdfFile(filename, None, password)
        bake_file.get_reader_unsafe()

    try:
        while True:
            if args.spec:
                spec = args.spec
            else:
                spec = input((bake_file.path.name if bake_file else '') + '> ')

            page_spec = PageSelector.parse(spec)
            print(page_spec)
            if bake_file:
                pprint(list(map(lambda x: x+1, page_spec.bake(bake_file))))

            if args.spec:
                break
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        if bake_file:
            bake_file.finalize()


def info(args: argparse.Namespace):
    _logger.debug(f'info {args}')

    def print_target(target: str, prefix: str, value: Any):
        if target in args.targets:
            print(prefix + ':\t' + str(value))

    file = PdfFile(*parse_file_specifier(args.file))
    with file.get_reader():
        pages = file.get_page_count()
        print_target("pages", "Pages", pages)
        print_target("metadata", "Metadata", file.get_metadata(printable=True))


def extract(args: argparse.Namespace):
    _logger.debug(f"extract {args}")

    tup = parse_file_specifier(args.file)
    stream = open(args.output_file, mode='w+') if args.output_file else sys.stdout
    file = PdfFile(*tup)
    with file.get_reader():
        for page in file.get_pages():
            print(page.extract_text(extraction_mode=args.extract_mode), file=stream)
    if args.output_file:
        stream.close()
        _logger.info(f"wrote extracted text to {repr(args.output_file)}")


def copy(args: argparse.Namespace) -> bool:
    _logger.debug(f"copy {args}")

    (filename, page_selector, password) = parse_file_specifier(args.file)
    blank_pages = PageSelector.parse(args.add_blank) if args.add_blank else None
    try:
        if args.select: page_selector = PageSelector.parse(args.select)
        # open in file
        file = PdfFile(filename, page_selector, password)
        # open out file
        out = PdfFile(args.output_file, owner=file)

        # open writer
        with file.get_reader(), out.get_writer() as writer:
            for page in file.get_pages():
                # copy every page
                if args.reverse:
                    writer.insert_page(page, 0)
                else:
                    writer.add_page(page)

            if blank_pages:
                bs = blank_pages.bake(file)
                for idx in bs:
                    out.insert_blank_page(idx)

            if args.copy_metadata:
                out.copy_metadata_from_owner()
            if args.password or args.owner_password:
                out.encrypt(args.password, args.owner_password)

        _logger.info(f"copied {repr(filename)} to {repr(str(out.path))}")

        if args.preview:
            util.open_file(out.path)
    except WrongPasswordError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]} (password provided: {repr(password)})")
        return False
    except FileNotDecryptedError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]} (no password provided)")
        return False
    except PdfReadError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]}")
        return False
    return True


def split(args: argparse.Namespace) -> bool:
    _logger.debug(f'split {args}')

    if args.count <= 0:
        _logger.err(f"count must be larger than 0 (is {args.count})")

    _logger.debug(f"split {repr(args.file)} count {args.count} " +
                f"(owner_password={repr(args.owner_password)})")

    (filename, page_spec, password) = parse_file_specifier(args.file)
    fp = Path(filename)
    template = args.output_file_template or "{dir}/{name}-{i}.pdf"

    try:
        file = PdfFile(filename, page_spec, password)
        with file.get_reader():
            if args.count > file.get_page_count():
                _logger.err(f"count must be smaller or equal to the page count ({args.count} > {file.get_page_count()})")

            outfiles: list[PdfFile] = []
            for i in range(args.count):
                outfiles.append(PdfFile(template.format(dir=fp.parent, name=fp.stem, ext=fp.suffix, i=i+1), owner=file))
                _logger.info(f"output file {i+1}: {outfiles[-1]}")

            i = 0
            for page in file.get_pages():
                outfiles[i % args.count].get_writer_unsafe().add_page(page)
                i += 1

            for f in outfiles:
                if args.copy_metadata:
                    f.copy_metadata_from_owner()
                if args.owner_password:
                    f.encrypt(args.owner_password)
                f.close_writer()
    except WrongPasswordError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]} (password provided: {repr(password)})")
        return False
    except FileNotDecryptedError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]} (no password provided)")
        return False
    except PdfReadError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]}")
        return False

    return True
