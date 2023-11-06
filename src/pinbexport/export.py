#!/usr/bin/env python3
import argparse
import json

from urllib.parse import urlencode
from urllib.request import urlopen

from .exporthelpers.export_helper import Json, setup_parser, Parser


class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.token: str = kwargs['token']
        self.api_base = 'https://api.pinboard.in/v1/'

    def _get(self, endpoint: str) -> Json:
        query = urlencode(
            [
                ('format', 'json'),
                ('auth_token', self.token),
            ]
        )
        url = self.api_base + endpoint + '?' + query
        return json.loads(urlopen(url).read())

    def export_json(self) -> Json:
        return dict(
            tags=self._get('tags/get'),
            posts=self._get('posts/all'),
            notes=self._get('notes/list'),
        )


def get_json(**params) -> Json:
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
    parser = Parser('Export your bookmarks from [[https://pinboard.in][Pinboard]]')
    setup_parser(
        parser=parser,
        params=['token'],
        extra_usage='''
You can also import ~export.py~ this as a module and call ~get_json~ function directly to get raw JSON.
''',
    )
    return parser


if __name__ == '__main__':
    main()
