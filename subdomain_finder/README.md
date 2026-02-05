# Subdomain Finder

Comprehensive Python utility to enumerate possible subdomains for a target domain using DNS resolution. Features threaded scanning, optional HTTP probing, and massive 1400+ entry wordlist.

## Quick Start

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. **Navigate to the project folder:**
```powershell
cd "C:\Users\Akila Widuruwan\Desktop\bug sni finder"
```

2. **Install dependencies:**
```powershell
python -m pip install -r subdomain_finder/requirements.txt
```

Or install manually:
```powershell
python -m pip install requests pytest
```

## How to Run

### Basic Usage (DNS-only, fastest)

```powershell
python subdomain_finder\src\subdomain_finder.py -t example.com -w subdomain_finder\wordlists\common.txt --no-http
```

**What it does:**
- Scans `example.com` for common subdomains
- Uses DNS resolution only (no HTTP probes)
- Prints found subdomains to console

**Example output:**
```
FOUND: www.example.com -> 93.184.216.34 (http=None)
FOUND: mail.example.com -> 93.184.216.35 (http=None)
Done. 2 subdomains found in 3.45s
```

### Full Scan with HTTP Probing

```powershell
python subdomain_finder\src\subdomain_finder.py -t example.com -w subdomain_finder\wordlists\common.txt -T 20
```

**What it does:**
- Scans all 1400+ subdomains
- Checks DNS resolution
- Attempts HTTP GET request to each found subdomain
- Shows HTTP status code (200, 404, 500, etc.)

### Save Results to File (JSON Lines format)

```powershell
python subdomain_finder\src\subdomain_finder.py -t example.com -w subdomain_finder\wordlists\common.txt -o results.jsonl --no-http
```

**Creates `results.jsonl`:**
```json
{"subdomain": "www.example.com", "ip": "93.184.216.34", "http_status": null}
{"subdomain": "mail.example.com", "ip": "93.184.216.35", "http_status": null}
```

### Increase Thread Count (faster scanning)

```powershell
python subdomain_finder\src\subdomain_finder.py -t example.com -w subdomain_finder\wordlists\common.txt -T 50
```

- `-T 50` = 50 concurrent threads (default is 20)
- Higher = faster, but may overwhelm the target or your network

### Adjust Timeout for Slow Networks

```powershell
python subdomain_finder\src\subdomain_finder.py -t example.com -w subdomain_finder\wordlists\common.txt --timeout 10
```

- `--timeout 10` = 10 seconds per request (default 5)
- Increase if timeouts occur, decrease for faster scans

## All Command-Line Options

```powershell
python subdomain_finder\src\subdomain_finder.py --help
```

Output:
```
usage: subdomain_finder.py [-h] -t TARGET -w WORDLIST [-T THREADS] [--timeout TIMEOUT]
                           [-o OUTPUT] [--no-http]

Simple subdomain finder

options:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        Target domain (example.com)
  -w WORDLIST, --wordlist WORDLIST
                        Path to wordlist file (one label per line)
  -T THREADS, --threads THREADS
                        Number of concurrent workers (default 20)
  --timeout TIMEOUT     Network timeout in seconds (default 5)
  -o OUTPUT, --output OUTPUT
                        Write found subdomains to this file (JSON lines)
  --no-http             Skip HTTP probing (faster, DNS-only)
```

## Real-World Examples

### Example 1: Quick scan of your own domain
```powershell
python subdomain_finder\src\subdomain_finder.py -t yourcompany.com -w subdomain_finder\wordlists\common.txt --no-http
```

### Example 2: Full scan with output file
```powershell
python subdomain_finder\src\subdomain_finder.py -t google.com -w subdomain_finder\wordlists\common.txt -T 30 -o google_subdomains.jsonl
```

### Example 3: Slow, thorough scan (with HTTP checks)
```powershell
python subdomain_finder\src\subdomain_finder.py -t microsoft.com -w subdomain_finder\wordlists\common.txt -T 15 --timeout 10
```

### Example 4: Fast DNS-only with high threads
```powershell
python subdomain_finder\src\subdomain_finder.py -t github.com -w subdomain_finder\wordlists\common.txt -T 100 --no-http --timeout 2
```

## Running Tests

Run the pytest test suite to verify the tool works:

```powershell
python -m pytest subdomain_finder -v
```

**Expected output:**
```
subdomain_finder/tests/test_subdomain_finder.py::test_load_wordlist PASSED
subdomain_finder/tests/test_subdomain_finder.py::test_resolve_host_success_and_failure PASSED
subdomain_finder/tests/test_subdomain_finder.py::test_find_subdomains_with_mocked_dns PASSED
====== 3 passed in 0.73s ======
```

## Understanding Output

When you run the scanner, you'll see output like:

```
FOUND: www.example.com -> 93.184.216.34 (http=None)
FOUND: mail.example.com -> 93.184.216.35 (http=200)
FOUND: api.example.com -> 93.184.216.36 (http=404)
Done. 3 subdomains found in 5.23s
```

**Breakdown:**
- `FOUND:` - Subdomain that successfully resolved via DNS
- `93.184.216.34` - IP address it resolved to
- `(http=None)` - HTTP probe was skipped (`--no-http` flag)
- `(http=200)` - HTTP probe succeeded, server responded with status 200
- `(http=404)` - HTTP probe succeeded, server responded with 404 Not Found

## Wordlist Information

The tool comes with a comprehensive **1,400+ entry wordlist** covering:
- Common web services (www, mail, api, admin, etc.)
- Cloud platforms (AWS, Azure, GCP)
- Development tools (Git, Jenkins, Docker, Kubernetes)
- Databases (MySQL, Postgres, Redis, MongoDB)
- Monitoring (Prometheus, Grafana, ELK)
- AI/ML services (OpenAI, TensorFlow, PyTorch)
- Blockchain (Bitcoin, Ethereum, DeFi)
- Gaming platforms (Steam, Epic, Roblox)
- And much more...

Located at: `subdomain_finder\wordlists\common.txt`

## Performance Tips

1. **Use `--no-http` for speed** – DNS-only is 5-10x faster than HTTP probing
2. **Increase threads** – Start with `-T 50`, increase up to 100+ for faster scans
3. **Reduce timeout** – Lower `--timeout 2` for faster failures on unresponsive hosts
4. **Target domains you own** – Don't scan third-party domains without permission

## Ethical & Legal Notes

⚠️ **IMPORTANT:**
- Only scan domains **you own or have explicit written permission to test**
- Unauthorized domain scanning may be illegal in your jurisdiction
- Excessive scanning may be detected as a denial-of-service attempt
- Use this tool responsibly and ethically

## Troubleshooting

### "Module not found" error
```powershell
python -m pip install -r subdomain_finder/requirements.txt
```

### "Wordlist not found" error
Make sure the wordlist path is correct:
```powershell
dir subdomain_finder\wordlists\
```

### Slow scanning
- Add `--no-http` flag for DNS-only mode
- Increase `-T` value (e.g., `-T 100`)
- Decrease `--timeout` value (e.g., `--timeout 2`)

### No results found
- Try a shorter timeout: `--timeout 2`
- Check your internet connection: `ping 8.8.8.8`
- Try a different target: `python ... -t google.com ...`

## File Structure

```
subdomain_finder/
├── src/
│   ├── __init__.py
│   └── subdomain_finder.py       # Main script
├── tests/
│   ├── __init__.py
│   └── test_subdomain_finder.py  # Unit tests
├── wordlists/
│   └── common.txt                # 1400+ subdomain labels
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## License & Attribution

This tool is provided for educational and authorized security testing purposes only.

---

**Last updated:** February 5, 2026
