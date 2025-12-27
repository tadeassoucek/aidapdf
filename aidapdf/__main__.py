import argparse

from aidapdf import commands
from aidapdf.log import Logger


_logger = Logger(__name__)


def main():
    parser = argparse.ArgumentParser("aidapdf")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-v', '--verbose', dest="verbose_level", action='store_const', const=3,
                        help="print debug information")
    verbosity_group.add_argument('-q', '--quiet', dest="verbose_level", action='store_const', const=1,
                        help="suppress logging messages except for warnings and errors")
    verbosity_group.add_argument('-Q', '--very-quiet', dest="verbose_level", action='store_const', const=0,
                                 help="suppress logging messages except for errors")

    sub = parser.add_subparsers()

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
    extract_command.add_argument('-o', '--output-file', help="text file to write the extracted text to")
    extract_command.add_argument('-m', '--extract-mode', nargs='?', default='plain',
                                 choices=['plain', 'layout'],
                                 help="extraction mode. options are 'plain' (strip formatting) and 'layout' (maintain "
                                      "the original layout to the best of your ability)")
    extract_command.set_defaults(func=commands.extract)

    copy_command = sub.add_parser("copy", aliases=["c"],
                                  help="creates a copy of the PDF file with the requested modifications")
    copy_command.add_argument("file", help="the original PDF file")
    copy_command.add_argument("-o", "--output-file", help="the new PDF file. as of now, this is "
                                                          "required, as pypdf can't write to stdout")
    copy_command.add_argument("-s", "--select", nargs="?", help="selected pages")
    copy_command.add_argument("-p", "--password", nargs="?", help="password to protect the new file with")
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
    split_command.add_argument("count", type=int)
    split_command.add_argument("-o", "--output-file-template", nargs="?")
    split_command.add_argument("-P", "--owner-password", nargs="?")
    split_command.add_argument('--copy-metadata', action=argparse.BooleanOptionalAction)
    split_command.set_defaults(func=commands.split)

    args = parser.parse_args()

    if "verbose_level" in args:
        Logger.LOG_LEVEL = args.verbose_level

    if "func" in args:
        args.func(args)

if __name__ == '__main__':
    main()
