#!/usr/bin/env python3
from typing import NamedTuple, Optional, Sequence, Iterator
from pathlib import Path
import json
from datetime import datetime
import logging

Url = str
Tag = str


def get_logger():
    return logging.getLogger('pinboard')


class Bookmark(NamedTuple):
    created: datetime
    url: Url
    title: str
    description: str
    tags: Sequence[Tag]

    error: Optional[Exception]=None

    @classmethod
    def make_error(cls, exc: Exception) -> 'Bookmark':
        return cls(
            error=exc,
        )

    @classmethod
    def try_parse(cls, js):
        try:
            urls   = js['href']
            dts    = js['time']
            tagss  = js['tags']
            titles = js['description']
            descs  = js['extended']
            created = pytz.utc.localize(datetime.strptime(dts, '%Y-%m-%dT%H:%M:%SZ'))

            if titles == False:
                titles = '' # *shrug* but happened once
        except Exception as e:
            yield echain(Error(raw=js), e)
            return
        else:
            yield cls(
                created=created,
                url=urls,
                title=titles,
                description=descs,
                tags=tuple(tagss.split()),
            )

class Model:
    def __init__(self, sources: Sequence[Path]) -> None:
        # TODO FIXME use new style exports
        # TODO FIXME take pathish everywhere?
        self.sources = list(map(Path, sources))
        # TODO defensive = True?

    def _iter_raw(self):
        last = max(self.sources)
        j = json.loads(last.read_text())
        if isinstance(j, list):
            # TODO ugh. old style export
            annotations = j
        else:
            annotations = j['annotations']
        yield from annotations



from datetime import datetime
from pathlib import Path
from typing import List, Dict, NamedTuple, Sequence, Optional, Iterable, Iterator, Set
import json
import logging
import pytz

from kython.kerror import ResT, echain, unwrap, sort_res_by
from kython.klogging import setup_logzero

class Error(Exception):
    def __init__(self, raw: Dict) -> None:
        super().__init__(f'error while processing {raw}')
        self.raw = raw

    @property
    def uid(self) -> str:
        return self.raw['hash']


Result = ResT[Bookmark, Error]



def iter_entries() -> Iterator[Result]:
    logger = get_logger()
    pp = _get_last()
    seen: Set[str] = set()
    for jj in json.loads(pp.read_text()):
        hh = jj['hash']
        if hh in seen:
            logger.warning('skipping duplicate item %s', jj)
            # huh, quite a few of them...
            continue
        seen.add(hh)
        yield from Bookmark.try_parse(jj)


def get_entries() -> List[Result]:
    return list(sort_res_by(iter_entries(), key=lambda e: (e.created, e.url)))


def get_ok_entries() -> List[Bookmark]:
    logger = get_logger()
    results = []
    for x in get_entries():
        try:
            res = unwrap(x)
        except Exception as e:
            logger.exception(e)
        else:
            results.append(res)
    return results


def test_errors(tmp_path):
    print(tmp_path)
    pass

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
