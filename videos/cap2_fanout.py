from fg import *
import fg

fg.SAY[:0] = [(r"\bEURUSD\b", "E U R U S D"), (r"\bwithTimeoutOrNull\b", "with timeout or null"),
              (r"\bcoroutineScope\b", "co-routine scope"), (r"\bsupervisorScope\b", "supervisor scope"),
              (r"\bTimeoutCancellationException\b", "Timeout Cancellation Exception"),
              (r"\bCancellationException\b", "Cancellation Exception"), (r"\bIOException\b", "I O Exception"),
              (r"\bNoQuoteException\b", "No Quote Exception"), (r"\bensureActive\b", "ensure active"),
              (r"\bcoroutines?\b", lambda m: "co-routine" + ("s" if m.group(0).endswith("s") else "")),
              (r"\basync\b", "ay-sink"), (r"\bNorthbank\b", "North bank"), (r"\bEastgate\b", "East gate"),
              (r"1\.0843", "one point oh eight four three"), (r"1\.0841", "one point oh eight four one"),
              (r"\bfan-out\b", "fan out")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if callable(anims):
                anims = anims()
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=24, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


X0, S = -3.9, 0.0115                 # 0 ms on the time axis, and units per millisecond
LY = [1.45, 0.45, -0.55]             # one lane per provider
NAMES = ["northbank", "eastgate", "fjord"]
COLS = [BLUE_M, TEAL_M, PURPLE_M]
BH = 0.46
DL = 250                             # the deadline in the lesson's figure


def xt(ms):
    return X0 + ms * S


def cross(at, s=0.17):
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(RED_M, 5).scale(s).move_to(at)


def make_run(clock, spec):
    """spec: one (start, end, kind, text) per lane. kind: ok (answer inside the bar), cut (grey, label after the end),
    fail (red cross and label). Every piece follows the clock in milliseconds."""
    parts = VGroup()
    for i, (t0, t1, kind, text) in enumerate(spec):
        col = COLS[i]
        bar = Rectangle(width=0.01, height=BH, stroke_width=0)

        def upd(m, t0=t0, t1=t1, kind=kind, col=col, i=i):
            t = clock.get_value()
            w = max(0.0, min(t, t1) - t0) * S
            ended = t >= t1
            c = GREY_D if (ended and kind == "cut") else col
            m.become(Rectangle(width=max(w, 0.001), height=BH, stroke_width=2 if w > 0 else 0, stroke_color=c)
                     .set_fill(c, 0.35 if w > 0 else 0).move_to([xt(t0) + w / 2, LY[i], 0]))
        bar.add_updater(upd)
        parts.add(bar)
        if kind == "ok":
            lab = M(text, 24, WHITE).move_to([xt(t1) - 0.1, LY[i], 0], aligned_edge=RIGHT)
        elif kind == "cut":
            lab = M(text, 24, GREY_B).move_to([xt(t1) + 0.15, LY[i], 0], aligned_edge=LEFT)
        else:
            x = cross([xt(t1) + 0.05, LY[i], 0])
            lab = VGroup(x, M(text, 22, RED_M if kind == "fail" else YELLOW_M)
                         .move_to([xt(t1) + 0.35, LY[i], 0], aligned_edge=LEFT))
        lab.set_opacity(0)
        lab.add_updater(lambda m, t1=t1: m.set_opacity(float(np.clip((clock.get_value() - t1 + 12) / 12, 0, 1))))
        parts.add(lab)
    return parts


def freeze(parts):
    for p in parts:
        p.clear_updaters()


class Cap2Fanout(VoiceScene):
    """cap2-02, sections 0 to 2 (Kotlin coroutines; Reactor shown as the Java equivalent): start all three calls
    together, give each call the deadline, let each fail alone in supervisorScope, rethrow only your own cancel
    (ensureActive), and serve the last good quote marked stale when nobody answers."""

    def construct(self):
        self.title_card("Fan out inside a deadline", "one request, three providers, Kotlin coroutines")

        head = T("one request: EURUSD", 28).move_to([-6.0, 2.85, 0], aligned_edge=LEFT)
        names = VGroup(*[M(n, 26, c).move_to([X0 - 0.25, y, 0], aligned_edge=RIGHT) for n, c, y in zip(NAMES, COLS, LY)])
        axis = Line([X0, -1.25, 0], [xt(650), -1.25, 0], stroke_width=2, color=GREY_C)
        tks = VGroup(*[Line([xt(v), -1.25, 0], [xt(v), -1.35, 0], stroke_width=2, color=GREY_C) for v in range(0, 700, 100)])
        tlab = VGroup(*[T(str(v), 22, GREY_B).move_to([xt(v), -1.6, 0]) for v in range(0, 700, 200)])
        ms = T("ms", 22, GREY_B).move_to([xt(650) + 0.35, -1.6, 0])
        ans_l = T("answer:", 26, GREY_B).move_to([-6.0, -2.6, 0], aligned_edge=LEFT)
        self.beat("One customer asks for a EURUSD price. Three providers can quote it. You want the lowest.",
                  FadeIn(head), LaggedStart(*[FadeIn(n, shift=RIGHT * 0.2) for n in names], lag_ratio=0.4),
                  Create(axis), FadeIn(tks), FadeIn(tlab), FadeIn(ms), run_time=2.4)

        clock = ValueTracker(0)

        def answer(text, col):
            return M(text, 26, col).next_to(ans_l, RIGHT, buff=0.3)

        # ---------------- one after another, then together ----------------
        r0 = make_run(clock, [(0, 120, "ok", "120"), (120, 420, "ok", "300"), (420, 620, "ok", "200")])
        self.add(r0)
        tot = T("620 ms", 30, WHITE).move_to([xt(620) + 0.1, 2.25, 0])
        seq(self, "One after another, their times add up: 620 milliseconds.",
            ([clock.animate(rate_func=linear).set_value(620)], 4.0), ([FadeIn(tot)], 0.4))
        freeze(r0)
        par = [Rectangle(width=d * S, height=BH, stroke_width=2, stroke_color=c).set_fill(c, 0.35)
               .move_to([X0 + d * S / 2, y, 0]) for d, c, y in zip([120, 300, 200], COLS, LY)]
        tot2 = T("300 ms", 30, WHITE).move_to([xt(300), 2.25, 0])
        self.beat("Start all three together with async, and you wait only for the slowest: 300.",
                  *[Transform(r0[2 * i], par[i]) for i in range(3)],
                  *[r0[2 * i + 1].animate.move_to([xt(d) - 0.1, LY[i], 0], aligned_edge=RIGHT)
                    for i, d in enumerate([120, 300, 200])],
                  Transform(tot, tot2), run_time=1.6)

        wall = DashedLine([xt(DL), 2.0, 0], [xt(DL), -1.25, 0], dash_length=0.12, stroke_width=3, color=YELLOW_M)
        wall_l = T("deadline 250 ms", 24, YELLOW_M).move_to([xt(DL), 2.25, 0])
        self.play(FadeOut(tot), run_time=0.3)
        self.beat("Give the request a deadline: 250 milliseconds.", Create(wall), FadeIn(wall_l), run_time=1.0)
        self.beat("Where does the timeout go? Around the whole fan-out, or around each call?")
        self.wait(1.0)
        self.play(FadeOut(r0), run_time=0.4)

        # ---------------- one timeout around everything ----------------
        whole_l = M("withTimeout { all three }", 24, GREY_A).move_to([3.6, 2.85, 0])
        clock.set_value(0)
        r1 = make_run(clock, [(0, 120, "ok", "1.0845"), (0, DL, "cut", "cancelled"), (0, 200, "ok", "1.0843")])
        self.add(r1)
        seq(self, "Around the whole fan-out, the deadline cancels everything. Northbank and Fjord had answered, and "
                  "both answers are thrown away.",
            ([FadeIn(whole_l)], 0.4),
            ([clock.animate(rate_func=linear).set_value(DL)], 2.5))
        freeze(r1)
        a1 = answer("nothing to send", RED_M)
        self.play(*[r.animate.set_fill(GREY_D, 0.35).set_stroke(GREY_D) for r in (r1[0], r1[4])],
                  *[r.animate.set_color(GREY_D) for r in (r1[1], r1[5])], FadeIn(ans_l), FadeIn(a1), run_time=0.8)
        self.wait(0.3)
        self.play(FadeOut(r1), FadeOut(a1), FadeOut(whole_l), run_time=0.4)

        # ---------------- a deadline per call ----------------
        each_l = M("async { withTimeoutOrNull(250 ms) { call } }", 22, GREY_A).move_to([2.8, 2.85, 0])
        clock.set_value(0)
        r2 = make_run(clock, [(0, 120, "ok", "1.0845"), (0, DL, "cut", "null"), (0, 200, "ok", "1.0843")])
        self.add(r2)
        a2 = answer("fjord 1.0843, at 250 ms", PURPLE_M)
        seq(self, "Around each call, with withTimeoutOrNull, only Eastgate is cut off. It becomes null. The answers "
                  "that arrived still count, and Fjord wins.",
            ([FadeIn(each_l)], 0.4),
            ([clock.animate(rate_func=linear).set_value(DL)], 2.5), 1.2,
            ([FadeIn(a2), Indicate(r2[5], color=PURPLE_M, scale_factor=1.15)], 1.0))
        freeze(r2)
        self.wait(0.2)
        self.play(FadeOut(r2), FadeOut(a2), FadeOut(each_l), FadeOut(wall), FadeOut(wall_l), run_time=0.5)

        # ---------------- one provider fails ----------------
        cs_l = M("coroutineScope", 26, GREY_A).move_to([3.6, 2.85, 0])
        clock.set_value(0)
        r3 = make_run(clock, [(0, 50, "fail", "IOException"), (0, 50, "cut", "cancelled"), (0, 50, "cut", "cancelled")])
        self.add(r3)
        a3 = answer("fails: IOException: northbank 503", RED_M)
        seq(self, "Now a rougher run, with no tight deadline. Northbank fails at 50 milliseconds.",
            ([FadeIn(cs_l)], 0.5), ([clock.animate(rate_func=linear).set_value(50)], 1.0))
        freeze(r3)
        self.beat("Inside coroutineScope, the three calls are one unit of work. One failure cancels the others, and "
                  "the request fails.", FadeIn(a3), run_time=1.0)
        self.play(FadeOut(r3), FadeOut(a3), run_time=0.4)

        ss_l = M("supervisorScope", 26, GREEN_M).move_to(cs_l)
        clock.set_value(0)
        r4 = make_run(clock, [(0, 50, "fail", "IOException"), (0, 100, "cut", "cancelled"),
                              (0, 100, "tce", "TimeoutCancellationException")])
        self.add(r4)
        seq(self, "A quote needs any one answer. supervisorScope lets each call fail alone.",
            ([Transform(cs_l, ss_l)], 0.8), ([clock.animate(rate_func=linear).set_value(70)], 1.4))
        self.beat("At 100 milliseconds, Fjord's own HTTP client gives up. It throws TimeoutCancellationException, which "
                  "is a CancellationException too.", clock.animate(rate_func=linear).set_value(100), run_time=1.2)
        freeze(r4)
        a4 = answer("fails: TimeoutCancellationException", RED_M)
        self.beat("Rethrow every cancel, the usual rule, and Fjord's timeout ends your whole request.", FadeIn(a4),
                  run_time=1.0)
        self.play(FadeOut(r4), FadeOut(a4), run_time=0.4)

        # ---------------- tell your cancel from theirs ----------------
        q_box = RoundedRectangle(corner_radius=0.12, width=4.7, height=2.2, stroke_color=WHITE, stroke_width=2.5)
        q_box.set_fill(BLACK, 1).move_to([3.95, 0.95, 0])
        q = VGroup(M("ensureActive()", 26, WHITE), T("was my coroutine cancelled?", 24, GREY_A),
                   T("yes, the client hung up: rethrow", 22, RED_M), T("no: that provider gives null", 22, GREEN_M))
        q.arrange(DOWN, buff=0.14).move_to(q_box)
        q.scale(min(1, 4.4 / q.width))
        self.beat("So ask first: was my own coroutine cancelled? ensureActive throws only if it was, say because the "
                  "client hung up.", FadeIn(q_box), LaggedStart(*[FadeIn(x, shift=DOWN * 0.1) for x in q], lag_ratio=0.5),
                  run_time=3.0)
        clock.set_value(0)
        r5 = make_run(clock, [(0, 50, "fail", "null"), (0, 300, "ok", "1.0841"), (0, 100, "tce", "null")])
        self.add(r5)
        a5 = answer("eastgate 1.0841, at 300 ms", TEAL_M)
        seq(self, "Here it wasn't. Fjord just has no answer, and Eastgate answers at 300.",
            ([Indicate(q[3], color=GREEN_M, scale_factor=1.08), clock.animate(rate_func=linear).set_value(300)], 2.8),
            ([FadeIn(a5)], 0.5))
        freeze(r5)
        self.wait(0.1)

        # ---------------- nobody answers ----------------
        c_box = RoundedRectangle(corner_radius=0.12, width=4.0, height=1.6, stroke_color=GOLD_M, stroke_width=2.5)
        c_box.set_fill(BLACK, 1).move_to([3.95, 0.95, 0])
        c_t = T("cache: last live quote", 24, GOLD_M).move_to([3.95, 1.45, 0])
        c_v = M("EURUSD 1.0841 eastgate", 24, WHITE).move_to([3.95, 0.75, 0])
        mover = a5.copy()
        self.play(FadeOut(VGroup(q_box, q)), FadeIn(c_box), FadeIn(c_t), run_time=0.5)
        self.play(mover.animate.move_to(c_v).set_opacity(0), FadeIn(c_v), run_time=0.8)
        self.remove(mover)
        self.play(FadeOut(r5), FadeOut(a5), FadeIn(wall), FadeIn(wall_l), FadeOut(cs_l), run_time=0.5)
        clock.set_value(0)
        r6 = make_run(clock, [(0, DL, "cut", "null"), (0, DL, "cut", "null"), (0, DL, "cut", "null")])
        self.add(r6)
        seq(self, "Last case. All three miss the deadline. Waiting breaks the deadline, and failing helps nobody.",
            ([clock.animate(rate_func=linear).set_value(DL)], 2.5))
        freeze(r6)
        a6 = VGroup(M("7", 26, WHITE), M("STALE", 26, GOLD_M), M("EURUSD 1.0841 eastgate", 26, WHITE)).arrange(RIGHT, buff=0.22)
        a6.next_to(ans_l, RIGHT, buff=0.3)
        live = T("only live answers refresh it", 22, GREY_B).move_to([3.95, -0.15, 0])
        nq = T("nothing cached: NoQuoteException", 22, RED_M).next_to(live, DOWN, buff=0.2)
        seq(self, "So serve the last good quote, marked stale, and let the client decide. Only live answers refresh the "
                  "cache.",
            ([TransformFromCopy(c_v, a6[2]), FadeIn(a6[0]), FadeIn(a6[1])], 1.4), 1.0, ([FadeIn(live), FadeIn(nq)], 0.6))
        self.play(FadeOut(VGroup(head, names, axis, tks, tlab, ms, ans_l, a6, r6, wall, wall_l, c_box, c_t, c_v, live, nq)),
                  run_time=0.7)

        # ---------------- the code ----------------
        kc = code(["supervisorScope {                              // each call fails alone",
                   "    providers.map { p ->",
                   "        async { withTimeoutOrNull(deadline) { p.quote(symbol) } }",
                   "    }.map { it.awaitOrNull() }                 // ensureActive() inside",
                   "}"], 22)
        jc = code(["call.timeout(DEADLINE)                         // on each of the three",
                   "    .map(Optional::of)",
                   "    .onErrorResume(e -> Mono.just(Optional.empty()))",
                   "// then Mono.zip the three and keep the lowest"], 22)
        kc[0].set_color(GREEN_M); kc[2].set_color(YELLOW_M)
        cg = VGroup(titled("Kotlin, coroutines (the lab)", kc), titled("Java equivalent, with Reactor", jc))
        cg.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.2, 0])
        self.beat("Here it is in Kotlin, with the Java version in Reactor below it.", FadeIn(cg, shift=UP * 0.2),
                  run_time=1.2)
        self.wait(1.0)
        self.play(FadeOut(cg), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Start every call together, give each the deadline,", 30),
                      T("let each fail alone, and rethrow only your own cancel.", 30)).arrange(DOWN, buff=0.2)
        rule.scale(min(1, 12 / rule.width)).move_to([0, 2.2, 0])
        self.beat("The rule. Start every call together, give each the deadline, let each fail alone, and rethrow only "
                  "your own cancel.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("You rethrow every CancellationException. Fjord's client", 28),
                     T("times out at 100 ms. What happens to Eastgate's answer at 300?", 28)).arrange(DOWN, buff=0.16)
        chk.scale(min(1, 12 / chk.width)).move_to([0, 0.1, 0])
        self.beat("Check yourself. You rethrow every CancellationException. Fjord's client times out at 100 "
                  "milliseconds. What happens to Eastgate's answer at 300?", FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = T("It never counts: the request fails at 100 ms with TimeoutCancellationException.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.6, 0])
        self.beat("It never counts. The request fails at 100 milliseconds with TimeoutCancellationException.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
