#!/usr/bin/env python3
import argparse
import json
from typing import Dict, NamedTuple, List, Any

from urllib.parse import urlencode
from urllib.request import urlopen

from .exporthelpers.export_helper import Json


class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.token = kwargs['token']
        self.api_base = 'https://api.pinboard.in/v1/'

    def _get(self, endpoint: str):
        query = urlencode([ # type: ignore
            ('format'    , 'json'),
            ('auth_token', self.token),
        ])
        url = self.api_base + endpoint + '?' + query
        return json.loads(urlopen(url).read(), encoding='utf8')

    def export_json(self) -> Json:
        return dict(
            tags = self._get('tags/get'),
            posts= self._get('posts/all'), # TODO
            notes= self._get('notes/list'),
        )


def get_json(**params):
    return Exporter(**params).export_json()


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


def make_parser() -> argparse.ArgumentParser:
    from .exporthelpers.export_helper import setup_parser, Parser
    parser = Parser('Export your bookmarks from Pinboard')
    setup_parser(
        parser=parser,
        params=['token'],
        extra_usage='''
You can also import ~export.py~ this as a module and call ~get_json~ function directly to get raw JSON.
''')
    return parser


if __name__ == '__main__':
    main()
