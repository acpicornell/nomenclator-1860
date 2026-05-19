# Nomenclàtor 1860 — Web estàtica

Explorador local del cens digitalitzat, amb DuckDB-WASM corrent al navegador.

## Llançar

DuckDB-WASM necessita servir-se per HTTP (no `file://`). Des de l'arrel del projecte:

```bash
cd web
python3 -m http.server 8000
```

Després obre <http://localhost:8000> al navegador.

Alternativament (més simple si tens `uv`):

```bash
uv run python -m http.server 8000 -d web
```

## Estructura

- `index.html` — single-page app
- `style.css` — estil (cream + terracotta, sòbria acadèmica)
- `app.js` — DuckDB-WASM + UI (mòdul ES, sense frameworks)
- `data/entries.parquet` (~54 KB) — dades principals
- `data/notes.parquet` (~6 KB) — notes a peu de pàgina
- `data/*.parquet` — fonts addicionals (errata, summaries, NGIB, INE, etc.)

## Pestanyes

1. **Explorar** — filtres (població, partit, municipi, classe, km) + taula paginada ordenable
2. **Estadístiques** — resums precalculats (top municipis, distribució de plantes, etc.)
3. **Consola SQL** — DuckDB SQL lliure contra les taules `entries` i `notes`

## Re-exportar Parquet després de tocar la BD

```bash
.venv/bin/python -c "
import duckdb
c = duckdb.connect('db/nomenclator.duckdb', read_only=True)
c.execute(\"COPY entries TO 'web/data/entries.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)\")
c.execute(\"COPY notes TO 'web/data/notes.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)\")
"
```
