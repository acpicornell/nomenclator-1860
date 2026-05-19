# Nomenclàtor de les Illes Balears · 1860

Digitalització completa del *Nomenclátor de la Provincia de las Baleares*, redactat el **25 de desembre de 1860** per la Junta General d'Estadística (predecessora de l'INE) sota Alejandro Oliván. És el primer nomenclàtor espanyol amb tabulació a nivell d'edifici.

Cada poble balear declara els edificis per ús (habitats permanentment, temporals, inhabitats), per nombre de plantes, més albergs i la distància al centre del municipi. Domini públic per antiguitat.

🔗 **Demo en directe**: <https://nomenclator-1860.acpicornell.workers.dev>
📂 **Codi**: <https://github.com/acpicornell/nomenclator-1860>

| Font | Període | Taules | Files |
|---|---|---|---|
| **Nomenclàtor 1860** — *Junta General de Estadística* | 25 desembre 1860 | `entries`, `notes`, `summaries`, `errata` | 3.026 entrades |

## Font primària

L'obra completa — «*Nomenclátor que comprende las poblaciones, grupos, edificios, viviendas, albergues, etc., de las cuarenta y nueve provincias de España*», editat per la Junta General de Estadística entre 1863-1871, Imprenta de José María Ortiz, Madrid — està digitalitzada per la **Biblioteca Nacional de España** (signatura 2/45404 V.1 - 2/45408 V.5, domini públic, llicència CC-BY 4.0):

- 📚 **Registre BNE**: [bdh-rd.bne.es/bdh0000167814](http://bdh.bne.es/bnesearch/detalle/bdh0000167814)
- 📄 [Volum 1 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=a98dc0b2-620e-436f-ab9b-ed039ee3754c)
- 📄 [Volum 2 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=32e3d5d6-2b1a-4aec-a30e-94c7b250b9d6)
- 📄 [Volum 3 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=bdc937a9-670d-4990-a06e-572c91b6d15b)
- 📄 [Volum 4 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=adfdc195-0261-4907-a632-643804d0a4ce)
- 📄 [Volum 5 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=57cd9a43-ac47-4376-a728-9a751cc9ea54)

Les 49 províncies de l'època apareixen disposades alfabèticament a través dels 5 volums. El PDF que digitalitzem aquí (`pdfs/Nomenclàtor 1860 balears.pdf`, no versionat — vegeu `.gitignore`) és l'extracció de les pàgines de la província de Balears.

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

Quan re-exportis els JSON, recorda bumpar `DATA_V` a `web/app.js` perquè el navegador no serveixi una versió obsoleta.

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

El web és pur estàtic — qualsevol hosting CDN serveix, però aquest projecte deploya a [Cloudflare Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/) connectant el repositori de GitHub directament:

1. **dash.cloudflare.com** → Workers & Pages → Create → Workers → Import a repository
2. Selecciona `acpicornell/nomenclator-1860`
3. Configuració:
   - Build command: *(buida)*
   - Build output directory: `web`
   - Root directory: `/`
4. Save and Deploy

El fitxer `web/_headers` configura `Cache-Control: no-store` perquè cada push es reflexi al següent reload, més una CSP raonable (script-src `'self' 'unsafe-eval'` per Vega). Vendor i dades són tots < 1.5 MB, ben per sota del límit de 25 MiB per fitxer de CF Workers.

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

La pàgina 50 del PDF (quadres-resum) es carrega a la BD però s'amaga a la pestanya d'exploració; es mostra a la pestanya *Estadístiques*.

## Comprovacions de consistència

`db/check_consistency.py` executa 8 comprovacions sobre la BD:

- Coherència interna de fila (HC+HT+Inh = P1+P2+P3+PM+Alb = total)
- Σfiles de municipi vs subtotal imprès
- Σmunis de partit vs total del partit
- Σentries vs Quadre 3 pàg. 50
- Anomalies de NULL i zeros
- Files duplicades (mateix page+muni+place)
- Estat de la fe d'errates (8 correccions verificades)
- Gaps de normalització de `class_normalized`

Estat actual: **100% coherència aritmètica interna** post-fix Ca'n Mena. Les 15 desviacions Σfiles vs subtotal imprès (Δ ∈ [-1, +3], net +11 sobre 74.107 edificis, 0,015%) **són del propi impressor del 1860**, no de la digitalització — tots els subtotals impresos s'han verificat visualment contra el facsímil i coincideixen exactament amb la BD.

## Convencions

- **Identificadors de codi** (taules, columnes, fitxers, variables): **anglès**.
- **UI web** (textos, etiquetes, comentaris): **català**.
- **README**: català.
- **Valors literals** (noms de població, classes com «Caserío»): tal com apareixen a la font.

## Llicència

- **Codi**: GNU **AGPL-3.0-or-later** — vegeu `LICENSE`.
- **Dades** (`web/data/*.json`): la font original (Nomenclátor de 1860) és **domini públic** per antiguitat (l'obra té més de 160 anys i és una publicació oficial de l'Estat anterior a 1880). Vegeu `data/SOURCES.md` per a l'atribució recomanada.
