#!/usr/bin/env python3
"""
Reads destinations.txt, formats with the template, POSTs to paste.rs,
and saves the returned URL to paste_url.txt.
Run this whenever destinations.txt changes.
"""
import os
import sys
import urllib.request

ADMAVEN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINATIONS_FILE = os.path.join(ADMAVEN_DIR, "destinations.txt")
TEMPLATE_FILE = os.path.join(ADMAVEN_DIR, "destinations_template.txt")
PASTE_URL_FILE = os.path.join(ADMAVEN_DIR, "paste_url.txt")


def build_content():
    template = open(TEMPLATE_FILE).read()

    destinations = [
        l.strip() for l in open(DESTINATIONS_FILE)
        if l.strip() and l.strip().startswith("http")
    ]
    if not destinations:
        print("[error] destinations.txt has no valid URLs")
        sys.exit(1)

    links_block = "\n".join(destinations)
    # Insert links after the first header line (🎬 Entertainment)
    return template + "\n" + links_block + "\n"


def post_to_paste_rs(content: str) -> str:
    data = content.encode("utf-8")
    req = urllib.request.Request("https://paste.rs/", data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode().strip()


def main():
    if not os.path.exists(DESTINATIONS_FILE):
        print(f"[error] {DESTINATIONS_FILE} not found")
        sys.exit(1)
    if not os.path.exists(TEMPLATE_FILE):
        print(f"[error] {TEMPLATE_FILE} not found")
        sys.exit(1)

    content = build_content()
    print("[sync]  posting to paste.rs...")
    url = post_to_paste_rs(content)
    print(f"[sync]  created: {url}")

    with open(PASTE_URL_FILE, "w") as f:
        f.write(url + "\n")
    print(f"[sync]  saved URL to paste_url.txt")


if __name__ == "__main__":
    main()
