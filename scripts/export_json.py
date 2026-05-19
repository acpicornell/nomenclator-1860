"""Exporta les taules de la BD a JSON estàtic per al web.

Aquest substitueix els parquets per JSON: el web no necessita DuckDB-WASM
al runtime, només `fetch()` + filtrat en JS. La pipeline Python segueix
fent servir DuckDB internament.

Ús:
    .venv/bin/python scripts/export_json.py
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import duckdb

PROJECT = Path(__file__).resolve().parent.parent
DB = str(PROJECT / "db" / "nomenclator.duckdb")
DATA_DIR = PROJECT / "web" / "data"


# (taula, filtre opcional)
TABLES: list[tuple[str, str]] = [
    ("entries", "WHERE page != 50"),  # excloem pàg.50 (quadres-resum)
    ("notes", ""),
    ("summaries", ""),
    ("errata", ""),
    ("source_metadata", ""),
]


def _default(o):
    """JSON encoder per a tipus que el módul standard no maneja."""
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"No serializable: {type(o)}")


def export_table(con: duckdb.DuckDBPyConnection, name: str, where: str) -> tuple[Path, int]:
    sql = f"SELECT * FROM {name} {where}".strip()
    rows = con.execute(sql).fetchall()
    cols = [d[0] for d in con.description]
    out = [dict(zip(cols, r)) for r in rows]
    path = DATA_DIR / f"{name}.json"
    # separators sense espais → ~15% més petit que el format pretty
    path.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":"), default=_default)
    )
    return path, len(out)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB, read_only=True)
    print(f"Exportant taules a {DATA_DIR.relative_to(PROJECT)}/")
    total_kb = 0
    for name, where in TABLES:
        path, n = export_table(con, name, where)
        size_kb = path.stat().st_size // 1024
        total_kb += size_kb
        print(f"  {name}.json:  {n:>5,} files · {size_kb:>5} KB")
    print(f"\nTotal: {total_kb} KB sense gzip")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
