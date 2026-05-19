"""Migration: split page 50 (summary charts) and apply the errata sheet.

- Page 50 of the PDF contains 4 summary charts per judicial district, not
  per municipality. Stored in a separate `summaries` table with values as
  an INT[] array. Values are re-parsed directly from the HTML to avoid
  the precision loss the original loader had (it treated "1.051" as a
  float).

- Page 51 contains an errata sheet. Stored in an `errata` table; the 8
  corrections are also applied to `entries.place`.

Idempotent: prior data is wiped before re-inserting.
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "db" / "nomenclator.duckdb"
HTML_50 = PROJECT / "output" / "claude_api" / "page0050.html"


# Column headers for each chart, derived from the PDF and verified against
# the footnotes on page 50. Used to label the `values` array.
CHARTS = {
    1: {
        "title": "Poblaciones y grupos",
        "columns": ["Ciudades", "Villas", "Lugares", "Aldéas",
                    "Caseríos", "Grupos", "Total"],
    },
    2: {
        "title": "Entidades aisladas",
        "columns": ["Casas", "Albergues", "Sítios", "Total"],
    },
    3: {
        "title": "Edificios por construcción",
        "columns": ["P1 poblado", "P2 poblado", "P3 poblado",
                    "P1 despoblado", "P2 despoblado", "P3 despoblado",
                    "P>3 poblado", "P>3 despoblado",
                    "Total edificios", "Albergues"],
    },
    4: {
        "title": "Edificios y albergues por habitación",
        "columns": ["Edif. hab. constante", "Edif. hab. temporal",
                    "Edif. inhab.", "Alb. hab. constante",
                    "Alb. hab. temporal", "Alb. inhab.", "Total"],
    },
}

# The 8 confirmed errata, mapped to page/municipality/place in the DB.
# `says_db` is what currently sits in the DB (Claude sometimes transcribed
# them "half-corrected": e.g. Clapar -> Ciapar, Báix -> Báig).
ERRATA = [
    {"page": 4,  "municipality": "SAN ANTÓNIO ABAD",
     "says_db": "Rolas (novales) (Las)",
     "should_say": "Rotas (novales) (Las)",
     "says_original": "Rolas (novales) (Las)"},
    {"page": 9,  "municipality": "COSTITX",
     "says_db": "Fornets",
     "should_say": "Jornets",
     "says_original": "Fornets"},
    {"page": 25, "municipality": "ARTÁ",
     "says_db": "Ciapar (El)",
     "should_say": "Claper (El)",
     "says_original": "Clapar (El)"},
    {"page": 28, "municipality": "FELANITX",
     "says_db": "Comezma (La)",
     "should_say": "Comerma (La)",
     "says_original": "Comezma (La)"},
    {"page": 32, "municipality": "PETRA",
     "says_db": "Ca'n Damátiga (tomate)",
     "should_say": "Ca'n Domátiga (tomate)",
     "says_original": "Ca'n Damátiga (tomate)"},
    {"page": 38, "municipality": "BUÑOLA",
     "says_db": "Báig d'el Púig (al pié del monte)",
     "should_say": "Báix d'el Púig (al pié del monte)",
     "says_original": "Báig d'el Púig (al pié del monte)"},
    {"page": 40, "municipality": "DEYÁ",
     "says_db": "Ca'n Berméi",
     "should_say": "Ca'n Verméi",
     "says_original": "Ca'n Berméi"},
    {"page": 44, "municipality": "PALMA",
     "says_db": "Ca na Galluza",
     "should_say": "Ca na Gallura",
     "says_original": "Ca na Galluza"},
]


def parse_int_es(s: str) -> int | None:
    """1.051 -> 1051, » -> 0, empty -> None."""
    s = s.strip()
    if not s:
        return None
    if s == "»":
        return 0
    try:
        return int(s.replace(".", ""))
    except ValueError:
        return None


def parse_page_50(html_path: Path) -> list[dict]:
    """Read raw page-50 HTML and return chart records."""
    html = html_path.read_text(encoding="utf-8")
    out = []
    for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL):
        cells = [c.strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr.group(1), re.DOTALL)]
        if len(cells) < 3:
            continue
        _prefix, label, title = cells[0], cells[1], cells[2]
        # Label like "Cuadro 3 - Inca" or "TOTAL Cuadro 3"
        m = re.match(r"(?:Cuadro\s+(\d+)\s*-\s*(\w+)|TOTAL\s+Cuadro\s+(\d+))", label)
        if not m:
            continue
        if m.group(1):
            chart_num = int(m.group(1))
            district = m.group(2)
            is_total = False
        else:
            chart_num = int(m.group(3))
            district = None
            is_total = True
        values = [v for v in (parse_int_es(c) for c in cells[3:]) if v is not None]
        out.append({
            "chart_num": chart_num,
            "chart_title": title,
            "judicial_district": district,
            "is_total": is_total,
            "values": values,
        })
    return out


def main() -> None:
    con = duckdb.connect(str(DB))

    con.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            chart_num         INTEGER NOT NULL,
            chart_title       TEXT,
            judicial_district TEXT,
            is_total          BOOLEAN,
            values            INTEGER[],
            columns           TEXT[]
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS errata (
            page_pdf      INTEGER,
            municipality  TEXT,
            says_original TEXT,
            says_db       TEXT,
            should_say    TEXT,
            applied       BOOLEAN
        )
    """)

    con.execute("DELETE FROM summaries")
    con.execute("DELETE FROM errata")

    rows_50 = parse_page_50(HTML_50)
    for row in rows_50:
        cols = CHARTS[row["chart_num"]]["columns"]
        con.execute(
            """INSERT INTO summaries
               (chart_num, chart_title, judicial_district, is_total, values, columns)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [row["chart_num"], row["chart_title"], row["judicial_district"],
             row["is_total"], row["values"], cols],
        )
    print(f"summaries: {len(rows_50)} rows inserted (4 charts x 5 districts + 4 totals)")

    deleted = con.execute(
        "DELETE FROM entries WHERE page = 50 RETURNING id"
    ).fetchall()
    print(f"entries: {len(deleted)} page-50 rows removed")

    applied = 0
    for e in ERRATA:
        rows = con.execute(
            "SELECT id FROM entries WHERE page = ? AND municipality = ? AND place = ?",
            [e["page"], e["municipality"], e["says_db"]],
        ).fetchall()
        if rows:
            con.execute(
                "UPDATE entries SET place = ? WHERE page = ? AND municipality = ? AND place = ?",
                [e["should_say"], e["page"], e["municipality"], e["says_db"]],
            )
            was_applied = True
            applied += 1
        else:
            was_applied = False
            print(f"WARN: errata not applied: {e['says_db']!r} not found at page {e['page']} {e['municipality']}")
        con.execute(
            """INSERT INTO errata
               (page_pdf, municipality, says_original, says_db, should_say, applied)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [e["page"], e["municipality"], e["says_original"], e["says_db"],
             e["should_say"], was_applied],
        )
    print(f"errata: {applied}/{len(ERRATA)} corrections applied to entries.place")

    con.commit()

    n_entries, n_summaries, n_errata = con.execute("""
        SELECT (SELECT COUNT(*) FROM entries),
               (SELECT COUNT(*) FROM summaries),
               (SELECT COUNT(*) FROM errata)
    """).fetchone()
    print()
    print(f"  entries:   {n_entries:>4} rows")
    print(f"  summaries: {n_summaries:>4} rows")
    print(f"  errata:    {n_errata:>4} rows")


if __name__ == "__main__":
    main()
