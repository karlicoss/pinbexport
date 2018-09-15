#!/usr/bin/env python3
from pinboard_secrets import PINBOARD_TOKEN
import requests

URL = "https://api.pinboard.in/v1/posts/all?format=json&auth_token=%s" % PINBOARD_TOKEN

print(requests.get(URL).text)
