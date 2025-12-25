import argparse
import sys
from pathlib import Path
from pprint import pprint
from typing import Any

from pypdf.errors import FileNotDecryptedError, WrongPasswordError, PdfReadError

from aidapdf.file import PdfOutFile, PdfFile, parse_file_specifier
from aidapdf.log import Logger
from aidapdf.pagespecparser import PageSpec


_logger = Logger(__name__)


def page_count(args: argparse.Namespace):
    print(args.terse, args.files)


def parse_page_spec(args: argparse.Namespace):
    bake_file: PdfFile | None = None
    if args.bake_file:
        (filename, _, password) = parse_file_specifier(args.bake_file)
        bake_file = PdfFile(filename, None, password)

    spec = None
    while True:
        if args.spec:
            spec = args.spec
        else:
            try:
                spec = input((bake_file.filename if bake_file else '') + '> ')
            except (EOFError, KeyboardInterrupt):
                break

        pagespec = PageSpec.parse(spec)
        print(pagespec)
        if bake_file:
            pprint(list(map(lambda x: x+1, pagespec.bake(bake_file))))

        if args.spec:
            break


def info(args: argparse.Namespace):
    def print_target(target: str, prefix: str, value: Any):
        if target in args.targets:
            print(prefix + ':', value)

    file = PdfFile(*parse_file_specifier(args.file))
    pages = file.get_page_count()
    print_target("pages", "Pages", pages)
    print_target("metadata", "Metadata", file.get_metadata())
    file.finalize()


def extract(args: argparse.Namespace):
    tup = parse_file_specifier(args.file)
    stream = open(args.output_file, mode='w+') if args.output_file else sys.stdout
    file = PdfFile(*tup)
    for page in file.get_pages():
        print(page.extract_text(extraction_mode=args.extract_mode), file=stream)
    file.finalize()
    if args.output_file:
        stream.close()


def copy(args: argparse.Namespace) -> bool:
    _logger.dbug(f"copy {repr(args.file)} to {repr(args.output_file)} " +
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
    except PdfReadError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]}")
        return False
    return True


def split(args: argparse.Namespace) -> bool:
    if args.count <= 0:
        _logger.err(f"count must be larger than 0 (is {args.count})")

    _logger.dbug(f"split {repr(args.file)} count {args.count} " +
                f"(owner_password={repr(args.owner_password)})")

    (filename, page_spec, password) = parse_file_specifier(args.file)
    fp = Path(filename)
    template = args.output_file_template or "{dir}/{name}-{i}.pdf"

    try:
        file = PdfFile(filename, page_spec, password)
        if args.count > file.get_page_count():
            _logger.err(f"count must be smaller or equal to the page count ({args.count} > {file.get_page_count()})")

        outfiles: list[PdfOutFile] = []
        for i in range(args.count):
            outfiles.append(PdfOutFile(template.format(dir=fp.parent, name=fp.stem, ext=fp.suffix, i=i+1), file))
            _logger.info(f"output file {i+1}: {outfiles[-1]}")

        i = 0
        for page in file.get_pages():
            outfiles[i % args.count].get_writer_unsafe().add_page(page)
            i += 1

        for f in outfiles:
            f.finalize(file.get_metadata() if args.copy_metadata else None, args.owner_password)
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
