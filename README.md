# Nomenclàtor de les Illes Balears · 1860

Digitalització completa del *Nomenclátor de la Provincia de las Baleares*, redactat el **25 de desembre de 1860** per la Junta General d'Estadística (predecessora de l'INE) sota Alejandro Oliván. És el primer nomenclàtor espanyol amb tabulació a nivell d'edifici.

Cada poble balear declara els edificis per ús (habitats permanentment, temporals, inhabitats), per nombre de plantes, més albergs i la distància en quilòmetres al centre del municipi. Domini públic per antiguitat.

| Font | Període | Taules | Files |
|---|---|---|---|
| **Nomenclàtor 1860** — *Junta General de Estadística* | 25 desembre 1860 | `entries`, `notes`, `summaries`, `errata` | 3.026 entrades |

## Arquitectura

```
                  db/nomenclator.duckdb
                  ├─ entries          ← una fila per població/edifici
                  ├─ notes            ← notes a peu d'article
                  ├─ summaries        ← pàg. 50 (4 quadres-resum)
                  ├─ errata           ← pàg. 51 (fe d'errates)
                  └─ source_metadata  ← provenença
                         │
                         ▼
                  web/data/*.parquet  (ZSTD)
                         │
                         ▼
                  web/  ← SPA + DuckDB-WASM (local vendor/, offline-first)
```

Els scripts d'extracció escriuen directament a DuckDB i el rebuild reexporta els Parquets. La marca temporal de `source_metadata` permet a la web mostrar "actualitzat fa N dies".

## Requisits

- Python ≥ 3.12 amb [uv](https://docs.astral.sh/uv/)
- `ANTHROPIC_API_KEY` a `.env` (només si tornes a executar l'extracció del PDF)

```bash
uv sync   # crea .venv amb tot
```

## Reconstruir la base de dades

### Orquestrador unificat (recomanat)

```bash
.venv/bin/python scripts/rebuild.py             # tot, excepte vision (car)
.venv/bin/python scripts/rebuild.py --parquet   # només re-exportar parquets
.venv/bin/python scripts/rebuild.py --seed      # només estampar metadata
.venv/bin/python scripts/rebuild.py --include-expensive   # amb Claude vision
```

`rebuild.py` corre cada pas en l'ordre correcte, reporta timing i row counts, i actualitza `source_metadata`.

### Passos individuals (debug)

```bash
# Extracció del PDF (car: Claude vision, ~10 USD)
.venv/bin/python scripts/extract_with_claude.py --range 4-51

# Càrrega i validació
.venv/bin/python scripts/load_claude_output.py
.venv/bin/python db/validate.py
.venv/bin/python db/validate_rows.py

# Correccions automàtiques
.venv/bin/python scripts/auto_fix.py --apply
.venv/bin/python scripts/auto_fix_2.py --apply

# Aplicar fe d'errates + carregar quadres-resum (pàg. 50, 51)
.venv/bin/python scripts/apply_errata_and_summaries.py
```

Quan re-exportis Parquets, recorda bumpar `DATA_V` a `web/app.js` perquè el navegador no serveixi una versió obsoleta.

## Web

```bash
cd web && python3 -m http.server 8000
```

Obrir <http://localhost:8000>. La pàgina ha de servir-se per HTTP (no `file://`): DuckDB-WASM carrega els Parquets via `fetch`. Pestanyes:

1. **Inici** — visió general amb estadístiques principals.
2. **Nomenclàtor 1860** — explorador amb filtres (població, partit judicial, municipi, classe, distància) sobre una taula paginada i ordenable. Inclou:
   - *Explorar* — filtres i taula
   - *Estadístiques* — agregats per partit, classes més freqüents, distribució per plantes, més els 4 quadres-resum oficials
   - *Glossari* — explicació de columnes, classes de població i convencions del text original
3. **Consola SQL** — DuckDB lliure contra les taules.

Tota la web és **offline-first**: les dependències (DuckDB-WASM, apache-arrow…) viuen a `web/vendor/` (~100 MB, reproduïble amb `scripts/download_vendor.py`).

## Schema

El schema complet és a `db/schema.sql`. Taula principal `entries`:

| Columna | Tipus | Significat |
|---|---|---|
| `judicial_district` | TEXT | Palma / Inca / Manacor / Eivissa / Maó |
| `municipality` | TEXT | Literal del PDF |
| `place` | TEXT | Població o entitat |
| `place_class`, `class_normalized` | TEXT | Caserío, Casa de labor, Molino, Iglesia… |
| `distance_km` | DOUBLE | Distància al centre del municipi |
| `inhabited_permanent`, `inhabited_seasonal`, `uninhabited` | INT | Per ús |
| `buildings_1_floor`…`buildings_over_3_floors`, `shelters` | INT | Per construcció |
| `total` | INT | Suma per fila |

La pàgina 50 del PDF (quadres-resum) es carrega a la BD però s'amaga a la pestanya d'exploració.

## Convencions

- **Identificadors de codi** (taules, columnes, fitxers, variables): **anglès**.
- **UI web** (textos, etiquetes, comentaris): **català**.
- **README**: català.
- **Valors literals** (noms de població, classes com «Caserío»): tal com apareixen a la font.

## Llicència

- **Codi**: GNU **AGPL-3.0-or-later** — vegeu `LICENSE`.
- **Dades** (`web/data/*.parquet`): la font original (Nomenclátor de 1860) és **domini públic** per antiguitat. Vegeu `data/SOURCES.md` per a l'atribució recomanada.
