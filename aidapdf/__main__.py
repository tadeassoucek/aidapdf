import argparse
import sys
from argparse import BooleanOptionalAction

from aidapdf import commands
from aidapdf.config import Config
from aidapdf.log import Logger


_logger = Logger(__name__)


def main():
    parser = argparse.ArgumentParser("aidapdf")

    parser.add_argument('--color', default=True, action=BooleanOptionalAction,
                        help="enable color output")
    parser.add_argument('-r', '--raw-filenames', default=False, action=BooleanOptionalAction,
                        help="treat filenames as raw, not as file specifiers")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-v', '--verbose', dest="verbose_level", action='store_const', const=3,
                        help="print debug information")
    verbosity_group.add_argument('-q', '--quiet', dest="verbose_level", action='store_const', const=1,
                        help="suppress logging messages except for warnings and errors")
    verbosity_group.add_argument('-Q', '--very-quiet', dest="verbose_level", action='store_const', const=0,
                                 help="suppress logging messages except for errors")

    sub = parser.add_subparsers()

    # Debug commands
    debug_command = sub.add_parser("debug", aliases=['dbg'], help="debug command")
    debug_sub = debug_command.add_subparsers()

    testlog_command = debug_sub.add_parser("log", help="test the log command")
    testlog_command.set_defaults(func=commands.debug_testlog)

    parse_selector_command = debug_sub.add_parser("selector", help="parse and show page selector")
    parse_selector_command.add_argument("select", nargs='?', help="page selector. if none is specified, "
                                                         "enters interactive mode")
    parse_selector_command.add_argument("-f", "--file", nargs='?', help="file to use as a bake file")
    parse_selector_command.set_defaults(func=commands.debug_parse_selector)

    parse_specifier_command = debug_sub.add_parser("specifier", aliases=['spec'],
                                                   help="parse and show file specifier")
    parse_specifier_command.add_argument("spec", nargs='?', help="file specifier")
    parse_specifier_command.set_defaults(func=commands.debug_parse_specifier)

    version_command = sub.add_parser('version', aliases=['v'], help="print version information and exit")
    version_command.add_argument('-t', '--terse', action='store_true',
                                 help="show only the version number without the program name")
    version_command.set_defaults(func=commands.version)

    info_command = sub.add_parser("info", aliases=['i'], help="print info about the PDF file")
    info_command.add_argument("file", help="the PDF file")
    group = info_command.add_mutually_exclusive_group(required=False)
    group.add_argument("-a", "--all", dest="targets", action="store_const",
                       const=["pages", "metadata"], default=["pages", "metadata"],
                       help="show all info")
    group.add_argument("-p", "--pages", dest="targets", action="store_const", const=["pages"],
                       help="print the number of pages")
    group.add_argument("-m", "--metadata", dest="targets", action="store_const", const=["metadata"],
                       help="print the metadata")
    info_command.set_defaults(func=commands.info)

    extract_command = sub.add_parser('extract', aliases=['x'],
                                     help="extract text, attachments and graphics from PDF file")
    extract_command.add_argument('file', help='the PDF file')
    extract_command.add_argument('-t', '--text-file', nargs="?", default='-',
                                 help="text file to write the extracted text to")
    extract_command.add_argument('-i', '--image-file-template', default="{dir}{name}-{p:03}-{i:03}-{img}",
                                 nargs='?', help="template for the extracted image files")
    extract_command.add_argument('-m', '--extract-mode', nargs='?', default='plain',
                                 choices=['plain', 'layout'],
                                 help="extraction mode. options are 'plain' (strip formatting) and 'layout' (preserve "
                                      "the original layout to the best of your ability)")
    extract_command.set_defaults(func=commands.extract)

    copy_command = sub.add_parser("copy", aliases=["c"],
                                  help="creates a copy of the PDF file with the requested modifications")
    copy_command.add_argument("file", help="the original PDF file")
    copy_command.add_argument("-o", "--output-file", help="the new PDF file. as of now, this is "
                                                          "required, as pypdf can't write to stdout")
    copy_command.add_argument("-s", "--select", nargs="?", help="selected pages")
    copy_command.add_argument('--copy-password', default=True, action=argparse.BooleanOptionalAction,
                              help="if the input file is protected by a password, protect the new file with the same "
                                   "password. if set and there is a password to copy, an owner password must be provided"
                                   "with the --owner-password option. on by default")
    copy_command.add_argument("-p", "--password", nargs="?",
                              help="password to protect the new file with. supercedes --copy-password option")
    copy_command.add_argument("-P", "--owner-password", nargs="?",
                              help="owner password to protect the new file with")
    copy_command.add_argument('--copy-metadata', default=True, action=argparse.BooleanOptionalAction,
                              help="copy metadata from the original file to the new one. on by default")
    copy_command.add_argument('--reverse', action="store_true", help="reverse the order of the pages")
    copy_command.add_argument('-b', '--add-blank', nargs='?', help="blank pages to add")
    copy_command.add_argument('-w', '--preview', action="store_true",
                              help="open the created file in the default program")
    copy_command.set_defaults(func=commands.copy)

    split_command = sub.add_parser("split", aliases=["s"])
    split_command.add_argument("file")
    split_command.add_argument('select', nargs="+", help="selected pages")
    split_command.add_argument("-o", "--output-file-template", nargs="?",
                               default="{dir}{name}-{i:03}.pdf")
    split_command.add_argument("-p", "--password", nargs="?")
    split_command.add_argument("-P", "--owner-password", nargs="?")
    split_command.add_argument('--copy-metadata', action=argparse.BooleanOptionalAction, default=True)
    split_command.add_argument('--copy-password', action=argparse.BooleanOptionalAction, default=True)
    split_command.set_defaults(func=commands.split)

    explode_command = sub.add_parser("explode", help="divides the PDF file into files of N pages each")
    explode_command.add_argument("file")
    explode_command.add_argument('count', type=int, default=1, nargs="?", help="number of pages per file")
    explode_command.add_argument('-s', '--select', nargs="?", help="page selector")
    explode_command.add_argument("-o", "--output-file-template", nargs="?",
                                 default="{dir}{name}-{i:03}.pdf")
    explode_command.add_argument("-p", "--password", nargs="?")
    explode_command.add_argument("-P", "--owner-password", nargs="?")
    explode_command.add_argument('--copy-metadata', action=argparse.BooleanOptionalAction, default=True)
    explode_command.add_argument('--copy-password', action=argparse.BooleanOptionalAction, default=True)
    explode_command.set_defaults(func=commands.explode)

    merge_command = sub.add_parser("merge", aliases=["m"], help="meges multiple PDF files")
    merge_command.add_argument("file", nargs="+")
    merge_command.add_argument("-o", "--output-file")
    merge_command.add_argument("-p", "--password", nargs="?")
    merge_command.add_argument("-P", "--owner-password", nargs="?")
    merge_command.set_defaults(func=commands.merge)

    args = parser.parse_args()

    Config.COLOR = args.color
    Config.RAW_FILENAMES = args.raw_filenames
    if "verbose_level" in args and args.verbose_level is not None:
        Config.VERBOSITY_LEVEL = args.verbose_level

    if "func" in args:
        if not args.func(args):
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
