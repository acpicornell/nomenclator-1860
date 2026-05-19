"""Incremental load: append a block of pages to the DB without resetting it."""
import sys
import importlib
from pathlib import Path
import duckdb

if len(sys.argv) < 2:
    print("Usage: load_block.py <module>   (e.g.: pages_6_8)")
    sys.exit(1)

PROJECT = Path(__file__).resolve().parent.parent
mod_name = sys.argv[1]
sys.path.insert(0, str(PROJECT / "data"))
mod = importlib.import_module(mod_name)

DB = PROJECT / "db" / "nomenclator.duckdb"
con = duckdb.connect(str(DB))

# Remove any prior entries for the pages covered by this module
pages = sorted({e[0] for e in mod.ENTRADAS})
con.execute(f"DELETE FROM entries WHERE page IN ({','.join(map(str, pages))})")
con.execute(f"DELETE FROM notes WHERE page IN ({','.join(map(str, pages))})")

con.executemany("""
    INSERT INTO entries (
        page, judicial_district, municipality, municipality_inhabitants,
        place, place_class, distance_km,
        inhabited_permanent, inhabited_seasonal, uninhabited,
        buildings_1_floor, buildings_2_floors, buildings_3_floors, buildings_over_3_floors,
        shelters, total, note_ref, is_municipality_total, highlighted, is_district_total
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", mod.ENTRADAS)

con.executemany("""
    INSERT INTO notes (page, ref, text, municipality)
    VALUES (?, ?, ?, ?)
""", mod.NOTAS)

con.commit()
print(f"Block {mod_name}: {len(mod.ENTRADAS)} entries, {len(mod.NOTAS)} notes (pages {pages}).")
