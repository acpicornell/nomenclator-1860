"""Auto-fix frequent errors detected by validate_rows.

Conservative rules — only applied if the row ends up internally consistent
after the change:

1. If hab_sum == bld_sum != total -> set total to hab_sum.
   (Typical case: Claude misread only the last cell.)

Shows the rows it would touch and optionally applies them.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import duckdb

DB = str(Path(__file__).resolve().parent.parent / "db" / "nomenclator.duckdb")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="apply changes (without --apply just shows them)")
    args = p.parse_args()

    con = duckdb.connect(DB, read_only=not args.apply)

    rows = con.execute("""
        WITH r AS (
            SELECT id, page, municipality, place, total,
                COALESCE(inhabited_permanent,0) + COALESCE(inhabited_seasonal,0) + COALESCE(uninhabited,0) AS sum_hab,
                COALESCE(buildings_1_floor,0) + COALESCE(buildings_2_floors,0) + COALESCE(buildings_3_floors,0) +
                    COALESCE(buildings_over_3_floors,0) + COALESCE(shelters,0) AS sum_bld
            FROM entries
            WHERE NOT is_municipality_total AND NOT is_district_total AND page != 50
        )
        SELECT id, page, municipality, place, total, sum_hab, sum_bld
        FROM r
        WHERE sum_hab = sum_bld AND sum_hab != total
    """).fetchall()

    if not rows:
        print("No rows match the 'hab=bld != total' rule.")
        return

    print(f"\nAuto-fixable rows ({len(rows)}): sum_hab = sum_bld != total")
    print("Replacing total with sum_hab (==sum_bld):")
    print()
    for r in rows[:30]:
        id_, pg, muni, place, tot, suma, _ = r
        print(f"  id={id_:4d}  p.{pg:2d}  {muni[:14]:14s}  {place[:32]:32s}  tot {tot:4d} -> {suma}")
    if len(rows) > 30:
        print(f"  ... and {len(rows) - 30} more")

    if args.apply:
        print("\nApplying changes...")
        for r in rows:
            id_, pg, muni, place, tot, suma, _ = r
            con.execute("UPDATE entries SET total = ? WHERE id = ?", [suma, id_])
        con.commit()
        print(f"OK: {len(rows)} rows updated.")
    else:
        print("\n(dry-run) Pass --apply to write changes.")


if __name__ == "__main__":
    main()
