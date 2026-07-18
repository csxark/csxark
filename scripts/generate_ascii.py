#!/usr/bin/env python3
"""
generate_ascii.py

Converts a portrait photo into a monospace ASCII-art SVG, framed as a
macOS-style terminal window (title bar, traffic lights, a whoami prompt
under the art) — matching the reference "portrait.sh" aesthetic.

Usage:
    python3 generate_ascii.py <input_image> <output_svg> \
        --user ark --cols 78 --crop 500,440,1120,1300
"""

import argparse
import html
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import _chrome

RAMP = "@%#*+=-:.//:)"
CHAR_ASPECT = 0.55
ART_COLOR = "#97ebfc"       
PROMPT_GREEN = "#20cb37"
PROMPT_TEXT = "#d6e8e0"
DIM = "#4f5763"


def image_to_ascii_rows(path: str, cols: int, crop=None) -> list[str]:
    img = Image.open(path).convert("L")
    if crop:
        img = img.crop(crop)
    w, h = img.size
    cell_h = w / cols / CHAR_ASPECT
    rows = max(1, round(h / cell_h))
    img = img.resize((cols, rows))
    pixels = list(img.getdata())
    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        line = []
        for c in range(cols):
            b = pixels[r * cols + c]
            idx = min(ramp_len - 1, b * ramp_len // 256)
            line.append(RAMP[idx])
        lines.append("".join(line))
    return lines


def render(rows: list[str], username: str, display_name: str, font_size: int = 8) -> str:
    char_w = font_size * CHAR_ASPECT
    cols = max(len(r) for r in rows)
    pad = 16
    art_w = round(cols * char_w)
    art_h = round(len(rows) * font_size)
    width = art_w + pad * 2

    lines = []
    for i, row in enumerate(rows):
        y = pad + font_size + i * font_size
        lines.append(
            f'<text x="{pad}" y="{y}" font-size="{font_size}" fill="{ART_COLOR}" '
            f'xml:space="preserve">{html.escape(row)}</text>'
        )
    art_bottom = pad + art_h

    prompt_y1 = art_bottom + 22
    prompt_y2 = prompt_y1 + 18
    body_height = prompt_y2 + 12

    lines.append(f'<line x1="{pad}" y1="{art_bottom + 8}" x2="{width - pad}" y2="{art_bottom + 8}" '
                  f'stroke="#1f2733" stroke-width="1"/>')
    lines.append(
        f'<text x="{pad}" y="{prompt_y1}" font-size="12" xml:space="preserve">'
        f'<tspan fill="{PROMPT_GREEN}">{html.escape(username)}@github</tspan>'
        f'<tspan fill="{DIM}">:~$ whoami</tspan></text>'
    )
    lines.append(
        f'<text x="{pad}" y="{prompt_y2}" font-size="12" fill="{PROMPT_TEXT}">{html.escape(display_name)}</text>'
    )

    body = "".join(lines)
    title = f"{username}@github: ~$ ./portrait.sh"
    return _chrome.window(width, body_height, title, body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--cols", type=int, default=78)
    ap.add_argument("--user", default="ark")
    ap.add_argument("--name", default="Ark")
    ap.add_argument("--crop", default=None, help="x1,y1,x2,y2 pixel box to crop before converting")
    args = ap.parse_args()

    crop = tuple(int(v) for v in args.crop.split(",")) if args.crop else None
    rows = image_to_ascii_rows(args.input, args.cols, crop)
    svg = render(rows, args.user, args.name)
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"Wrote {args.output} ({len(rows)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()
