from collections.abc import Iterator, Sequence
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, NewType

import hpikit.cli.dal as cli
from hpikit.datetime import AwareDateTime, aware
from hpikit.json import Json, loads
from hpikit.paths import as_paths
from kloggy import get_logger
from kloggy.progress import progress
from more_itertools import unique_everseen

Url = NewType('Url', str)

Tag = str


logger = get_logger(__name__)


class Bookmark(NamedTuple):
    raw: Json

    @property
    def created(self) -> AwareDateTime:
        dts = self.raw['time']
        # contains Z at the end, so will end up as UTC
        return aware(datetime.fromisoformat(dts))

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
    def __init__(self, sources: Sequence[Path | str]) -> None:
        self.sources = as_paths(sources)

    def raw(self) -> Iterator[Json | list[Json] | Exception]:
        for path in progress(
            # TODO: perhaps reversing this should be configurable?
            # a bit of a problem that if we process in chronological order, we never emit updates for bookmarks
            # note that for pinboard it's hard to guarantee sort order when we emit items anyway
            # because API is flaky and sometimes bookmarks disappear from some exports for no reason
            # (sliced rather than reversed(), which has no length, so the progress bar knows the total)
            self.sources[::-1],
            # however in some cases it may be useful to emit everything with minimal uniquification
            # e.g. if we want some sort of database that actually contains updates for all entities
            logger=logger,
            unit='files',
        ):
            try:
                yield loads(path.read_bytes())
            except Exception as e:
                ex = RuntimeError(f'While processing {path}')
                ex.__cause__ = e
                yield ex

    def _bookmarks_raw(self) -> Iterator[Json | Exception]:
        for j in self.raw():
            if isinstance(j, Exception):
                yield j
            else:
                if isinstance(j, list):
                    # old format
                    yield from j
                else:
                    yield from j['posts']

    def bookmarks(self) -> Iterator[Bookmark | Exception]:
        # first step -- deduplicate raw jsons
        # this is just a speedup: the second step keeps only the first (i.e. newest) version per (created, url) anyway,
        #   and equal time/href strings always give equal (created, url), so the result is the same
        # unlike keying on the whole record, this already drops older versions of edited bookmarks (e.g. changed tags)
        it_jsons: Iterator[Json | Exception] = unique_everseen(
            self._bookmarks_raw(),
            # without it, dict isn't hashable, so unique_everseen takes quadratic time
            key=lambda j: j if isinstance(j, Exception) else (j['time'], j['href']),
        )
        # fmt: off
        it_bookmarks: Iterator[Bookmark | Exception] = (
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
    cli.main(DAL=DAL, demo=demo)
