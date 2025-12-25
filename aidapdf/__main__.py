import argparse

from aidapdf import commands


def main():
    parser = argparse.ArgumentParser("aidapdf")
    sub = parser.add_subparsers()

    parsepagespec_command = sub.add_parser('parsepagespec')
    parsepagespec_command.add_argument('spec', nargs="?")
    parsepagespec_command.add_argument('-b', '--bake-file', nargs='?')
    parsepagespec_command.set_defaults(func=commands.parse_page_spec)

    pagecount_command = sub.add_parser("pagecount")
    pagecount_command.add_argument("files", nargs="+")
    pagecount_command.add_argument("-t", "--terse", action="store_true")
    pagecount_command.set_defaults(func=commands.page_count)

    copy_command = sub.add_parser("copy", aliases=["c"])
    copy_command.add_argument("file")
    copy_command.add_argument("pages", nargs="?")
    copy_command.add_argument("-o", "--output-file")
    copy_command.add_argument("-p", "--owner-password", nargs="?")
    copy_command.add_argument('--copy-metadata', action=argparse.BooleanOptionalAction)
    copy_command.set_defaults(func=commands.copy)

    split_command = sub.add_parser("split", aliases=["s"])
    split_command.add_argument("file")
    split_command.add_argument("count", type=int)
    split_command.add_argument("-o", "--output-file-template", nargs="?")
    split_command.add_argument("-p", "--owner-password", nargs="?")
    split_command.add_argument('--copy-metadata', action=argparse.BooleanOptionalAction)
    split_command.set_defaults(func=commands.split)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
