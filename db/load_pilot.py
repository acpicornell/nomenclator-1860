"""Load the pilot data (pages 3-5) into the DuckDB database."""
import sys
from pathlib import Path
import duckdb

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "data"))
from pages_3_5 import ENTRADAS, NOTAS

DB = PROJECT / "db" / "nomenclator.duckdb"
con = duckdb.connect(str(DB))

con.execute("DELETE FROM entries")
con.execute("DELETE FROM notes")
con.execute("DROP SEQUENCE IF EXISTS seq_entry_id")
con.execute("DROP SEQUENCE IF EXISTS seq_note_id")
con.execute("CREATE SEQUENCE seq_entry_id START 1")
con.execute("CREATE SEQUENCE seq_note_id START 1")

con.executemany("""
    INSERT INTO entries (
        page, judicial_district, municipality, municipality_inhabitants,
        place, place_class, distance_km,
        inhabited_permanent, inhabited_seasonal, uninhabited,
        buildings_1_floor, buildings_2_floors, buildings_3_floors, buildings_over_3_floors,
        shelters, total, note_ref, is_municipality_total, highlighted
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ENTRADAS)

con.executemany("""
    INSERT INTO notes (page, ref, text, municipality)
    VALUES (?, ?, ?, ?)
""", NOTAS)

con.commit()
print(f"Inserted {len(ENTRADAS)} entries and {len(NOTAS)} notes.")
print(f"DB: {DB}")
