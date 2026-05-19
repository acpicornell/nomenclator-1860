// 1860 Nomenclator — static web amb dades JSON pures.
// No fa servir DuckDB-WASM ni cap dependència externa: tota la lògica
// de query corre en JavaScript dins el navegador, sobre arrays carregats
// per fetch() inicial.

const PAGE_SIZE = 50;

// Estat global de les dades carregades
const DB = {
  entries: [],   // 3.026 entrades (excloent pàg.50)
  notes: [],
  summaries: [],
  errata: [],
  source_metadata: [],
};

// Lookup ràpid notes per (page, ref)
const notesByKey = new Map();

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

// === DATA LOAD ===
// Sense cache-busting per query string: el servidor envia
// Cache-Control: no-store (vegeu web/_headers), així el navegador
// no guarda mai cap còpia local i sempre demana el deploy més recent.
async function loadData() {
  const get = (name) => fetch(`data/${name}.json`).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status} loading ${name}.json`);
    return r.json();
  });
  const [entries, notes, summaries, errata, meta] = await Promise.all([
    get("entries"), get("notes"), get("summaries"),
    get("errata"), get("source_metadata"),
  ]);
  DB.entries = entries;
  DB.notes = notes;
  DB.summaries = summaries;
  DB.errata = errata;
  DB.source_metadata = meta;
  // Lookup notes per (page, ref) — usat pels popovers de la taula
  notesByKey.clear();
  for (const n of DB.notes) {
    if (n.page != null && n.ref != null) {
      notesByKey.set(`${n.page}|${n.ref}`, n);
    }
  }
}

// === HELPERS JS (substitueixen SQL bàsic) ===
function distinctSorted(arr, key, filterFn = null) {
  const set = new Set();
  for (const x of arr) {
    if (filterFn && !filterFn(x)) continue;
    const v = x[key];
    if (v != null) set.add(v);
  }
  return [...set].sort((a, b) => String(a).localeCompare(String(b)));
}

function countBy(arr, key, filterFn = null) {
  const m = new Map();
  for (const x of arr) {
    if (filterFn && !filterFn(x)) continue;
    const v = x[key];
    if (v == null) continue;
    m.set(v, (m.get(v) || 0) + 1);
  }
  return m;
}

function sumBy(arr, key, filterFn = null) {
  let s = 0;
  for (const x of arr) {
    if (filterFn && !filterFn(x)) continue;
    s += x[key] || 0;
  }
  return s;
}

function groupAggregate(arr, groupKey, aggregators, filterFn = null) {
  // aggregators: { name: (rows) => value }
  const groups = new Map();
  for (const x of arr) {
    if (filterFn && !filterFn(x)) continue;
    const k = x[groupKey];
    if (k == null) continue;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(x);
  }
  const out = [];
  for (const [k, items] of groups) {
    const row = { [groupKey]: k };
    for (const name in aggregators) row[name] = aggregators[name](items);
    out.push(row);
  }
  return out;
}

function sortBy(arr, col, dir = "asc") {
  const mul = dir === "desc" ? -1 : 1;
  return arr.slice().sort((a, b) => {
    const av = a[col], bv = b[col];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;   // nulls last
    if (bv == null) return -1;
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * mul;
    return String(av).localeCompare(String(bv), "ca") * mul;
  });
}

// Aplica els filtres de l'estat sobre DB.entries.
function filterEntries(s = state, includeTotalsOverride = null) {
  let r = DB.entries;
  if (s.place) {
    const p = s.place.toLowerCase();
    r = r.filter(e => (e.place || "").toLowerCase().includes(p));
  }
  if (s.district) r = r.filter(e => e.judicial_district === s.district);
  if (s.municipality) r = r.filter(e => e.municipality === s.municipality);
  if (s.placeClass) r = r.filter(e => e.class_normalized === s.placeClass);
  if (s.km_min != null) r = r.filter(e => e.distance_km != null && e.distance_km >= s.km_min);
  if (s.km_max != null) r = r.filter(e => e.distance_km != null && e.distance_km <= s.km_max);
  const incl = includeTotalsOverride !== null ? includeTotalsOverride : s.include_totals;
  if (!incl) r = r.filter(e => !e.is_municipality_total && !e.is_district_total);
  return r;
}

// Predicats senzills reutilitzats arreu
const isNormal = e => !e.is_municipality_total && !e.is_district_total;
const hasMuni = e => e.municipality != null && e.municipality !== "SUMMARY";

// === FILL FILTER DROPDOWNS ===
async function fillFilters() {
  const districts = distinctSorted(DB.entries, "judicial_district");
  fillSelect("f-district", districts.map(v => ({ v })));
  await refillMunicipalities();
  await refillClasses();
}

async function refillMunicipalities() {
  const filterFn = state.district
    ? e => e.judicial_district === state.district
    : null;
  const munis = distinctSorted(DB.entries, "municipality", filterFn);
  fillSelect("f-municipality", munis.map(v => ({ v })));
  if (state.municipality && !munis.includes(state.municipality)) {
    state.municipality = "";
  }
  document.getElementById("f-municipality").value = state.municipality || "";
}

async function refillClasses() {
  const filterFn = e => {
    if (state.district && e.judicial_district !== state.district) return false;
    if (state.municipality && e.municipality !== state.municipality) return false;
    return e.class_normalized != null;
  };
  const counts = countBy(DB.entries, "class_normalized", filterFn);
  const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 40);
  fillSelect("f-class", sorted.map(([v, n]) => ({ v, n })),
             r => `${r.v} (${r.n})`);
  if (state.placeClass && !sorted.some(([v]) => v === state.placeClass)) {
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

// === STATS GENERALS (per al header de la pestanya Explorar i Inici) ===
async function loadSourceStats() {
  const normal = DB.entries.filter(isNormal);
  const munis = new Set(
    DB.entries.filter(e => hasMuni(e)).map(e => e.municipality)
  ).size;
  const districts = new Set(
    DB.entries.map(e => e.judicial_district).filter(Boolean)
  ).size;
  const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  const fmt = n => n.toLocaleString("ca-ES");
  setText("stat-rows", fmt(normal.length));
  setText("stat-munis", fmt(munis));
  setText("stat-districts", fmt(districts));
  setText("stat-notes", fmt(DB.notes.length));
  setText("home-stat-rows", fmt(normal.length));
  setText("home-stat-munis", fmt(munis));
  setText("home-stat-districts", fmt(districts));
  setText("home-stat-notes", fmt(DB.notes.length));
}

// === EXPLORE: paginació i renderitzat ===
async function loadResults() {
  const filtered = filterEntries(state);
  const sorted = sortBy(filtered, state.sort_col || "municipality", state.sort_dir);
  const total = sorted.length;
  document.getElementById("results-count").innerHTML =
    `<strong>${total.toLocaleString("ca-ES")}</strong> entrades`;
  const offset = state.page * PAGE_SIZE;
  const slice = sorted.slice(offset, offset + PAGE_SIZE);
  renderTable(slice);
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
      <td>${renderNoteCell(r)}</td>
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

// Renderitza la cel·la "Nota" de la taula d'entries.
// Si la referencia matcha una nota a peu de pàgina, és clickable i obre un
// popover amb el text complet. Si no, només mostra el text literal (cas
// rar de metadades llargues a algunes files TOTAL PARTIDO).
function renderNoteCell(entry) {
  if (!entry.note_ref) return "";
  const key = `${entry.page}|${entry.note_ref}`;
  if (notesByKey.has(key)) {
    return `<span class="note-ref" data-page="${entry.page}" data-ref="${esc(entry.note_ref)}">(${esc(entry.note_ref)})</span>`;
  }
  return esc(entry.note_ref);
}

function showNotePopover(anchor, note) {
  document.getElementById("note-popover")?.remove();
  const p = document.createElement("div");
  p.id = "note-popover";
  p.className = "note-popover";
  const muniLine = note.municipality
    ? `<em class="note-muni">${esc(note.municipality)}</em>` : "";
  p.innerHTML = `
    <button class="note-close" aria-label="Tancar">&times;</button>
    <div class="note-meta">Pàgina ${esc(note.page)} · nota (${esc(note.ref)})</div>
    ${muniLine}
    <p class="note-text">${esc(note.text)}</p>
  `;
  document.body.appendChild(p);
  // Posiciona sota l'àncora, ajustat per no sortir-se de la finestra
  const rect = anchor.getBoundingClientRect();
  const popW = 360;
  const top = window.scrollY + rect.bottom + 6;
  let left = rect.left + window.scrollX - 10;
  if (left + popW > window.scrollX + window.innerWidth - 10) {
    left = window.scrollX + window.innerWidth - popW - 10;
  }
  if (left < window.scrollX + 10) left = window.scrollX + 10;
  p.style.top = top + "px";
  p.style.left = left + "px";
}

function closeNotePopover() {
  document.getElementById("note-popover")?.remove();
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
  const meta = DB.source_metadata.find(m => m.source_name === "1860");
  if (!meta) return;
  const el = document.getElementById("fresh-1860");
  if (!el) return;
  el.textContent = formatRelativeTime(new Date(meta.fetched_at));
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
  let filtered = filterEntries(state);
  // En CSV també tenim en compte la cerca per municipi a 'place' (legacy)
  // del codi DuckDB, però la funció actual ja filtra place individual.
  const sorted = sortBy(filtered, state.sort_col, state.sort_dir);
  const COLS = ["page","judicial_district","municipality","place","place_class",
                "class_normalized","distance_km","inhabited_permanent",
                "inhabited_seasonal","uninhabited","buildings_1_floor",
                "buildings_2_floors","buildings_3_floors","buildings_over_3_floors",
                "shelters","total","is_municipality_total","is_district_total"];
  downloadCsv(csvFilename("nomenclator_1860"), sorted, COLS);
}

function updatePagination(total) {
  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);
  document.getElementById("btn-prev").disabled = state.page === 0;
  document.getElementById("btn-next").disabled = state.page >= lastPage;
  document.getElementById("page-info").textContent = `pàgina ${state.page + 1} de ${lastPage + 1}`;
}

// === STATS (pestanya Estadístiques) ===
async function loadStats() {
  const normal = DB.entries.filter(isNormal);

  // Taula 1: edificis per partit judicial
  const byDistrict = groupAggregate(
    normal, "judicial_district",
    { places: r => r.length, total: r => sumBy(r, "total") }
  );
  byDistrict.sort((a, b) => b.total - a.total);
  renderSimpleTable("t-districts",
    ["Partit", "Poblacions", "Edificis"],
    byDistrict,
    r => [r.judicial_district,
          r.places.toLocaleString("ca-ES"),
          r.total.toLocaleString("ca-ES")]);

  // Taula 2: top 15 municipis per edificis
  const byMuni = groupAggregate(
    normal.filter(hasMuni), "municipality",
    { total: r => sumBy(r, "total") }
  );
  byMuni.sort((a, b) => b.total - a.total);
  const top15 = byMuni.slice(0, 15);
  renderSimpleTable("t-top-munis",
    ["Municipi", "Edificis"],
    top15,
    r => [r.municipality, r.total.toLocaleString("ca-ES")]);

  // Taula 3: classes més freqüents
  const classes = countBy(normal, "class_normalized");
  const classList = [...classes.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([cls, n]) => ({ cls, n }));
  renderSimpleTable("t-classes",
    ["Classe", "Nº files"],
    classList,
    r => [r.cls, r.n.toLocaleString("ca-ES")]);

  // Taula 4: distribució per nombre de plantes
  const p1 = sumBy(normal, "buildings_1_floor");
  const p2 = sumBy(normal, "buildings_2_floors");
  const p3 = sumBy(normal, "buildings_3_floors");
  const pm = sumBy(normal, "buildings_over_3_floors");
  const alb = sumBy(normal, "shelters");
  const totalBuildings = p1 + p2 + p3 + pm + alb;
  const dist = [
    ["Una planta", p1],
    ["Dues plantes", p2],
    ["Tres plantes", p3],
    ["Més de tres plantes", pm],
    ["Albergs / coves / barraques", alb],
  ];
  renderSimpleTable("t-floors",
    ["Tipus", "Quantitat", "%"],
    dist,
    r => [r[0],
          r[1].toLocaleString("ca-ES"),
          `${(100 * r[1] / totalBuildings).toFixed(1)}%`]);

  await loadSummaries();
}

const DISTRICT_ORDER = ["Ibiza", "Inca", "Mahon", "Manacor", "Palma"];

async function loadSummaries() {
  for (const chart of [1, 2, 3, 4]) {
    const rows = DB.summaries.filter(s => s.chart_num === chart);
    if (!rows.length) continue;
    const cols = rows[0].columns;
    const title = rows[0].chart_title;
    document.getElementById(`r-c${chart}-title`).textContent =
      `Quadre ${chart} — ${title}`;
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
      populateClassesMuniFilter(),
      chartClasses(),
      setupOccupancyChart(),
      chartDistance(),
      chartPareto(),
      chartToponymRoots(),
      setupFloorsChart(),
    ]);
  } catch (err) {
    console.error("Error carregant gràfiques:", err);
  }
}

async function populateClassesMuniFilter() {
  const sel = document.getElementById("f-classes-muni");
  if (!sel) return;
  const munis = distinctSorted(DB.entries, "municipality",
                               e => isNormal(e) && hasMuni(e));
  for (const m of munis) {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    sel.appendChild(opt);
  }
  sel.addEventListener("change", () => chartClasses(sel.value));
}

// 1. Donut top-10 + altres
async function chartClasses(municipality = "") {
  const filterFn = e => {
    if (!isNormal(e)) return false;
    if (e.class_normalized == null) return false;
    if (municipality && e.municipality !== municipality) return false;
    return true;
  };
  const counts = countBy(DB.entries, "class_normalized", filterFn);
  const sorted = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([cls, n]) => ({ cls, n }));
  const top10 = sorted.slice(0, 10);
  const others = sorted.slice(10).reduce((s, r) => s + r.n, 0);
  const rows = others > 0 ? top10.concat([{ cls: "altres", n: others }]) : top10;
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

// 2. HC/HT/Inh apilades normalitzades
const OCCUPANCY_DOMAIN = ["Habitats constantment", "Habitats temporalment", "Inhabitats"];
const OCCUPANCY_COLORS = ["#3d5a3d", "#c98455", "#8b6b4f"];

async function setupOccupancyChart() {
  const sel = document.getElementById("f-occupancy-group");
  if (!sel) return;
  sel.addEventListener("change", () => chartOccupancy(sel.value));
  await chartOccupancy(sel.value);
}

async function chartOccupancy(mode = "district") {
  const isDistrict = mode === "district";
  const groupCol = isDistrict ? "judicial_district" : "municipality";
  const normal = DB.entries.filter(e => isNormal(e) && (isDistrict || hasMuni(e)));
  let grouped = groupAggregate(normal, groupCol, {
    hc:  r => sumBy(r, "inhabited_permanent"),
    ht:  r => sumBy(r, "inhabited_seasonal"),
    inh: r => sumBy(r, "uninhabited"),
    tot: r => sumBy(r, "total"),
  });
  grouped.sort((a, b) => b.tot - a.tot);
  if (mode === "muni-top20") grouped = grouped.slice(0, 20);
  const rows = [];
  for (const g of grouped) {
    rows.push({ grp: g[groupCol], tipus: OCCUPANCY_DOMAIN[0], valor: g.hc,  total: g.tot });
    rows.push({ grp: g[groupCol], tipus: OCCUPANCY_DOMAIN[1], valor: g.ht,  total: g.tot });
    rows.push({ grp: g[groupCol], tipus: OCCUPANCY_DOMAIN[2], valor: g.inh, total: g.tot });
  }
  const order = grouped.map(g => g[groupCol]);
  const isMany = mode !== "district";
  const groupTitle = isDistrict ? "Partit judicial" : "Municipi";
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: isMany ? Math.max(360, order.length * 22 + 60) : 320,
    data: { values: rows },
    mark: { type: "bar", stroke: "#fdf8f1", strokeWidth: 0.5 },
    encoding: {
      [isMany ? "y" : "x"]: {
        field: "grp", type: "nominal",
        title: isMany ? null : groupTitle,
        sort: order,
        axis: isMany ? { labelLimit: 200 } : { labelAngle: 0 },
      },
      [isMany ? "x" : "y"]: {
        field: "valor", type: "quantitative",
        stack: "normalize",
        title: "% d'edificis",
        axis: { format: "%" },
      },
      color: {
        field: "tipus", type: "nominal", title: null,
        scale: { domain: OCCUPANCY_DOMAIN, range: OCCUPANCY_COLORS },
        legend: { orient: "top" },
      },
      order: { field: "tipus", sort: OCCUPANCY_DOMAIN },
      tooltip: [
        { field: "grp", type: "nominal", title: groupTitle },
        { field: "tipus", type: "nominal", title: "Tipus" },
        { field: "valor", type: "quantitative", title: "Edificis", format: "," },
        { field: "total", type: "quantitative", title: "Total", format: "," },
      ],
    },
  };
  await vegaEmbed("#chart-occupancy", spec, { actions: false });
}

// 3. Boxplot distance_km per classe (top 8 amb >= 30 files i km no-NULL)
async function chartDistance() {
  const normal = DB.entries.filter(e =>
    isNormal(e) && e.class_normalized != null && e.distance_km != null);
  const counts = countBy(normal, "class_normalized");
  const topClasses = [...counts.entries()]
    .filter(([, n]) => n >= 30)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([cls]) => cls);
  const topSet = new Set(topClasses);
  const rows = normal
    .filter(e => topSet.has(e.class_normalized))
    .map(e => ({ cls: e.class_normalized, km: e.distance_km }));
  // Ordenem per mediana
  const med = {};
  for (const cls of topClasses) {
    const kms = rows.filter(r => r.cls === cls).map(r => r.km).sort((a, b) => a - b);
    med[cls] = kms[Math.floor(kms.length / 2)];
  }
  const order = topClasses.slice().sort((a, b) => med[a] - med[b]);

  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: 340,
    title: {
      text: "Distància a la capital del municipi · km",
      subtitle: "Literal del cens: «Su distancia de la capital del Ayuntamiento». La metodologia de mesura no s'explicita.",
      subtitleColor: "#7c6f5a",
      subtitleFontSize: 11,
      subtitleFontStyle: "italic",
      anchor: "start",
    },
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

// 4. Pareto de la concentració d'edificis
async function chartPareto() {
  const normal = DB.entries.filter(e => isNormal(e) && e.total != null && e.total > 0);
  const sorted = normal.slice().sort((a, b) => b.total - a.total);
  const totalAll = sumBy(sorted, "total");
  const totalPlaces = sorted.length;
  let cum = 0;
  const rows = sorted.map((e, i) => {
    cum += e.total;
    return {
      rk: i + 1,
      place: e.place,
      municipality: e.municipality,
      total: e.total,
      pct_places: 100.0 * (i + 1) / totalPlaces,
      pct_buildings: 100.0 * cum / totalAll,
    };
  });
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
        // Capa de punts transparents per al hover (precisa)
        mark: { type: "point", size: 30, opacity: 0, filled: true, color: "#5e2620" },
        encoding: {
          x: { field: "pct_places", type: "quantitative" },
          y: { field: "pct_buildings", type: "quantitative" },
          opacity: {
            condition: { param: "hover", value: 0.9, empty: false },
            value: 0,
          },
          tooltip: [
            { field: "rk", type: "quantitative", title: "Rang", format: "," },
            { field: "place", type: "nominal", title: "Topònim" },
            { field: "municipality", type: "nominal", title: "Municipi" },
            { field: "total", type: "quantitative", title: "Edificis", format: "," },
            { field: "pct_places", type: "quantitative", title: "% topònims", format: ".2f" },
            { field: "pct_buildings", type: "quantitative", title: "% acumulat edificis", format: ".2f" },
          ],
        },
        params: [{
          name: "hover",
          select: { type: "point", on: "mouseover", nearest: true,
                    fields: ["pct_places"] },
        }],
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

// 5. Top arrels toponímiques (classificació per LIKE-equivalent en JS)
async function chartToponymRoots() {
  // L'ordre matters: el primer patró que matchi guanya.
  const patterns = [
    ["Son",                      p => p.startsWith("Son ") || p.startsWith("Son-")],
    ["Ca'n / Ca's / Ca na",      p => p.startsWith("Ca'n ") || p.startsWith("Ca na ")
                                    || p.startsWith("Ca's ") || p.startsWith("Ca'l ")
                                    || p.startsWith("Ca de ")],
    ["Molí / Molins",            p => p.startsWith("Molí") || p.startsWith("Molino")
                                    || p.startsWith("Molins")],
    ["Sant / Santa / San",       p => p.startsWith("Sant ") || p.startsWith("Santa ")
                                    || p.startsWith("San ")],
    ["Venda (eivissenc)",        p => p.startsWith("Venda ") || /^Venda d/.test(p)],
    ["Hort / Horta",             p => /^Hort d/.test(p) || p.startsWith("Hort ")
                                    || p.startsWith("Horta")],
    ["Casetas (de labradors)",   p => p.startsWith("Casetas ") || /^Casetas d/.test(p)],
    ["Torre / Torret",           p => /^Torre d/.test(p) || p.startsWith("Torre ")
                                    || p.startsWith("Torret")],
    ["Rafal",                    p => p.startsWith("Rafal ") || p.startsWith("Rafal-")
                                    || p.startsWith("Rafal'")],
    ["Alqueria",                 p => p.startsWith("Alquería")],
    ["Camp",                     p => p.startsWith("Camp ") || /^Camp d/.test(p)],
    ["Plá / Pla",                p => /^Pl[áa] /.test(p) || /^Pl[áa] d/.test(p)],
    ["Coll",                     p => p.startsWith("Coll ") || /^Coll d/.test(p)],
    ["Coma",                     p => p.startsWith("Coma ") || /^Coma d/.test(p)],
    ["Puig / Púig",              p => /^P[uú]ig/.test(p)],
    ["Pujol",                    p => p.startsWith("Pujol")],
    ["Sementeri",                p => p.startsWith("Sementeri")],
    ["Costa",                    p => p.startsWith("Costa ") || /^Costa d/.test(p)],
    ["Taulera",                  p => p.startsWith("Taulera")],
  ];
  const counts = new Map();
  for (const e of DB.entries) {
    if (!isNormal(e) || !e.place) continue;
    for (const [label, test] of patterns) {
      if (test(e.place)) {
        counts.set(label, (counts.get(label) || 0) + 1);
        break;
      }
    }
  }
  const rows = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([root, n]) => ({ root, n }));
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

// 6. Composició arquitectònica per territori (P1..PM + Albergs apilats)
const FLOOR_COLS = [
  { key: "buildings_1_floor",       label: "1 planta" },
  { key: "buildings_2_floors",      label: "2 plantes" },
  { key: "buildings_3_floors",      label: "3 plantes" },
  { key: "buildings_over_3_floors", label: "Més de 3 plantes" },
  { key: "shelters",                label: "Albergs" },
];
const FLOOR_DOMAIN = FLOOR_COLS.map(f => f.label);
const FLOOR_RANGE  = ["#c98455","#a04f3c","#5e2620","#6b4561","#8b6b4f"];

async function setupFloorsChart() {
  const sel = document.getElementById("f-floors-group");
  if (!sel) return;
  sel.addEventListener("change", () => chartFloors(sel.value));
  await chartFloors(sel.value);
}

async function chartFloors(mode = "district") {
  const isDistrict = mode === "district";
  const groupCol = isDistrict ? "judicial_district" : "municipality";
  const normal = DB.entries.filter(e => isNormal(e) && (isDistrict || hasMuni(e)));
  const aggs = { tot: r => sumBy(r, "total") };
  for (const f of FLOOR_COLS) {
    aggs[f.label] = r => sumBy(r, f.key);
  }
  let grouped = groupAggregate(normal, groupCol, aggs);
  grouped.sort((a, b) => b.tot - a.tot);
  if (mode === "muni-top20") grouped = grouped.slice(0, 20);
  const rows = [];
  for (const g of grouped) {
    for (const f of FLOOR_COLS) {
      rows.push({
        grp: g[groupCol], tipus: f.label, valor: g[f.label], total: g.tot,
      });
    }
  }
  const order = grouped.map(g => g[groupCol]);
  const isMany = mode !== "district";
  const groupTitle = isDistrict ? "Partit judicial" : "Municipi";
  const spec = {
    ...VEGA_THEME,
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width: "container",
    height: isMany ? Math.max(360, order.length * 22 + 60) : 320,
    data: { values: rows },
    mark: { type: "bar", stroke: "#fdf8f1", strokeWidth: 0.5 },
    encoding: {
      [isMany ? "y" : "x"]: {
        field: "grp", type: "nominal",
        title: isMany ? null : groupTitle,
        sort: order,
        axis: isMany ? { labelLimit: 200 } : { labelAngle: 0 },
      },
      [isMany ? "x" : "y"]: {
        field: "valor", type: "quantitative",
        stack: "normalize",
        title: "% del parc construït",
        axis: { format: "%" },
      },
      color: {
        field: "tipus", type: "nominal", title: null,
        scale: { domain: FLOOR_DOMAIN, range: FLOOR_RANGE },
        legend: { orient: "top" },
      },
      order: { field: "tipus", sort: FLOOR_DOMAIN },
      tooltip: [
        { field: "grp", type: "nominal", title: groupTitle },
        { field: "tipus", type: "nominal", title: "Tipus" },
        { field: "valor", type: "quantitative", title: "Edificis", format: "," },
        { field: "total", type: "quantitative", title: "Total municipal", format: "," },
      ],
    },
  };
  await vegaEmbed("#chart-floors", spec, { actions: false });
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
          if (key === "t" || key === "u") continue;
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
    if (e.target.closest("aside.filters")) {
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

  // Popover de notes a peu — click sobre una cel·la (a)(b)... obre, click fora o ESC tanca
  document.addEventListener("click", e => {
    const ref = e.target.closest(".note-ref");
    if (ref) {
      const key = `${ref.dataset.page}|${ref.dataset.ref}`;
      const note = notesByKey.get(key);
      if (note) showNotePopover(ref, note);
      e.stopPropagation();
      return;
    }
    if (e.target.closest(".note-close")) {
      closeNotePopover();
      return;
    }
    if (!e.target.closest("#note-popover")) {
      closeNotePopover();
    }
  });
  window.addEventListener("keydown", e => {
    if (e.key === "Escape") closeNotePopover();
  });
  window.addEventListener("scroll", closeNotePopover, { passive: true });

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
  setStatus("Carregant dades…");
  try {
    await loadData();
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
      `<tr><td colspan="14" class="empty">Error carregant les dades: ${esc(err.message || String(err))}</td></tr>`;
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
