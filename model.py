#!/usr/bin/env python3
from typing import NamedTuple, Optional, Sequence, Iterator, Union, Dict, List, Any, Set
from pathlib import Path
import json
from datetime import datetime
import logging

import pytz

PathIsh = Union[str, Path]
Json = Dict[str, Any]

Url = str
Tag = str


def get_logger():
    return logging.getLogger('pinbexport')


class Bookmark(NamedTuple):
    created: datetime
    url: Url
    title: str
    description: str
    tags: Sequence[Tag]
    error: Optional[Exception]=None

    # @classmethod
    # def make_error(cls, exc: Exception) -> 'Bookmark':
    #     return cls(
    #         error=exc,
    #     )

    @classmethod
    def try_parse(cls, js):
        try:
            # TODO hash?
            urls   = js['href']
            dts    = js['time']
            titles = js['description']
            descs  = js['extended']
            tags   = tuple(js['tags'].split())
            # TODO isoformat?
            created = pytz.utc.localize(datetime.strptime(dts, '%Y-%m-%dT%H:%M:%SZ'))

            if titles == False:
                titles = '' # *shrug* happened once
        except Exception as e:
            raise e
            # TODO imlement error handling later..
            # yield echain(Error(raw=js), e)
        yield cls(
            created=created,
            url=urls,
            title=titles,
            description=descs,
            tags=tags,
        )


class Model:
    def __init__(self, sources: Sequence[PathIsh]) -> None:
        # TODO FIXME use new style exports
        self.sources = list(map(Path, sources))
        # TODO defensive = True?

    def raw(self) -> Json:
        last = max(self.sources)
        return json.loads(last.read_text())

    def _bookmarks_raw(self) -> List[Json]:
        data = self.raw()
        if isinstance(data, list):
            return data # old format
        else:
            return data['posts']

    def iter_bookmars(self) -> Iterator[Bookmark]:
        logger = get_logger()
        emitted = set() # type: Set[Bookmark]
        for a in self._bookmarks_raw():
            for b in Bookmark.try_parse(a):
                if b in emitted:
                    # TODO could also detect that by hash?
                    logger.info('skipping duplicate item %s', b)
                    continue
                emitted.add(b)
                yield b

    def bookmarks(self) -> Sequence[Bookmark]:
        return list(self.iter_bookmars())


class Error(Exception):
    def __init__(self, raw: Dict) -> None:
        super().__init__(f'error while processing {raw}')
        self.raw = raw

    @property
    def uid(self) -> str:
        return self.raw['hash']


# def get_entries() -> List[Result]:
#     return list(sort_res_by(iter_entries(), key=lambda e: (e.created, e.url)))
# 
# 
# def get_ok_entries() -> List[Bookmark]:
#     logger = get_logger()
#     results = []
#     for x in get_entries():
#         try:
#             res = unwrap(x)
#         except Exception as e:
#             logger.exception(e)
#         else:
#             results.append(res)
#     return results

# TODO motivation for having historic backups: can keep track of changes (if you're into that sort of stats)
# TODO why data backups are hard: defensive parsing so it wouldn't require your attention immediately?
# TODO error attribute?


# alternatives:
# fill fields with dummy ids/etc/ and pass eror=Exception
# error: Optional[]
# might still break some invariants (e.g TODO friends??)
# benefit is that you don't have to do anything special and users code wouldn't fail
# downside is that it's easy to miss errors?

# returning Union[Result, Exception]
# downside: no standard method of processing such things in python
# if user forgets to handle Exception, they would end up with more exceptions which is arguably more annoying?
# on the other hand, if you got exception and
# the only minor annoyance is mypy?
# annoying to force user to han
# upside is that static checkers assist you with that (e.g. isinstance(x, Exception))
# TODO could also export Exception/Error type?

# best of two worlds?
# 'strict' -- throw all errors? requires assistance from TODO; error=None
# 'defensive' -- sets up error=attribute?
# 'return' -- TODO return exceptions?

# TODO defensive
