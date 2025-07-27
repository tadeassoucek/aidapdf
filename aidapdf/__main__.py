import aidapdf.page_range_parser as prp
import aidapdf.pdfutil as pdf
import argparse

from aidapdf.config import Config
from aidapdf.ioutil import PdfFile
from aidapdf.log import log_err
from aidapdf.pdfutil import AidaException


def cmd_fn(fn):
    def internal(args: argparse.Namespace):
        if args.overwrite:
            Config.FORCE_OVERWRITE = args.overwrite
        try:
            fn(args)
        except AidaException as e:
            log_err(', '.join(map(str, e.args)))
    return internal


@cmd_fn
def combine_files(args: argparse.Namespace):
    pdf.combine_files(PdfFile.from_list(args.files), PdfFile.from_str(args.output_file))


@cmd_fn
def copy_fn(args: argparse.Namespace):
    pdf.copy(PdfFile.from_str(args.file), PdfFile.from_str(args.output_file))


@cmd_fn
def page_count_fn(args: argparse.Namespace):
    pdf.count_pages(PdfFile.from_list(args.files), args.terse)


@cmd_fn
def divide_fn(args: argparse.Namespace):
    pdf.divide_file(PdfFile.from_str(args.input_file), args.count, args.output_file_format)


@cmd_fn
def reverse_cmd(args: argparse.Namespace):
    pdf.reverse_file(PdfFile.from_list(args.files), args.output_file_format)


@cmd_fn
def double_sided_print(args: argparse.Namespace):
    pdf.double_sided_print(PdfFile.from_list(args.files), args.output_file_format)


@cmd_fn
def parse_range(args: argparse.Namespace):
    def eval_ranges(s: str):
        toks = prp.parse_ranges(s)
        print(toks)
        print(prp.bake_range(toks, 100))

    if args.range and len(args.range):
        for rng in args.range:
            eval_ranges(rng)
    else:
        while True:
            eval_ranges(input("> "))


def main():
    parser = argparse.ArgumentParser(
        prog='aidapdf',
        description='PDF tool'
    )

    parser.add_argument('-f', '--overwrite', action='store_true')

    subparsers = parser.add_subparsers()

    # Combine command
    combine_parser = subparsers.add_parser('combine', help='combine PDFs')
    combine_parser.add_argument('files', nargs='+')
    combine_parser.add_argument('-o', '--output-file', nargs='?', type=str)
    combine_parser.set_defaults(func=combine_files)

    copy_parser = subparsers.add_parser('copy', aliases=['c'], help='copy PDF')
    copy_parser.add_argument('file')
    copy_parser.add_argument('-o', '--output-file', nargs='?', type=str)
    copy_parser.set_defaults(func=copy_fn)

    page_count_parser = subparsers.add_parser('page-count', aliases=['pages', 'count', 'count-pages'],
                                               help='count pages in PDFs')
    page_count_parser.add_argument('files', nargs='+', type=str)
    page_count_parser.add_argument('-t', '--terse', action='store_true', default=False,
                                    help='terse output -- the page count for each file is printed on its own line with no extra information')
    page_count_parser.set_defaults(func=page_count_fn)

    divide_parser = subparsers.add_parser('divide', aliases=['d'], help='divide PDF into N PDFs')
    divide_parser.add_argument('input_file', type=str)
    divide_parser.add_argument('-c', '--count', default=2, type=int)
    divide_parser.add_argument('-o', '--output-file-format', default=Config.MULTIPLE_OUTPUT_FILE_TEMPLATE)
    divide_parser.set_defaults(func=divide_fn)

    reverse_parser = subparsers.add_parser('reverse', aliases=['r'], help='reverse PDF pages')
    reverse_parser.add_argument('files', nargs='+', type=str)
    reverse_parser.add_argument('-o', '--output-file-format', default=Config.REVERSE_OUTPUT_FILE_TEMPLATE)
    reverse_parser.set_defaults(func=reverse_cmd)

    double_sided_print_parser = subparsers.add_parser('double-sided-print', aliases=['2side'])
    double_sided_print_parser.add_argument('files', nargs='+', type=str)
    double_sided_print_parser.add_argument('-o', '--output-file-format',
                                           default=Config.MULTIPLE_OUTPUT_FILE_TEMPLATE)
    double_sided_print_parser.set_defaults(func=double_sided_print)

    parse_range_parser = subparsers.add_parser('parse')
    parse_range_parser.add_argument('range', nargs='*', type=str)
    parse_range_parser.set_defaults(func=parse_range)

    cli_args = parser.parse_args()
    cli_args.func(cli_args)

if __name__ == '__main__':
    main()
