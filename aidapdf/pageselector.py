import string
import abc
from typing import Iterator, TYPE_CHECKING

from aidapdf.log import Logger


_logger = Logger(__name__)

if TYPE_CHECKING:
    from aidapdf.file import PdfFile


class PageSelectorParserException(Exception):
    pass


class PageSelectorToken(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def bake(self, file: 'PdfFile') -> list[int]:
        raise NotImplementedError()


def _ntos(n: int) -> str:
    return str(n).replace('-', '^')


class PageSelectorNumberToken(PageSelectorToken):
    def __init__(self, number: int):
        self.number = number

    def bake(self, file: 'PdfFile') -> list[int]:
        n = self.number - 1 if self.number >= 0 else file.get_page_count() + self.number
        return [n]

    def __str__(self):
        return _ntos(self.number)


class PageSelectorCondition:
    IS_EVEN = 0
    IS_ODD = 1

    def __init__(self, call: IS_EVEN | IS_ODD):
        self.call = call

    def __call__(self, *args, **kwargs) -> bool:
        x = args[0]
        assert type(x) is int
        x += 1
        if self.call == self.IS_EVEN:
            return x % 2 == 0
        elif self.call == self.IS_ODD:
            return x % 2 == 1
        else:
            raise NotImplementedError(f"{self.call} not implemented")

    def __repr__(self) -> str:
        return (
                '{' +
                {PageSelectorCondition.IS_ODD: "odd", PageSelectorCondition.IS_EVEN: "even"}[self.call] +
                '}'
        )


class PageSelectorRangeToken(PageSelectorToken):
    ALL: 'PageSelectorRangeToken'

    def __init__(self, start: int, end: int = -1):
        self.start = start
        self.end = end
        self.condition: PageSelectorCondition | None = None

    def bake(self, file: 'PdfFile'):
        start = self.start - 1 if self.start >= 0 else file.get_page_count() + self.start
        end = self.end - 1 if self.end >= 0 else file.get_page_count() + self.end
        if self.condition:
            if self.condition.call == PageSelectorCondition.IS_ODD:
                if (start+1) % 2 == 0: start += 1
                return list(range(start, end+1, 2))
            elif self.condition.call == PageSelectorCondition.IS_EVEN:
                if (start+1) % 2 == 1: start += 1
                return list(range(start, end+1, 2))
            else:
                return list(filter(self.condition.__call__, range(start, end+1)))
        else:
            return list(range(start, end+1))

    def __str__(self):
        if self.start == 1 and self.end == -1:
            rng = "*"
        else:
            rng = _ntos(self.start) + "-" + _ntos(self.end)

        return rng + (repr(self.condition) if self.condition else '')


PageSelectorRangeToken.ALL = PageSelectorRangeToken(1)


class PageSelector:
    ALL: 'PageSelector'

    @staticmethod
    def parse(text: str) -> 'PageSelector':
        assert type(text) is str

        toks = _lex(text)
        toktype = None
        res: list[PageSelectorToken] = []
        parsing_condition = False
        condition: PageSelectorCondition | None = None

        for tok in toks:
            assert type(tok) is str or type(tok) is int

            if parsing_condition:
                if type(tok) is str:
                    if tok == '}':
                        parsing_condition = False
                        last = res[-1]
                        if isinstance(last, PageSelectorRangeToken):
                            last.condition = condition
                        else:
                            raise PageSelectorParserException(f"invalid token {repr(tok)}")
                    elif tok == 'even':
                        condition = PageSelectorCondition(PageSelectorCondition.IS_EVEN)
                    elif tok == 'odd':
                        condition = PageSelectorCondition(PageSelectorCondition.IS_ODD)
                    else:
                        raise PageSelectorParserException(f"invalid or unspecified condition expression: {repr(tok)}")
                else:
                    raise PageSelectorParserException(f"can't have numbers in condition expression: {repr(tok)}")
            else:
                if type(tok) is str:
                    if tok == ',':
                        toktype = None
                    elif tok == '-':
                        last = res[-1]
                        if isinstance(last, PageSelectorNumberToken):
                            toktype = PageSelectorRangeToken
                            res[-1] = PageSelectorRangeToken(last.number)
                        else:
                            raise PageSelectorParserException(f"invalid token {repr(tok)}")
                    elif tok == '*':
                        if toktype is None:
                            res.append(PageSelectorRangeToken.ALL)
                            toktype = PageSelectorRangeToken
                        else:
                            raise PageSelectorParserException(f"invalid token {repr(tok)}")
                    elif tok == '{':
                        if toktype is PageSelectorRangeToken and not parsing_condition:
                            parsing_condition = True
                        else:
                            raise PageSelectorParserException(f"invalid token {repr(tok)}; must follow condition and can't nest")
                    elif tok in ['even', 'odd']:
                        if toktype is None:
                            rng = PageSelectorRangeToken(1)
                            if tok == 'even':
                                rng.condition = PageSelectorCondition(PageSelectorCondition.IS_EVEN)
                            else:
                                rng.condition = PageSelectorCondition(PageSelectorCondition.IS_ODD)
                            res.append(rng)
                        else:
                            raise PageSelectorParserException(f"invalid token {repr(tok)}")
                    else:
                        raise PageSelectorParserException(f"invalid token {repr(tok)}")
                elif type(tok) is int:
                    if toktype is None:
                        res.append(PageSelectorNumberToken(tok))
                    elif toktype is PageSelectorRangeToken:
                        rng = res[-1]
                        assert isinstance(rng, PageSelectorRangeToken)
                        rng.end = tok
                    else:
                        raise PageSelectorParserException(f"invalid token {repr(tok)}")

        if len(res) == 0:
            res = [PageSelectorRangeToken.ALL]

        ret = PageSelector(res)
        _logger.debug(f"parsed {repr(text)} {toks} as {ret}")
        return ret

    def __init__(self, tokens: list[PageSelectorToken]):
        self.tokens = tokens

    def bake(self, file: 'PdfFile') -> Iterator[int]:
        baked = map(lambda t: t.bake(file), self.tokens)
        for xs in baked:
            for x in xs:
                yield x

    def __repr__(self) -> str:
        return "PageSpec(" + ", ".join(map(str, self.tokens)) + ")"


PageSelector.ALL = PageSelector([PageSelectorRangeToken.ALL])

READING_ANY = 0
READING_NUM = 1
READING_ID = 2

def _lex(text: str) -> list[str | int]:
    reading = READING_ANY
    tok = ""
    toks: list[str | int] = []

    def _push(t: str):
        nonlocal reading
        if t:
            if reading == READING_NUM:
                t = int(t)
            toks.append(t)
        reading = READING_ANY

    def push_and_clear(*ts):
        nonlocal reading, tok
        if not ts: raise Exception("no tokens supplied")
        for t in ts:
            _push(t)
        tok = ""

    parenthesis_depth = 0

    i = 0
    for c in text:
        if c == ',':
            push_and_clear(tok, ',')
        elif c in string.digits:
            reading = READING_NUM
            tok += c
        elif c == '^':
            reading = READING_NUM
            tok += '-'
        elif c == '-':
            if reading in [READING_NUM, READING_ANY]:
                push_and_clear(tok, '-')
                reading = READING_NUM
            else:
                raise PageSelectorParserException(f"invalid char {repr(c)} # {i}")
        elif c == '*':
            if reading == READING_ANY:
                push_and_clear('*')
            else:
                raise PageSelectorParserException(f"invalid char {repr(c)} # {i}")
        elif c == '{':
            push_and_clear(tok, '{')
            parenthesis_depth += 1
        elif c == '}':
            push_and_clear(tok, '}')
            if parenthesis_depth <= 0:
                raise PageSelectorParserException(f"invalid char {repr(c)} # {i} (no parenthesis to close)")
            parenthesis_depth -= 1
        elif c in string.ascii_letters:
            if reading == READING_ANY or reading == READING_ID:
                reading = READING_ID
                tok += c
            else:
                raise PageSelectorParserException(f"invalid char {repr(c)} # {i}")
        elif c in string.whitespace:
            push_and_clear(tok)
        else:
            raise PageSelectorParserException(f"invalid char {repr(c)} # {i}")

        i += 1

    if parenthesis_depth > 0:
        raise PageSelectorParserException(str(parenthesis_depth) + " unclosed parenthes" + ("is" if parenthesis_depth == 1 else "es"))

    if tok:
        push_and_clear(tok)

    return toks
