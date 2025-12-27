import argparse

from aidapdf import commands
from aidapdf.log import Logger


def main():
    parser = argparse.ArgumentParser("aidapdf")

    parser.add_argument('-v', '--verbose', dest="verbose_level", action='store_const', const=3)
    parser.add_argument('-q', '--quiet', dest="verbose_level", action='store_const', const=1)

    sub = parser.add_subparsers()

    version_command = sub.add_parser('version', aliases=['v'])
    version_command.add_argument('-t', '--terse', action='store_true')
    version_command.set_defaults(func=commands.version)

    info_command = sub.add_parser("info", aliases=['i'])
    info_command.add_argument("file")
    group = info_command.add_mutually_exclusive_group(required=False)
    group.add_argument("-a", "--all", dest="targets", action="store_const",
                       const=["pages", "metadata"], default=["pages", "metadata"])
    group.add_argument("-p", "--pages", dest="targets", action="store_const", const=["pages"])
    group.add_argument("-m", "--metadata", dest="targets", action="store_const", const=["metadata"])
    info_command.set_defaults(func=commands.info)

    parsepagespec_command = sub.add_parser('parsepagespec')
    parsepagespec_command.add_argument('spec', nargs="?")
    parsepagespec_command.add_argument('-f', '--file', nargs='?')
    parsepagespec_command.set_defaults(func=commands.parse_page_spec)

    extract_command = sub.add_parser('extract', aliases=['x'])
    extract_command.add_argument('file')
    extract_command.add_argument('-o', '--output-file')
    extract_command.add_argument('-m', '--extract-mode', nargs='?', default='plain',
                                 choices=['plain', 'layout'])
    extract_command.set_defaults(func=commands.extract)

    copy_command = sub.add_parser("copy", aliases=["c"])
    copy_command.add_argument("file")
    copy_command.add_argument("pages", nargs="?")
    copy_command.add_argument("-o", "--output-file")
    copy_command.add_argument("-p", "--password", nargs="?")
    copy_command.add_argument("-P", "--owner-password", nargs="?")
    copy_command.add_argument('--copy-metadata', default=True, action=argparse.BooleanOptionalAction)
    copy_command.add_argument('--reverse', action="store_true")
    copy_command.add_argument('-b', '--add-blank', nargs='?')
    copy_command.add_argument('-w', '--preview', action="store_true")
    copy_command.set_defaults(func=commands.copy)

    split_command = sub.add_parser("split", aliases=["s"])
    split_command.add_argument("file")
    split_command.add_argument("count", type=int)
    split_command.add_argument("-o", "--output-file-template", nargs="?")
    split_command.add_argument("-P", "--owner-password", nargs="?")
    split_command.add_argument('--copy-metadata', action=argparse.BooleanOptionalAction)
    split_command.set_defaults(func=commands.split)

    args = parser.parse_args()
    if args.verbose_level:
        Logger.LOG_LEVEL = args.verbose_level
    args.func(args)

if __name__ == '__main__':
    main()
