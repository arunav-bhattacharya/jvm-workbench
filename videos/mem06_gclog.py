from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"-Xlog:gc with a star", "X log G C with a star"), (r"-Xlog:gc", "X log G C"), (r"\bPrintGCDetails\b", "print G C details"),
    (r"0\.440s", "0.440 seconds"), (r"\bGC\(0\)", "G C zero"), (r"\bGC\(17\)", "G C seventeen"),
    (r"(\d+(?:\.\d+)?)ms\b", r"\1 milliseconds"), (r"\b(\d+(?:\.\d+)?) ms\b", r"\1 milliseconds"),
    (r"\b(\d+)M\b", r"\1 megabytes"), (r"\bMB\b", "megabytes"), (r"\bKB\b", "kilobytes"),
    (r"\bgc\.log\.0\b", "G C dot log dot zero"), (r"\bgc\.log\b", "G C dot log"), (r"\bHotSpot\b", "hot spot"),
]

# every spoken line, in order
N = {
    "open": "Every cleaning crew keeps a logbook. After each round, someone writes one line: when it happened, what "
            "kind of round it was and why, how full the floor was before and after, and how long the workers waited.",
    "open2": "After a bad afternoon, that logbook is how you find out what happened.",
    "shyq": "So here's a question that's easy to be shy about. My requests got slow this afternoon. Was it the garbage "
            "collector? And how would I even know?",
    "flag": "The JVM keeps that logbook too, if you ask. One flag, -Xlog:gc, makes the garbage collector write a line "
            "for every collection. Older guides show PrintGCDetails, which JDK 9 replaced.",
    "line": "Here's the first line from G1, the default collector, on JDK 25, running the thumbnail service's stand-in "
            "load. It looks like noise. It isn't. Let's read it left to right, like a logbook entry.",
    "when": "0.440s, in brackets, is when: the time since the JVM started. Then the log level, info, and the tag, gc, "
            "the topic of the line.",
    "id": "GC(0) numbers the collection. Round zero, the very first one.",
    "what": "Pause Young is the event, the kind of round. Pause means every application thread was stopped. Normal says "
            "it cleaned only the young part of the heap. And G1 Evacuation Pause is the why: eden, the area for new "
            "objects, was full.",
    "full": "Then, how full the floor was. 28M, an arrow, 2M, and 214M in brackets. That's the heap in use before the "
            "pause, the heap in use after it, and the committed heap, the memory the operating system has really "
            "handed over.",
    "wait": "And last, 8.692ms: how long every one of your threads stood still. That's the number a person waiting on a "
            "request feels.",
    "predq": "Now a stretch from the same run, with the start of each line cut off. Seven lines. Which ones stopped your "
             "threads? Pause and guess.",
    "wrong": "The tempting answer is every line that ends in milliseconds. But look at the second Concurrent Mark Cycle "
             "line. That cycle took 25.055 ms, and it ran beside your program, while your threads kept working.",
    "rule": "So here's the rule, and it works for every HotSpot collector. A pause line has Pause right after GC and its "
            "number, and ends with a duration in ms. Five lines pass: Concurrent Start, Remark, Cleanup, Prepare Mixed "
            "and Mixed. 26.5 ms in all.",
    "joke": "It's like a bread recipe. Knead for five minutes, then let it rise for an hour. Only the kneading keeps your "
            "hands busy. So the point is: read the word right after GC, not just the number at the end.",
    "evac": "Now look at the last two lines: Evacuation Failure, twice in a row. G1 ran out of free regions to copy into, "
            "so this heap is too small for what's live. JDK 21 writes just Evacuation Failure, and JDK 25 adds the "
            "reason. Search for Evacuation Failure, and you'll find both.",
    "star": "-Xlog:gc with a star turns on every GC tag: phases, region counts, metaspace and CPU time. That's ten to "
            "fifteen lines per pause, for when you need the detail.",
    "prod": "For a service, write the log to rotating files with the time of day. The colons split it into four parts. "
            "What to log, where to write it, the decorations at the start of each line, and the rotation: at most 5 "
            "files of 20 MB.",
    "brk": "Here a paper logbook and the JVM part ways. When the current gc.log is full, the JVM renames it to a "
           "numbered file, like gc.log.0, and starts a fresh one. And with five files, the oldest one is thrown away.",
    "demo": "The lesson's demo does just this, with tiny 40 KB files so you can watch them rotate. Two seconds of load in "
            "a 256 MB heap. The first young pause went from 29M to 2M. The last ones left 120 to 245 MB behind: the floor "
            "rose as the cache filled. And the files held 2 Pause Full lines, and 7 to 13 lines with Evacuation Failure.",
    "guard": "So leave the logbook on in production. It costs a few lines per collection, and in an incident it's the "
             "first thing you'll want.",
    "joke2": "A logbook you start after the bad afternoon is just a diary of the next one. So turn it on before you need "
             "it.",
    "moral": "So, was it the garbage collector? Open the logbook. Find the lines with Pause right after the number, and "
             "read how long each one stopped your threads. Then watch the after-values. If that floor keeps rising, "
             "something is filling the heap.",
    "check": "Quick check. GC(17) Concurrent Mark Cycle 25.055ms. Did your threads stand still for 25 milliseconds?",
    "check_a": "No. There's no Pause after the number, so that cycle ran beside your threads. Its two pauses, Remark and "
               "Cleanup, have lines of their own.",
}

# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at()/at_text() wait for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4, pos=(-6.4, 3.3), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole memory track's warehouse
WORKER, BOX, NOTE, CREW, PLAN, BAD, OK = BLUE_M, GOLD_M, YELLOW_M, TEAL_M, PURPLE_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color=WORKER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def crate(w=1.0, h=0.75, color=BOX, label=True):
    """A cardboard box on a shelf: body [0], tape [1], and a small paper label [2]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.26), 1)
    tape = Rectangle(width=w * 0.18, height=h * 0.3).set_stroke(width=0).set_fill(dim(color, 0.6), 1).move_to(body.get_top() + DOWN * h * 0.15)
    g = VGroup(body, tape)
    if label:
        lab = Rectangle(width=w * 0.5, height=h * 0.26).set_stroke(GREY_B, 1).set_fill(PAPER, 1).move_to(body.get_center() + DOWN * h * 0.12)
        g.add(lab)
    return g


def shelf(x0, x1, y, color=GREY_B):
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=4, color=color)
    return top


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26, mono_right=False):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = (M if mono_right else T)(right, size - 2 if mono_right else size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    """Rows of (left, arrow, right) with the arrows in one column at x_arrow."""
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def table(rows, widths, size=24, colors=None, dy=0.55, mono_cols=()):
    """A plain table: rows of strings, column widths; the first row is the header (grey)."""
    out = VGroup()
    for i, r in enumerate(rows):
        line = VGroup()
        x = 0
        for j, (cell, w) in enumerate(zip(r, widths)):
            c = GREY_B if i == 0 else ((colors or {}).get((i, j)) or WHITE)
            t = (M if (j in mono_cols and i > 0) else T)(cell, size if i else size - 2, c)
            if j == 0:
                t.move_to([x, -i * dy, 0], aligned_edge=LEFT)
            else:
                t.move_to([x + w / 2, -i * dy, 0])
            line.add(t)
            x += w
        out.add(line)
    return out


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


EDEN_C, SURV_C, OLD_C, GARB = GREEN_M, PURPLE_M, BLUE_M, GREY_D


def area(w, h, color, title, size=24):
    r = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.08), 1)
    t = T(title, size, color).next_to(r, UP, buff=0.12)
    return VGroup(r, t)


def mini(color=BOX, s=0.42):
    return Rectangle(width=s, height=s * 0.75).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)


def fill_grid(rect, n_cols, n_rows, color=BOX, s=0.42):
    cx, cy = rect.get_center()[:2]
    w, h = rect.width, rect.height
    out = VGroup()
    for j in range(n_rows):
        for i in range(n_cols):
            x = cx - w / 2 + (i + 0.5) * w / n_cols
            y = cy + h / 2 - (j + 0.5) * h / n_rows
            out.add(mini(color, s).move_to([x, y, 0]))
    return out


# ---- the logbook: one colour per column, the same all video ----
WHEN_C, ROUND_C, KIND_C, FULL_C, WAIT_C = GREY_A, PURPLE_M, CREW, GREEN_M, RED_M

LINE0 = [("[0.440s]", WHEN_C), ("[info]", GREY_B), ("[gc]", GREY_B), ("GC(0)", ROUND_C), ("Pause Young", KIND_C),
         ("(Normal)", KIND_C), ("(G1 Evacuation Pause)", YELLOW_M), ("28M->2M(214M)", FULL_C), ("8.692ms", WAIT_C)]

STRETCH = [("GC(16) Pause Young (Concurrent Start) (G1 Humongous Allocation)", "205M->158M(256M) 8.143ms"),
           ("GC(17) Concurrent Mark Cycle", None),
           ("GC(17) Pause Remark 185M->185M(256M) 0.447ms", None),
           ("GC(17) Pause Cleanup 185M->185M(256M) 0.085ms", None),
           ("GC(17) Concurrent Mark Cycle 25.055ms", None),
           ("GC(18) Pause Young (Prepare Mixed) (G1 Evacuation Pause)", "(Evacuation Failure: Allocation) 248M->142M(256M) 3.544ms"),
           ("GC(19) Pause Young (Mixed) (G1 Evacuation Pause)", "(Evacuation Failure: Allocation) 248M->211M(256M) 14.287ms")]


def logbook(w=11.4, rows=3):
    heads = ["when", "which round", "kind, and why", "before -> after", "workers waited"]
    cols = [1.7, 2.1, 2.7, 2.5, 2.4]
    r = Rectangle(width=w, height=0.6 + rows * 0.55).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    g = VGroup(r)
    x = r.get_left()[0]
    for k, (h, cw) in enumerate(zip(heads, cols)):
        g.add(T(h, 22, INK).move_to([x + cw / 2, r.get_top()[1] - 0.3, 0]))
        if k:
            g.add(Line([x, r.get_top()[1], 0], [x, r.get_bottom()[1], 0], stroke_width=1.2, color=GREY_B))
        x += cw
    for j in range(rows):
        y = r.get_top()[1] - 0.6 - j * 0.55
        g.add(Line([r.get_left()[0], y, 0], [r.get_right()[0], y, 0], stroke_width=1.0, color=GREY_B))
    return g


def stretch_term(disp):
    out = term(disp, 22, "the same JDK 25 run, decorations cut off")
    cw = M("0123456789", 22).width / 10
    conts = {a for a, b in STRETCH if b} and {b for a, b in STRETCH if b}
    for k, line in enumerate(disp):
        if line in conts:
            out[1][k].shift(RIGHT * 4 * cw)
    out[0].stretch_to_fit_width(out[1].width + 0.5).move_to(out[1])
    out[2].next_to(out[0], UP, buff=0.1).align_to(out[0], LEFT)
    return out


def field_chip(txt, color, size=26):
    t = M(txt, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.24, height=0.62).set_stroke(color, 2).set_fill("#101010", 1)
    return VGroup(r, t.move_to(r))


class Mem06Gclog(Narrated):
    """mem-06, section 0 (with the pause rule of section 1): the crew's logbook; the shy question (was it the GC, and
    how would I know?); -Xlog:gc; G1's first line on JDK 25 read field by field and mapped onto the logbook columns;
    predict which of seven lines stopped the threads; break 'every duration is a pause' (Concurrent Mark Cycle
    25.055 ms); the rule; the bread recipe; Evacuation Failure on JDK 21 and 25; -Xlog:gc*; the production setting
    and rotation, where the logbook picture breaks; GcLogFileDemo's run (29M->2M, 120 to 245 MB, 2 Pause Full,
    7 to 13 Evacuation Failure); leave it on, and the diary; moral; a check."""

    def construct(self):
        self.title_card("The crew's logbook", "reading one GC log line, field by field")

        # ================= the logbook =================
        crew = VGroup(*[person(CREW, 1.1) for _ in range(2)]).arrange(RIGHT, buff=0.3).move_to([-5.2, -2.6, 0])
        crew_t = T("the cleaning crew", 22, CREW).next_to(crew, DOWN, buff=0.12)
        lb = logbook().move_to([0, 1.6, 0])
        heads = [x for x in lb if isinstance(x, Text)]
        self.say("open")
        self.play(FadeIn(crew), FadeIn(crew_t), run_time=0.5)
        self.play(FadeIn(lb[0]), *[FadeIn(x) for x in lb if isinstance(x, Line)], run_time=0.6)
        for k, key in enumerate(("when it", "what kind", "and why", "how full", "how long")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(heads[k], shift=DOWN * 0.05), run_time=0.35)
        self.hold()
        bad = T("a bad afternoon: the logbook says what happened", 28, YELLOW_M).move_to([0, -1.4, 0])
        self.say("open2")
        self.play(FadeIn(bad, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("My requests got slow this afternoon.", 34)
        q2 = T("Was it the garbage collector?", 38, YELLOW_M)
        q3 = T("And how would I even know?", 34, GREY_A)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.3)
        self.wipe()

        # ================= the flag, and one line =================
        flag = M("java -Xlog:gc ...", 36, YELLOW_M).move_to([0, 2.0, 0])
        old = VGroup(M("-XX:+PrintGCDetails", 26, GREY_B), T("older guides; replaced in JDK 9", 24, GREY_B)).arrange(RIGHT, buff=0.3).move_to([0, 0.9, 0])
        strike = Line(old[0].get_left(), old[0].get_right(), stroke_width=3, color=BAD)
        self.say("flag")
        self.at(1)
        self.play(FadeIn(flag, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(old), run_time=0.5)
        self.play(Create(strike), run_time=0.4)
        self.hold()
        self.wipe()

        raw = M("[0.440s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 28M->2M(214M) 8.692ms", 24, GREY_A)
        fit(raw, 12.6).move_to([0, 2.6, 0])
        src = T("G1, JDK 25, the thumbnail service's stand-in load", 22, GREY_B).next_to(raw, DOWN, buff=0.2)
        self.say("line")
        self.play(FadeIn(raw), FadeIn(src), run_time=0.7)
        self.hold()

        chips = VGroup(*[field_chip(t, c) for t, c in LINE0])
        for k, c in enumerate(chips):
            c.move_to([-0.5, 1.95 - k * 0.6, 0], aligned_edge=RIGHT)
        labs = ["when: time since the JVM started", "log level", "tag: the topic", "which round", "the event", "young only",
                "why", "before -> after (committed)", "how long every thread stood still"]
        labt = VGroup(*[T(l, 26, LINE0[k][1]).next_to(chips[k], RIGHT, buff=0.35) for k, l in enumerate(labs)])
        for l in labt:
            l.move_to([0.0, l.get_center()[1], 0], aligned_edge=LEFT)

        def show(ks):
            return [FadeIn(chips[k], shift=DOWN * 0.1) for k in ks] + [FadeIn(labt[k]) for k in ks]

        self.say("when")
        self.play(FadeOut(src), raw.animate.move_to([0, 2.95, 0]), *show([0]), run_time=0.6)
        self.at(1)
        self.play(*show([1, 2]), run_time=0.6)
        self.hold()
        self.say("id")
        self.play(*show([3]), run_time=0.6)
        self.hold()
        self.say("what")
        self.play(*show([4]), run_time=0.5)
        self.at(1)
        pz = T(": every application thread stopped", 26, KIND_C).next_to(labt[4], RIGHT, buff=0.05)
        self.play(FadeIn(pz), run_time=0.4)
        self.at(2)
        self.play(*show([5]), run_time=0.5)
        self.at(3)
        self.play(*show([6]), run_time=0.5)
        ed = T(": eden was full", 26, YELLOW_M).next_to(labt[6], RIGHT, buff=0.05)
        self.play(FadeIn(ed), run_time=0.4)
        self.hold()
        self.say("full")
        self.play(*show([7]), run_time=0.6)
        self.at(2)
        self.play(Indicate(chips[7][1], color=FULL_C, scale_factor=1.12), run_time=0.9)
        self.hold()
        self.say("wait")
        self.play(*show([8]), run_time=0.6)
        self.at(1)
        feel = T("what a person waiting on a request feels", 26, WAIT_C).move_to([0, -3.45, 0])
        self.play(FadeIn(feel), Indicate(chips[8], color=WAIT_C, scale_factor=1.1), run_time=0.8)
        self.hold(after=0.6)
        self.wipe()

        # ================= which lines stopped the threads? =================
        disp = []
        for a, b in STRETCH:
            disp.append(a)
            if b:
                disp.append(b)
        out = stretch_term(disp)
        fit(out, 12.6).move_to([0, 0.6, 0])
        L = out[1]
        logical = []                    # display-line indices for each of the seven log lines
        k = 0
        for a, b in STRETCH:
            logical.append([k, k + 1] if b else [k])
            k += 2 if b else 1
        self.say("predq")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.1) for x in L], lag_ratio=0.15), run_time=1.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        cm = L[logical[4][0]]
        self.say("wrong")
        ms_ends = [L[logical[i][-1]] for i in range(7) if STRETCH[i][0].endswith("ms") or STRETCH[i][1]]
        self.play(*[Indicate(x[-8:], color=YELLOW_M, scale_factor=1.15) for x in ms_ends], run_time=0.9)
        self.at(1)
        self.play(part(cm, "ConcurrentMarkCycle").animate.set_color(CREW), part(cm, "25.055ms").animate.set_color(CREW), run_time=0.6)
        self.at(2)
        beside = T("ran beside your program: not a pause", 26, CREW).move_to([0, -2.9, 0])
        self.play(FadeIn(beside), run_time=0.5)
        self.hold()
        rl = VGroup(T("A pause line has", 26), M("Pause", 26, BAD), T("right after", 26), M("GC(id)", 26, ROUND_C),
                    T("and ends in", 26), M("ms", 26, WAIT_C)).arrange(RIGHT, buff=0.16).move_to([0, -2.9, 0])
        fit(rl, 12.4)
        pauses = [0, 2, 3, 5, 6]
        self.say("rule")
        self.play(FadeOut(beside), FadeIn(rl), run_time=0.6)
        self.at(2)
        marks = VGroup(*[tick(True, 0.16).next_to(L[logical[i][-1]], RIGHT, buff=0.15) for i in pauses])
        self.play(*[part(L[logical[i][0]], "Pause").animate.set_color(BAD) for i in pauses], FadeIn(marks), run_time=0.8)
        self.at(3)
        tot = T("5 pauses, 26.5 ms in all", 28, BAD).next_to(out, UP, buff=0.15).align_to(out, RIGHT)
        self.play(FadeIn(tot), run_time=0.5)
        self.hold()
        self.wipe(rt=0.5)

        # light moment: the bread recipe
        knead = VGroup(T("knead: 5 minutes", 32, BAD), T("your hands are busy", 24, GREY_A)).arrange(DOWN, buff=0.15).move_to([-3.2, 1.2, 0])
        rise = VGroup(T("let it rise: 1 hour", 32, CREW), T("you do something else", 24, GREY_A)).arrange(DOWN, buff=0.15).move_to([3.2, 1.2, 0])
        cash = T("read the word right after GC, not just the number at the end", 28, YELLOW_M).move_to([0, -1.4, 0])
        fit(cash, 12.4)
        self.say("joke")
        self.at(1)
        self.play(FadeIn(knead), run_time=0.5)
        self.at_text("then let", lead=0.2)
        self.play(FadeIn(rise), run_time=0.5)
        self.at(3)
        self.play(FadeIn(cash, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= evacuation failure, two spellings =================
        out = stretch_term(disp)
        fit(out, 12.6).move_to([0, 1.2, 0])
        L = out[1]
        self.add(out)
        self.say("evac")
        ef = [L[logical[5][1]], L[logical[6][1]]]
        self.play(*[part(x, "(EvacuationFailure:Allocation)").animate.set_color(BAD) for x in ef], run_time=0.8)
        self.at(1)
        small = T("no free regions to copy into: the heap is too small for what's live", 24, BAD).move_to([0, -1.85, 0])
        fit(small, 12.4)
        self.play(FadeIn(small), run_time=0.5)
        self.at(2)
        v = VGroup(VGroup(M("JDK 21", 24, GREY_B), M("(Evacuation Failure)", 24, BAD)).arrange(RIGHT, buff=0.3),
                   VGroup(M("JDK 25", 24, GREY_B), M("(Evacuation Failure: Allocation)", 24, BAD)).arrange(RIGHT, buff=0.3))
        v.arrange(DOWN, buff=0.15, aligned_edge=LEFT).move_to([0, -2.9, 0])
        self.play(FadeIn(v), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= more detail, and the production setting =================
        star = VGroup(M("-Xlog:gc*", 34, YELLOW_M), T("every GC tag: phases, region counts, metaspace, CPU time", 26)).arrange(RIGHT, buff=0.35)
        fit(star, 12.4).move_to([0, 2.7, 0])
        star2 = T("10 to 15 lines per pause", 24, GREY_A).next_to(star, DOWN, buff=0.15)
        self.say("star")
        self.play(FadeIn(star), run_time=0.6)
        self.at(1)
        self.play(FadeIn(star2), run_time=0.4)
        self.hold()
        parts_ = [("gc*", "what to log"), ("file=/var/log/app/gc.log", "where to write it"),
                  ("time,uptime,level,tags", "decorations: time of day first"), ("filecount=5,filesize=20m", "rotation: 5 files of 20 MB")]
        pr = VGroup(M("-Xlog:", 26, GREY_A))
        for k, (p_, _) in enumerate(parts_):
            pr.add(M(p_, 26, [YELLOW_M, KIND_C, WHEN_C, FULL_C][k]))
            if k < 3:
                pr.add(M(":", 26, GREY_A))
        pr.arrange(RIGHT, buff=0.04)
        fit(pr, 12.6).move_to([0, 0.9, 0])
        segs = [pr[1], pr[3], pr[5], pr[7]]
        plabs = VGroup(*[T(lbl, 22, s.get_color()).move_to([0, -0.2 - k * 0.5, 0]) for k, ((_, lbl), s) in enumerate(zip(parts_, segs))])
        lines_ = VGroup()
        for k, s in enumerate(segs):
            plabs[k].move_to([s.get_center()[0], -0.1 - k * 0.55, 0])
            lines_.add(DashedLine(s.get_bottom() + DOWN * 0.05, plabs[k].get_top() + UP * 0.05, stroke_width=1.5, color=GREY_D))
        for k in range(4):
            if plabs[k].get_left()[0] < -6.5:
                plabs[k].shift(RIGHT * (-6.5 - plabs[k].get_left()[0]))
            if plabs[k].get_right()[0] > 6.5:
                plabs[k].shift(LEFT * (plabs[k].get_right()[0] - 6.5))
        self.say("prod")
        self.play(FadeIn(pr), run_time=0.7)
        self.at(1)
        self.play(*[Indicate(pr[i], color=WHITE, scale_factor=1.5) for i in (2, 4, 6)], run_time=0.8)
        for k, key in enumerate(("What to log", "where to write", "the decorations", "and the rotation")):
            self.at_text(key, lead=0.2)
            self.play(Create(lines_[k]), FadeIn(plabs[k]), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= where the logbook picture breaks: rotation =================
        def fbox(name, color=GREY_A):
            r = Rectangle(width=2.0, height=1.4).set_stroke(color, 2.5).set_fill("#151515", 1)
            return VGroup(r, M(name, 22, color).move_to(r))
        cur = fbox("gc.log", YELLOW_M).move_to([-5.3, 0.6, 0])
        fill = Rectangle(width=2.0, height=0.01).set_stroke(width=0).set_fill(YELLOW_M, 0.35).move_to(cur[0].get_bottom(), aligned_edge=DOWN)
        paper_t = T("a paper logbook keeps every page", 24, GREY_B).move_to([0, 2.7, 0])
        self.say("brk")
        self.play(FadeIn(paper_t), FadeIn(cur), run_time=0.5)
        self.at(1)
        self.play(fill.animate.stretch_to_fit_height(1.38).move_to(cur[0].get_bottom(), aligned_edge=DOWN), run_time=1.0)
        f0 = fbox("gc.log.0").move_to([-2.6, 0.6, 0])
        self.play(cur.animate.move_to(f0), FadeOut(fill), run_time=0.7)
        self.play(Transform(cur[1], M("gc.log.0", 22, GREY_A).move_to(f0)), cur[0].animate.set_stroke(GREY_A), run_time=0.4)
        fresh = fbox("gc.log", YELLOW_M).move_to([-5.3, 0.6, 0])
        self.play(FadeIn(fresh), run_time=0.4)
        self.at(2)
        olds = VGroup(*[fbox(f"gc.log.{i}") for i in (1, 2, 3)]).arrange(RIGHT, buff=0.25).next_to(f0, RIGHT, buff=0.25)
        self.play(FadeIn(olds), run_time=0.5)
        gone = olds[-1]
        self.play(gone.animate.shift(DOWN * 2.2).set_opacity(0.2), run_time=0.8)
        tossed = T("the oldest is thrown away", 24, BAD).next_to(gone, DOWN, buff=0.15)
        fc = T("filecount=5", 24, GREY_B).move_to([0, -2.9, 0])
        self.play(FadeIn(tossed), FadeIn(fc), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the demo's run =================
        u = 11.0 / 256
        heap = Rectangle(width=256 * u, height=0.55).set_stroke(GREY_B, 2).move_to([-5.5, 1.9, 0], aligned_edge=LEFT)
        heap_t = T("256 MB heap", 22, GREY_B).next_to(heap, UP, buff=0.1).align_to(heap, LEFT)
        first = Rectangle(width=2 * u, height=0.55).set_stroke(FULL_C, 2).set_fill(FULL_C, 0.7).move_to(heap.get_left(), aligned_edge=LEFT)
        first_t = T("first young pause: 29M -> 2M", 24, FULL_C).next_to(heap, DOWN, buff=0.15).align_to(heap, LEFT)
        heap2 = heap.copy().move_to([-5.5, -0.4, 0], aligned_edge=LEFT)
        lo = Rectangle(width=120 * u, height=0.55).set_stroke(FULL_C, 2).set_fill(FULL_C, 0.7).move_to(heap2.get_left(), aligned_edge=LEFT)
        hi = Rectangle(width=245 * u, height=0.55).set_stroke(FULL_C, 2).set_fill(FULL_C, 0.7).move_to(heap2.get_left(), aligned_edge=LEFT)
        last_t = T("the last ones leave 120 to 245 MB behind", 24, FULL_C).next_to(heap2, DOWN, buff=0.15).align_to(heap2, LEFT)
        demo_t = T("GcLogFileDemo, JDK 25: 40 KB files, two seconds of load", 22, GREY_B).move_to([0, 3.0, 0])
        cnt = VGroup(VGroup(M("Pause Full", 26, BAD), T("lines: 2", 26)).arrange(RIGHT, buff=0.2),
                     VGroup(M("Evacuation Failure", 26, BAD), T("lines: 7 to 13", 26)).arrange(RIGHT, buff=0.2)).arrange(RIGHT, buff=1.0)
        cnt.move_to([0, -2.7, 0])
        self.say("demo")
        self.play(FadeIn(demo_t), run_time=0.4)
        self.at(1)
        self.play(FadeIn(heap), FadeIn(heap_t), run_time=0.5)
        self.at(2)
        self.play(GrowFromEdge(first, LEFT), FadeIn(first_t), run_time=0.6)
        self.at(3)
        self.play(FadeIn(heap2), GrowFromEdge(lo, LEFT), FadeIn(last_t), run_time=0.7)
        self.play(Transform(lo, hi), run_time=0.9)
        self.at(4)
        self.play(FadeIn(cnt), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail and the diary =================
        g1 = rule_row("leave the logbook on in production", 30)
        g2 = T("a few lines per collection; the first thing you'll want in an incident", 26, GREY_A)
        gg = VGroup(g1, g2).arrange(DOWN, buff=0.25).move_to([0, 2.0, 0])
        fit(gg, 12.4)
        self.say("guard")
        self.play(FadeIn(g1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(g2), run_time=0.5)
        self.hold()
        diary = paper(["Dear diary,", "the next bad afternoon", "went like this..."], 24).move_to([-2.6, -1.0, 0])
        tip = T("turn it on before you need it", 30, YELLOW_M).move_to([3.0, -1.0, 0])
        self.say("joke2")
        self.play(FadeIn(diary, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tip), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mg = VGroup(T("open the logbook", 30), VGroup(T("find the lines with", 30), M("Pause", 30, BAD), T("right after the number", 30)).arrange(RIGHT, buff=0.18),
                    T("read how long each one stopped your threads", 30, WAIT_C),
                    T("watch the after-values: a rising floor means something fills the heap", 30, FULL_C)).arrange(DOWN, buff=0.3).move_to([0, 0.5, 0])
        fit(mg, 12.4)
        self.say("moral")
        for k, key in enumerate(("Open the", "Find the", "and read", "Then watch")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(mg[k], shift=UP * 0.1), run_time=0.45)
        self.hold()
        self.wipe()

        cl = M("GC(17) Concurrent Mark Cycle 25.055ms", 30).move_to([0, 1.4, 0])
        cq = VGroup(T("Check:", 30, YELLOW_M), T("did your threads stand still for 25 ms?", 30)).arrange(RIGHT, buff=0.25).move_to([0, 2.8, 0])
        self.say("check")
        self.play(FadeIn(cq), FadeIn(cl), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = T("No: no Pause after the number. It ran beside your threads.", 30, CREW).move_to([0, -0.1, 0])
        fit(ans, 12.4)
        ans2 = VGroup(M("Pause Remark", 26, BAD), T("and", 26), M("Pause Cleanup", 26, BAD), T("have lines of their own", 26)).arrange(RIGHT, buff=0.2).move_to([0, -1.2, 0])
        fit(ans2, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), part(cl, "ConcurrentMarkCycle").animate.set_color(CREW), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ans2), run_time=0.5)
        self.hold(after=0)
        self.wait(2.0)
