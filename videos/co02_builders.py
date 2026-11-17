from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [
    (r"\bkotlinx\.coroutines\b", "kotlin X co-routines"), (r"\bcoroutineScope\b", "co-routine scope"),
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bawaitAll\b", "await all"),
    (r"\basync\b", "ay-sink"), (r"\brunBlocking\b", "run blocking"), (r"\bcallAhead\b", "call ahead"),
    (r"\ballPrices\b", "all prices"), (r"\bpriceList\b", "price list"),
]

# every spoken line, in order
N = {
    "open": "Tonight, the cook texts three shops to ask who has the cheapest tomatoes. "
            "The greengrocer takes 300 milliseconds to reply, the market 120, and the farm stand 200.",
    "recap": "In code, each shop is a Grocer, and price suspends until the shop replies. async starts one question, "
             "and hands back a Deferred at once: a pot with the lid on. await lifts the lid.",
    "recap2": "Text all three first, then read the replies, and you wait only for the slowest shop: "
              "300 milliseconds, not 620. The lesson's demo, on a busy machine, took 321 milliseconds, against 666.",
    "launch": "Now a different job. The cook only wants to tell each shop: we'll order bread today. "
              "She needs no replies, so she uses launch, which is async without the answer. "
              "It starts a coroutine and returns a Job at once: a handle you can wait for or cancel, with no value inside.",
    "shyq": "Which brings up a question that's easy to be shy about. launch returns at once, three times, "
            "and nothing waits for the replies. So when does the function return? And if it returns at once, "
            "who's still texting?",
    "pain": "Let's entertain the scary answer. Say it returns at once. The caller thinks the job is done, and serves dinner, "
            "while three texts are still out. If one of them fails, there's nobody left to tell.",
    "drawer": "The cook is clearing the table, and her phone, in a drawer somewhere, is still texting the shops. "
              "So we need someone whose job is to wait for every text.",
    "course": "A kitchen already has that someone: the course. The starters don't go out until every dish in them is ready. "
              "The cook can finish her own part early. The plate still waits for the slowest dish.",
    "map": "In code, the course is coroutineScope. It runs its block, the cook's own part. "
           "Every coroutine started inside becomes one of its dishes, a child. "
           "And the course going out is coroutineScope returning.",
    "pred_q": "So here's callAhead. Inside coroutineScope, it launches one text per grocer, and its block ends right away. "
              "When does callAhead return?",
    "pred_a": "At 300 milliseconds, when the slowest grocer has answered. The block was done at once, "
              "but the scope waits for every child, even the ones nobody awaited.",
    "value": "And if the block ends with a value, the value waits too. A scope that launches a 200 millisecond job, "
             "and then says 42, returns 42 after 200 milliseconds.",
    "promise": "That's the promise coroutineScope makes to your callers: when a suspend function returns, "
               "the work it started is done. Nothing keeps running behind their back. No phone in a drawer.",
    "scope": "It's also why you can't call launch just anywhere. launch needs a scope: something that keeps track "
             "of the coroutines started in it, and becomes their parent. Here, that's the course.",
    "fail_q": "Now one dish goes wrong. The market's reply fails at 120 milliseconds. "
              "When does callAhead finish, and what happens to the other two texts?",
    "fail_a": "It fails at about 120 milliseconds. The scope cancels the other two texts, waits for them to stop, "
              "and then hands the market's exception to its caller. Nothing is left texting.",
    "fail2": "Waiting for the children, and stopping the rest when one fails: the next lesson draws the family tree "
             "behind both.",
    "nest": "While it waits, coroutineScope suspends. It doesn't block, so the thread is free to cook something else. "
            "And because it's a suspend function itself, it nests. The lab's priceList asks about tomatoes and basil, "
            "each with allPrices and its own scope inside. Six questions at once, and the list is ready in 300 milliseconds.",
    "g1": "A few rules keep this honest. Start everything, then await. An await straight after each async waits "
          "before the next text goes out. In the demo, that took 627 milliseconds, the full sum, "
          "and it still passed a test that only checked the answers.",
    "g2": "Use launch when you don't need the value. An async that nobody awaits hides what you meant. "
          "And keep runBlocking in main and tests. It waits for its children too, but it holds its thread the whole time: "
          "the cook back at the pot. Eight 200 millisecond lookups on two threads took 858 milliseconds that way, "
          "instead of 292.",
    "limit": "One limit. The overlap comes from waiting. Three dishes that each need 300 milliseconds of chopping, "
             "on one thread, take 900, async or not. async can't grow the cook more hands. "
             "So the point is: it overlaps waits, not work.",
    "code": "Here's callAhead in Kotlin, with its closest Java match. A Java executor in a try block waits, "
            "when it closes, for every task it was given. But if one task fails, it doesn't stop the others. "
            "coroutineScope does both.",
    "moral": "So, what stops a function from returning while its work is still going? coroutineScope. "
             "launch and async start the dishes and return at once. The course waits for every dish, "
             "and if one fails, it stops the rest and tells the caller. A suspend function should return only when its work is done.",
    "check": "Quick check. Inside coroutineScope, the cook awaits the greengrocer's price, 300 milliseconds, "
             "and launches a 500 millisecond text to the farm stand that nobody awaits. When does the scope return?",
    "check_a": "At 500 milliseconds. The price is in at 300, but the course waits for every dish.",
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


# one colour per thing, for the whole coroutines track
COOK, COURSE, BAD, OFF = BLUE_M, PURPLE_M, RED_M, GREY_D
GG, MK, FS = GREEN_M, GOLD_M, TEAL_M          # greengrocer, market, farm stand
SHOPS = [("greengrocer", 300, GG), ("market", 120, MK), ("farm stand", 200, FS)]


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def phone(s=1.0, color=GREY_A):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(BLUE_M, 0.5), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def shop(name, color, s=1.0):
    body = Rectangle(width=1.3, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.14), 1)
    awn = Polygon([-0.78, 0, 0], [0.78, 0, 0], [0.62, 0.3, 0], [-0.62, 0.3, 0]).set_stroke(color, 2.5)
    awn.set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0)
    door = Rectangle(width=0.3, height=0.42).set_stroke(color, 2).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.21)
    lab = T(name, 22, color).next_to(body, DOWN, buff=0.15)
    return VGroup(body, awn, door, lab).scale(s)


def pot(color, s=1.0, lid=True):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    g = VGroup(body, rim, hl, hr)
    if lid:
        top = ArcBetweenPoints(LEFT * 0.5, RIGHT * 0.5, angle=-PI / 3).set_stroke(color, 3)
        knob = Circle(radius=0.07).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1)
        top.move_to(rim.get_center() + UP * 0.1)
        knob.next_to(top, UP, buff=-0.02)
        g.add(VGroup(top, knob))
    return g.scale(s)


def drawer(s=1.0):
    front = RoundedRectangle(corner_radius=0.05, width=2.2, height=0.8).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    knob = RoundedRectangle(corner_radius=0.04, width=0.5, height=0.12).set_stroke(GREY_A, 2).move_to(front.get_center() + DOWN * 0.15)
    return VGroup(front, knob).scale(s)


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
    r = RoundedRectangle(corner_radius=0.07, width=t.width + 0.3, height=max(0.5, t.height + 0.24)).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r))


# a time axis: x(ms)
X0, PX = -3.3, 0.0128


def tx(ms):
    return X0 + ms * PX


def bar(ms0, ms1, y, color, h=0.32, label=None, size=20):
    r = Rectangle(width=max(0.04, (ms1 - ms0) * PX), height=h).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
    r.move_to([(tx(ms0) + tx(ms1)) / 2, y, 0])
    if label:
        t = T(label, size, WHITE)
        if t.width > r.width - 0.1:
            t.next_to(r, RIGHT, buff=0.12)
        else:
            t.move_to(r)
        return VGroup(r, t)
    return VGroup(r)


def axis(y, ticks, top=None):
    ln = Arrow([tx(0) - 0.1, y, 0], [tx(max(ticks)) + 0.6, y, 0], buff=0, stroke_width=2.5, color=GREY_B,
               max_tip_length_to_length_ratio=0.03)
    tk = VGroup(*[VGroup(Line([tx(m), y - 0.07, 0], [tx(m), y + 0.07, 0], stroke_width=2, color=GREY_B),
                         T(f"{m}", 20, GREY_B).move_to([tx(m), y - 0.28, 0])) for m in ticks])
    ms = T("ms", 20, GREY_B).next_to(ln, RIGHT, buff=0.1)
    return VGroup(ln, tk, ms)


def marker(ms, y0, y1, color, text, size=22, side=UP):
    ln = DashedLine([tx(ms), y0, 0], [tx(ms), y1, 0], dash_length=0.08).set_stroke(color, 2.5)
    t = T(text, size, color).next_to(ln, side, buff=0.1)
    return VGroup(ln, t)


class Co02Builders(Narrated):
    """co-02, section 2: coroutineScope waits for every child it started. The cook texts three shops (async, a pot
    with the lid on; 300 not 620); launch returns a Job at once; the shy question (when does the function return?);
    the scary answer (a phone in a drawer); the course; callAhead returns at 300 ms; 42 after 200 ms; the promise;
    the market fails at 120 ms; suspends and nests (priceList, 6 questions, 300 ms); guardrails; Kotlin and Java."""

    def construct(self):
        self.title_card("A course waits for its dishes", "launch, async and coroutineScope")

        # ================= the familiar: texting three shops =================
        cook = person(COOK, 1.2).move_to([-5.3, 1.75, 0])
        ph = phone(0.9).next_to(cook, RIGHT, buff=0.12).shift(DOWN * 0.1)
        SHX = [0.4, 2.65, 4.9]
        shops = [shop(n, c).move_to([x, 1.85, 0]) for (n, _, c), x in zip(SHOPS, SHX)]
        lat = [T(f"{ms} ms", 22, c).next_to(s[3], DOWN, buff=0.1) for (n, ms, c), s in zip(SHOPS, shops)]
        self.say("open")
        self.play(FadeIn(cook), FadeIn(ph), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.15) for s in shops], lag_ratio=0.2), run_time=1.0)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l) for l in lat], lag_ratio=0.4), run_time=1.4)
        self.hold()

        pots = [pot(c, 0.75).move_to([x, -0.35, 0]) for (n, ms, c), x in zip(SHOPS, SHX)]
        d_l = VGroup(M("Deferred", 24, GREY_A), T("a pot with the lid on", 22, GREY_A)).arrange(DOWN, buff=0.08)
        d_l.move_to([-4.3, -0.35, 0])
        self.say("recap")
        self.at_text("async starts", lead=0.3)
        texts = [Line(ph.get_right() + RIGHT * 0.05, s[0].get_left() + LEFT * 0.1) for s in shops]
        self.play(*[travel(l, c, run_time=0.9) for l, (n, ms, c) in zip(texts, SHOPS)], run_time=0.9)
        self.at_text("and hands", lead=0.3)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in pots], lag_ratio=0.2), FadeIn(d_l), run_time=0.9)
        self.at_text("await lifts", lead=0.3)
        self.play(pots[1][4].animate.shift(UP * 0.35).rotate(0.3), run_time=0.6)
        val = T("149 cents", 22, MK).next_to(pots[1], RIGHT, buff=0.15)
        self.play(FadeIn(val), run_time=0.4)
        self.hold()

        ax = axis(-3.0, [0, 120, 300, 620])
        rA = [bar(0, 300, -1.45, GG), bar(300, 420, -1.45, MK), bar(420, 620, -1.45, FS)]
        rA_l = T("one after another", 22, GREY_A).move_to([tx(0) - 0.25, -1.45, 0], aligned_edge=RIGHT)
        rB = [bar(0, 300, -1.95, GG), bar(0, 120, -2.3, MK), bar(0, 200, -2.65, FS)]
        rB_l = T("all at once", 22, GREY_A).move_to([tx(0) - 0.25, -2.3, 0], aligned_edge=RIGHT)
        eA = T("620", 24, BAD).next_to(rA[2], RIGHT, buff=0.15)
        eB = T("300: the slowest shop", 24, GG).next_to(rB[0], RIGHT, buff=0.15)
        demo = T("the demo: 666 ms against 321 ms", 22, GREY_B).move_to([3.6, -2.3, 0])
        self.say("recap2")
        self.play(FadeIn(ax), FadeIn(rA_l), run_time=0.5)
        self.play(*[GrowFromEdge(b, LEFT) for b in rA], run_time=0.9)
        self.play(FadeIn(eA), run_time=0.3)
        self.play(FadeIn(rB_l), *[GrowFromEdge(b, LEFT) for b in rB], run_time=0.9)
        self.at_text("300 milliseconds", lead=0.4)
        self.play(FadeIn(eB), run_time=0.4)
        self.at(1)
        demo.next_to(eB, DOWN, buff=0.35).align_to(eB, LEFT)
        self.play(FadeIn(demo), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(ax, *rA, rA_l, *rB, rB_l, eA, eB, demo, *pots, d_l, val, *lat)), run_time=0.6)

        # ================= launch, and the shy question =================
        bread = T("\"we'll order bread today\"", 24, GREY_A).move_to([-2.2, 0.75, 0])
        ln = code_block(["grocers.forEach { g -> launch { g.price(\"bread\") } }"], 26, {"launch": COOK})
        ln.move_to([0, -0.45, 0])
        jobs = [chip_t("Job", c, 22, mono=True).move_to([x, 0.75, 0]) for (n, ms, c), x in zip(SHOPS, SHX)]
        job_l = T("a handle: wait for it, or cancel it. No value inside.", 24, GREY_A).move_to([0, -1.3, 0])
        self.say("launch")
        self.play(FadeIn(bread, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ln, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(*[travel(l, c, run_time=0.8) for l, (n, ms, c) in zip(texts, SHOPS)],
                  LaggedStart(*[FadeIn(j, scale=0.7) for j in jobs], lag_ratio=0.2), run_time=0.9)
        self.play(FadeIn(job_l), run_time=0.5)
        self.hold()

        q = T("launch returns at once. So when does the function return?", 30).move_to([0, -2.3, 0])
        fit(q, 12.4)
        q2 = T("And who's still texting?", 30, YELLOW_M).next_to(q, DOWN, buff=0.2)
        self.say("shyq")
        self.at(1)
        self.play(*[Indicate(j[1], color=WHITE) for j in jobs], run_time=0.8)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(q, q2, job_l, bread, *jobs)), run_time=0.5)

        # ================= the scary answer =================
        ax2 = axis(-3.0, [0, 120, 200, 300])
        ret0 = marker(0, -0.2, -2.85, BAD, "returns at once?", 24)
        out = [bar(0, ms, y, c, label=n) for (n, ms, c), y in zip(SHOPS, (-1.05, -1.6, -2.15))]
        still = T("still out", 24, GREY_A).move_to([tx(300) + 1.3, -1.6, 0])
        self.say("pain")
        self.play(ln.animate.move_to([0, 0.6, 0]), FadeIn(ax2), run_time=0.6)
        self.at(1)
        self.play(Create(ret0[0]), FadeIn(ret0[1]), run_time=0.6)
        self.at(2)
        self.play(*[GrowFromEdge(b, LEFT) for b in out], run_time=1.4)
        self.play(FadeIn(still), run_time=0.4)
        self.at(3)
        xb = tick(False, 0.2).next_to(out[1], RIGHT, buff=0.15)
        nob = T("nobody to tell", 22, BAD).next_to(xb, RIGHT, buff=0.15)
        self.play(FadeOut(still), out[1][0].animate.set_stroke(BAD).set_fill(dim(BAD, 0.4)), Create(xb), FadeIn(nob), run_time=0.8)
        self.hold()

        dr = drawer(1.0).move_to([3.4, 0.0, 0])
        dph = phone(0.8).move_to(dr.get_top() + UP * 0.12 + LEFT * 0.4).set_z_index(-1)
        buzz = VGroup(*[Arc(radius=r, start_angle=-0.6, angle=1.2).set_stroke(GREY_A, 2).move_to(dph.get_right() + RIGHT * (0.1 + r))
                        for r in (0.12, 0.24)])
        need = T("someone has to wait for every text", 26, YELLOW_M).move_to([0, 2.4, 0])
        self.say("drawer")
        self.play(FadeOut(VGroup(ln, ax2, ret0, *out, xb, nob, *shops, ph)), cook.animate.move_to([-3.5, 0.2, 0]), run_time=0.8)
        self.play(FadeIn(dr), FadeIn(dph, shift=UP * 0.2), run_time=0.6)
        self.play(Wiggle(dph, scale_value=1.15), FadeIn(buzz), run_time=1.0)
        self.at(1)
        self.play(FadeIn(need, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(dr, dph, buzz, need)), run_time=0.5)

        # ================= the course =================
        crs = RoundedRectangle(corner_radius=0.16, width=6.6, height=2.5).set_stroke(COURSE, 3).set_fill(dim(COURSE, 0.1), 1)
        crs.move_to([0.9, 0.15, 0])
        crs_t = T("the starters", 28, COURSE).next_to(crs, UP, buff=0.15)
        DX = [-1.3, 0.9, 3.1]
        dishes = [pot(c, 0.9, lid=False).move_to([x, 0.25, 0]) for (n, ms, c), x in zip(SHOPS, DX)]
        ready = [tick(True, 0.22).next_to(d, DOWN, buff=0.25) for d in dishes]
        part = T("her part: done", 24, COOK).next_to(cook, DOWN, buff=0.3)
        self.say("course")
        self.play(FadeIn(crs), FadeIn(crs_t), LaggedStart(*[FadeIn(d, shift=UP * 0.1) for d in dishes], lag_ratio=0.2),
                  run_time=1.0)
        self.at(1)
        self.play(Create(ready[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(part), run_time=0.5)
        self.at(3)
        self.play(Create(ready[2]), run_time=0.5)
        self.play(Create(ready[0]), run_time=0.5)
        course_g = VGroup(crs, crs_t, *dishes, *ready)
        self.play(course_g.animate.shift(RIGHT * 0.5), run_time=0.6)
        self.play(course_g.animate.shift(LEFT * 0.5), run_time=0.4)
        self.hold()

        m1 = M("coroutineScope", 26, COURSE).move_to(crs_t)
        m2 = T("the block", 24, COOK).move_to(part)
        m3 = T("children", 24, WHITE).move_to([0.9, -1.55, 0])
        m4 = T("going out = returning", 24, COURSE).move_to([0.9, -2.2, 0])
        self.say("map")
        self.play(FadeOut(crs_t, shift=UP * 0.1), FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("the cook's", lead=0.4)
        self.play(FadeOut(part), FadeIn(m2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m3), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m4), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(crs, *dishes, *ready, m1, m2, m3, m4, cook)), run_time=0.6)

        # ================= predict callAhead =================
        ca = code_block(["suspend fun callAhead() = coroutineScope {",
                         "    grocers.forEach { g -> launch { g.price(\"bread\") } }", "}"], 24,
                        {"coroutineScope": COURSE, "launch": COOK})
        ca.move_to([0, 2.45, 0])
        ax3 = axis(-3.0, [0, 120, 200, 300, 500])
        blk = bar(0, 6, 0.95, COOK)
        blk_l = T("block: done at once", 22, COOK).move_to([tx(6) + 0.2, 0.95, 0], aligned_edge=LEFT)
        kids = [bar(0, ms, y, c, label=n) for (n, ms, c), y in zip(SHOPS, (0.3, -0.25, -0.8))]
        sc_bar = Rectangle(width=300 * PX, height=0.36).set_stroke(COURSE, 2.5).set_fill(dim(COURSE, 0.35), 1)
        sc_bar.move_to([(tx(0) + tx(300)) / 2, -1.55, 0])
        sc_l = M("coroutineScope", 22, COURSE).move_to([tx(0) - 0.25, -1.55, 0], aligned_edge=RIGHT)
        self.say("pred_q")
        self.play(FadeIn(ca, shift=UP * 0.1), FadeIn(ax3), run_time=0.8)
        self.at(1)
        self.play(GrowFromEdge(blk, LEFT), FadeIn(blk_l), *[GrowFromEdge(k, LEFT) for k in kids], run_time=1.2)
        self.at(2)
        qm = T("?", 44).move_to([tx(150), -1.55, 0])
        self.play(FadeIn(sc_l), FadeIn(qm), run_time=0.5)
        self.hold(after=0)
        self.predict()
        ret = marker(300, -1.25, -2.85, COURSE, "returns at 300 ms", 22, RIGHT)
        ret[1].move_to([tx(300) + 0.2, -2.35, 0], aligned_edge=LEFT)
        self.say("pred_a")
        self.play(FadeOut(qm), GrowFromEdge(sc_bar, LEFT), run_time=1.2)
        self.play(Create(ret[0]), FadeIn(ret[1]), run_time=0.6)
        self.at(1)
        self.play(Indicate(blk_l, color=COOK), run_time=0.7)
        self.play(Indicate(kids[0][1], color=GG), run_time=0.7)
        self.hold()

        v_code = M("coroutineScope { launch { delay(200) }; 42 }", 24, t2c={"coroutineScope": COURSE, "42": YELLOW_M})
        v_code.move_to([2.3, 0.95, 0])
        v_kid = bar(0, 200, 0.3, GREY_A, label="delay(200)")
        v_sc = Rectangle(width=200 * PX, height=0.36).set_stroke(COURSE, 2.5).set_fill(dim(COURSE, 0.35), 1)
        v_sc.move_to([(tx(0) + tx(200)) / 2, -0.4, 0])
        v_ret = T("42, at 200 ms", 26, YELLOW_M).next_to(v_sc, RIGHT, buff=0.2)
        self.say("value")
        self.play(FadeOut(VGroup(ca, blk, blk_l, *kids, sc_bar, sc_l, ret)), run_time=0.5)
        self.play(FadeIn(v_code), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(v_kid, LEFT), run_time=0.7)
        self.play(GrowFromEdge(v_sc, LEFT), run_time=0.7)
        self.play(FadeIn(v_ret, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(v_code, v_kid, v_sc, v_ret, ax3)), run_time=0.5)

        # ================= the promise =================
        pr1 = T("When a suspend function returns,", 34).move_to([0, 1.6, 0])
        pr2 = T("the work it started is done.", 34, COURSE).next_to(pr1, DOWN, buff=0.2)
        pd = VGroup(drawer(0.8), tick(False, 0.25)).arrange(RIGHT, buff=0.3).move_to([0, -0.4, 0])
        need_s = VGroup(M("launch", 28, COOK), T("needs a scope: something that tracks its coroutines,", 26),
                        T("and becomes their parent", 26)).arrange(DOWN, buff=0.15).move_to([0, -2.1, 0])
        self.say("promise")
        self.play(FadeIn(pr1, shift=UP * 0.1), run_time=0.6)
        self.at_text("the work", lead=0.3)
        self.play(FadeIn(pr2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(pd), run_time=0.6)
        self.hold()
        self.say("scope")
        self.play(FadeOut(pd), run_time=0.4)
        self.at(1)
        self.play(FadeIn(need_s, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(pr2, color=COURSE, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(pr1, pr2, need_s)), run_time=0.5)

        # ================= failure =================
        ax4 = axis(-3.0, [0, 120, 200, 300])
        kids = [bar(0, ms, y, c, label=n) for (n, ms, c), y in zip(SHOPS, (1.3, 0.75, 0.2))]
        f_sc_l = M("coroutineScope", 22, COURSE).move_to([tx(0) - 0.25, -0.55, 0], aligned_edge=RIGHT)
        self.say("fail_q")
        self.play(FadeIn(ax4), *[GrowFromEdge(k, LEFT) for k in kids], FadeIn(f_sc_l), run_time=1.0)
        self.at(1)
        xm = tick(False, 0.2).move_to([tx(120) + 0.3, 0.75, 0])
        self.play(Create(xm), kids[1][0].animate.set_stroke(BAD).set_fill(dim(BAD, 0.45)), run_time=0.7)
        self.hold(after=0)
        self.predict()

        def cut(b, ms, color):
            r = Rectangle(width=ms * PX, height=0.32).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
            r.move_to([(tx(0) + tx(ms)) / 2, b.get_y(), 0])
            return r

        self.say("fail_a")
        f_sc = Rectangle(width=120 * PX, height=0.36).set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.35), 1)
        f_sc.move_to([(tx(0) + tx(120)) / 2, -0.55, 0])
        f_ret = marker(120, 1.65, -2.85, BAD, "fails at 120 ms", 22, UP)
        f_ret[1].move_to([tx(120) + 0.2, -1.2, 0], aligned_edge=LEFT)
        self.play(GrowFromEdge(f_sc, LEFT), Create(f_ret[0]), FadeIn(f_ret[1]), run_time=0.8)
        self.at(1)
        rest = [kids[0][0], kids[2][0]]
        stubs = [cut(kids[0][0], 120, GG), cut(kids[2][0], 120, FS)]
        offs = VGroup(*[T("cancelled", 22, GREY_A).move_to([tx(260), b.get_y(), 0]) for b in rest])
        self.play(*[r.animate.set_stroke(OFF).set_fill(dim(OFF, 0.3)) for r in rest],
                  *[FadeIn(s) for s in stubs], FadeIn(offs), run_time=0.9)
        self.at(2)
        up = Arrow([tx(120) + 1.4, -0.55, 0], [tx(120) + 1.4, -1.95, 0], buff=0, stroke_width=3, color=BAD,
                   max_tip_length_to_length_ratio=0.15)
        cl = T("to the caller", 22, BAD).next_to(up, RIGHT, buff=0.15)
        self.play(GrowArrow(up), FadeIn(cl), run_time=0.6)
        self.hold()

        tree_n = T("next lesson: the family tree behind both", 26, YELLOW_M).move_to([0, 2.65, 0])
        self.say("fail2")
        self.play(FadeIn(tree_n, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= suspends, and nests =================
        fc = person(COOK, 1.0).move_to([-5.4, 2.0, 0])
        fc_l = T("thread: free", 22, COOK).next_to(fc, DOWN, buff=0.12)
        outer = RoundedRectangle(corner_radius=0.16, width=10.6, height=3.7).set_stroke(COURSE, 3).set_fill(dim(COURSE, 0.06), 1)
        outer.move_to([0.9, -0.85, 0])
        outer_t = M("priceList(tomatoes, basil)", 24, COURSE).next_to(outer, UP, buff=0.12).align_to(outer, LEFT)

        def inner(item, cx):
            r = RoundedRectangle(corner_radius=0.12, width=4.9, height=2.7).set_stroke(COURSE, 2.5).set_fill(dim(COURSE, 0.12), 1)
            r.move_to([cx, -1.05, 0])
            t = M(f"allPrices({item})", 22, COURSE).move_to(r.get_top() + DOWN * 0.3)
            bs = VGroup()
            for k, (n, ms, c) in enumerate(SHOPS):
                b = Rectangle(width=ms * 0.0125, height=0.32).set_stroke(c, 2).set_fill(dim(c, 0.45), 1)
                b.move_to([cx - 2.1 + ms * 0.0125 / 2, -0.75 - 0.5 * k, 0])
                bs.add(VGroup(b, T(n, 20, WHITE).next_to(b, RIGHT, buff=0.1)))
            return VGroup(r, t, bs)

        i1, i2 = inner("tomatoes", -1.75), inner("basil", 3.55)
        six = T("6 questions at once: ready in 300 ms", 28, YELLOW_M).move_to([0.9, -3.15, 0])
        self.say("nest")
        self.play(FadeIn(fc), FadeIn(fc_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(outer), FadeIn(outer_t), run_time=0.6)
        self.at_text("each with", lead=0.4)
        self.play(FadeIn(i1[:2]), FadeIn(i2[:2]), run_time=0.6)
        self.play(*[GrowFromEdge(b, LEFT) for b in (*i1[2], *i2[2])], run_time=1.0)
        self.at_text("Six questions", lead=0.3)
        self.play(FadeIn(six, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(fc, fc_l, outer, outer_t, i1, i2, six)), run_time=0.6)

        # ================= guardrails =================
        def rule(n, head, body, color):
            num = T(n, 30, color)
            h = T(head, 28, color)
            b = T(body, 22, GREY_A)
            txt = VGroup(h, b).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            return VGroup(num, txt).arrange(RIGHT, buff=0.35, aligned_edge=UP)

        r1 = rule("1", "Start everything, then await", "an await straight after each async: 627 ms, and the test still passed", YELLOW_M)
        r2 = rule("2", "launch when you need no value", "an async that nobody awaits hides what you meant", COOK)
        r3 = rule("3", "runBlocking only in main and tests", "it holds its thread: 8 lookups on 2 threads, 858 ms instead of 292", BAD)
        rules = VGroup(r1, r2, r3).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(rules, 12.0).move_to([0, 0.6, 0])
        self.say("g1")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at_text("passed a test", lead=0.5)
        self.play(Indicate(r1[1][1], color=YELLOW_M, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.say("g2")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.7)
        self.hold()

        lim_t = T("the limit: the overlap comes from waiting", 28, GREY_A).move_to([0, -1.7, 0])
        chop = VGroup(*[bar(300 * k, 300 * (k + 1), 0, GREY_A, h=0.34) for k in range(3)])
        chop.move_to([0, -2.45, 0])
        chop_l = T("3 x 300 ms of chopping on one thread: 900 ms", 24, GREY_A).next_to(chop, DOWN, buff=0.15)
        hands = T("async can't grow the cook more hands", 26, YELLOW_M).move_to([0, -1.7, 0])
        self.say("limit")
        self.play(rules.animate.shift(UP * 0.6), FadeIn(lim_t), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in chop], lag_ratio=0.9), FadeIn(chop_l), run_time=1.6)
        self.at(3)
        self.play(FadeOut(lim_t), FadeIn(hands), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(rules, chop, chop_l, hands)), run_time=0.6)

        # ================= the code, last =================
        khl = {"coroutineScope": COURSE, "launch": COOK}
        k2 = code_block(["suspend fun callAhead() = coroutineScope {",
                         "    grocers.forEach { g -> launch { g.price(\"bread\") } }",
                         "}   // returns after the slowest grocer answers"], 22, {**khl, "// returns after the slowest grocer answers": GREY_B})
        j2 = code_block(["void callAhead() {",
                         "    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {",
                         "        grocers.forEach(g -> executor.submit(() -> g.price(\"bread\")));",
                         "    }   // close() waits for every task, but cancels none",
                         "}"], 22, {"// close() waits for every task, but cancels none": GREY_B})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k2).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java (JDK 19+)", 24, GREY_B), j2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.3, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(j2[3], color=GREY_A, scale_factor=1.02), run_time=0.9)
        self.at(3)
        self.play(Indicate(k2[0], color=COURSE, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("What stops a function from returning early? coroutineScope.", 32).move_to(UP * 2.4)
        m1 = T("launch and async start the dishes, and return at once.", 30).move_to(UP * 1.55)
        m2 = T("The course waits for every dish, and stops the rest if one fails.", 30, COURSE).move_to(UP * 0.85)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M), T("await a 300 ms price, and launch a 500 ms text nobody awaits.", 28))
        qq.arrange(RIGHT, buff=0.25)
        qq2 = T("When does coroutineScope return?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("at 500 ms: the course waits for every dish", 30, COURSE).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
