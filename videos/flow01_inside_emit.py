from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\b(emit|take)\((\d)\)", r"\1 \2")]

# every spoken line, in order
N = {
    "open": "A reader needs 100 milliseconds to read each settlement line. A ledger writer needs 300 milliseconds to post it. "
            "A plain flow connects the two.",
    "q": "The reader emits the first line at 100 milliseconds. When does it emit the second?",
    "cook": "Picture one cook and one diner. collect runs the flow block, and that block is the cook. "
            "Reading a line takes 100 milliseconds.",
    "walk": "Then the cook calls emit, and walks the plate to the table. "
            "emit runs your collector's code right inside it. That's the diner.",
    "stand": "The diner posts to the ledger for 300 milliseconds. "
             "And the cook stands at the table the whole time, because emit hasn't returned.",
    "back": "emit returns only when the box inside it closes, at 400. "
            "Then the cook reads the next line, which takes 100 more. So the second emit is at 500, not 200.",
    "rest": "The same happens for every line. Each one costs 100 plus 300. "
            "Three lines take 1200 milliseconds, where the writer alone needs 900.",
    "seq": "Two rules come out of this one picture. First, a flow is sequential. "
           "While emit(1) is open, the cook can't start line 2, and the diner never holds two plates at once.",
    "bp": "Second, a slow collector slows the producer. The reader could read a line every 100 milliseconds. "
          "Here it reads one every 400, because it waits at the table. That is backpressure, for free, with no protocol.",
    "break": "One thing the picture gets wrong. The waiting cook is a suspended coroutine, and it holds no thread. "
             "While your collector waits on the ledger, the thread runs other coroutines.",
    "code": "In code, nothing marks the wait. Kotlin's emit and Java's accept are plain calls, "
            "and they return when the collector's code returns.",
    "rule": "So emit is a direct call into the collector. A plain flow handles one value at a time, "
            "at the speed of its collector.",
    "check": "Quick check. A reader needs 50 milliseconds per line, and the writer needs 200. When is the second emit?",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.1, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def frame(l, r, t, b, color, k=0.10, sw=3):
    """A rounded box given by its left, right, top and bottom edges."""
    rr = RoundedRectangle(corner_radius=0.14, width=r - l, height=t - b, stroke_color=color, stroke_width=sw)
    rr.set_fill(BLACK if ManimColor(color).to_hex().upper() == "#FFFFFF" else dim(color, k), 1)
    return rr.move_to([(l + r) / 2, (t + b) / 2, 0])


def row(*parts, buff=0.16):
    return VGroup(*parts).arrange(RIGHT, buff=buff)


def card(label, sub, color, w=3.2):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=0.95, stroke_color=color, stroke_width=3).set_fill(dim(color), 1)
    return VGroup(r, T(label, 30).move_to(r), T(sub, 26, GREY_B).next_to(r, DOWN, buff=0.2))


def chip_tok(text, color, size=24, w=None):
    t = T(text, size)
    r = RoundedRectangle(corner_radius=0.1, width=w or t.width + 0.36, height=0.5, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def plate(n):
    t = M(str(n), 24)
    r = RoundedRectangle(corner_radius=0.08, width=0.5, height=0.5, stroke_color=GOLD_M, stroke_width=2.5).set_fill(dim(GOLD_M, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


# one colour per thing, for the whole video
COOK, EMIT, DINER, VAL, CLK = BLUE_M, PURPLE_M, TEAL_M, GOLD_M, GREY_B

# the clock (a vertical timeline on the right: time runs downward)
T0Y, T1Y = 2.35, -3.05
K = (T0Y - T1Y) / 1200
XC, XD, LW, XL = 1.35, 2.3, 0.34, 2.85
COOKS = [(0, 100), (400, 500), (800, 900)]
WAITS = [(100, 400), (500, 800), (900, 1200)]


def ty(ms):
    return T0Y - K * ms


# the call stack (nested boxes on the left)
KITCHEN = np.array([-5.35, 1.3, 0])
P_SPOT = np.array([-4.6, 1.3, 0])     # where a plate appears when its line is read
TABLE = np.array([-5.25, -1.15, 0])
P_TABLE = np.array([-5.25, -0.5, 0])
PLATE_IN = np.array([-3.95, -0.95, 0])
BAR_K = (-4.15, -1.0, 1.3)            # kitchen bar: left, right, y
BAR_D = (-4.25, -1.65, -1.6)          # the diner's bar


class Flow01InsideEmit(Narrated):
    """flow-01 section 3: the collector runs inside emit, so a flow is sequential and a slow collector slows the producer."""

    def construct(self):
        self.title_card("Inside emit", "why a slow collector slows the producer")

        # ================= the problem =================
        rd = card("reader", "100 ms per line", COOK).move_to([-3.7, 1.0, 0])
        rd[2].next_to(rd[0], DOWN, buff=0.2)
        lw = card("ledger writer", "300 ms per posting", DINER, w=3.4).move_to([3.7, 1.0, 0])
        lw[2].next_to(lw[0], DOWN, buff=0.2)
        ar = Arrow(rd[0].get_right(), lw[0].get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        ar_l = T("a plain flow, no buffer", 26, GREY_B).next_to(ar, UP, buff=0.18)
        self.say("open")
        self.play(FadeIn(rd, shift=UP * 0.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lw, shift=UP * 0.15), run_time=0.7)
        self.at(2)
        self.play(GrowArrow(ar), FadeIn(ar_l), run_time=0.8)
        self.hold()

        q1 = row(T("first", 30), M("emit", 30, EMIT), T("at 100 ms", 30))
        q2 = row(T("second", 30), M("emit", 30, EMIT), T("at", 30), T("?", 36, YELLOW_M))
        qa = VGroup(q1, q2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -1.6, 0])
        self.say("q")
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(rd, lw, ar, ar_l, qa)), run_time=0.6)

        # ================= the clock =================
        clock = ValueTracker(0)
        kf, df = ValueTracker(0), ValueTracker(0)     # the kitchen bar and the diner's bar
        hdr = VGroup(T("cook", 22, COOK).move_to([XC, 2.85, 0]), T("diner", 22, DINER).move_to([XD, 2.85, 0]))
        readout = always_redraw(lambda: T(f"t = {int(round(clock.get_value() / 10) * 10)} ms", 26)
                                .move_to([XL, 2.85, 0], aligned_edge=LEFT))
        tracks = VGroup(*[Rectangle(width=LW, height=T0Y - T1Y, stroke_color=GREY_D, stroke_width=1.2).move_to([x, (T0Y + T1Y) / 2, 0])
                          for x in (XC, XD)])

        def lane(intervals, x, color, solid):
            def mk():
                t = clock.get_value()
                g = VGroup()
                for a, b in intervals:
                    if t <= a + 0.5:
                        continue
                    e = min(b, t)
                    r = Rectangle(width=LW - (0 if solid else 0.04), height=K * (e - a),
                                  stroke_color=color, stroke_width=0 if solid else 2)
                    r.set_fill(color if solid else dim(color, 0.3), 0.85 if solid else 1)
                    g.add(r.move_to([x, ty((a + e) / 2), 0]))
                return g
            return always_redraw(mk)

        cook_work = lane(COOKS, XC, COOK, True)
        cook_wait = lane(WAITS, XC, COOK, False)
        eat = lane(WAITS, XD, DINER, True)
        cursor = always_redraw(lambda: Line([XC - LW / 2 - 0.12, ty(clock.get_value()), 0],
                                            [XD + LW / 2 + 0.12, ty(clock.get_value()), 0], stroke_width=2.5, color=WHITE))
        events = {}

        def ev(ms, *parts):
            g = row(T(str(ms), 24, CLK), *parts, buff=0.14).move_to([XL, ty(ms), 0], aligned_edge=LEFT)
            tk = DashedLine([XD + LW / 2 + 0.05, ty(ms), 0], [XL - 0.08, ty(ms), 0], dash_length=0.05, stroke_width=1.5, color=GREY_C)
            events[ms] = VGroup(tk, g)
            return FadeIn(events[ms], shift=LEFT * 0.1)

        def called(n):
            return [M(f"emit({n})", 22, EMIT), T("called", 24)]

        def returns(n):
            return [M(f"emit({n})", 22, EMIT), T("returns", 24)]

        # ================= the stack =================
        c_box = frame(-6.45, 0.55, 2.95, -3.3, WHITE, sw=2.5)
        c_lab = row(T("main calls", 24, GREY_B), M("collect { }", 24)).move_to([-6.2, 2.62, 0], aligned_edge=LEFT)
        f_box = frame(-6.2, 0.3, 2.3, -3.05, COOK, k=0.07)
        f_lab = row(M("flow { }", 24, COOK), T("block: the cook", 26, COOK)).move_to([-5.95, 1.98, 0], aligned_edge=LEFT)
        cook = chip_tok("cook", COOK).move_to(KITCHEN)
        k_lab = T("100 ms", 24, GREY_B).move_to([BAR_K[1] + 0.15, BAR_K[2], 0], aligned_edge=LEFT)
        k_trk = Rectangle(width=BAR_K[1] - BAR_K[0], height=0.2, stroke_color=COOK, stroke_width=1.5).move_to(
            [(BAR_K[0] + BAR_K[1]) / 2, BAR_K[2], 0])
        k_bar = always_redraw(lambda: Rectangle(width=max(0.001, (BAR_K[1] - BAR_K[0]) * kf.get_value()), height=0.2, stroke_width=0)
                              .set_fill(COOK, 0.85).move_to([BAR_K[0], BAR_K[2], 0], aligned_edge=LEFT))

        def emit_box(n):
            box = frame(-5.95, 0.05, 0.85, -2.8, EMIT, k=0.12)
            lab = row(M(f"emit({n}):", 24, EMIT), T("the cook at the table", 26, EMIT)).move_to([-5.7, 0.52, 0], aligned_edge=LEFT)
            return box, lab

        def coll_box(n):
            box = frame(-4.55, -0.2, 0.1, -2.55, DINER, k=0.16)
            lab = T("your collector: the diner", 26, DINER).move_to([-4.3, -0.22, 0], aligned_edge=LEFT)
            code = M(f"ledger.post({n})", 24).move_to([-3.5, PLATE_IN[1], 0], aligned_edge=LEFT)
            trk = Rectangle(width=BAR_D[1] - BAR_D[0], height=0.2, stroke_color=DINER, stroke_width=1.5).move_to(
                [(BAR_D[0] + BAR_D[1]) / 2, BAR_D[2], 0])
            ms = T("300 ms", 24, GREY_B).move_to([-1.45, BAR_D[2], 0], aligned_edge=LEFT)
            return VGroup(box, lab, code, trk, ms)

        d_bar = always_redraw(lambda: Rectangle(width=max(0.001, (BAR_D[1] - BAR_D[0]) * df.get_value()), height=0.2, stroke_width=0)
                              .set_fill(DINER, 0.85).move_to([BAR_D[0], BAR_D[2], 0], aligned_edge=LEFT).set_z_index(3))

        self.say("cook")
        self.add(cook_wait, cook_work, eat)
        self.play(Create(c_box), FadeIn(c_lab), FadeIn(hdr), FadeIn(tracks), FadeIn(cursor), FadeIn(readout), run_time=0.9)
        self.at(1)
        self.play(FadeIn(f_box), FadeIn(f_lab), FadeIn(cook, scale=0.7), run_time=0.8)
        self.at(2)
        self.play(FadeIn(k_lab), FadeIn(k_trk), run_time=0.4)
        self.add(k_bar)
        self.play(clock.animate.set_value(100), kf.animate.set_value(1), run_time=1.8, rate_func=linear)
        self.hold()

        # ---- emit(1): the walk to the table ----
        (e1, e1_l), c1 = emit_box(1), coll_box(1)
        p1 = plate(1).move_to(P_SPOT)
        self.say("walk")
        self.play(FadeIn(p1, scale=0.6), run_time=0.35)
        self.play(FadeIn(e1), ev(100, *called(1)), kf.animate.set_value(0), run_time=0.6)
        self.play(cook.animate.move_to(TABLE), p1.animate.move_to(P_TABLE), run_time=1.0)
        self.play(FadeIn(e1_l), run_time=0.4)
        self.at(1)
        self.play(FadeIn(c1), p1.animate.move_to(PLATE_IN), run_time=0.9)
        self.hold()

        wait_n = T("waits", 22, COOK).next_to(TABLE, DOWN, buff=0.42)
        self.say("stand")
        self.add(d_bar)
        self.play(clock.animate.set_value(260), df.animate.set_value(0.53), run_time=2.6, rate_func=linear)
        self.at(1)
        self.play(clock.animate.set_value(400), df.animate.set_value(1), FadeIn(wait_n),
                  Circumscribe(cook, color=COOK, buff=0.08, run_time=1.4), run_time=2.6, rate_func=linear)
        self.hold()

        # ---- emit(1) returns ----
        self.say("back")
        self.play(Circumscribe(c1[0], color=DINER, buff=0.06), run_time=0.9)
        self.play(FadeOut(VGroup(c1, p1), scale=0.92), df.animate.set_value(0), run_time=0.6)
        self.play(FadeOut(VGroup(e1, e1_l), scale=0.95), FadeOut(wait_n), ev(400, *returns(1)), run_time=0.5)
        self.play(cook.animate.move_to(KITCHEN), run_time=0.5)
        self.at(1)
        self.play(clock.animate.set_value(500), kf.animate.set_value(1), run_time=1.6, rate_func=linear)
        self.at_text("So the second")
        not200 = row(T("200?", 24, RED_M), tick(False, 0.13)).move_to([XL, ty(200), 0], aligned_edge=LEFT)
        self.play(ev(500, *called(2)), run_time=0.5)
        self.at_text("not 200")
        self.play(FadeIn(not200), run_time=0.5)
        self.hold()

        # ---- the same for lines 2 and 3 ----
        self.say("rest")
        self.play(FadeOut(not200), run_time=0.3)

        def serve(n, t_emit, t_back, t_next, rt=1.0):
            (e, el), c, p = emit_box(n), coll_box(n), plate(n).move_to(P_SPOT)
            self.play(FadeIn(p, scale=0.6), FadeIn(e), run_time=0.25 * rt)
            self.play(kf.animate.set_value(0), cook.animate.move_to(TABLE), p.animate.move_to(P_TABLE), run_time=0.5 * rt)
            self.play(FadeIn(el), FadeIn(c), p.animate.move_to(PLATE_IN), run_time=0.4 * rt)
            self.play(clock.animate.set_value(t_back), df.animate.set_value(1), run_time=1.1 * rt, rate_func=linear)
            self.play(FadeOut(VGroup(c, p), scale=0.92), df.animate.set_value(0), run_time=0.3 * rt)
            self.play(FadeOut(VGroup(e, el), scale=0.95), ev(t_back, *returns(n)), run_time=0.3 * rt)
            self.play(cook.animate.move_to(KITCHEN), run_time=0.3 * rt)
            if t_next:
                self.play(clock.animate.set_value(t_next), kf.animate.set_value(1), run_time=0.45 * rt, rate_func=linear)
                self.play(ev(t_next, *called(n + 1)), run_time=0.3 * rt)

        serve(2, 500, 800, 900, rt=0.85)
        serve(3, 900, 1200, None, rt=0.85)
        self.at(2)
        stack = VGroup(c_box, c_lab, f_box, f_lab, cook, k_lab, k_trk)
        self.remove(k_bar, d_bar)
        br = Brace(Line([XC - LW / 2, ty(0), 0], [XC - LW / 2, ty(1200), 0]), direction=LEFT, buff=0.12, color=GREY_B)
        br_l = VGroup(T("3 lines: 1200 ms", 30), T("the writer alone: 900 ms", 26, DINER)).arrange(DOWN, aligned_edge=RIGHT, buff=0.2)
        br_l.next_to(br, LEFT, buff=0.3)
        self.play(FadeOut(stack), FadeOut(cursor), run_time=0.6)
        self.play(GrowFromCenter(br), FadeIn(br_l, shift=LEFT * 0.1), run_time=0.8)
        self.hold()

        # ================= rule 1: sequential =================
        bands = VGroup(*[Rectangle(width=XD - XC + LW + 0.2, height=K * (b - a), stroke_color=EMIT, stroke_width=2)
                         .set_fill(EMIT, 0.16).move_to([(XC + XD) / 2, ty((a + b) / 2), 0]) for a, b in WAITS]).set_z_index(-1)
        r1 = VGroup(T("1. One value at a time", 32),
                    T("line 2 starts only after", 26, GREY_B),
                    row(M("emit(1)", 24, EMIT), T("has returned", 26, GREY_B)),
                    T("the diner holds one plate at a time", 26, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        r1.move_to([-6.2, 1.1, 0], aligned_edge=LEFT)
        self.say("seq")
        self.play(FadeOut(br), FadeOut(br_l), run_time=0.5)
        self.at(1)
        self.play(FadeIn(r1[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r1[1:3], shift=UP * 0.1), FadeIn(bands[0]), run_time=0.7)
        self.play(FadeIn(bands[1:]), run_time=0.6)
        self.at_text("and the diner")
        self.play(FadeIn(r1[3], shift=UP * 0.1), Circumscribe(tracks[1], color=DINER, buff=0.06, run_time=1.4), run_time=1.4)
        self.hold()

        # ================= rule 2: a slow collector slows the producer =================
        cyc = VGroup()
        for a in (0, 400, 800):
            b = Brace(Line([XC - LW / 2, ty(a), 0], [XC - LW / 2, ty(a + 400), 0]), direction=LEFT, buff=0.1, color=COOK)
            cyc.add(VGroup(b, T("400 ms", 24, COOK).next_to(b, LEFT, buff=0.12)))
        r2 = VGroup(T("2. A slow collector", 32), T("slows the producer", 32),
                    T("could read a line every 100 ms", 26, GREY_B),
                    T("reads one every 400 ms", 26, COOK)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        r2[1].shift(UP * 0.08)
        r2.move_to([-6.2, 1.1, 0], aligned_edge=LEFT)
        free = T("backpressure, for free", 30, YELLOW_M).move_to([-6.2, -1.6, 0], aligned_edge=LEFT)
        self.say("bp")
        self.play(FadeOut(r1), FadeOut(bands), run_time=0.5)
        self.play(FadeIn(r2[:2], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2[2], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2[3], shift=UP * 0.1), LaggedStart(*[FadeIn(c) for c in cyc], lag_ratio=0.3), run_time=1.2)
        self.at(3)
        self.play(FadeIn(free, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= where the picture is wrong =================
        r3 = VGroup(T("Where the picture is wrong", 32),
                    T("the waiting cook is a suspended", 26, GREY_B),
                    T("coroutine: it holds no thread", 26, GREY_B),
                    T("the thread runs other coroutines", 26, GREY_B),
                    T("while the diner waits on the ledger", 26, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        r3.move_to([-6.2, 0.6, 0], aligned_edge=LEFT)
        self.say("break")
        self.play(FadeOut(VGroup(r2, free, cyc)), run_time=0.5)
        self.play(FadeIn(r3[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(r3[1:3], shift=UP * 0.1), Indicate(cook_wait, color=YELLOW_M, scale_factor=1.0), run_time=1.2)
        self.at(2)
        self.play(FadeIn(r3[3:], shift=UP * 0.1), run_time=0.7)
        self.hold()
        for m in (cook_wait, cook_work, eat, readout):
            m.clear_updaters()
        self.play(FadeOut(VGroup(r3, hdr, tracks, cook_wait, cook_work, eat, readout, *events.values())), run_time=0.7)

        # ================= the code, last =================
        cw = M("0123456789", 24).width / 10

        def code(lines, hl):
            g = VGroup(*[M(l.lstrip(), 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            for i, l in enumerate(lines):
                g[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return g

        kt = code(["flow {",
                   "    for (line in lines) emit(read(line))    // read: 100 ms",
                   "}.collect { id -> ledger.post(id) }         // 300 ms, inside the call"],
                  {"emit": EMIT, "// read: 100 ms": GREY_B, "// 300 ms, inside the call": GREY_B, "ledger.post": DINER})
        jv = code(["for (String line : lines)",
                   "    ledgerWriter.accept(read(line));        // returns after the post"],
                  {"accept": EMIT, "// returns after the post": GREY_B})
        kg = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        jg = VGroup(T("Java, a hand-written push flow", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(pair, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(jg, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(pair), run_time=0.6)

        # ================= the rule and a check =================
        l1 = row(M("emit", 30, EMIT), T("is a direct call into the collector.", 32))
        l2 = T("A plain flow handles one value at a time,", 32)
        l3 = T("at the speed of its collector.", 32)
        rule = VGroup(l1, l2, l3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a reader needs 50 ms per line, and the writer needs 200 ms.", 28),
                    row(T("When is the second", 28), M("emit", 28, EMIT), T("?", 28), buff=0.12)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.6)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(l1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(VGroup(l2, l3), shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
