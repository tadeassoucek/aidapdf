import argparse

from aidapdf.file import PdfFile
from aidapdf.pagespecparser import PageSpec


def pagecount_fn(args: argparse.Namespace):
    print(args.terse, args.files)


def parsepagespec_fn(args: argparse.Namespace):
    pagespec = PageSpec.parse(args.spec)
    print(pagespec)
    print(pagespec.bake(PdfFile(20)))


def main():
    parser = argparse.ArgumentParser("aidapdf")
    commands = parser.add_subparsers()

    parsepagespec_command = commands.add_parser('parsepagespec')
    parsepagespec_command.add_argument('spec')
    parsepagespec_command.set_defaults(func=parsepagespec_fn)

    pagecount_command = commands.add_parser("pagecount")
    pagecount_command.add_argument("files", nargs="+")
    pagecount_command.add_argument("-t", "--terse", action="store_true")
    pagecount_command.set_defaults(func=pagecount_fn)

    args = parser.parse_args()
    print(args)
    args.func(args)

if __name__ == '__main__':
    main()
