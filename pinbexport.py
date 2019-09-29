#!/usr/bin/env python3
import argparse
import json
from typing import Dict, NamedTuple, List, Any

from urllib.parse import urlencode
from urllib.request import urlopen


Json = Dict[str, Any]


class PinboardData(NamedTuple):
    tags: List[Json]
    posts: List[Json]
    notes: List[Json]


class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.auth_token = kwargs['auth_token']
        self.api_base = 'https://api.pinboard.in/v1/'

    def _get(self, endpoint: str):
        query = urlencode([ # type: ignore
            ('format'    , 'json'),
            ('auth_token', self.auth_token),
        ])
        url = self.api_base + endpoint + '?' + query
        return json.loads(urlopen(url).read(), encoding='utf8')

    def export_json(self) -> Json:
        return PinboardData(
            tags =self._get('tags/get'),
            posts=self._get('posts/all'), # TODO
            notes=self._get('notes/list'),
        )._asdict()


def get_json(**params):
    return Exporter(**params).export_json()


def main():
    from export_helper import setup_parser
    parser = argparse.ArgumentParser("Exporter for you Pinboard data")
    setup_parser(parser=parser, params=['auth_token'])
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


if __name__ == '__main__':
    main()
