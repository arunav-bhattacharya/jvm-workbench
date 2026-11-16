from fg import *
import fg

fg.SAY[:0] = [(r"\bcoroutineScope\b", "co-routine scope"), (r"\bNorthbank\b", "North bank"), (r"\bp99\b", "P 99"),
              (r"\bp95\b", "P 95"), (r"\bp50\b", "P 50")]


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


def code(lines, size=22, color=WHITE, ls=0.6):
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


def bar(clock, xt, t0, t1, y, col, h, cut=None):
    """A bar that grows with the clock from t0 to t1 (ms). With cut, it stops at cut and turns grey."""
    end = cut if cut is not None else t1

    def draw():
        t = clock.get_value()
        w = max(0.0, min(t, end) - t0) * xt.s
        c = GREY_D if (cut is not None and t >= cut) else col
        return Rectangle(width=max(w, 0.001), height=h, stroke_width=2 if w > 0 else 0, stroke_color=c) \
            .set_fill(c, 0.4 if w > 0 else 0).move_to([xt(t0) + w / 2, y, 0])
    return always_redraw(draw)


class Axis:
    def __init__(self, x0, s):
        self.x0, self.s = x0, s

    def __call__(self, ms):
        return self.x0 + ms * self.s


def axis(xt, y, upto, step, lab_step):
    line = Line([xt(0), y, 0], [xt(upto), y, 0], stroke_width=2, color=GREY_C)
    tks = VGroup(*[Line([xt(v), y, 0], [xt(v), y - 0.1, 0], stroke_width=2, color=GREY_C)
                   for v in range(0, upto + 1, step)])
    labs = VGroup(*[T(str(v), 22, GREY_B).move_to([xt(v), y - 0.33, 0]) for v in range(0, upto + 1, lab_step)])
    ms = T("ms", 22, GREY_B).move_to([xt(upto) + 0.35, y, 0], aligned_edge=LEFT)
    return VGroup(line, tks, labs, ms)


WIDE = Axis(-4.6, 0.0155)            # 0 to 650 ms, for twenty calls
NEAR = Axis(-4.2, 0.045)             # 0 to 200 ms, for one request
ROWS = [2.45 - 0.2 * i for i in range(20)]
SLOW = 13                            # the one call in twenty that takes 600 ms
L1, L2 = 1.2, 0.0                    # first call and hedge lanes in the near view


class Cap2Hedge(VoiceScene):
    """cap2-03, section 2: Northbank answers in 40 ms but one call in twenty takes 600 ms. Hedge after 80 ms (when
    19 calls in 20 have answered): send one identical call, take the first answer, cancel the other. p99 600 -> 120 ms
    for 210 calls instead of 200. Only safe-to-repeat calls may be hedged, and the hedge takes its own permit."""

    def construct(self):
        self.title_card("Hedge the slow tail", "one more call, only when the first is late")

        # ---------------- twenty calls ----------------
        clock = ValueTracker(0)
        ax = axis(WIDE, -1.65, 650, 100, 200)
        who = VGroup(T("Northbank,", 24, BLUE_M), T("20 calls", 24, GREY_B)).arrange(DOWN, buff=0.12)
        who.move_to([-5.65, 0.55, 0])
        bars = [bar(clock, WIDE, 0, 600 if i == SLOW else 40, y, BLUE_M, 0.1) for i, y in enumerate(ROWS)]
        self.add(*bars)
        l40 = T("40 ms", 22, GREY_B).move_to([WIDE(40) + 0.45, ROWS[0], 0])
        l600 = T("600 ms", 24, RED_M).move_to([WIDE(600) + 0.55, ROWS[SLOW], 0])
        seq(self, "Northbank answers a quote in 40 milliseconds, most of the time. But one call in twenty takes 600, "
                  "a garbage collection pause or a slow replica.",
            ([FadeIn(ax), FadeIn(who)], 0.6),
            ([clock.animate(rate_func=linear).set_value(40)], 0.8), ([FadeIn(l40)], 0.3), 1.2,
            ([clock.animate(rate_func=linear).set_value(600)], 3.0), ([FadeIn(l600)], 0.3))
        for b in bars:
            b.clear_updaters()
        p99 = T("p99: 600 ms", 30, RED_M).move_to([3.4, 2.9, 0])
        self.beat("So the p99, the time 99 of 100 requests beat, is 600 milliseconds.", FadeIn(p99), run_time=1.0)
        self.beat("A retry won't help. Nothing failed. The call is just slow.", Indicate(l600, color=RED_M), run_time=1.2)
        self.play(FadeOut(VGroup(*bars, l40, l600, ax, who, p99)), run_time=0.6)

        # ---------------- one request, close up ----------------
        ax2 = axis(NEAR, -0.9, 200, 20, 40)
        n1 = T("first call", 26, BLUE_M).move_to([-5.55, L1, 0])
        n2 = T("hedge", 26, TEAL_M).move_to([-5.55, L2, 0])
        hx = NEAR(80)
        hl = DashedLine([hx, 1.85, 0], [hx, -0.9, 0], dash_length=0.12, stroke_width=3, color=YELLOW_M)
        hl_l = T("hedge time: 80 ms", 26, YELLOW_M).move_to([hx, 2.55, 0])
        hl_n = T("by now, 19 calls in 20 have answered", 22, GREY_B).move_to([hx, 2.15, 0])
        self.beat("Watch one request. By 80 milliseconds, 19 calls in 20 have answered.",
                  FadeIn(ax2), FadeIn(n1), Create(hl), FadeIn(hl_l), FadeIn(hl_n), run_time=1.6)

        clock.set_value(0)
        fa = bar(clock, NEAR, 0, 40, L1, BLUE_M, 0.5)
        fa_l = T("answer", 24).move_to([NEAR(40) - 0.55, L1, 0])
        self.add(fa)
        seq(self, "A fast call answers at 40, and nothing else happens.",
            ([clock.animate(rate_func=linear).set_value(40)], 1.0), ([FadeIn(fa_l)], 0.3),
            ([clock.animate(rate_func=linear).set_value(110)], 1.2))
        self.play(FadeOut(fa), FadeOut(fa_l), run_time=0.4)

        clock.set_value(0)
        f1 = bar(clock, NEAR, 0, 600, L1, BLUE_M, 0.5, cut=120)
        f2 = bar(clock, NEAR, 80, 120, L2, TEAL_M, 0.5)
        self.add(f1, f2)
        seq(self, "Now the first call is a slow one. At 80, it still hasn't answered. So send one more identical call: "
                  "the hedge.",
            ([clock.animate(rate_func=linear).set_value(80)], 2.4), ([FadeIn(n2), Indicate(hl_l, color=YELLOW_M)], 0.8),
            ([clock.animate(rate_func=linear).set_value(100)], None))
        self.beat("Which answer comes first, and when?")
        self.wait(1.3)
        win = T("answer", 24).move_to([NEAR(120) - 0.55, L2, 0])
        cut_l = T("cancelled", 24, GREY_B).move_to([NEAR(120) + 0.85, L1, 0])
        at = T("answer at 120 ms = 80 + 40", 28, TEAL_M).move_to([1.0, -2.2, 0])
        seq(self, "The hedge, at 120: 80 of waiting, plus 40. Take it, and cancel the slow call.",
            ([clock.animate(rate_func=linear).set_value(120)], 0.8), ([FadeIn(win), FadeIn(at)], 0.5), 1.0,
            ([FadeIn(cut_l)], 0.5))
        for b in (f1, f2):
            b.clear_updaters()
        ghost = DashedLine([NEAR(120), L1, 0], [NEAR(200) + 0.2, L1, 0], dash_length=0.1, stroke_width=4, color=RED_M)
        ghost_l = T("no cancel: done at 600 ms", 24, RED_M).move_to([2.6, 0.6, 0])
        self.beat("Skip the cancel, and in Kotlin coroutineScope waits for every child. The request ends with the slow "
                  "call, at 600.", FadeOut(cut_l), Create(ghost), FadeIn(ghost_l), run_time=1.6)
        self.wait(0.3)
        self.play(FadeOut(VGroup(ghost, ghost_l, f1, f2, win, at, ax2, n1, n2, hl, hl_l, hl_n)), run_time=0.6)

        # ---------------- the tail, and the cost ----------------
        clock.set_value(40)
        rows = [bar(clock, WIDE, 0, 40, y, BLUE_M, 0.1) for i, y in enumerate(ROWS) if i != SLOW]
        for b in rows:
            b.update(); b.clear_updaters()
        sy = ROWS[SLOW]
        slow = Rectangle(width=600 * WIDE.s, height=0.1, stroke_width=2, stroke_color=BLUE_M).set_fill(BLUE_M, 0.4)
        slow.move_to([WIDE(0) + 300 * WIDE.s, sy, 0])
        ax = axis(WIDE, -1.65, 650, 100, 200)
        l600 = T("600 ms", 24, RED_M).move_to([WIDE(600) + 0.55, sy, 0])
        self.play(FadeIn(VGroup(*rows, slow, ax, who, l600)), run_time=0.6)
        slow_new = Rectangle(width=120 * WIDE.s, height=0.1, stroke_width=2, stroke_color=GREY_D).set_fill(GREY_D, 0.4)
        slow_new.move_to([WIDE(0) + 60 * WIDE.s, sy, 0])
        hedge_b = Rectangle(width=40 * WIDE.s, height=0.1, stroke_width=2, stroke_color=TEAL_M).set_fill(TEAL_M, 0.6)
        hedge_b.move_to([WIDE(100), sy, 0])
        l120 = T("120 ms", 24, TEAL_M).move_to([WIDE(120) + 0.55, sy, 0])
        self.beat("Back to all twenty calls. Only the slow one got a hedge, and it now ends at 120.",
                  Transform(slow, slow_new), FadeIn(hedge_b), Transform(l600, l120), run_time=1.8)

        hdr = [T("200 quotes", 24, GREY_B), T("no hedge", 24, GREY_B), T("hedge at 80 ms", 24, YELLOW_M)]
        rws = [[T("p50", 26), M("40 ms", 26), M("40 ms", 26)],
               [T("p99", 26), M("600 ms", 26, RED_M), M("120 ms", 26, TEAL_M)],
               [T("calls", 26), M("200", 26), M("210", 26, GOLD_M)]]
        tab = VGroup()
        cx = [-0.4, 1.9, 4.4]
        for r, cells in enumerate([hdr] + rws):
            for c, cell in enumerate(cells):
                cell.move_to([cx[c], 1.6 - 0.75 * r, 0])
                tab.add(cell)
        rule_l = Line([cx[0] - 0.9, 1.25, 0], [cx[2] + 1.3, 1.25, 0], stroke_width=1.5, color=GREY_D)
        self.beat("In the lesson's demo, 200 quotes: the p99 fell from 600 to 120 milliseconds. The median, the p50, "
                  "stayed at 40.", FadeIn(VGroup(*tab[:9], rule_l)), run_time=1.6)
        cost = T("+10 calls: about 5% more", 26, GOLD_M).move_to([2.2, -1.2, 0])
        self.beat("The cost: 210 calls instead of 200. Hedging at the 95th percentile adds about 5 percent.",
                  FadeIn(VGroup(*tab[9:])), FadeIn(cost), run_time=1.6)
        self.wait(0.3)
        self.play(FadeOut(VGroup(*rows, slow, hedge_b, l600, ax, who, tab, rule_l, cost)), run_time=0.6)

        # ---------------- only what is safe to repeat ----------------
        def card(title, col, lines, verdict, vcol, x):
            r = RoundedRectangle(corner_radius=0.14, width=6.0, height=2.6, stroke_color=col, stroke_width=3)
            r.set_fill(dark(col), 1).move_to([x, 0.9, 0])
            body = VGroup(T(title, 28, col), *[T(s, 24, GREY_A) for s in lines], T(verdict, 26, vcol))
            body.arrange(DOWN, buff=0.17)
            body.scale(min(1, 5.5 / body.width)).move_to(r)
            return VGroup(r, body)

        nb = card("Northbank", BLUE_M, ["indicative prices:", "asking twice changes nothing"], "may be hedged",
                  GREEN_M, -3.2)
        fj = card("Fjord", PURPLE_M, ["firm quotes: each call reserves", "liquidity, so a hedge reserves twice"],
                  "exactly one call", RED_M, 3.2)
        self.beat("A hedge is a duplicate request. Northbank's prices are indicative, so asking twice changes nothing.",
                  FadeIn(nb, shift=UP * 0.15), run_time=1.2)
        self.beat("Fjord's quotes are firm. Each call reserves liquidity, so a hedge would reserve twice. Fjord gets "
                  "exactly one call.", FadeIn(fj, shift=UP * 0.15), run_time=1.2)
        perm = VGroup(T("a hedge takes its own bulkhead permit:", 26),
                      T("under full load it waits, and the first call usually wins", 26)).arrange(DOWN, buff=0.14)
        perm.scale(min(1, 12 / perm.width)).move_to([0, -1.75, 0])
        self.beat("And the hedge takes its own permit from Northbank's bulkhead. Under full load it waits for one, so "
                  "it can't add to the queue that made Northbank slow.", FadeIn(perm, shift=UP * 0.15), run_time=1.4)
        self.wait(0.4)
        self.play(FadeOut(VGroup(nb, fj, perm)), run_time=0.6)

        # ---------------- the code ----------------
        kc = code(["coroutineScope {",
                   "    val first = async { call() }",
                   "    val early = withTimeoutOrNull(after) { first.await() }",
                   "    if (early != null) return@coroutineScope early",
                   "    val second = async { call() }                // the hedge",
                   "    val winner = select { first.onAwait { it }; second.onAwait { it } }",
                   "    coroutineContext.cancelChildren()            // stop the loser",
                   "    winner",
                   "}"])
        jc = code(["return Mono.firstWithValue(call, Mono.delay(after).then(call));"])
        kc[2].set_color(YELLOW_M); kc[4].set_color(TEAL_M); kc[6].set_color(GREY_B)
        cg = VGroup(titled("Kotlin, coroutines (the lab)", kc), titled("Java equivalent, with Reactor", jc))
        cg.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.3, 0])
        self.beat("Here it is in Kotlin, the lab's language, with the Java equivalent in Reactor below it.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.2)
        self.wait(1.5)
        self.play(FadeOut(cg), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Hedge only calls that are safe to repeat, only where the tail hurts,", 30),
                      T("after about the p95 latency, and cancel the loser.", 30)).arrange(DOWN, buff=0.2)
        rule.scale(min(1, 12 / rule.width)).move_to([0, 2.2, 0])
        self.beat("The rule. Hedge only calls that are safe to repeat, only where the tail hurts, after about the p95 "
                  "latency, and cancel the loser.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("You move the hedge to 30 ms, below Northbank's normal 40.", 28),
                     T("How many calls do 200 quotes make?", 28)).arrange(DOWN, buff=0.16)
        chk.scale(min(1, 12 / chk.width)).move_to([0, 0.1, 0])
        self.beat("Check yourself. You move the hedge to 30 milliseconds, below Northbank's normal 40. How many calls "
                  "do 200 quotes make?", FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = T("400. At 30 ms every call is still running, so every request is hedged: twice the load.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.6, 0])
        self.beat("400. At 30, every call is still running, so every request is hedged: twice the load.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
