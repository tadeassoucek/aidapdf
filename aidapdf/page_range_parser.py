from abc import abstractmethod, ABCMeta

from aidapdf.log import log_action


class PageRangeParserException(Exception):
    pass


def _int_to_page_number(page: int, page_number: int) -> int:
    if page < 0:
        return page_number + page + 1
    return page


class RangeStringToken(metaclass=ABCMeta):
    @abstractmethod
    def to_values(self, page_number: int) -> list[int]:
        pass


class PageNumber(RangeStringToken):
    def __init__(self, page: int):
        self.page = page

    def to_values(self, page_number: int) -> list[int]:
        return [_int_to_page_number(self.page, page_number)]

    def __repr__(self):
        return f'PageNumber({self.page})'


class PageRange(RangeStringToken):
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def to_values(self, page_number: int) -> list[int]:
        start = _int_to_page_number(self.start, page_number)
        end = _int_to_page_number(self.end, page_number)
        step = 1 if start < end else -1
        return list(range(start, end+step, step))

    def __repr__(self):
        return f'PageRange({self.start}, {self.end})'


def _is_num(s: str) -> bool:
    return s.isdigit() or (s[0] == '^' and s[1:].isdigit())

def _parse_num(s: str) -> int:
    if s[0] == '^':
        return -int(s[1:])
    else:
        return int(s)

def parse_ranges(src: str) -> list[RangeStringToken]:
    pages: list[RangeStringToken] = []
    tokens = src.split(',')

    for tok in tokens:
        tok = tok.strip()
        if '-' in tok:
            rng = tok.split('-')
            assert len(rng) == 2
            [a, b] = map(_parse_num, rng)
            pages.append(PageRange(a, b))
        elif _is_num(tok):
            pages.append(PageNumber(_parse_num(tok)))
        else:
            raise PageRangeParserException('invalid token: ' + tok)

    log_action(f"parse_range \"{src}\" -> {pages}")

    return pages

def bake_range(toks: list[RangeStringToken], page_number: int) -> list[int]:
    pages: list[int] = []
    for tok in toks:
        pages += tok.to_values(page_number)
    return pages

def range_to_str(toks: list[RangeStringToken]) -> str:
    n = lambda x: str(x).replace('-', '^')
    res: list[str] = []
    for tok in toks:
        if isinstance(tok, PageNumber):
            res.append(n(tok.page))
        elif isinstance(tok, PageRange):
            res.append(f'{n(tok.start)}-{n(tok.end)}')
        else:
            raise PageRangeParserException('invalid token: ' + repr(tok))
    return ','.join(res)
