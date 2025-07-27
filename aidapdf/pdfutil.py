from aidapdf.log import log_hint, log_cmd
from aidapdf.ioutil import PdfFile
from aidapdf.config import Config
from aidapdf import util


class AidaException(Exception):
    pass


def count_pages(files: list[PdfFile], terse: bool):
    log_cmd("count-pages", locals())

    for file in files:
        reader = file.get_writer()
        if terse:
            print(len(reader.pages))
        else:
            print(str(file.path) + '\t' + str(len(reader.pages)))


def combine_files(files: list[PdfFile], output_file: PdfFile):
    log_cmd("combine", locals())

    if len(files) == 1:
        raise AidaException('only one document (need at least 2)')

    writer = output_file.get_writer()

    for file in files:
        writer.append(file.path)

    writer.write(output_file.path)
    writer.close()


def divide_file(file: PdfFile, count: int, output_file_format: str) -> list[PdfFile]:
    log_cmd("divide", locals())

    file.get_reader()
    out_files = [
        PdfFile(output_file_format.format(
            dir=file.path.parent,
            name=file.path.stem,
            n=i+1
        ))
        for i in range(count)
    ]
    writers = [file.get_writer() for file in out_files]

    i = 0
    for page in file.selected_pages():
        writers[i % count].add_page(page)
        i += 1

    i = 0
    for file in out_files:
        i += 1
        file.write()
    return out_files


def reverse_file(files: list[PdfFile], output_file_format: str) -> list[PdfFile]:
    log_cmd("reverse", locals())

    fns: list[PdfFile] = []
    for file in files:
        output_file = PdfFile(util.format_path(output_file_format, file.path))
        file.get_reader()
        writer = output_file.get_writer()
        for page in file.selected_pages(reverse=True):
            writer.add_page(page)
        fns.append(output_file)
        output_file.write()
    return fns


def double_sided_print(files: list[PdfFile], output_file_format: str):
    log_cmd("double-sided-print", locals())

    for file in files:
        file.get_reader()
        fst = PdfFile.from_str(Config.MULTIPLE_OUTPUT_FILE_TEMPLATE.format(
            dir=file.path.parent,
            name=file.path.stem,
            n=1
        ))
        lst = PdfFile.from_str(Config.MULTIPLE_OUTPUT_FILE_TEMPLATE.format(
            dir=file.path.parent,
            name=file.path.stem,
            n=2
        ))

        i = 0
        even_pages = []
        fst_writer = fst.get_writer()
        for page in file.selected_pages():
            i += 1
            if i % 2 == 0:
                even_pages.append(page)
            else:
                fst_writer.add_page(page)
        fst.write()

        lst_writer = lst.get_writer()
        for page in reversed(even_pages):
            lst_writer.add_page(page)
        if len(even_pages) != len(fst_writer.pages):
            lst_writer.insert_blank_page(index=0)
        lst.write()

        log_hint(f"""to print {file} as a two-sided file:
1. print {fst} first
2. take the printed pages and put them back into the loading tray
3. print {lst}""")


def copy(file: PdfFile, output_file: PdfFile):
    log_cmd("copy", locals())

    file.get_reader()
    writer = output_file.get_writer()
    for p in file.selected_pages():
        writer.add_page(p)
    output_file.write()
