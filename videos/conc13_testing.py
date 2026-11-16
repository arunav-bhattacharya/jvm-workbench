from fg import *
import fg
import random

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bjcstress\b", "J C stress"), (r"\bOpenJDK\b", "open J D K"),
              (r"\bCI\b", "C I"), (r"\bARM\b", "arm"), (r"\b1, 2\b", "one two"), (r"\b2, 1\b", "two one"),
              (r"\b1, 1\b", "one one")]


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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def seg(x0, x1, y, color, h=0.3, op=0.85):
    return Rectangle(width=max(0.02, x1 - x0), height=h, stroke_width=0).set_fill(color, op).move_to(
        [(x0 + x1) / 2, y, 0])


def grow(m):
    return GrowFromEdge(m, LEFT)


class Conc13Testing(VoiceScene):
    """conc-13, section 0: a concurrency test has to make threads collide (start latch, more threads than cores,
    many operations, many rounds, an invariant after join); wait for events with latches and deadlines, not sleeps;
    jcstress runs tiny tests millions of times and labels every outcome."""

    def construct(self):
        self.title_card("Testing concurrent code", "make the threads collide, then wait for events")
        rng = random.Random(13)

        # ---------------- the naive test: two threads that never meet ----------------
        LY = [1.9 - 0.48 * i for i in range(8)]       # lane centres, top to bottom
        XL = -4.5                                       # where time starts
        names = VGroup(*[T(f"thread {i + 1}", 24, GREY_B).move_to([XL - 0.35, y, 0], aligned_edge=RIGHT)
                         for i, y in enumerate(LY)])
        axis = Arrow([XL, -1.75, 0], [6.4, -1.75, 0], buff=0, stroke_width=2.5, color=GREY_B,
                     max_tip_length_to_length_ratio=0.02)
        axis_l = T("time", 24, GREY_B).next_to(axis, DOWN, buff=0.1).align_to(axis, RIGHT)

        # big two-lane picture for the naive test
        NY = [0.7, -0.35]
        nn = VGroup(*[T(f"thread {i + 1}", 28, GREY_B).move_to([-4.4, y, 0], aligned_edge=RIGHT) for i, y in enumerate(NY)])
        nax = Arrow([-4.1, -1.2, 0], [6.3, -1.2, 0], buff=0, stroke_width=2.5, color=GREY_B,
                    max_tip_length_to_length_ratio=0.02)
        nax_l = T("time", 24, GREY_B).next_to(nax, DOWN, buff=0.1).align_to(nax, RIGHT)
        st1, rf1 = seg(-4.0, -1.0, NY[0], GREY_D, h=0.5), seg(-1.0, -0.2, NY[0], BLUE_M, h=0.5)
        st2, rf2 = seg(-3.4, 0.6, NY[1], GREY_D, h=0.5), seg(0.6, 1.4, NY[1], BLUE_M, h=0.5)
        lab_s = T("starting the thread", 24, GREY_B).move_to([-2.75, 1.3, 0])
        lab_r = T("one refund", 24, BLUE_M).move_to([-0.25, 1.3, 0])
        passed = VGroup(tick(True, 0.26), T("pass", 34, GREEN_M)).arrange(RIGHT, buff=0.2).move_to([3.6, 0.7, 0])
        seq(self, "A refund ledger has a race. A test starts two threads, each makes one refund, and checks the total. "
                  "It passes, every time.",
            ([FadeIn(nn), Create(nax), FadeIn(nax_l)], 0.6), 1.0,
            ([grow(st1), FadeIn(lab_s)], 0.9), ([grow(rf1), FadeIn(lab_r)], 0.5),
            ([grow(st2)], 0.9), ([grow(rf2)], 0.5), ([FadeIn(passed)], 0.4))
        gap = DashedLine([0.2, 1.1, 0], [0.2, -0.75, 0], dash_length=0.08, stroke_width=3, color=RED_M)
        gap_l = T("never at the same time", 28, RED_M).move_to([3.9, -0.35, 0])
        self.beat("Starting a thread takes a while, and one refund is over in a moment. They never overlap, "
                  "so the race never happens.",
                  Create(gap), FadeIn(gap_l), Indicate(st2, color=WHITE, scale_factor=1.02), run_time=2.0)
        self.beat("How would you make them collide?")
        self.wait(1.3)
        self.play(FadeOut(VGroup(nn, nax, nax_l, st1, rf1, st2, rf2, lab_s, lab_r, passed, gap, gap_l)), run_time=0.5)
        self.play(FadeIn(names[0]), FadeIn(names[1]), Create(axis), FadeIn(axis_l), run_time=0.5)

        # ---------------- the stress test ----------------
        GX = -2.6
        gate = Line([GX, 2.15, 0], [GX, -1.55, 0], stroke_width=5, color=GOLD_M)
        gate_l = T("start latch", 26, GOLD_M).move_to([GX, 2.55, 0])
        arrive = [GX - rng.uniform(0.3, 1.6) for _ in LY]
        starts = [seg(XL + 0.15 * i, arrive[i], y, GREY_D) for i, y in enumerate(LY[:2])]
        waits = [DashedLine([arrive[i], y, 0], [GX - 0.05, y, 0], dash_length=0.07, stroke_width=2, color=GREY_B)
                 for i, y in enumerate(LY[:2])]
        short = [seg(GX, GX + 0.45, y, BLUE_M) for y in LY[:2]]
        seq(self, "Hold every thread at a start latch, then release them all at once.",
            ([Create(gate), FadeIn(gate_l)], 0.6), ([*[grow(s) for s in starts]], 0.7),
            ([*[Create(w) for w in waits]], 0.5), 0.3,
            ([gate.animate.set_stroke(opacity=0.35), *[grow(s) for s in short]], 0.6))

        starts += [seg(XL + 0.15 * i, arrive[i], y, GREY_D) for i, y in enumerate(LY) if i >= 2]
        waits += [DashedLine([arrive[i], y, 0], [GX - 0.05, y, 0], dash_length=0.07, stroke_width=2, color=GREY_B)
                  for i, y in enumerate(LY) if i >= 2]
        ends = [5.6 - rng.uniform(0, 0.5) for _ in LY]
        longb = [seg(GX, ends[i], y, BLUE_M) for i, y in enumerate(LY)]
        more = T("8 threads, more than the cores", 24, GREY_B).move_to([2.0, 2.55, 0])
        seq(self, "Use more threads than cores, and many operations each, so they overlap for a long time.",
            ([*[FadeIn(n) for n in names[2:]], *[grow(s) for s in starts[2:]], *[Create(w) for w in waits[2:]],
              FadeIn(more)], 0.9),
            ([*[FadeOut(s) for s in short], *[grow(b) for b in longb]], 1.4))

        def hits(n):
            g = VGroup()
            for _ in range(n):
                i = rng.randrange(len(LY))
                x = rng.uniform(GX + 0.4, 5.2)
                g.add(VGroup(Line([x - 0.17, LY[i] - 0.17, 0], [x + 0.17, LY[i] + 0.17, 0]),
                             Line([x - 0.17, LY[i] + 0.17, 0], [x + 0.17, LY[i] - 0.17, 0])).set_stroke(RED_M, 7).set_z_index(6))
            return g

        rnd = T("round 1 of 20", 26, WHITE).move_to([5.3, 2.55, 0])
        h1 = hits(5)
        self.play(FadeOut(more), FadeIn(rnd), run_time=0.4)

        def redraw(k):
            new_ends = [5.6 - rng.uniform(0, 0.5) for _ in LY]
            return [Transform(b, seg(GX, new_ends[i], LY[i], BLUE_M)) for i, b in enumerate(longb)] + \
                   [Transform(rnd, T(f"round {k} of 20", 26, WHITE).move_to([5.3, 2.55, 0]))]
        steps = [([LaggedStart(*[Create(h) for h in h1], lag_ratio=0.3)], 0.9), ([FadeOut(h1)], 0.3)]
        for k in (2, 3, 4):
            hk = hits(4)
            steps += [(redraw(k), 0.4), ([LaggedStart(*[Create(h) for h in hk], lag_ratio=0.3)], 0.6), ([FadeOut(hk)], 0.2)]
        seq(self, "Run many rounds with fresh state. Each round is one sample of the interleavings.",
            *steps)

        join = Line([5.85, 2.15, 0], [5.85, -1.55, 0], stroke_width=4, color=WHITE)
        join_l = M("join()", 24).move_to([5.85, -2.0, 0])
        inv = VGroup(T("invariant after join:", 28), M("approved == 10,000", 28, GREEN_M)).arrange(RIGHT, buff=0.3)
        inv.move_to([-0.2, -2.45, 0])
        seq(self, "After join, check an invariant. Eight threads try 2,000 one-cent refunds each, against 10,000 cents. "
                  "A correct ledger approves exactly 10,000.",
            ([FadeOut(axis_l), Create(join), FadeIn(join_l)], 0.6), 1.0, ([FadeIn(inv, shift=UP * 0.15)], 0.6))
        got = VGroup(T("racy ledger:", 28, RED_M), M("approved == 16,000", 28, RED_M)).arrange(RIGHT, buff=0.3)
        got.move_to([-0.2, -3.05, 0])
        self.beat("The racy one approves 16,000.", FadeIn(got, shift=UP * 0.15), run_time=0.8)
        res = VGroup(T("lesson demo, racy counter:  naive test failed 0 to 6 of 20 runs", 28, GREY_B),
                     T("stress test failed 20 of 20", 28, GREEN_M)).arrange(DOWN, buff=0.22).move_to([-0.2, -2.75, 0])
        fit(res, 12)
        seq(self, "On the lesson's racy counter, the naive test failed at most 6 of 20 runs. The stress test failed all 20.",
            ([FadeOut(inv), FadeOut(got)], 0.4), ([FadeIn(res, shift=UP * 0.15)], 0.6))
        self.play(FadeOut(VGroup(names, axis, gate, gate_l, *starts, *waits, *longb, rnd, join, join_l, res)), run_time=0.7)

        # ---------------- sleep vs latch ----------------
        X0, K50 = -3.0, 3.2                     # time zero, and the width of 50 ms
        head_s = M("Thread.sleep(50)", 30, GREY_A).move_to([-4.6, 2.75, 0])
        legend = VGroup(seg(0, 0.5, 0, TEAL_M, h=0.2), T("worker settles the payment", 24, TEAL_M),
                        seg(0, 0.5, 0, GREY_C, h=0.2), T("test thread waits", 24, GREY_B)).arrange(RIGHT, buff=0.2)
        legend[2].shift(RIGHT * 0.4); legend[3].shift(RIGHT * 0.4)
        legend.move_to([0, -3.15, 0])
        rows = {"laptop": 1.85, "ci": 0.9}
        rl = VGroup(T("your laptop", 26).move_to([X0 - 0.4, rows["laptop"], 0], aligned_edge=RIGHT),
                    T("busy CI", 26).move_to([X0 - 0.4, rows["ci"], 0], aligned_edge=RIGHT))
        work_lap = seg(X0, X0 + 1.1, rows["laptop"] + 0.15, TEAL_M, h=0.26)
        work_ci = seg(X0, X0 + 4.6, rows["ci"] + 0.15, TEAL_M, h=0.26)
        slp_lap = seg(X0, X0 + K50, rows["laptop"] - 0.15, GREY_C, h=0.26)
        slp_ci = seg(X0, X0 + K50, rows["ci"] - 0.15, GREY_C, h=0.26)
        ok1 = tick(True, 0.18).move_to([X0 + K50 + 0.35, rows["laptop"], 0])
        bad1 = tick(False, 0.18).move_to([X0 + K50 + 0.35, rows["ci"] - 0.15, 0])
        mark50 = DashedLine([X0 + K50, 2.4, 0], [X0 + K50, 0.45, 0], dash_length=0.07, stroke_width=2, color=GREY_B)
        mark50_l = T("50 ms: check", 24, GREY_B).move_to([X0 + K50, 2.65, 0])
        seq(self, "Next, waiting. This test submits a payment, sleeps 50 milliseconds, then checks that it settled.",
            ([FadeIn(head_s), FadeIn(rl[0]), FadeIn(legend)], 0.6), ([grow(work_lap), grow(slp_lap)], 1.2),
            ([Create(mark50), FadeIn(mark50_l), Create(ok1)], 0.5))
        q = T("fails for no reason", 26, RED_M).move_to([X0 + 6.3, rows["ci"], 0])
        seq(self, "On a busy CI machine, the work runs longer. The check comes too soon, and the test fails for no reason.",
            ([FadeIn(rl[1])], 0.4), ([grow(work_ci), grow(slp_ci)], 1.4), ([Create(bad1), FadeIn(q)], 0.5))
        quarter = T("in the lesson's runs: 24 and 32 failures in 100", 24, RED_M).move_to([0.6, 0.05, 0])
        self.beat("In the lesson's runs, it failed about a quarter of the time.", FadeIn(quarter, shift=UP * 0.1),
                  run_time=0.8)

        # latch rows below
        head_l = M("settled.await(10, SECONDS)", 30, GOLD_M).move_to([-3.6, -0.65, 0])
        rows2 = {"laptop": -1.45, "ci": -2.35}
        rl2 = VGroup(T("your laptop", 26).move_to([X0 - 0.4, rows2["laptop"], 0], aligned_edge=RIGHT),
                     T("busy CI", 26).move_to([X0 - 0.4, rows2["ci"], 0], aligned_edge=RIGHT))
        w2l = seg(X0, X0 + 1.1, rows2["laptop"] + 0.15, TEAL_M, h=0.26)
        w2c = seg(X0, X0 + 4.6, rows2["ci"] + 0.15, TEAL_M, h=0.26)
        a2l = seg(X0, X0 + 1.1, rows2["laptop"] - 0.15, GOLD_M, h=0.26, op=0.7)
        a2c = seg(X0, X0 + 4.6, rows2["ci"] - 0.15, GOLD_M, h=0.26, op=0.7)
        ok2 = tick(True, 0.18).move_to([X0 + 1.45, rows2["laptop"], 0])
        ok3 = tick(True, 0.18).move_to([X0 + 4.95, rows2["ci"], 0])
        dl = DashedLine([6.0, -0.95, 0], [6.0, -2.75, 0], dash_length=0.08, stroke_width=3, color=RED_M)
        dl_l = T("deadline: 10 s", 24, RED_M).move_to([5.7, -0.65, 0])
        seq(self, "Instead, wait for the event. A latch counts down when the payment settles, and the test awaits it, "
                  "with a deadline of 10 seconds.",
            ([FadeIn(head_l), FadeIn(rl2)], 0.6), 1.0,
            ([grow(w2l), grow(a2l), grow(w2c), grow(a2c)], 1.6), ([Create(ok2), Create(ok3)], 0.5), 1.0,
            ([Create(dl), FadeIn(dl_l)], 0.6))
        zero = T("failed 0 times", 24, GREEN_M).move_to([X0 + 7.0, rows2["laptop"], 0])
        self.beat("Fast when the work is fast, patient when the machine is slow. It failed zero times.",
                  FadeIn(zero), run_time=0.8)
        self.play(FadeOut(VGroup(head_s, legend, rl, work_lap, work_ci, slp_lap, slp_ci, ok1, bad1, mark50, mark50_l,
                                 q, quarter, head_l, rl2, w2l, w2c, a2l, a2c, ok2, ok3, dl, dl_l, zero)),
                  run_time=0.7)

        jc = code(["CountDownLatch settled = new CountDownLatch(1);",
                   "store.onSettled(id -> settled.countDown());",
                   "worker.submit(payment);",
                   "assertThat(settled.await(10, SECONDS)).isTrue();"], 24)
        kc = code(["val settled = CountDownLatch(1)",
                   "store.onSettled { settled.countDown() }",
                   "worker.submit(payment)",
                   "assertThat(settled.await(10, SECONDS)).isTrue()"], 24)
        for b in (jc, kc):
            b[1].set_color(TEAL_M); b[3].set_color(GOLD_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin: the same Java class", kc)).arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.1, 0])
        self.beat("In Java and Kotlin, it is the same four lines.", FadeIn(cg, shift=UP * 0.2), run_time=1.2)
        self.wait(0.3)
        self.play(FadeOut(cg), run_time=0.6)

        # ---------------- jcstress ----------------
        head_j = T("jcstress", 36, PURPLE_M).move_to([0, 2.75, 0])
        jn = T("Java only", 22, GREY_B).next_to(head_j, RIGHT, buff=0.3)
        a1 = VGroup(T("actor 1", 26, BLUE_M), M("r1 = ++refunds", 26, BLUE_M)).arrange(DOWN, buff=0.15)
        a2 = VGroup(T("actor 2", 26, TEAL_M), M("r2 = ++refunds", 26, TEAL_M)).arrange(DOWN, buff=0.15)
        actors = VGroup(a1, a2).arrange(DOWN, buff=0.6).move_to([-4.0, 0.4, 0])
        self.beat("Some races need millions of tries. jcstress, the OpenJDK harness, does that.",
                  FadeIn(head_j), FadeIn(jn), run_time=1.0)
        outs = [("1, 2", 3.6, GREEN_M, "acceptable"), ("2, 1", 3.3, GREEN_M, "acceptable"),
                ("1, 1", 0.35, GOLD_M, "interesting: an increment lost")]
        bars, labs = [], []
        for j, (o, w, col, lb) in enumerate(outs):
            y = 1.3 - j * 0.95
            labs.append(M(o, 28).move_to([-0.6, y, 0], aligned_edge=RIGHT))
            b = seg(-0.3, -0.3 + w, y, col, h=0.5)
            bars.append(b)
            labs.append(T(lb, 24, col).next_to(b, RIGHT, buff=0.2))
        seq(self, "Two actors increment one counter, and record what they read. "
                  "It runs this millions of times, and counts each outcome.",
            ([FadeIn(actors)], 0.8), 2.0,
            ([*[FadeIn(labs[2 * j]) for j in range(3)], *[grow(b) for b in bars]], 1.6))
        seq(self, "1, 2 and 2, 1 are acceptable. 1, 1 means both read zero, so an increment was lost. "
                  "It is labeled interesting: the race you are looking for.",
            ([FadeIn(labs[1]), FadeIn(labs[3])], 0.6), 1.6, ([FadeIn(labs[5]), Indicate(labs[4], color=GOLD_M)], 0.8))
        forb = T("label an outcome FORBIDDEN: one sighting fails the test", 26, RED_M).move_to([0.4, -1.8, 0])
        fit(forb, 12)
        self.beat("Label an outcome forbidden, and one sighting fails the test.", FadeIn(forb, shift=UP * 0.15),
                  run_time=0.8)
        self.play(FadeOut(VGroup(head_j, jn, actors, *bars, *labs, forb)), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = T("Make threads collide on purpose, and wait for events, not time.", 32).move_to([0, 2.3, 0])
        rule2 = T("A pass means: not found this time.", 32, GOLD_M).move_to([0, 1.65, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule.width))
        self.beat("The rule. Make threads collide on purpose, wait for events instead of time, "
                  "and read a pass as: not found this time.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A test starts two threads, each makes one refund,", 28).move_to([0, 0.15, 0])
        chk2 = T("and it has never failed. Is the ledger safe?", 28).move_to([0, -0.45, 0])
        VGroup(chk, chk2).scale(min(1, 12 / chk.width))
        self.beat("Check yourself. A test starts two threads, each makes one refund, and it has never failed. "
                  "Is the ledger safe?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.3)
        ans = T("You can't tell: the refunds probably never overlapped.", 28, GOLD_M).move_to([0, -1.7, 0])
        fit(ans, 12)
        self.beat("You can't tell. The refunds probably never overlapped. A pass only means this run found nothing.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.3)
