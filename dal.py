#!/usr/bin/env python3
from typing import NamedTuple, Optional, Sequence, Iterator, Set, Iterable
from pathlib import Path
import json
from datetime import datetime
import logging

import pytz

if __name__ == '__main__':
    # see dal_helper.setup for the explanation
    import dal_helper # type: ignore[import]
    dal_helper.fix_imports(globals())

from . import dal_helper  # type: ignore[no-redef]
from .dal_helper import PathIsh, Json


Url = str
Tag = str

# TODO reuse logger from helper
def get_logger():
    return logging.getLogger('pinbexport')


class Bookmark(NamedTuple):
    raw: Json

    @property
    def created(self) -> datetime:
        dts = self.raw['time']
        return pytz.utc.localize(datetime.strptime(dts, '%Y-%m-%dT%H:%M:%SZ'))

    @property
    def url(self) -> Url:
        return self.raw['href']

    @property
    def title(self) -> str:
        titles = self.raw['description']
        if titles == False:
            titles = '' # *shrug* happened onc
        return titles

    @property
    def description(self) -> str:
        return self.raw['extended']

    @property
    def tags(self) -> Sequence[Tag]:
        return tuple(self.raw['tags'].split())



class DAL:
    def __init__(self, sources: Sequence[PathIsh]) -> None:
        self.sources = list(map(Path, sources))

    def raw(self) -> Json:
        # TODO merge them carefully
        last = max(self.sources)
        return json.loads(last.read_text())

    def _bookmarks_raw(self) -> Iterable[Json]:
        data = self.raw()
        if isinstance(data, list):
            return data # old format
        else:
            return data['posts']

    def bookmarks(self) -> Iterator[Bookmark]:
        def key(b: Bookmark):
            return (b.created, b.url)
        logger = get_logger()
        emitted: Set = set()
        for j in self._bookmarks_raw():
            bm = Bookmark(j)
            # TODO could also detect that by hash?
            bk = key(bm)
            if bk in emitted:
                logger.debug('skipping duplicate item %s', bm)
                continue
            emitted.add(bk)
            yield bm


def demo(dal: DAL) -> None:
    bookmarks = list(dal.bookmarks())
    print(f"Parsed {len(bookmarks)} bookmarks")


if __name__ == '__main__':
    logger = get_logger()
    dal_helper.main(DAL=DAL, demo=demo)
