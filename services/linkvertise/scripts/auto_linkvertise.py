#!/usr/bin/env python3
"""
Auto-runner for the Linkvertise ad flow.

Usage:
  python3 run.py --linkvertise <url> [options]
  python3 run.py --linkvertise --count 5 --concurrency 2
"""

import argparse
import asyncio
import os
import random
import sys
from datetime import datetime, timezone, timedelta

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT_DIR)

from core.proxy import ProxyPool
from services.linkvertise.linkvertise import run

_IST = timezone(timedelta(hours=5, minutes=30))

LOGS_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOGS_FILE = os.path.join(LOGS_DIR, "run_logs.jsonl")

DEFAULT_PROXIES = os.path.join(ROOT_DIR, "config", "Proxies.txt")
MAX_CONCURRENT  = 3

os.makedirs(LOGS_DIR, exist_ok=True)


def write_log(entry: dict):
    import json
    with open(LOGS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


async def run_instance(idx, url, device, headless, pool, logs, sem):
    async with sem:
        print(f"\n[#{idx}] starting  url={url[:60]}  proxy={'yes' if pool else 'no'}")
        result = await run(
            url=url,
            device=device,
            headless=headless,
            proxy_pool=pool,
        )
        skipped = result.get("skipped", False)
        success = result.get("success", False)
        status  = "~" if skipped else ("✓" if success else "✗")
        bw_kb   = (result.get("bytes_sent", 0) + result.get("bytes_recv", 0)) / 1024
        print(f"\n[#{idx}] {status} device={result['device']}  ip={result['ip']}  success={success}")
        if logs:
            entry = {
                "ts":       datetime.now(tz=_IST).strftime("%Y-%m-%d %I:%M:%S %p IST"),
                "instance": idx,
                "device":   result["device"],
                "ip":       result["ip"],
                "url":      url,
                "success":  success,
                "skipped":  skipped,
                "bw_kb":    round(bw_kb, 1),
            }
            write_log(entry)
            print(f"[#{idx}] logged → {LOGS_FILE}  ({bw_kb:.1f} KB)")
        return result


async def main_async(args):
    pool = None
    if not args.no_proxy and os.path.exists(args.proxy_file):
        pool = ProxyPool(args.proxy_file)
        print(f"[proxy] loaded from {os.path.basename(args.proxy_file)}")
    elif not args.no_proxy:
        print(f"[warn]  proxy file not found: {args.proxy_file}")

    headless = args.headless or (pool is not None and not args.headed)

    count       = args.count
    concurrency = args.concurrency
    sem         = asyncio.Semaphore(concurrency)
    url         = args.url

    print(f"[run]  {count} instance(s), max {concurrency} concurrent\n")

    idx           = 0
    active        = set()
    completed     = 0
    succeeded     = 0
    total_skipped = 0
    total_bytes   = 0

    async def _spawn():
        nonlocal idx
        idx += 1
        t = asyncio.ensure_future(
            run_instance(idx, url, args.device, headless, pool, args.logs, sem)
        )
        active.add(t)

    for _ in range(min(count, concurrency)):
        await _spawn()

    while active:
        done, _ = await asyncio.wait(active, return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            active.discard(t)
            try:
                result = t.result()
            except Exception:
                completed += 1
                if completed + len(active) < count:
                    await _spawn()
                continue
            if result.get("skipped"):
                total_skipped += 1
                if completed + len(active) < count:
                    await asyncio.sleep(random.uniform(2, 5))
                    await _spawn()
            else:
                completed += 1
                total_bytes += result.get("bytes_sent", 0) + result.get("bytes_recv", 0)
                if result.get("success"):
                    succeeded += 1
                if completed + len(active) < count:
                    await _spawn()

    avg_kb = (total_bytes / completed / 1024) if completed else 0
    print(f"\n[done] {succeeded}/{count} succeeded  ({total_skipped} skipped)")
    print(f"[bw]   {total_bytes/1024/1024:.2f} MB total  ·  {avg_kb:.1f} KB/run avg")


def main():
    ap = argparse.ArgumentParser(description="Auto-complete the Linkvertise ad flow.")
    ap.add_argument("url", help="Linkvertise URL to complete")
    ap.add_argument("--count",       type=int, default=1,            help="total runs (default: 1)")
    ap.add_argument("--concurrency", type=int, default=MAX_CONCURRENT, help=f"max concurrent (default: {MAX_CONCURRENT})")
    ap.add_argument("--device",      default=None,                   help="device to emulate (random if omitted)")
    ap.add_argument("--headless",    action="store_true",            help="force headless")
    ap.add_argument("--headed",      action="store_true",            help="force headed (show browser)")
    ap.add_argument("--no-proxy",    action="store_true",            help="use real IP — skip proxy")
    ap.add_argument("--logs",        action="store_true",            help="append run_logs.jsonl after each instance")
    ap.add_argument("--proxy-file",  default=DEFAULT_PROXIES,        help="path to proxy list")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
