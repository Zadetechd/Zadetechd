"""
make_ascii_svg.py
Turns a headshot into an animated, neofetch-style ASCII terminal SVG for a GitHub profile README.

Usage:
  python make_ascii_svg.py photo.jpg assets/neofetch.svg
"""

import random
import sys
from html import escape

import cv2
import numpy as np

# ---------- Settings you can tweak ----------
COLS = 84                 # ASCII width in characters (more = more detail)
BG_CUTOFF = 215           # pixels brighter than this count as background (white backdrop)
CONTRAST = 2.5            # local contrast boost (2 = gentle, 4 = strong)
ZOOM = 1.0                # 1.0 = whole photo, 1.2 = zoom in a little on the centre
RAMP = " .,:;i1tfLCG08@"  # light to dense

INFO = [
    ("Name", "Godwin Eggan"),
    ("Role", "Full-stack & AI Engineer"),
    ("Studio", "The Eggan Syndicate (2023)"),
    ("Shipping", "since 2022"),
    ("Frontend", "TypeScript, React, Next.js, Tailwind"),
    ("Backend", "Python, FastAPI, Node, Express"),
    ("Data", "Supabase, PostgreSQL"),
    ("AI", "Claude, Gemini, agents, evals"),
    ("Uptime", "4+ years shipping"),
]
HANDLE = "godwin@eggan-syndicate"
SIGNATURE = "Ex Arte The Eggan Syndicate"
# ---------------------------------------------

FONT = 9.2
CHAR_W = FONT * 0.6
LINE_H = 10.4
PAD = 28
TOP = 58


def photo_to_ascii(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"Could not read image: {path}")

    # Square crop from the centre, optionally zoomed
    h, w = img.shape
    side = int(min(h, w) / ZOOM)
    top, left = (h - side) // 2, (w - side) // 2
    img = img[top:top + side, left:left + side]

    rows = int(COLS * CHAR_W / LINE_H)
    boosted = cv2.createCLAHE(clipLimit=CONTRAST, tileGridSize=(8, 8)).apply(img)
    g = cv2.resize(boosted, (COLS, rows), interpolation=cv2.INTER_AREA)
    raw = cv2.resize(img, (COLS, rows), interpolation=cv2.INTER_AREA)

    # Circular frame, like a profile picture
    yy, xx = np.mgrid[0:rows, 0:COLS]
    cx, cy = (COLS - 1) / 2, (rows - 1) / 2
    inside = ((xx - cx) / (COLS / 2 * 0.97)) ** 2 + ((yy - cy) / (rows / 2 * 0.97)) ** 2 <= 1
    person = (raw <= BG_CUTOFF) & inside

    lines = []
    for y in range(rows):
        row, shade = "", []
        for x in range(COLS):
            if not person[y, x]:
                row += " "
                shade.append(0.0)
                continue
            # Outline of the person glows brightest
            edge = any(
                0 <= y + dy < rows and 0 <= x + dx < COLS and not person[y + dy, x + dx]
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ) and inside[min(y + 1, rows - 1), x] and inside[max(y - 1, 0), x]
            d = 1 - g[y, x] / 255
            row += RAMP[max(1, min(len(RAMP) - 1, int(d * len(RAMP))))]
            shade.append(1.0 if edge else 0.35 + 0.65 * d)
        lines.append((row.rstrip(), shade))

    while lines and not lines[0][0].strip():
        lines.pop(0)
    while lines and not lines[-1][0].strip():
        lines.pop()
    return lines


def shaded(line, shade):
    """Light each glyph by its own tone (6 levels), merged into runs to keep the file small."""
    parts, cur, buf = [], None, ""
    for ch, d in zip(line, shade):
        lvl = -1 if ch == " " else min(5, int(d * 6))
        if lvl != cur and buf:
            parts.append((cur, buf))
            buf = ""
        cur = lvl
        buf += ch
    if buf:
        parts.append((cur, buf))
    op = [0.3, 0.42, 0.56, 0.7, 0.85, 1.0]
    return "".join(
        escape(t) if lvl < 0 else f'<tspan fill-opacity="{op[lvl]}">{escape(t)}</tspan>'
        for lvl, t in parts
    )


def scramble(line, rng):
    pool = "01<>/\\|{}[]#$%&*+=?!"
    return "".join(c if c == " " else rng.choice(pool) for c in line)


def build_svg(rows):
    rng = random.Random(7)
    lines = [r[0] for r in rows]
    ascii_w = COLS * CHAR_W
    ascii_h = len(lines) * LINE_H
    ay = TOP + 2
    info_x = PAD + ascii_w + 34
    width = int(info_x + 440)
    height = int(max(ay + ascii_h + 44, TOP + 26 + (len(INFO) + 5) * 22 + 60))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    out.append(f"""<defs>
  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#9dffb0"/>
    <stop offset="0.6" stop-color="#39d353"/>
    <stop offset="1" stop-color="#1f6f3b"/>
  </linearGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="{ay}" x2="{ascii_w * 0.5}" y2="{ay + ascii_h}">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.45" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#e3ffe8" stop-opacity="0.95"/>
    <stop offset="0.55" stop-color="#fff" stop-opacity="0"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    <animateTransform attributeName="gradientTransform" type="translate"
      values="{-ascii_w * 1.2:.0f} 0;{ascii_w * 1.4:.0f} 0" dur="4.5s" begin="4s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#39d353" stop-opacity="0"/>
    <stop offset="1" stop-color="#39d353" stop-opacity="0.25"/>
  </linearGradient>
  <clipPath id="asciiArea"><rect x="{PAD - 6}" y="{ay - 6}" width="{ascii_w + 12}" height="{ascii_h + 12}"/></clipPath>
  <pattern id="crt" width="4" height="3" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="#000" opacity="0.3"/>
  </pattern>
  <filter id="glow" x="-5%" y="-5%" width="110%" height="110%">
    <feGaussianBlur stdDeviation="1.4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<style>
  .a {{ font: {FONT}px 'Courier New', Consolas, monospace; white-space: pre; }}
  .r {{ font: 11px 'Courier New', Consolas, monospace; fill: #39d353; }}
  .k {{ font: bold 14px 'Courier New', Consolas, monospace; fill: #39d353; }}
  .v {{ font: 14px 'Courier New', Consolas, monospace; fill: #e6edf3; }}
  .t {{ font: 13px 'Courier New', Consolas, monospace; fill: #8b949e; }}
  .h {{ font: bold 15px 'Courier New', Consolas, monospace; fill: #39d353; }}
  .s {{ font: 11px 'Courier New', Consolas, monospace; fill: #3fb950; }}
</style>""")

    # Window chrome
    out.append(f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>')
    out.append(f'<rect width="{width}" height="34" rx="12" fill="#161b22"/>')
    out.append(f'<rect y="22" width="{width}" height="12" fill="#161b22"/>')
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        out.append(f'<circle cx="{20 + i * 20}" cy="17" r="6" fill="{c}"/>')
    out.append(f'<text x="{width / 2}" y="22" text-anchor="middle" class="t">godwin@eggan: ~</text>')

    # Matrix rain behind the portrait
    out.append('<g clip-path="url(#asciiArea)" opacity="0.22">')
    for c in range(22):
        x = PAD + (c + rng.random() * 0.6) * ascii_w / 22
        n = rng.randint(10, 20)
        chars = "".join(rng.choice("0123456789ABCDEF<>/*+") for _ in range(n))
        dur, delay = rng.uniform(3.5, 7.5), rng.uniform(0, 4)
        tsp = "".join(
            f'<tspan x="{x:.1f}" dy="12" opacity="{0.25 + 0.75 * (k + 1) / n:.2f}">{escape(ch)}</tspan>'
            for k, ch in enumerate(chars)
        )
        out.append(
            f'<text class="r" y="0">{tsp}<animateTransform attributeName="transform" type="translate" '
            f'values="0 {ay - n * 12};0 {ay + ascii_h + 10}" dur="{dur:.2f}s" begin="{delay:.2f}s" '
            f'repeatCount="indefinite"/></text>'
        )
    out.append("</g>")

    # Command typed at the top
    cmd = "$ neofetch --ascii portrait --decode"
    out.append(f'<clipPath id="cc"><rect x="{PAD}" y="38" width="0" height="22">'
               f'<animate attributeName="width" from="0" to="{len(cmd) * 9 + 6}" '
               f'begin="0.2s" dur="1.1s" fill="freeze"/></rect></clipPath>')
    out.append(f'<text x="{PAD}" y="54" class="v" clip-path="url(#cc)">{escape(cmd)}</text>')

    # Portrait: scrambled frames, then each line decodes
    start, step = 1.4, 0.05
    portrait, scrambled = ['<g id="portrait">'], []
    for i, line in enumerate(lines):
        y = ay + 10 + i * LINE_H
        tl = f'textLength="{len(line) * CHAR_W:.1f}" lengthAdjust="spacingAndGlyphs"'
        t0 = start + i * step
        for f in range(2):
            on = t0 + f * 0.12
            scrambled.append(
                f'<text x="{PAD}" y="{y:.1f}" class="a" fill="#7ee787" xml:space="preserve" opacity="0" {tl}>'
                f'{escape(scramble(line, rng))}<set attributeName="opacity" to="1" begin="{on:.2f}s"/>'
                f'<set attributeName="opacity" to="0" begin="{on + 0.12:.2f}s"/></text>'
            )
        portrait.append(
            f'<text x="{PAD}" y="{y:.1f}" class="a" xml:space="preserve" opacity="0" {tl}>'
            f'{shaded(line, rows[i][1])}<set attributeName="opacity" to="1" begin="{t0 + 0.24:.2f}s"/></text>'
        )
    portrait.append("</g>")
    reveal_end = start + len(lines) * step + 0.3

    # RGB split glitch
    for color, dx in (("#ff3b6b", -3), ("#2fd8ff", 3)):
        out.append(
            f'<use xlink:href="#portrait" href="#portrait" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;0.75;0;0.6;0;0" '
            f'keyTimes="0;0.9;0.915;0.93;0.95;0.965;1" dur="6s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;{dx} 0;{-dx} 1;{dx * 2} 0;0 0;0 0" keyTimes="0;0.9;0.915;0.93;0.95;0.965;1" '
            f'dur="6s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/></use>'
        )

    # The portrait itself, with a soft glow
    out.append('<g fill="url(#g)" filter="url(#glow)">' + "\n".join(portrait) + "</g>")
    out.extend(scrambled)

    # Slice glitch: thin bands of the portrait jump sideways for a split second
    for b in range(3):
        band_y = ay + rng.uniform(0.15, 0.85) * ascii_h
        band_h = rng.uniform(8, 22)
        shift = rng.choice([-10, -7, 7, 10])
        when = reveal_end + 1.5 + b * 2.1
        out.append(
            f'<clipPath id="band{b}"><rect x="{PAD - 20}" y="{band_y:.0f}" width="{ascii_w + 40:.0f}" height="{band_h:.0f}"/></clipPath>'
            f'<g clip-path="url(#band{b})"><rect x="{PAD - 20}" y="{band_y:.0f}" width="{ascii_w + 40:.0f}" '
            f'height="{band_h:.0f}" fill="#0d1117" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.95;0.951;0.975;0.976;1" '
            f'dur="7s" begin="{when:.2f}s" repeatCount="indefinite"/></rect>'
            f'<use xlink:href="#portrait" href="#portrait" fill="#b6ffbf" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.95;0.951;0.975;0.976;1" '
            f'dur="7s" begin="{when:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;{shift} 0;{-shift / 2} 0;0 0;0 0" '
            f'keyTimes="0;0.95;0.951;0.963;0.976;1" dur="7s" begin="{when:.2f}s" repeatCount="indefinite"/></use></g>'
        )

    # Shimmer sweep, CRT lines and a scanline
    out.append('<use xlink:href="#portrait" href="#portrait" fill="url(#shine)"/>')
    out.append(f'<rect x="{PAD - 6}" y="{ay - 6}" width="{ascii_w + 12}" height="{ascii_h + 12}" fill="url(#crt)" opacity="0.4"/>')
    out.append(
        f'<g clip-path="url(#asciiArea)"><rect x="{PAD - 6}" y="{ay - 40}" width="{ascii_w + 12}" height="40" '
        f'fill="url(#scan)" opacity="0"><set attributeName="opacity" to="1" begin="{reveal_end:.2f}s"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {ascii_h + 46:.0f}" '
        f'dur="3.2s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/></rect></g>'
    )

    # Info panel, typed line by line
    items = [(f'<tspan class="h">{escape(HANDLE)}</tspan>', len(HANDLE)),
             (f'<tspan class="t">{"-" * len(HANDLE)}</tspan>', len(HANDLE))]
    items += [(f'<tspan class="k">{escape(k)}</tspan><tspan class="v">: {escape(v)}</tspan>', len(k) + 2 + len(v))
              for k, v in INFO]
    t = reveal_end
    y = TOP + 26
    for i, (content, n) in enumerate(items):
        w, dur = n * 9.4 + 12, max(0.25, n * 0.018)
        out.append(
            f'<clipPath id="c{i}"><rect x="{info_x:.0f}" y="{y - 16}" width="0" height="22">'
            f'<animate attributeName="width" from="0" to="{w:.0f}" begin="{t:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'</rect></clipPath><text x="{info_x:.0f}" y="{y}" clip-path="url(#c{i})">{content}</text>'
        )
        t += dur * 0.6
        y += 22

    # Live-looking system stats with animated bars
    y += 12
    stats = [("CPU", 0.62, 0.88), ("COFFEE", 0.9, 0.45), ("SHIP", 0.75, 0.97)]
    for i, (label, a, b) in enumerate(stats):
        bx = info_x + 80
        out.append(f'<text x="{info_x:.0f}" y="{y}" class="s" opacity="0">{label}'
                   f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/></text>')
        out.append(f'<rect x="{bx:.0f}" y="{y - 9}" width="200" height="9" rx="2" fill="#161b22" stroke="#30363d"/>')
        out.append(
            f'<rect x="{bx:.0f}" y="{y - 9}" width="0" height="9" rx="2" fill="#39d353">'
            f'<animate attributeName="width" values="{a * 200:.0f};{b * 200:.0f};{a * 200:.0f}" '
            f'dur="{3 + i}s" begin="{t:.2f}s" repeatCount="indefinite"/></rect>'
        )
        y += 18
    t += 0.4

    # Signature and colour blocks
    y += 14
    out.append(f'<text x="{info_x:.0f}" y="{y}" class="t" opacity="0">{escape(SIGNATURE)}'
               f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/></text>')
    by = y + 16
    for i, c in enumerate(["#0e4429", "#006d32", "#26a641", "#39d353", "#7ee787", "#e6edf3"]):
        out.append(
            f'<rect x="{info_x + i * 30:.0f}" y="{by}" width="26" height="14" rx="3" fill="{c}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{t + i * 0.08:.2f}s" dur="0.2s" fill="freeze"/>'
            f'<animate attributeName="y" values="{by};{by - 5};{by}" dur="0.5s" '
            f'begin="{t + 1 + i * 0.1:.2f}s;{t + 6 + i * 0.1:.2f}s"/></rect>'
        )

    # Blinking cursor
    cy = height - 16
    out.append(f'<text x="{PAD}" y="{cy}" class="v" opacity="0">$ <set attributeName="opacity" to="1" begin="{t + 0.6:.2f}s"/></text>')
    out.append(f'<rect x="{PAD + 18}" y="{cy - 12}" width="9" height="15" fill="#39d353" opacity="0">'
               f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" calcMode="discrete" '
               f'begin="{t + 0.6:.2f}s" dur="1s" repeatCount="indefinite"/></rect>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python make_ascii_svg.py photo.jpg output.svg")
    rows = photo_to_ascii(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(build_svg(rows))
    print(f"Wrote {sys.argv[2]} ({len(rows)} ASCII lines)")


if __name__ == "__main__":
    main()
