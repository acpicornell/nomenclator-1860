"""Orquestrador de reconstrucció del Nomenclàtor de 1860.

Ús
==

    .venv/bin/python scripts/rebuild.py
        Tots els passos no-cars: load_claude_output → validacions → auto_fix
        → apply_errata. NO re-extreu el PDF amb Claude.

    .venv/bin/python scripts/rebuild.py --include-expensive
        Inclou la re-extracció amb Claude vision (~10 USD). Cal
        ANTHROPIC_API_KEY a .env.

    .venv/bin/python scripts/rebuild.py --json
        Només re-exportar els JSON estàtics a web/data/ (no toca la BD).

    .venv/bin/python scripts/rebuild.py --seed
        Només estampar source_metadata amb l'estat actual i re-exportar
        els JSON. Útil quan la BD ja és bona però volem refrescar la
        marca "actualitzat fa X".
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "db" / "nomenclator.duckdb"
SCHEMA = PROJECT / "db" / "schema.sql"
PYTHON = str(PROJECT / ".venv" / "bin" / "python")


# Cada pas: (camí_relatiu, args, expensive).
#   expensive=True s'omet per defecte i només corre amb --include-expensive.
STEPS: list[tuple[str, list[str], bool]] = [
    ("scripts/extract_with_claude.py", ["--range", "4-51"], True),
    ("scripts/load_claude_output.py", [], False),
    ("db/validate.py", [], False),
    ("db/validate_rows.py", [], False),
    ("scripts/auto_fix.py", ["--apply"], False),
    ("scripts/auto_fix_2.py", ["--apply"], False),
    ("scripts/apply_errata_and_summaries.py", [], False),
]

NOTES = "PDF INE 1860 + Claude vision; 100% coherència aritmètica"


def _ensure_schema() -> None:
    con = duckdb.connect(str(DB))
    con.execute(SCHEMA.read_text())
    con.close()


def _run_step(script_rel: str, args: list[str]) -> None:
    cmd = [PYTHON, str(PROJECT / script_rel), *args]
    print(f"  ▸ {shlex.join([script_rel, *args])}")
    t0 = time.monotonic()
    r = subprocess.run(cmd, cwd=PROJECT)
    dt = time.monotonic() - t0
    if r.returncode != 0:
        raise SystemExit(f"FAIL: {script_rel} (codi {r.returncode})")
    print(f"    {dt:.1f}s")


def _write_metadata(scripts_ran: list[str]) -> int:
    """Stamp source_metadata amb el row count actual i els scripts executats.

    El timestamp s'emmagatzema en UTC explícit (naïve); export_json.py
    el serialitza com a ISO 8601 i el navegador el parseja amb `new Date()`.
    """
    con = duckdb.connect(str(DB))
    n = con.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    con.execute(
        """INSERT OR REPLACE INTO source_metadata
           (source_name, fetched_at, n_rows, scripts, notes)
           VALUES (?, ?, ?, ?, ?)""",
        ["1860", now_utc, n, ", ".join(scripts_ran), NOTES],
    )
    con.close()
    return n


def _export_json() -> None:
    """Delega a scripts/export_json.py — converteix DuckDB → JSON."""
    cmd = [PYTHON, str(PROJECT / "scripts" / "export_json.py")]
    r = subprocess.run(cmd, cwd=PROJECT)
    if r.returncode != 0:
        raise SystemExit(f"FAIL: export_json.py (codi {r.returncode})")


def run_all(include_expensive: bool) -> None:
    print("\n=== Reconstruint Nomenclàtor 1860 ===")
    ran: list[str] = []
    for script_rel, args, expensive in STEPS:
        if expensive and not include_expensive:
            print(f"  ◌ {script_rel} (car — passa --include-expensive)")
            continue
        _run_step(script_rel, args)
        ran.append(script_rel)
    if not ran:
        print("  cap pas executat")
        return
    n = _write_metadata(ran)
    print(f"  ✓ 1860: {n} files al final · {NOTES}")


def seed_metadata() -> None:
    """Stamp source_metadata per a l'estat actual sense re-executar res."""
    print("Seeding source_metadata (sense re-executar scripts)…")
    try:
        n = _write_metadata([s[0] for s in STEPS])
        print(f"  ✓ 1860: {n} files")
    except duckdb.CatalogException:
        print("  ◌ taula 'entries' buida o no existent, saltat")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Orquestrador per a reconstruir la BD del Nomenclàtor 1860"
    )
    p.add_argument(
        "--json", action="store_true",
        help="Només re-exportar JSON estàtics a web/data/ (no toca la BD)",
    )
    p.add_argument(
        "--seed", action="store_true",
        help="Només estampar source_metadata amb l'estat actual",
    )
    p.add_argument(
        "--include-expensive", action="store_true",
        help="Inclou re-extracció amb Claude vision (~10 USD)",
    )
    args = p.parse_args()

    _ensure_schema()

    if args.json:
        print("=== Re-exportant JSON ===")
        _export_json()
        return 0

    if args.seed:
        seed_metadata()
        print("\n=== Re-exportant JSON ===")
        _export_json()
        return 0

    run_all(args.include_expensive)
    print("\n=== Re-exportant JSON ===")
    _export_json()
    return 0


if __name__ == "__main__":
    sys.exit(main())
