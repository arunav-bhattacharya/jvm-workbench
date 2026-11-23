from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bJOL\b", "jay oh ell"), (r"\bOpenJDK\b", "Open J D K"), (r"\bFalseSharingDemo\b", "false sharing demo"),
    (r"\bJvmField\b", "J V M field"), (r"\bLongAdder\b", "long adder"), (r"\bparsed\+\+", "parsed plus plus"),
]

# every spoken line, in order
N = {
    "open": "Picture two cooks at one counter, sharing a single cutting board. One chops onions. The other chops "
            "peppers. They never touch each other's vegetables. But only one knife fits on the board at a time, "
            "so each cook keeps stepping back, to wait for the other.",
    "shyq": "Now, a question that feels too silly to ask. My two threads never touch the same field. No shared "
            "data, no locks. So how could they possibly slow each other down?",
    "cache1": "To answer that, we go one level down, into the processor. Main memory is far away, as distances "
              "inside a computer go. So each core, the part that runs one thread, keeps small, fast memories "
              "close by. They're called caches.",
    "cache2": "And caches don't hold single variables. They hold cache lines: blocks of 64 bytes. The hardware "
              "moves the whole line, never one field. That's our cutting board. It moves as a unit, never a "
              "single onion.",
    "coh": "Each core keeps its own copy of the lines it uses, and the hardware keeps the copies in step. But a "
           "core that wants to write a line needs the only valid copy. Every other copy is marked invalid, and "
           "must be fetched again before it's used.",
    "obj": "Now the report service. A parser thread counts documents parsed. A writer thread counts reports "
           "written. Two volatile longs, in one small object. JOL, a small OpenJDK library, reads the real "
           "layout from the running JVM: parsed at offset 16, written at 24, in a 32 byte object. Eight bytes "
           "apart. Same board.",
    "map": "So let's map it. The cooks are the two threads. Their vegetables are the two fields. The board is the "
           "cache line. And stepping back for the knife is a core, waiting for the line.",
    "trace": "Let's trace two writes. Core 1 holds the line, and adds one to parsed. Core 2 wants to add one to "
             "written. Its copy is invalid, so it waits while the line travels over. Now core 1's copy is "
             "invalid, so its next write waits for the line to come back.",
    "name": "Each increment is a few nanoseconds of work, wrapped in a wait. The program shares nothing. The "
            "hardware shares a lot. This is called false sharing.",
    "pq": "FalseSharingDemo runs exactly this. Two threads, 25 million increments each. First with the fields "
          "side by side, then padded apart, onto lines of their own. How much faster is padded? Pause and guess.",
    "quiet": "On a quiet day, on the course machine, adjacent took 957 to 1,387 milliseconds. Padded took 206 to "
             "247. About five times faster, from nothing but space between two fields.",
    "busy": "But here's the same demo, same machine, on a busy day: 994 against 785. 977 against 784. A small "
            "gap. And across nine runs, padded lost one round in three.",
    "why": "So was the story wrong? No. More than twenty busy programs shared those four cores, so our two "
           "threads were rarely running at the same moment. A line only bounces between two cores that both want "
           "it right now. Our cooks were mostly working different shifts.",
    "count": "And notice what never changed. Every count ended at exactly 25 million. False sharing costs time, "
             "never correctness.",
    "breaks": "Here's where the cutting board picture breaks. A cook who waits for the board notices, and it costs "
              "seconds. A core waits nanoseconds for a line, and nobody notices, until it happens a few hundred "
              "million times. That's why you measure instead of guessing.",
    "fix": "The cure is space. Keep at least 64 bytes between fields that different threads write: give each cook "
           "a board of their own. The dependable way in Java is a chain of classes, because superclass fields "
           "are usually laid out first. With eight padding longs between them, JOL puts written at offset 88, "
           "72 bytes after parsed.",
    "code": "Here's the chain in Java and in Kotlin. Each hot field, and each block of padding, gets a class of its "
            "own. In Kotlin the classes must be abstract or open, and JvmField makes each property a plain field.",
    "guard": "Now the guardrails. Padding costs memory: 160 bytes instead of 32, on every object. Fine for one "
             "counter, a lot for a million. So pad only fields that different threads write in a hot loop. And "
             "don't promise a speed-up. The mechanism is certain. The size isn't. Measure on the hardware, and "
             "under the load, you really run with.",
    "rule": "Separate fields aren't separate memory. Fields that different threads write in a hot loop need lines "
            "of their own.",
    "moral": "The moral of the story: memory moves in 64 byte boards, not in fields. Two cooks who never touch "
             "each other's vegetables can still spend the day waiting for the board.",
    "chk": "Quick check. An array of longs, one slot per worker thread, and each thread adds to its own slot in a "
           "busy loop. Can they slow each other down?",
    "chka": "Yes. Slots 8 bytes apart share a line. And for a counter that many threads bump, the JDK has already "
            "done the padding for you: LongAdder, coming up next.",
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

    def predict(self, secs=2.4, pos=(6.4, 3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole performance track's kitchen
CARD, C1C, C2C, NOTE, COOK, BAD = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREY_A, RED_M
PAPER = "#EDE6D6"


def cook(s=1.0, color=COOK):
    body = RoundedRectangle(corner_radius=0.16, width=0.5, height=0.46).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.15).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    band = Rectangle(width=0.3, height=0.08).set_stroke(WHITE, 2).set_fill(WHITE, 1).next_to(head, UP, buff=0.01)
    puff = VGroup(*[Circle(radius=0.1).set_stroke(WHITE, 2).set_fill(WHITE, 1) for _ in range(3)]).arrange(RIGHT, buff=-0.08)
    puff.next_to(band, UP, buff=-0.05)
    return VGroup(body, head, band, puff).scale(s)


def recipe_card(lines=4, w=1.5, h=1.1, title="recipe"):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.18), 1)
    t = T(title, 18, CARD).move_to(r.get_top() + DOWN * 0.18)
    ls = VGroup(*[Line(LEFT * w * 0.36, RIGHT * w * 0.36, stroke_width=2, color=GREY_B) for _ in range(lines)])
    ls.arrange(DOWN, buff=(h - 0.45) / max(lines, 1) * 0.6).next_to(t, DOWN, buff=0.12)
    return VGroup(r, t, ls)


def cheat(w=1.1, h=0.8):
    r = Rectangle(width=w, height=h).set_stroke(C1C, 2.5).set_fill(dim(C1C, 0.3), 1).rotate(-6 * DEGREES)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=2.5, color=C1C) for _ in range(2)]).arrange(DOWN, buff=0.2)
    ls.move_to(r).rotate(-6 * DEGREES)
    return VGroup(r, ls)


def notepad(w=0.8, h=0.95):
    r = Rectangle(width=w, height=h).set_stroke(NOTE, 2.5).set_fill(dim(NOTE, 0.3), 1)
    rings = VGroup(*[Circle(radius=0.04).set_stroke(NOTE, 2) for _ in range(3)]).arrange(RIGHT, buff=0.12).move_to(r.get_top() + DOWN * 0.08)
    ls = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.8, color=NOTE) for _ in range(3)]).arrange(DOWN, buff=0.16)
    ls.move_to(r.get_center() + DOWN * 0.06)
    return VGroup(r, rings, ls)


def star(r=0.45):
    return Star(5, outer_radius=r, inner_radius=r * 0.45).set_stroke(C2C, 3).set_fill(dim(C2C, 0.5), 1)


def tally(n=7, color=GREY_A, h=0.42):
    g = VGroup()
    x = 0
    for i in range(n):
        if i % 5 == 4:
            g.add(Line([x - 0.55, -h / 2 + 0.05, 0], [x - 0.05, h / 2 - 0.05, 0], stroke_width=3, color=color))
            x += 0.18
        else:
            g.add(Line([x, -h / 2, 0], [x, h / 2, 0], stroke_width=3, color=color))
            x += 0.13
    return g.center()


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def panel(m, color=GREY_D, buff=0.3):
    return SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = T(right, size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


PAR, WRI, LINE_C, BOARD = TEAL_M, GOLD_M, BLUE_M, "#8B5A2B"


def board(w=2.4, h=0.9):
    return RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke("#C08A55", 3).set_fill(dim("#C08A55", 0.35), 1)


def veg(color, r=0.16):
    return Circle(radius=r).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)


def knife():
    blade = Polygon([0, 0, 0], [0.75, 0, 0], [0.75, 0.16, 0], [0.1, 0.13, 0]).set_stroke(GREY_A, 2).set_fill(GREY_C, 1)
    handle = Rectangle(width=0.4, height=0.16).set_stroke("#C08A55", 2).set_fill(dim("#C08A55", 0.6), 1).next_to(blade, LEFT, buff=0)
    return VGroup(blade, handle)


def cline(slots, w=0.78, h=0.62, color=LINE_C, size=20):
    """A 64-byte cache line: 8 slots of 8 bytes. slots: list of (label, colour) or None."""
    g = VGroup()
    for lab in slots:
        sq = Rectangle(width=w, height=h).set_stroke(color, 2)
        if lab:
            sq.set_fill(dim(lab[1], 0.45), 1).set_stroke(lab[1], 2.5)
        else:
            sq.set_fill("#101010", 1)
        cell = VGroup(sq)
        if lab and lab[0] and size:
            cell.add(T(lab[0], size, WHITE).move_to(sq))
        g.add(cell)
    g.arrange(RIGHT, buff=0)
    return g


ADJ = [("hdr", GREY_C), ("hdr", GREY_C), ("parsed", PAR), ("written", WRI), None, None, None, None]


class Perf04FalseSharing(Narrated):
    """perf-04, section 1: two cooks share one cutting board; the shy question (threads that never touch the same
    field slow each other down?); caches and 64-byte lines; coherence (one valid copy to write); JOL's layout
    (parsed at 16, written at 24, 32 bytes); the map; the trace; false sharing named; predict, then the quiet day
    (about five times) and the busy day (a small gap, sometimes reversed); why: the threads rarely ran at once;
    counts always exact; where the picture breaks; the cure: a chain of classes (written at 88); Java and Kotlin;
    guardrails, the rule, the moral and a check."""

    def construct(self):
        self.title_card("Two fields, one cache line", "false sharing")

        # ================= two cooks, one board =================
        bd = board(3.2, 1.2).move_to([0, -0.6, 0])
        ca = cook(1.7).move_to([-3.0, -0.2, 0])
        cb = cook(1.7).move_to([3.0, -0.2, 0])
        ons = VGroup(*[veg(PURPLE_M) for _ in range(3)]).arrange(RIGHT, buff=0.08).move_to(bd.get_center() + LEFT * 0.8)
        pep = VGroup(*[veg(RED_M) for _ in range(3)]).arrange(RIGHT, buff=0.08).move_to(bd.get_center() + RIGHT * 0.8)
        kn = knife().move_to(bd.get_center() + UP * 0.05)
        la = T("onions", 24, PURPLE_M).next_to(ca, DOWN, buff=0.2)
        lb = T("peppers", 24, RED_M).next_to(cb, DOWN, buff=0.2)
        one = T("one board, one knife at a time", 26, GREY_A).move_to([0, -2.6, 0])
        self.say("open")
        self.play(FadeIn(bd), FadeIn(ca), FadeIn(cb), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ons), FadeIn(la), run_time=0.5)
        self.at(2)
        self.play(FadeIn(pep), FadeIn(lb), run_time=0.5)
        self.at(4)
        self.play(FadeIn(kn), FadeIn(one), run_time=0.5)
        for k in range(2):
            self.play(cb.animate.shift(RIGHT * 0.6), kn.animate.move_to(bd.get_center() + LEFT * 0.6 + UP * 0.05), run_time=0.5)
            self.play(cb.animate.shift(LEFT * 0.6), ca.animate.shift(LEFT * 0.6), kn.animate.move_to(bd.get_center() + RIGHT * 0.6 + UP * 0.05), run_time=0.5)
            self.play(ca.animate.shift(RIGHT * 0.6), run_time=0.3)
        self.hold()

        q1 = T("My two threads never touch the same field. No shared data, no locks.", 28)
        q2 = T("So how could they slow each other down?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).move_to([0, 2.9, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q1, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.0)
        self.wipe()

        # ================= caches and lines =================
        def core(name, color):
            r = RoundedRectangle(corner_radius=0.12, width=2.6, height=1.0).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
            return VGroup(r, T(name, 26, color).move_to(r))
        c1 = core("core 1", PAR).move_to([-4.6, 2.2, 0])
        c2 = core("core 2", WRI).move_to([-4.6, -1.6, 0])
        k1 = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.9).set_stroke(GREY_B, 2).set_fill("#121212", 1).next_to(c1, DOWN, buff=0.15)
        k2 = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.9).set_stroke(GREY_B, 2).set_fill("#121212", 1).next_to(c2, DOWN, buff=0.15)
        k1t = T("its cache", 22, GREY_A).move_to(k1)
        k2t = T("its cache", 22, GREY_A).move_to(k2)
        mem = RoundedRectangle(corner_radius=0.14, width=2.6, height=4.6).set_stroke(GREY_C, 2.5).set_fill("#0e0e0e", 1).move_to([5.0, 0.2, 0])
        mem_t = VGroup(T("main", 26, GREY_A), T("memory", 26, GREY_A)).arrange(DOWN, buff=0.08).move_to(mem)
        far = DoubleArrow([-2.9, 0.3, 0], [3.4, 0.3, 0], buff=0, stroke_width=3, color=GREY_D, tip_length=0.2)
        far_t = T("far away, as computers go", 22, GREY_B).next_to(far, UP, buff=0.1)
        self.say("cache1")
        self.play(FadeIn(mem), FadeIn(mem_t), run_time=0.6)
        self.at(1)
        self.play(GrowFromCenter(far), FadeIn(far_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(c1), FadeIn(c2), run_time=0.6)
        self.play(FadeIn(k1), FadeIn(k1t), FadeIn(k2), FadeIn(k2t), run_time=0.6)
        self.hold()

        ln = cline([None] * 8).move_to([0.4, -1.9, 0])
        ln_t = T("one cache line: 64 bytes, 8 slots of 8 bytes", 22, LINE_C).next_to(ln, DOWN, buff=0.15)
        bd2 = board(1.6, 0.6).next_to(ln, UP, buff=0.35)
        bd2_t = T("= the board", 22, "#C08A55").next_to(bd2, RIGHT, buff=0.2)
        self.say("cache2")
        self.play(FadeOut(far), FadeOut(far_t), run_time=0.3)
        self.at(1)
        self.play(FadeIn(ln), FadeIn(ln_t), run_time=0.7)
        self.at(2)
        mv = ln.copy()
        self.play(mv.animate.move_to(mem.get_center() + DOWN * 1.4).scale(0.4), run_time=0.8)
        self.play(mv.animate.move_to(k1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(bd2), FadeIn(bd2_t), run_time=0.6)
        self.hold()

        mv2 = mv.copy().move_to(k2)
        k1t.set_opacity(0)
        k2t.set_opacity(0)
        wr = T("writes", 24, PAR).next_to(c1, RIGHT, buff=0.3)
        inv = T("invalid", 24, RED_M).next_to(k2, RIGHT, buff=0.3)
        self.say("coh")
        self.play(FadeIn(mv2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wr), Indicate(mv, color=PAR), run_time=0.8)
        self.at(2)
        self.play(mv2.animate.set_opacity(0.25), FadeIn(inv), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the stats object, from JOL =================
        objc = VGroup(T("volatile long parsed;", 26, PAR), T("volatile long written;", 26, WRI)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        thr = VGroup(T("parser thread writes", 22, PAR), T("writer thread writes", 22, WRI)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        objc.move_to([-2.3, 2.6, 0])
        thr.next_to(objc, RIGHT, buff=0.8)
        big = cline(ADJ, w=1.35, h=0.95, size=24).move_to([0, 0.1, 0])
        offs = VGroup(*[T(str(8 * i), 22, GREY_B).move_to(big[0].get_corner(DL) + RIGHT * 1.35 * i + DOWN * 0.3) for i in range(9)])
        objbr = BraceBetweenPoints(big[3].get_corner(DR), big[0].get_corner(DL), direction=DOWN, color=GREY_B).shift(DOWN * 0.6)
        obj_t = T("the object: 32 bytes", 22, GREY_A).next_to(objbr, DOWN, buff=0.1)
        hdr_t = T("header 12 bytes + 4 gap", 20, GREY_B).next_to(big[0:2], UP, buff=0.15)
        line_t = T("one 64-byte line", 22, LINE_C).next_to(big, UP, buff=0.15).align_to(big, RIGHT)
        apart = T("8 bytes apart: same board", 28, YELLOW_M).move_to([0, -2.9, 0])
        self.say("obj")
        self.play(FadeIn(objc[0]), FadeIn(thr[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(objc[1]), FadeIn(thr[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(big), FadeIn(offs), FadeIn(line_t), run_time=0.8)
        self.at_text("parsed at", lead=0.2)
        self.play(Indicate(big[2], color=PAR), FadeIn(hdr_t), run_time=0.7)
        self.at_text("written at", lead=0.2)
        self.play(Indicate(big[3], color=WRI), run_time=0.6)
        self.play(GrowFromCenter(objbr), FadeIn(obj_t), run_time=0.6)
        self.at(5)
        self.play(FadeIn(apart), run_time=0.5)
        self.hold()
        self.wipe()

        rows = [maprow("the two cooks", "the two threads", GREY_A, GREY_A),
                maprow("their vegetables", "the two fields", PURPLE_M, WRI),
                maprow("the board", "the cache line: 64 bytes", "#C08A55", LINE_C),
                maprow("stepping back for the knife", "a core waiting for the line", GREY_A, RED_M)]
        tbl = maptable(rows, x_arrow=-0.3, y0=1.6, dy=0.9)
        fit(tbl, 12.6)
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(rows[i]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the trace =================
        cc1 = core("core 1: parsed++", PAR).move_to([-3.6, 2.4, 0])
        cc2 = core("core 2: written++", WRI).move_to([3.6, 2.4, 0])
        for c in (cc1, cc2):
            c[0].stretch_to_fit_width(3.6)
        l1 = cline(ADJ[:4] + [None] * 4, w=0.55, h=0.5, size=0).move_to([-3.6, 0.9, 0])
        l2 = l1.copy().move_to([3.6, 0.9, 0])
        l2.set_opacity(0.25)
        st1 = T("valid", 22, GREEN_M).next_to(l1, DOWN, buff=0.15)
        st2 = T("invalid", 22, RED_M).next_to(l2, DOWN, buff=0.15)
        self.say("trace")
        self.play(FadeIn(cc1), FadeIn(cc2), FadeIn(l1), FadeIn(l2), FadeIn(st1), FadeIn(st2), run_time=0.8)
        self.at(1)
        self.play(Indicate(l1[2], color=PAR), run_time=0.6)
        self.at(2)
        self.play(Indicate(cc2, color=WRI), run_time=0.6)
        self.at(3)
        trav = l1.copy().set_opacity(1)
        self.play(trav.animate.move_to(l2), l1.animate.set_opacity(0.25), run_time=1.0)
        self.play(FadeOut(trav), l2.animate.set_opacity(1), st1.animate.become(T("invalid", 22, RED_M).move_to(st1)),
                  st2.animate.become(T("valid", 22, GREEN_M).move_to(st2)), run_time=0.4)
        self.at(4)
        trav = l2.copy()
        self.play(trav.animate.move_to(l1), l2.animate.set_opacity(0.25), run_time=1.0)
        self.play(FadeOut(trav), l1.animate.set_opacity(1), st1.animate.become(T("valid", 22, GREEN_M).move_to(st1)),
                  st2.animate.become(T("invalid", 22, RED_M).move_to(st2)), run_time=0.4)
        self.hold()

        bounce = VGroup(Arrow([-1.4, 0.95, 0], [1.4, 0.95, 0], buff=0, stroke_width=3, color=RED_M),
                        Arrow([1.4, 0.65, 0], [-1.4, 0.65, 0], buff=0, stroke_width=3, color=RED_M))
        work = T("a few nanoseconds of work, wrapped in a wait", 26, GREY_A).move_to([0, -0.9, 0])
        fs = T("false sharing", 40, YELLOW_M).move_to([0, -2.1, 0])
        fs2 = T("the program shares nothing; the hardware shares a lot", 24, GREY_B).next_to(fs, DOWN, buff=0.18)
        self.say("name")
        self.play(FadeIn(bounce), FadeIn(work), run_time=0.7)
        self.at(1)
        self.play(FadeIn(fs2), run_time=0.6)
        self.at(3)
        self.play(FadeIn(fs, scale=0.8), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= predict, then the runs =================
        hd = VGroup(M("FalseSharingDemo", 24, GREY_A), T("2 threads x 25 million increments", 24, GREY_A)).arrange(RIGHT, buff=0.4)
        hd.move_to([0, 3.1, 0])
        q = VGroup(T("adjacent", 26, RED_M), T("vs", 24, GREY_B), T("padded apart", 26, GREEN_M), T(": how much faster?", 26)).arrange(RIGHT, buff=0.2)
        q.move_to([0, 2.3, 0])
        self.say("pq")
        self.play(FadeIn(hd), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.5))

        X0, K = -2.6, 8.4 / 1400
        def rbar(v0, v1, y, color, h=0.42):
            r = Rectangle(width=max(0.05, v1 * K), height=h).set_stroke(color, 2).set_fill(dim(color, 0.55), 1)
            r.move_to([X0, y, 0], aligned_edge=LEFT)
            return r
        qd = T("a quiet day", 26, GREY_A).move_to([-5.1, 1.2, 0])
        qa = rbar(0, 1387, 1.45, RED_M)
        qa_lo = Line([X0 + 957 * K, 1.2, 0], [X0 + 957 * K, 1.7, 0], stroke_width=3, color=WHITE)
        qa_t = T("adjacent 957 to 1,387 ms", 22, RED_M).next_to(qa, RIGHT, buff=0.15)
        qp = rbar(0, 247, 0.9, GREEN_M)
        qp_t = T("padded 206 to 247 ms", 22, GREEN_M).next_to(qp, RIGHT, buff=0.15)
        five = T("about 5 times faster", 26, YELLOW_M).move_to([3.2, 0.3, 0])
        fit(qa_t, 3.0)
        self.say("quiet")
        self.play(FadeIn(qd), GrowFromEdge(qa, LEFT), Create(qa_lo), FadeIn(qa_t), run_time=0.9)
        self.at_text("Padded took", lead=0.2)
        self.play(GrowFromEdge(qp, LEFT), FadeIn(qp_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(five), run_time=0.5)
        self.hold()

        bd_t = T("a busy day", 26, GREY_A).move_to([-5.1, -1.1, 0])
        busy = [(994, 785), (977, 784), (1124, 806)]
        bars = VGroup()
        for i, (a, p) in enumerate(busy):
            y = -0.5 - i * 0.75
            ba = rbar(0, a, y, RED_M, 0.28)
            bp = rbar(0, p, y - 0.3, GREEN_M, 0.28)
            ta = T(f"{a:,}", 20, RED_M).next_to(ba, RIGHT, buff=0.1)
            tp = T(f"{p:,}", 20, GREEN_M).next_to(bp, RIGHT, buff=0.1)
            bars.add(VGroup(ba, bp, ta, tp))
        lost = T("across nine runs, padded lost one round in three", 22, GREY_B).move_to([2.2, -2.9, 0])
        small = T("a small gap", 26, YELLOW_M).move_to([3.6, -1.1, 0])
        self.say("busy")
        self.play(FadeIn(bd_t), run_time=0.4)
        self.at_text("994", lead=0.2)
        self.play(FadeIn(bars[0]), run_time=0.5)
        self.at_text("977", lead=0.2)
        self.play(FadeIn(bars[1]), FadeIn(bars[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(small), run_time=0.4)
        self.at(3)
        self.play(FadeIn(lost), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= why the busy day hid it =================
        tl_y = [1.3, -0.3]
        tl_c = [PAR, WRI]
        tl = VGroup()
        for y, c, lab in zip(tl_y, tl_c, ["parser thread", "writer thread"]):
            tl.add(T(lab, 24, c).move_to([-5.0, y, 0]))
            tl.add(Line([-3.6, y, 0], [5.8, y, 0], stroke_width=1.5, color=GREY_D))
        runs_a = [(-3.5, -2.4), (-0.9, 0.1), (2.2, 3.0), (4.6, 5.4)]
        runs_b = [(-2.3, -1.0), (0.2, 1.3), (3.0, 4.4)]
        ra = VGroup(*[Rectangle(width=b - a, height=0.45).set_stroke(PAR, 2).set_fill(dim(PAR, 0.5), 1).move_to([(a + b) / 2, tl_y[0], 0]) for a, b in runs_a])
        rb = VGroup(*[Rectangle(width=b - a, height=0.45).set_stroke(WRI, 2).set_fill(dim(WRI, 0.5), 1).move_to([(a + b) / 2, tl_y[1], 0]) for a, b in runs_b])
        tt = T("time on a core", 20, GREY_B).move_to([5.0, 2.0, 0])
        why_t = T("more than 20 busy programs, 4 cores", 26, GREY_A).move_to([0, 2.8, 0])
        rule2 = T("a line only bounces between cores that both want it right now", 26, YELLOW_M).move_to([0, -1.6, 0])
        fit(rule2, 12.4)
        shifts = T("different shifts", 28, GREY_A).move_to([0, -2.5, 0])
        self.say("why")
        self.play(FadeIn(why_t), FadeIn(tl), FadeIn(tt), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(r) for r in ra], lag_ratio=0.2), LaggedStart(*[FadeIn(r) for r in rb], lag_ratio=0.2), run_time=1.4)
        self.at(3)
        self.play(FadeIn(rule2), run_time=0.6)
        self.at(4)
        self.play(FadeIn(shifts), run_time=0.5)
        self.hold()
        self.wipe()

        cnt = VGroup(T("every count:", 30, GREY_A), M("25,000,000", 34, GREEN_M)).arrange(RIGHT, buff=0.3).move_to([0, 1.2, 0])
        tm = VGroup(T("costs time,", 34, RED_M), T("never correctness", 34, GREEN_M)).arrange(RIGHT, buff=0.3).move_to([0, 0.0, 0])
        self.say("count")
        self.at(1)
        self.play(FadeIn(cnt), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tm), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        ckb = cook(1.4).move_to([-4.0, 0.8, 0])
        ckb_t = VGroup(T("a cook waits seconds,", 26, GREY_A), T("and notices", 26, GREY_A)).arrange(DOWN, buff=0.08).next_to(ckb, DOWN, buff=0.3)
        dv = DashedLine([-0.8, 2.6, 0], [-0.8, -2.4, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        crb = core("a core", PAR).move_to([3.0, 1.2, 0])
        crb_t = VGroup(T("waits nanoseconds,", 26, GREY_A), T("nobody notices...", 26, GREY_A)).arrange(DOWN, buff=0.08).next_to(crb, DOWN, buff=0.3)
        times = T("...until it happens a few hundred million times", 24, YELLOW_M).move_to([2.6, -1.4, 0])
        fit(times, 6.6)
        meas = T("measure, don't guess", 30, YELLOW_M).move_to([0, -3.0, 0])
        self.say("breaks")
        self.play(FadeIn(ckb), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ckb_t), run_time=0.5)
        self.at(2)
        self.play(Create(dv), FadeIn(crb), FadeIn(crb_t), run_time=0.7)
        self.at_text("until it", lead=0.2)
        self.play(FadeIn(times), run_time=0.5)
        self.at(3)
        self.play(FadeIn(meas), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the cure: space =================
        la_ = cline([("hdr", GREY_C), ("hdr", GREY_C), ("parsed", PAR)] + [("pad", GREY_D)] * 5, w=1.25, h=0.8, size=22)
        lb_ = cline([("pad", GREY_D)] * 3 + [("written", WRI)] + [("pad", GREY_D)] * 4, w=1.25, h=0.8, size=22)
        VGroup(la_, lb_).arrange(DOWN, buff=0.9).move_to([0, 0.3, 0])
        la_t = T("line A", 22, LINE_C).next_to(la_, LEFT, buff=0.2)
        lb_t = T("line B", 22, LINE_C).next_to(lb_, LEFT, buff=0.2)
        o16 = T("offset 16", 22, PAR).next_to(la_[2], UP, buff=0.12)
        o88 = T("offset 88", 22, WRI).next_to(lb_[3], DOWN, buff=0.12)
        two = VGroup(board(1.1, 0.45), board(1.1, 0.45)).arrange(RIGHT, buff=0.3).move_to([0, 2.8, 0])
        two_t = T("a board each", 24, "#C08A55").next_to(two, RIGHT, buff=0.3)
        chain = T("a chain of classes: superclass fields come first", 24, GREY_A).move_to([0, -2.6, 0])
        note = T("LayoutDemo's padded chain, JDK 21 and JDK 25: 72 bytes apart", 20, GREY_B).move_to([0, -3.3, 0])
        self.say("fix")
        self.play(FadeIn(two), FadeIn(two_t), run_time=0.6)
        self.at(2)
        self.play(FadeIn(chain), run_time=0.5)
        self.at(3)
        self.play(FadeIn(la_), FadeIn(lb_), FadeIn(la_t), FadeIn(lb_t), run_time=0.8)
        self.play(FadeIn(o16), FadeIn(o88), FadeIn(note), run_time=0.6)
        self.hold()
        self.wipe()

        jv = code_block(["abstract class ParsedCounter { volatile long parsed; }",
                         "abstract class PadAfterParsed extends ParsedCounter {",
                         "    long p1, p2, p3, p4, p5, p6, p7, p8; }",
                         "abstract class WrittenCounter extends PadAfterParsed {",
                         "    volatile long written; }"], 24, hl={"parsed;": PAR, "written;": WRI})
        kt = code_block(["abstract class ParsedCounter { @Volatile @JvmField var parsed = 0L }",
                         "abstract class PadAfterParsed : ParsedCounter() {",
                         "    @JvmField var p1 = 0L; @JvmField var p2 = 0L   // ... to p8",
                         "}",
                         "abstract class WrittenCounter : PadAfterParsed() {",
                         "    @Volatile @JvmField var written = 0L }"], 24, hl={"parsed": PAR, "written": WRI})
        jc = VGroup(T("Java", 22, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        kc = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(jc), FadeIn(kc), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(VGroup(jv[1], jv[2]), color=GREY_B, buff=0.05), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(kt[0][0:8], kt[1][0:8], kt[4][0:8]), color=YELLOW_M), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= guardrails, rule, moral, check =================
        gs = VGroup(T("1.  Padding costs memory: 160 bytes instead of 32, on every object.", 28),
                    T("2.  Pad only fields that different threads write in a hot loop.", 28),
                    T("3.  Don't promise a speed-up: measure where you really run.", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        fit(gs, 12.2).move_to([0, 1.3, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gs[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(gs[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(gs[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        r1 = T("Separate fields aren't separate memory.", 34)
        r2 = T("Fields that different threads write in a hot loop", 30, YELLOW_M)
        r3 = T("need lines of their own.", 30, YELLOW_M)
        rg = VGroup(r1, r2, r3).arrange(DOWN, buff=0.22).move_to([0, -1.9, 0])
        fit(rg, 12.4)
        self.say("rule")
        self.play(FadeIn(r1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2), FadeIn(r3), run_time=0.6)
        self.hold()
        self.wipe()

        bd3 = board(2.6, 1.0).move_to([0, 1.6, 0])
        cka = cook(1.2).next_to(bd3, LEFT, buff=0.5)
        ckb2 = cook(1.2).next_to(bd3, RIGHT, buff=0.5)
        mm = VGroup(T("Memory moves in 64-byte boards, not in fields.", 30),
                    T("Two cooks who never share a vegetable can still wait all day for the board.", 26, GREY_A)).arrange(DOWN, buff=0.2)
        mm.move_to([0, -0.1, 0])
        fit(mm, 12.4)
        self.say("moral")
        self.play(FadeIn(bd3), FadeIn(cka), FadeIn(ckb2), run_time=0.6)
        self.at(0)
        self.play(FadeIn(mm[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mm[1]), run_time=0.6)
        self.hold()
        qa = VGroup(T("Check:", 28, YELLOW_M), T("long[] slots, one per worker thread, each adds to its own slot.", 28)).arrange(RIGHT, buff=0.25)
        qb = T("Can they slow each other down?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to([0, -1.8, 0])
        fit(qg2, 12.4)
        self.say("chk")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.5))
        ans = T("Yes: slots 8 bytes apart share a line. For counters: LongAdder.", 28, C1C).move_to([0, -3.1, 0])
        fit(ans, 12.4)
        self.say("chka")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
