"""website_automation — spoofed mobile browser + Tor IP rotation for testing your site.

    browser.py  — MobileBrowser, DEVICE_PROFILE, spoof_script
    tor.py      — TorController (SOCKS proxy + NEWNYM identity rotation)
    locker.py   — task-locker automation (random device + IP per run)
"""

from browser import DEVICE_PROFILE, MobileBrowser, spoof_script
from locker import run as run_locker
from proxy import ProxyPool
from tor import TorController, TorError

__all__ = ["MobileBrowser", "DEVICE_PROFILE", "spoof_script",
           "TorController", "TorError", "ProxyPool", "run_locker"]
