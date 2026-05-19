"""Detecta inconsistències a la BD del Nomenclàtor 1860.

Executa 8 comprovacions ordenades de més greu a anècdotic:

  A. Coherència interna de fila: HC+HT+Inh = P1+P2+P3+PM+Alb = total
  B. Σfiles d'un municipi vs la fila is_municipality_total
  C. Σmunis d'un partit vs la fila is_district_total
  D. Σentries vs Quadre 3 oficial (pàg. 50)
  E. Anomalies de NULL i zeros
  F. Files duplicades (page + muni + place)
  G. Errata: estat real (entries) vs flag 'applied'
  H. Estat de la normalització de class_normalized

Sortida: text formatat a stdout. Codi de retorn 0 sempre (és diagnòstic,
no validació estricta). Per a la validació estricta del pipeline d'ingesta
fes servir db/validate.py.

Ús:
    .venv/bin/python db/check_consistency.py
"""
from __future__ import annotations

from pathlib import Path
import duckdb

PROJECT = Path(__file__).resolve().parent.parent
DB = str(PROJECT / "db" / "nomenclator.duckdb")


def main() -> int:
    con = duckdb.connect(DB, read_only=True)

    # --- A ---
    print("=" * 76)
    print("A. Coherència interna de fila")
    print("=" * 76)
    bad_use = con.execute("""
        SELECT COUNT(*) FROM entries WHERE page != 50
          AND COALESCE(inhabited_permanent,0)+COALESCE(inhabited_seasonal,0)+COALESCE(uninhabited,0)
            != COALESCE(total,0)
    """).fetchone()[0]
    bad_flr = con.execute("""
        SELECT COUNT(*) FROM entries WHERE page != 50
          AND COALESCE(buildings_1_floor,0)+COALESCE(buildings_2_floors,0)
            +COALESCE(buildings_3_floors,0)+COALESCE(buildings_over_3_floors,0)
            +COALESCE(shelters,0) != COALESCE(total,0)
    """).fetchone()[0]
    n_total = con.execute("SELECT COUNT(*) FROM entries WHERE page != 50").fetchone()[0]
    print(f"  Files HC+HT+Inh != total     : {bad_use} / {n_total}")
    print(f"  Files P1+P2+P3+PM+Alb != total: {bad_flr} / {n_total}")

    # --- B ---
    print()
    print("=" * 76)
    print("B. Σfiles del municipi vs is_municipality_total")
    print("=" * 76)
    rows = con.execute("""
        WITH normals AS (
          SELECT judicial_district, municipality, SUM(total) AS sum_total
          FROM entries WHERE page != 50 AND NOT is_municipality_total AND NOT is_district_total
            AND municipality IS NOT NULL AND municipality != 'SUMMARY'
          GROUP BY 1, 2
        ),
        subs AS (
          SELECT judicial_district, municipality, total AS sub_total
          FROM entries WHERE is_municipality_total AND NOT is_district_total
        )
        SELECT n.judicial_district, n.municipality, n.sum_total, s.sub_total,
               (n.sum_total - s.sub_total) AS diff
        FROM normals n LEFT JOIN subs s USING (judicial_district, municipality)
        ORDER BY n.judicial_district, n.municipality
    """).fetchall()
    bad = [r for r in rows if r[4] != 0]
    print(f"  {len(rows) - len(bad)} / {len(rows)} municipis coincideixen exactes; {len(bad)} amb desviació")
    if bad:
        print(f"\n  {'Partit':<9} {'Municipi':<18} {'Σfiles':>7} {'Subt.':>6} {'Δ':>5}")
        for r in sorted(bad, key=lambda x: (-abs(x[4]), x[0], x[1])):
            print(f"    {r[0]:<9} {r[1]:<18} {r[2]:>7} {r[3]:>6} {r[4]:>+5}")

    # --- C ---
    print()
    print("=" * 76)
    print("C. Σmunis del partit vs is_district_total")
    print("=" * 76)
    for r in con.execute("""
        WITH ms AS (SELECT judicial_district, SUM(total) AS s FROM entries
                    WHERE is_municipality_total AND NOT is_district_total GROUP BY 1),
        ds AS (SELECT judicial_district, total AS d FROM entries WHERE is_district_total)
        SELECT m.judicial_district, m.s, d.d, m.s-d.d
        FROM ms m LEFT JOIN ds d USING(judicial_district) ORDER BY 1
    """).fetchall():
        flag = "✓" if r[3] == 0 else f"Δ={r[3]:+d}"
        print(f"  {r[0]:<10}: Σmunis={r[1]:>6,}  PJ={r[2]:>6,}  {flag}")

    # --- D ---
    print()
    print("=" * 76)
    print("D. Σentries vs Quadre 3 pàg.50 (Total edificios + Albergues)")
    print("=" * 76)
    edif = {r[0]: r[1] for r in con.execute("""
        SELECT judicial_district,
               SUM(buildings_1_floor+buildings_2_floors+buildings_3_floors+buildings_over_3_floors)
        FROM entries WHERE page!=50 AND NOT is_municipality_total AND NOT is_district_total
        GROUP BY 1
    """).fetchall()}
    alb = {r[0]: r[1] for r in con.execute("""
        SELECT judicial_district, SUM(shelters)
        FROM entries WHERE page!=50 AND NOT is_municipality_total AND NOT is_district_total
        GROUP BY 1
    """).fetchall()}
    ch3 = {}
    for r in con.execute("SELECT judicial_district, is_total, columns, values FROM summaries WHERE chart_num=3").fetchall():
        label = "TOTAL" if r[1] else r[0]
        cols, vals = r[2], r[3]
        ch3[label] = (vals[cols.index("Total edificios")], vals[cols.index("Albergues")])
    print(f"  {'PJ':<10} {'Σedif':>7} {'Ch3.E':>7} {'Δ':>4}  |  {'Σalb':>6} {'Ch3.A':>6} {'Δ':>4}")
    for k in ["Ibiza", "Inca", "Mahon", "Manacor", "Palma"]:
        e_db = edif.get(k, 0)
        a_db = alb.get(k, 0)
        e_ch, a_ch = ch3[k]
        print(f"  {k:<10} {e_db:>7,} {e_ch:>7,} {e_db-e_ch:>+4}  |  {a_db:>6,} {a_ch:>6,} {a_db-a_ch:>+4}")

    # --- E ---
    print()
    print("=" * 76)
    print("E. Anomalies de NULL i zeros")
    print("=" * 76)
    checks = [
        ("Files normals amb total=0",
         "SELECT COUNT(*) FROM entries WHERE NOT is_municipality_total AND NOT is_district_total AND page!=50 AND total=0"),
        ("Files normals amb total NULL",
         "SELECT COUNT(*) FROM entries WHERE NOT is_municipality_total AND NOT is_district_total AND page!=50 AND total IS NULL"),
        ("Files amb place_class NULL",
         "SELECT COUNT(*) FROM entries WHERE place_class IS NULL AND NOT is_municipality_total AND NOT is_district_total AND page!=50"),
        ("Files amb class_normalized NULL",
         "SELECT COUNT(*) FROM entries WHERE class_normalized IS NULL AND NOT is_municipality_total AND NOT is_district_total AND page!=50"),
        ("Files amb distance_km NULL",
         "SELECT COUNT(*) FROM entries WHERE distance_km IS NULL AND NOT is_municipality_total AND NOT is_district_total AND page!=50"),
        ("Files amb municipality NULL",
         "SELECT COUNT(*) FROM entries WHERE municipality IS NULL"),
    ]
    for label, sql in checks:
        n = con.execute(sql).fetchone()[0]
        print(f"  {label:<35}: {n}")
    print(f"  {'Files amb note_ref no-NULL':<35}: {con.execute('SELECT COUNT(*) FROM entries WHERE note_ref IS NOT NULL').fetchone()[0]}")
    print(f"  {'Notes a la taula notes':<35}: {con.execute('SELECT COUNT(*) FROM notes').fetchone()[0]}")

    # --- F ---
    print()
    print("=" * 76)
    print("F. Files duplicades (mateix page + muni + place)")
    print("=" * 76)
    dups = con.execute("""
        SELECT page, municipality, place, COUNT(*) AS n
        FROM entries WHERE NOT is_municipality_total AND NOT is_district_total
        GROUP BY 1,2,3 HAVING COUNT(*) > 1 ORDER BY n DESC, page
    """).fetchall()
    if not dups:
        print("  (cap)")
    else:
        for r in dups:
            print(f"  pàg {r[0]:>2} | {r[1]:<12} | {r[2]!r} ×{r[3]}")
        print("  (sovint són noms reals repetits amb classes diferents — vegeu detall a la BD)")

    # --- G ---
    print()
    print("=" * 76)
    print("G. Errata: estat real (entries) vs flag 'applied'")
    print("=" * 76)
    n_app_real = 0
    n_app_flag = 0
    for r in con.execute("SELECT page_pdf, municipality, says_db, should_say, applied FROM errata ORDER BY page_pdf").fetchall():
        page, muni, says, should, applied = r
        n_old = con.execute("SELECT COUNT(*) FROM entries WHERE page=? AND place=?", [page, says]).fetchone()[0]
        n_new = con.execute("SELECT COUNT(*) FROM entries WHERE page=? AND place=?", [page, should]).fetchone()[0]
        real = (n_old == 0 and n_new >= 1)
        n_app_real += int(real)
        n_app_flag += int(applied)
        ok_flag = "OK" if applied == real else "??"
        print(f"  flag={str(applied):<5} real={str(real):<5} [{ok_flag}] pàg {page} {muni}: {says!r} -> {should!r}")
    print(f"\n  Resum: {n_app_real} aplicades realment · {n_app_flag} marcades amb flag")
    if n_app_real != n_app_flag:
        print(f"  ⚠️  Discrepància {n_app_real - n_app_flag} files: el flag applied no reflecteix l'estat real.")

    # --- H ---
    print()
    print("=" * 76)
    print("H. Normalització de class_normalized")
    print("=" * 76)
    n_total = con.execute("""
        SELECT COUNT(*) FROM entries
        WHERE place_class IS NOT NULL AND NOT is_municipality_total AND NOT is_district_total AND page!=50
    """).fetchone()[0]
    n_null = con.execute("""
        SELECT COUNT(*) FROM entries
        WHERE place_class IS NOT NULL AND class_normalized IS NULL
          AND NOT is_municipality_total AND NOT is_district_total AND page!=50
    """).fetchone()[0]
    print(f"  Files amb place_class no-NULL: {n_total}")
    print(f"  Files class_normalized NULL  : {n_null} ({100*n_null/n_total:.1f}%)")
    ambig = con.execute("""
        SELECT place_class,
               SUM(CASE WHEN class_normalized IS NULL THEN 1 ELSE 0 END) AS null_n,
               SUM(CASE WHEN class_normalized IS NOT NULL THEN 1 ELSE 0 END) AS notnull_n
        FROM entries WHERE place_class IS NOT NULL
          AND NOT is_municipality_total AND NOT is_district_total AND page!=50
        GROUP BY 1
        HAVING null_n > 0 AND notnull_n > 0
        ORDER BY null_n DESC LIMIT 10
    """).fetchall()
    if ambig:
        print("\n  ⚠️  Classes ambigues (mateix place_class, alguns normalitzats i altres no):")
        print(f"  {'null':>5} {'notnull':>7}  place_class")
        for r in ambig:
            print(f"  {r[1]:>5} {r[2]:>7}  {r[0]!r}")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
