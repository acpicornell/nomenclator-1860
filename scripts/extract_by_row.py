"""Prototype: row-by-row extraction of a Nomenclator page.

Pipeline:
1. Render the page at 400 DPI from the PDF.
2. Detect the skew angle and rotate the image.
3. Locate horizontal whitespace gaps between rows via horizontal
   projection (the typography has no rules, only whitespace).
4. Crop strips for each row (between two consecutive gaps).
5. For each strip ask Claude to extract the 9 numeric values.
6. Return a rebuilt <table> HTML plus cost metrics.

Usage:
    .venv/bin/python scripts/extract_by_row.py 7 --table-x 530
        # page 7, the numeric block starts at x=530
"""
from __future__ import annotations
import argparse
import base64
import json
import re
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image
from anthropic import Anthropic
from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT / ".env")
PDF = PROJECT / "pdfs" / "Nomenclàtor 1860 balears.pdf"
OUT_DIR = PROJECT / "output" / "by_row"
DPI = 400

ROW_PROMPT = """This image shows ONE row of the 1860 Nomenclátor de Baleares census table.
The row has 13 cells in this order:
  1. Ayuntamiento (may be empty if merged from row above)
  2. Población (place name)
  3. Su Clase (e.g., "Caserío", "Casa de labor", "Villa", "Prédio (casa de labranza)")
  4. km (distance, decimal with apostrophe like "9'3"; can be empty)
  5. HabConst (constantly inhabited buildings)
  6. HabTemp (temporarily inhabited)
  7. Inhab (uninhabited)
  8. P1 (buildings of one floor)
  9. P2 (two floors)
  10. P3 (three floors)
  11. PMas (more than three floors)
  12. Albergues (shelters/caves/huts)
  13. Total

CRITICAL: Numeric columns 5-13 each contain exactly ONE number or »  (where » means zero).
Count carefully — each cell is separated by a vertical line in the image.

If the Ayuntamiento cell is empty (visually merged), output empty string for cell 1.

Output ONLY a single JSON line like:
{"ayuntamiento":"","poblacion":"...","clase":"...","km":"...","hc":N,"ht":N,"inh":N,"p1":N,"p2":N,"p3":N,"pm":N,"alb":N,"tot":N}

For numeric cells: N is an integer (» → 0), or null if blank/unreadable.
For "km": preserve as string "9'3" or empty string if absent.

After detecting and merging adjacent rows for "TOTAL <ayuntamiento>", treat it as one row with empty ayuntamiento and poblacion="TOTAL <name>"."""


def detect_skew(img: Image.Image) -> float:
    gray = np.array(img.convert("L"))
    bw = (gray < 128).astype(np.uint8)
    def score(arr, angle):
        r = Image.fromarray(arr * 255).rotate(angle, fillcolor=0, resample=Image.BILINEAR)
        return np.array(r).sum(axis=1).var()
    return max(np.arange(-2.0, 2.01, 0.1), key=lambda a: score(bw, a))


def detect_row_boundaries(img: Image.Image, debug: bool = False) -> list[int]:
    """Find Y positions of whitespace gaps between rows via valleys in the
    horizontal projection. The Nomenclator typography has no rules — only
    white gaps."""
    from scipy.signal import find_peaks
    gray = np.array(img.convert("L"))
    bw = (gray < 100).astype(np.uint8)
    # Table body (skip approximate header/footer).
    y_start, y_end = 400, bw.shape[0] - 200
    body = bw[y_start:y_end]
    h_proj = body.sum(axis=1)
    smooth = np.convolve(h_proj, np.ones(5)/5, mode='same')
    # Valleys = peaks of -smooth, at least 40 px apart (minimum row height).
    valleys, _ = find_peaks(-smooth, distance=40, prominence=50)
    boundaries = [int(v + y_start) for v in valleys]
    if debug:
        print(f"Boundaries detected: {len(boundaries)}")
        print(f"First 10: {boundaries[:10]}")
    return boundaries


def crop_row_strips(img: Image.Image, boundaries: list[int], pad: int = 2) -> list[tuple[int, Image.Image]]:
    """Crop strips between consecutive boundaries. Returns [(y_top, strip)]."""
    strips = []
    for i in range(len(boundaries) - 1):
        y0 = boundaries[i] + pad
        y1 = boundaries[i+1] - pad
        if y1 - y0 < 20:
            continue
        strip = img.crop((0, y0, img.width, y1))
        strips.append((y0, strip))
    return strips


def extract_row(client: Anthropic, strip: Image.Image, page_num: int, row_idx: int) -> dict:
    """Send a strip to Claude and return parsed JSON."""
    buf = BytesIO()
    strip.save(buf, format="JPEG", quality=92, optimize=True)
    img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

    # Sonnet 4.6 is ~10x cheaper than Opus with identical quality on 1-row
    # strips. Haiku 4.5 fails on column alignment — do not use it here.
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=[{"type": "text", "text": ROW_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                {"type": "text", "text": f"Extract page {page_num} row {row_idx}."},
            ]
        }]
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.M).strip()
    # Sonnet 4.6 pricing: $3/MTok input, $15/MTok output.
    cost = (resp.usage.input_tokens * 3 + resp.usage.output_tokens * 15) / 1_000_000
    cache_read = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
    if cache_read:
        cost = (resp.usage.input_tokens * 3
                + cache_read * 0.3
                + resp.usage.output_tokens * 15) / 1_000_000
    try:
        return json.loads(text), cost
    except json.JSONDecodeError:
        return {"_raw": text, "_error": "parse"}, cost


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("page", type=int)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--save-strips", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(PDF)
    pix = doc.load_page(args.page - 1).get_pixmap(dpi=DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    print(f"Page {args.page} rendered: {img.size}")

    angle = detect_skew(img)
    print(f"Skew detected: {angle:+.2f}°")
    if abs(angle) >= 0.05:
        img = img.rotate(angle, fillcolor=(255,255,255), resample=Image.BICUBIC)
        print("Image deskewed")

    boundaries = detect_row_boundaries(img, debug=args.debug)
    print(f"Rows detected (boundaries): {len(boundaries)} -> {len(boundaries)-1} potential strips")

    strips = crop_row_strips(img, boundaries)
    print(f"Usable strips after filtering: {len(strips)}")

    if args.save_strips:
        strips_dir = OUT_DIR / f"page{args.page:04d}_strips"
        strips_dir.mkdir(exist_ok=True)
        for i, (y, strip) in enumerate(strips):
            strip.save(strips_dir / f"row{i:03d}_y{y}.png")
        print(f"Strips saved at {strips_dir}")

    out_file = OUT_DIR / f"page{args.page:04d}_rows.json"
    client = Anthropic()
    rows = []
    total_cost = 0.0
    t0 = time.time()
    for i, (y, strip) in enumerate(strips):
        print(f"  - row {i+1}/{len(strips)} (y={y})...", end="", flush=True)
        try:
            data, cost = extract_row(client, strip, args.page, i)
        except Exception as exc:
            print(f" ERROR: {type(exc).__name__}: {exc}")
            rows.append({"y": y, "data": {"_error": str(exc)}})
            out_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
            continue
        total_cost += cost
        rows.append({"y": y, "data": data})
        if "_error" in data:
            print(f" parse error: {data['_raw'][:80]}")
        else:
            print(f" {data.get('poblacion', '?')[:30]:30}  floors={data.get('p1')}/{data.get('p2')}/{data.get('p3')}  ${cost:.4f}")
        # Save incrementally per row so partial progress is not lost.
        out_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2))

    elapsed = time.time() - t0
    print(f"\nTotal: {len(strips)} rows, ${total_cost:.4f}, {elapsed:.1f}s")
    print(f"Saved at {out_file}")


if __name__ == "__main__":
    main()
