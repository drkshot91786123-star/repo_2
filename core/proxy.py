"""
Residential proxy pool — built from EVOMI_* environment variables.
"""

import os
import random


def _build_proxies(countries_env_key):
    host = os.environ.get("EVOMI_HOST")
    port = os.environ.get("EVOMI_PORT")
    user = os.environ.get("EVOMI_USER")
    pwd  = os.environ.get("EVOMI_PASS")
    if not all([host, port, user, pwd]):
        raise ValueError("EVOMI_HOST, EVOMI_PORT, EVOMI_USER, EVOMI_PASS must all be set")
    countries = os.environ.get(countries_env_key, "")
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
    def __init__(self, countries_env_key="EVOMI_HIGH_CPM_COUNTRIES"):
        self.proxies = _build_proxies(countries_env_key)
        print(f"[proxy] {len(self.proxies)} proxies from env ({countries_env_key})")

    def pick(self):
        p = random.choice(self.proxies)
        print(f"[proxy] using {p['server']} user={p['username']}")
        return p

    def __len__(self):
        return len(self.proxies)
