"""Extract 1860 Nomenclator tables with Claude Opus 4.7.

- Model: claude-opus-4-7 (vision).
- Prompt caching: the instructions are cached on the first call and
  reused for the remaining 47 (~10% input cost on reads).
- Resume: skips pages with an existing HTML file.
- Cost tracking: logs per-page and total input/output/cache tokens.

Usage:
    .venv/bin/python scripts/extract_with_claude.py 3            # 1 page
    .venv/bin/python scripts/extract_with_claude.py 4 5 6        # multiple
    .venv/bin/python scripts/extract_with_claude.py --range 4-51 # range
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import pymupdf
from anthropic import Anthropic
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MODEL = "claude-opus-4-7"
# Opus 4.7 pricing ($/1M tokens). See docs.anthropic.com/en/docs/about-claude/models/overview.
PRICE_INPUT = 5.00
PRICE_OUTPUT = 25.00
PRICE_CACHE_WRITE = 5.00 * 1.25  # 5 min TTL
PRICE_CACHE_READ = 5.00 * 0.10

PDF = PROJECT_ROOT / "pdfs" / "Nomenclàtor 1860 balears.pdf"
OUT_DIR = PROJECT_ROOT / "output" / "claude_api"
DPI = 300        # 200 -> 300 gives the visual acuity needed for 1860 typography
JPEG_QUALITY = 95  # high quality; keeps image <5 MB
MAX_TOKENS = 8000

SYSTEM_PROMPT = """You are extracting tabular data from a 19th-century Spanish census of the Balearic Islands (Nomenclátor de la Provincia de las Baleares, 1860).

Each table page has 13 columns in this order:
  1. AYUNTAMIENTO (municipality — visually merged on the left, spans many rows)
  2. POBLACIÓN (place/settlement name)
  3. SU CLASE (type: "Casa de labor", "Casa de huerto", "Torre de vigía", "Molino de viento", "Caserío", "Parróquia y casa", "Albergues", "Villa", "Ciudad", "Prédio (casa de labranza)", etc.)
  4. km (distance from capital, decimal with apostrophe like "9'3" meaning 9.3)
  5. HabConst — buildings inhabited constantly
  6. HabTemp — buildings inhabited temporarily
  7. Inhab — uninhabited buildings
  8. P1 — buildings of one floor
  9. P2 — buildings of two floors
  10. P3 — buildings of three floors
  11. PMas — buildings of more than three floors
  12. Albergues — shelters/caves/huts
  13. Total

⚠ CRITICAL — DO NOT MERGE ADJACENT NUMERIC CELLS:
Each of the 9 numeric columns (5-13) contains EXACTLY ONE number (or »  meaning zero) per row.
The columns are narrow and adjacent. If two columns show small values like "1" and "140" with the column
separator between them, output them as <td>1</td><td>140</td>, NEVER as <td>141</td>. Use the column header
positions at the top of the page as your alignment guide — each header word sits centered above ITS column.

For the headquarters row (class "Villa" or "Ciudad", often bold), values can be LARGER than surrounding rows
but the row STILL has exactly 9 numeric cells. Common shape for a Mallorca pueblo's headquarters: HabConst
in the hundreds, P1 small (often 0-5), P2 in the hundreds, P3 in tens-hundreds, Albergues 0.

OUTPUT REQUIREMENTS:
- Output ONLY a single <table>...</table> element with one <tr> per data row.
- Every <tr> has EXACTLY 13 <td> cells in the order above.
- Repeat the AYUNTAMIENTO label in EVERY row, even when visually merged (e.g., FORMENTERA, IBIZA, ALARÓ).
- Include EVERY row — bold/highlighted rows, subtotal/TOTAL rows, and rows with footnote markers (a), (b), (c).
- For TOTAL/subtotal rows, leave the AYUNTAMIENTO cell empty AND the POBLACIÓN cell as "TOTAL <ayuntamiento_name>".
- In the POBLACIÓN cell write only the place name, no leading dots, no trailing footnote markers.
- If a cell shows » (right-angle quotation mark) in the original, output » literally in that <td>.
- Preserve text content exactly: "Ca'n", "Molí", "d'es", "d'en", accented characters, etc.
- Footnote references like (a), (b), (c) attached to a row: capture as a separate attribute in the <tr> opening tag like <tr nota="a">. The footnote text itself (at the bottom of the page) should appear AFTER the </table> as <p class="nota" ref="a">...</p>.
- If the page has the global "AYUNTAMIENTOS…N (Habitantes X.XXX)" partido-summary row, output it as a row with poblacion="TOTAL PARTIDO".

MENTAL CHECK before finalising: for each TOTAL row,  P1+P2+P3+PMas+Albergues should equal HabConst+HabTemp+Inhab
(it's the same buildings counted by structure vs by use). If they don't match, recount the columns of the
heaviest row — likely a column-merge error.

CRITICAL: Do not omit columns. Do not insert columns. Do not add commentary before or after. Output starts with <table> and ends with </p> if there are footnotes, otherwise </table>."""


def render_page(doc: pymupdf.Document, page_index: int) -> bytes:
    """Render the page as JPEG (keeps OCR detail and stays under the 5 MB
    API limit)."""
    from io import BytesIO
    from PIL import Image
    page = doc[page_index]
    pix = page.get_pixmap(dpi=DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def extract_page(client: Anthropic, page_num: int, doc: pymupdf.Document) -> dict:
    """Extract one page. Returns dict with html, usage and elapsed time."""
    out_html = OUT_DIR / f"page{page_num:04d}.html"
    out_meta = OUT_DIR / f"page{page_num:04d}.json"

    print(f"  - rendering page {page_num}...", end="", flush=True)
    img_bytes = render_page(doc, page_num - 1)
    img_b64 = base64.standard_b64encode(img_bytes).decode("ascii")
    print(f" {len(img_bytes) // 1024} KB")

    print(f"  - calling {MODEL}...", end="", flush=True)
    t0 = time.time()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Extract the data table from this page (page {page_num}). Output ONLY the <table>...</table> followed by any <p class=\"nota\"> elements for footnotes.",
                    },
                ],
            }
        ],
    )
    elapsed = time.time() - t0

    text = "".join(b.text for b in resp.content if b.type == "text")
    out_html.write_text(text, encoding="utf-8")

    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
    }
    cost = (
        usage["input_tokens"] / 1_000_000 * PRICE_INPUT
        + usage["output_tokens"] / 1_000_000 * PRICE_OUTPUT
        + usage["cache_creation_input_tokens"] / 1_000_000 * PRICE_CACHE_WRITE
        + usage["cache_read_input_tokens"] / 1_000_000 * PRICE_CACHE_READ
    )
    meta = {
        "page": page_num,
        "model": MODEL,
        "dpi": DPI,
        "elapsed_seconds": round(elapsed, 2),
        "usage": usage,
        "cost_usd": round(cost, 6),
        "char_count": len(text),
        "stop_reason": resp.stop_reason,
    }
    out_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f" {elapsed:.1f}s | "
        f"in={usage['input_tokens']} cached_r={usage['cache_read_input_tokens']} "
        f"out={usage['output_tokens']} | ${cost:.4f}"
    )
    return meta


def parse_args() -> list[int]:
    p = argparse.ArgumentParser(description="Claude Opus 4.7 -> Nomenclator tables")
    p.add_argument("pages", nargs="*", type=int, help="individual pages (1-indexed)")
    p.add_argument("--range", dest="range_", help="closed range, e.g. 4-51")
    p.add_argument("--force", action="store_true", help="reprocess even if HTML exists")
    args = p.parse_args()
    pages = list(args.pages)
    if args.range_:
        lo, hi = args.range_.split("-")
        pages.extend(range(int(lo), int(hi) + 1))
    if not pages:
        p.error("specify at least one page or --range")
    return sorted(set(pages)), args.force


def main() -> None:
    pages, force = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not found in environment or .env")
        sys.exit(1)

    client = Anthropic()
    doc = pymupdf.open(PDF)

    print(f"Model: {MODEL}")
    print(f"PDF: {PDF.name} ({len(doc)} pages)")
    print(f"Output: {OUT_DIR}")
    print(f"Pages to process: {pages}\n")

    total_cost = 0.0
    total_in = 0
    total_out = 0
    total_cache_r = 0
    total_cache_w = 0
    processed = 0
    skipped = 0
    errors: list[tuple[int, str]] = []

    for page_num in pages:
        out_html = OUT_DIR / f"page{page_num:04d}.html"
        if out_html.exists() and not force:
            print(f"p.{page_num}: already processed (skip)")
            skipped += 1
            continue

        print(f"p.{page_num}:")
        try:
            meta = extract_page(client, page_num, doc)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            errors.append((page_num, str(exc)))
            continue

        total_cost += meta["cost_usd"]
        total_in += meta["usage"]["input_tokens"]
        total_out += meta["usage"]["output_tokens"]
        total_cache_r += meta["usage"]["cache_read_input_tokens"]
        total_cache_w += meta["usage"]["cache_creation_input_tokens"]
        processed += 1

    print("\n" + "=" * 60)
    print(f"Processed: {processed}")
    print(f"Skipped:   {skipped}")
    print(f"Errors:    {len(errors)}")
    print()
    print(f"Input tokens (uncached):  {total_in:>10,}")
    print(f"Cache READ tokens:        {total_cache_r:>10,}")
    print(f"Cache WRITE tokens:       {total_cache_w:>10,}")
    print(f"Output tokens:            {total_out:>10,}")
    print(f"\nTotal cost: ${total_cost:.4f}")
    if errors:
        print("\nPages with errors:")
        for p, e in errors:
            print(f"  p.{p}: {e}")


if __name__ == "__main__":
    main()
