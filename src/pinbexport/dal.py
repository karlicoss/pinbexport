#!/usr/bin/env python3
from datetime import datetime
import json
from pathlib import Path
from typing import NamedTuple, Sequence, Iterator, Set, Iterable, NewType

from .exporthelpers import dal_helper
from .exporthelpers.dal_helper import PathIsh, Json, datetime_aware
from .exporthelpers.logging_helper import make_logger


Url = NewType('Url', str)

Tag = str


logger = make_logger(__name__)


class Bookmark(NamedTuple):
    raw: Json

    @property
    def created(self) -> datetime_aware:
        dts = self.raw['time']
        # contains Z at the end, so will end up as UTC
        return datetime.fromisoformat(dts)

    @property
    def url(self) -> Url:
        return self.raw['href']

    @property
    def title(self) -> str:
        titles = self.raw['description']
        if titles is False:
            titles = ''  # *shrug* happened a few times
        return titles

    @property
    def description(self) -> str:
        return self.raw['extended']

    @property
    def tags(self) -> Sequence[Tag]:
        return tuple(self.raw['tags'].split())


class DAL:
    def __init__(self, sources: Sequence[PathIsh]) -> None:
        self.sources = [p if isinstance(p, Path) else Path(p) for p in sources]

    def raw(self) -> Json:
        # TODO merge them carefully
        last = max(self.sources)
        try:
            return json.loads(last.read_text())
        except Exception as e:
            raise RuntimeError(f'While processing {last}') from e

    def _bookmarks_raw(self) -> Iterable[Json]:
        data = self.raw()
        if isinstance(data, list):
            return data  # old format
        else:
            return data['posts']

    def bookmarks(self) -> Iterator[Bookmark]:
        def key(b: Bookmark):
            return (b.created, b.url)

        emitted: Set = set()
        for j in self._bookmarks_raw():
            bm = Bookmark(j)
            # TODO could also detect that by hash?
            bk = key(bm)
            if bk in emitted:
                logger.debug(f'skipping duplicate item {bm}')
                continue
            emitted.add(bk)
            yield bm


def demo(dal: DAL) -> None:
    bookmarks = list(dal.bookmarks())
    print(f"Parsed {len(bookmarks)} bookmarks")


if __name__ == '__main__':
    dal_helper.main(DAL=DAL, demo=demo)
