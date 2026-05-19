// 1860 Nomenclator — static web with DuckDB-WASM.
// Loads the Parquet files into the WASM DB and mounts the navigable UI.
// DuckDB-WASM and its deps (apache-arrow, flatbuffers, tslib) live under
// vendor/, so the site is 100% offline.
import * as duckdb from "./vendor/duckdb-wasm.mjs";

const PAGE_SIZE = 50;

let db = null;
let conn = null;
let state = {
  place: "",
  district: "",
  municipality: "",
  placeClass: "",
  km_min: null,
  km_max: null,
  include_totals: false,
  page: 0,
  sort_col: "municipality",
  sort_dir: "asc",
};

// === BOOTSTRAP DUCKDB-WASM ===
async function initDuckDB() {
  const base = new URL("vendor/", location.href).href;
  const bundles = {
    mvp: { mainModule: base + "duckdb-mvp.wasm",
           mainWorker: base + "duckdb-browser-mvp.worker.js" },
    eh:  { mainModule: base + "duckdb-eh.wasm",
           mainWorker: base + "duckdb-browser-eh.worker.js" },
    coi: { mainModule: base + "duckdb-coi.wasm",
           mainWorker: base + "duckdb-browser-coi.worker.js",
           pthreadWorker: base + "duckdb-browser-coi.pthread.worker.js" },
  };
  const bundle = await duckdb.selectBundle(bundles);
  const workerUrl = URL.createObjectURL(
    new Blob([`importScripts("${bundle.mainWorker}");`], { type: "text/javascript" })
  );
  const worker = new Worker(workerUrl);
  const logger = new duckdb.ConsoleLogger();
  db = new duckdb.AsyncDuckDB(logger, worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  URL.revokeObjectURL(workerUrl);
  conn = await db.connect();
  // Cache-busting per a fitxers de dades: bumpa quan canvia el contingut
  // d'algun Parquet i el navegador en serveix una versió obsoleta.
  const DATA_V = "v=3";
  const data = (name) => new URL(`data/${name}?${DATA_V}`, location.href).href;
  await db.registerFileURL("entries.parquet", data("entries.parquet"), 4, false);
  await db.registerFileURL("notes.parquet", data("notes.parquet"), 4, false);
  await db.registerFileURL("summaries.parquet", data("summaries.parquet"), 4, false);
  await db.registerFileURL("errata.parquet", data("errata.parquet"), 4, false);
  await db.registerFileURL("source_metadata.parquet", data("source_metadata.parquet"), 4, false);
  // Page 50 is the statistical summary (Charts 1-4) and SUMMARY rows:
  // cross-tabulations with legitimate zeros that confuse the data view.
  await conn.query("CREATE VIEW entries AS SELECT * FROM 'entries.parquet' WHERE page != 50");
  await conn.query("CREATE VIEW notes AS SELECT * FROM 'notes.parquet'");
  await conn.query("CREATE VIEW summaries AS SELECT * FROM 'summaries.parquet'");
  await conn.query("CREATE VIEW errata AS SELECT * FROM 'errata.parquet'");
  await conn.query("CREATE VIEW source_metadata AS SELECT * FROM 'source_metadata.parquet'");
}

async function query(sql, params = []) {
  const stmt = await conn.prepare(sql);
  const res = await stmt.query(...params);
  const rows = res.toArray().map(r => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, normalizeValue(v)])));
  await stmt.close();
  return rows;
}

function normalizeValue(v) {
  if (v == null) return v;
  if (typeof v === "bigint") return Number(v);
  if (v instanceof Uint32Array && v.length === 4) {
    return v[0] + v[1] * 4294967296 + v[2] * 2 ** 64 + v[3] * 2 ** 96;
  }
  if (v && typeof v.toArray === "function" && typeof v !== "string") {
    return Array.from(v.toArray()).map(normalizeValue);
  }
  if (Array.isArray(v)) return v.map(normalizeValue);
  return v;
}

// === FILL FILTER DROPDOWNS ===
async function fillFilters() {
  const districts = await query("SELECT DISTINCT judicial_district AS v FROM entries WHERE judicial_district IS NOT NULL ORDER BY v");
  fillSelect("f-district", districts);
  await refillMunicipalities();
  await refillClasses();
}

async function refillMunicipalities() {
  let sql = "SELECT DISTINCT municipality AS v FROM entries WHERE municipality IS NOT NULL";
  const params = [];
  if (state.district) {
    sql += " AND judicial_district = ?";
    params.push(state.district);
  }
  sql += " ORDER BY v";
  const munis = await query(sql, params);
  fillSelect("f-municipality", munis);
  if (state.municipality && !munis.some(r => r.v === state.municipality)) {
    state.municipality = "";
  }
  document.getElementById("f-municipality").value = state.municipality || "";
}

async function refillClasses() {
  let sql = "SELECT class_normalized AS v, COUNT(*) AS n FROM entries WHERE class_normalized IS NOT NULL";
  const params = [];
  if (state.district) { sql += " AND judicial_district = ?"; params.push(state.district); }
  if (state.municipality) { sql += " AND municipality = ?"; params.push(state.municipality); }
  sql += " GROUP BY 1 ORDER BY n DESC LIMIT 40";
  const classes = await query(sql, params);
  fillSelect("f-class", classes, r => `${r.v} (${r.n})`);
  if (state.placeClass && !classes.some(r => r.v === state.placeClass)) {
    state.placeClass = "";
  }
  document.getElementById("f-class").value = state.placeClass || "";
}

function fillSelect(id, rows, labelFn = r => r.v) {
  const sel = document.getElementById(id);
  while (sel.options.length > 1) sel.remove(1);
  for (const r of rows) {
    const opt = document.createElement("option");
    opt.value = r.v;
    opt.textContent = labelFn(r);
    sel.appendChild(opt);
  }
}

// === STATS ===
async function loadSourceStats() {
  const r = await query(`
    SELECT
      (SELECT COUNT(*) FROM entries WHERE NOT is_municipality_total AND NOT is_district_total) AS rows_1860,
      (SELECT COUNT(DISTINCT municipality) FROM entries WHERE municipality IS NOT NULL AND municipality != 'SUMMARY') AS munis,
      (SELECT COUNT(DISTINCT judicial_district) FROM entries WHERE judicial_district IS NOT NULL) AS districts,
      (SELECT COUNT(*) FROM notes) AS notes
  `);
  const s = r[0];
  const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  setText("stat-rows", s.rows_1860.toLocaleString("ca-ES"));
  setText("stat-munis", s.munis.toLocaleString("ca-ES"));
  setText("stat-districts", s.districts.toLocaleString("ca-ES"));
  setText("stat-notes", s.notes.toLocaleString("ca-ES"));
  setText("home-stat-rows", s.rows_1860.toLocaleString("ca-ES"));
  setText("home-stat-munis", s.munis.toLocaleString("ca-ES"));
  setText("home-stat-districts", s.districts.toLocaleString("ca-ES"));
  setText("home-stat-notes", s.notes.toLocaleString("ca-ES"));
}

// === EXPLORE: filters -> SQL ===
function buildWhere() {
  const conditions = [];
  const params = [];
  if (state.place) {
    conditions.push("LOWER(place) LIKE LOWER(?)");
    params.push(`%${state.place}%`);
  }
  if (state.district) {
    conditions.push("judicial_district = ?");
    params.push(state.district);
  }
  if (state.municipality) {
    conditions.push("municipality = ?");
    params.push(state.municipality);
  }
  if (state.placeClass) {
    conditions.push("class_normalized = ?");
    params.push(state.placeClass);
  }
  if (state.km_min != null) {
    conditions.push("distance_km >= ?");
    params.push(state.km_min);
  }
  if (state.km_max != null) {
    conditions.push("distance_km <= ?");
    params.push(state.km_max);
  }
  if (!state.include_totals) {
    conditions.push("NOT is_municipality_total AND NOT is_district_total");
  }
  return [conditions.length ? "WHERE " + conditions.join(" AND ") : "", params];
}

async function loadResults() {
  const [whereSql, params] = buildWhere();
  const countRow = await query(`SELECT COUNT(*) AS n FROM entries ${whereSql}`, params);
  const total = countRow[0].n;
  document.getElementById("results-count").innerHTML = `<strong>${total.toLocaleString("ca-ES")}</strong> entrades`;

  const offset = state.page * PAGE_SIZE;
  const orderCol = state.sort_col || "id";
  const orderDir = state.sort_dir === "desc" ? "DESC" : "ASC";
  const sql = `SELECT * FROM entries ${whereSql} ORDER BY ${orderCol} ${orderDir} NULLS LAST LIMIT ${PAGE_SIZE} OFFSET ${offset}`;
  const rows = await query(sql, params);
  renderTable(rows);
  updatePagination(total);
}

function renderTable(rows) {
  const tbody = document.getElementById("tbody-results");
  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="14" class="empty">Sense resultats amb aquests filtres.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const cls = (r.is_municipality_total || r.is_district_total) ? "is-total" : "";
    return `<tr class="${cls}">
      <td>${esc(r.municipality)}</td>
      <td>${esc(r.place)}</td>
      <td>${esc(r.place_class)}</td>
      <td class="num">${formatKm(r.distance_km)}</td>
      <td class="num">${num(r.inhabited_permanent)}</td>
      <td class="num">${num(r.inhabited_seasonal)}</td>
      <td class="num">${num(r.uninhabited)}</td>
      <td class="num">${num(r.buildings_1_floor)}</td>
      <td class="num">${num(r.buildings_2_floors)}</td>
      <td class="num">${num(r.buildings_3_floors)}</td>
      <td class="num">${num(r.buildings_over_3_floors)}</td>
      <td class="num">${num(r.shelters)}</td>
      <td class="num"><strong>${num(r.total)}</strong></td>
      <td>${esc(r.note_ref)}</td>
    </tr>`;
  }).join("");
}

function num(v) {
  if (v == null || v === 0) return '<span style="color:#ccc">·</span>';
  return Number(v).toLocaleString("ca-ES");
}
function formatKm(v) {
  if (v == null) return '<span style="color:#ccc">·</span>';
  return Number(v).toFixed(1);
}
function esc(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function formatRelativeTime(dt) {
  if (!dt) return "";
  const d = dt instanceof Date ? dt : new Date(dt);
  if (isNaN(d)) return "";
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 0) return "";
  const days = diffMs / 86400000;
  if (days < 1) return "actualitzat avui";
  if (days < 2) return "actualitzat ahir";
  if (days < 30) return `actualitzat fa ${Math.floor(days)} dies`;
  const months = days / 30.44;
  if (months < 12) return `actualitzat fa ${Math.floor(months)} mes${Math.floor(months) > 1 ? "os" : ""}`;
  return `actualitzat el ${d.toLocaleDateString("ca-ES")}`;
}

async function loadFreshness() {
  let rows;
  try {
    rows = await query(
      "SELECT source_name, EPOCH_MS(fetched_at) AS fetched_ms " +
      "FROM source_metadata WHERE source_name = '1860'"
    );
  } catch (e) {
    return;
  }
  if (!rows.length) return;
  const el = document.getElementById("fresh-1860");
  if (!el) return;
  el.textContent = formatRelativeTime(new Date(Number(rows[0].fetched_ms)));
}

// === CSV EXPORT ===
function _csvCell(v) {
  if (v === null || v === undefined) return "";
  if (Array.isArray(v)) v = v.join("|");
  if (typeof v === "object") v = JSON.stringify(v);
  const s = String(v);
  if (/[",\n\r\t]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function downloadCsv(filename, rows, columns) {
  if (!rows || !rows.length) {
    alert("No hi ha resultats a exportar amb els filtres actuals.");
    return;
  }
  const cols = columns || Object.keys(rows[0]);
  const lines = [
    cols.join(","),
    ...rows.map(r => cols.map(c => _csvCell(r[c])).join(",")),
  ];
  const blob = new Blob(["﻿" + lines.join("\n")],
                       { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 0);
}

function csvFilename(prefix) {
  const d = new Date().toISOString().slice(0, 10);
  return `${prefix}_${d}.csv`;
}

async function export1860() {
  const conditions = [];
  const params = [];
  if (state.place) {
    conditions.push("(LOWER(place) LIKE LOWER(?) OR LOWER(municipality) LIKE LOWER(?))");
    params.push(`%${state.place}%`, `%${state.place}%`);
  }
  if (state.district) { conditions.push("judicial_district = ?"); params.push(state.district); }
  if (state.municipality) { conditions.push("municipality = ?"); params.push(state.municipality); }
  if (state.placeClass) { conditions.push("class_normalized = ?"); params.push(state.placeClass); }
  if (state.km_min !== null) { conditions.push("distance_km >= ?"); params.push(state.km_min); }
  if (state.km_max !== null) { conditions.push("distance_km <= ?"); params.push(state.km_max); }
  if (!state.include_totals) {
    conditions.push("NOT is_municipality_total AND NOT is_district_total");
  }
  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
  const rows = await query(
    `SELECT page, judicial_district, municipality, place, place_class,
            class_normalized, distance_km, inhabited_permanent,
            inhabited_seasonal, uninhabited, buildings_1_floor,
            buildings_2_floors, buildings_3_floors, buildings_over_3_floors,
            shelters, total, is_municipality_total, is_district_total
     FROM entries ${where}
     ORDER BY ${state.sort_col} ${state.sort_dir}`,
    params
  );
  downloadCsv(csvFilename("nomenclator_1860"), rows);
}

function updatePagination(total) {
  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);
  document.getElementById("btn-prev").disabled = state.page === 0;
  document.getElementById("btn-next").disabled = state.page >= lastPage;
  document.getElementById("page-info").textContent = `pàgina ${state.page + 1} de ${lastPage + 1}`;
}

// === STATS ===
async function loadStats() {
  const districts = await query(`
    SELECT judicial_district AS district, COUNT(*) AS places, CAST(SUM(total) AS BIGINT) AS total_buildings
    FROM entries
    WHERE NOT is_municipality_total AND NOT is_district_total AND judicial_district IS NOT NULL
    GROUP BY 1 ORDER BY 3 DESC
  `);
  renderSimpleTable("t-districts", ["Partit", "Poblacions", "Edificis"], districts, r => [r.district, r.places.toLocaleString("ca-ES"), r.total_buildings.toLocaleString("ca-ES")]);

  const munis = await query(`
    SELECT municipality, CAST(SUM(total) AS BIGINT) AS total_buildings
    FROM entries
    WHERE NOT is_municipality_total AND NOT is_district_total AND municipality IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC LIMIT 15
  `);
  renderSimpleTable("t-top-munis", ["Municipi", "Edificis"], munis, r => [r.municipality, r.total_buildings.toLocaleString("ca-ES")]);

  const classes = await query(`
    SELECT class_normalized AS class, COUNT(*) AS n
    FROM entries
    WHERE NOT is_municipality_total AND NOT is_district_total AND class_normalized IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC LIMIT 20
  `);
  renderSimpleTable("t-classes", ["Classe", "Nº files"], classes, r => [r.class, r.n.toLocaleString("ca-ES")]);

  const floors = await query(`
    SELECT
      CAST(SUM(buildings_1_floor) AS BIGINT) AS p1,
      CAST(SUM(buildings_2_floors) AS BIGINT) AS p2,
      CAST(SUM(buildings_3_floors) AS BIGINT) AS p3,
      CAST(SUM(buildings_over_3_floors) AS BIGINT) AS pm,
      CAST(SUM(shelters) AS BIGINT) AS alb
    FROM entries WHERE NOT is_municipality_total AND NOT is_district_total
  `);
  const p = floors[0];
  const totalBuildings = p.p1 + p.p2 + p.p3 + p.pm + p.alb;
  const dist = [
    ["Una planta", p.p1],
    ["Dues plantes", p.p2],
    ["Tres plantes", p.p3],
    ["Més de tres plantes", p.pm],
    ["Albergs / coves / barraques", p.alb],
  ];
  renderSimpleTable("t-floors", ["Tipus", "Quantitat", "%"], dist, r => [r[0], r[1].toLocaleString("ca-ES"), `${(100 * r[1] / totalBuildings).toFixed(1)}%`]);

  await loadSummaries();
}

const DISTRICT_ORDER = ["Ibiza", "Inca", "Mahon", "Manacor", "Palma"];

async function loadSummaries() {
  for (const chart of [1, 2, 3, 4]) {
    const rows = await query(
      `SELECT judicial_district, is_total, values, columns, chart_title
       FROM summaries WHERE chart_num = ? ORDER BY is_total, judicial_district`,
      [chart]
    );
    if (!rows.length) continue;
    const cols = rows[0].columns;
    document.getElementById(`r-c${chart}-title`).textContent =
      `Quadre ${chart} — ${rows[0].chart_title}`;
    rows.sort((a, b) => {
      if (a.is_total !== b.is_total) return a.is_total ? 1 : -1;
      return DISTRICT_ORDER.indexOf(a.judicial_district) - DISTRICT_ORDER.indexOf(b.judicial_district);
    });
    renderSummary(`t-summary-c${chart}`, cols, rows);
  }
}

function renderSummary(tableId, cols, rows) {
  const t = document.getElementById(tableId);
  const headerCells = `<th>Partit</th>${cols.map(c => `<th class="num">${esc(c)}</th>`).join("")}`;
  const bodyRows = rows.map(r => {
    const label = r.is_total ? "TOTAL" : r.judicial_district;
    const cls = r.is_total ? "is-total" : "";
    const values = r.values.map(v =>
      `<td class="num">${v == null ? '<span style="color:#ccc">·</span>' : Number(v).toLocaleString("ca-ES")}</td>`
    ).join("");
    return `<tr class="${cls}"><td><strong>${esc(label)}</strong></td>${values}</tr>`;
  }).join("");
  t.innerHTML = `<thead><tr>${headerCells}</tr></thead><tbody>${bodyRows}</tbody>`;
}

function renderSimpleTable(id, headers, rows, rowFn) {
  const t = document.getElementById(id);
  t.innerHTML = `
    <thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => {
      const cells = rowFn(r);
      return `<tr>${cells.map((c, i) => `<td class="${i === 0 ? "" : "num"}">${esc(c)}</td>`).join("")}</tr>`;
    }).join("")}</tbody>
  `;
}

// === CHARTS (Vega-Lite) ===
// Carrega les 5 gràfiques de la pestanya Gràfiques. Es crida una sola
// vegada per sessió (`_chartsLoaded` flag) per no repetir queries cares.
let _chartsLoaded = false;

const VEGA_THEME = {
  config: {
    font: "system-ui, sans-serif",
    background: null,
    view: { stroke: null },
    axis: { labelFontSize: 11, titleFontSize: 12, labelColor: "#3d3022",
            titleColor: "#3d3022", gridColor: "#e5dccf" },
    legend: { labelFontSize: 11, titleFontSize: 12 },
    title: { fontSize: 13, color: "#5e2620" },
    range: { category: ["#5e2620","#a04f3c","#c98455","#7c8c6e","#3d5a3d",
                        "#8b6b4f","#b8a07c","#4a6d8a","#6b4561","#8c8c5e"] },
  }
};

async function loadCharts() {
  if (_chartsLoaded) return;
  _chartsLoaded = true;
  try {
    await Promise.all([
      chartClasses(),
      chartOccupancy(),
      chartDistance(),
      chartPareto(),
      chartToponymRoots(),
    ]);
  } catch (err) {
    console.error("Error carregant gràfiques:", err);
  }
}

// 1. Donut de classes d'edifici (top 10 + altres)
async function chartClasses() {
  const rows = await query(`
    WITH ranked AS (
      SELECT class_normalized AS cls, COUNT(*) AS n,
             ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rk
      FROM entries
      WHERE NOT is_municipality_total AND NOT is_district_total
        AND class_normalized IS NOT NULL
      GROUP BY 1
    )
    SELECT cls, n FROM ranked WHERE rk <= 10
    UNION ALL
    SELECT 'altres' AS cls, SUM(n) FROM ranked WHERE rk > 10
  `);
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: 360,
    data: { values: rows },
    mark: { type: "arc", innerRadius: 80, stroke: "#fdf8f1", strokeWidth: 2 },
    encoding: {
      theta: { field: "n", type: "quantitative", stack: true },
      color: { field: "cls", type: "nominal", title: "Classe",
               sort: { field: "n", order: "descending" },
               legend: { orient: "right", labelLimit: 220 } },
      tooltip: [
        { field: "cls", type: "nominal", title: "Classe" },
        { field: "n", type: "quantitative", title: "Files", format: "," },
      ],
    },
  };
  await vegaEmbed("#chart-classes", spec, { actions: false });
}

// 2. Barres apilades normalitzades HC/HT/Inh per partit
async function chartOccupancy() {
  const rows = await query(`
    WITH d AS (
      SELECT judicial_district,
             CAST(SUM(inhabited_permanent) AS BIGINT) AS hc,
             CAST(SUM(inhabited_seasonal) AS BIGINT) AS ht,
             CAST(SUM(uninhabited) AS BIGINT) AS inh
      FROM entries
      WHERE NOT is_municipality_total AND NOT is_district_total
      GROUP BY 1
    )
    SELECT judicial_district AS partit, 'Habitats constantment' AS tipus, hc AS valor FROM d
    UNION ALL SELECT judicial_district, 'Habitats temporalment', ht FROM d
    UNION ALL SELECT judicial_district, 'Inhabitats', inh FROM d
  `);
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: 320,
    data: { values: rows },
    mark: { type: "bar", stroke: "#fdf8f1", strokeWidth: 1 },
    encoding: {
      x: { field: "partit", type: "nominal", title: null,
           sort: ["Ibiza","Inca","Mahon","Manacor","Palma"] },
      y: { field: "valor", type: "quantitative", stack: "normalize",
           title: "% d'edificis", axis: { format: "%" } },
      color: { field: "tipus", type: "nominal", title: null,
               scale: { domain: ["Habitats constantment","Habitats temporalment","Inhabitats"],
                        range: ["#3d5a3d","#c98455","#8b6b4f"] },
               legend: { orient: "top" } },
      tooltip: [
        { field: "partit", type: "nominal", title: "Partit" },
        { field: "tipus", type: "nominal", title: "Tipus" },
        { field: "valor", type: "quantitative", title: "Edificis", format: "," },
      ],
    },
  };
  await vegaEmbed("#chart-occupancy", spec, { actions: false });
}

// 3. Boxplot distance_km per classe (top 8 classes amb >= 30 files i km no-NULL)
async function chartDistance() {
  const rows = await query(`
    WITH top_classes AS (
      SELECT class_normalized, COUNT(*) AS n
      FROM entries
      WHERE NOT is_municipality_total AND NOT is_district_total
        AND class_normalized IS NOT NULL AND distance_km IS NOT NULL
      GROUP BY 1 HAVING COUNT(*) >= 30
      ORDER BY 2 DESC LIMIT 8
    )
    SELECT e.class_normalized AS cls, e.distance_km AS km
    FROM entries e
    WHERE NOT e.is_municipality_total AND NOT e.is_district_total
      AND e.distance_km IS NOT NULL
      AND e.class_normalized IN (SELECT class_normalized FROM top_classes)
  `);
  // Mediana per ordenar
  const med = {};
  const grp = {};
  for (const r of rows) {
    if (!grp[r.cls]) grp[r.cls] = [];
    grp[r.cls].push(r.km);
  }
  for (const c in grp) {
    const arr = grp[c].slice().sort((a,b) => a-b);
    med[c] = arr[Math.floor(arr.length/2)];
  }
  const order = Object.keys(med).sort((a,b) => med[a] - med[b]);
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: 340,
    data: { values: rows },
    mark: { type: "boxplot", size: 18, color: "#a04f3c",
            outliers: { color: "#5e2620", opacity: 0.4, size: 18 } },
    encoding: {
      x: { field: "km", type: "quantitative", title: "Distància al nucli (km)",
           scale: { domainMin: 0 } },
      y: { field: "cls", type: "nominal", title: null, sort: order },
      tooltip: [
        { field: "cls", type: "nominal", title: "Classe" },
        { field: "km", type: "quantitative", title: "km", format: ".1f" },
      ],
    },
  };
  await vegaEmbed("#chart-distance", spec, { actions: false });
}

// 4. Pareto: % acumulat d'edificis vs ranking de topònim
async function chartPareto() {
  const rows = await query(`
    WITH r AS (
      SELECT place, municipality, total,
             ROW_NUMBER() OVER (ORDER BY total DESC) AS rk,
             SUM(total) OVER (ORDER BY total DESC ROWS UNBOUNDED PRECEDING) AS cum
      FROM entries
      WHERE NOT is_municipality_total AND NOT is_district_total
        AND total IS NOT NULL AND total > 0
    ),
    total AS (SELECT SUM(total) AS t FROM r WHERE rk=rk)
    SELECT r.rk, r.place, r.municipality, r.total,
           100.0 * r.rk / (SELECT MAX(rk) FROM r) AS pct_places,
           100.0 * r.cum / (SELECT MAX(cum) FROM r) AS pct_buildings
    FROM r
    ORDER BY rk
  `);
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: 320,
    data: { values: rows },
    layer: [
      {
        mark: { type: "line", color: "#5e2620", strokeWidth: 2 },
        encoding: {
          x: { field: "pct_places", type: "quantitative",
               title: "% de topònims (ordenats per mida descendent)",
               axis: { format: ".0f", values: [0,10,20,30,40,50,60,70,80,90,100] } },
          y: { field: "pct_buildings", type: "quantitative",
               title: "% acumulat d'edificis",
               axis: { format: ".0f", values: [0,10,20,30,40,50,60,70,80,90,100] } },
        },
      },
      {
        mark: { type: "rule", color: "#a04f3c", strokeDash: [4,4], opacity: 0.7 },
        data: { values: [{ x: 20 }] },
        encoding: { x: { field: "x", type: "quantitative" } },
      },
      {
        mark: { type: "rule", color: "#a04f3c", strokeDash: [4,4], opacity: 0.7 },
        data: { values: [{ y: 80 }] },
        encoding: { y: { field: "y", type: "quantitative" } },
      },
    ],
  };
  await vegaEmbed("#chart-pareto", spec, { actions: false });
}

// 5. Top arrels toponímiques amb LIKE sobre place
async function chartToponymRoots() {
  // Patrons triats segons frequencies reals al dataset (verificats amb
  // split_part(place, ' ', 1)). LIKE és més fiable que regex_matches per
  // a textos curts amb accents i apostrofs.
  const rows = await query(`
    SELECT root, COUNT(*) AS n
    FROM (
      SELECT CASE
        WHEN place LIKE 'Son %' OR place LIKE 'Son-%' THEN 'Son'
        WHEN place LIKE 'Ca''n %' OR place LIKE 'Ca na %' OR place LIKE 'Ca''s %'
          OR place LIKE 'Ca''l %' OR place LIKE 'Ca de %' THEN 'Ca''n / Ca''s / Ca na'
        WHEN place LIKE 'Molí%' OR place LIKE 'Molino%' OR place LIKE 'Molins%' THEN 'Molí / Molins'
        WHEN place LIKE 'Sant %' OR place LIKE 'Santa %' OR place LIKE 'San %' THEN 'Sant / Santa / San'
        WHEN place LIKE 'Venda %' OR place LIKE 'Venda d%' THEN 'Venda (eivissenc)'
        WHEN place LIKE 'Hort %' OR place LIKE 'Hort d%' OR place LIKE 'Horta%' THEN 'Hort / Horta'
        WHEN place LIKE 'Casetas %' OR place LIKE 'Casetas d%' THEN 'Casetas (de labradors)'
        WHEN place LIKE 'Torre %' OR place LIKE 'Torre d%' OR place LIKE 'Torret%' THEN 'Torre / Torret'
        WHEN place LIKE 'Rafal %' OR place LIKE 'Rafal-%' OR place LIKE 'Rafal''%' THEN 'Rafal'
        WHEN place LIKE 'Alquería%' THEN 'Alqueria'
        WHEN place LIKE 'Camp %' OR place LIKE 'Camp d%' THEN 'Camp'
        WHEN place LIKE 'Pl_ %' OR place LIKE 'Pl_ d%' THEN 'Plá / Pla'
        WHEN place LIKE 'Coll %' OR place LIKE 'Coll d%' THEN 'Coll'
        WHEN place LIKE 'Coma %' OR place LIKE 'Coma d%' THEN 'Coma'
        WHEN place LIKE 'P_ig%' OR place LIKE 'Pújig%' THEN 'Puig / Púig'
        WHEN place LIKE 'Pujol%' THEN 'Pujol'
        WHEN place LIKE 'Sementeri%' THEN 'Sementeri'
        WHEN place LIKE 'Costa %' OR place LIKE 'Costa d%' THEN 'Costa'
        WHEN place LIKE 'Taulera%' THEN 'Taulera'
        ELSE NULL
      END AS root
      FROM entries
      WHERE NOT is_municipality_total AND NOT is_district_total
        AND place IS NOT NULL
    )
    WHERE root IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC
  `);
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: 360,
    data: { values: rows },
    mark: { type: "bar", color: "#5e2620" },
    encoding: {
      y: { field: "root", type: "nominal", title: null,
           sort: { field: "n", order: "descending" } },
      x: { field: "n", type: "quantitative", title: "Topònims",
           axis: { format: "," } },
      tooltip: [
        { field: "root", type: "nominal", title: "Arrel" },
        { field: "n", type: "quantitative", title: "Topònims", format: "," },
      ],
    },
  };
  await vegaEmbed("#chart-roots", spec, { actions: false });
}

// === SQL CONSOLE ===
async function runSql() {
  const sql = document.getElementById("sql-input").value.trim();
  const status = document.getElementById("sql-status");
  const result = document.getElementById("t-sql-result");
  if (!sql) return;
  status.className = "";
  status.textContent = "Executant…";
  try {
    const t0 = performance.now();
    const rows = await query(sql);
    const elapsed = (performance.now() - t0).toFixed(0);
    status.className = "ok";
    status.textContent = `${rows.length} fila${rows.length === 1 ? "" : "s"} · ${elapsed} ms`;
    if (rows.length === 0) {
      result.innerHTML = '<tbody><tr><td class="empty">Sense files.</td></tr></tbody>';
      return;
    }
    const headers = Object.keys(rows[0]);
    result.innerHTML = `
      <thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${rows.slice(0, 1000).map(r =>
        `<tr>${headers.map(h => {
          const v = r[h];
          const isNum = typeof v === "number";
          return `<td class="${isNum ? "num" : ""}">${v == null ? '<span style="color:#ccc">·</span>' : esc(v)}</td>`;
        }).join("")}</tr>`
      ).join("")}</tbody>
    `;
    if (rows.length > 1000) status.textContent += " (mostrant primeres 1000)";
  } catch (err) {
    status.className = "error";
    status.textContent = `Error: ${err.message || err}`;
    result.innerHTML = "";
  }
}

// === URL STATE (bookmarkable filters) ===
const URL_TABS = {
  explore: {
    ref: () => state,
    inputs: { place: "#f-place", km_min: "#f-km-min", km_max: "#f-km-max",
              include_totals: "#f-include-totals" },
    init: async () => {
      await refillMunicipalities();
      await refillClasses();
      await loadResults();
    },
  },
};

function _coerceForState(raw, current) {
  if (typeof current === "boolean") return raw === "true";
  if (typeof current === "number") return Number(raw);
  if (current === null && /^-?\d+(\.\d+)?$/.test(raw)) return Number(raw);
  return raw;
}

let _applyingUrl = false;

function syncUrlFromState() {
  try {
    if (_applyingUrl) return;
    const top = document.querySelector("nav.tabs-main .tab.active")?.dataset.toptab;
    if (!top) return;
    const params = new URLSearchParams();
    params.set("t", top);
    const conf = URL_TABS[top];
    if (conf) {
      const s = conf.ref();
      if (s) {
        for (const [k, v] of Object.entries(s)) {
          if (k === "loaded") continue;
          if (k === "page" || k.startsWith("sort_")) continue;
          if (v === null || v === undefined || v === "" || v === false) continue;
          params.set(k, String(v));
        }
      }
    }
    if (top === "sql") {
      const q = document.getElementById("sql-input")?.value?.trim();
      if (q && q.length < 800) params.set("q", q);
    }
    const hash = "#" + params.toString();
    if (location.hash !== hash) {
      history.replaceState(null, "", hash);
    }
  } catch (e) {
    console.error("syncUrlFromState error:", e);
  }
}

async function applyStateFromUrl() {
  const raw = location.hash.startsWith("#") ? location.hash.slice(1) : "";
  if (!raw) return;
  _applyingUrl = true;
  try {
    const params = new URLSearchParams(raw);
    const top = params.get("t") || "home";

    const conf = URL_TABS[top];

    if (conf?.ref) {
      const s = conf.ref();
      if (s) {
        for (const key of params.keys()) {
          if (key === "t" || key === "u" || key === "q") continue;
          if (!(key in s)) continue;
          s[key] = _coerceForState(params.get(key), s[key]);
        }
      }
    }

    switchTopTab(top);

    if (conf?.inputs) {
      const s = conf.ref();
      for (const [k, sel] of Object.entries(conf.inputs)) {
        const el = document.querySelector(sel);
        if (!el) continue;
        const v = s?.[k];
        if (el.type === "checkbox") el.checked = !!v;
        else el.value = v ?? "";
      }
    }

    if (top === "explore") {
      await refillMunicipalities();
      await refillClasses();
      await loadResults();
    }

    if (top === "sql") {
      const q = params.get("q");
      if (q) document.getElementById("sql-input").value = q;
    }
  } finally {
    setTimeout(() => { _applyingUrl = false; }, 50);
  }
}

// === TAB SWITCHING ===
function switchTopTab(top) {
  document.querySelectorAll("nav.tabs-main .tab").forEach(b =>
    b.classList.toggle("active", b.dataset.toptab === top)
  );
  document.querySelectorAll(".tab-content").forEach(s => {
    s.classList.toggle("active", s.dataset.toptab === top);
  });
  if (top === "stats") loadStats();
  if (top === "charts") loadCharts();
  syncUrlFromState();
}

// === EVENT WIRING ===
function wireEvents() {
  document.addEventListener("input", e => {
    if (e.target.closest("aside.filters, #sql-input")) {
      setTimeout(syncUrlFromState, 0);
    }
  });
  document.addEventListener("change", e => {
    if (e.target.closest("aside.filters")) {
      setTimeout(syncUrlFromState, 0);
    }
  });
  window.addEventListener("hashchange", () => {
    if (!_applyingUrl) applyStateFromUrl();
  });

  document.querySelectorAll("nav.tabs-main .tab").forEach(btn => {
    btn.addEventListener("click", () => switchTopTab(btn.dataset.toptab));
  });
  document.querySelectorAll(".home-action[data-goto]").forEach(btn => {
    btn.addEventListener("click", () => switchTopTab(btn.dataset.goto));
  });

  const debouncedReload = debounce(() => { state.page = 0; loadResults(); }, 200);
  document.getElementById("f-place").addEventListener("input", e => { state.place = e.target.value.trim(); debouncedReload(); });
  document.getElementById("f-district").addEventListener("change", async e => {
    state.district = e.target.value;
    state.page = 0;
    await refillMunicipalities();
    await refillClasses();
    loadResults();
  });
  document.getElementById("f-municipality").addEventListener("change", async e => {
    state.municipality = e.target.value;
    state.page = 0;
    await refillClasses();
    loadResults();
  });
  document.getElementById("f-class").addEventListener("change", e => { state.placeClass = e.target.value; state.page = 0; loadResults(); });
  document.getElementById("f-km-min").addEventListener("input", e => { state.km_min = e.target.value === "" ? null : parseFloat(e.target.value); debouncedReload(); });
  document.getElementById("f-km-max").addEventListener("input", e => { state.km_max = e.target.value === "" ? null : parseFloat(e.target.value); debouncedReload(); });
  document.getElementById("f-include-totals").addEventListener("change", e => { state.include_totals = e.target.checked; state.page = 0; loadResults(); });
  document.getElementById("btn-clear").addEventListener("click", async () => {
    state = { ...state, place: "", district: "", municipality: "", placeClass: "", km_min: null, km_max: null, include_totals: false, page: 0 };
    document.querySelectorAll("aside.filters input, aside.filters select").forEach(el => {
      if (el.type === "checkbox") el.checked = false;
      else el.value = "";
    });
    await refillMunicipalities();
    await refillClasses();
    loadResults();
  });

  document.getElementById("btn-prev").addEventListener("click", () => { if (state.page > 0) { state.page--; loadResults(); }});
  document.getElementById("btn-next").addEventListener("click", () => { state.page++; loadResults(); });

  document.querySelectorAll("thead th[data-sort]").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      if (state.sort_col === col) {
        state.sort_dir = state.sort_dir === "asc" ? "desc" : "asc";
      } else {
        state.sort_col = col;
        state.sort_dir = "asc";
      }
      document.querySelectorAll("thead th[data-sort]").forEach(t => t.classList.remove("sorted-asc", "sorted-desc"));
      th.classList.add(state.sort_dir === "asc" ? "sorted-asc" : "sorted-desc");
      loadResults();
    });
  });

  document.getElementById("btn-sql-run").addEventListener("click", runSql);
  document.getElementById("sql-input").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runSql();
  });

  const btnExport = document.getElementById("btn-export-1860");
  if (btnExport) btnExport.addEventListener("click", export1860);
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// === MAIN ===
(async function main() {
  wireEvents();

  setStatus("Inicialitzant DuckDB-WASM (~3 MB de WASM)…");
  try {
    await initDuckDB();
    setStatus("Carregant dades…");
    await Promise.all([fillFilters(), loadSourceStats(), loadFreshness()]);
    await loadResults();
    if (location.hash && location.hash.length > 1) {
      await applyStateFromUrl();
    }
    setStatus("");
  } catch (err) {
    console.error("Error inicialitzant:", err);
    setStatus(`Error: ${err.message || err}`, true);
    document.getElementById("tbody-results").innerHTML =
      `<tr><td colspan="14" class="empty">Error carregant DuckDB-WASM: ${esc(err.message || String(err))}<br><br>Revisa la consola del navegador (F12) per a més detalls.</td></tr>`;
  }
})();

function setStatus(msg, isError = false) {
  let bar = document.getElementById("status-bar");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "status-bar";
    bar.style.cssText = "position:fixed;bottom:0;left:0;right:0;padding:0.6em 1em;background:#5e2620;color:white;font-size:0.85em;text-align:center;z-index:1000;transition:opacity 0.3s";
    document.body.appendChild(bar);
  }
  if (!msg) { bar.style.opacity = "0"; setTimeout(() => bar.remove(), 300); return; }
  bar.style.background = isError ? "#5e2620" : "#3d5a3d";
  bar.style.opacity = "1";
  bar.textContent = msg;
}
