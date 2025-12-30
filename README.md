# AidaPdf

A CLI PDF file editor. Basically just an interface for the [`pypdf`](https://pypi.org/project/pypdf/) library, except it's (hopefully) a little more
powerful than the other ones.

```
usage: aidapdf [-h] [--color | --no-color] [-r | --raw-filenames | --no-raw-filenames] [-v | -q | -Q]
               {debug,dbg,version,v,info,i,extract,x,edit,e,split,s,explode,merge,m} ...

positional arguments:
  {debug,dbg,version,v,info,i,extract,x,edit,e,split,s,explode,merge,m}
    debug (dbg)         debug command
    version (v)         print version information and exit
    info (i)            print info about the PDF file
    extract (x)         extract text, attachments and graphics from PDF file
    edit (e)            edit the PDF file
    explode             divides the PDF file into files of N pages each
    merge (m)           meges multiple PDF files

options:
  -h, --help            show this help message and exit
  --color, --no-color   enable color output
  -r, --raw-filenames, --no-raw-filenames
                        treat filenames as raw, not as file specifiers
  -v, --verbose         print debug information
  -q, --quiet           suppress logging messages except for warnings and errors
  -Q, --very-quiet      suppress logging messages except for errors
```

## Commands

### `edit`

```
usage: aidapdf edit [-h] [-o [OUTPUT_FILE]] [-s [SELECT]] [--copy-password | --no-copy-password] [-p [PASSWORD]] [-P [OWNER_PASSWORD]] [--copy-metadata | --no-copy-metadata]
                    [--reverse] [-b [ADD_BLANK]] [--pad-to PAD_TO | --pad-to-even | --pad-to-odd] [--pad-where {start,end}] [-w]
                    file
```

The `edit` command is the main way to interface with the program. It takes an input file (`file`) and applies the edits
specified by the other arguments.

| Option                | Value            | Help                                                              |
|-----------------------|------------------|-------------------------------------------------------------------|
| `-o`, `--output-file` | file to write to | write the edited file to this path.                               |
| `-s`, `--select`      | page selector    | pages to select from the input file. the other pages are ignored. |
