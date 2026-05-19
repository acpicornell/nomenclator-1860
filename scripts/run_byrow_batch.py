"""Run extract_by_row.py over a list of pages with controlled concurrency."""
from __future__ import annotations
import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def run_page(page: int) -> tuple[int, int, str, int]:
    log = Path(f"/tmp/byrow{page}.log")
    t0 = time.time()
    proc = subprocess.run(
        [".venv/bin/python", "scripts/extract_by_row.py", str(page)],
        cwd=PROJECT,
        stdout=open(log, "w"),
        stderr=subprocess.STDOUT,
    )
    elapsed = int(time.time() - t0)
    return page, proc.returncode, str(log), elapsed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pages", nargs="+", type=int)
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    print(f"Pages: {args.pages}  ({len(args.pages)})")
    print(f"Parallel workers: {args.workers}")
    print()

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_page, pg): pg for pg in args.pages}
        for fut in as_completed(futures):
            pg, rc, log, elapsed = fut.result()
            status = "OK" if rc == 0 else "FAIL"
            done = sum(1 for f in futures if f.done())
            total_elapsed = int(time.time() - t0)
            print(f"  {status} page {pg} ({elapsed}s) - {done}/{len(args.pages)} done, {total_elapsed}s total")

    print(f"\nTotal: {int(time.time() - t0)}s")


if __name__ == "__main__":
    main()
