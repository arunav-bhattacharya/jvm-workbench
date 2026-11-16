from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"-Xint\b", "dash X int"), (r"\bx86\b", "x eighty-six"), (r"\bARM\b", "arm"),
    (r"\bThread A\b", "Thread eigh"), (r"@Volatile", "at Volatile"), (r"\bspins\+\+", "spins plus plus"),
]

# every spoken line, in order
N = {
    "open": "Picture an office. When it's time to go home, the manager writes it on the whiteboard by the door. "
            "Everyone glances at the board now and then, and leaves when it says yes.",
    "program": "A program can do the same. A worker thread, one path of work running beside others, loops through small jobs. "
               "Before each one, it checks a shared field called stop. One second in, the main thread sets stop to true.",
    "output": "Here's what the demo printed on JDK 25. Main set stop to true. Three seconds later, is the worker still running? "
              "True. It never stops. No crash, no error, just a busy processor doing laps.",
    "shy": "So here's a question that feels almost too simple to ask. Main wrote true. "
           "So where is the worker reading false from? Where does the old value live?",
    "usual": "Most people answer: the cache. A core is the part of the processor that runs one thread at a time. "
             "Next to each core sits a cache, a small, fast memory that keeps copies of recent data. "
             "Main memory is about a hundred times slower.",
    "usual2": "So the story goes like this. The worker's core has an old copy of stop in its cache, and reads that copy forever. "
              "It sounds right. Let's test it.",
    "xint_q": "Java has a switch, -Xint, that turns off the JIT compiler, the part of Java that turns busy code into fast "
              "machine code while the program runs. The caches don't change at all. "
              "So if the cache is to blame, the worker should still hang. Will it?",
    "xint_a": "It stopped at once, after about 113 million laps. Same machine, same caches, and only the JIT changed. "
              "So the cache has an alibi. It was there in both runs, and only one run hung.",
    "office": "To find the real place, let's go back to the office and look at the desks. "
              "The whiteboard holds the numbers everyone shares. That's main memory. "
              "Each desk is a core, and the one working at it is a thread.",
    "copy": "Walking to the wall is slow, so each desk keeps a photocopy of the part of the board it uses. "
            "That photocopy is the cache.",
    "rule": "And the office has one strict rule. When anyone changes a number on the board, "
            "every photocopy of it is crossed out at once. The next look goes back to the board.",
    "coh": "Processors follow that rule in hardware. It's called cache coherence, and it works within nanoseconds, "
           "billionths of a second. So a photocopy can't stay wrong.",
    "tray": "But there is one place where a write can wait. Each desk has an outbox tray. "
            "When a clerk has a new number for the board, she drops a note in her tray and goes on with her next task. "
            "A runner carries it to the board a moment later.",
    "sb": "That tray is called a store buffer: a small queue inside each core where writes wait on their way to the cache, "
          "so the core never stands around.",
    "swap": "Notice the catch. If her next task is to read a different number, she may read it before her own note arrives. "
            "To everyone else, her write and her read look swapped.",
    "test": "Let's catch that with the smallest test there is. Two fields, x and y, both start at 0. "
            "Thread A writes 1 into x, then reads y. Thread B writes 1 into y, then reads x.",
    "hand": "Play it by hand first. Shuffle the four steps any way you like, but keep each thread's two steps in order, "
            "like shuffling two decks of cards together. Whoever reads second reads after the other's write. "
            "So at least one thread sees a 1. Both reading 0 should be impossible.",
    "count_q": "The demo runs this test 524,288 times. In how many trials do both threads read 0?",
    "count_a": "Run one: 240,989. Run two: 225,261. Run three: 171,281. "
               "That's a third to nearly half of all trials. For something impossible, it happens a lot.",
    "why": "Here's how. Thread A drops its note for x in its tray, and Thread B drops its note for y in its tray. "
           "Then each one reads the other field from its photocopy. Zero, and zero. "
           "Only then do the runners reach the board.",
    "xint2": "Turn the JIT off again, and the count drops, but stays well above zero: 44,000 to 110,000 in our runs. "
             "The interpreter doesn't reorder anything. So this time, it really is the hardware.",
    "vol1": "Now make both fields volatile, a keyword that marks a field as shared between threads. "
            "The count is 0, every time. On x86 chips, the kind in most laptops, "
            "Java follows each volatile write with an instruction that empties the tray before any later read.",
    "tray_alibi": "So the tray can swap a write and a read. But it always delivers, within nanoseconds. "
                  "It can't hold stop for an hour. The outbox has an alibi too.",
    "notepad": "There's one more thing on each desk: a notepad. To work with a number, a clerk copies it onto her notepad, "
               "because a glance down is quicker than a walk to the wall. "
               "The notepad has no crossing-out rule, and nobody else can write on it.",
    "jit": "Now here's what the JIT did. Once the loop had run many thousands of times, it compiled it. "
           "It saw that nothing in the loop writes stop or talks to other threads. "
           "So it read stop once, before the loop, and turned the rest into while true.",
    "hoist_office": "In the office, it's as if the clerk copied the answer, no, onto her notepad once, "
                    "and from then on reads only the notepad.",
    "hang": "Main writes true. The note leaves the tray. The board says true. Both photocopies say true. "
            "And the worker keeps reading its notepad.",
    "register": "The notepad is a register, a tiny storage slot inside a core, the fastest place a value can live. "
                "That's where the old value lives.",
    "loyal": "It's the most focused worker in the building. It never looks up, so it never goes home. "
             "Jokes aside, the compiled loop never reads memory again, so no rule in the hardware can reach it.",
    "names": "So here's the office as it stands. The photocopy, the cache, agrees within nanoseconds. "
             "The outbox, the store buffer, holds a write for nanoseconds, then always delivers. "
             "The notepad, the register, can hold an old value forever, but only because the JIT chose it.",
    "breaks": "And here's where the office picture breaks. A clerk decides where to look, glance by glance. "
              "The JIT decides once, when it compiles the loop, and the core repeats that choice billions of times. "
              "That's why the hang lasts forever.",
    "chips": "One warning. Chips differ in how much they swap. x86 chips only let a later read pass an earlier write, "
             "like our test. ARM chips, in phones and many servers, also let reads pass reads, and writes pass writes.",
    "polite": "So code that never fails on your laptop can fail on a server. A clean run on your laptop only proves "
              "your laptop is polite. Write to Java's rules instead: the Java Memory Model. "
              "It promises visibility, one thread seeing another's write, only when something links the threads.",
    "fix": "For our flag, the link is one word: volatile. The JIT may not keep a volatile field on the notepad, "
           "so every pass reads it again. The photocopy says true, and the worker finally goes home. "
           "And Java promises that main's write becomes visible to the loop.",
    "code": "Here it is, Java on the left and Kotlin on the right. In Kotlin, the annotation @Volatile marks the field "
            "volatile, so the compiled code is the same.",
    "moral": "So, where does the old value live? Not in the cache: the photocopies agree within nanoseconds. "
             "Not in the outbox: it delivers within nanoseconds too. It lives on the notepad, a register, "
             "because the JIT chose to read stop once. volatile takes the notepad away.",
    "check": "Quick check. A loop hangs with the JIT on, and stops with the JIT off. Photocopy, outbox, or notepad?",
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

    def predict(self, secs=2.4):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.7, extra=()):
        """Small dots run from each source to each target at the same time (a read or a write)."""
        dots = [Dot(radius=0.09, color=color).move_to(a).set_z_index(8) for a, _ in pairs]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], *extra, run_time=rt)
        self.remove(*dots)

    def glide(self, paths, color, rt=0.7):
        """Dots that run along polylines (routed around boxes) at the same time."""
        dots, anims = [], []
        for pts in paths:
            pl = VMobject().set_points_as_corners([np.array(x, dtype=float) for x in pts])
            d = Dot(radius=0.09, color=color).move_to(pts[0]).set_z_index(8)
            dots.append(d)
            anims.append(MoveAlongPath(d, pl, rate_func=smooth))
        self.add(*dots)
        self.play(*anims, run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
WK, MN, OLD, NEWV, TRAY, COH, GOOD = BLUE_M, TEAL_M, RED_M, TEAL_M, GOLD_M, GOLD_M, GREEN_M

# the office layout
DX, DESK_Y, DESK_W, DESK_H = 3.35, 0.62, 6.0, 3.95
HEAD_Y, CODE_Y, NOTE_Y, OUT_Y, COPY_Y, BOARD_Y = 2.28, 1.8, 1.05, 0.15, -0.75, -2.42
CW = 5.3


def plain(c):
    return ManimColor(c).to_hex().upper() in (ManimColor(GREY_B).to_hex().upper(), ManimColor(WHITE).to_hex().upper())


class Cell(VGroup):
    """A box with a serif label and a monospace value, left aligned: 'photocopy (cache):  stop = false'."""

    def __init__(self, label, value, color=GREY_B, vcolor=WHITE, w=CW, h=0.66, center=False):
        r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5)
        r.set_fill(BLACK if plain(color) else dim(color), 1)
        super().__init__(r)
        self.center_text = center
        self.add(self._row(label, value, vcolor))
        self.label, self.value, self.vcolor = label, value, vcolor

    def _row(self, label, value, vcolor):
        lab = T(label + ":", 24, GREY_A)
        val = M(value, 22, vcolor)
        row = VGroup(lab, val).arrange(RIGHT, buff=0.22)
        row.move_to(self[0])
        if not self.center_text:
            row.align_to(self[0], LEFT).shift(RIGHT * 0.25)
        return row

    def set(self, label=None, value=None, vcolor=None, color=None):
        self.label = label if label is not None else self.label
        self.value = value if value is not None else self.value
        self.vcolor = vcolor if vcolor is not None else self.vcolor
        anims = [Transform(self[1], self._row(self.label, self.value, self.vcolor))]
        if color is not None:
            anims.append(self[0].animate.set_stroke(color).set_fill(BLACK if plain(color) else dim(color), 1))
        return anims


def strike(c):
    """A red line through a cell's value: the photocopy is crossed out."""
    v = c[1][1]
    return Line(v.get_left() + LEFT * 0.12, v.get_right() + RIGHT * 0.12, stroke_width=5, color=OLD).set_z_index(6)


class Desk:
    def __init__(self, cx, color, title, code):
        self.cx, self.color = cx, color
        self.frame = RoundedRectangle(corner_radius=0.15, width=DESK_W, height=DESK_H, stroke_color=color, stroke_width=3)
        self.frame.move_to([cx, DESK_Y, 0])
        self.head = T(title, 26, color).move_to([cx, HEAD_Y, 0])
        self.code = M(code, 22, color).move_to([cx, CODE_Y, 0])
        self.note = Cell("notepad", "empty", vcolor=GREY_B).move_to([cx, NOTE_Y, 0])
        self.out = Cell("outbox", "empty", vcolor=GREY_B).move_to([cx, OUT_Y, 0])
        self.copy = Cell("photocopy", "stop = false").move_to([cx, COPY_Y, 0])

    def retitle(self, title, code):
        return [Transform(self.head, T(title, 26, self.color).move_to([self.cx, HEAD_Y, 0])),
                Transform(self.code, M(code, 22, self.color).move_to([self.cx, CODE_Y, 0]))]


def side(d, a, b):
    """A route from cell a up or down to cell b along the desk's right inner strip, so dots never cross a box."""
    x = d.cx + 2.83
    return [a.get_right(), [x, a.get_y(), 0], [x, b.get_y(), 0], b.get_right()]


def code_block(src, size=24, color=WHITE, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def card(text, color):
    r = RoundedRectangle(corner_radius=0.08, width=2.6, height=0.58, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, M(text, 24).move_to(r))


def figure(color=GREY_A):
    head = Circle(radius=0.17, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.18, width=0.55, height=0.6, stroke_color=color, stroke_width=3)
    body.next_to(head, DOWN, buff=0.05)
    return VGroup(head, body)


class Jmm01StopLoop(Narrated):
    """jmm-01, section 2: the office whiteboard; a stop flag the loop never sees. The cache story broken by -Xint;
    photocopies (caches) kept in agreement; the outbox tray (store buffer) and the x/y test; the notepad (register)
    the JIT reads from; x86 vs ARM; volatile."""

    def construct(self):
        self.title_card("Where does the old value live?", "a stop flag, the caches, the outbox and the notepad")

        # ================= the office, then the program =================
        wb = RoundedRectangle(corner_radius=0.1, width=6.4, height=2.2, stroke_color=GREY_A, stroke_width=4).move_to([0, 1.0, 0])
        ledge = Line([-2.6, -0.18, 0], [2.6, -0.18, 0], stroke_width=6, color=GREY_B)
        wb_lab = T("the whiteboard by the door", 24, GREY_B).next_to(wb, UP, buff=0.2)
        q1 = T("time to go home?", 40).move_to([-0.55, 1.0, 0])
        ans = T("no", 40, OLD).next_to(q1, RIGHT, buff=0.35)
        people = VGroup(*[figure() for _ in range(3)]).arrange(RIGHT, buff=1.6).move_to([0, -1.75, 0])
        looks = VGroup(*[DashedLine(p[0].get_top() + UP * 0.05, wb.get_bottom() + RIGHT * (p.get_x() * 0.4) + DOWN * 0.05,
                                    dash_length=0.08).set_stroke(GREY_C, 2) for p in people])
        self.say("open")
        self.play(Create(wb), FadeIn(wb_lab), FadeIn(ledge), run_time=1.0)
        self.play(Write(q1), FadeIn(ans), run_time=1.0)
        self.at(1)
        self.play(FadeIn(people, shift=UP * 0.2), run_time=0.6)
        self.play(Create(looks), run_time=0.6)
        self.at_text("leaves when", lead=0.1)
        self.play(Transform(ans, T("yes", 40, GOOD).next_to(q1, RIGHT, buff=0.35)), FadeOut(looks), run_time=0.6)
        self.play(people.animate.shift(RIGHT * 2.5).set_opacity(0), run_time=1.2, rate_func=rush_into)
        self.remove(people)
        self.hold()

        # the board becomes a shared field
        mem = Cell("shared field", "stop = false", w=5.4, h=0.8, center=True).move_to([0, 0.15, 0])
        wk = chip("worker thread", WK).move_to([-4.3, 2.55, 0])
        wk_c = M("while (!stop) spins++;", 22, WK).next_to(wk, DOWN, buff=0.25)
        mn = chip("main thread", MN).move_to([4.3, 2.55, 0])
        mn_c = M("stop = true;", 22, MN).next_to(mn, DOWN, buff=0.25)
        self.say("program")
        self.play(FadeOut(VGroup(wb, ledge, wb_lab, q1, ans)), FadeIn(mem), run_time=0.8)
        self.at(1)
        self.play(FadeIn(wk, shift=RIGHT * 0.2), FadeIn(wk_c), run_time=0.6)
        self.at(2)
        for _ in range(2):
            self.fly([(mem.get_top(), wk_c.get_bottom())], WK, rt=0.55)
        self.at(3)
        self.play(FadeIn(mn, shift=LEFT * 0.2), FadeIn(mn_c), run_time=0.6)
        self.fly([(mn_c.get_bottom(), mem.get_top())], MN, rt=0.6)
        self.play(*mem.set(value="stop = true", vcolor=NEWV), run_time=0.4)
        self.hold()

        term = RoundedRectangle(corner_radius=0.1, width=9.6, height=1.5, stroke_color=GREY_D, stroke_width=2).move_to([0, -2.0, 0])
        o1 = M("main set stop = true", 24, GREY_A)
        o2 = M("worker still running 3 s later? true", 24, t2c={"true": OLD})
        outp = VGroup(o1, o2).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(term)
        self.say("output")
        self.play(FadeIn(term), FadeIn(o1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(o2), run_time=0.6)
        self.at(3)
        self.play(Indicate(o2[-4:], color=OLD, scale_factor=1.2), run_time=0.8)
        self.at(4)
        for _ in range(3):
            self.fly([(mem.get_top() + LEFT * 2.0, wk_c.get_bottom())], WK, rt=0.4)
        self.hold()

        qa = T("main wrote true.", 40)
        qb = T("So where is the worker reading false from?", 40, YELLOW_M)
        qq = VGroup(qa, qb).arrange(DOWN, buff=0.35).move_to(UP * 0.3)
        fit(qq, 12.4)
        self.say("shy")
        self.play(FadeOut(VGroup(mem, wk, wk_c, mn, mn_c, term, outp)), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(qq), run_time=0.5)

        # ================= the usual story: a stale cache =================
        def core(cx, color, title, val, vcol):
            fr = RoundedRectangle(corner_radius=0.15, width=5.4, height=2.2, stroke_color=color, stroke_width=3).move_to([cx, 1.75, 0])
            hd = T(title, 26, color).move_to([cx, 2.48, 0])
            ca = Cell("cache", val, vcolor=vcol, w=4.6).move_to([cx, 1.75, 0])
            return fr, hd, ca
        f0, h0, ca0 = core(-3.3, WK, "core 0: the worker", "stop = false", WHITE)
        f1, h1, ca1 = core(3.3, MN, "core 1: main", "stop = true", NEWV)
        ram = Cell("main memory", "stop = true", vcolor=NEWV, w=12.0, h=0.62, center=True).move_to([0, 0.0, 0])
        w0 = Line(ca0.get_bottom(), [ca0.get_x(), ram.get_top()[1], 0], stroke_width=2, color=GREY_D).set_z_index(-1)
        w1 = Line(ca1.get_bottom(), [ca1.get_x(), ram.get_top()[1], 0], stroke_width=2, color=GREY_D).set_z_index(-1)
        slow = T("about a hundred times slower than a cache", 22, GREY_B).next_to(ram, DOWN, buff=0.18)
        self.say("usual")
        self.at(1)
        self.play(FadeIn(VGroup(f0, h0)), FadeIn(VGroup(f1, h1)), run_time=0.8)
        self.at(2)
        self.play(FadeIn(ca0), FadeIn(ca1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(ram), Create(w0), Create(w1), run_time=0.7)
        self.play(FadeIn(slow), run_time=0.4)
        self.hold()

        self.say("usual2")
        self.at(1)
        self.play(*ca0.set(vcolor=OLD, color=OLD), run_time=0.6)
        for _ in range(2):
            self.fly([(ca0.get_top(), h0.get_bottom())], WK, rt=0.45)
        self.hold()

        r_on = VGroup(T("JIT on:", 26, GREY_A), M("worker still running 3 s later? true", 24, t2c={"true": OLD}))
        r_off = VGroup(T("JIT off (-Xint):", 26, GREY_A), M("?", 26, GREY_B))
        for row, y in ((r_on, -1.45), (r_off, -2.3)):
            row.arrange(RIGHT, buff=0.35).move_to([-6.2, y, 0], aligned_edge=LEFT)
        res = M("worker saw stop after 113,153,939 spins", 24, GOOD).move_to(r_off[1], aligned_edge=LEFT)
        self.say("xint_q")
        self.play(FadeIn(r_on), run_time=0.6)
        self.play(FadeIn(r_off), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(ca0[1], ca1[1]), color=WHITE, scale_factor=1.06), run_time=0.9)
        self.hold(after=0)
        self.predict()

        alibi = chip("alibi", COH, size=24).move_to([ca0.get_right()[0] - 0.5, 1.02, 0])
        self.say("xint_a")
        self.play(Transform(r_off[1], res), run_time=0.7)
        self.at(1)
        self.play(Indicate(VGroup(ca0[1], ca1[1]), color=WHITE, scale_factor=1.06), run_time=0.8)
        self.at(2)
        self.play(*ca0.set(vcolor=WHITE, color=GREY_B), FadeIn(alibi, scale=1.3), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the office desks =================
        board = Cell("whiteboard", "stop = false", color=WHITE, w=12.7, h=0.8, center=True).move_to([0, BOARD_Y, 0])
        dw = Desk(-DX, WK, "the worker's desk", "while (!stop) spins++;")
        dm = Desk(DX, MN, "main's desk", "stop = true;")
        self.say("office")
        self.play(FadeIn(board), run_time=0.6)
        self.at(2)
        self.play(*board.set(label="whiteboard (main memory)"), run_time=0.6)
        self.at(3)
        self.play(FadeIn(VGroup(dw.frame, dw.head, dw.code)), FadeIn(VGroup(dm.frame, dm.head, dm.code)), run_time=0.8)
        self.play(*dw.retitle("the worker's desk (core 0)", "while (!stop) spins++;"),
                  *dm.retitle("main's desk (core 1)", "stop = true;"), run_time=0.6)
        self.hold()

        def wire(d):
            return Line(d.copy.get_bottom(), [d.cx, board.get_top()[1], 0], stroke_width=2, color=GREY_D).set_z_index(-1)
        wr0, wr1 = wire(dw), wire(dm)
        self.say("copy")
        self.play(FadeIn(dw.copy), FadeIn(dm.copy), Create(wr0), Create(wr1), run_time=0.8)
        self.fly([(board.get_top() + LEFT * DX, dw.copy.get_bottom()), (board.get_top() + RIGHT * DX, dm.copy.get_bottom())],
                 GREY_A, rt=0.6)
        self.at(1)
        self.play(*dw.copy.set(label="photocopy (cache)"), *dm.copy.set(label="photocopy (cache)"), run_time=0.6)
        self.hold()

        self.say("rule")
        self.at(1)
        self.glide([[dm.code.get_left(), [0, CODE_Y, 0], [0, board.get_top()[1], 0]]], MN, rt=0.9)
        self.play(*board.set(value="stop = true", vcolor=NEWV), run_time=0.4)
        s0, s1 = strike(dw.copy), strike(dm.copy)
        self.play(Create(s0), Create(s1), run_time=0.5)
        self.at(2)
        self.fly([(board.get_top() + LEFT * DX, dw.copy.get_bottom()), (board.get_top() + RIGHT * DX, dm.copy.get_bottom())],
                 GREY_A, rt=0.6)
        self.play(FadeOut(s0), FadeOut(s1), *dw.copy.set(value="stop = true", vcolor=NEWV),
                  *dm.copy.set(value="stop = true", vcolor=NEWV), run_time=0.5)
        self.hold()

        coh = T("cache coherence: every copy agrees within nanoseconds", 24, COH).move_to([0, -3.2, 0])
        self.say("coh")
        self.at_text("cache coherence", lead=0.3)
        self.play(FadeIn(coh, shift=UP * 0.1), wr0.animate.set_stroke(COH, 3), wr1.animate.set_stroke(COH, 3), run_time=0.7)
        self.hold()

        # ================= the outbox tray =================
        self.say("tray")
        self.play(FadeOut(coh), wr0.animate.set_stroke(GREY_D, 2), wr1.animate.set_stroke(GREY_D, 2),
                  *board.set(value="stop = false", vcolor=WHITE), *dw.copy.set(value="stop = false", vcolor=WHITE),
                  *dm.copy.set(value="stop = false", vcolor=WHITE), run_time=0.7)
        rewind = T("rewind", 22, GREY_B).move_to([0, -3.2, 0])
        self.play(FadeIn(rewind), run_time=0.3)
        self.at(1)
        self.play(FadeIn(dw.out), FadeIn(dm.out), FadeOut(rewind), run_time=0.6)
        self.at(2)
        note = chip("stop = true", MN, size=22, mono=True).move_to(dm.code).set_z_index(7)
        self.play(FadeIn(note), run_time=0.3)
        self.play(note.animate.move_to(dm.out.get_right() + LEFT * 1.0), run_time=0.7)
        self.play(FadeOut(note), *dm.out.set(value="stop = true", vcolor=NEWV, color=TRAY), run_time=0.4)
        nxt = T("next task...", 22, GREY_B).next_to(dm.code, RIGHT, buff=0.2)
        self.play(FadeIn(nxt, shift=RIGHT * 0.1), run_time=0.4)
        self.at(3)
        self.fly([(dm.out.get_bottom(), dm.copy.get_top())], TRAY, rt=0.4)
        self.play(*dm.out.set(value="empty", vcolor=GREY_B, color=GREY_B), *dm.copy.set(value="stop = true", vcolor=NEWV),
                  run_time=0.3)
        self.fly([(dm.copy.get_bottom(), board.get_top() + RIGHT * DX)], TRAY, rt=0.4)
        self.play(*board.set(value="stop = true", vcolor=NEWV), run_time=0.3)
        s0 = strike(dw.copy)
        self.play(Create(s0), run_time=0.3)
        self.fly([(board.get_top() + LEFT * DX, dw.copy.get_bottom())], GREY_A, rt=0.4)
        self.play(FadeOut(s0), *dw.copy.set(value="stop = true", vcolor=NEWV), run_time=0.3)
        self.hold()

        self.say("sb")
        self.play(*dw.out.set(label="outbox (store buffer)"), *dm.out.set(label="outbox (store buffer)"), run_time=0.7)
        self.hold()

        catch = T("her write waits in the tray, and her next read goes ahead", 24, TRAY).move_to([0, -3.2, 0])
        self.say("swap")
        self.at(1)
        self.play(Indicate(dm.out[1], color=TRAY, scale_factor=1.05), run_time=0.8)
        self.at(2)
        self.play(FadeIn(catch, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the smallest test =================
        self.say("test")
        self.play(FadeOut(catch), FadeOut(nxt), run_time=0.4)
        self.at(1)
        self.play(*board.set(value="x = 0, y = 0", vcolor=WHITE), *dw.copy.set(value="x = 0, y = 0", vcolor=WHITE),
                  *dm.copy.set(value="x = 0, y = 0", vcolor=WHITE), run_time=0.7)
        self.at(2)
        self.play(*dw.retitle("thread A's desk", "x = 1;   r1 = y;"), run_time=0.7)
        self.at(3)
        self.play(*dm.retitle("thread B's desk", "y = 1;   r2 = x;"), run_time=0.7)
        self.hold()

        desks = VGroup(board, dw.frame, dw.head, dw.code, dw.out, dw.copy, dm.frame, dm.head, dm.code, dm.out, dm.copy, wr0, wr1)
        self.play(FadeOut(desks), run_time=0.6)

        # shuffle two decks
        A1, A2, B1, B2 = card("A: x = 1", WK), card("A: r1 = y", WK), card("B: y = 1", MN), card("B: r2 = x", MN)
        for c, y in ((A1, 1.9), (A2, 1.25), (B1, 0.2), (B2, -0.45)):
            c.move_to([-5.15, y, 0])
        decks = VGroup(A1, A2, B1, B2)
        slots = [1.9, 1.25, 0.6, -0.05]
        self.say("hand")
        self.play(FadeIn(decks, shift=RIGHT * 0.2), run_time=0.6)
        self.at(1)
        p1 = [A1.copy(), B1.copy(), A2.copy(), B2.copy()]
        for c, y in zip(p1, slots):
            self.play(c.animate.move_to([-1.55, y, 0]), run_time=0.35)
        r11 = T("sees 1", 24, GOOD).next_to(p1[2], RIGHT, buff=0.2)
        r12 = T("sees 1", 24, GOOD).next_to(p1[3], RIGHT, buff=0.2)
        self.play(FadeIn(r11), FadeIn(r12), run_time=0.4)
        p2 = [A1.copy(), A2.copy(), B1.copy(), B2.copy()]
        for c, y in zip(p2, slots):
            self.play(c.animate.move_to([2.75, y, 0]), run_time=0.35)
        r21 = T("sees 0", 24, OLD).next_to(p2[1], RIGHT, buff=0.2)
        r22 = T("sees 1", 24, GOOD).next_to(p2[3], RIGHT, buff=0.2)
        self.play(FadeIn(r21), FadeIn(r22), run_time=0.4)
        self.at(2)
        self.play(Indicate(VGroup(p1[3], p2[3]), color=WHITE, scale_factor=1.05), run_time=0.8)
        least = T("every shuffle: at least one read sees 1", 30).move_to([0, -1.45, 0])
        imp = T("both read 0?  impossible", 32, YELLOW_M).move_to([0, -2.35, 0])
        self.at(3)
        self.play(FadeIn(least, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(imp, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(decks, *p1, *p2, r11, r12, r21, r22, least, imp)), run_time=0.6)

        # the counts
        ttl = T("both threads read 0, out of 524,288 trials", 32).move_to([0, 2.55, 0])

        def row(label, value, y, vc=OLD):
            l = T(label, 28, GREY_A).move_to([-5.6, y, 0], aligned_edge=LEFT)
            v = M(value, 28, vc).move_to([5.6, y, 0], aligned_edge=RIGHT)
            return VGroup(l, v)
        run1, run2, run3 = (row("plain fields, run 1", "240,989", 1.55), row("plain fields, run 2", "225,261", 0.9),
                            row("plain fields, run 3", "171,281", 0.25))
        q_mark = M("?", 32, GREY_B).move_to(run1[1], aligned_edge=RIGHT)
        self.say("count_q")
        self.play(FadeIn(ttl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(run1[0]), FadeIn(q_mark), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("count_a")
        self.play(FadeOut(q_mark), FadeIn(run1[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(run2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(run3), run_time=0.5)
        self.at(3)
        self.play(Indicate(VGroup(run1[1], run2[1], run3[1]), color=OLD, scale_factor=1.08), run_time=0.9)
        self.hold()
        table = VGroup(ttl, run1, run2, run3)
        self.play(FadeOut(table), run_time=0.5)

        # how: both notes sit in the trays while each thread reads
        self.play(FadeIn(desks), run_time=0.6)
        na = chip("x = 1", WK, size=22, mono=True).move_to(dw.code).set_z_index(7)
        nb = chip("y = 1", MN, size=22, mono=True).move_to(dm.code).set_z_index(7)
        ra = M("r1 = 0", 26, OLD).move_to([-DX, NOTE_Y, 0])
        rb = M("r2 = 0", 26, OLD).move_to([DX, NOTE_Y, 0])
        self.say("why")
        self.play(FadeIn(na), FadeIn(nb), run_time=0.3)
        self.play(na.animate.move_to(dw.out.get_right() + LEFT * 0.9), nb.animate.move_to(dm.out.get_right() + LEFT * 0.9),
                  run_time=0.8)
        self.play(FadeOut(na), FadeOut(nb), *dw.out.set(value="x = 1", vcolor=WK, color=TRAY),
                  *dm.out.set(value="y = 1", vcolor=MN, color=TRAY), run_time=0.4)
        self.at(1)
        self.glide([side(dw, dw.copy, ra), side(dm, dm.copy, rb)], GREY_A, rt=0.8)
        self.play(FadeIn(ra), FadeIn(rb), run_time=0.4)
        self.at(2)
        self.fly([(dw.out.get_bottom(), board.get_top() + LEFT * DX), (dm.out.get_bottom(), board.get_top() + RIGHT * DX)],
                 TRAY, rt=0.8)
        self.play(*dw.out.set(value="empty", vcolor=GREY_B, color=GREY_B), *dm.out.set(value="empty", vcolor=GREY_B, color=GREY_B),
                  *board.set(value="x = 1, y = 1", vcolor=NEWV), run_time=0.4)
        s0, s1 = strike(dw.copy), strike(dm.copy)
        self.play(Create(s0), Create(s1), run_time=0.3)
        self.play(FadeOut(s0), FadeOut(s1), *dw.copy.set(value="x = 1, y = 1", vcolor=NEWV),
                  *dm.copy.set(value="x = 1, y = 1", vcolor=NEWV), run_time=0.4)
        late = T("too late: both reads already said 0", 24, OLD).move_to([0, -3.2, 0])
        self.play(FadeIn(late), run_time=0.4)
        self.hold()
        self.play(FadeOut(desks), FadeOut(ra), FadeOut(rb), FadeOut(late), run_time=0.6)

        offr = row("plain fields, JIT off (-Xint)", "44,000 to 110,000", -0.75)
        volr = row("volatile fields", "0, every run", -1.4, GOOD)
        self.say("xint2")
        self.play(FadeIn(table), run_time=0.6)
        self.play(FadeIn(offr), run_time=0.6)
        self.hold()

        self.say("vol1")
        self.play(FadeIn(volr[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(volr[1]), run_time=0.5)
        self.hold()

        always = T("the tray always delivers, within nanoseconds", 28, TRAY).move_to([0, -2.45, 0])
        alibi2 = chip("alibi", COH, size=24).next_to(always, RIGHT, buff=0.35)
        self.say("tray_alibi")
        self.at(1)
        self.play(FadeIn(always, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(alibi2, scale=1.3), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(table, offr, volr, always, alibi2)), run_time=0.6)

        # ================= the notepad =================
        dw = Desk(-DX, WK, "the worker's desk (core 0)", "while (!stop) spins++;")
        dm = Desk(DX, MN, "main's desk (core 1)", "stop = true;")
        for d in (dw, dm):
            d.out = Cell("outbox (store buffer)", "empty", vcolor=GREY_B).move_to([d.cx, OUT_Y, 0])
            d.copy = Cell("photocopy (cache)", "stop = false").move_to([d.cx, COPY_Y, 0])
        board = Cell("whiteboard (main memory)", "stop = false", color=WHITE, w=12.7, h=0.8, center=True).move_to([0, BOARD_Y, 0])
        desks = VGroup(board, dw.frame, dw.head, dw.code, dw.out, dw.copy, dm.frame, dm.head, dm.code, dm.out, dm.copy, wr0, wr1)
        self.say("notepad")
        self.play(FadeIn(desks), run_time=0.7)
        self.play(FadeIn(dw.note), FadeIn(dm.note), run_time=0.6)
        self.at(1)
        self.glide([side(dw, dw.copy, dw.note)], GREY_A, rt=0.8)
        self.play(*dw.note.set(value="stop = false", vcolor=WHITE), run_time=0.4)
        self.at(2)
        self.play(Indicate(dw.note[1], color=WHITE, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(desks), FadeOut(dw.note), FadeOut(dm.note), run_time=0.6)

        left = VGroup(T("what you wrote", 24, GREY_B), code_block(["while (!stop) {", "    spins++;", "}"], 26))
        right = VGroup(T("what the compiled loop may do", 24, GREY_B),
                       code_block(["if (!stop) {", "    while (true) { spins++; }", "}"], 26, OLD))
        for g in (left, right):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        jit = VGroup(left, right).arrange(RIGHT, buff=1.7, aligned_edge=UP).move_to(UP * 1.0)
        fit(jit, 12.4)
        jarr = Arrow(left.get_right() + RIGHT * 0.05, right.get_left() + LEFT * 0.05, buff=0.1, color=GREY_B, stroke_width=3)
        jlab = T("the JIT", 24, GREY_B).next_to(jarr, UP, buff=0.1)
        why_ok = T("nothing in the loop writes stop or talks to other threads", 26, GREY_B).move_to(DOWN * 1.3)
        self.say("jit")
        self.play(FadeIn(left, shift=UP * 0.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(why_ok), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(jarr), FadeIn(jlab), FadeIn(right, shift=LEFT * 0.2), run_time=1.2)
        self.hold()
        self.play(FadeOut(VGroup(left, right, jarr, jlab, why_ok)), run_time=0.6)

        self.say("hoist_office")
        self.play(FadeIn(desks), FadeIn(dw.note), FadeIn(dm.note), run_time=0.7)
        self.play(*dw.note.set(vcolor=OLD, color=OLD), run_time=0.5)
        for _ in range(3):
            self.fly([(dw.note.get_top(), dw.code.get_bottom())], WK, rt=0.4)
        self.hold()

        self.say("hang")
        note = chip("stop = true", MN, size=22, mono=True).move_to(dm.code).set_z_index(7)
        self.play(FadeIn(note), run_time=0.25)
        self.play(note.animate.move_to(dm.out.get_right() + LEFT * 1.0), run_time=0.5)
        self.play(FadeOut(note), *dm.out.set(value="stop = true", vcolor=NEWV, color=TRAY), run_time=0.3)
        self.at(1)
        self.fly([(dm.out.get_bottom(), dm.copy.get_top())], TRAY, rt=0.35,
                 extra=[*dm.out.set(value="empty", vcolor=GREY_B, color=GREY_B)])
        self.play(*dm.copy.set(value="stop = true", vcolor=NEWV), run_time=0.25)
        self.fly([(dm.copy.get_bottom(), board.get_top() + RIGHT * DX)], TRAY, rt=0.35)
        self.play(*board.set(value="stop = true", vcolor=NEWV), run_time=0.3)
        self.at(3)
        s0 = strike(dw.copy)
        self.play(Create(s0), run_time=0.25)
        self.fly([(board.get_top() + LEFT * DX, dw.copy.get_bottom())], GREY_A, rt=0.35)
        self.play(FadeOut(s0), *dw.copy.set(value="stop = true", vcolor=NEWV), run_time=0.3)
        self.at(4)
        for _ in range(3):
            self.fly([(dw.note.get_top(), dw.code.get_bottom())], WK, rt=0.4)
        self.hold()

        self.say("register")
        self.play(*dw.note.set(label="notepad (register)"), *dm.note.set(label="notepad (register)"), run_time=0.7)
        self.at(1)
        self.play(Indicate(dw.note[1][1], color=OLD, scale_factor=1.15), run_time=0.9)
        self.hold()

        self.say("loyal")
        for _ in range(2):
            self.fly([(dw.note.get_top(), dw.code.get_bottom())], WK, rt=0.4)
        self.hold()

        # the office as it stands: the worker's desk with a verdict on each row
        mdesk = VGroup(dm.frame, dm.head, dm.code, dm.note, dm.out, dm.copy, wr1)
        newb = Cell("whiteboard (main memory)", "stop = true", color=WHITE, vcolor=NEWV, w=DESK_W, h=0.8, center=True)
        newb.move_to([-DX, BOARD_Y, 0])
        v_note = T("old forever: the JIT's choice", 26, OLD).move_to([0.6, NOTE_Y, 0], aligned_edge=LEFT)
        v_out = T("waits nanoseconds, then delivers", 26, TRAY).move_to([0.6, OUT_Y, 0], aligned_edge=LEFT)
        v_copy = T("agrees within nanoseconds", 26, GOOD).move_to([0.6, COPY_Y, 0], aligned_edge=LEFT)
        v_head = T("where a value can wait", 28, GREY_A).move_to([0.6, HEAD_Y, 0], aligned_edge=LEFT)
        self.say("names")
        self.play(FadeOut(mdesk), Transform(board, newb), run_time=0.7)
        self.play(FadeIn(v_head), run_time=0.4)
        self.at(1)
        self.play(FadeIn(v_copy, shift=LEFT * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(v_out, shift=LEFT * 0.2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(v_note, shift=LEFT * 0.2), run_time=0.5)
        self.hold()

        b1 = VGroup(T("a clerk decides where to look,", 26), T("glance by glance", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        b2 = VGroup(T("the JIT decides once, when it compiles;", 26, OLD),
                    T("the core repeats it billions of times", 26, OLD)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        b1.move_to([0.6, 1.0, 0], aligned_edge=LEFT)
        b2.move_to([0.6, -0.4, 0], aligned_edge=LEFT)
        bh = T("where the office picture breaks", 28, GREY_A).move_to([0.6, HEAD_Y, 0], aligned_edge=LEFT)
        self.say("breaks")
        self.play(FadeOut(VGroup(v_note, v_out, v_copy)), Transform(v_head, bh), run_time=0.6)
        self.at(1)
        self.play(FadeIn(b1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(b2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= guardrail: chips differ =================
        ch_t = T("Chips differ in how much they swap", 34).move_to([0, 2.55, 0])
        x86 = VGroup(mbox("x86", WHITE, w=1.6, size=26), T("most laptops and servers", 22, GREY_B))
        arm = VGroup(mbox("ARM", WHITE, w=1.6, size=26), T("phones, many servers", 22, GREY_B))
        for g in (x86, arm):
            g.arrange(DOWN, buff=0.15)
        x86.move_to([-5.0, 1.15, 0])
        arm.move_to([-5.0, -0.55, 0])
        x86_r = T("a later read may pass an earlier write", 28).move_to([-3.6, 1.3, 0], aligned_edge=LEFT)
        arm_r = VGroup(T("that, and also:", 28), T("reads pass reads, writes pass writes", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        arm_r.move_to([-3.6, -0.45, 0], aligned_edge=LEFT)
        self.say("chips")
        self.play(FadeIn(ch_t), run_time=0.6)
        self.at(1)
        self.play(FadeIn(x86), FadeIn(x86_r), run_time=0.7)
        self.at(3)
        self.play(FadeIn(arm), FadeIn(arm_r), run_time=0.7)
        self.hold()

        pol = T("Write to Java's rules, not to your chip.", 32, YELLOW_M).move_to([0, -2.1, 0])
        jmm = T("the Java Memory Model: visibility only when something links the threads", 24, GREY_B).move_to([0, -2.8, 0])
        fit(jmm, 12.4)
        self.say("polite")
        self.at(2)
        self.play(FadeIn(pol, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(jmm), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(ch_t, x86, arm, x86_r, arm_r, pol, jmm)), run_time=0.6)

        # ================= the fix =================
        fd = Desk(-DX, WK, "the worker's desk (core 0)", "while (!stop) spins++;")
        fd.note = Cell("notepad (register)", "stop = false", color=OLD, vcolor=OLD).move_to([-DX, NOTE_Y, 0])
        fd.out = Cell("outbox (store buffer)", "empty", vcolor=GREY_B).move_to([-DX, OUT_Y, 0])
        fd.copy = Cell("photocopy (cache)", "stop = true", vcolor=NEWV).move_to([-DX, COPY_Y, 0])
        fb = Cell("whiteboard (main memory)", "stop = true", color=WHITE, vcolor=NEWV, w=DESK_W, h=0.8, center=True)
        fb.move_to([-DX, BOARD_Y, 0])
        fw = Line(fd.copy.get_bottom(), [-DX, fb.get_top()[1], 0], stroke_width=2, color=GREY_D).set_z_index(-1)
        fdesk = VGroup(fd.frame, fd.head, fd.code, fd.note, fd.out, fd.copy, fb, fw)
        vt = T("volatile", 44, GOOD).move_to([3.3, 2.0, 0])
        v1 = T("no notepad for a volatile field", 26).move_to([3.3, 1.05, 0])
        v2 = T("every pass reads it again", 26).move_to([3.3, 0.4, 0])
        saw = M("worker saw stop", 28, GOOD).move_to([3.3, -0.8, 0])
        path = VMobject().set_points_as_corners([fd.copy.get_left() + LEFT * 0.05, [-DX - 2.83, COPY_Y, 0], [-DX - 2.83, CODE_Y, 0],
                                                 fd.code.get_left() + LEFT * 0.1]).set_stroke(GOOD, 3)
        self.say("fix")
        self.play(FadeIn(fdesk), FadeIn(vt), run_time=0.8)
        self.at(1)
        sn = strike(fd.note)
        self.play(Create(sn), FadeIn(v1), run_time=0.6)
        self.play(FadeOut(sn), *fd.note.set(value="not used", vcolor=GREY_B, color=GREY_B), run_time=0.4)
        self.play(Create(path), FadeIn(v2), run_time=0.7)
        self.at(2)
        for _ in range(2):
            dot = Dot(radius=0.09, color=GOOD).set_z_index(8)
            self.play(MoveAlongPath(dot, path.copy()), run_time=0.6)
            self.remove(dot)
        self.play(FadeIn(saw, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(fdesk, vt, v1, v2, saw, path)), run_time=0.6)

        hl = {"volatile": GOOD, "@Volatile": GOOD}
        jc = code_block(["static volatile boolean stop;", "", "while (!stop) {", "    spins++;", "}"], 26, hl=hl)
        kc = code_block(["@Volatile var stop = false", "", "while (!stop) {", "    spins++", "}"], 26, hl=hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.25),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
                      ).arrange(RIGHT, buff=1.3, aligned_edge=UP)
        fit(cols, 12.4).move_to(UP * 0.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=GOOD, scale_factor=1.04), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Where does the old value live?", 36, YELLOW_M).move_to(UP * 2.6)
        m1 = T("Not in the cache: the photocopies agree within nanoseconds.", 30)
        m2 = T("Not in the outbox: it delivers within nanoseconds too.", 30)
        m3 = T("On the notepad, a register, because the JIT read stop once.", 30, OLD)
        m4 = T("volatile takes the notepad away.", 30, GOOD)
        moral = VGroup(m1, m2, m3, m4).arrange(DOWN, buff=0.3).move_to(UP * 0.75)
        fit(moral, 12.4)
        cq = VGroup(T("Check: a loop hangs with the JIT on, and stops with the JIT off.", 28, YELLOW_M),
                    T("Photocopy, outbox, or notepad?", 28, YELLOW_M)).arrange(DOWN, buff=0.2).move_to(DOWN * 2.3)
        fit(cq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m4, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
