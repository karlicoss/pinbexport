import argparse
import json
from urllib.parse import urlencode
from urllib.request import urlopen

import hpikit.cli.export as cli
from hpikit.json import Json


class Exporter:
    def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002
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
        return {
            'tags': self._get('tags/get'),
            'posts': self._get('posts/all'),
            'notes': self._get('notes/list'),
        }


def get_json(**params) -> Json:
    return Exporter(**params).export_json()


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    params = cli.get_params(parser, args)

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    cli.dump(js, path=args.path)


def make_parser() -> argparse.ArgumentParser:
    parser = cli.make_parser(
        description='Export your bookmarks from [Pinboard](https://pinboard.in)',
        params=['token'],
        extra_usage='''
You can also import `export.py` this as a module and call `get_json` function directly to get raw JSON.
''',
    )
    return parser


if __name__ == '__main__':
    main()
