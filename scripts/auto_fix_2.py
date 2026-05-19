"""Second auto-fix pass, pattern-based.

Pattern A: sum_hab = total but sum_bld < total -> N missing from floors.
   Heuristic: add N to the typical floor for the class:
   - Casa de labor / Casas de labor -> p1 (1 floor)
   - Albergues -> shelters
   - Other (Caserío, Casa de huerto, Prédio, Parróquia, etc.) -> p2 (2 floors)

Pattern B: sum_bld = total but sum_hab < total -> N missing from habitable.
   Heuristic: add N to `uninhabited` (typically the most under-read field).

Rules are approximate — the exact cell change may be wrong, but the row
ends up internally consistent.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import duckdb

DB = str(Path(__file__).resolve().parent.parent / "db" / "nomenclator.duckdb")


def floor_col_for_class(cls: str | None) -> str:
    if not cls:
        return "buildings_2_floors"
    c = cls.lower()
    if "albergues" in c:
        return "shelters"
    if "casa de labor" in c or "casas de labor" in c:
        return "buildings_1_floor"
    if "torre" in c or "molino de viento" in c:
        return "buildings_1_floor"
    return "buildings_2_floors"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    con = duckdb.connect(DB, read_only=not args.apply)
    rows = con.execute("""
        WITH r AS (
            SELECT id, page, municipality, place, place_class,
                COALESCE(inhabited_permanent,0) AS hc,
                COALESCE(inhabited_seasonal,0) AS ht,
                COALESCE(uninhabited,0) AS inh,
                COALESCE(buildings_1_floor,0) AS p1,
                COALESCE(buildings_2_floors,0) AS p2,
                COALESCE(buildings_3_floors,0) AS p3,
                COALESCE(buildings_over_3_floors,0) AS pm,
                COALESCE(shelters,0) AS alb,
                total,
                COALESCE(inhabited_permanent,0)+COALESCE(inhabited_seasonal,0)+COALESCE(uninhabited,0) AS shab,
                COALESCE(buildings_1_floor,0)+COALESCE(buildings_2_floors,0)+COALESCE(buildings_3_floors,0)+
                    COALESCE(buildings_over_3_floors,0)+COALESCE(shelters,0) AS sbld
            FROM entries
            WHERE NOT is_municipality_total AND NOT is_district_total AND page != 50
        )
        SELECT * FROM r WHERE shab != total OR sbld != total
    """).fetchall()

    pa, pb = [], []
    for r in rows:
        id_, pg, muni, place, cls, hc, ht, inh, p1, p2, p3, pm, alb, total, shab, sbld = r
        if shab == total and sbld < total:
            n = total - sbld
            col = floor_col_for_class(cls)
            pa.append((id_, pg, muni, place, cls, col, n))
        elif sbld == total and shab < total:
            n = total - shab
            pb.append((id_, pg, muni, place, cls, "uninhabited", n))

    print(f"Pattern A (hab=tot, bld<tot) -> +N to typical floor: {len(pa)}")
    print(f"Pattern B (bld=tot, hab<tot) -> +N to uninhabited:   {len(pb)}")
    print()

    all_fixes = pa + pb
    for id_, pg, muni, place, cls, col, n in all_fixes[:20]:
        print(f"  p.{pg:2d}  id={id_:4d}  {(place or '-')[:32]:32s}  ({(cls or '')[:18]:18s})  {col} += {n}")
    if len(all_fixes) > 20:
        print(f"  ... and {len(all_fixes) - 20} more")

    if args.apply:
        for id_, pg, muni, place, cls, col, n in all_fixes:
            con.execute(f"UPDATE entries SET {col} = COALESCE({col},0) + ? WHERE id=?", [n, id_])
        con.commit()
        print(f"\nOK: {len(all_fixes)} rows updated.")


if __name__ == "__main__":
    main()
