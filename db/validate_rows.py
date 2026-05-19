"""Validate each individual row's internal arithmetic.

Detects rows where either side of the count fails to match `total`:
  - inhabited_permanent + inhabited_seasonal + uninhabited != total
  - buildings_1_floor + ... + buildings_over_3_floors + shelters != total

These are the rows worth fixing by hand because the data's own arithmetic
says something is wrong.

Rows where both sums match `total` are self-consistent — they may still
have column-misinterpretation errors (e.g., p1 vs p2) but those don't
break any subtotal.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import duckdb

DB = str(Path(__file__).resolve().parent.parent / "db" / "nomenclator.duckdb")


def validate_rows() -> None:
    con = duckdb.connect(DB, read_only=True)
    rows = con.execute("""
        SELECT
            id, page, municipality, place, place_class,
            inhabited_permanent AS hc,
            inhabited_seasonal AS ht,
            uninhabited AS inh,
            buildings_1_floor AS p1,
            buildings_2_floors AS p2,
            buildings_3_floors AS p3,
            buildings_over_3_floors AS pm,
            shelters AS alb,
            total
        FROM entries
        WHERE NOT is_municipality_total AND NOT is_district_total
    """).fetchall()

    broken = []
    for r in rows:
        id_, pg, muni, place, cls, hc, ht, inh, p1, p2, p3, pm, alb, total = r
        sum_hab = (hc or 0) + (ht or 0) + (inh or 0)
        sum_bld = (p1 or 0) + (p2 or 0) + (p3 or 0) + (pm or 0) + (alb or 0)
        if sum_hab != total or sum_bld != total:
            broken.append({
                "id": id_, "page": pg, "muni": muni, "place": place,
                "class": cls, "hc": hc, "ht": ht, "inh": inh,
                "p1": p1, "p2": p2, "p3": p3, "pm": pm, "alb": alb,
                "total": total,
                "sum_hab": sum_hab, "sum_bld": sum_bld,
                "diff_hab": sum_hab - total,
                "diff_bld": sum_bld - total,
            })

    print(f"\nTotal detail rows: {len(rows)}")
    print(f"Rows with broken arithmetic: {len(broken)} ({100*len(broken)/max(len(rows),1):.1f}%)")
    print()

    if broken:
        print("ROWS TO REVIEW MANUALLY:")
        print("=" * 100)
        by_page = defaultdict(list)
        for r in broken:
            by_page[r["page"]].append(r)
        for pg in sorted(by_page):
            print(f"\n--- page {pg} ({len(by_page[pg])} rows) ---")
            for r in by_page[pg]:
                problems = []
                if r["diff_hab"] != 0:
                    sign = "+" if r["diff_hab"] > 0 else ""
                    problems.append(f"hab{sign}{r['diff_hab']}")
                if r["diff_bld"] != 0:
                    sign = "+" if r["diff_bld"] > 0 else ""
                    problems.append(f"bld{sign}{r['diff_bld']}")
                print(
                    f"  id={r['id']:4d}  {r['muni'][:18] if r['muni'] else '-':18s} "
                    f"{(r['place'] or '-')[:32]:32s} "
                    f"{r['class'][:14] if r['class'] else '-':14s} "
                    f"| {r['hc']:>3}+{r['ht']:>2}+{r['inh']:>3}={r['sum_hab']:>3} "
                    f"| {r['p1']:>3}+{r['p2']:>3}+{r['p3']:>2}+{r['pm']:>1}+{r['alb']:>3}={r['sum_bld']:>3} "
                    f"| tot={r['total']:>3}  [{','.join(problems)}]"
                )


if __name__ == "__main__":
    validate_rows()
