import argparse
import os
import sys
from pathlib import Path
from pprint import pprint
from typing import Any

from pypdf.errors import FileNotDecryptedError, WrongPasswordError, PdfReadError

import aidapdf
import readline
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


def debug_testlog(_: argparse.Namespace) -> None:
    _logger.debug("message", s="Hello world!", i=10)
    _logger.info("message", s="Hello world!", i=10)
    _logger.warn("message", s="Hello world!", i=10)
    _logger.err("message", s="Hello world!", i=10)


def debug_parse_selector(args: argparse.Namespace):
    bake_file: PdfFile | None = None
    if args.file:
        (filename, _, password) = parse_file_specifier(args.file)
        bake_file = PdfFile(filename, None, password)
        bake_file.get_reader_unsafe()

    while True:
        raw_select = ""

        if args.select:
            raw_select = args.select
        else:
            try:
                raw_select = input((bake_file.path.name if bake_file else '') + '> ')
            except (EOFError, KeyboardInterrupt):
                print()
                break
            finally:
                if bake_file:
                    bake_file.close_reader()

        select = PageSelector.parse(raw_select)
        print(select)
        if bake_file:
            pprint(list(map(lambda x: x+1, select.bake(bake_file))))

        if args.select:
            break


def debug_parse_specifier(args: argparse.Namespace):
    while True:
        spec = ""
        if args.spec:
            spec = args.spec
        else:
            try:
                spec = input('> ')
            except (EOFError, KeyboardInterrupt):
                print()
                break

        path, selector, password = parse_file_specifier(spec)
        print(f"path = {repr(path)}, selector = {repr(selector)}, password = {repr(password)}")

        if args.spec:
            break


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
            if (args.copy_password and file.password) or args.owner_password:
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

    if len(args.select) <= 1:
        _logger.warn("only one selector provided; this action will only create one file which is more idiomatically "
                     "achieved with the `copy` command")

    (filename, page_spec, password) = parse_file_specifier(args.file)
    fp = Path(filename)
    template = args.output_file_template or "{dir}{name}-{i}.pdf"

    try:
        # input file
        file = PdfFile(filename, page_spec, args.password or password)
        with file.get_reader():
            for i in range(len(args.select)):
                selector = PageSelector.parse(args.select[i])
                ofp = template.format(dir=str(fp.parent) + os.sep, name=fp.stem, ext=fp.suffix,
                                                        i=i+1)
                # output file
                outfile = PdfFile(ofp, owner=file)

                with outfile.get_writer() as writer:
                    # copy selected pages
                    for page in file.get_pages(selector):
                        writer.add_page(page)

                    if args.copy_metadata:
                        outfile.copy_metadata_from_owner()
                    if (args.copy_password and file.password) or args.owner_password:
                        outfile.encrypt(args.password, args.owner_password)

                _logger.info(f"wrote to {repr(str(outfile.path))}")
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
