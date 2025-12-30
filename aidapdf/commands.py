import argparse
import os
import sys
from pathlib import Path
from pprint import pprint
from typing import Any, Optional

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
    _logger.debug("message")
    _logger.info("message")
    _logger.warn("message")
    _logger.err("message")


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


def info(args: argparse.Namespace) -> bool:
    _logger.debug(f'info {args}')

    def print_target(target: str, prefix: str, value: Any):
        if target in args.targets:
            print(prefix + ':\t' + str(value))

    file = PdfFile(*parse_file_specifier(args.file))
    with file.get_reader():
        pages = file.get_page_count()
        print_target("pages", "Pages", pages)
        print_target("metadata", "Metadata", file.get_metadata(resolve=True))

    return True


def extract(args: argparse.Namespace) -> bool:
    _logger.debug(f"extract {args}")

    extract_text = not not args.text_file
    text_file: str = "stdout" if args.text_file == '-' else args.text_file
    text_file_stream = None if not extract_text else sys.stdout if text_file == "stdout" else open(args.output_file, mode='w+')
    extract_images = not not args.image_file_template
    image_file_template: str = args.image_file_template

    if not extract_text and not extract_images:
        _logger.warn("nothing to extract specified")
        return False

    try:
        filename, page_spec, password = parse_file_specifier(args.file)
    except FileNotFoundError as e:
        _logger.err(e.args[0])
        return False

    try:
        file = PdfFile(filename, page_spec, password)
        with file.get_reader():
            text = ""
            for page in file.get_pages():
                if extract_text:
                    text += page.extract_text(extraction_mode=args.extract_mode)
                if extract_images:
                    _logger.debug(f"found {len(page.images)} images on page {page.page_number+1}")
                    for i, image_object in enumerate(page.images):
                        ext = image_object.name.split(".")[-1]
                        fp = image_file_template.format(dir=str(file.path.parent) + os.sep, name=file.path.stem, p=page.page_number+1,
                                                        i=i+1, img=image_object.name, ext=ext)
                        image_object.image.save(fp)
                        _logger.info(f"wrote image on page {page.page_number+1} to file {repr(fp)}")
            if extract_text:
                print(text, file=text_file_stream)
        if extract_text:
            text_file_stream.close()
            _logger.info(f"wrote extracted text to {repr(text_file)}")
    except PdfReadError as e:
        _logger.err(f"{repr(filename)}: {e.args[0]}")
        return False

    return True


def edit(args: argparse.Namespace) -> bool:
    _logger.debug(f"copy {args}")

    try:
        (filename, page_selector, password) = parse_file_specifier(args.file)
    except FileNotFoundError as e:
        _logger.err(e.args[0])
        return False

    output_file = filename if args.output_file == '-' else args.output_file
    blank_pages = PageSelector.parse(args.add_blank) if args.add_blank else None

    try:
        if args.select: page_selector = PageSelector.parse(args.select)
        # open in file
        file = PdfFile(filename, page_selector, args.password or password)
        # open out file
        out = PdfFile(output_file, owner=file)

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

            page_count = file.get_page_count()
            if args.pad_to:
                if args.pad_to <= page_count:
                    _logger.warn(f"file has {util.pluralize(page_count, 'page')}, "
                                 f"which is <= --pad-to {args.pad_to}")
                else:
                    out.pad_pages(args.pad_to, args.pad_where)
            elif (args.pad_to_odd and page_count % 2 == 0) or (args.pad_to_even and page_count % 2 == 1):
                out.pad_pages(page_count + 1, args.pad_where)

            if args.copy_metadata:
                out.copy_metadata_from_owner()
            if (args.copy_password and file.password) or args.owner_password:
                out.encrypt(args.password, args.owner_password)

        if file.path == out.path:
            _logger.info(f"edited file {repr(filename)} ({util.pluralize(page_count, 'page')})")
        else:
            _logger.info(f"copied {repr(filename)} to {repr(str(out.path))} "
                         '(' + util.pluralize(page_count, 'page') + ')')

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

    try:
        (filename, page_spec, password) = parse_file_specifier(args.file)
    except FileNotFoundError as e:
        _logger.err(e.args[0])
        return False

    fp = Path(filename)
    template = args.output_file_template

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


def explode(args: argparse.Namespace) -> bool:
    _logger.debug(f"explode {args}")

    count: int = args.count
    if count < 1:
        _logger.err("count must be >= 1")
        return False

    try:
        (filename, page_selector, password) = parse_file_specifier(args.file)
    except FileNotFoundError as e:
        _logger.err(e.args[0])
        return False

    template = args.output_file_template

    try:
        file = PdfFile(filename, args.select or page_selector, args.password or password)
        with (file.get_reader()):
            file_count = file.get_page_count() // count
            outfiles: list[PdfFile] = []
            page_limit = file_count * count
            # create files
            for i in range(file_count):
                fp = template.format(dir=str(file.path.parent) + os.sep, name=file.path.stem, ext=file.path.suffix, i=i+1)
                outfiles.append(PdfFile(fp, owner=file))
            # write pages to file
            file_idx = 0
            for i, page in enumerate(file.get_pages()):
                outfiles[file_idx % file_count].get_writer_unsafe().add_page(page)
                if (i+1) % count == 0:
                    file_idx += 1
                if i+1 >= page_limit:
                    break
            # close file writers
            for out in outfiles:
                if args.copy_metadata:
                    out.copy_metadata_from_owner()
                if (args.copy_password and file.password) or args.owner_password:
                    out.encrypt(args.password, args.owner_password)

                out.close_writer()
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


def merge(args: argparse.Namespace) -> bool:
    _logger.debug(f"merge {args}")

    if len(args.file) < 1:
        _logger.err("need more than one input file")
        return False
    elif len(args.file) == 1:
        _logger.warn("only one file provided; this action will only create one file which is more idiomatically "
                     "achieved with the `copy` command")

    try:
        fsps: list[tuple[str, Optional[str], Optional[str]]] = list(map(parse_file_specifier, args.file))
    except FileNotFoundError as e:
        _logger.err(e.args[0])
        return False

    outfile = PdfFile(args.output_file, owner=None)

    with outfile.get_writer() as writer:
        for fsp in fsps:
            file = PdfFile(fsp[0], selector=fsp[1], password=fsp[2] or args.password)
            pages_written = 0
            with file.get_reader():
                for page in file.get_pages():
                    writer.add_page(page)
                    pages_written += 1
            _logger.info(f"wrote {util.pluralize(pages_written, 'page')} from {repr(str(file.path))} to " +
                         repr(str(outfile.path)))

    return True
