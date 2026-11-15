from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bavailableProcessors\b", "available processors"), (r"\bGoetz's\b", "Getz's")]


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
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def counter(fmt, fn, pos, size=30, color=WHITE, edge=ORIGIN):
    """Text that shows fmt.format(fn()); it changes in place with become(), so no stale copy is ever drawn."""
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = T(fmt.format(n), size, color).move_to(pos, aligned_edge=edge)
        return cache[n]
    n0 = fn()
    holder = get(n0).copy()
    holder.shown = n0

    def upd(m):
        n = fn()
        if n != m.shown:
            m.become(get(n))
            m.shown = n
    holder.add_updater(upd)
    return holder


def tchip(n):
    c = Circle(radius=0.3, stroke_color=BLUE_M, stroke_width=3).set_fill(dark(BLUE_M, 0.25), 1)
    return VGroup(c, T(str(n), 26).move_to(c)).set_z_index(5)


class Exec03Sizing(VoiceScene):
    """exec-03, section 2: one thread per core for CPU work; threads that wait leave the core free;
    Little's law as requests flowing through a pool (400/s x 250 ms = 100; 50 threads finish 200/s)."""

    def construct(self):
        self.title_card("How many threads?", "cores, waiting, and Little's law")

        # =============== part 1: CPU-bound work ===============
        CX = [-5.7, -4.3, -2.9, -1.5]
        cores = VGroup(*[RoundedRectangle(corner_radius=0.1, width=1.1, height=1.1, stroke_color=TEAL_M, stroke_width=3)
                         .set_fill(dark(TEAL_M, 0.1), 1).move_to([x, 2.0, 0]) for x in CX])
        core_lab = T("4 cores", 28, TEAL_M).move_to([-3.6, 3.0, 0])
        wbox = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=5.4, height=0.85, stroke_color=GREY_B,
                                               stroke_width=2), num_dashes=60).move_to([-3.6, 0.45, 0])
        wlab = T("waiting for a core", 24, GREY_B).move_to([-3.6, -0.22, 0])
        WX = [-5.4, -4.2, -3.0, -1.8]

        def new_pile():
            return VGroup(*[Square(0.3, stroke_width=0).set_fill(GOLD_M, 0.9) for _ in range(32)]
                          ).arrange_in_grid(4, 8, buff=0.12).move_to([-3.6, -2.05, 0])
        pile = new_pile()
        pile_lab = T("32 hashing tasks", 26, GOLD_M).move_to([-3.6, -0.95, 0])

        head = T("time for all 32 tasks", 26, GREY_B).move_to([3.5, 3.0, 0])
        vals = [(1, 359), (2, 171), (4, 92), (8, 96), (16, 98)]
        RY = [2.2, 1.4, 0.6, -0.2, -1.0]
        BX, SC = 2.35, 3.0 / 359
        rlab = [T(f"{n} thread" + ("s" if n > 1 else ""), 26).move_to([0.6, y, 0], aligned_edge=LEFT) for (n, _), y in zip(vals, RY)]
        bars = [Rectangle(width=v * SC, height=0.42).set_fill(GOLD_M, 0.85).set_stroke(width=0).move_to([BX, y, 0], aligned_edge=LEFT)
                for (_, v), y in zip(vals, RY)]
        vlab = [T(f"{v} ms", 26, RED_M if n >= 8 else WHITE).next_to(b, RIGHT, buff=0.15) for (n, v), b in zip(vals, bars)]

        self.beat("32 hashing tasks, with no I/O and no locks, on a machine with four cores.",
                  FadeIn(VGroup(cores, core_lab)), FadeIn(VGroup(wbox, wlab)), FadeIn(pile_lab),
                  LaggedStart(*[FadeIn(s) for s in pile], lag_ratio=0.03), FadeIn(head), run_time=2.2)

        chips = [tchip(i + 1) for i in range(8)]
        shown = [0]

        def place(n):
            out = []
            for i in range(shown[0], n):
                c = chips[i]
                c.move_to([CX[i], 2.0, 0] if i < 4 else [WX[i - 4], 0.45, 0])
                out.append(FadeIn(c, scale=0.6))
            shown[0] = n
            return out

        def drain(p, k, rt, lag=None):
            """The tasks are used up k at a time (one per running thread), in place."""
            batches = [VGroup(*p[i:i + k]) for i in range(0, len(p), k)]
            return LaggedStart(*[FadeOut(b, scale=0.4) for b in batches], lag_ratio=1.0, run_time=rt)

        # 1, 2 and 4 threads
        seq(self, "One thread works through them in 359 ms.",
            ([*place(1), FadeIn(rlab[0])], 0.6),
            ([drain(pile, 1, 2.4), GrowFromEdge(bars[0], LEFT, run_time=2.4)], 2.4),
            ([FadeIn(vlab[0])], 0.3))
        pile2, pile4 = new_pile(), new_pile()
        seq(self, "Two threads take 171. Four take 92.",
            ([FadeIn(pile2), *place(2), FadeIn(rlab[1])], 0.5),
            ([drain(pile2, 2, 1.0), GrowFromEdge(bars[1], LEFT, run_time=1.0)], 1.0),
            ([FadeIn(vlab[1])], 0.2),
            ([FadeIn(pile4), *place(4), FadeIn(rlab[2])], 0.3),
            ([drain(pile4, 4, 0.6), GrowFromEdge(bars[2], LEFT, run_time=0.6)], 0.6),
            ([FadeIn(vlab[2])], 0.3))

        q8 = T("?", 30, YELLOW_M).move_to([BX + 0.4, RY[3], 0])
        pile = new_pile()
        self.beat("So how long will eight threads take?",
                  FadeIn(pile), *place(8), FadeIn(rlab[3]), FadeIn(q8), run_time=1.0)
        self.wait(2.0)

        # 8 threads: four run, four wait, they swap, and the bar ends where the 4-thread bar did
        half1, half2 = VGroup(*pile[:16]), VGroup(*pile[16:])
        b8 = bars[3]
        b8_half = b8.copy().stretch_to_fit_width(b8.width * 0.5, about_edge=LEFT)

        def swap():
            return [chips[i].animate.move_to([WX[i], 0.45, 0]) for i in range(4)] + \
                   [chips[i + 4].animate.move_to([CX[i], 2.0, 0]) for i in range(4)]

        def swap_back():
            return [chips[i].animate.move_to([CX[i], 2.0, 0]) for i in range(4)] + \
                   [chips[i + 4].animate.move_to([WX[i], 0.45, 0]) for i in range(4)]
        seq(self, "96 ms. No faster. Sixteen threads take 98.",
            ([FadeOut(q8), drain(half1, 4, 0.6), GrowFromEdge(b8_half, LEFT, run_time=0.6)], 0.6),
            (swap, 0.5),
            ([drain(half2, 4, 0.6), Transform(b8_half, b8)], 0.6),
            ([FadeIn(vlab[3])], 0.3), 0.6,
            ([FadeIn(rlab[4]), GrowFromEdge(bars[4], LEFT), FadeIn(vlab[4])], 0.7))
        seq(self, "A core runs one thread at a time. Thread five only gets a core by taking it from another thread. "
                  "That switch costs time, and adds no work.",
            2.2, (swap_back, 0.7), 0.6, (swap, 0.7), 0.4,
            ([Indicate(VGroup(vlab[2], vlab[3], vlab[4]), color=RED_M)], 1.0))
        rule1 = T("CPU-bound: about one thread per core", 26, TEAL_M).move_to([0.6, -2.0, 0], aligned_edge=LEFT)
        rule1b = M("availableProcessors() = 4", 24, BLUE_M).move_to([0.6, -2.6, 0], aligned_edge=LEFT)
        rule1c = T("in a container: the container's CPU limit", 22, GREY_B).move_to([0.6, -3.1, 0], aligned_edge=LEFT)
        self.beat("This is CPU-bound work: about one thread per core, the number availableProcessors returns.",
                  FadeIn(rule1, shift=UP * 0.15), FadeIn(rule1b, shift=UP * 0.15), FadeIn(rule1c), run_time=1.4)
        part1 = VGroup(cores, core_lab, wbox, wlab, pile_lab, head, *rlab, b8_half, *[bars[i] for i in (0, 1, 2, 4)], *vlab,
                       *chips, rule1, rule1b, rule1c)
        self.play(FadeOut(part1), run_time=0.8)

        # =============== part 2: work that waits ===============
        X0, X1 = -4.2, 5.8
        PX = (X1 - X0) / 200

        def tx(ms):
            return X0 + ms * PX

        def seg(a, b, y, color, op, h=0.26):
            return Rectangle(width=(b - a) * PX, height=h).set_fill(color, op).set_stroke(width=0).move_to([tx(a), y, 0], aligned_edge=LEFT)
        track = Rectangle(width=X1 - X0, height=0.42, stroke_color=TEAL_M, stroke_width=2.5).move_to([(X0 + X1) / 2, 2.6, 0])
        tlab = T("core", 26, TEAL_M).next_to(track, LEFT, buff=0.25)
        TY = [1.7 - 0.42 * k for k in range(10)]
        thr_lab = [T(f"thread {k + 1}", 26, BLUE_M).move_to([X0 - 0.25, y, 0], aligned_edge=RIGHT) for k, y in enumerate(TY)]
        rows = []
        for k, y in enumerate(TY):
            g = VGroup(seg(20 * k, 20 * k + 20, y, GOLD_M, 0.9))
            if k > 0:
                g.add(seg(0, 20 * k, y, GREY_M, 0.35))
            if k < 9:
                g.add(seg(20 * k + 20, 200, y, GREY_M, 0.35))
            rows.append(g)
        busy = [seg(20 * k, 20 * k + 20, 2.6, GOLD_M, 0.9, h=0.3) for k in range(10)]
        axis = Line([X0, -2.45, 0], [X1, -2.45, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([tx(m), -2.38, 0], [tx(m), -2.52, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([tx(m), -2.82, 0])) for m in (0, 100, 200)])
        c_note = T("computes 20 ms", 24, GOLD_M).move_to([tx(10) + 0.3, 2.06, 0])
        w_note = T("waits 180 ms for the card issuer", 24, GREY_A).move_to([tx(115), 2.06, 0])
        idle = T("idle", 24, GREY_B).move_to([tx(110), 2.6, 0])

        self.beat("Most backend work waits. An authorization computes for 20 ms, then waits 180 ms for the card issuer.",
                  FadeIn(VGroup(track, tlab, axis, ticks)), FadeIn(thr_lab[0]), FadeIn(rows[0]), FadeIn(busy[0]),
                  FadeIn(c_note), FadeIn(w_note), run_time=2.0)
        self.beat("While it waits, the thread needs no CPU. The core sits idle nine tenths of the time.",
                  FadeIn(idle), Indicate(track, color=GREY_B, scale_factor=1.02), run_time=1.4)
        q = T("?", 30, YELLOW_M).next_to(thr_lab[1], LEFT, buff=0.3)
        self.beat("How many threads does it take to keep this one core busy?", FadeIn(q), run_time=0.8)
        self.wait(2.0)
        seq(self, "About ten. The wait is nine times the compute, so while one thread computes, nine can wait. "
                  "This is I/O-bound work.",
            ([FadeOut(q), FadeOut(idle),
              LaggedStart(*[AnimationGroup(FadeIn(thr_lab[k]), FadeIn(rows[k]), FadeIn(busy[k])) for k in range(1, 10)],
                          lag_ratio=0.35)], 3.6))
        gantt = VGroup(track, tlab, axis, ticks, *thr_lab, *rows, *busy, c_note, w_note)
        f1 = T("threads = cores × target CPU use × (1 + wait / compute)", 32)
        f2 = T("8 × 0.8 × (1 + 180 / 20) = 64", 32, GOLD_M)
        f3 = T("measure wait and compute; don't guess them", 26, GREY_B)
        fg_ = VGroup(f1, f2, f3).arrange(DOWN, buff=0.45)
        fg_.scale(min(1, 12 / fg_.width)).move_to(UP * 0.2)
        self.play(FadeOut(gantt), run_time=0.7)
        seq(self, "Goetz's formula says the same. Eight cores at 80 percent CPU: 64 threads.",
            ([FadeIn(f1, shift=UP * 0.15)], 1.0), 1.6, ([FadeIn(f2, shift=UP * 0.15)], 0.8), 0.6, ([FadeIn(f3)], 0.6))
        self.play(FadeOut(fg_), run_time=0.6)

        # =============== part 3: Little's law ===============
        BL, BR = -3.5, 3.5                       # the service box: 250 ms wide
        W_MS, GAP = 250.0, 2.5                   # 400 a second: one arrival every 2.5 ms
        LANE4 = [0.6, 0.2, -0.2, -0.6]
        sbox = RoundedRectangle(corner_radius=0.15, width=BR - BL + 0.3, height=1.8, stroke_color=BLUE_M, stroke_width=3)
        sbox.set_fill(dark(BLUE_M, 0.08), 1).move_to([0, 0, 0])
        door = arrow(np.array([-5.6, 0, 0]), np.array([BL - 0.25, 0, 0]), color=YELLOW_M)
        door_lab = T("400 arrive each second", 26, YELLOW_M).move_to([-4.6, 1.35, 0])
        out_arrow = arrow(np.array([BR + 0.25, 0, 0]), np.array([5.6, 0, 0]), color=GREY_B)
        out_lab = T("done", 26, GREY_B).next_to(out_arrow, UP, buff=0.15)
        span = VGroup(Line([BL, -1.25, 0], [BR, -1.25, 0], stroke_width=2, color=GREY_B),
                      Line([BL, -1.12, 0], [BL, -1.38, 0], stroke_width=2, color=GREY_B),
                      Line([BR, -1.12, 0], [BR, -1.38, 0], stroke_width=2, color=GREY_B))
        span_lab = T("each one stays 250 ms", 26, GREY_A).move_to([0, -1.65, 0])

        t1 = ValueTracker(-1.0)
        N1 = 300
        dots1 = VGroup(*[Dot(radius=0.05, color=YELLOW_M) for _ in range(N1)]).set_z_index(3)
        dots1[0].scale(2.0).set_color(GOLD_M).set_z_index(4)

        def upd1(g):
            t = t1.get_value()
            for i, d in enumerate(g):
                a = i * GAP
                if a <= t < a + W_MS:
                    d.set_opacity(1).move_to([BL + (t - a) / W_MS * (BR - BL), LANE4[i % 4], 0])
                else:
                    d.set_opacity(0)
        dots1.add_updater(upd1)
        upd1(dots1)

        def inside1():
            t = t1.get_value()
            return sum(1 for i in range(N1) if i * GAP <= t < i * GAP + W_MS)
        cnt1 = counter("inside: {}", inside1, [0, 1.6, 0], 32)
        q_in = T("inside: ?", 32).move_to([0, 1.6, 0])

        self.beat("From the traffic side: 400 authorizations arrive each second, and each one stays 250 ms.",
                  FadeIn(sbox), GrowArrow(door), FadeIn(door_lab), GrowArrow(out_arrow), FadeIn(out_lab),
                  FadeIn(span), FadeIn(span_lab), run_time=2.2)
        self.beat("How many are inside at any moment?", FadeIn(q_in), run_time=0.8)
        self.wait(2.0)
        self.add(dots1)
        self.remove(q_in)
        self.add(cnt1)
        follow = Triangle(color=GOLD_M, fill_opacity=1, stroke_width=0).scale(0.12).rotate(PI).set_z_index(4)
        follow.add_updater(lambda m: m.move_to([dots1[0].get_x(), 1.12, 0]))
        seq(self, "Follow the first one. While it crosses, new ones keep arriving behind it. "
                  "When it leaves, 100 are inside, and the count stays there.",
            ([t1.animate(rate_func=linear).set_value(0.0), FadeIn(follow)], 0.3),
            ([t1.animate(rate_func=linear).set_value(W_MS - 0.01)], 6.0),
            ([FadeOut(follow), t1.animate(rate_func=linear).set_value(W_MS + 25)], 0.6),
            ([t1.animate(rate_func=linear).set_value(W_MS + 50)], 0.6))
        follow.clear_updaters()
        law = T("in flight = arrival rate × time inside", 30).move_to([0, -2.35, 0])
        law2 = T("L = λ × W = 400 / s × 0.25 s = 100", 30, GOLD_M).move_to([0, -2.95, 0])
        seq(self, "This is Little's law. In flight equals arrival rate times time inside. "
                  "400 times a quarter second is 100. One thread each: 100 threads.",
            ([FadeIn(law, shift=UP * 0.15), t1.animate(rate_func=linear).set_value(W_MS + 90)], 1.0),
            ([t1.animate(rate_func=linear).set_value(W_MS + 210)], 3.0),
            ([FadeIn(law2, shift=UP * 0.15), t1.animate(rate_func=linear).set_value(W_MS + 250)], 1.0),
            ([t1.animate(rate_func=linear).set_value(W_MS + 410)], 4.0))
        dots1.clear_updaters(); cnt1.clear_updaters()
        self.play(FadeOut(VGroup(dots1, cnt1, law, law2, door, door_lab, span, span_lab)), run_time=0.7)

        # ---- 50 threads: the pool finishes 200 a second, the queue grows ----
        LANE2 = [0.2, -0.2]
        sbox2 = RoundedRectangle(corner_radius=0.15, width=BR - BL + 0.3, height=1.0, stroke_color=BLUE_M, stroke_width=3)
        sbox2.set_fill(dark(BLUE_M, 0.08), 1).move_to([0, 0, 0])
        pool_lab = T("pool: 50 threads", 28, BLUE_M).move_to([0, 0.95, 0])
        rate_lab = T("200 a second", 26, GREY_A).next_to(out_arrow, UP, buff=0.15).align_to(out_arrow, LEFT).shift(RIGHT * 0.2)
        arr_lab = T("400 arrive each second", 26, YELLOW_M).move_to([-4.6, 1.95, 0])
        QL = [0.72 - 0.16 * r for r in range(10)]
        QX0, QDX = BL - 0.3, 0.13
        t2 = ValueTracker(0.0)
        N2 = 210                                   # arrivals in the first 500 ms ... enough for 1 s of queue
        ENTRY = 5.0                                # 50 threads / 250 ms: one seat frees every 5 ms
        pre = VGroup(*[Dot(radius=0.05, color=YELLOW_M) for _ in range(50)]).set_z_index(3)   # already inside at t=0
        new = VGroup(*[Dot(radius=0.05, color=YELLOW_M) for _ in range(410)]).set_z_index(3)

        def upd_pre(g):
            t = t2.get_value()
            for j, d in enumerate(g):
                e = -ENTRY * (50 - j)
                if t < e + W_MS:
                    d.set_opacity(1).move_to([BL + (t - e) / W_MS * (BR - BL), LANE2[j % 2], 0])
                else:
                    d.set_opacity(0)

        def upd_new(g):
            t = t2.get_value()
            for k, d in enumerate(g):
                a, e = k * GAP, k * ENTRY
                if t < a:
                    d.set_opacity(0)
                elif t < e:                        # queued: 10 lanes, moving up as seats free
                    p = (k - t / ENTRY) / 10
                    d.set_opacity(1).move_to([QX0 - p * QDX, QL[k % 10], 0])
                elif t < e + W_MS:
                    d.set_opacity(1).move_to([BL + (t - e) / W_MS * (BR - BL), LANE2[k % 2], 0])
                else:
                    d.set_opacity(0)
        pre.add_updater(upd_pre); new.add_updater(upd_new)
        upd_pre(pre); upd_new(new)

        def queued():
            t = t2.get_value()
            return sum(1 for k in range(len(new)) if k * GAP <= t < k * ENTRY)
        qcnt = counter("waiting: {}", queued, [-5.0, 1.35, 0], 28, YELLOW_M)
        self.play(Transform(sbox, sbox2), run_time=0.6)
        self.add(pre, new)
        seq(self, "Turn it around. With only 50 threads, each finishing four requests a second, "
                  "the pool finishes 200 a second.",
            ([FadeIn(pool_lab), FadeIn(pre)], 0.8), 2.4, ([Transform(out_lab, rate_lab)], 0.6))
        seq(self, "But 400 arrive. Each second, the other 200 wait in the queue, and the queue grows until memory or patience runs out.",
            ([FadeIn(arr_lab), FadeIn(qcnt)], 0.5),
            ([t2.animate(rate_func=linear).set_value(1000.0)], 7.8))
        pre.clear_updaters(); new.clear_updaters(); qcnt.clear_updaters()
        self.play(FadeOut(VGroup(sbox, pool_lab, arr_lab, pre, new, qcnt, out_arrow, out_lab)), run_time=0.8)

        # =============== code, rule, check ===============
        r1 = T("Threads that compute: one per core.", 34, TEAL_M)
        r2 = T("Threads that wait: arrival rate × time inside.", 34, YELLOW_M)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.35).move_to(UP * 1.6)
        self.beat("Threads that compute: one per core. Threads that wait: arrival rate times time inside.",
                  FadeIn(r1, shift=UP * 0.15), FadeIn(r2, shift=UP * 0.15), run_time=1.6)
        chk = T("20 threads. Each request takes 100 ms.", 30).move_to(DOWN * 0.6)
        chk2 = T("How many requests a second can the pool finish?", 30).move_to(DOWN * 1.2)
        self.beat("Check yourself. 20 threads, and each request takes 100 ms. How many requests a second?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("20 / 0.1 s = 200 a second", 30, GOLD_M).move_to(DOWN * 2.2)
        self.beat("200. Each thread finishes ten a second.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
