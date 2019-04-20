#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, NamedTuple, Sequence, Optional, Iterable, Iterator
import json
import logging

from kython.kerror import Res, echain, unwrap, sort_res_by
from kython.klogging import setup_logzero


BDIR = Path('/L/backups/pinboard')


def get_logger():
    return logging.getLogger('pinboard-provider')


def _get_last() -> Path:
    return max(BDIR.glob('*.json'))


Url = str
Tag = str

class Entry(NamedTuple):
    created: datetime
    url: Url
    description: str
    tags: Sequence[Tag]
    deleted_dt: Optional[datetime]=None

    @property
    def is_deleted(self):
        return self.deleted_dt is not None

    @classmethod
    def try_parse(cls, js) -> Iterable[Res['Entry']]:
        try:
            urls  = js['href']
            dts   = js['time']
            tagss = js['tags']
            descs = js['description']
        except Exception as e:
            yield echain(f'error while parsing {js}', e)
            return
        else:
            yield cls(
                created=dts,
                url=urls,
                description=descs,
                tags=tuple(tagss.split()),
            )
# {"href":"https:\/\/www.booking.com\/hotel\/gb\/tarn-hows.en-gb.html?aid=397594;label=gog235jc-1DCAEoggI46AdICVgDaFCIAQGYAQm4AQjIAQzYAQPoAQH4AQKIAgGoAgO4Ar2FneUFwAIB;sid=949119fe10304ddc1bbbbc967ce97f70;atlas_src=sr_iw_btn;checkin=2019-05-22;checkout=201
# 9-05-26;dist=0;group_adults=1;group_children=0;nflt=pri%3D2%3B;no_rooms=1;room1=A;sb_price_type=total;type=total;ucfs=1&","description":"Tarn Hows, Keswick \u2013 Updated 2019 Prices","extended":"","meta":"e03e43ce89b5d6471b196dbb1d48cb7b","hash":"cb8775
# d288009592a58e8cc3e4decd68","time":"2019-04-05T12:21:12Z","shared":"no","toread":"yes","tags":""},


Result = Res[Entry]


def iter_entries() -> Iterator[Result]:
    pp = _get_last()
    for jj in json.loads(pp.read_text()):
        yield from Entry.try_parse(jj)


def get_entries() -> List[Result]:
    return list(sort_res_by(iter_entries(), key=lambda e: e.created))


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
    assert any('хранение шума' in x.description for x in datas)


def main():
    setup_logzero(get_logger(), level=logging.INFO)
    test()

if __name__ == '__main__':
    main()
