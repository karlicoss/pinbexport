from collections.abc import Iterator, Sequence
from datetime import datetime
from typing import NamedTuple, NewType

import orjson
from more_itertools import unique_everseen

from .exporthelpers import dal_helper
from .exporthelpers.dal_helper import Json, PathIsh, Res, datetime_aware, pathify
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
        self.sources = list(map(pathify, sources))

    def raw(self) -> Iterator[Res[Json]]:
        total = len(self.sources)
        width = len(str(total))
        for idx, path in enumerate(
            # TODO: perhaps reversing this should be configurable?
            # a bit of a problem that if we process in chronological order, we never emit updates for bookmarks
            # note that for pinboard it's hard to guarantee sort order when we emit items anyway
            # because API is flaky and sometimes bookmarks disappear from some exports for no reason
            reversed(self.sources),
            # however in some cases it may be useful to emit everything with minimal uniquification
            # e.g. if we want some sort of database that actually contains updates for all entities
        ):
            logger.info(f'processing [{idx:>{width}}/{total:>{width}}] {path}')
            try:
                yield orjson.loads(path.read_bytes())
            except Exception as e:
                ex = RuntimeError(f'While processing {path}')
                ex.__cause__ = e
                yield ex

    def _bookmarks_raw(self) -> Iterator[Res[Json]]:
        for j in self.raw():
            if isinstance(j, Exception):
                yield j
            else:
                if isinstance(j, list):
                    yield from j  # old format
                else:
                    yield from j['posts']

    def bookmarks(self) -> Iterator[Res[Bookmark]]:
        # first step -- deduplicate raw jsons
        it_jsons: Iterator[Res[Json]] = unique_everseen(
            self._bookmarks_raw(),
            # without it, dict isn't hashable, so unique_everseen takes quadratic time
            key=lambda j: j if isinstance(j, Exception) else orjson.dumps(j),
            # ugh. it's a bit wasteful to parse first and then dump again though?
            # might be much nicer if we can do some sort of partial parsing of the json
        )
        # fmt: off
        it_bookmarks: Iterator[Res[Bookmark]] = (
            j if isinstance(j, Exception) else Bookmark(j)
            for j in it_jsons
        )
        # fmt: on

        # second step -- deduplicate bookmarks with same dt/url
        # sadly pinboard doesn't have unique ids for bookmarks
        it_bookmarks = unique_everseen(
            it_bookmarks,
            key=lambda b: b if isinstance(b, Exception) else (b.created, b.url),
        )
        return it_bookmarks


def demo(dal: DAL) -> None:
    bookmarks = list(dal.bookmarks())
    print(f"Parsed {len(bookmarks)} bookmarks")


if __name__ == '__main__':
    dal_helper.main(DAL=DAL, demo=demo)
