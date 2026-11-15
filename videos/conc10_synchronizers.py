from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bCountDownLatch\b", "count down latch"), (r"\bCyclicBarrier\b", "cyclic barrier"),
    (r"\bcountDown\b", "count down"),
]


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
    """Speak one line and play several animation groups one after another inside it.
    A step is (animations, run_time), (callable returning animations, run_time), or a bare number for a pause."""
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
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


WAITER, LOADER, COUNT = BLUE_M, TEAL_M, GOLD_M
GX = 1.4                       # every lane has its gate at the same x
YL, YB, YS = 2.25, 0.0, -2.25  # lane centres: latch, barrier, semaphore


def dot(color, r=0.19):
    return Dot(radius=r, color=color).set_z_index(5)


def gate(yc):
    return Line([GX, yc - 0.82, 0], [GX, yc + 0.4, 0], stroke_width=11, color=RED_M)


def counter(yc, text):
    r = RoundedRectangle(corner_radius=0.08, width=1.1, height=0.56, stroke_color=COUNT, stroke_width=2.5)
    r.set_fill(BLACK, 1).move_to([GX + 0.8, yc + 0.62, 0])
    return VGroup(r, M(text, 30, COUNT).move_to(r))


def recount(c, text, **kw):
    return Transform(c[1], M(text, 30, COUNT).move_to(c[0]), **kw)


def opened(g):
    return g.animate.set_color(GREEN_M).set_stroke(width=4).set_opacity(0.8)


def closed(g):
    return g.animate.set_color(RED_M).set_stroke(width=11).set_opacity(1)


def permit():
    return Square(0.3, stroke_width=0).set_fill(COUNT, 1).set_z_index(6)


def spark(src, dst, color=COUNT, rt=0.6):
    d = Dot(radius=0.07, color=color).move_to(src).set_z_index(7)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=rt).move_to(dst), FadeOut(d, run_time=0.1))


class Conc10Synchronizers(VoiceScene):
    """conc-10, section 0: three lanes with one gate each. CountDownLatch: events count it down to zero, the gate opens
    for good (one-shot). CyclicBarrier: the last of four to arrive runs the action, all go, the gate closes again
    (cyclic); a Phaser lets the group shrink. Semaphore: permits taken and given back; a release without an acquire adds
    a permit. Then all three side by side, the constructors in Java and Kotlin, the rule and a check."""

    def construct(self):
        self.title_card("Synchronizers", "a latch, a barrier and a semaphore, side by side")

        # ---- the three lanes ----
        def lane_label(name, sub, yc):
            return VGroup(M(name, 26), T(sub, 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.14) \
                .move_to([-6.3, yc, 0], aligned_edge=LEFT)

        lab_l = lane_label("CountDownLatch", "waits for events, once", YL)
        lab_b = lane_label("CyclicBarrier", "waits for a group, every round", YB)
        lab_s = lane_label("Semaphore", "limits how many at once", YS)
        seps = VGroup(*[DashedLine([-6.3, y, 0], [6.3, y, 0], dash_length=0.08, stroke_width=1.5, color=GREY_D)
                        for y in (1.125, -1.125)])

        # ---- latch: the problem, then the gate ----
        g_l = gate(YL)
        c_l = counter(YL, "3")
        loaders = VGroup(*[dot(LOADER) for _ in range(3)]).arrange(DOWN, buff=0.28).move_to([-2.3, YL, 0])
        ld_t = T("loaders", 22, LOADER).next_to(loaders, RIGHT, buff=0.2).align_to(loaders, UP)
        opener = dot(WAITER).move_to([-0.2, YL - 0.35, 0])
        op_t = T("opener", 24, WAITER).next_to(opener, LEFT, buff=0.15)
        op_t.add_updater(lambda m: m.next_to(opener, LEFT, buff=0.15))

        self.beat("Before this service takes traffic, three caches must be warm. "
                  "The thread that opens the port must wait for three loaders.",
                  FadeIn(lab_l), FadeIn(loaders), FadeIn(ld_t), FadeIn(opener), FadeIn(op_t), run_time=1.6)
        seq(self, "A CountDownLatch is a gate with a counter. It starts at three. "
                  "The opener calls await, and stops at the gate.",
            ([Create(g_l), FadeIn(c_l)], 0.8), 2.0, ([opener.animate.move_to([GX - 0.3, YL - 0.35, 0])], 1.0))

        def count_down(i, to):
            def f():
                return [spark(loaders[i].get_center(), c_l.get_center(), rt=0.5),
                        Succession(Wait(0.55), AnimationGroup(recount(c_l, to), loaders[i].animate.set_opacity(0.3),
                                                              run_time=0.3))]
            return f

        seq(self, "Each loader calls countDown when it is done. Three, two, one.",
            1.4, (count_down(0, "2"), 0.9), 0.3, (count_down(1, "1"), 0.9), 0.3, (count_down(2, "0"), 0.9))
        seq(self, "At zero, the gate opens, and every thread waiting there goes on.",
            ([opened(g_l), Indicate(c_l[1], color=GREEN_M)], 0.8), ([opener.animate.move_to([4.0, YL - 0.35, 0])], 1.2))
        late = dot(WAITER).move_to([-0.2, YL - 0.7, 0])
        late_t = T("late", 24, WAITER).next_to(late, LEFT, buff=0.15)
        late_t.add_updater(lambda m: m.next_to(late, LEFT, buff=0.15))
        self.beat("Now a late thread calls await. Does it wait?", FadeIn(late), FadeIn(late_t), run_time=0.6, after=1.6)
        seq(self, "No. The gate stays open. The count never goes back up, and there is no reset. A latch is one-shot.",
            ([late.animate.move_to([5.4, YL - 0.7, 0])], 1.3), 1.2, ([Indicate(c_l[1], color=COUNT, scale_factor=1.4)], 0.9))

        # ---- barrier ----
        g_b = gate(YB)
        c_b = counter(YB, "0/4")
        slots = [YB + 0.6, YB + 0.2, YB - 0.2, YB - 0.6]
        starts = [-2.4, -1.6, -0.8, -2.0]
        workers = VGroup(*[dot(WAITER).move_to([starts[i], slots[i], 0]) for i in range(4)])
        day = T("day 1", 24, GREY_A).move_to([-1.2, YB + 0.9, 0])
        act = VGroup(RoundedRectangle(corner_radius=0.1, width=2.6, height=0.5, stroke_color=COUNT, stroke_width=2.5)
                     .set_fill(BLACK, 1), T("barrier action", 22, COUNT))
        act[1].move_to(act[0])
        act.move_to([4.95, YB + 0.62, 0])
        self.beat("Next, four workers simulate one day each. Nobody may start day two until all four finish.",
                  FadeIn(seps[0]), FadeIn(lab_b), FadeIn(workers), FadeIn(day), Create(g_b), FadeIn(c_b), run_time=1.6)

        def arrive(i, n):
            return [workers[i].animate.move_to([GX - 0.3, slots[i], 0]), recount(c_b, f"{n}/4")]

        seq(self, "A CyclicBarrier counts threads, not events. Each worker calls await at the line, and waits there.",
            1.8, (arrive(2, 1), 0.8), 0.4, (arrive(0, 2), 0.8), 0.4, (arrive(3, 3), 0.8))
        seq(self, "The fourth to arrive runs the barrier action once, here adding up the day. Then all four go on together.",
            (arrive(1, 4), 0.9), ([FadeIn(act, scale=0.9), Indicate(c_b[1], color=WHITE)], 0.9), 1.2,
            ([opened(g_b), *[w.animate.move_to([3.0, slots[i], 0]) for i, w in enumerate(workers)]], 1.3))
        self.beat("Day two. Is the gate still open, like the latch?",
                  Transform(day, T("day 2", 24, GREY_A).move_to(day)), FadeOut(act),
                  *[w.animate.move_to([starts[i], slots[i], 0]) for i, w in enumerate(workers)],
                  recount(c_b, "0/4"), run_time=1.2, after=1.6)
        seq(self, "No. It closed again behind them. The barrier resets itself every round. That is the cyclic part.",
            ([closed(g_b), Flash(g_b.get_center(), color=RED_M, flash_radius=0.6)], 0.8), 1.8,
            ([Indicate(c_b[1], color=WHITE)], 0.8))

        # phaser, in one beat: the group shrinks
        seq(self, "A Phaser is a barrier whose group can change. A party can deregister and leave. "
                  "Each phase then waits only for the parties still registered.",
            1.4, ([workers[3].animate.shift(DOWN * 0.5 + LEFT * 0.4).set_opacity(0), recount(c_b, "0/3")], 1.0), 1.6,
            ([*[workers[i].animate.move_to([GX - 0.3, slots[i], 0]) for i in range(3)], recount(c_b, "3/3")], 1.0),
            ([opened(g_b), *[workers[i].animate.move_to([3.0, slots[i], 0]) for i in range(3)]], 1.0))

        # ---- semaphore ----
        area = RoundedRectangle(corner_radius=0.12, width=3.7, height=1.6, stroke_color=GREY_B, stroke_width=2.5)
        area.move_to([4.3, YS - 0.05, 0])
        area_t = T("calls to the issuer", 22, GREY_B).move_to(area.get_top() + DOWN * 0.27)
        tray = RoundedRectangle(corner_radius=0.08, width=0.55, height=1.4, stroke_color=COUNT, stroke_width=2)
        tray.move_to([GX, YS - 0.05, 0])
        pslots = [YS + 0.37, YS - 0.05, YS - 0.47]
        perms = [permit().move_to([GX, y, 0]) for y in pslots]
        inside = [np.array([3.2, YS - 0.3, 0]), np.array([4.3, YS - 0.3, 0]), np.array([5.4, YS - 0.3, 0])]
        thr = [dot(WAITER).move_to([x, YS - 0.3, 0]) for x in (-2.4, -1.7, -1.0, -0.3)]
        self.beat("Last, the card issuer allows 20 calls at once. A Semaphore holds permits. Here, three.",
                  FadeIn(seps[1]), FadeIn(lab_s), FadeIn(area), FadeIn(area_t), FadeIn(tray), *[FadeIn(p, scale=0.5) for p in perms],
                  *[FadeIn(t) for t in thr], run_time=1.6)

        def take(i, k, dest):
            """thread i walks to the tray, picks up permit k, and goes into the area with it."""
            def f():
                return [Succession(thr[i].animate(run_time=0.5).move_to([GX - 0.55, perms[k].get_y(), 0]),
                                   AnimationGroup(thr[i].animate(run_time=0.7).move_to(dest),
                                                  perms[k].animate(run_time=0.7).move_to(dest + UP * 0.32)))]
            return f

        seq(self, "acquire takes a permit. Only a thread with a permit calls the issuer.",
            0.4, (take(0, 0, inside[0]), 1.2), (take(1, 1, inside[1]), 1.2), (take(2, 2, inside[2]), 1.2))
        seq(self, "The fourth thread finds the tray empty, so it waits.",
            ([thr[3].animate.move_to([GX - 0.55, YS - 0.05, 0])], 0.8), ([Indicate(tray, color=RED_M)], 0.8))
        seq(self, "When a call finishes, release gives the permit back, and the waiting thread takes it.",
            ([thr[0].animate.move_to([6.0, YS - 0.3, 0]).set_opacity(0), perms[0].animate.move_to([GX, pslots[0], 0])], 1.1),
            0.6, (take(3, 0, inside[0]), 1.2))
        rogue = dot(GREY_B).move_to([-1.0, YS - 0.3, 0])
        rogue_t = T("never acquired", 24, GREY_B).next_to(rogue, LEFT, buff=0.15)
        rogue_t.add_updater(lambda m: m.next_to(rogue, LEFT, buff=0.15))
        self.beat("Now a thread that never took a permit calls release. What happens?",
                  FadeIn(rogue), FadeIn(rogue_t), rogue.animate.move_to([GX - 0.5, YS - 0.3, 0]), run_time=1.2, after=1.6)
        extra = permit().move_to([GX, pslots[1], 0])
        newcomer = dot(WAITER).move_to([-2.4, YS - 0.3, 0])
        inside4 = np.array([3.75, YS - 0.3, 0])
        seq(self, "The semaphore just adds a permit. Permits have no owner. "
                  "Now four threads fit, and the limit has quietly drifted.",
            (lambda: [rogue_t.clear_updaters(), FadeIn(extra, scale=2.0), FadeOut(rogue), FadeOut(rogue_t)][1:], 0.8), 1.4,
            ([FadeIn(newcomer)], 0.3),
            ([Succession(newcomer.animate(run_time=0.6).move_to([GX - 0.55, pslots[1], 0]),
                         AnimationGroup(newcomer.animate(run_time=0.7).move_to(inside4 + DOWN * 0.15),
                                        extra.animate(run_time=0.7).move_to(inside4 + UP * 0.17)))], 1.3),
            ([Indicate(area, color=RED_M, scale_factor=1.04)], 0.8))

        # ---- side by side, in motion ----
        movers = VGroup(opener, late, op_t, late_t, *workers, *thr, *perms, extra, newcomer, loaders, ld_t, day)
        op_t.clear_updaters(); late_t.clear_updaters()
        self.play(FadeOut(movers), closed(g_l), closed(g_b), recount(c_l, "3"), recount(c_b, "0/4"), run_time=0.8)

        o2 = dot(WAITER).move_to([-0.2, YL - 0.35, 0])
        ld2 = VGroup(*[dot(LOADER) for _ in range(3)]).arrange(DOWN, buff=0.3).move_to([-2.3, YL, 0])
        w2 = VGroup(*[dot(WAITER).move_to([starts[i], slots[i], 0]) for i in range(4)])
        p2 = [permit().move_to([GX, y, 0]) for y in pslots]
        t2 = [dot(WAITER).move_to([x, YS - 0.3, 0]) for x in (-2.4, -1.7, -1.0, -0.3)]
        self.play(FadeIn(VGroup(o2, ld2, w2, *p2, *t2)), run_time=0.5)

        def lat():
            return Succession(o2.animate(run_time=0.8).move_to([GX - 0.3, YL - 0.35, 0]),
                              spark(ld2[0].get_center(), c_l.get_center(), rt=0.4), recount(c_l, "2", run_time=0.2),
                              spark(ld2[1].get_center(), c_l.get_center(), rt=0.4), recount(c_l, "1", run_time=0.2),
                              spark(ld2[2].get_center(), c_l.get_center(), rt=0.4), recount(c_l, "0", run_time=0.2),
                              g_l.animate(run_time=0.4).set_color(GREEN_M).set_stroke(width=4).set_opacity(0.8),
                              o2.animate(run_time=0.9).move_to([4.0, YL - 0.35, 0]))

        def bar():
            arr = [w2[i].animate(run_time=0.6).move_to([GX - 0.3, slots[i], 0]) for i in (2, 0, 3, 1)]
            return Succession(arr[0], recount(c_b, "1/4", run_time=0.15), arr[1], recount(c_b, "2/4", run_time=0.15),
                              arr[2], recount(c_b, "3/4", run_time=0.15), arr[3], recount(c_b, "4/4", run_time=0.15),
                              AnimationGroup(g_b.animate.set_color(GREEN_M).set_stroke(width=4).set_opacity(0.8),
                                             *[w.animate.move_to([3.0, slots[i], 0]) for i, w in enumerate(w2)], run_time=0.9),
                              AnimationGroup(g_b.animate.set_color(RED_M).set_stroke(width=11).set_opacity(1), recount(c_b, "0/4"), run_time=0.4))

        def sem():
            steps = []
            for i in range(3):
                steps += [t2[i].animate(run_time=0.4).move_to([GX - 0.55, p2[i].get_y(), 0]),
                          AnimationGroup(t2[i].animate.move_to(inside[i]), p2[i].animate.move_to(inside[i] + UP * 0.32),
                                         run_time=0.6)]
            steps += [t2[3].animate(run_time=0.6).move_to([GX - 0.55, YS - 0.05, 0]), Indicate(tray, color=RED_M, run_time=0.8)]
            return Succession(*steps)

        seq(self, "Side by side: a latch waits for events, once. A barrier waits for a group, every round. "
                  "A semaphore limits how many are inside.",
            ([lat(), bar(), sem()], 5.6))

        # ---- code ----
        lanes = VGroup(lab_l, lab_b, lab_s, seps, g_l, c_l, g_b, c_b, area, area_t, tray)
        self.play(FadeOut(lanes), FadeOut(VGroup(o2, ld2, w2, *p2, *t2)), run_time=0.8)
        title = T("One constructor each", 40).to_edge(UP, buff=0.6)
        jc = code(["var warm = new CountDownLatch(3);",
                   "var day = new CyclicBarrier(4, this::sumDay);",
                   "var issuer = new Semaphore(20);"], 26)
        kc = code(["val warm = CountDownLatch(3)",
                   "val day = CyclicBarrier(4) { sumDay() }",
                   "val issuer = Semaphore(20)"], 26)
        cols = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        cols.scale(min(1, 12 / cols.width)).next_to(title, DOWN, buff=0.5)
        calls = T("count events with a latch, meet with a barrier, limit with a semaphore", 26, COUNT)
        calls.scale(min(1, 12 / calls.width)).next_to(cols, DOWN, buff=0.6)
        self.beat("In code, each is one constructor, in Java and in Kotlin.",
                  Write(title), FadeIn(cols, shift=UP * 0.2), run_time=1.6)
        self.beat("The rule: count events with a latch, meet with a barrier, limit with a semaphore.",
                  FadeIn(calls), run_time=0.8)
        self.play(FadeOut(VGroup(title, cols, calls)), run_time=0.7)

        # ---- check question, on the lanes ----
        self.play(FadeIn(VGroup(lab_l, lab_b, lab_s, seps)), FadeIn(VGroup(g_l, c_l, g_b, c_b)),
                  FadeIn(VGroup(area, area_t, tray)), recount(c_l, "0"), run_time=0.8)
        self.beat("Quick check. Four workers settle twelve monthly batches. Each month must finish before the next starts. "
                  "Latch or barrier?", after=2.2)
        self.beat("A barrier. A latch would stay open after the first month.",
                  Indicate(lab_b, color=WAITER, scale_factor=1.08), run_time=1.2)
        self.wait(0.8)
