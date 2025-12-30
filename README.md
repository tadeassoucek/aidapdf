# AidaPdf

A CLI PDF file editor. Basically just an interface for the [`pypdf`](https://pypi.org/project/pypdf/) library, except it's (hopefully) a little more
powerful than the other ones.

```commandline
$ aida copy examples/sample.pdf --no-copy-password -s "1,even" --reverse -o examples/output.pdf
ERR!:file:PdfFile('examples/sample.pdf')  incorrect password
Password to read file 'examples/sample.pdf': 
INFO:file:PdfFile('examples/sample.pdf')  decrypted successfully
INFO:commands  copied 'examples/sample.pdf' to 'examples/output.pdf'
```
