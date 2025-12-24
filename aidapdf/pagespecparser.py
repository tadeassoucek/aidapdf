"""
1-102![is odd],*[starts with "Appendix" or starts with "Apdx"]
"""

import string
import abc

from aidapdf.file import PdfFile


class PageSpecParserException(Exception):
    pass


class PageSpecToken(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def bake(self, file: PdfFile) -> list[int]:
        raise NotImplementedError()


def _ntos(n: int) -> str:
    return str(n).replace('-', '^')


class PageSpecNumberToken(PageSpecToken):
    def __init__(self, number: int):
        self.number = number

    def bake(self, file: PdfFile) -> list[int]:
        n = self.number if self.number >= 0 else file.page_count + self.number + 1
        return [n]

    def __str__(self):
        return _ntos(self.number)


class PageSpecRangeToken(PageSpecToken):
    def __init__(self, start: int):
        self.start = start
        self.end: int = -1

    def bake(self, file: PdfFile):
        start = self.start if self.start >= 0 else file.page_count + self.start + 1
        end = self.end if self.end >= 0 else file.page_count + self.end + 1
        return list(range(start, end+1))

    def __str__(self):
        return _ntos(self.start) + "-" + _ntos(self.end)


class PageSpec:
    @staticmethod
    def parse(text: str) -> 'PageSpec':
        toks = _lex(text)
        toktype = None
        res: list[PageSpecToken] = []

        i = 0
        for tok in toks:
            if type(tok) is str:
                if tok == ',':
                    toktype = None
                elif tok == '-':
                    last = res[-1]
                    if isinstance(last, PageSpecNumberToken):
                        toktype = PageSpecRangeToken
                        res[-1] = PageSpecRangeToken(last.number)
                    else:
                        raise PageSpecParserException(f"invalid token # {i}")
            elif type(tok) is int:
                if toktype is None:
                    res.append(PageSpecNumberToken(tok))
                elif toktype is PageSpecRangeToken:
                    rng = res[-1]
                    assert isinstance(rng, PageSpecRangeToken)
                    rng.end = tok
                else:
                    raise PageSpecParserException(f"invalid token # {i}")

            i += 1

        return PageSpec(res)

    def __init__(self, tokens: list[PageSpecToken]):
        self.tokens = tokens

    def bake(self, file: PdfFile) -> list[int]:
        baked = map(lambda t: t.bake(file), self.tokens)
        return [x for xs in baked for x in xs]

    def __repr__(self) -> str:
        return "PageSpec(" + ", ".join(map(str, self.tokens)) + ")"


def _lex(text: str) -> list[str | int]:
    toks: list[str | int] = []
    tok: str = ""
    i = 0
    for c in text:
        if c == ',':
            if tok:
                toks.append(int(tok))
                toks.append(',')
                tok = ""
            else:
                raise PageSpecParserException(f"double comma @ {i}")
        elif c == '^':
            if not tok:
                tok = "-"
            else:
                raise PageSpecParserException(f"invalid char ^ @ {i}")
        elif c == '-':
            toks.append(int(tok))
            toks.append('-')
            tok = ""
        elif c in string.digits:
            tok += c

        i += 1

    if tok:
        toks.append(int(tok))

    return toks
