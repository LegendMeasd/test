"""Simple threaded subdomain finder.

Behavior:
- Load a newline-separated wordlist of labels (e.g. www, mail, dev)
- For each label, attempt to resolve LABEL.TARGET via DNS (socket.gethostbyname)
- If resolution succeeds, optionally attempt an HTTP GET to http://LABEL.TARGET to collect status
- Report found subdomains with IP and HTTP status

This is intentionally lightweight and dependency-minimal.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import socket
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional

import requests


def load_wordlist(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def resolve_host(host: str, timeout: float = 5.0) -> Optional[str]:
    """Return the IPv4/IPv6 address for host, or None if resolution fails."""
    try:
        # socket.gethostbyname may block; caller should use threads if many lookups
        return socket.gethostbyname(host)
    except Exception:
        return None


def probe_http(host: str, timeout: float = 5.0) -> Optional[int]:
    url = f"http://{host}/"
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        return r.status_code
    except Exception:
        return None


def find_subdomains(target: str, labels: Iterable[str], threads: int = 20, timeout: float = 5.0, http_probe: bool = True):
    """Yield dicts: {subdomain, ip, http_status}

    This uses a ThreadPoolExecutor to parallelize hostname resolution and optional HTTP checks.
    """
    target = target.strip().lower().rstrip('.')

    def check(label: str):
        sub = f"{label}.{target}"
        ip = resolve_host(sub, timeout=timeout)
        if not ip:
            return None
        http_status = None
        if http_probe:
            http_status = probe_http(sub, timeout=timeout)
        return {"subdomain": sub, "ip": ip, "http_status": http_status}

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(check, label): label for label in labels}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            if res:
                yield res


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Simple subdomain finder")
    parser.add_argument("-t", "--target", required=True, help="Target domain (example.com)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist file (one label per line)")
    parser.add_argument("-T", "--threads", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--timeout", type=float, default=5.0, help="Network timeout in seconds")
    parser.add_argument("-o", "--output", help="Write found subdomains to this file (JSON lines)")
    parser.add_argument("--no-http", dest="http_probe", action="store_false", help="Skip HTTP probing (faster)")

    args = parser.parse_args(argv)

    wordlist_path = Path(args.wordlist)
    if not wordlist_path.exists():
        print(f"Wordlist not found: {wordlist_path}", file=sys.stderr)
        return 2

    labels = load_wordlist(wordlist_path)
    out_path = Path(args.output) if args.output else None

    results = []
    start = time.time()
    for item in find_subdomains(args.target, labels, threads=args.threads, timeout=args.timeout, http_probe=args.http_probe):
        print(f"FOUND: {item['subdomain']} -> {item['ip']} (http={item['http_status']})")
        results.append(item)
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(item) + "\n")

    elapsed = time.time() - start
    print(f"Done. {len(results)} subdomains found in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
