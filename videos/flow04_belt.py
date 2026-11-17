from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bflowOn\b", "flow on"),
    (r"\bbuffer\((\d+)\)", r"buffer \1"), (r"\bbuffer\(\)", "buffer"), (r"\bcollectLatest\b", "collect latest"),
    (r"\bonBufferOverflow\b", "on buffer overflow"), (r"\bDROP_OLDEST\b", "drop oldest"), (r"\bDROP_LATEST\b", "drop latest"),
    (r"\bSUSPEND\b", "suspend"), (r"\bonBackpressureLatest\b", "on back pressure latest"),
]

# every spoken line, in order
N = {
    "open": "A big family lunch. The cook is making dumplings, two hundred of them, one at a time, and a diner eats "
            "them as they come.",
    "phone": "Then the diner's phone rings, with dumpling 1 still on the plate. Somebody's aunt, by the sound of it. "
             "In a plain flow, the cook stands at the table holding dumpling 2 until the call ends.",
    "shelf": "Put a shelf in the hatch, and she can keep cooking while the diner talks. In code, that's buffer(10): a "
             "shelf with ten spots.",
    "shyq": "Here's a question that's easy to be shy about. How far does she actually get? While the diner is on the "
            "phone, how many of her emit calls return?",
    "a11": "Eleven. Ten dumplings wait on the shelf. And one more, dumpling 1, left the shelf when the diner picked "
           "it up. Ten, plus one in hand.",
    "how": "Here's the machine. It's the wall with a hatch from lesson 3. buffer moves the cook into a second "
           "coroutine, and her emit becomes a send into a channel with ten spots. send returns as long as a spot "
           "is free.",
    "how2": "On our side, a loop takes each dumpling off the shelf, and calls the real emit, which runs the diner. "
            "flowOn builds this machine to change the thread. buffer builds it to change the shelf.",
    "nums": "So the count is always one more than the shelf. No buffer: zero, because emit runs the diner. buffer(0), "
            "a hand-over where both hands must meet: one. buffer(10): eleven. And buffer() with no size has 64 spots, "
            "so 65.",
    "zero": "Even one dumpling of slack matters. buffer(0) turns lesson 1's dinner, 1,200 milliseconds, into 1,000.",
    "full": "So far, a full shelf made the cook wait. That's the default overflow policy, SUSPEND, and nothing is "
            "lost. The other two policies never wait. When the shelf is full, something goes in the bin.",
    "oven": "Dumplings are the wrong food for the bin, so take something where only the newest value matters: the "
            "oven's thermometer, and the little screen on the oven door. The screen is stuck drawing reading 1, "
            "while 200 readings arrive.",
    "drops": "buffer(10) shows all 200, because the thermometer waited. DROP_OLDEST bins the oldest waiting reading, "
             "and shows 1, then 191 to 200. DROP_LATEST bins each new one, and shows 1 to 11.",
    "conflate": "And conflate keeps only the newest: one spot, where each new reading pushes the waiting one into the "
                "bin. The screen shows 1, and then 200. It never makes anybody wait.",
    "trap": "Here's the trap. A helper wants the newest 64, and writes buffer with DROP_OLDEST, and no size. With a "
            "drop policy, the default size means one spot. So that line is conflate under another name. If you mean "
            "64, write 64.",
    "cost": "So before you pick a drop policy, ask what one lost value costs. A stale temperature is worth nothing. A "
            "lost plate of dumplings is a guest with no lunch. Plates get SUSPEND, always.",
    "fuse": "Two shelves side by side don't stay two. buffer(10) then buffer(20) snap together into one shelf of 30, "
            "so the cook gets 31 ahead. That's called fusion. And a drop policy at the end relabels the whole shelf: "
            "buffer(10) then conflate is just conflate.",
    "latest": "Last, collectLatest. A new reading cancels the drawing in progress. But a cancelled drawing must wipe "
              "its half-drawn number first, and that takes 50 milliseconds. Readings come every 100, and a drawing "
              "takes 300. When does the thermometer emit reading 3?",
    "latest_a": "Most people say 300. The virtual clock says 350, and the run ends at 700, not 600.",
    "latest_why": "collectLatest cancels the old block, then waits for it to finish, and it does that inside the "
                  "thermometer's emit. So the thermometer stands at the hatch with reading 2, while the screen wipes "
                  "reading 1.",
    "latest_rule": "So use the Latest operators only for work you can throw away, like drawing a number, and keep "
                   "the cleanup short.",
    "code": "Here it is in code. Plates get buffer(64): a full shelf makes the cook wait. Readings get conflate. In "
            "Java, plates go through a queue with 64 slots, and Reactor's onBackpressureLatest keeps only the "
            "newest reading.",
    "moral": "So, how far does the cook get? One more than the shelf holds, and then she waits, unless you chose a "
             "policy that bins. Shelves side by side snap into one, and collectLatest waits for the cleanup. Pick "
             "by what one lost value costs.",
    "check": "Quick check. buffer(10), then buffer(20). The diner is stuck on the first dumpling. How many emits "
             "return?",
    "check_a": "31. The two shelves fuse into one shelf of 30, plus one dumpling in the diner's hands.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole flow track (the cook is the coroutines track's cook)
COOK, DINER, EMIT, BAD, HATCH, DUMP, THERMO, SCREEN = BLUE_M, TEAL_M, PURPLE_M, RED_M, GREEN_M, GOLD_M, RED_M, TEAL_M
FLOOR = -1.95
WX = -0.6                       # the wall
HB, HT = -0.25, 0.95            # the hatch opening


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def table(w=2.6):
    top = Line(LEFT * w / 2, RIGHT * w / 2, stroke_width=6, color=GREY_B)
    legs = VGroup(Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_left() + RIGHT * 0.2 + DOWN * 0.35),
                  Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_right() + LEFT * 0.2 + DOWN * 0.35))
    return VGroup(top, legs)


def phone(s=1.0, color=GREY_A):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(BLUE_M, 0.5), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def rings(m, color=YELLOW_M):
    c = m.get_right() + RIGHT * 0.05
    return VGroup(*[Arc(radius=r, start_angle=-PI / 4, angle=PI / 2, arc_center=c).set_stroke(color, 2.5) for r in (0.18, 0.32)])


def dumpling(n=None, s=1.0):
    body = Ellipse(width=0.42, height=0.3).set_stroke(DUMP, 2.5).set_fill(dim(DUMP, 0.35), 1)
    g = VGroup(body)
    if n is not None:
        g.add(T(str(n), 20, WHITE).move_to(body))
    return g.scale(s).set_z_index(6)


def stove(s=1.0):
    body = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.95).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    door = RoundedRectangle(corner_radius=0.05, width=1.0, height=0.45).set_stroke(GREY_C, 2).set_fill(BLACK, 1)
    door.move_to(body.get_center() + DOWN * 0.12)
    knobs = VGroup(*[Circle(radius=0.05).set_stroke(GREY_B, 2).set_fill(GREY_D, 1) for _ in range(3)]).arrange(RIGHT, buff=0.2)
    knobs.move_to(body.get_top() + DOWN * 0.15)
    return VGroup(body, door, knobs).scale(s)


def wall_with_hatch(shelf_w=4.8):
    lo = Rectangle(width=0.32, height=HB - FLOOR).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([WX, (HB + FLOOR) / 2, 0])
    hi = Rectangle(width=0.32, height=2.45 - HT).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([WX, (2.45 + HT) / 2, 0])
    shelf = Rectangle(width=shelf_w, height=0.1).set_stroke(HATCH, 2).set_fill(dim(HATCH, 0.6), 1).move_to([WX, HB - 0.02, 0])
    return VGroup(lo, hi, shelf)


def spot_x(i, n=10, w=4.6):
    """x of shelf spot i (0-based) on a shelf of n spots centred on the wall."""
    step = w / n
    return WX - w / 2 + step * (i + 0.5)


def thermometer(s=1.0):
    tube = RoundedRectangle(corner_radius=0.1, width=0.2, height=0.9).set_stroke(THERMO, 2.5).set_fill(BLACK, 1)
    bulb = Circle(radius=0.17).set_stroke(THERMO, 2.5).set_fill(dim(THERMO, 0.6), 1).next_to(tube, DOWN, buff=-0.08)
    level = Rectangle(width=0.08, height=0.55).set_stroke(width=0).set_fill(THERMO, 1).move_to(tube.get_bottom() + UP * 0.32)
    return VGroup(tube, bulb, level).scale(s)


def oven_screen(text="1", s=1.0):
    r = RoundedRectangle(corner_radius=0.1, width=1.5, height=0.95).set_stroke(SCREEN, 3).set_fill(BLACK, 1)
    t = M(text, 30, SCREEN).move_to(r)
    return VGroup(r, t).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def chip_t(text, color, size=22, mono=False):
    t = (M if mono else T)(text, size, color)
    r = RoundedRectangle(corner_radius=0.07, width=t.width + 0.3, height=max(0.48, t.height + 0.24)).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


# the collectLatest clock
X0, PX = -4.3, 10.0 / 700


def tx(ms):
    return X0 + ms * PX


def bar(ms0, ms1, y, color, h=0.46, label=None, size=20, k=0.45, tc=WHITE):
    r = Rectangle(width=max(0.04, (ms1 - ms0) * PX), height=h).set_stroke(color, 2).set_fill(dim(color, k), 1)
    r.move_to([(tx(ms0) + tx(ms1)) / 2, y, 0])
    if label:
        return VGroup(r, T(label, size, tc).move_to(r))
    return VGroup(r)


class Flow04Belt(Narrated):
    """flow-04, section 0: buffer(n) is a shelf with n spots in the hatch. The family lunch, 200 dumplings, the
    diner's phone rings at dumpling 1; buffer(10): 11 emits return (10 on the shelf, 1 in hand); the machine (lesson
    3's wall, a second coroutine, a channel); 0, 1, 11, 65; buffer(0) turns 1,200 ms into 1,000; overflow policies on
    the oven screen (all 200; 1, 191..200; 1..11; conflate 1 and 200); the one-spot trap; what a lost value costs;
    fusion (30 spots, 31 ahead; conflate relabels); collectLatest joins the cleanup (emit 3 at 350, done at 700)."""

    def construct(self):
        self.title_card("A shelf in the hatch", "buffer, conflate and collectLatest")

        # ================= hook: the lunch and the phone =================
        floor = Line([-6.5, FLOOR, 0], [6.5, FLOOR, 0], stroke_width=1.5, color=GREY_D)
        stv = stove(1.0).move_to([-5.2, -1.45, 0])
        cook = person(COOK, 1.3).move_to([-3.9, -0.9, 0])
        tbl = table(2.6).move_to([4.2, -1.55, 0])
        diner = person(DINER, 1.3).move_to([4.95, -0.85, 0])
        plate1 = dumpling(1, 1.2).move_to(tbl[0].get_center() + LEFT * 0.35 + UP * 0.22)
        count = VGroup(T("200 dumplings,", 28, DUMP), T("one at a time", 28)).arrange(RIGHT, buff=0.2).move_to([0, 2.9, 0])
        self.say("open")
        self.play(FadeIn(VGroup(floor, stv, cook, tbl, diner)), run_time=0.8)
        self.at_text("two hundred", lead=0.3)
        self.play(FadeIn(count, shift=DOWN * 0.1), run_time=0.6)
        self.at_text("and a diner", lead=0.3)
        self.play(FadeIn(plate1, shift=DOWN * 0.1), run_time=0.5)
        self.hold()

        ph = phone(1.1).next_to(diner, UP, buff=0.2).shift(RIGHT * 0.45)
        rg = rings(ph)
        d2 = dumpling(2, 1.2).next_to(cook, RIGHT, buff=0.1)
        waits = T("emit(2) can't return: the cook waits at the table", 24, COOK).move_to([0.6, 1.45, 0])
        fit(waits, 9.0)
        self.say("phone")
        self.play(FadeIn(ph, shift=UP * 0.1), Create(rg), run_time=0.6)
        self.play(Wiggle(ph, scale_value=1.2, rotation_angle=0.05 * TAU), run_time=0.8)
        self.at(2)
        self.play(FadeIn(d2), run_time=0.3)
        self.play(VGroup(cook, d2).animate.move_to([2.6, -0.85, 0]), run_time=1.4)
        self.play(FadeIn(waits), run_time=0.5)
        self.hold()

        # ================= buffer(10): a shelf in the hatch =================
        w = wall_with_hatch()
        bl = M(".buffer(10)", 26, HATCH).move_to([WX, 2.85, 0])
        self.say("shelf")
        self.play(FadeOut(waits), FadeOut(d2), FadeOut(count), cook.animate.move_to([-3.9, -0.9, 0]), run_time=0.9)
        self.play(FadeIn(w[0], shift=UP * 0.2), FadeIn(w[1], shift=DOWN * 0.2), run_time=0.7)
        self.play(GrowFromCenter(w[2]), run_time=0.5)
        self.at_text("In code", lead=0.3)
        self.play(FadeIn(bl, shift=DOWN * 0.1), run_time=0.5)
        slots = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.3, height=0.06).set_stroke(HATCH, 1.5)
                         .move_to([spot_x(i), HB + 0.06, 0]) for i in range(10)])
        self.play(FadeIn(slots), run_time=0.5)
        self.hold()

        qn = T("How many emits return while the diner is on the phone?", 28).move_to([0, -2.7, 0])
        fit(qn, 11.5)
        self.say("shyq")
        self.at(2)
        self.play(FadeIn(qn, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        dumps = [dumpling(n) for n in range(2, 12)]
        for i, d in enumerate(dumps):
            d.move_to([spot_x(i), HB + 0.2, 0])
        d12 = dumpling(12).next_to(cook, RIGHT, buff=0.1)
        tally = VGroup(T("emits returned:", 28), T("11", 34, YELLOW_M)).arrange(RIGHT, buff=0.2).move_to([0, -2.55, 0])
        tsum = T("10 on the shelf + 1 in the diner's hands", 24, GREY_A).next_to(tally, DOWN, buff=0.15)
        self.say("a11")
        self.play(FadeOut(qn), LaggedStart(*[FadeIn(d, shift=RIGHT * 0.3) for d in dumps], lag_ratio=0.12), run_time=1.6)
        self.play(FadeIn(tally), run_time=0.4)
        self.at(1)
        self.play(Indicate(VGroup(*dumps), color=DUMP, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(plate1, color=DUMP, scale_factor=1.3), run_time=0.8)
        self.at(3)
        self.play(FadeIn(tsum), FadeIn(d12), run_time=0.5)
        self.hold()

        # ================= the machine =================
        sec = VGroup(T("a second coroutine", 22, COOK), T("emit became send", 22, GREY_A)).arrange(DOWN, buff=0.06)
        sec.move_to([-4.2, 0.65, 0])
        chan = VGroup(T("a channel with 10 spots", 22, HATCH), T("send returns while a spot is free", 20, GREY_A)).arrange(DOWN, buff=0.06)
        chan.move_to([WX, -2.6, 0])
        full = chip_t("send 12: waits", BAD, 20).next_to(d12, UP, buff=0.25)
        self.say("how")
        self.play(FadeOut(tally), FadeOut(tsum), Indicate(w[2], color=HATCH, scale_factor=1.05), run_time=0.8)
        self.at(1)
        self.play(FadeIn(sec, shift=DOWN * 0.1), run_time=0.6)
        self.at_text("into a channel", lead=0.3)
        self.play(FadeIn(chan, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(full, shift=UP * 0.1), run_time=0.5)
        self.hold()

        loop = VGroup(T("a loop calls the real emit:", 22, DINER), T("the diner runs here", 22, DINER)).arrange(DOWN, buff=0.06)
        loop.move_to([2.6, 0.75, 0])
        vs = VGroup(M("flowOn", 24, YELLOW_M), T("changes the thread,", 24), M("buffer", 24, HATCH), T("changes the shelf", 24))
        vs.arrange(RIGHT, buff=0.18).move_to([0, 2.85, 0])
        fit(vs, 12.4)
        self.say("how2")
        self.play(FadeIn(loop, shift=LEFT * 0.1), FadeOut(bl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(vs[:2], shift=DOWN * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(vs[2:], shift=DOWN * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the numbers =================
        rows = [("no buffer", "0", "emit runs the diner"), ("buffer(0)", "1", "a hand-over: both hands meet"),
                ("buffer(10)", "11", "10 on the shelf + 1 in hand"), ("buffer()", "65", "64 spots + 1 in hand")]
        tbl_rows = VGroup()
        for code_, n, why in rows:
            tbl_rows.add(VGroup(M(code_, 26, HATCH), T(n, 30, YELLOW_M), T(why, 24, GREY_A)))
        for r in tbl_rows:
            r[0].move_to([-4.0, 0, 0], aligned_edge=LEFT)
            r[1].move_to([-0.6, 0, 0])
            r[2].move_to([0.4, 0, 0], aligned_edge=LEFT)
        for i, r in enumerate(tbl_rows):
            r.shift(UP * (1.9 - i * 0.85))
        head = VGroup(T("chain", 22, GREY_B).move_to([-4.0, 2.75, 0], aligned_edge=LEFT),
                      T("emits ahead", 22, GREY_B).move_to([-0.6, 2.75, 0]))
        rule = T("Behind buffer(n), the cook gets n + 1 ahead.", 32, YELLOW_M).move_to([0, -1.75, 0])
        self.say("nums")
        self.play(FadeIn(head), run_time=0.4)
        self.at(1)
        self.play(FadeIn(tbl_rows[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(tbl_rows[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(tbl_rows[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(tbl_rows[3], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()

        z = VGroup(T("lesson 1's dinner:", 26, GREY_A), T("1,200 ms", 26, COOK), T("with buffer(0):", 26, GREY_A),
                   T("1,000 ms", 26, HATCH)).arrange(RIGHT, buff=0.22).move_to([0, -2.75, 0])
        fit(z, 12.4)
        self.say("zero")
        self.play(Indicate(tbl_rows[1], color=HATCH, scale_factor=1.04), run_time=0.8)
        self.at(1)
        self.play(FadeIn(z, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= when the shelf is full: the oven screen =================
        th = thermometer(1.3).move_to([-5.2, 0.9, 0])
        th_l = T("thermometer", 22, THERMO).next_to(th, DOWN, buff=0.2)
        sc = oven_screen("1", 1.2).move_to([4.9, 0.9, 0])
        sc_l = T("the oven-door screen", 22, SCREEN).next_to(sc, DOWN, buff=0.2)
        stuck = T("stuck drawing reading 1", 22, GREY_A).next_to(sc_l, DOWN, buff=0.1)
        sh = Rectangle(width=3.6, height=0.1).set_stroke(HATCH, 2).set_fill(dim(HATCH, 0.6), 1).move_to([-0.2, 0.5, 0])
        a1 = Arrow(th.get_right(), sh.get_left(), buff=0.25, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        a2 = Arrow(sh.get_right(), sc.get_left(), buff=0.25, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        pol = VGroup(T("full shelf, default policy", 24, GREY_A), M("SUSPEND", 24, HATCH), T(": the cook waits, nothing lost", 24, GREY_A))
        pol.arrange(RIGHT, buff=0.15).move_to([0, 2.85, 0])
        fit(pol, 12.4)
        self.say("full")
        self.play(FadeIn(pol, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        bin_ = VGroup(Polygon([-0.3, 0.3, 0], [0.3, 0.3, 0], [0.22, -0.3, 0], [-0.22, -0.3, 0]).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1),
                      Line([-0.36, 0.34, 0], [0.36, 0.34, 0], stroke_width=3, color=GREY_B)).move_to([-0.2, -0.6, 0])
        bin_l = T("the bin", 22, GREY_B).next_to(bin_, DOWN, buff=0.12)
        self.play(FadeIn(bin_), FadeIn(bin_l), run_time=0.5)
        self.hold()

        self.say("oven")
        self.at(1)
        self.play(FadeIn(th), FadeIn(th_l), FadeIn(sh), GrowArrow(a1), GrowArrow(a2), FadeIn(sc), FadeIn(sc_l), run_time=1.0)
        self.at(2)
        self.play(FadeIn(stuck), Indicate(sc[1], color=SCREEN, scale_factor=1.3), run_time=0.8)
        self.hold()

        res = [("buffer(10)", "all 200", "the thermometer waited", HATCH),
               ("buffer(10, DROP_OLDEST)", "1, then 191 to 200", "binned the oldest waiting", GOLD_M),
               ("buffer(10, DROP_LATEST)", "1 to 11", "binned each new one", GOLD_M),
               ("conflate()", "1 and 200", "one spot, the newest wins", YELLOW_M)]
        rr = VGroup()
        for code_, shows, why, c in res:
            rr.add(VGroup(M(code_, 22, c), T(shows, 24, WHITE), T(why, 20, GREY_A)))
        for i, r in enumerate(rr):
            r[0].move_to([-6.2, 0, 0], aligned_edge=LEFT)
            r[1].move_to([-1.6, 0, 0], aligned_edge=LEFT)
            r[2].move_to([1.8, 0, 0], aligned_edge=LEFT)
            r.shift(UP * (-1.6 - i * 0.48))
        self.say("drops")
        self.play(FadeOut(VGroup(bin_, bin_l)), FadeOut(pol), run_time=0.4)
        self.play(FadeIn(rr[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rr[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rr[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        one = RoundedRectangle(corner_radius=0.05, width=0.5, height=0.42).set_stroke(YELLOW_M, 2.5).move_to(sh.get_center() + UP * 0.28)
        r_old = T("57", 20).move_to(one)
        r_new = T("58", 20, YELLOW_M).move_to(one)
        cname = VGroup(T("conflation:", 24, YELLOW_M), T("keep only the newest waiting value", 24)).arrange(RIGHT, buff=0.15)
        cname.move_to([0, 2.85, 0])
        self.say("conflate")
        self.play(FadeIn(rr[3], shift=RIGHT * 0.1), FadeIn(cname, shift=DOWN * 0.1), run_time=0.6)
        self.play(Create(one), FadeIn(r_old), run_time=0.5)
        self.at_text("where each", lead=0.3)
        self.play(FadeIn(r_new, shift=RIGHT * 0.3), r_old.animate.shift(DOWN * 0.9).set_opacity(0), run_time=0.9)
        self.at(1)
        sc2 = oven_screen("200", 1.2).move_to(sc)
        self.play(Transform(sc, sc2), run_time=0.6)
        self.hold()

        trap = VGroup(M("buffer(onBufferOverflow = DROP_OLDEST)", 24, GOLD_M), T("\"the newest 64\"?", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        trap.move_to([0, 2.85, 0])
        fit(trap, 12.4)
        trap_a = VGroup(T("one spot: it is conflate().", 24, BAD), T("Mean 64? Write", 24), M("buffer(64, DROP_OLDEST)", 24, GOLD_M))
        trap_a.arrange(RIGHT, buff=0.18).move_to([0, 2.2, 0])
        fit(trap_a, 12.4)
        self.say("trap")
        self.play(FadeOut(cname), FadeIn(trap, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(trap_a[0]), Indicate(one, color=BAD, scale_factor=1.3), run_time=0.8)
        self.at(4)
        self.play(FadeIn(trap_a[1:]), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= what does one lost value cost? =================
        lft = VGroup(thermometer(1.0), T("a stale reading:", 26, THERMO), T("worth nothing", 26), M("conflate()", 24, YELLOW_M))
        lft.arrange(DOWN, buff=0.22).move_to([-3.3, 0.6, 0])
        rgt = VGroup(VGroup(dumpling(None, 1.6), person(DINER, 0.9)).arrange(RIGHT, buff=0.3), T("a lost plate:", 26, DUMP),
                     T("a guest with no lunch", 26), M("buffer(64)  // SUSPEND", 24, HATCH))
        rgt.arrange(DOWN, buff=0.22).move_to([3.3, 0.6, 0])
        q = T("Before a drop policy, ask: what does one lost value cost?", 30, YELLOW_M).move_to([0, -2.5, 0])
        fit(q, 12.4)
        self.say("cost")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lft[:3]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rgt[:3]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(lft[3]), FadeIn(rgt[3]), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= fusion: shelves snap together =================
        def shelf_g(n_spots, w, label, color=HATCH):
            board = Rectangle(width=w, height=0.12).set_stroke(color, 2).set_fill(dim(color, 0.6), 1)
            ticks = VGroup(*[Line(UP * 0.0, UP * 0.16, stroke_width=1.5, color=color).move_to(board.get_left() + RIGHT * (w * (i + 0.5) / n_spots) + UP * 0.12)
                             for i in range(n_spots)])
            lab = M(label, 24, color).next_to(board, UP, buff=0.35)
            return VGroup(board, ticks, lab)

        s1 = shelf_g(10, 2.6, "buffer(10)").move_to([-2.4, 1.2, 0])
        s2 = shelf_g(20, 5.2, "buffer(20)").move_to([2.4, 1.2, 0])
        s12 = shelf_g(30, 7.8, "one shelf: 30 spots").move_to([0, 1.2, 0])
        s12[2].set_color(YELLOW_M)
        ahead = VGroup(T("the cook gets", 26), T("31", 30, YELLOW_M), T("ahead", 26)).arrange(RIGHT, buff=0.15).move_to([0, -0.3, 0])
        fname = VGroup(T("fusion:", 26, YELLOW_M), T("neighbouring buffers merge into one channel", 26)).arrange(RIGHT, buff=0.15)
        fname.move_to([0, -1.05, 0])
        fit(fname, 12.4)
        s3 = shelf_g(10, 2.6, "buffer(10)").move_to([-1.6, -2.35, 0])
        s3l = M(".conflate()", 24, YELLOW_M).move_to([1.6, -2.05, 0])
        s4 = shelf_g(1, 0.5, "= conflate(): one spot", YELLOW_M).move_to([0, -2.35, 0])
        self.say("fuse")
        self.play(FadeIn(s1), FadeIn(s2), run_time=0.7)
        self.at(1)
        self.play(FadeOut(s1[2]), FadeOut(s2[2]), s1[:2].animate.move_to(s12[:2].get_left(), aligned_edge=LEFT),
                  s2[:2].animate.move_to(s12[:2].get_right(), aligned_edge=RIGHT), run_time=0.9)
        self.play(FadeIn(s12), FadeOut(s1[:2]), FadeOut(s2[:2]), run_time=0.4)
        self.play(FadeIn(ahead, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(fname, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(s3), FadeIn(s3l), run_time=0.6)
        self.at(4)
        self.play(FadeOut(s3), FadeOut(s3l), FadeIn(s4), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= collectLatest waits for the cleanup =================
        TY, SY, AY = 0.9, -0.1, -0.95
        lab = VGroup(M("readings.collectLatest { draw(it) }", 26, SCREEN)).move_to([0, 3.05, 0])
        facts = T("a reading every 100 ms, a drawing takes 300, a cancelled one wipes for 50", 24, GREY_A).move_to([0, 2.45, 0])
        fit(facts, 12.4)
        axl = Arrow([tx(0) - 0.1, AY, 0], [tx(700) + 0.5, AY, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.03)
        tks = VGroup(*[VGroup(Line([tx(m), AY - 0.07, 0], [tx(m), AY + 0.07, 0], stroke_width=2, color=GREY_B),
                              T(f"{m}", 20, GREY_B).move_to([tx(m), AY - 0.3, 0])) for m in (0, 100, 200, 250, 350, 400, 700)])
        msl = T("ms", 20, GREY_B).next_to(axl, RIGHT, buff=0.1)
        rl = VGroup(T("thermometer", 22, THERMO).move_to([tx(0) - 0.25, TY, 0], aligned_edge=RIGHT),
                    T("screen", 22, SCREEN).move_to([tx(0) - 0.25, SY, 0], aligned_edge=RIGHT))

        def emk(ms, n):
            tri = Triangle(color=THERMO).set_fill(THERMO, 1).scale(0.09).rotate(PI).move_to([tx(ms), TY + 0.05, 0])
            t = T(f"emit {n}", 20, THERMO).next_to(tri, UP, buff=0.08)
            return VGroup(tri, t)

        e1, e2, e3 = emk(100, 1), emk(200, 2), emk(350, 3)
        d1 = bar(100, 200, SY, SCREEN, label="draw 1", k=0.35)
        w1 = bar(200, 250, SY, BAD, label="", k=0.35)
        d2 = bar(250, 350, SY, SCREEN, label="draw 2", k=0.35)
        w2 = bar(350, 400, SY, BAD, label="", k=0.35)
        d3 = bar(400, 700, SY, SCREEN, label="draw 3: done at 700", k=0.45)
        wipe_l = T("wipe", 20, BAD).move_to([tx(225), SY - 0.48, 0])
        wipe_l2 = T("wipe", 20, BAD).move_to([tx(375), SY - 0.48, 0])
        wait_bar = bar(200, 250, TY, THERMO, h=0.3, k=0.2, label="")
        wait_l = T("waits at the hatch", 20, THERMO).move_to([tx(225) + 0.3, 0.4, 0])
        ghost = DashedLine([tx(300), TY + 0.3, 0], [tx(300), AY, 0], dash_length=0.06).set_stroke(GREY_B, 2)
        ghost_t = T("300?", 22, GREY_B).move_to([tx(300), 1.75, 0])
        self.say("latest")
        self.play(FadeIn(lab, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(Create(axl), FadeIn(tks), FadeIn(msl), FadeIn(rl), FadeIn(e1), FadeIn(d1), FadeIn(e2), run_time=1.0)
        self.at(2)
        self.play(GrowFromEdge(w1, LEFT), FadeIn(wipe_l), run_time=0.7)
        self.at(3)
        self.play(FadeIn(facts), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)

        self.say("latest_a")
        self.play(Create(ghost), FadeIn(ghost_t), run_time=0.5)
        self.at(1)
        self.play(GrowFromEdge(d2, LEFT), FadeIn(e3, shift=DOWN * 0.1), run_time=0.8)
        self.play(GrowFromEdge(w2, LEFT), FadeIn(wipe_l2), run_time=0.5)
        self.play(GrowFromEdge(d3, LEFT), run_time=0.8)
        gx = tick(False, 0.14).next_to(ghost_t, RIGHT, buff=0.1)
        self.play(Create(gx), run_time=0.4)
        self.hold()

        why = VGroup(T("cancel the old block,", 26), T("then wait for it to finish,", 26, BAD), T("inside the thermometer's emit", 26))
        why.arrange(RIGHT, buff=0.15).move_to([0, -2.3, 0])
        fit(why, 12.4)
        self.say("latest_why")
        self.play(FadeOut(VGroup(ghost, ghost_t, gx)), FadeIn(why, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(GrowFromEdge(wait_bar, LEFT), FadeIn(wait_l), Indicate(w1, color=BAD), run_time=0.9)
        self.hold()

        lr = T("Latest operators: only for work you can throw away. Keep the cleanup short.", 28, YELLOW_M).move_to([0, -3.05, 0])
        fit(lr, 12.4)
        self.say("latest_rule")
        self.play(FadeIn(lr, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code =================
        k = code_block(["cook.plates().buffer(64)          // full: the cook waits, nothing lost",
                        "    .collect { diner.eat(it) }",
                        "readings.conflate()               // one spot: the newest wins",
                        "    .collect { screen.draw(it) }"], 22,
                       {"buffer(64)": HATCH, "conflate()": YELLOW_M, "// full: the cook waits, nothing lost": GREY_B,
                        "// one spot: the newest wins": GREY_B})
        j = code_block(["BlockingQueue<Plate> shelf = new ArrayBlockingQueue<>(64);   // full: blocks",
                        "readings.onBackpressureLatest()                              // Reactor: newest wins"], 22,
                       {"ArrayBlockingQueue<>(64)": HATCH, "onBackpressureLatest()": YELLOW_M,
                        "// full: blocks": GREY_B, "// Reactor: newest wins": GREY_B})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.4).move_to([0, 0.2, 0])
        self.say("code")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(k[0], color=HATCH, buff=0.05), run_time=0.9)
        self.at(2)
        self.play(Circumscribe(k[2], color=YELLOW_M, buff=0.05), run_time=0.9)
        self.at(3)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= moral and check =================
        mq = T("How far does the cook get? One more than the shelf holds, then she waits.", 30).move_to(UP * 2.55)
        m1 = T("Drop policies never wait: they bin. Shelves side by side snap into one.", 30, HATCH).move_to(UP * 1.8)
        m2 = T("collectLatest waits for the cleanup. Pick by what one lost value costs.", 30, YELLOW_M).move_to(UP * 1.05)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), M("cook.buffer(10).buffer(20)", 26, HATCH), T("and the diner is stuck on 1.", 28))
        qa.arrange(RIGHT, buff=0.25)
        qb = T("How many emits return?", 28)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.22).move_to(DOWN * 0.7)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("31: one fused shelf of 30, plus one dumpling in hand", 30, YELLOW_M).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
