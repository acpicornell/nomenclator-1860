# Nomenclàtor de les Illes Balears · 1860

[![Deploy](https://github.com/acpicornell/nomenclator-1860/actions/workflows/deploy.yml/badge.svg)](https://github.com/acpicornell/nomenclator-1860/actions/workflows/deploy.yml)

A complete digitisation of the *Nomenclátor de la Provincia de las Baleares*,
drawn up on 25 December 1860 by the Junta General de Estadística — the first
Spanish gazetteer tabulated down to the building. Every Balearic place declares
its buildings by use, by number of floors, its shelters and its distance to the
centre of the municipality; this edition makes that a queryable database and an
explorable website.

**Live site: <https://1860.corpusbalear.org>** — part of
[Corpus Balear](https://corpusbalear.org), digital editions of Balearic
historical sources.

## What's in it

- **3 026 entries** (places and buildings), with the page's footnotes, the four
  official summary tables of p. 50 and the errata of p. 51.
- Five judicial districts: Palma, Inca, Manacor, Eivissa, Maó.
- 100% internal arithmetic coherence; the 15 deviations from printed subtotals
  (net +11 over 74 107 buildings) are the 1860 printer's own, verified against
  the facsimile.
- A website in Catalan with filters, CSV download, statistics, six interactive
  Vega-Lite charts and a glossary.

## How it was made

The Balearic pages of the BNE's digitised volumes were extracted page by page
with Claude Vision, loaded into DuckDB, corrected automatically and by the
book's own errata, and validated against the printed subtotals and summary
tables. The output for the web is static JSON, filtered in the browser with no
database at runtime.

## Run locally

```bash
uv sync
.venv/bin/python scripts/rebuild.py      # everything except the (paid) vision extraction
cd web && python3 -m http.server 8000
```

Re-running the extraction (`--include-expensive`) needs `ANTHROPIC_API_KEY` in
`.env`.

## Documentation

The documentation is in Catalan.

- [docs/DATA.md](docs/DATA.md) — the source (BNE volumes), the `entries`
  schema, the eight consistency checks with their current state, and the
  licence as originally stated.
- [docs/PIPELINE.md](docs/PIPELINE.md) — architecture, requirements, rebuilding
  the database step by step, the website's tabs, Cloudflare deployment and
  conventions.
- [data/SOURCES.md](data/SOURCES.md) — data provenance, licence and recommended
  attribution.
- [web/README.md](web/README.md) — the static site.

## Licence and citation

- **Code**: GNU **AGPL-3.0-or-later** — see `LICENSE`.
- **Data** (`web/data/*.json`): the original source (the 1860 Nomenclátor) is
  **public domain** by age (over 160 years old, an official State publication
  predating 1880). See [data/SOURCES.md](data/SOURCES.md) for the recommended
  attribution.

The site cites itself as: Picornell Company, A. C. *Nomenclàtor* (1860), edició
digital. Corpus Balear · 1860.corpusbalear.org
