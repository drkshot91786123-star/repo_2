#!/usr/bin/env python3
"""Open an interactive iOS (Safari/WebKit) mobile browser you can search in.

    python3 ios_browser.py                  # opens Google as iPhone 15
    python3 ios_browser.py https://duckduckgo.com
    python3 ios_browser.py --device "iPhone 13"
    python3 ios_browser.py --tor            # route through Tor (Western exit IP)

The window stays open — type, search, tap, scroll. Close the window or press
Ctrl+C here to quit.
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser import MobileBrowser
from tor import TorController


async def run(url, device, use_tor):
    proxy = None
    if use_tor:
        tor = TorController()
        tor.require_running()
        tor.set_exit_countries()       # Western-rich exits only
        tor.new_identity(wait=8)       # fresh IP
        proxy = tor.socks_url
        print("Routing through Tor.")

    async with MobileBrowser(device, headless=False, proxy=proxy) as mb:
        await mb.open(url)
        print(f"Opened {url} as {device}. Search away — Ctrl+C to quit.")
        await mb.wait_until_closed()


def main():
    ap = argparse.ArgumentParser(description="Interactive iOS mobile browser.")
    ap.add_argument("url", nargs="?", default="https://www.google.com")
    ap.add_argument("--device", default="iPhone 15", help="iPhone model to emulate")
    ap.add_argument("--tor", action="store_true", help="route through Tor")
    args = ap.parse_args()
    if "iPhone" not in args.device:
        ap.error("ios_browser is for iPhones; use run.py for Android devices.")
    try:
        asyncio.run(run(args.url, args.device, args.tor))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
