#!/usr/bin/env python3
"""Plate III, 'happens before': a weaving draft whose drawdown carries a serialized band.
Writes art/build/plate-{dark,light}.html; render with art/render.js."""
import pathlib
FONTS = pathlib.Path("/root/.claude/skills/synced/5c806f8d-0769-4e35-ac24-a3ea18081c67_433d709e-8728-4258-b10c-98909f71fe68/canvas-design/canvas-fonts")
OUT = pathlib.Path(__file__).parent / "build"

W, H = 2400, 1500
CW, CH = 34, 20            # one cell of the draft
ENDS, PICKS, SHAFTS, TREADLES = 28, 44, 4, 6
X0, Y0 = 220, 258          # top-left of the threading strip
GAP = 24
DX, DY = X0, Y0 + SHAFTS * CH + GAP                 # drawdown origin
TX = DX + ENDS * CW + GAP                           # treadling origin x
BAND = range(18, 26)                                # the serialized picks

PAL = {
    "dark":  dict(ground="#0f1218", line="#e9e3d6", mark="#5b74d6", hold="#e2a43a", faint=0.10, hollow=0.30, text=0.78),
    "light": dict(ground="#f3eee4", line="#1c2030", mark="#2f47a8", hold="#c27e12", faint=0.12, hollow=0.34, text=0.80),
}

# pointed draw threading: 1 2 3 4 3 2 1 2 3 4 ...
cycle = [0, 1, 2, 3, 2, 1]
threading = [cycle[i % len(cycle)] for i in range(ENDS)]
# 2/2 twill tie-up on treadles 1-4, tabby on 5-6
tieup = {0: {0, 1}, 1: {1, 2}, 2: {2, 3}, 3: {3, 0}, 4: {0, 2}, 5: {1, 3}}
tcycle = [0, 1, 2, 3, 2, 1]
treadling = []
for p in range(PICKS):
    treadling.append(4 + (p % 2) if p in BAND else tcycle[p % len(tcycle)])


def plate(mode):
    c = PAL[mode]
    s = []
    a = s.append
    # faint guide grid over threading, drawdown, treadling and tie-up
    def grid(x, y, cols, rows):
        for i in range(cols + 1):
            a(f'<line x1="{x + i * CW}" y1="{y}" x2="{x + i * CW}" y2="{y + rows * CH}" stroke="{c["line"]}" stroke-opacity="{c["faint"]}" stroke-width="1"/>')
        for j in range(rows + 1):
            a(f'<line x1="{x}" y1="{y + j * CH}" x2="{x + cols * CW}" y2="{y + j * CH}" stroke="{c["line"]}" stroke-opacity="{c["faint"]}" stroke-width="1"/>')
    grid(X0, Y0, ENDS, SHAFTS)
    grid(DX, DY, ENDS, PICKS)
    grid(TX, DY, TREADLES, PICKS)
    grid(TX, Y0, TREADLES, SHAFTS)

    def cell(x, y, color, op=1.0, hollow=False):
        if hollow:
            a(f'<rect x="{x + 4.5}" y="{y + 4.5}" width="{CW - 9}" height="{CH - 9}" fill="none" stroke="{c["line"]}" stroke-opacity="{c["hollow"]}" stroke-width="1"/>')
        else:
            a(f'<rect x="{x + 3}" y="{y + 3}" width="{CW - 6}" height="{CH - 6}" fill="{color}" fill-opacity="{op}"/>')

    # warp hairlines: one per end, from above the threading to a loose end below the drawdown
    for e in range(ENDS):
        x = DX + e * CW + CW / 2
        tail = 26 + (e * 7) % 23
        a(f'<line x1="{x}" y1="{Y0 - 34}" x2="{x}" y2="{DY + PICKS * CH + tail}" stroke="{c["line"]}" stroke-opacity="0.16" stroke-width="0.8"/>')
    # threading (shaft 1 at the bottom row of the strip, as in a draft)
    for e, sh in enumerate(threading):
        cell(X0 + e * CW, Y0 + (SHAFTS - 1 - sh) * CH, c["line"], 0.85)
    # tie-up
    for t, shafts in tieup.items():
        for sh in shafts:
            cell(TX + t * CW, Y0 + (SHAFTS - 1 - sh) * CH, c["hold"] if t >= 4 else c["line"], 0.85)
    # treadling and drawdown
    k = 0
    for p, t in enumerate(treadling):
        y = DY + p * CH
        held = p in BAND
        cell(TX + t * CW, y, c["hold"] if held else c["line"], 0.85)
        if held:
            # one end at a time passes; every other end waits, drawn hollow
            turn = 3 + k * 3
            k += 1
            for e in range(ENDS):
                if e == turn:
                    cell(DX + e * CW, y, c["hold"])
                else:
                    cell(DX + e * CW, y, None, hollow=True)
        else:
            for e, sh in enumerate(threading):
                if sh in tieup[t]:
                    cell(DX + e * CW, y, c["mark"])
    # the weft for the held band: a single saffron hairline stepping through the turns
    pts = []
    for i, p in enumerate(BAND):
        x = DX + (3 + i * 3) * CW + CW / 2
        pts.append(f"{x},{DY + p * CH + CH / 2}")
    a(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{c["hold"]}" stroke-width="1.2" stroke-opacity="0.9"/>')

    # reference markers: pick numbers every 4 on the left, end numbers every 4 on top
    mono = 'font-family="JB" font-size="13" letter-spacing="1.5"'
    for p in range(4, PICKS + 1, 4):
        a(f'<text x="{DX - 18}" y="{DY + p * CH - 6}" text-anchor="end" {mono} fill="{c["line"]}" fill-opacity="0.42">{p:02d}</text>')
    for e in range(4, ENDS + 1, 4):
        a(f'<text x="{DX + e * CW - CW / 2}" y="{Y0 - 46}" text-anchor="middle" {mono} fill="{c["line"]}" fill-opacity="0.42">{e:02d}</text>')
    # band brackets on the right edge of the treadling
    by0, by1 = DY + BAND.start * CH, DY + BAND.stop * CH
    bx = TX + TREADLES * CW + 18
    a(f'<path d="M{bx - 6} {by0} H{bx} V{by1} H{bx - 6}" fill="none" stroke="{c["hold"]}" stroke-width="1.2"/>')
    a(f'<text x="{bx + 14}" y="{(by0 + by1) / 2 + 4}" {mono} fill="{c["hold"]}">HOLD</text>')

    # plate caption, top right
    RX = 1640
    a(f'<text x="{RX}" y="{Y0 + 14}" {mono} fill="{c["line"]}" fill-opacity="{c["text"]}">PLATE III</text>')
    a(f'<line x1="{RX}" y1="{Y0 + 34}" x2="{RX + 520}" y2="{Y0 + 34}" stroke="{c["line"]}" stroke-opacity="0.35" stroke-width="1"/>')
    a(f'<text x="{RX}" y="{Y0 + 64}" {mono} fill="{c["line"]}" fill-opacity="0.5">DRAWDOWN · {ENDS} ENDS × {PICKS} PICKS</text>')
    a(f'<text x="{RX}" y="{Y0 + 90}" {mono} fill="{c["line"]}" fill-opacity="0.5">POINTED DRAW · 2/2 TWILL</text>')

    # the whispered phrase
    a(f'<text x="{RX - 6}" y="{DY + BAND.start * CH + 52}" font-family="IS" font-style="italic" font-size="92" fill="{c["line"]}" fill-opacity="0.92">happens</text>')
    a(f'<text x="{RX + 92}" y="{DY + BAND.start * CH + 144}" font-family="IS" font-style="italic" font-size="92" fill="{c["line"]}" fill-opacity="0.92">before</text>')

    # key, bottom right, aligned with the last pick
    ky = DY + PICKS * CH - 60
    for i, (label, kind) in enumerate([("RUN", "mark"), ("WAIT", "hollow"), ("HOLD", "hold")]):
        x = RX + i * 170
        if kind == "hollow":
            cell(x, ky, None, hollow=True)
        else:
            cell(x, ky, c[kind])
        a(f'<text x="{x + CW + 12}" y="{ky + 15}" {mono} fill="{c["line"]}" fill-opacity="0.6">{label}</text>')
    a(f'<line x1="{RX}" y1="{ky + 44}" x2="{RX + 520}" y2="{ky + 44}" stroke="{c["line"]}" stroke-opacity="0.35" stroke-width="1"/>')
    a(f'<text x="{RX}" y="{ky + 72}" {mono} fill="{c["line"]}" fill-opacity="0.42">1 PICK = 1 TURN</text>')

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="{c["ground"]}"/>{"".join(s)}</svg>'
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:JB;src:url('file://{FONTS}/JetBrainsMono-Regular.ttf')}}
@font-face{{font-family:IS;font-style:italic;src:url('file://{FONTS}/InstrumentSerif-Italic.ttf')}}
html,body{{margin:0;background:{c["ground"]}}}svg{{display:block}}</style></head><body>{svg}</body></html>"""
    (OUT / f"plate-{mode}.html").write_text(html)
    (OUT / f"plate-{mode}.svg").write_text(svg)


for m in PAL:
    plate(m)
print("ok")
