# Arquitectura, pipeline i deploy

## Arquitectura

```
                  db/nomenclator.duckdb       (build-time, local)
                  ├─ entries          ← una fila per població/edifici
                  ├─ notes            ← notes a peu d'article
                  ├─ summaries        ← pàg. 50 (4 quadres-resum)
                  ├─ errata           ← pàg. 51 (fe d'errates)
                  └─ source_metadata  ← provenença
                         │
                         ▼  scripts/export_json.py
                  web/data/*.json    (~1.5 MB sense gzip, ~500 KB gzip)
                         │
                         ▼
                  web/  ← HTML + JS pur + Vega-Lite (sense WASM)
```

La pipeline Python local fa servir DuckDB internament per a extracció,
validació i ingesta, però l'**output final per al web és JSON estàtic**.
El runtime web no necessita DuckDB-WASM ni cap altra base de dades: tot
el filtrat i les agregacions es fan en JavaScript sobre arrays en memòria
del navegador. Això permet hostatjar la web a qualsevol CDN amb límits
estrictes (Cloudflare Workers Free, GitHub Pages, S3 estàtic…).

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
.venv/bin/python scripts/rebuild.py --json      # només re-exportar JSON a web/data/
.venv/bin/python scripts/rebuild.py --seed      # només estampar metadata
.venv/bin/python scripts/rebuild.py --include-expensive   # amb Claude vision
```

`rebuild.py` corre cada pas en l'ordre correcte, reporta timing i row counts, i actualitza `source_metadata`. Al final delega a `scripts/export_json.py` per generar els JSON consumits per la web.

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

# Comprovacions de consistència
.venv/bin/python db/check_consistency.py
```

Els JSON re-exportats no necessiten cap versió a `web/app.js`: `web/_headers` serveix tots els actius amb `Cache-Control: no-store`, així el navegador sempre demana el deploy més recent.

## Web

```bash
cd web && python3 -m http.server 8000
```

Obrir <http://localhost:8000>. La pàgina ha de servir-se per HTTP (no `file://`) perquè els JSON es carreguen via `fetch`. Pestanyes:

1. **Inici** — visió general amb estadístiques principals.
2. **Explorar** — filtres (població, partit judicial, municipi, classe, distància) sobre una taula paginada i ordenable, amb descàrrega CSV.
3. **Estadístiques** — agregats per partit, classes més freqüents, distribució per plantes, més els 4 quadres-resum oficials de la pàg. 50.
4. **Gràfiques** — sis visualitzacions Vega-Lite interactives:
   1. Donut de classes d'edifici (filtrable per municipi)
   2. Ocupació HC/HT/Inh per partit o municipi (amb selector)
   3. Boxplot de distàncies al nucli per classe
   4. Corba de Pareto de la concentració d'edificis
   5. Arrels toponímiques més freqüents (Son, Ca'n, Molí, Torre, Venda…)
   6. Composició arquitectònica per nombre de plantes (amb selector)
5. **Glossari** — explicació de columnes, classes de població i convencions del text original.

L'única dependència de runtime és Vega-Lite (~800 KB a `web/vendor/`, reproduïble amb `scripts/download_vendor.py`).

## Deploy a Cloudflare Workers

El web és pur estàtic — qualsevol hosting CDN serveix, però aquest projecte deploya a [Cloudflare Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/) des de GitHub Actions. A cada push a `main`, `.github/workflows/deploy.yml` executa `scripts/check_site.py web` i després publica `web/` amb `cloudflare/wrangler-action` (configuració a `wrangler.jsonc`). Cal el secret de repositori `CLOUDFLARE_API_TOKEN`; mentre no hi és, el workflow se salta el deploy i acaba en verd.

El fitxer `web/_headers` configura `Cache-Control: no-store` perquè cada push es reflexi al següent reload, més una CSP raonable (script-src `'self' 'unsafe-eval'` per Vega). Vendor i dades són tots < 1.5 MB, ben per sota del límit de 25 MiB per fitxer de CF Workers.

## Convencions

- **Identificadors de codi** (taules, columnes, fitxers, variables): **anglès**.
- **UI web** (textos, etiquetes, comentaris): **català**.
- **README**: anglès; **documentació a `docs/`**: català.
- **Valors literals** (noms de població, classes com «Caserío»): tal com apareixen a la font.
