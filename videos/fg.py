"""Shared helpers for the course videos: 3Blue1Brown-style look + Kokoro teacher voice in sync.
Copied from ai-engineer-from-zero/videos/fg.py so both sites look and sound the same.
Set KOKORO_DIR to the folder with kokoro-v1.0.fp16.onnx and voices-v1.0.bin
(from github.com/thewh1teagle/kokoro-onnx releases, model-files-v1.0)."""
import hashlib, os, pathlib, re
import numpy as np, soundfile as sf
from manim import *  # noqa: F401,F403

config.background_color = "#000000"
FONT = "CMU Serif"
MONO = "CMU Typewriter Text"
BLUE_M, TEAL_M, GREEN_M, YELLOW_M, GOLD_M, RED_M, PURPLE_M, GREY_M = (
    "#58C4DD", "#5CD0B3", "#83C167", "#F7D96F", "#F0AC5F", "#FC6255", "#9A72AC", "#888888")

HERE = pathlib.Path(__file__).resolve().parent
TTS = pathlib.Path(os.environ.get("KOKORO_DIR", HERE / "tts"))
CACHE = HERE / "voice"; CACHE.mkdir(parents=True, exist_ok=True)
_K = None
SAY = [
    (r"\bJVMs\b", "J V Ms"), (r"\bJVM\b", "J V M"), (r"\bJDK\b", "J D K"), (r"\bJMM\b", "J M M"), (r"\bJIT\b", "jit"),
    (r"\bJFR\b", "J F R"), (r"\bJMH\b", "J M H"), (r"\bGC\b", "G C"), (r"\bG1\b", "G one"), (r"\bZGC\b", "Z G C"),
    (r"\bC1\b", "C one"), (r"\bC2\b", "C two"), (r"\bCAS\b", "C A S"), (r"\bCPUs?\b", lambda m: "C P U" + ("s" if m.group(0).endswith("s") else "")),
    (r"\bNIO\b", "N I O"), (r"\bI/O\b", "I O"), (r"\bIO\b", "I O"), (r"\bOS\b", "O S"), (r"\bCDS\b", "C D S"), (r"\bAOT\b", "A O T"),
    (r"\bTLABs?\b", lambda m: "T lab" + ("s" if m.group(0).endswith("s") else "")), (r"\bepoll\b", "E poll"), (r"\bio_uring\b", "I O uring"),
    (r"\bVert\.x\b", "Vert X"), (r"\bjavac\b", "java C"), (r"\bjavap\b", "java P"), (r"\bjcmd\b", "J command"), (r"\bCRaC\b", "crack"),
    (r"\bAPIs?\b", lambda m: "A P I" + ("s" if m.group(0).endswith("s") else "")), (r"\bJSON\b", "jay-son"), (r"\bSQL\b", "S Q L"),
    (r"count\+\+", "count plus plus"), (r"\+\+", " plus plus"), (r"\be\.g\.", "for example"), (r"\bi\.e\.", "that is"),
]


def spoken(t):
    for pat, rep in SAY:
        t = re.sub(pat, rep, t)
    return t


def voice(text, speed=0.96):
    """Synthesize one line with Kokoro af_heart; returns (wav path, seconds). Cached by text."""
    global _K
    h = hashlib.sha1(f"af_heart|{speed}|{text}".encode()).hexdigest()[:16]
    p = CACHE / f"{h}.wav"
    if not p.exists():
        if _K is None:
            from kokoro_onnx import Kokoro
            _K = Kokoro(str(TTS / "kokoro-v1.0.fp16.onnx"), str(TTS / "voices-v1.0.bin"))
        parts, sr = [], 24000
        for s in re.split(r"(?<=[.!?])\s+", spoken(text).strip()):
            if not s.strip():
                continue
            a, sr = _K.create(s, voice="af_heart", speed=speed, lang="en-us")
            parts += [a.astype(np.float32), np.zeros(int(sr * 0.22), dtype=np.float32)]
        sf.write(p, np.concatenate(parts), sr)
    info = sf.info(str(p))
    return str(p), info.frames / info.samplerate


def T(text, size=36, color=WHITE, **kw):
    return Text(text, font=FONT, font_size=size, color=color, **kw)


def M(text, size=30, color=WHITE, **kw):
    return Text(text, font=MONO, font_size=size, color=color, **kw)


CAPS = HERE / "captions"; CAPS.mkdir(exist_ok=True)


def _ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


class VoiceScene(Scene):
    """beat(): speak one line and play animations inside that time, like a narrated 3b1b segment.
    Every spoken line is also written to captions/<Scene>.vtt, split by sentence."""

    def setup(self):
        self._cues = []

    def tear_down(self):
        out = ["WEBVTT", ""]
        for i, (a, b, txt) in enumerate(self._cues, 1):
            # WebVTT treats < and & as markup: escape them (text already escaped stays as it is)
            txt = re.sub(r"&(?!lt;|gt;|amp;)", "&amp;", txt).replace("<", "&lt;").replace(">", "&gt;")
            out += [str(i), f"{_ts(a)} --> {_ts(b)}", txt, ""]
        (CAPS / f"{type(self).__name__}.vtt").write_text("\n".join(out))

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def beat(self, text, *anims, run_time=None, after=0.25):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def title_card(self, title, sub=None):
        t = T(title, 54)
        g = VGroup(t)
        if sub:
            s = T(sub, 28, GREY_B).next_to(t, DOWN, buff=0.35)
            g.add(s)
        self.play(Write(t), run_time=1.2)
        if sub:
            self.play(FadeIn(g[1], shift=0.2 * UP), run_time=0.6)
        self.wait(0.4)
        self.play(FadeOut(g), run_time=0.5)


def box(label, color=WHITE, w=None, h=0.8, size=28):
    t = T(label, size)
    r = RoundedRectangle(corner_radius=0.12, width=w or max(1.6, t.width + 0.6), height=h, stroke_color=color, stroke_width=3)
    # solid fill (colour at 12% over black) so lines behind a box never show through it
    white = ManimColor(color).to_hex().upper() == "#FFFFFF"
    r.set_fill(BLACK if white else interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    return VGroup(r, t)


def arrow(a, b, color=GREY_B, buff=0.15, sw=3):
    """Thin 3b1b-style arrow between two points or mobjects."""
    pa = a.get_center() if isinstance(a, Mobject) else a
    pb = b.get_center() if isinstance(b, Mobject) else b
    return Arrow(pa, pb, buff=buff, stroke_width=sw, color=color, max_tip_length_to_length_ratio=0.12, max_stroke_width_to_length_ratio=8)


def edge_arrow(a, b, color=GREY_B, buff=0.12):
    """Arrow from the edge of mobject a to the edge of mobject b, along the line between centres."""
    pa, pb = ends(a, b)
    return Arrow(pa, pb, buff=buff, stroke_width=3, color=color,
                 max_tip_length_to_length_ratio=0.15, max_stroke_width_to_length_ratio=8)


def exit_point(m, d):
    """Where a ray from m's centre in direction d leaves m's bounding box."""
    c = m.get_center(); w, h = m.width / 2, m.height / 2
    t = min(w / abs(d[0]) if abs(d[0]) > 1e-6 else 1e9, h / abs(d[1]) if abs(d[1]) > 1e-6 else 1e9)
    return c + t * d


def ends(a, b):
    d = b.get_center() - a.get_center(); d = d / (np.linalg.norm(d) or 1)
    return exit_point(a, d), exit_point(b, -d)


def link(a, b, color=GREY_D, dashed=True, sw=1.5):
    """Plain connector line between the edges of two boxes."""
    pa, pb = ends(a, b)
    return (DashedLine(pa, pb, dash_length=0.08, stroke_width=sw, color=color) if dashed else Line(pa, pb, stroke_width=sw, color=color))


def chip(text, color=BLUE_M, size=28, mono=False):
    t = (M if mono else T)(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=max(0.62, t.height + 0.3), stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=0.18)
    return VGroup(r, t)


def travel(path_mob, color=YELLOW_M, run_time=1.0):
    """A small dot that runs along a line or arrow, to show something flowing."""
    d = Dot(radius=0.08, color=color).move_to(path_mob.get_start())
    line = Line(path_mob.get_start(), path_mob.get_end()) if isinstance(path_mob, Arrow) else path_mob
    return Succession(FadeIn(d, run_time=0.05), MoveAlongPath(d, line, rate_func=smooth, run_time=run_time), FadeOut(d, run_time=0.15))


def mbox(label, color=WHITE, w=None, h=0.8, size=22):
    """Box with a monospace label, for code names like tool names."""
    t = M(label, size)
    r = RoundedRectangle(corner_radius=0.12, width=w or max(1.6, t.width + 0.5), height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    return VGroup(r, t)


def on_circle(c, r, deg):
    return c + r * np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg)), 0])


def fit(m, w):
    """Shrink m to width w if it is wider."""
    if m.width > w:
        m.scale(w / m.width)
    return m


def tick(ok, s=0.2):
    """Green check or red cross drawn with strokes (fonts may lack the glyphs)."""
    if ok:
        return VMobject(stroke_color=GREEN_M, stroke_width=5).set_points_as_corners([[-1, 0.05, 0], [-0.35, -0.6, 0], [1, 0.8, 0]]).scale(s)
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(RED_M, 5).scale(s * 0.75)
