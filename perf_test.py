#!/usr/bin/env python3
"""Measure response times for surf-weather frontend and backend endpoints."""

import argparse
import sys
import time
import urllib.request
import urllib.error
from statistics import mean

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

ENVS = {
    "test": {
        "frontend": "https://surf-frontend-test-476326886107.us-central1.run.app",
        "backend": "https://surf-backend-test-476326886107.us-central1.run.app",
    },
    "prod": {
        "frontend": "https://surf-frontend-476326886107.us-central1.run.app",
        "backend": "https://surf-backend-476326886107.us-central1.run.app",
    },
}

# All paths are relative to the frontend URL.
# /api/* is proxied by nginx to the backend — matches real browser behaviour.
ENDPOINTS = [
    "/",
    "/api/lakes",
    "/api/lakes/east_canyon",
    "/api/lakes/echo",
    "/api/lakes/lake_powell",
    "/api/lakes/flaming_gorge",
]


def color_time(t: float) -> tuple[str, str]:
    """Return (raw_str, ansi_colored_str) for a timing value."""
    raw = f"{t:.2f}s"
    if t < 1.0:
        color = GREEN
    elif t < 3.0:
        color = YELLOW
    else:
        color = RED
    return raw, f"{color}{raw}{RESET}"


def measure_once(url: str, timeout: int) -> tuple[float | None, int]:
    try:
        start = time.perf_counter()
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read()
        elapsed = time.perf_counter() - start
        return elapsed, resp.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception:
        return None, 0


def run_test(env: str, runs: int, timeout: int) -> None:
    urls = ENVS[env]

    print(f"\n{BOLD}Surf Weather — Performance Test{RESET}")
    print(f"  Environment : {BOLD}{env}{RESET}")
    print(f"  Frontend    : {urls['frontend']}")
    print(f"  Backend     : {urls['backend']}")
    print(f"  Runs per endpoint : {runs}")
    print()

    results: list[tuple[str, list[float | None], list[int]]] = []

    for path in ENDPOINTS:
        url = urls["frontend"] + path

        print(f"  {DIM}{path}...{RESET}", end="", flush=True)

        times: list[float | None] = []
        statuses: list[int] = []
        for _ in range(runs):
            t, s = measure_once(url, timeout)
            times.append(t)
            statuses.append(s)
            print(f"{DIM}.{RESET}", end="", flush=True)

        print()
        results.append((path, times, statuses))

    # ── table ──────────────────────────────────────────────────────────────
    print()
    label_w = max(len(r[0]) for r in results) + 2
    col_w = 7  # visual width of each time column ("99.99s" = 6 chars + 1 pad)

    headers = [f"Run {i + 1}" for i in range(runs)] + ["Avg"]
    header_line = "  " + "Endpoint".ljust(label_w)
    for h in headers:
        header_line += "  " + h.rjust(col_w)
    print(header_line)
    print("  " + "─" * (label_w + (col_w + 2) * len(headers)))

    for label, times, statuses in results:
        valid = [t for t in times if t is not None]
        avg = mean(valid) if valid else None

        cells: list[str] = []
        for t, s in zip(times, statuses):
            if t is None:
                raw = f"ERR{s}"
                colored = f"{RED}{raw}{RESET}"
            else:
                raw, colored = color_time(t)
            pad = " " * max(0, col_w - len(raw))
            cells.append(pad + colored)

        if avg is None:
            avg_raw = "ERROR"
            avg_colored = f"{RED}{avg_raw}{RESET}"
        else:
            avg_raw, avg_colored = color_time(avg)
        pad = " " * max(0, col_w - len(avg_raw))
        cells.append(pad + avg_colored)

        print("  " + label.ljust(label_w) + "  " + "  ".join(cells))

    print()
    print(f"  {GREEN}●{RESET} < 1s   {YELLOW}●{RESET} 1–3s   {RED}●{RESET} > 3s")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure surf-weather response times")
    parser.add_argument(
        "--env", choices=["test", "prod"], default="test",
        help="Environment to test (default: test)",
    )
    parser.add_argument(
        "--runs", type=int, default=3, metavar="N",
        help="Number of requests per endpoint (default: 3)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, metavar="S",
        help="Request timeout in seconds (default: 30)",
    )
    args = parser.parse_args()

    run_test(args.env, args.runs, args.timeout)


if __name__ == "__main__":
    main()
