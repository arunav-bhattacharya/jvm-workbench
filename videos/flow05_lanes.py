from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bflatMapConcat\b", "flat map concat"), (r"\bflatMapMerge\b", "flat map merge"),
              (r"\bflatMapLatest\b", "flat map latest"), (r"\bflatMaps\b", "flat maps"), (r"\bflatMap\b", "flat map"),
              (r"\bpart a\b", "part A"), (r"\bpart b\b", "part B"),
              (r"\b([1-3])([ab])\b", lambda m: f"{m.group(1)} {m.group(2).upper()}"), (r"\bm([1-5])\b", r"M \1")]

# every spoken line, in order
N = {
    "open": "Three picks reach a search box, 100 milliseconds apart. Each pick starts an inner flow: "
            "part a after 50 milliseconds, part b 150 later. The flatMaps differ in their lanes.",
    "concat_q": "flatMapConcat has one lane. When does the outer flow emit pick 2?",
    "concat": "Not at 100. The inner flow runs inside the outer's emit, so the outer is stuck until inner 1 is done. "
              "Only then does its delay start. Pick 2 comes at 300, and the run takes 800.",
    "merge": "flatMapMerge gives each inner flow its own lane. Picks come at 0, 100 and 200, "
             "and values come out as they finish: 1b after 2a. Done at 400.",
    "latest": "flatMapLatest has one lane and a switch. A new pick cancels the inner flow in the lane, waits for it to stop, "
              "and starts the next. 1b and 2b never arrive. That is the shape for search as you type.",
    "fee_q": "Now a fee fan-out. Five lookups take 300, 100, 200, 50 and 150 milliseconds, "
             "and the fee service allows two calls at once. A teammate calls the lookup in the flatMapMerge lambda. "
             "How long does it take?",
    "fee_slow": "800 milliseconds, one call at a time. The lambda runs in the one coroutine that reads the merchants, "
                "before any lane is taken. Picture a toll plaza where the dispatcher inspects every car himself. "
                "The booths sit empty.",
    "fee_fast": "Move the lookup inside the flow you return. Now the dispatcher only waves cars in, and the lookups run "
                "in the lanes. Two at a time, done at 450. Results come out as they finish, m2 first.",
    "code": "The slow call goes inside the returned flow. Reactor has the same trap: "
            "block in the mapper, and flatMap runs one call at a time.",
    "rule": "So flatMapConcat runs one lane and makes the outer wait. flatMapMerge gives each returned flow a lane. "
            "flatMapLatest keeps one lane and cuts the old one.",
    "check": "Quick check. Ten merchants, 100 milliseconds each, four lanes, and the lookup inside the returned flow. "
             "How long does it take?",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=1.9):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video: each pick and its inner flow, the outer, lookups, cuts
PICK = {1: TEAL_M, 2: GOLD_M, 3: PURPLE_M}
OUTER, FEE, CUT, NOTE, WAIT = BLUE_M, GOLD_M, RED_M, GREY_B, GREY_M

YH, YP, YO, YA, YN = 3.15, 2.2, -1.45, -2.3, -3.05
YL = [1.2, 0.4, -0.4]
X0, K = -4.6, 10.5 / 800
LX = X0 - 0.35          # right edge of the row labels


def X(ms):
    return X0 + K * ms


def marble(text, color, r=0.26, size=22):
    c = Circle(radius=r, stroke_width=0).set_fill(color, 1)
    return VGroup(c, M(text, size, BLACK).move_to(c)).set_z_index(4)


def ghost(text, color, r=0.26):
    c = DashedVMobject(Circle(radius=r, color=color, stroke_width=2), num_dashes=14)
    return VGroup(c, M(text, 22, color).move_to(c)).set_z_index(4)


def live_bar(tm, a, b, color, y, h=0.42, op=0.8, pad=0.03):
    """A bar on a row that grows with the clock from a to b, then stays."""
    def build():
        t = min(max(tm.get_value(), a), b)
        w = K * (t - a) - (2 * pad if t >= b else pad)
        r = Rectangle(width=max(w, 0.001), height=h, stroke_width=0).set_fill(color, op if w > 0.01 else 0)
        return r.move_to([X(a) + pad, y, 0], aligned_edge=LEFT)
    return always_redraw(build)


def bar_label(a, b, text, y, color=BLACK, size=22):
    return T(text, size, color).move_to([(X(a) + X(b)) / 2, y, 0]).set_z_index(3)


class Flow05Lanes(Narrated):
    """flow-05 sections 1 and 0: flatMapConcat, flatMapMerge and flatMapLatest drawn as lanes on one clock,
    and the fee fan-out where only the returned flow gets a lane."""

    def construct(self):
        self.title_card("Lanes for inner flows", "flatMapConcat, flatMapMerge and flatMapLatest in Kotlin Flow")

        # ---------------- the stage: a clock and rows ----------------
        axis = VGroup(Line([X(0), YA, 0], [X(800), YA, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 801, 100):
            axis.add(Line([X(ms), YA - 0.07, 0], [X(ms), YA + 0.07, 0], stroke_width=1.5, color=GREY_D))
            axis.add(T(str(ms), 22, NOTE).move_to([X(ms), YA - 0.33, 0]))
        axis.add(T("ms", 22, NOTE).move_to([X(800) + 0.45, YA - 0.33, 0]))

        def row_line(y):
            return DashedLine([X(0), y, 0], [X(800), y, 0], dash_length=0.06, stroke_width=1.2, color=GREY_D)

        def row_lab(text, y, color=NOTE):
            return T(text, 26, color).move_to([LX, y, 0], aligned_edge=RIGHT)

        r_picks, l_picks = row_line(YP), row_lab("picks", YP, OUTER)
        r_lane = [row_line(y) for y in YL]
        l_lane = [row_lab("lane", YL[0]), row_lab("lane 2", YL[1]), row_lab("lane 3", YL[2])]
        r_out, l_out = row_line(YO), row_lab("output", YO)

        tm = ValueTracker(0)
        cursor = always_redraw(lambda: Line([X(tm.get_value()), YP + 0.45, 0], [X(tm.get_value()), YO - 0.4, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.35 if tm.get_value() > 1 else 0))

        def to(ms, speed=260.0):
            dt = ms - tm.get_value()
            if dt > 0.5:
                self.play(tm.animate.set_value(ms), run_time=dt / speed, rate_func=linear)

        def header(name, desc):
            return VGroup(M(name, 30, WHITE), T(desc, 26, NOTE)).arrange(RIGHT, buff=0.4).move_to([-6.4, YH, 0], aligned_edge=LEFT)

        def out(text, ms, color, dy=0.0):
            m = marble(text, color, r=0.24).move_to([X(ms), YO + dy, 0])
            return m

        def lane_dot(ms, y):
            return Dot([X(ms), y, 0], radius=0.07, color=WHITE).set_z_index(5)

        self.say("open")
        self.play(FadeIn(axis), Create(r_picks), FadeIn(l_picks), run_time=0.8)
        picks0 = VGroup(*[marble(str(n), PICK[n]).move_to([X(100 * (n - 1)), YP, 0]) for n in (1, 2, 3)])
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in picks0], lag_ratio=0.3), run_time=1.0)
        self.at(1)
        # one inner flow, drawn once as a sample: part a at +50, part b at +200
        sample_bar = Rectangle(width=K * 200 - 0.06, height=0.42, stroke_width=0).set_fill(PICK[1], 0.8)
        sample_bar.move_to([X(0) + 0.03, YL[0], 0], aligned_edge=LEFT)
        s_a, s_b = lane_dot(50, YL[0]), lane_dot(200, YL[0])
        s_la = T("a at +50", 22, NOTE).next_to(s_a, DOWN, buff=0.3)
        s_lb = T("b at +200", 22, NOTE).next_to(s_b, DOWN, buff=0.3).shift(RIGHT * 0.35)
        s_lab = T("inner flow 1", 22, NOTE).next_to(sample_bar, RIGHT, buff=0.3)
        self.play(FadeIn(sample_bar), FadeIn(s_lab), run_time=0.6)
        self.play(FadeIn(s_a), FadeIn(s_la), run_time=0.4)
        self.play(FadeIn(s_b), FadeIn(s_lb), run_time=0.4)
        self.at(2)
        self.play(Create(r_lane[0]), FadeIn(l_lane[0]), Create(r_out), FadeIn(l_out), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(sample_bar, s_a, s_b, s_la, s_lb, s_lab, picks0)), run_time=0.5)
        self.add(cursor)

        # ================= flatMapConcat: one lane, the outer waits =================
        h = header("flatMapConcat", "one lane")
        self.say("concat_q")
        self.play(FadeIn(h, shift=DOWN * 0.1), run_time=0.6)
        p1 = marble("1", PICK[1]).move_to([X(0), YP, 0])
        self.play(FadeIn(p1, scale=0.6), run_time=0.4)
        self.hold(after=0)
        self.predict()

        bars = [live_bar(tm, 0, 200, PICK[1], YL[0]), live_bar(tm, 300, 500, PICK[2], YL[0]), live_bar(tm, 600, 800, PICK[3], YL[0])]
        waits = [live_bar(tm, a, a + 200, WAIT, YP, h=0.16, op=0.9, pad=0.0) for a in (0, 300, 600)]
        stuff = VGroup()
        self.say("concat")
        self.add(*bars, *waits)
        to(50)
        o = out("1a", 50, PICK[1])
        d = lane_dot(50, YL[0])
        self.play(FadeIn(o, scale=0.6), FadeIn(d), run_time=0.3)
        stuff.add(o, d)
        to(100)
        g2 = ghost("2", PICK[2]).move_to([X(100), YP, 0])
        self.play(FadeIn(g2), run_time=0.3)
        self.at_text("so the outer")
        w_lab = T("outer waits inside emit", 22, NOTE).move_to([X(100), YP + 0.55, 0])
        self.play(FadeIn(w_lab), run_time=0.4)
        to(200, speed=150)
        o = out("1b", 200, PICK[1])
        d = lane_dot(200, YL[0])
        il = bar_label(0, 200, "inner 1", YL[0])
        self.play(FadeIn(o, scale=0.6), FadeIn(d), FadeIn(il), run_time=0.3)
        stuff.add(o, d, il)
        self.at(2)
        to(300, speed=110)
        p2 = marble("2", PICK[2]).move_to([X(300), YP, 0])
        self.play(g2.animate.move_to([X(300), YP, 0]), run_time=0.4)
        self.remove(g2)
        self.add(p2)
        self.at(3)
        for ms, lab, n in ((350, "2a", 2), (500, "2b", 2), (600, None, 3), (650, "3a", 3), (800, "3b", 3)):
            to(ms, speed=330)
            if lab:
                o = out(lab, ms, PICK[n])
                d = lane_dot(ms, YL[0])
                self.play(FadeIn(o, scale=0.6), FadeIn(d), run_time=0.25)
                stuff.add(o, d)
            else:
                p3 = marble("3", PICK[3]).move_to([X(600), YP, 0])
                self.play(FadeIn(p3, scale=0.6), run_time=0.25)
        done = T("done at 800 ms", 26, WHITE).move_to([0.5, YN, 0])
        self.play(FadeIn(done), run_time=0.4)
        self.hold()
        for b in bars + waits:
            b.clear_updaters()
        self.play(FadeOut(VGroup(*bars, *waits, stuff, p1, p2, p3, w_lab, done, h)), run_time=0.6)
        tm.set_value(0)

        # ================= flatMapMerge: a lane per inner flow =================
        h = header("flatMapMerge", "a lane per inner flow")
        bars = [live_bar(tm, 100 * i, 100 * i + 200, PICK[i + 1], YL[i]) for i in range(3)]
        picks = {n: marble(str(n), PICK[n]).move_to([X(100 * (n - 1)), YP, 0]) for n in (1, 2, 3)}
        outs = {}
        self.say("merge")
        self.play(FadeIn(h, shift=DOWN * 0.1), Transform(l_lane[0], row_lab("lane 1", YL[0])),
                  Create(r_lane[1]), FadeIn(l_lane[1]), Create(r_lane[2]), FadeIn(l_lane[2]), run_time=0.8)
        self.at(1)
        self.add(*bars)
        events = [(0, "p", 1), (50, "1a", 1), (100, "p", 2), (150, "2a", 2), (200, "p", 3), (200, "1b", 1),
                  (250, "3a", 3), (300, "2b", 2), (400, "3b", 3)]
        stuff = VGroup()
        for ms, what, n in events:
            to(ms, speed=150)
            if what == "p":
                self.play(FadeIn(picks[n], scale=0.6), run_time=0.25)
            else:
                o = out(what, ms, PICK[n])
                outs[what] = o
                d = lane_dot(ms, YL[n - 1])
                self.play(FadeIn(o, scale=0.6), FadeIn(d), run_time=0.25)
                stuff.add(d)
        self.at_text("1b after")
        self.play(Indicate(outs["2a"], color=WHITE, scale_factor=1.3), Indicate(outs["1b"], color=WHITE, scale_factor=1.3),
                  run_time=0.9)
        self.at_text("Done at")
        done = T("done at 400 ms", 26, WHITE).move_to([0.5, YN, 0])
        self.play(FadeIn(done), run_time=0.4)
        self.hold()
        for b in bars:
            b.clear_updaters()
        self.play(FadeOut(VGroup(*bars, stuff, *outs.values(), *picks.values(), done, h)),
                  FadeOut(VGroup(r_lane[1], r_lane[2], l_lane[1], l_lane[2])), Transform(l_lane[0], row_lab("lane", YL[0])),
                  run_time=0.6)
        tm.set_value(0)

        # ================= flatMapLatest: one lane and a switch =================
        h = header("flatMapLatest", "one lane, a new pick cuts the old one")
        bars = [live_bar(tm, 0, 100, PICK[1], YL[0]), live_bar(tm, 100, 200, PICK[2], YL[0]), live_bar(tm, 200, 400, PICK[3], YL[0])]
        picks = {n: marble(str(n), PICK[n]).move_to([X(100 * (n - 1)), YP, 0]) for n in (1, 2, 3)}
        stuff = VGroup()
        self.say("latest")
        self.play(FadeIn(h, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.add(*bars)
        events = [(0, "p", 1), (50, "1a", 1), (100, "p", 2), (150, "2a", 2), (200, "p", 3), (250, "3a", 3), (400, "3b", 3)]
        for ms, what, n in events:
            to(ms, speed=150)
            if what == "p":
                anims = [FadeIn(picks[n], scale=0.6)]
                if n > 1:
                    cut = Line([X(ms), YL[0] - 0.36, 0], [X(ms), YL[0] + 0.36, 0], stroke_width=6, color=CUT).set_z_index(5)
                    clab = T("cut", 22, CUT).next_to(cut, DOWN, buff=0.08)
                    anims += [Create(cut), FadeIn(clab)]
                    stuff.add(cut, clab)
                self.play(*anims, run_time=0.3)
            else:
                o = out(what, ms, PICK[n])
                d = lane_dot(ms, YL[0])
                self.play(FadeIn(o, scale=0.6), FadeIn(d), run_time=0.25)
                stuff.add(o, d)
        self.at(2)
        lost = VGroup()
        for lab, ms, n in (("1b", 200, 1), ("2b", 300, 2)):
            gh = ghost(lab, PICK[n], r=0.24).move_to([X(ms), YO, 0]).set_opacity(0.6)
            x = tick(False, 0.22).move_to(gh).set_z_index(6)
            lost.add(gh, x)
        self.play(FadeIn(lost), run_time=0.6)
        done = T("done at 400 ms", 26, WHITE).move_to([0.5, YN, 0])
        self.play(FadeIn(done), run_time=0.4)
        self.hold()
        for b in bars:
            b.clear_updaters()
        self.remove(cursor)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        tm.set_value(0)

        # ================= the fee fan-out: what gets a lane =================
        def fee_bar(a, b, y, name):
            g = VGroup(live_bar(tm, a, b, FEE, y))
            return g, bar_label(a, b, name, y)

        r_disp, l_disp = row_line(YP), row_lab("dispatcher", YP, OUTER)
        l_disp2 = T("runs your lambda", 20, NOTE).move_to([LX, YP - 0.42, 0], aligned_edge=RIGHT)
        r_l1, r_l2 = row_line(YL[0]), row_line(YL[1])
        l_l1, l_l2 = row_lab("lane 1", YL[0]), row_lab("lane 2", YL[1])
        r_out2, l_out2 = row_line(YO), row_lab("fees out", YO)
        h = header("flatMapMerge(2)", "lookups: 300, 100, 200, 50, 150 ms")
        self.add(cursor)
        self.say("fee_q")
        self.play(FadeIn(axis), FadeIn(h, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(Create(r_disp), FadeIn(l_disp), FadeIn(l_disp2), Create(r_l1), FadeIn(l_l1), Create(r_l2), FadeIn(l_l2),
                  Create(r_out2), FadeIn(l_out2), run_time=0.9)
        self.at(3)
        slow_code = M("{ m -> val fee = lookup(m); flowOf(fee) }", 24, t2c={"lookup(m)": FEE}).move_to([0.6, YN, 0])
        self.play(FadeIn(slow_code), run_time=0.5)
        self.hold(after=0)
        self.predict()

        spans = [("m1", 0, 300), ("m2", 300, 400), ("m3", 400, 600), ("m4", 600, 650), ("m5", 650, 800)]
        s_bars, s_labs, s_outs = [], VGroup(), VGroup()
        self.say("fee_slow")
        for name, a, b in spans:
            g, lab = fee_bar(a, b, YP, name)
            s_bars.append(g[0])
            self.add(g)
            to(b, speed=400)
            o = out(name, b, FEE)
            s_labs.add(lab)
            s_outs.add(o)
            self.play(FadeIn(lab), FadeIn(o, scale=0.6), run_time=0.2)
        idle = T("lanes idle", 26, NOTE).move_to([X(400), (YL[0] + YL[1]) / 2, 0])
        self.play(FadeIn(idle), run_time=0.4)
        self.at_text("Picture a toll")
        self.play(Indicate(l_disp, color=WHITE), run_time=0.9)
        self.at_text("The booths")
        self.play(Indicate(idle, color=WHITE), run_time=0.9)
        self.hold()
        for b in s_bars:
            b.clear_updaters()
        self.play(FadeOut(VGroup(*s_bars, s_labs, s_outs, idle)), run_time=0.5)
        tm.set_value(0)

        fast_code = M("{ m -> flow { emit(lookup(m)) } }", 24, t2c={"lookup(m)": FEE}).move_to([0.6, YN, 0])
        lanes = [("m1", 0, 300, 0), ("m2", 0, 100, 1), ("m3", 100, 300, 1), ("m4", 300, 350, 0), ("m5", 300, 450, 1)]
        f_bars, f_labs = [], VGroup()
        self.say("fee_fast")
        self.play(FadeOut(slow_code), FadeIn(fast_code), run_time=0.6)
        self.at(1)
        for name, a, b, lane in lanes:
            g, lab = fee_bar(a, b, YL[lane], name)
            f_bars.append(g[0])
            f_labs.add(lab)
            self.add(g)
        # the dispatcher now only builds each flow: a short mark per merchant
        marks = VGroup(*[Line([X(ms), YP - 0.2, 0], [X(ms), YP + 0.2, 0], stroke_width=4, color=FEE) for ms in (0, 100, 300)])
        self.play(FadeIn(marks), run_time=0.3)
        f_outs = {}
        for ms, names in ((100, ["m2"]), (300, ["m1", "m3"]), (350, ["m4"]), (450, ["m5"])):
            to(ms, speed=170)
            anims = []
            for i, name in enumerate(names):
                dy = 0 if len(names) == 1 else (0.27 if i == 0 else -0.27)
                o = out(name, ms, FEE, dy)
                f_outs[name] = o
                anims.append(FadeIn(o, scale=0.6))
            for name, a, b, lane in lanes:
                if b == ms:
                    anims.append(FadeIn(f_labs[[n for n, *_ in lanes].index(name)]))
            self.play(*anims, run_time=0.25)
        done = T("done at 450 ms", 26, WHITE).move_to([X(450) + 0.3, (YL[1] + YO) / 2 - 0.1, 0], aligned_edge=LEFT)
        self.play(FadeIn(done), run_time=0.4)
        self.at(3)
        self.play(Indicate(f_outs["m2"], color=WHITE, scale_factor=1.3), run_time=0.8)
        self.hold()
        for b in f_bars:
            b.clear_updaters()
        self.remove(cursor)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code, last =================
        hl = {"lookup(m)": FEE, "lookupBlocking(m)": FEE, "// 450 ms": GREEN_M, "// about 450 ms": GREEN_M,
              "// 800 ms": RED_M, "// about 800 ms": RED_M}
        kt = VGroup(T("Kotlin", 26, NOTE),
                    M("merchants.flatMapMerge(2) { m -> flow { emit(lookup(m)) } }   // 450 ms", 24, t2c=hl),
                    M("merchants.flatMapMerge(2) { m -> flowOf(lookup(m)) }          // 800 ms", 24, t2c=hl)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        jv = VGroup(T("Java, Reactor", 26, NOTE),
                    M("merchants.flatMap(m -> lookup(m), 2);                   // about 450 ms", 24, t2c=hl),
                    M("merchants.flatMap(m -> Mono.just(lookupBlocking(m)), 2); // about 800 ms", 24, t2c=hl)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        code = VGroup(kt, jv).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(code, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(kt, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(jv, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.9)
        self.play(FadeOut(code), run_time=0.6)

        # ================= the rule and a check =================
        r1 = VGroup(M("flatMapConcat", 28, PICK[1]), T("one lane, and the outer waits.", 32)).arrange(RIGHT, buff=0.25)
        r2 = VGroup(M("flatMapMerge", 28, PICK[2]), T("a lane for each returned flow.", 32)).arrange(RIGHT, buff=0.25)
        r3 = VGroup(M("flatMapLatest", 28, PICK[3]), T("one lane, and a new value cuts the old one.", 32)).arrange(RIGHT, buff=0.25)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.32, aligned_edge=LEFT).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("ten merchants, 100 ms each, four lanes, the lookup inside the returned flow.", 28),
                    T("How long does it take?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
