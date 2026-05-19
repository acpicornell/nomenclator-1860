-- 1860 Nomenclator schema — Balearic Islands.
-- Place and class text is kept literally as it appears in the PDF.
-- The "»" symbol in the original (meaning zero / nothing) becomes 0.
-- Distances originally written with apostrophe decimal (e.g. "9'3") are
-- stored as 9.3.

CREATE SEQUENCE IF NOT EXISTS seq_entry_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_note_id START 1;

CREATE TABLE IF NOT EXISTS entries (
    id                        INTEGER PRIMARY KEY DEFAULT nextval('seq_entry_id'),
    page                      INTEGER NOT NULL,
    judicial_district         TEXT,
    municipality              TEXT,
    municipality_inhabitants  INTEGER,
    place                     TEXT NOT NULL,
    place_class               TEXT,
    distance_km               DOUBLE,
    inhabited_permanent       INTEGER,
    inhabited_seasonal        INTEGER,
    uninhabited               INTEGER,
    buildings_1_floor         INTEGER,
    buildings_2_floors        INTEGER,
    buildings_3_floors        INTEGER,
    buildings_over_3_floors   INTEGER,
    shelters                  INTEGER,
    total                     INTEGER,
    note_ref                  TEXT,
    is_municipality_total     BOOLEAN DEFAULT FALSE,
    highlighted               BOOLEAN DEFAULT FALSE,
    is_district_total         BOOLEAN DEFAULT FALSE,
    class_normalized          TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id            INTEGER PRIMARY KEY DEFAULT nextval('seq_note_id'),
    page          INTEGER NOT NULL,
    ref           TEXT,
    text          TEXT,
    municipality  TEXT
);

CREATE INDEX IF NOT EXISTS idx_entries_municipality ON entries(municipality);
CREATE INDEX IF NOT EXISTS idx_entries_district ON entries(judicial_district);
CREATE INDEX IF NOT EXISTS idx_entries_page ON entries(page);

-- Resums i errates del Cens de 1860 (pàg. 50 i 51 del PDF).
-- `summaries` és el desglossament dels 4 quadres estadístics (chart 1-4)
-- per partit judicial. `errata` és la full d'errates aplicada a les
-- entrades, conservada per traçabilitat.

CREATE TABLE IF NOT EXISTS summaries (
    chart_num         INTEGER NOT NULL,
    chart_title       TEXT,
    judicial_district TEXT,
    is_total          BOOLEAN,
    values            INTEGER[],
    columns           TEXT[]
);

CREATE TABLE IF NOT EXISTS errata (
    page_pdf      INTEGER,
    municipality  TEXT,
    says_original TEXT,
    says_db       TEXT,
    should_say    TEXT,
    applied       BOOLEAN
);

-- Metadades de provenença. Cada execució de scripts/rebuild.py
-- estampa una entrada amb la data de càrrega, el comptador de files i
-- una referència als scripts implicats. Permet mostrar a la web
-- "actualitzat fa X" i auditar quan es va re-ingestar la font.

CREATE TABLE IF NOT EXISTS source_metadata (
    source_name  TEXT PRIMARY KEY,    -- '1860'
    fetched_at   TIMESTAMP,
    n_rows       INTEGER,
    scripts      TEXT,                 -- scripts implicats, separats per coma
    notes        TEXT                  -- origen, mètode, particularitats
);
