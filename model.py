#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, NamedTuple, Sequence, Optional, Iterable, Iterator, Set
import json
import logging
import pytz

from kython.kerror import ResT, echain, unwrap, sort_res_by
from kython.klogging import setup_logzero


BDIR = Path('/L/backups/pinboard')


def get_logger():
    return logging.getLogger('pinboard-provider')


def _get_last() -> Path:
    return max(BDIR.glob('*.json'))


Url = str
Tag = str


class Error(Exception):
    def __init__(self, raw: Dict) -> None:
        super().__init__(f'error while processing {raw}')
        self.raw = raw

    @property
    def uid(self) -> str:
        return self.raw['hash']


Result = ResT['Entry', Error]

class Entry(NamedTuple):
    created: datetime
    url: Url
    title: str
    description: str
    tags: Sequence[Tag]
    deleted_dt: Optional[datetime]=None

    @property
    def uid(self) -> str:
        return self.url

    @property
    def is_deleted(self):
        return self.deleted_dt is not None

    @classmethod
    def try_parse(cls, js) -> Iterable[Result]:
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
        yield from Entry.try_parse(jj)


def get_entries() -> List[Result]:
    return list(sort_res_by(iter_entries(), key=lambda e: (e.created, e.url)))


def get_ok_entries() -> List[Entry]:
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


def test():
    datas = get_ok_entries()
    assert len(datas) > 100
    assert any('хранение шума' in x.title for x in datas)


def main():
    setup_logzero(get_logger(), level=logging.INFO)
    test()

if __name__ == '__main__':
    main()
