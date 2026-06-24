#!/usr/bin/env python3
"""Create an AdMaven content locker via API with a random title."""

import random
import string
import requests

API_URL   = "https://publishers.ad-maven.com/api/public/content_locker"
API_TOKEN = "8924852faa8a3901f7ed34e84d3dfc6f3e820b12cf9c9af47386e3696af40a5a"


def random_title(length=random.randint(6, 7)):
    return "".join(random.choices(string.ascii_uppercase, k=length))


def create_locker(dest_url, background=None):
    title = random_title()
    payload = {"title": title, "url": dest_url}
    if background:
        payload["background"] = background

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    resp = requests.post(API_URL, json=payload, headers=headers)
    data = resp.json()

    if data.get("type") == "error":
        print(f"[error] {data['message']}")
        return None

    msg = data["message"][0]
    print(f"[created] title={title}  short={msg['short']}  url={msg['full_short']}")
    return msg["full_short"]


if __name__ == "__main__":
    create_locker()
