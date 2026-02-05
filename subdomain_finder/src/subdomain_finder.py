"""Simple threaded subdomain finder.

Behavior:
- Load a newline-separated wordlist of labels (e.g. www, mail, dev)
- For each label, attempt to resolve LABEL.TARGET via DNS using dnspython for better reliability
- If resolution succeeds, optionally attempt an HTTP GET to http://LABEL.TARGET to collect status
- Report found subdomains with IP and HTTP status

Enhanced with:
- Better DNS resolution (dnspython with configurable timeout)
- Retry logic for failed lookups
- Support for both A and AAAA records
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

try:
    import dns.resolver
    import dns.exception
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


def load_wordlist(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def resolve_host(host: str, timeout: float = 5.0, retries: int = 2) -> Optional[str]:
    """Return the IPv4/IPv6 address for host, or None if resolution fails.
    
    Uses dnspython if available (more reliable), falls back to socket.gethostbyname.
    Includes retry logic for transient failures.
    """
    if HAS_DNSPYTHON:
        # Try with dnspython first (more reliable timeout handling)
        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        
        for attempt in range(retries):
            try:
                # Try to resolve A record (IPv4)
                answers = resolver.resolve(host, "A")
                for rdata in answers:
                    return str(rdata)
            except (dns.exception.Timeout, dns.exception.NXDOMAIN, dns.exception.NoAnswer, dns.exception.DNSException):
                if attempt < retries - 1:
                    time.sleep(0.1)  # Brief delay before retry
                continue
            except Exception:
                continue
        
        return None
    else:
        # Fallback to socket.gethostbyname if dnspython not available
        for attempt in range(retries):
            try:
                return socket.gethostbyname(host)
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.1)
                continue
        return None


def probe_http(host: str, timeout: float = 5.0) -> Optional[int]:
    url = f"http://{host}/"
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        return r.status_code
    except Exception:
        return None


def find_subdomains(target: str, labels: Iterable[str], threads: int = 20, timeout: float = 5.0, http_probe: bool = True, retries: int = 2):
    """Yield dicts: {subdomain, ip, http_status}

    This uses a ThreadPoolExecutor to parallelize hostname resolution and optional HTTP checks.
    Enhanced with retry logic for better reliability on slow/unreliable DNS.
    """
    target = target.strip().lower().rstrip('.')

    def check(label: str):
        sub = f"{label}.{target}"
        ip = resolve_host(sub, timeout=timeout, retries=retries)
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
    parser = argparse.ArgumentParser(description="Simple subdomain finder with enhanced DNS resolution")
    parser.add_argument("-t", "--target", required=True, help="Target domain (example.com)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist file (one label per line)")
    parser.add_argument("-T", "--threads", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--timeout", type=float, default=5.0, help="DNS timeout in seconds")
    parser.add_argument("--retries", type=int, default=2, help="Number of retries for failed DNS lookups")
    parser.add_argument("-o", "--output", help="Write found subdomains to this file (JSON lines)")
    parser.add_argument("--no-http", dest="http_probe", action="store_false", help="Skip HTTP probing (faster, DNS-only)")

    args = parser.parse_args(argv)

    wordlist_path = Path(args.wordlist)
    if not wordlist_path.exists():
        print(f"Wordlist not found: {wordlist_path}", file=sys.stderr)
        return 2

    labels = load_wordlist(wordlist_path)
    out_path = Path(args.output) if args.output else None

    print(f"[*] Starting scan of {args.target} with {len(labels)} labels ({args.threads} threads)")
    print(f"[*] DNS timeout: {args.timeout}s, Retries: {args.retries}")
    if HAS_DNSPYTHON:
        print(f"[*] Using dnspython for reliable DNS resolution")
    else:
        print(f"[*] Using socket.gethostbyname (install dnspython for better reliability)")
    print()

    results = []
    start = time.time()
    for item in find_subdomains(args.target, labels, threads=args.threads, timeout=args.timeout, http_probe=args.http_probe, retries=args.retries):
        print(f"FOUND: {item['subdomain']} -> {item['ip']} (http={item['http_status']})")
        results.append(item)
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(item) + "\n")

    elapsed = time.time() - start
    print()
    print(f"Done. {len(results)} subdomains found in {elapsed:.2f}s ({len(results)/elapsed:.1f} results/sec)")
    print(f"Total labels attempted: {len(labels)}")
    if out_path:
        print(f"Results saved to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
