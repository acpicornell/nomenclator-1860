"""Re-assign entries.judicial_district using the TOTAL PARTIDO markers.

The loader's `infer_judicial_district` decides district by page range,
which is wrong when a page straddles two districts: it collapses Mahon
(Menorca) inside Manacor, and duplicates ALARÓ between Ibiza/Inca and
ALGÁIDA between Manacor/Palma.

This script walks the rows in order (page, id), starts with "Ibiza" and
advances to the next district every time it sees an `is_district_total`
row. The order Ibiza -> Inca -> Mahon -> Manacor -> Palma is confirmed
by page 50 (Cuadros 1-4 list the 5 districts in that order).
"""
from __future__ import annotations

from pathlib import Path

import duckdb

DB = Path(__file__).resolve().parent.parent / "db" / "nomenclator.duckdb"
ORDER = ["Ibiza", "Inca", "Mahon", "Manacor", "Palma"]


def main() -> None:
    con = duckdb.connect(str(DB))

    rows = con.execute("""
        SELECT id, page, municipality, place, is_district_total, judicial_district
        FROM entries ORDER BY page, id
    """).fetchall()

    idx = 0
    updates: list[tuple[str, int]] = []
    changes_per_district = {p: 0 for p in ORDER}
    count_totals = 0

    for row_id, page, muni, place, is_total, current in rows:
        new_district = ORDER[idx] if idx < len(ORDER) else ORDER[-1]
        if new_district != current:
            updates.append((new_district, row_id))
            changes_per_district[new_district] += 1
        if is_total:
            count_totals += 1
            idx += 1

    print(f"Rows analyzed: {len(rows)}")
    print(f"TOTAL PARTIDO markers found: {count_totals} (expected 5)")
    print(f"Rows to update: {len(updates)}")
    for p, n in changes_per_district.items():
        print(f"  -> {p:10}: +{n} rows")

    if count_totals != 5:
        print("\nAbort: marker count != 5, refusing to corrupt the DB.")
        return

    con.executemany("UPDATE entries SET judicial_district = ? WHERE id = ?", updates)
    con.commit()

    print("\n=== Final distribution ===")
    for r in con.execute("""
        SELECT judicial_district, COUNT(*) AS n_rows,
               COUNT(DISTINCT municipality) AS n_munis
        FROM entries WHERE judicial_district IS NOT NULL
        GROUP BY judicial_district ORDER BY judicial_district
    """).fetchall():
        print(f"  {r[0]:10}  {r[1]:>4} rows, {r[2]:>2} municipalities")

    duplicates = con.execute("""
        SELECT municipality, COUNT(DISTINCT judicial_district) AS n
        FROM entries WHERE municipality IS NOT NULL
        GROUP BY municipality HAVING n > 1
    """).fetchall()
    if duplicates:
        print(f"\nWARNING: municipalities in >1 district after fix: {duplicates}")
    else:
        print("\nOK: each municipality belongs to a single district.")


if __name__ == "__main__":
    main()
