"""Validate the 1860 Nomenclator data.

For each municipality with a subtotal row:
  (1) Sum the detail rows and compare against the PDF's printed subtotal.
  (2) Check internal consistency of the PDF subtotal:
      total == p1+p2+p3+pmas + shelters   (buildings side)
      total == hc + ht + inh              (occupancy side)
      If both sides yield the same total, the PDF subtotal is internally
      coherent. Otherwise the PDF subtotal itself has an arithmetic error
      from 1860.

Discrepancies are classified as:
  - TRANSCRIPTION: our sums match neither side of an internally coherent
    PDF subtotal.
  - PDF DEFECT: our sums match one side but the PDF subtotal is internally
    inconsistent.
"""
import sys
from pathlib import Path

import duckdb

DB = str(Path(__file__).resolve().parent.parent / "db" / "nomenclator.duckdb")

FIELDS = [
    "inhabited_permanent",
    "inhabited_seasonal",
    "uninhabited",
    "buildings_1_floor",
    "buildings_2_floors",
    "buildings_3_floors",
    "buildings_over_3_floors",
    "shelters",
    "total",
]


def validate():
    con = duckdb.connect(DB, read_only=True)
    sum_cols = ", ".join(f"SUM({c}) AS {c}" for c in FIELDS)

    sums = {
        row[0]: dict(zip(FIELDS, row[1:]))
        for row in con.execute(f"""
            SELECT municipality, {sum_cols}
            FROM entries
            WHERE NOT is_municipality_total
            GROUP BY municipality
        """).fetchall()
    }
    cols_sel = ", ".join(FIELDS)
    totals = {
        row[0]: dict(zip(FIELDS, row[1:]))
        for row in con.execute(f"""
            SELECT municipality, {cols_sel}
            FROM entries WHERE is_municipality_total
        """).fetchall()
    }

    transcription_errs = []
    pdf_errs = []
    ok = []
    no_total = []

    for muni, suma in sums.items():
        if muni not in totals:
            no_total.append(muni)
            continue
        pdf = totals[muni]

        side_habitable = pdf["inhabited_permanent"] + pdf["inhabited_seasonal"] + pdf["uninhabited"]
        side_buildings = (pdf["buildings_1_floor"] + pdf["buildings_2_floors"] +
                          pdf["buildings_3_floors"] + pdf["buildings_over_3_floors"] + pdf["shelters"])
        pdf_coherent = (side_habitable == side_buildings == pdf["total"])

        diffs = {c: (suma[c], pdf[c]) for c in FIELDS if suma[c] != pdf[c]}
        if not diffs:
            ok.append(muni)
        elif not pdf_coherent:
            pdf_errs.append((muni, diffs, side_habitable, side_buildings, pdf["total"]))
        else:
            transcription_errs.append((muni, diffs))

    print(f"\nVALIDATION ({len(sums)} municipalities analyzed)")
    print("=" * 70)

    if ok:
        print(f"\nOK ({len(ok)}):")
        for a in ok:
            print(f"    - {a}")

    if pdf_errs:
        print(f"\nPDF subtotal inconsistent — likely 1860 arithmetic error ({len(pdf_errs)}):")
        for muni, diffs, hab, edif, tot in pdf_errs:
            print(f"    - {muni}:")
            print(f"        PDF subtotal sides: hc+ht+inh={hab}, p+alb={edif}, printed total={tot}")
            for c, (s, p) in diffs.items():
                sign = "+" if s > p else ""
                print(f"        {c:30s} our_sum={s}, pdf={p}, diff={sign}{s - p}")

    if transcription_errs:
        print(f"\nTranscription errors to fix ({len(transcription_errs)}):")
        for muni, diffs in transcription_errs:
            print(f"    - {muni}:")
            for c, (s, p) in diffs.items():
                sign = "+" if s > p else ""
                print(f"        {c:30s} our_sum={s}, pdf={p}, diff={sign}{s - p}")

    if no_total:
        print(f"\nNo subtotal yet in DB ({len(no_total)} — continues on later page):")
        for a in no_total:
            print(f"    - {a}")

    return 0 if not transcription_errs else 1


if __name__ == "__main__":
    sys.exit(validate())
