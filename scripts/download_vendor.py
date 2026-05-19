"""Descarrega les llibreries JS que el web necessita a web/vendor/.

Actualment només Vega + Vega-Lite + Vega-Embed (~800 KB total), els únics
deps de runtime: la web fa servir JSON estàtic + filtrat en JS pur, no
necessita DuckDB-WASM ni cap altre paquet.

Idempotent: fitxers existents es deixen sense tocar. Per forçar re-descàrrega,
esborra web/vendor/ i torna a executar.

Ús: .venv/bin/python scripts/download_vendor.py
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
VENDOR = PROJECT / "web" / "vendor"
VENDOR.mkdir(parents=True, exist_ok=True)


def get(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"  -> {dest.relative_to(PROJECT)}", end="", flush=True)
    raw = urllib.request.urlopen(url, timeout=120).read()
    dest.write_bytes(raw)
    print(f"  ({len(raw)/1024:.1f} KB)")


# === Vega + Vega-Lite + Vega-Embed (UMD bundles) ===
get("https://cdn.jsdelivr.net/npm/vega@5.30.0/build/vega.min.js",
    VENDOR / "vega.min.js")
get("https://cdn.jsdelivr.net/npm/vega-lite@5.21.0/build/vega-lite.min.js",
    VENDOR / "vega-lite.min.js")
get("https://cdn.jsdelivr.net/npm/vega-embed@6.26.0/build/vega-embed.min.js",
    VENDOR / "vega-embed.min.js")

print("\nFet. web/vendor/ conté totes les dependències.")
total = sum(p.stat().st_size for p in VENDOR.rglob('*') if p.is_file())
print(f"Total: {total / 1024:.1f} KB")
