"""Load Claude API HTML output into DuckDB.

Reads output/claude_api/page*.html, parses each <tr>, validates the
13-cell structure, and replaces the corresponding rows in the `entries`
table. Also picks up footnotes <p class="nota" ref="X">.

Conventions:
  - "»" in the original -> 0 in numeric columns.
  - Distance "9'3" -> 9.3 ; empty / "»" -> NULL.
  - Municipality is inferred from cell 1 of each <tr>.

Usage:
    .venv/bin/python scripts/load_claude_output.py             # load all (3-51)
    .venv/bin/python scripts/load_claude_output.py --pages 3 4 5
    .venv/bin/python scripts/load_claude_output.py --dry-run   # report only
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import duckdb

PROJECT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT / "output" / "claude_api"
DB = PROJECT / "db" / "nomenclator.duckdb"

# Inhabitants per municipality, parsed from page headers
# (e.g., "FORMENTERA (b). (1.684 habitantes)."). Optional.
MUNI_INHABITANTS: dict[str, int] = {}


def parse_distance(s: str) -> float | None:
    s = s.strip()
    if not s or s == "»":
        return None
    s = s.replace("'", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_int(s: str) -> int:
    """Handle the European thousands separator (1.062 = 1062) and » = 0."""
    s = s.strip()
    if s in ("», ", "»", "", "0"):
        return 0
    # Strip European thousands separator. "1.062" -> "1062".
    # Distances use ' (apostrophe), not '.', so this doesn't conflict.
    s_clean = s.replace(".", "")
    try:
        return int(s_clean)
    except ValueError:
        if "»" in s:
            return 0
        try:
            return int(float(s_clean))
        except ValueError:
            return 0


def parse_html(html: str, page: int) -> tuple[list[dict], list[dict]]:
    """Return (entries, notes)."""
    entries = []
    for tr in re.finditer(r"<tr([^>]*)>(.*?)</tr>", html, re.DOTALL):
        attrs = tr.group(1)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr.group(2), re.DOTALL)
        if len(cells) != 13:
            continue
        nota_match = re.search(r'nota\s*=\s*"([^"]+)"', attrs)
        note = nota_match.group(1) if nota_match else None
        muni = cells[0].strip()
        place = cells[1].strip()
        cls = cells[2].strip() or None
        km = parse_distance(cells[3])
        is_muni_total = place.startswith("TOTAL ") and not muni
        is_district_total = "PARTIDO" in place.upper() and "TOTAL" in place.upper()

        entries.append({
            "page": page,
            "municipality": muni if muni else None,
            "place": place,
            "place_class": cls,
            "distance_km": km,
            "inhabited_permanent": parse_int(cells[4]),
            "inhabited_seasonal": parse_int(cells[5]),
            "uninhabited": parse_int(cells[6]),
            "buildings_1_floor": parse_int(cells[7]),
            "buildings_2_floors": parse_int(cells[8]),
            "buildings_3_floors": parse_int(cells[9]),
            "buildings_over_3_floors": parse_int(cells[10]),
            "shelters": parse_int(cells[11]),
            "total": parse_int(cells[12]),
            "note_ref": note,
            "is_municipality_total": is_muni_total,
            "is_district_total": is_district_total,
        })

    notes = []
    for p in re.finditer(r'<p class="nota"[^>]*ref="([^"]+)"[^>]*>(.*?)</p>', html, re.DOTALL):
        notes.append({
            "page": page,
            "ref": p.group(1).strip(),
            "text": p.group(2).strip(),
        })

    return entries, notes


def infer_judicial_district(page: int) -> str | None:
    """Approximate district by page range. Not exact when a page straddles
    two districts (e.g., page 25 mixes the end of Mahon with the start of
    Manacor). Run scripts/fix_judicial_district.py after loading to fix
    those rows using is_district_total markers."""
    if page <= 6:
        return "Ibiza"
    if page <= 20:
        return "Inca"
    if page <= 25:
        return "Mahon"
    if page <= 35:
        return "Manacor"
    return "Palma"


def load_page(con: duckdb.DuckDBPyConnection, page: int, dry_run: bool = False) -> tuple[int, int]:
    html_path = OUT_DIR / f"page{page:04d}.html"
    if not html_path.exists():
        return 0, 0
    html = html_path.read_text(encoding="utf-8")
    entries, notes = parse_html(html, page)
    if dry_run:
        return len(entries), len(notes)

    con.execute("DELETE FROM entries WHERE page = ?", [page])
    con.execute("DELETE FROM notes WHERE page = ?", [page])

    rows = [
        (
            f["page"],
            infer_judicial_district(page),
            f["municipality"],
            MUNI_INHABITANTS.get(f["municipality"] or "", None),
            f["place"],
            f["place_class"],
            f["distance_km"],
            f["inhabited_permanent"],
            f["inhabited_seasonal"],
            f["uninhabited"],
            f["buildings_1_floor"],
            f["buildings_2_floors"],
            f["buildings_3_floors"],
            f["buildings_over_3_floors"],
            f["shelters"],
            f["total"],
            f["note_ref"],
            f["is_municipality_total"],
            False,
            f["is_district_total"],
        )
        for f in entries
    ]
    if rows:
        con.executemany(
            """INSERT INTO entries (
                page, judicial_district, municipality, municipality_inhabitants,
                place, place_class, distance_km,
                inhabited_permanent, inhabited_seasonal, uninhabited,
                buildings_1_floor, buildings_2_floors, buildings_3_floors, buildings_over_3_floors,
                shelters, total, note_ref,
                is_municipality_total, highlighted, is_district_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )

    if notes:
        # Find the municipality owning each note: the first row on this page
        # with a matching note_ref gives us the municipality (approximate).
        note_rows = []
        for n in notes:
            muni = next(
                (f["municipality"] for f in entries if f["note_ref"] == n["ref"]),
                None,
            )
            note_rows.append((n["page"], n["ref"], n["text"], muni))
        con.executemany(
            "INSERT INTO notes (page, ref, text, municipality) VALUES (?, ?, ?, ?)",
            note_rows,
        )

    con.commit()
    return len(entries), len(notes)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pages", nargs="*", type=int, help="specific pages")
    p.add_argument("--range", dest="range_", help="closed range, e.g. 3-51")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.pages:
        pages = sorted(args.pages)
    elif args.range_:
        lo, hi = args.range_.split("-")
        pages = list(range(int(lo), int(hi) + 1))
    else:
        pages = sorted(int(f.stem.removeprefix("page")) for f in OUT_DIR.glob("page*.html"))

    con = duckdb.connect(str(DB))

    total_f = total_n = 0
    for pg in pages:
        nf, nn = load_page(con, pg, dry_run=args.dry_run)
        action = "[dry-run]" if args.dry_run else ""
        print(f"p.{pg}: {nf} rows, {nn} notes {action}")
        total_f += nf
        total_n += nn

    print(f"\nTotal: {total_f} rows, {total_n} notes in {len(pages)} pages")
    if args.dry_run:
        print("(DB was not modified)")


if __name__ == "__main__":
    main()
