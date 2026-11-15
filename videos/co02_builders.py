from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bkotlinx\.coroutines\b", "kotlin X co-routines"), (r"\bcoroutineScope\b", "co-routine scope"),
              (r"\bcoroutine", "co-routine"), (r"\bawaitAll\b", "await all"), (r"\bfjord-fx\b", "fjord F X"),
              (r"\bFX\b", "F X")]

# every spoken line, in order
N = {
    "open": "Three FX providers answer in 300, 120 and 200 milliseconds. "
            "Ask them one after another, and the caller waits 620 milliseconds.",
    "lanes": "But the calls don't need each other. Start all three at once, and you wait only for the slowest: 300.",
    "launch": "In Kotlin, a builder starts each lane: a plain function that starts a coroutine. "
              "launch starts a child and returns at once, with a Job: a handle you can join or cancel.",
    "job": "A Job holds no value. So launch is for work whose result you don't need.",
    "async": "async is launch with a result. It also returns at once, with a Deferred: a ticket for a value that isn't there yet.",
    "await": "awaitAll suspends the caller and frees its thread. Each ticket fills when its call answers. "
             "Done at 300 milliseconds, the slowest call.",
    "mistake_q": "Now await each call right after you start it. How long does it take?",
    "mistake": "Each await ends before the next async starts, so the calls run one at a time: 620 again. "
               "The overlap lives in the gap between async and await.",
    "scope": "Every child needs a parent. In a suspend function, that's coroutineScope.",
    "scope_q": "Its block launches three calls and awaits nothing, so the block ends right away. When does coroutineScope return?",
    "scope_a": "The scope can't close while a child still runs, even one that nobody awaited. So it returns at 300. "
               "When a suspend function returns, the work it started is done.",
    "fail": "If fjord-fx throws at 120, the scope cancels the other two, waits for them to stop, and rethrows. "
            "The call fails at 120.",
    "code": "This is Kotlin only. The builders come from kotlinx.coroutines.",
    "rule": "So launch and async start a child and return at once. await waits for one value. "
            "coroutineScope waits for every child before it returns.",
    "check": "Quick check. In coroutineScope, you async a 300 millisecond quote, launch a 500 millisecond audit write, "
             "and await only the quote. When does the scope return?",
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


def later(delay, anim):
    """Play anim after delay seconds, inside an AnimationGroup (no-op filler, not Wait, which has no mobject)."""
    if delay < 0.02:
        return anim
    return Succession(Animation(Mobject(), run_time=delay), anim)


# one colour per thing, for the whole video
CALLER, CHILD, TICKET, SCOPE, WAIT, FAIL, CANCEL = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREY_M, RED_M, YELLOW_M

X0, K = -3.7, 9.6 / 650          # x of t = 0 ms, and units per ms


def X(t):
    return X0 + K * t


Y_HAND, Y_FLAB, Y_FTOP, Y_STATE, Y_CALLER = 3.0, 2.45, 2.15, 1.83, 1.4
Y_LANES = [0.45, -0.3, -1.05]
Y_FBOT, Y_AXIS, Y_RES = -1.4, -1.75, -2.75
NAMES = ["northbank", "fjord-fx", "tidewater"]
MS = [300, 120, 200]
RATES = ["1.0842", "1.0839", "1.0845"]


def chip(text, color, mono=False, w=1.6):
    t = (M if mono else T)(text, 24)
    r = RoundedRectangle(corner_radius=0.08, width=w, height=0.5, stroke_color=color, stroke_width=2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def hand(i):
    return np.array([X0 + 0.8 + 1.8 * i, Y_HAND, 0])


class Co02Builders(Narrated):
    """co-02 section 2 (with sections 0 and 1): launch and async return at once; coroutineScope waits for its children (Kotlin only)."""

    def construct(self):
        self.title_card("What returns when?", "launch, async and coroutineScope in Kotlin")

        tm = ValueTracker(0)
        segs = []           # timeline pieces, drawn up to the current time
        frame_end = [None]  # scope frame closes here (ms); None = no frame

        def draw():
            t = tm.get_value()
            g = VGroup()
            for s in segs:
                if t <= s["t0"] + 1e-6:
                    continue
                e = min(t, s["t1"])
                w = K * (e - s["t0"])
                if w < 0.02:
                    continue
                col = s["color"]
                if s["kind"] == "bar":
                    r = Rectangle(width=w, height=0.36, stroke_color=col, stroke_width=2).set_fill(dim(col, 0.5), 1)
                    g.add(r.move_to([X(s["t0"]), s["y"], 0], aligned_edge=LEFT))
                else:  # waiting: a dashed grey stretch
                    g.add(DashedLine([X(s["t0"]), s["y"], 0], [X(e), s["y"], 0], dash_length=0.1, stroke_width=5, color=col))
            if frame_end[0] is not None and frame_op.get_value() > 0.01:
                fe = min(t, frame_end[0])
                xl, xr = X0 - 0.15, X(fe) + 0.15
                pts = [[xr, Y_FTOP, 0], [xl, Y_FTOP, 0], [xl, Y_FBOT, 0], [xr, Y_FBOT, 0]]
                if t >= frame_end[0] - 1e-6:      # closed: the scope has returned
                    pts.append([xr, Y_FTOP, 0])
                fr = VMobject(stroke_color=frame_col[0], stroke_width=3).set_points_as_corners(pts)
                g.add(fr.set_stroke(opacity=frame_op.get_value()))
            return g if len(g) else VMobject()

        frame_col = [SCOPE]
        frame_op = ValueTracker(0)
        timeline = always_redraw(draw)
        cursor = always_redraw(lambda: Line([X(tm.get_value()), Y_CALLER + 0.25, 0], [X(tm.get_value()), Y_FBOT + 0.05, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.35 if tm.get_value() > 0.5 else 0))

        def run(t1, rt, events=()):
            """Move time to t1 over rt seconds; each (ms, anim) event starts when the clock passes ms."""
            t0 = tm.get_value()
            anims = [tm.animate(run_time=rt, rate_func=linear).set_value(t1)]
            for te, anim in events:
                anims.append(later(rt * (te - t0) / (t1 - t0), anim))
            self.play(AnimationGroup(*anims))

        def reveal(m):
            """Show m at its turn inside a group: add it invisible now, fade it in later (avoids the FadeIn trap)."""
            tgt = m.copy()
            m.set_opacity(0)
            self.add(m)
            return Transform(m, tgt, run_time=0.35)

        def wipe(*extra):
            """Fade out what the timeline drew so far (and extra mobjects), then reset the clock to 0."""
            static = draw()
            segs.clear()
            tm.set_value(0)
            self.add(static)
            self.play(FadeOut(static), *[FadeOut(m) for m in extra], run_time=0.5)

        # ---------- the lanes and the clock ----------
        lane_c = DashedLine([X0, Y_CALLER, 0], [X(650), Y_CALLER, 0], dash_length=0.07, stroke_width=1.5, color=GREY_D)
        lab_c = T("caller", 28, CALLER).move_to([X0 - 0.35, Y_CALLER, 0], aligned_edge=RIGHT)
        lanes = [DashedLine([X0, y, 0], [X(650), y, 0], dash_length=0.07, stroke_width=1.5, color=GREY_D) for y in Y_LANES]
        labs = [T(n, 26, CHILD).move_to([X0 - 0.35, y, 0], aligned_edge=RIGHT) for n, y in zip(NAMES, Y_LANES)]
        axis = VGroup(Line([X0, Y_AXIS, 0], [X(650), Y_AXIS, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 601, 100):
            axis.add(Line([X(ms), Y_AXIS - 0.06, 0], [X(ms), Y_AXIS + 0.06, 0], stroke_width=1.5, color=GREY_D))
            axis.add(T(f"{ms}" + (" ms" if ms == 600 else ""), 22, GREY_B).move_to([X(ms) + (0.2 if ms == 600 else 0), Y_AXIS - 0.32, 0]))

        # ================= the problem: one after another =================
        seq_t = [0, 300, 420, 620]
        seq = [Rectangle(width=K * MS[i] - 0.03, height=0.36, stroke_color=CHILD, stroke_width=2).set_fill(dim(CHILD, 0.5), 1)
               .move_to([X(seq_t[i]) + 0.015, Y_CALLER, 0], aligned_edge=LEFT) for i in range(3)]
        seq_l = [T(f"{NAMES[i]} {MS[i]}", 22).move_to(seq[i]) for i in range(3)]
        res_seq = T("one after another: 620 ms", 28, FAIL).move_to([0.8, Y_RES, 0])

        self.say("open")
        self.play(FadeIn(lab_c), Create(lane_c), FadeIn(axis), run_time=0.9)
        self.at_text("answer in")
        self.play(LaggedStart(*[FadeIn(VGroup(labs[i], lanes[i])) for i in range(3)], lag_ratio=0.5), run_time=1.6)
        self.at_text("Ask them")
        for i in range(3):
            self.play(GrowFromEdge(seq[i], LEFT), run_time=0.45 + MS[i] / 300, rate_func=linear)
            self.add(seq_l[i])
        self.play(FadeIn(res_seq, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # the same three calls, each in its own lane, all started at 0
        res_par = T("all at once: the slowest, 300 ms", 28, GREEN_M).move_to([0.8, Y_RES, 0])
        line300 = DashedLine([X(300), Y_FTOP - 0.05, 0], [X(300), Y_FBOT + 0.05, 0], dash_length=0.08, stroke_width=2, color=GREEN_M)
        self.say("lanes")
        self.at_text("Start all")
        self.play(*[VGroup(seq[i], seq_l[i]).animate.move_to([X(0) + 0.015, Y_LANES[i], 0], aligned_edge=LEFT) for i in range(3)],
                  run_time=1.6)
        self.at_text("and you wait")
        self.play(Create(line300), FadeOut(res_seq), FadeIn(res_par, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(*seq, *seq_l, line300, res_par)), run_time=0.6)

        # ================= launch: start a child, return at once with a Job =================
        self.add(timeline, cursor)
        fork = VGroup(Line([X0, Y_CALLER, 0], [X0, Y_LANES[2], 0], stroke_width=2.5, color=GREY_B),
                      *[Dot([X0, y, 0], radius=0.07, color=GREY_B) for y in Y_LANES], Dot([X0, Y_CALLER, 0], radius=0.07, color=CALLER))
        fork.set_z_index(4)
        jobs = [chip("Job", WHITE).move_to([X0 + 0.3, y, 0]) for y in Y_LANES]
        held = T("the caller holds:", 22, GREY_B).move_to([X0 - 0.35, Y_HAND, 0], aligned_edge=RIGHT)
        st_go = T("carries on", 24, CALLER).move_to([X(60), Y_STATE, 0])
        nov = T("a handle, no value inside", 22, GREY_B).next_to(VGroup(*[Dot(hand(i)) for i in range(3)]), RIGHT, buff=0.9)
        self.say("launch")
        self.at_text("launch starts")
        self.play(Create(fork), run_time=0.7)
        self.at_text("and returns")
        self.play(FadeIn(held), *[FadeIn(j, scale=0.7) for j in jobs], run_time=0.4)
        self.play(*[j.animate.move_to(hand(i)) for i, j in enumerate(jobs)], run_time=0.8)
        segs[:] = [dict(kind="bar", y=Y_CALLER, t0=0, t1=1e9, color=CALLER)] + \
                  [dict(kind="bar", y=Y_LANES[i], t0=0, t1=MS[i], color=CHILD) for i in range(3)]
        run(110, 1.6, [(5, reveal(st_go))])
        self.hold()

        self.say("job")
        self.play(FadeIn(nov, shift=LEFT * 0.1), *[Indicate(j[1], color=WHITE) for j in jobs], run_time=1.0)
        self.hold()

        # ================= async: the same, plus a ticket for the value =================
        tickets = [chip("Deferred", TICKET).move_to(hand(i)) for i in range(3)]
        wipe(st_go, nov)
        self.say("async")
        self.at_text("It also returns")
        self.play(*[Transform(jobs[i], tickets[i]) for i in range(3)], run_time=0.9)
        self.hold()

        st_wait = VGroup(T("suspended in awaitAll", 24, WAIT), T("(the thread is free)", 22, GREY_B)).arrange(RIGHT, buff=0.2)
        st_wait.move_to([X(200), Y_STATE, 0])
        st_back = T("has all three", 24, CALLER).move_to([X(300) + 0.2, Y_STATE, 0], aligned_edge=LEFT)
        vals = [chip(RATES[i], TICKET, mono=True).move_to(hand(i)) for i in range(3)]
        for v in vals:
            v[0].set_fill(dim(TICKET, 0.55), 1)
        segs[:] = [dict(kind="wait", y=Y_CALLER, t0=0, t1=300, color=WAIT), dict(kind="bar", y=Y_CALLER, t0=300, t1=1e9, color=CALLER)] + \
                  [dict(kind="bar", y=Y_LANES[i], t0=0, t1=MS[i], color=CHILD) for i in range(3)]
        res_ok = T("done at 300 ms: the slowest call", 28, GREEN_M).move_to([0.8, Y_RES, 0])
        self.say("await")
        self.play(reveal(st_wait), run_time=0.5)
        run(360, 4.6, [(120, Transform(jobs[1], vals[1], run_time=0.3)), (200, Transform(jobs[2], vals[2], run_time=0.3)),
                       (300, Transform(jobs[0], vals[0], run_time=0.3)), (305, FadeOut(st_wait, run_time=0.3)),
                       (310, reveal(st_back))])
        self.at(2)
        self.play(FadeIn(res_ok, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the classic mistake: await right after async =================
        wipe(*jobs, held, st_back, res_ok, fork)
        code_m = VGroup(M("async { northbank.quote() }.await()", 24, CALLER),
                        M("async { fjord.quote() }.await()", 24, CALLER),
                        M("async { tidewater.quote() }.await()", 24, CALLER)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        code_m.move_to([X(250), Y_HAND - 0.25, 0])
        self.say("mistake_q")
        self.play(FadeIn(code_m, shift=DOWN * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict()

        forks = [VGroup(Line([X(t), Y_CALLER, 0], [X(t), Y_LANES[i], 0], stroke_width=2.5, color=GREY_B),
                        Dot([X(t), Y_LANES[i], 0], radius=0.07, color=GREY_B)).set_z_index(4)
                 for i, t in enumerate(seq_t[:3])]
        segs[:] = [dict(kind="wait", y=Y_CALLER, t0=0, t1=620, color=WAIT), dict(kind="bar", y=Y_CALLER, t0=620, t1=1e9, color=CALLER)] + \
                  [dict(kind="bar", y=Y_LANES[i], t0=seq_t[i], t1=seq_t[i + 1], color=CHILD) for i in range(3)]
        res_bad = T("done at 620 ms: one call at a time", 28, FAIL).move_to([0.8, Y_RES, 0])
        self.say("mistake")
        run(640, 4.6, [(0, reveal(forks[0])), (300, reveal(forks[1])),
                       (420, reveal(forks[2])), (625, reveal(res_bad))])
        self.at(1)
        self.play(Indicate(code_m, color=YELLOW_M, scale_factor=1.03), run_time=1.2)
        self.hold()
        wipe(code_m, res_bad, *forks)

        # ================= coroutineScope: the parent waits for every child =================
        f_lab = M("coroutineScope {", 26, SCOPE).move_to([X0 - 0.15, Y_FLAB, 0], aligned_edge=LEFT)
        frame_end[0] = 300
        self.say("scope")
        self.at_text("In a suspend")
        self.play(frame_op.animate.set_value(1), FadeIn(f_lab), run_time=1.0)
        self.hold()

        jobs = [chip("Job", WHITE).move_to(hand(i)) for i in range(3)]
        st_block = T("block done", 24, CALLER).move_to([X(10), Y_STATE, 0], aligned_edge=LEFT)
        self.say("scope_q")
        self.play(Create(fork), FadeIn(held), *[FadeIn(j, scale=0.7) for j in jobs], run_time=0.8)
        self.at_text("so the block")
        segs[:] = [dict(kind="bar", y=Y_CALLER, t0=0, t1=12, color=CALLER)]
        self.play(tm.animate.set_value(12), FadeIn(st_block), run_time=0.5)
        self.hold(after=0)
        self.predict()

        # the frame grows with time and closes only when the last child is done
        segs[:] = [dict(kind="bar", y=Y_CALLER, t0=0, t1=12, color=CALLER), dict(kind="wait", y=Y_CALLER, t0=12, t1=300, color=WAIT),
                   dict(kind="bar", y=Y_CALLER, t0=300, t1=1e9, color=CALLER)] + \
                  [dict(kind="bar", y=Y_LANES[i], t0=0, t1=MS[i], color=CHILD) for i in range(3)]
        st_wait2 = T("suspended in coroutineScope", 24, WAIT).move_to([X(160), Y_STATE, 0])
        st_ret = T("returns", 24, CALLER).move_to([X(300) + 0.4, Y_STATE, 0], aligned_edge=LEFT)
        res_scope = T("coroutineScope returns at 300 ms", 28, SCOPE).move_to([0.8, Y_RES, 0])
        self.say("scope_a")
        run(370, 4.0, [(14, FadeOut(st_block, run_time=0.3)), (40, reveal(st_wait2)), (300, FadeOut(st_wait2, run_time=0.3)),
                       (302, reveal(st_ret)), (305, reveal(res_scope))])
        self.hold()

        # ================= failure: the same path, in reverse =================
        frame_end[0] = None
        wipe(st_ret, res_scope)
        frame_end[0] = 120
        segs[:] = [dict(kind="bar", y=Y_CALLER, t0=0, t1=12, color=CALLER), dict(kind="wait", y=Y_CALLER, t0=12, t1=120, color=WAIT)] + \
                  [dict(kind="bar", y=Y_LANES[i], t0=0, t1=MS[i], color=CHILD) for i in range(3)]
        tm.set_value(12)
        boom = T("throws", 24, FAIL).move_to([X(120) + 0.2, Y_LANES[1], 0], aligned_edge=LEFT)
        canc = [T("cancelled", 24, CANCEL).move_to([X(120) + 0.2, Y_LANES[i], 0], aligned_edge=LEFT) for i in (0, 2)]
        st_re = T("rethrows", 24, FAIL).move_to([X(120) + 0.2, Y_CALLER, 0], aligned_edge=LEFT)
        res_fail = T("the call fails at 120 ms", 28, FAIL).move_to([0.8, Y_RES, 0])
        self.say("fail")
        run(120, 2.0)
        segs[3]["color"] = FAIL
        self.play(FadeIn(boom), Flash([X(120), Y_LANES[1], 0], color=FAIL, flash_radius=0.45), run_time=0.6)
        self.at_text("the scope cancels")
        for i in (2, 4):
            segs[i]["color"] = CANCEL
            segs[i]["t1"] = 120
        self.play(*[FadeIn(c) for c in canc], run_time=0.6)
        self.at_text("and rethrows")
        frame_col[0] = FAIL
        segs[1]["t1"] = 120
        self.play(FadeIn(st_re), FadeIn(res_fail, shift=UP * 0.1), run_time=0.6)
        self.hold()
        static = draw()
        self.remove(timeline, cursor)
        self.add(static)
        everything = VGroup(*[m for m in self.mobjects if isinstance(m, VMobject)])
        self.play(FadeOut(everything), run_time=0.6)
        self.clear()

        # ================= the code, last =================
        cw = M("0123456789", 26).width / 10
        src = ["suspend fun allQuotes(pair: String) = coroutineScope {",
               "    val pending = providers.map { p ->",
               "        async { p.quote(pair) }     // starts, returns at once",
               "    }",
               "    pending.awaitAll()              // waits for the slowest",
               "}                                   // every child is done"]
        hl = {"coroutineScope": SCOPE, "async": CHILD, "awaitAll": CALLER}
        lines = VGroup(*[M(l.lstrip(), 26, t2c=hl) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        for i, l in enumerate(src):
            lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
        code = VGroup(T("Kotlin only (kotlinx.coroutines)", 24, GREY_B), lines).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(code, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(code, shift=UP * 0.15), run_time=0.9)
        self.hold(after=1.8)
        self.play(FadeOut(code), run_time=0.6)

        # ================= the rule and a check =================
        r1 = VGroup(M("launch", 30, CHILD), T("and", 32), M("async", 30, CHILD), T("start a child and return at once.", 32)).arrange(RIGHT, buff=0.2)
        r2 = VGroup(M("await", 30, CALLER), T("waits for one value.", 32)).arrange(RIGHT, buff=0.2)
        r3 = VGroup(M("coroutineScope", 30, SCOPE), T("waits for every child before it returns.", 32)).arrange(RIGHT, buff=0.2)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        q = VGroup(T("Check:", 28, YELLOW_M),
                   T("inside coroutineScope: async a 300 ms quote, launch a 500 ms audit write.", 28),
                   T("You await only the quote. When does the scope return?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(q, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
