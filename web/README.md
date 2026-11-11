# Nomenclàtor 1860 — static site

A single-page site with no build step. `app.js` fetches the JSON files in
`data/` and runs every filter and aggregate in plain JavaScript; the charts are
drawn with Vega/Vega-Lite, vendored under `vendor/`.

Serve it over HTTP (`fetch` does not work from `file://`):

```bash
python3 -m http.server 8000 -d web
```

## Layout

- `index.html` — the page; tabs Inici, Explorar, Estadístiques, Gràfiques, Glossari
- `app.js` — data loading, filters, tables and chart specs (no framework)
- `style.css`, `theme.js` — styling and the light/dark toggle
- `data/*.json` — produced by `scripts/export_json.py` (called by `scripts/rebuild.py`)
- `vendor/` — Vega, Vega-Lite and vega-embed (`scripts/download_vendor.py`)
- `_headers` — cache and Content-Security-Policy headers for Cloudflare

See the root `README.md` for the data pipeline and deployment.
