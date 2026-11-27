"""
make_ascii_svg.py
Turns a headshot into an animated, neofetch-style ASCII SVG for a GitHub profile README.

Usage:
  python make_ascii_svg.py photo.jpg assets/neofetch.svg
"""

import random
import sys
from html import escape

import cv2

# ---------- Settings you can tweak ----------
COLS = 100                # ASCII width in characters (more = more detail)
BG_CUTOFF = 215           # pixels brighter than this count as background (white backdrop)
CONTRAST = 3.0            # local contrast boost (2 = gentle, 4 = strong)
RAMP = " .,:;i1tfLCG08@"  # light to dense

INFO = [
    ("", "godwin@eggan-syndicate"),
    ("", "----------------------"),
    ("Name", "Godwin Eggan"),
    ("Role", "Full-stack & AI Engineer"),
    ("Studio", "The Eggan Syndicate (2023)"),
    ("Shipping", "since 2022"),
    ("Frontend", "TypeScript, React, Next.js, Tailwind"),
    ("Backend", "Python, FastAPI, Node, Express"),
    ("Data", "Supabase, PostgreSQL"),
    ("AI", "Gemini, LLM pipelines, evals"),
    ("Uptime", "4+ years shipping"),
    ("", ""),
    ("", "Ex Arte The Eggan Syndicate"),
]
# ---------------------------------------------

FONT = 9.2
LINE_H = 10.4
CHAR_W = FONT * 0.6
PAD = 28
TOP = 58


def photo_to_ascii(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"Could not read image: {path}")

    # Centre square crop
    h, w = img.shape
    side = min(h, w)
    top, left = (h - side) // 2, (w - side) // 2
    img = img[top:top + side, left:left + side]

    # Boost contrast region by region so the face keeps detail next to dark hair/clothes
    boosted = cv2.createCLAHE(clipLimit=CONTRAST, tileGridSize=(8, 8)).apply(img)

    rows = int(COLS * 0.5)  # characters are about twice as tall as wide
    g = cv2.resize(boosted, (COLS, rows), interpolation=cv2.INTER_AREA)
    raw = cv2.resize(img, (COLS, rows), interpolation=cv2.INTER_AREA)

    lines = []
    for y in range(rows):
        row = ""
        for x in range(COLS):
            if raw[y, x] > BG_CUTOFF:
                row += " "
                continue
            density = 1 - g[y, x] / 255
            row += RAMP[min(len(RAMP) - 1, int(density * len(RAMP)))]
        lines.append(row.rstrip())

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def scramble(line, rng):
    pool = "01<>/\\|{}[]#$%&*+=?!"
    return "".join(c if c == " " else rng.choice(pool) for c in line)


def build_svg(lines):
    rng = random.Random(7)
    ascii_w = COLS * CHAR_W
    ascii_h = len(lines) * LINE_H
    info_x = PAD + ascii_w + 30
    width = int(info_x + 440)
    body_h = max(ascii_h, len(INFO) * 22 + 40)
    height = int(TOP + body_h + 52)
    ay = TOP + 2  # top of ascii block

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    out.append(f"""<defs>
  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#7ee787"/>
    <stop offset="1" stop-color="#1f6f3b"/>
  </linearGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="{ay}" x2="{ascii_w * 0.5}" y2="{ay + ascii_h}">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.45" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#d2ffd9" stop-opacity="0.95"/>
    <stop offset="0.55" stop-color="#fff" stop-opacity="0"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    <animateTransform attributeName="gradientTransform" type="translate"
      values="{-ascii_w * 1.2} 0;{ascii_w * 1.4} 0" dur="4.5s" begin="4s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#39d353" stop-opacity="0"/>
    <stop offset="1" stop-color="#39d353" stop-opacity="0.22"/>
  </linearGradient>
  <clipPath id="asciiArea"><rect x="{PAD - 6}" y="{ay - 6}" width="{ascii_w + 12}" height="{ascii_h + 12}"/></clipPath>
  <pattern id="crt" width="4" height="3" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="#000" opacity="0.35"/>
  </pattern>
</defs>
<style>
  .a {{ font: {FONT}px 'Courier New', Consolas, monospace; white-space: pre; }}
  .r {{ font: 11px 'Courier New', Consolas, monospace; fill: #39d353; }}
  .k {{ font: bold 14px 'Courier New', Consolas, monospace; fill: #39d353; }}
  .v {{ font: 14px 'Courier New', Consolas, monospace; fill: #e6edf3; }}
  .t {{ font: 13px 'Courier New', Consolas, monospace; fill: #8b949e; }}
  .h {{ font: bold 15px 'Courier New', Consolas, monospace; fill: #39d353; }}
</style>""")

    # Terminal window
    out.append(f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>')
    out.append(f'<rect width="{width}" height="34" rx="12" fill="#161b22"/>')
    out.append(f'<rect y="22" width="{width}" height="12" fill="#161b22"/>')
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        out.append(f'<circle cx="{20 + i * 20}" cy="17" r="6" fill="{c}"/>')
    out.append(f'<text x="{width / 2}" y="22" text-anchor="middle" class="t">godwin@eggan: ~</text>')

    # Matrix rain behind the portrait (loops forever)
    out.append(f'<g clip-path="url(#asciiArea)" opacity="0.18">')
    ncols = 22
    for c in range(ncols):
        x = PAD + (c + rng.random() * 0.6) * ascii_w / ncols
        n = rng.randint(10, 20)
        chars = "".join(rng.choice("01アイウエオカキクケコ<>/*+") if False else rng.choice("0123456789ABCDEF<>/*+")
                        for _ in range(n))
        dur = rng.uniform(3.5, 7.5)
        delay = rng.uniform(0, 4)
        tsp = "".join(
            f'<tspan x="{x:.1f}" dy="12" opacity="{0.25 + 0.75 * (k + 1) / n:.2f}">{escape(ch)}</tspan>'
            for k, ch in enumerate(chars)
        )
        out.append(
            f'<text class="r" y="0">{tsp}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {ay - n * 12};0 {ay + ascii_h + 10}" dur="{dur:.2f}s" begin="{delay:.2f}s" '
            f'repeatCount="indefinite"/></text>'
        )
    out.append("</g>")

    # Prompt typed at the top
    cmd = "$ neofetch --ascii portrait --decode"
    out.append(f'<clipPath id="cc"><rect x="{PAD}" y="38" width="0" height="22">'
               f'<animate attributeName="width" from="0" to="{len(cmd) * 9 + 6}" '
               f'begin="0.2s" dur="1.1s" fill="freeze"/></rect></clipPath>')
    out.append(f'<text x="{PAD}" y="54" class="v" clip-path="url(#cc)">{escape(cmd)}</text>')

    # Portrait: each line shows two scrambled frames, then decodes to the real line
    start = 1.4
    step = 0.05
    portrait = ['<g id="portrait">']
    scrambled = []
    for i, line in enumerate(lines):
        y = ay + 10 + i * LINE_H
        tl = f'textLength="{len(line) * CHAR_W:.1f}" lengthAdjust="spacingAndGlyphs"'
        t0 = start + i * step
        for f in range(2):
            on = t0 + f * 0.12
            scrambled.append(
                f'<text x="{PAD}" y="{y:.1f}" class="a" fill="#7ee787" xml:space="preserve" opacity="0" {tl}>'
                f'{escape(scramble(line, rng))}'
                f'<set attributeName="opacity" to="1" begin="{on:.2f}s"/>'
                f'<set attributeName="opacity" to="0" begin="{on + 0.12:.2f}s"/></text>'
            )
        portrait.append(
            f'<text x="{PAD}" y="{y:.1f}" class="a" xml:space="preserve" opacity="0" {tl}>'
            f'{escape(line)}<set attributeName="opacity" to="1" begin="{t0 + 0.24:.2f}s"/></text>'
        )
    portrait.append("</g>")
    reveal_end = start + len(lines) * step + 0.3

    # Glitch copies (red / cyan split) that flicker every few seconds
    for color, dx in (("#ff3b6b", -3), ("#2fd8ff", 3)):
        out.append(
            f'<use xlink:href="#portrait" href="#portrait" fill="{color}" opacity="0" transform="translate({dx} 0)">'
            f'<animate attributeName="opacity" values="0;0;0.75;0;0.6;0;0" '
            f'keyTimes="0;0.9;0.915;0.93;0.95;0.965;1" dur="6s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;{dx} 0;{-dx} 1;{dx * 2} 0;0 0;0 0" keyTimes="0;0.9;0.915;0.93;0.95;0.965;1" '
            f'dur="6s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/></use>'
        )
    out.append(f'<g fill="url(#g)">' + "\n".join(portrait) + "</g>")
    out.extend(scrambled)
    # Shimmer sweep over the portrait
    out.append(f'<use xlink:href="#portrait" href="#portrait" fill="url(#shine)"/>')

    # CRT lines and a scanline sweeping down
    out.append(f'<rect x="{PAD - 6}" y="{ay - 6}" width="{ascii_w + 12}" height="{ascii_h + 12}" fill="url(#crt)" opacity="0.5"/>')
    out.append(
        f'<rect x="{PAD - 6}" y="{ay - 40}" width="{ascii_w + 12}" height="40" fill="url(#scan)" clip-path="url(#asciiArea)" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{reveal_end:.2f}s"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {ascii_h + 46}" '
        f'dur="3.2s" begin="{reveal_end:.2f}s" repeatCount="indefinite"/></rect>'
    )

    # Info panel, each line typed out
    t = reveal_end
    for i, (key, val) in enumerate(INFO):
        y = TOP + 26 + i * 22
        if not key and not val:
            continue
        if key:
            content = f'<tspan class="k">{escape(key)}</tspan><tspan class="v">: {escape(val)}</tspan>'
            n = len(key) + 2 + len(val)
        else:
            cls = "h" if i == 0 else ("t" if val.startswith("-") or val.startswith("Ex Arte") else "v")
            content = f'<tspan class="{cls}">{escape(val)}</tspan>'
            n = len(val)
        w = n * 9.4 + 12
        dur = max(0.25, n * 0.018)
        out.append(
            f'<clipPath id="c{i}"><rect x="{info_x}" y="{y - 16}" width="0" height="22">'
            f'<animate attributeName="width" from="0" to="{w:.0f}" begin="{t:.2f}s" '
            f'dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        out.append(f'<text x="{info_x}" y="{y}" clip-path="url(#c{i})">{content}</text>')
        t += dur * 0.6

    # Colour blocks that pulse
    by = TOP + 26 + len(INFO) * 22 + 2
    colors = ["#0e4429", "#006d32", "#26a641", "#39d353", "#7ee787", "#e6edf3"]
    for i, c in enumerate(colors):
        out.append(
            f'<rect x="{info_x + i * 30}" y="{by}" width="26" height="14" rx="3" fill="{c}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{t + i * 0.08:.2f}s" dur="0.2s" fill="freeze"/>'
            f'<animate attributeName="y" values="{by};{by - 5};{by}" dur="0.5s" '
            f'begin="{t + 1 + i * 0.1:.2f}s;{t + 1 + i * 0.1 + 5:.2f}s" /></rect>'
        )

    # Blinking cursor
    cy = height - 22
    out.append(f'<text x="{PAD}" y="{cy}" class="v" opacity="0">$ '
               f'<set attributeName="opacity" to="1" begin="{t + 0.6:.2f}s"/></text>')
    out.append(f'<rect x="{PAD + 18}" y="{cy - 12}" width="9" height="15" fill="#39d353" opacity="0">'
               f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" calcMode="discrete" '
               f'begin="{t + 0.6:.2f}s" dur="1s" repeatCount="indefinite"/></rect>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python make_ascii_svg.py photo.jpg output.svg")
    lines = photo_to_ascii(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(build_svg(lines))
    print(f"Wrote {sys.argv[2]} ({len(lines)} ASCII lines)")


if __name__ == "__main__":
    main()
