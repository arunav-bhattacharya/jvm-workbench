from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bthenApply\b", "then apply"), (r"\bwhenComplete\b", "when complete"),
              (r"\bexceptionally\b", "exceptionally"), (r"\borTimeout\b", "or timeout"), (r"\ballOf\b", "all of"),
              (r"\bTimeoutException\b", "Timeout Exception"), (r"\bsupplyAsync\b", "supply async"),
              (r"\bCompletableFuture\b", "Completable Future"), (r"\b502\b", "five oh two"), (r"\b503\b", "five oh three"),
              (r"\bFX\b", "F X"), (r"\bUSD\b", "U S D"), (r"\bio\b", "I O")]


# ---- helpers for this file ----
def code(lines, size=26, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


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
            if rt is None:                       # stretch this step to the end of the line
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def stage(label, method, color=GREY_B, w=1.75):
    """One stage of a chain: a box with what it does, and the method name under it."""
    b = box(label, color, w=w, h=0.85, size=26)
    m = M(method, 20, GREY_B).next_to(b, DOWN, buff=0.15)
    return VGroup(b, m)


def token(text, color, size=24):
    c = chip(text, color, size=size, mono=True)
    c[0].set_fill(dark(color, 0.45), 1)
    return c.set_z_index(8)


class Exec07CfErrors(VoiceScene):
    """exec-07, section 0: a failure skips every later stage until a handler; where exceptionally sits decides what
    you can recover; orTimeout completes the future, not the work; allOf fails if one call fails, so each call
    turns its failure into an empty answer with handle first."""

    def construct(self):
        self.title_card("When a future fails", "errors, timeouts and fan-out in a CompletableFuture chain")

        # =============== part 1: a failure slides down the chain ===============
        XS = [-5.375, -3.225, -1.075, 1.075, 3.225, 5.375]
        SY, TY = 0.5, 1.5           # stage row, token row
        specs = [("FX rate", "supplyAsync", BLUE_M), ("convert", "thenApply", GREY_B), ("round", "thenApply", GREY_B),
                 ("charge", "thenApply", GREY_B), ("log", "whenComplete", PURPLE_M), ("recover", "exceptionally", GREEN_M)]
        st = [stage(a, b, c).move_to([x, SY, 0]) for (a, b, c), x in zip(specs, XS)]
        for s_ in st:
            s_[1].next_to(s_[0], DOWN, buff=0.15)
        links = VGroup(*[Arrow(st[i][0].get_right(), st[i + 1][0].get_left(), buff=0.06, stroke_width=3, color=GREY_D,
                               max_tip_length_to_length_ratio=0.35) for i in range(5)])

        def above(i):
            return np.array([XS[i], TY, 0])

        self.beat("A checkout is a chain of stages. Get the FX rate, convert the amount, round it to cents, charge the card.",
                  LaggedStart(*[FadeIn(s_) for s_ in st[:4]], lag_ratio=0.3), FadeIn(links[:3]), run_time=2.6)
        self.beat("Then a stage that logs the outcome, and one that recovers from a failure.",
                  FadeIn(st[4]), FadeIn(st[5]), FadeIn(links[3:]), run_time=1.2)

        # a quick success pass
        ok = token("value", GOLD_M).move_to(above(0))

        def flash(i, color):
            return Indicate(st[i][0][1], color=color, scale_factor=1.15)
        seq(self, "Each stage runs when the one before it completes with a value.",
            ([FadeIn(ok, scale=0.6), flash(0, GOLD_M)], 0.5),
            ([Succession(*[AnimationGroup(ok.animate.move_to(above(i)), flash(i, GOLD_M)) for i in range(1, 6)],
                         run_time=3.0)], 3.0),
            ([FadeOut(ok)], 0.3))

        # the failure
        bad = token("502", RED_M).move_to(above(0))
        q = T("which numbered steps run?", 26, YELLOW_M).move_to([0, -1.55, 0])
        self.beat("Now the FX provider answers with a 502, and the first stage throws. Which of the next three steps run?",
                  FadeIn(bad, scale=0.6), st[0][0][0].animate.set_stroke(RED_M), FadeIn(q), run_time=1.4)
        self.wait(2.0)
        skips = VGroup(*[T("skipped", 24, GREY_B).next_to(st[i][1], DOWN, buff=0.15) for i in (1, 2, 3)])

        def skip(i):
            return [bad.animate.move_to(above(i)), st[i].animate.set_opacity(0.3), FadeIn(skips[i - 1])]
        seq(self, "None of them. The failure skips every thenApply. Their functions never run, and each one's future "
                  "fails with the same cause.",
            ([FadeOut(q)], 0.4), 0.6,
            (lambda: skip(1), 0.8), 0.3, (lambda: skip(2), 0.8), 0.3, (lambda: skip(3), 0.8))
        sees = T("sees it, passes it on", 24, PURPLE_M).next_to(st[4][1], DOWN, buff=0.15)
        dec = token("declined", GREEN_M).move_to(above(5))
        res1 = T("result: declined: FX rate unavailable", 28, GREEN_M).move_to([0, -2.2, 0])
        seq(self, "It slides down the chain until it reaches a handler. whenComplete sees it and passes it on. "
                  "exceptionally catches it, but this late, all it can return is: declined.",
            1.2, ([bad.animate.move_to(above(4)), flash(4, PURPLE_M)], 0.8), ([FadeIn(sees)], 0.5), 1.4,
            ([bad.animate.move_to(above(5)), flash(5, GREEN_M)], 0.8), 0.6,
            ([FadeOut(bad, scale=0.6), FadeIn(dec, scale=0.6)], 0.6), 1.0, ([FadeIn(res1)], 0.6))

        # move the handler up, right after the FX call
        self.play(FadeOut(VGroup(dec, res1, sees, skips)), *[st[i].animate.set_opacity(1) for i in (1, 2, 3)],
                  st[0][0][0].animate.set_stroke(BLUE_M), run_time=0.7)
        new_x = [XS[0], XS[2], XS[3], XS[4], XS[5], XS[1]]       # recover goes second, the rest shift right
        arc = ArcBetweenPoints(st[5].get_center(), np.array([XS[1], SY, 0]), angle=PI * 0.5)
        moves = [st[i].animate.move_to([new_x[i], SY, 0]) for i in range(1, 5)]
        seq(self, "Now move exceptionally up, right after the FX call.",
            ([FadeOut(links)], 0.4),
            ([MoveAlongPath(st[5], arc), *moves], 1.4),
            ([FadeIn(links)], 0.4))
        order = [0, 5, 1, 2, 3, 4]                                 # stage index at each position

        def at(pos):
            return np.array([XS[pos], TY, 0])
        bad = token("502", RED_M).move_to(at(0))
        rate = token("1.0800", GOLD_M).move_to(at(1))
        seq(self, "The failure reaches it at once, and it returns the last known rate.",
            ([FadeIn(bad, scale=0.6), st[0][0][0].animate.set_stroke(RED_M)], 0.6),
            ([bad.animate.move_to(at(1)), flash(5, GREEN_M)], 0.8), 0.4,
            ([FadeOut(bad, scale=0.6), FadeIn(rate, scale=0.6)], 0.6))
        vals = ["108.000000", "108.00", "charged"]
        toks = [token(v, GOLD_M).move_to(at(p)) for v, p in zip(vals, (2, 3, 4))]
        runs = VGroup(*[T("runs", 24, GOLD_M).next_to(st[order[p]][1], DOWN, buff=0.15) for p in (2, 3, 4)])
        res2 = T("result: charged 108.00 USD", 28, GOLD_M).move_to([0, -2.2, 0])
        sees2 = T("sees a success", 24, PURPLE_M).next_to(st[4][1], DOWN, buff=0.15)
        seq(self, "Every step after it runs as if nothing went wrong, and the card is charged 108 USD.",
            (lambda: [rate.animate.move_to(at(2)), flash(1, GOLD_M)], 0.6), (lambda: [Transform(rate, toks[0]), FadeIn(runs[0])], 0.4),
            (lambda: [rate.animate.move_to(at(3)), flash(2, GOLD_M)], 0.6), (lambda: [Transform(rate, toks[1]), FadeIn(runs[1])], 0.4),
            (lambda: [rate.animate.move_to(at(4)), flash(3, GOLD_M)], 0.6), (lambda: [Transform(rate, toks[2]), FadeIn(runs[2])], 0.4),
            (lambda: [rate.animate.move_to(at(5)), flash(4, PURPLE_M), FadeIn(sees2)], 0.6), ([FadeIn(res2)], 0.6))
        r1 = T("Recover as close to the failing call as you can.", 30).move_to([0, -3.0, 0])
        self.beat("Recover as close to the failing call as you can.", FadeIn(r1, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(*st, links, rate, runs, res2, sees2, r1)), run_time=0.7)

        # =============== part 2: orTimeout fills the box, the work runs on ===============
        LX0, LX1 = -5.2, 1.4
        PX = (LX1 - LX0) / 600
        def lx(ms):
            return LX0 + ms * PX
        io_l = T("io thread", 26, TEAL_M).move_to([lx(0), 1.7, 0], aligned_edge=LEFT)
        call = Rectangle(width=600 * PX, height=0.5, stroke_color=TEAL_M, stroke_width=2.5).set_fill(dark(TEAL_M, 0.3), 1)
        call.move_to([lx(300), 1.05, 0])
        call_t = T("asking the slow provider", 24, TEAL_M).move_to(call).set_z_index(3)
        axis = Line([lx(0), 0.45, 0], [lx(600), 0.45, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([lx(m), 0.52, 0], [lx(m), 0.38, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([lx(m), 0.15, 0])) for m in (0, 200, 400, 600)])
        fut = RoundedRectangle(corner_radius=0.15, width=3.2, height=1.3, stroke_color=WHITE, stroke_width=3).move_to([4.6, 1.05, 0])
        fut.set_fill(BLACK, 1)
        fut_l = T("the future", 26).next_to(fut, UP, buff=0.18)
        fut_v = T("empty", 26, GREY_B).move_to(fut)
        timer = M("orTimeout(200 ms)", 22, RED_M).move_to([4.6, -0.55, 0])
        cursor = Line([0, 1.45, 0], [0, 0.65, 0], stroke_width=3, color=YELLOW_M)
        tt = ValueTracker(0.0)
        cursor.add_updater(lambda m: m.set_x(lx(tt.get_value())))
        part = call.copy().stretch_to_fit_width(200 * PX, about_edge=LEFT)
        self.beat("A future is only a box for the answer. The work that fills it runs somewhere else, here on an io thread.",
                  FadeIn(fut), FadeIn(fut_l), FadeIn(fut_v), FadeIn(io_l), FadeIn(axis), FadeIn(ticks), FadeIn(call_t), run_time=1.6)
        tok_to = token("TimeoutException", RED_M, size=22).move_to(timer)
        self.add(cursor)
        seq(self, "Put orTimeout of 200 ms on the future. At 200 ms a timer fills the box with a TimeoutException, "
                  "and that failure goes down the chain like any other.",
            ([FadeIn(timer)], 0.6), 1.2,
            ([GrowFromEdge(part, LEFT, rate_func=linear), tt.animate(rate_func=linear).set_value(200)], 2.2),
            ([FadeIn(tok_to, scale=0.6)], 0.4), ([tok_to.animate.move_to(fut), FadeOut(fut_v), fut.animate.set_stroke(RED_M)], 0.8))
        ans = token("1.0842", GOLD_M).move_to([lx(600), 1.05, 0])
        lost = T("nobody is listening", 24, GREY_A).move_to([2.2, 1.75, 0])
        seq(self, "But the call itself never hears about it. It keeps its thread until 600 ms, "
                  "and then its answer is thrown away.",
            ([Transform(part, call, rate_func=linear), tt.animate(rate_func=linear).set_value(600)], 3.0),
            ([FadeOut(cursor), FadeIn(ans, scale=0.6)], 0.4),
            ([ans.animate.move_to([3.0, 1.05, 0]).set_opacity(0.25)], 0.8), ([FadeIn(lost)], 0.4))
        cursor.clear_updaters()
        r2 = T("A timeout ends the wait, not the work.", 30).move_to([0, -2.2, 0])
        r2b = T("give the client its own timeout too", 24, GREY_B).move_to([0, -2.8, 0])
        self.beat("A timeout ends the wait, not the work. So give the client its own timeout too.",
                  FadeIn(r2, shift=UP * 0.15), FadeIn(r2b), run_time=1.0)
        self.play(FadeOut(VGroup(io_l, call_t, part, axis, ticks, fut, fut_l, timer, tok_to, ans, lost, r2, r2b)), run_time=0.7)

        # =============== part 3: fan-out with allOf ===============
        FX0, FX1 = -4.1, 0.7          # 0 .. 300 ms
        FPX = (FX1 - FX0) / 300
        def fx(ms):
            return FX0 + ms * FPX
        LY = [1.6, 0.3, -1.0]
        prov = [("flaky", 50, None), ("alpha", 100, "1.0850"), ("beta", 300, "1.0842")]
        PCOL = [RED_M, BLUE_M, TEAL_M]
        names = VGroup(*[T(n, 28, c).move_to([-6.3, y, 0], aligned_edge=LEFT) for (n, _, _), y, c in zip(prov, LY, PCOL)])
        bars = [Rectangle(width=ms * FPX, height=0.42, stroke_width=0).set_fill(c, 0.45).move_to([fx(ms / 2), y, 0])
                for (_, ms, _), y, c in zip(prov, LY, PCOL)]
        AX = 4.0
        allof = RoundedRectangle(corner_radius=0.15, width=1.6, height=3.6, stroke_color=WHITE, stroke_width=3).move_to([AX, LY[1], 0])
        allof.set_fill(BLACK, 1)
        allof_l = M("allOf", 26).next_to(allof, UP, buff=0.18)
        slots = [np.array([AX, y, 0]) for y in LY]
        axis = Line([fx(0), -1.75, 0], [fx(300), -1.75, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([fx(m), -1.68, 0], [fx(m), -1.82, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([fx(m), -2.08, 0])) for m in (0, 100, 200, 300)])
        cursor = Line([0, 2.0, 0], [0, -1.4, 0], stroke_width=3, color=YELLOW_M)
        tt = ValueTracker(0.0)
        cursor.add_updater(lambda m: m.set_x(fx(tt.get_value())))

        self.beat("Now a fan-out. Ask three FX providers at once and wait for all of them with allOf.",
                  FadeIn(names), FadeIn(allof), FadeIn(allof_l), FadeIn(axis), FadeIn(ticks), run_time=1.4)
        lane_n = VGroup(T("fails at 50 ms", 22, GREY_A).next_to(names[0], DOWN, buff=0.08, aligned_edge=LEFT),
                        T("answers at 100 ms", 22, GREY_A).next_to(names[1], DOWN, buff=0.08, aligned_edge=LEFT),
                        T("answers at 300 ms", 22, GREY_A).next_to(names[2], DOWN, buff=0.08, aligned_edge=LEFT))
        tk = [token("503", RED_M), token("1.0850", BLUE_M), token("1.0842", TEAL_M)]
        for t_, (_, ms, _), y in zip(tk, prov, LY):
            t_.move_to([fx(ms) + 0.75, y, 0])
        self.add(cursor)

        RT = 4.0

        def lanes(tok_list, through=None):
            """Step 1: the clock runs 0 to 300 ms, each bar grows in step, and the early tokens fly to allOf
            (through a handle box first, if given). Step 2: beta's token, which only exists at 300 ms."""
            parts = []
            for k in (0, 1):
                ms = prov[k][1]
                t_ = tok_list[k].set_opacity(0)
                seen = t_.copy().set_opacity(1)
                steps = [GrowFromEdge(bars[k], LEFT, rate_func=linear, run_time=RT * ms / 300),
                         Transform(t_, seen, run_time=0.25)]
                used = RT * ms / 300 + 0.25
                cur = seen
                if through is not None:
                    at_h = cur.copy().move_to([through[0], LY[k], 0])
                    steps.append(Transform(t_, at_h, run_time=0.4)); used += 0.4
                    cur = at_h
                    if through[1][k] is not None:
                        steps.append(Transform(t_, through[1][k].copy().move_to(at_h), run_time=0.3)); used += 0.3
                        cur = through[1][k].copy().move_to(at_h)
                steps.append(Transform(t_, cur.copy().move_to(slots[k]), run_time=0.45)); used += 0.45
                steps.append(Wait(run_time=max(0.01, RT - used)))
                parts.append(Succession(*steps))
            step1 = [tt.animate(rate_func=linear).set_value(300), *parts,
                     GrowFromEdge(bars[2], LEFT, rate_func=linear)]
            t2 = tok_list[2]
            if through is not None:
                step2 = lambda: [Succession(FadeIn(t2, scale=0.6, run_time=0.25),
                                            t2.animate(run_time=0.4).move_to([through[0], LY[2], 0]),
                                            Wait(run_time=0.05),
                                            t2.animate(run_time=0.45).move_to(slots[2]))]
            else:
                step2 = lambda: [Succession(FadeIn(t2, scale=0.6, run_time=0.25), t2.animate(run_time=0.5).move_to(slots[2]))]
            return step1, step2
        s1, s2 = lanes(tk)
        seq(self, "flaky fails at 50 ms. alpha answers at 100, beta at 300.",
            ([FadeIn(lane_n)], 0.6), (s1, RT), (s2, 0.75))
        fail = token("fails: 503", RED_M).move_to([AX, -2.45, 0])
        seq(self, "allOf waits for every one of them, then fails, because one of them failed. "
                  "One bad answer at 50 ms fails the whole call, 300 ms later.",
            1.6, ([allof.animate.set_stroke(RED_M), FadeIn(fail, shift=DOWN * 0.2)], 0.8), 1.4,
            ([Indicate(tk[0][1], color=RED_M, scale_factor=1.3)], 1.0))

        # ---- the safe version: handle on each call turns a failure into "no answer" ----
        HX = 2.2
        handles = VGroup(*[mbox("handle", GREEN_M, w=1.35, h=0.6, size=22).move_to([HX, y, 0]) for y in LY])
        self.play(FadeOut(VGroup(*tk, fail, *bars)), allof.animate.set_stroke(WHITE), run_time=0.7)
        tt.set_value(0)
        cursor.update()
        bars = [Rectangle(width=ms * FPX, height=0.42, stroke_width=0).set_fill(c, 0.45).move_to([fx(ms / 2), y, 0])
                for (_, ms, _), y, c in zip(prov, LY, PCOL)]
        self.beat("The fix: put a handle on each call first. It turns a failure into an empty answer, so allOf can only succeed.",
                  LaggedStart(*[FadeIn(h, shift=LEFT * 0.2) for h in handles], lag_ratio=0.25), run_time=1.6)
        tk2 = [token("503", RED_M), token("1.0850", BLUE_M), token("1.0842", TEAL_M)]
        for t_, (_, ms, _), y in zip(tk2, prov, LY):
            t_.move_to([fx(ms) + 0.75, y, 0])
        emp = token("empty", GREY_B)
        s1, s2 = lanes(tk2, through=(HX, [emp, None, None]))
        best = token("1.0842", TEAL_M).move_to([AX, -2.45, 0])
        best_l = T("lowest price", 22, GREY_A).next_to(best, RIGHT, buff=0.2)
        seq(self, "Run it again. flaky's failure comes out of its handle as an empty answer. At 300 ms allOf has "
                  "two prices and one empty, and the next step picks the lowest.",
            0.8, (s1, RT), (s2, 1.15), 0.3,
            ([allof.animate.set_stroke(GREEN_M), FadeIn(best, shift=DOWN * 0.2), FadeIn(best_l)], 0.8))
        clocks = VGroup(*[M("orTimeout", 20, RED_M).next_to(h, UP, buff=0.08) for h in handles])
        self.beat("Give each call its own orTimeout before the handle, too. A provider that hangs becomes one more empty answer.",
                  LaggedStart(*[FadeIn(c) for c in clocks], lag_ratio=0.25), run_time=1.4)
        cursor.clear_updaters()
        self.play(FadeOut(VGroup(names, lane_n, *bars, *tk2, handles, clocks, allof, allof_l, axis, ticks, cursor, best, best_l)),
                  run_time=0.8)

        # =============== part 4: code, rule, check ===============
        jc = code(["CompletableFuture<Optional<BigDecimal>> safe = ask(provider)",
                   "    .orTimeout(200, TimeUnit.MILLISECONDS)",
                   "    .handle((p, ex) -> ex == null ? Optional.of(p) : Optional.empty());"], 22)
        kc = code(["val safe = ask(provider)",
                   "    .orTimeout(200, TimeUnit.MILLISECONDS)",
                   "    .handle { p, ex -> if (ex == null) Optional.of(p) else Optional.empty() }"], 22)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        cg.scale(min(1, 12.4 / cg.width)).move_to([0, 0.4, 0])
        note = T("then allOf over the safe futures, and pick from what came back", 24, GREY_B).next_to(cg, DOWN, buff=0.45)
        self.beat("In code, each call gets its deadline and its handle. The same chain works from Kotlin.",
                  FadeIn(cg, shift=UP * 0.2), FadeIn(note), run_time=1.4)
        self.play(FadeOut(VGroup(cg, note)), run_time=0.6)
        rule = T("A failure skips every stage until a handler catches it.", 32).move_to([0, 2.2, 0])
        rule2 = T("Catch it where you still have a useful answer.", 30, GREEN_M).move_to([0, 1.5, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule.width))
        self.beat("The rule. A failure skips every stage until a handler catches it. Catch it where you still have a useful answer.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = M("supplyAsync(fails) -> thenApply(A) -> exceptionally -> thenApply(B)", 22).move_to([0, -0.1, 0])
        chk.scale(min(1, 12 / chk.width))
        chk2 = T("Which of A and B runs?", 30).move_to([0, -0.8, 0])
        self.beat("Check yourself. The first stage fails, then comes thenApply A, then exceptionally, then thenApply B. "
                  "Which of A and B runs?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("only B: A is skipped, exceptionally recovers, B gets its value", 28, GOLD_M).move_to([0, -1.9, 0])
        ans.scale(min(1, 12 / ans.width))
        self.beat("Only B. A is skipped, exceptionally recovers, and B runs on the value it returns.",
                  FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
