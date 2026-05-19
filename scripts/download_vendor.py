"""Download every JS/CSS/WASM library the web needs into web/vendor/ so it
can run offline (except for OpenStreetMap tiles used by the NGIB map,
which are fetched on demand from osm.org).

Idempotent: existing files are left untouched. To force a re-download,
delete web/vendor/ and run again.

Usage: .venv/bin/python scripts/download_vendor.py
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
VENDOR = PROJECT / "web" / "vendor"
VENDOR.mkdir(parents=True, exist_ok=True)
(VENDOR / "images").mkdir(exist_ok=True)


def get(url: str, dest: Path, force: bool = False) -> None:
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return
    print(f"  -> {dest.relative_to(PROJECT)}", end="", flush=True)
    raw = urllib.request.urlopen(url, timeout=120).read()
    dest.write_bytes(raw)
    print(f"  ({len(raw)/1024:.1f} KB)")


# === Leaflet 1.9.4 ===
LV = "1.9.4"
LEAFLET = f"https://cdn.jsdelivr.net/npm/leaflet@{LV}/dist"
get(f"{LEAFLET}/leaflet.css", VENDOR / "leaflet.css")
get(f"{LEAFLET}/leaflet.js", VENDOR / "leaflet.js")
for img in ("marker-icon.png", "marker-icon-2x.png", "marker-shadow.png",
            "layers.png", "layers-2x.png"):
    get(f"{LEAFLET}/images/{img}", VENDOR / "images" / img)

# === Leaflet.markercluster 1.5.3 ===
MCV = "1.5.3"
MC = f"https://cdn.jsdelivr.net/npm/leaflet.markercluster@{MCV}/dist"
get(f"{MC}/MarkerCluster.css", VENDOR / "MarkerCluster.css")
get(f"{MC}/MarkerCluster.Default.css", VENDOR / "MarkerCluster.Default.css")
get(f"{MC}/leaflet.markercluster.js", VENDOR / "leaflet.markercluster.js")

# === DuckDB-WASM 1.30.0 ===
# Workers and WASM binaries go straight in. The ESM (+esm) bundle is
# served by jsdelivr but imports apache-arrow, tslib and flatbuffers from
# absolute paths; resolve them recursively and rewrite the imports.
DV = "1.30.0"
DD = f"https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@{DV}/dist"
for w in ("duckdb-browser-mvp.worker.js",
          "duckdb-browser-eh.worker.js",
          "duckdb-browser-coi.worker.js",
          "duckdb-browser-coi.pthread.worker.js"):
    get(f"{DD}/{w}", VENDOR / w)
for wasm in ("duckdb-mvp.wasm", "duckdb-eh.wasm", "duckdb-coi.wasm"):
    get(f"{DD}/{wasm}", VENDOR / wasm)


def pkg_to_local(npm_path: str) -> str:
    """'/npm/apache-arrow@17.0.0/+esm' -> 'apache-arrow-17.0.0.mjs'"""
    m = re.match(r"/npm/(.+?)/\+esm", npm_path)
    if not m:
        raise ValueError(npm_path)
    pkg = m.group(1)
    # @scope/name@ver -> scope__name-ver
    return pkg.replace("/", "__").replace("@", "-", 1 if pkg.startswith("@") else 0).replace("@", "-") + ".mjs"


seen: set[str] = set()


def fetch_esm(npm_path: str, local_name: str | None = None) -> None:
    if npm_path in seen:
        return
    seen.add(npm_path)
    local_name = local_name or pkg_to_local(npm_path)
    dest = VENDOR / local_name
    if dest.exists() and dest.stat().st_size > 0:
        # Still extract its deps in case they need processing.
        raw = dest.read_text(encoding="utf-8")
    else:
        print(f"  -> vendor/{local_name}", end="", flush=True)
        raw = urllib.request.urlopen("https://cdn.jsdelivr.net" + npm_path, timeout=60).read().decode("utf-8")
        print(f"  ({len(raw)/1024:.1f} KB)")
    deps = set(re.findall(r'from\s*["\'](/npm/[^"\']+\+esm)["\']', raw))
    deps.update(re.findall(r'import\s*\(\s*["\'](/npm/[^"\']+\+esm)["\']\s*\)', raw))
    for dep in deps:
        local = pkg_to_local(dep)
        raw = raw.replace(dep, "./" + local)
    dest.write_text(raw, encoding="utf-8")
    for dep in deps:
        fetch_esm(dep)


fetch_esm(f"/npm/@duckdb/duckdb-wasm@{DV}/+esm", "duckdb-wasm.mjs")

# === Vega + Vega-Lite + Vega-Embed (UMD bundles, ~1 MB total) ===
# Used by the "Gràfiques" tab. UMD bundles are easier than ESM here
# because vega-embed wraps the other two and exposes a single global.
get("https://cdn.jsdelivr.net/npm/vega@5.30.0/build/vega.min.js",
    VENDOR / "vega.min.js")
get("https://cdn.jsdelivr.net/npm/vega-lite@5.21.0/build/vega-lite.min.js",
    VENDOR / "vega-lite.min.js")
get("https://cdn.jsdelivr.net/npm/vega-embed@6.26.0/build/vega-embed.min.js",
    VENDOR / "vega-embed.min.js")

print("\nDone. web/vendor/ contains every required library.")
print(f"Total: {sum(p.stat().st_size for p in VENDOR.rglob('*') if p.is_file()) / (1024*1024):.1f} MB")
