"""
Residential proxy pool — loads proxies from a file (host:port:user:pass, one per line)
or generates them from EVOMI_* environment variables if the file doesn't exist.
"""

import os
import random


def _proxies_from_env():
    """Build proxy list from EVOMI_* env vars. Returns [] if vars not set."""
    host = os.environ.get("EVOMI_HOST")
    port = os.environ.get("EVOMI_PORT")
    user = os.environ.get("EVOMI_USER")
    pwd  = os.environ.get("EVOMI_PASS")
    countries = os.environ.get("EVOMI_COUNTRIES", "")
    if not all([host, port, user, pwd]):
        return []
    proxies = []
    if countries:
        for country in countries.split(","):
            country = country.strip()
            if country:
                proxies.append({
                    "server":   f"http://{host}:{port}",
                    "username": f"{user}_country-{country}",
                    "password": pwd,
                })
    else:
        proxies.append({
            "server":   f"http://{host}:{port}",
            "username": user,
            "password": pwd,
        })
    return proxies


class ProxyPool:
    def __init__(self, path=None):
        self.proxies = []

        if path and os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(":")
                    if len(parts) != 4:
                        continue
                    ip, port, user, pwd = parts
                    self.proxies.append({
                        "server":   f"http://{ip}:{port}",
                        "username": user,
                        "password": pwd,
                    })
            if self.proxies:
                print(f"[proxy] loaded {len(self.proxies)} proxies from {path}")
                return

        self.proxies = _proxies_from_env()
        if self.proxies:
            print(f"[proxy] loaded {len(self.proxies)} proxies from env vars")
            return

        raise ValueError("No proxies available — set EVOMI_* env vars or provide a proxy file")

    def pick(self):
        """Return a random proxy dict ready for Playwright's proxy= option."""
        p = random.choice(self.proxies)
        print(f"[proxy] using {p['server']}")
        return p

    def __len__(self):
        return len(self.proxies)
