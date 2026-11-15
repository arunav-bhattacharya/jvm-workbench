from fg import *
import fg
import bisect

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\b1 MB\b", "one megabyte"), (r"\bMB\b", "megabytes"), (r"\bGB\b", "gigabytes"),
              (r"\b64-bit\b", "sixty-four bit"), (r"\b1\.28\b", "one point two eight")]


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


def stage_bar(issuer_ms, x0, x1, y, h, min_w=0.0):
    """One request as five blocks: parse, fraud, issuer, ledger, reply. Gold = CPU, grey = waiting."""
    parts = [(2, GOLD_M), (40, GREY_M), (issuer_ms, GREY_M), (35, GREY_M), (3, GOLD_M)]
    total = sum(p for p, _ in parts)
    widths = [max(min_w, (x1 - x0) * p / total) for p, _ in parts]
    k = (x1 - x0) / sum(widths)
    g, x = VGroup(), x0
    for (p, c), w in zip(parts, widths):
        w *= k
        r = Rectangle(width=w, height=h, stroke_color=BLACK, stroke_width=2)
        r.set_fill(c if c == GOLD_M else dark(GREY_M, 0.55), 1).move_to([x + w / 2, y, 0])
        g.add(r)
        x += w
    return g


# ---- the pool simulation: 200 threads, FIFO queue, each request holds its thread for W ms ----
N_THREADS = 200
T_UP = 600.0          # traffic rises from 800 to 1,500 a second here (sim ms)


def simulate(t_slow, t_end):
    arr, t = [], -700.0
    while t < t_end:
        arr.append(t)
        t += 1000.0 / (800.0 if t < T_UP else 1500.0)
    free_at = [-1e9] * N_THREADS
    starts, ends, tid, prev = [], [], [], -1e9
    for a in arr:
        t0 = max(a, prev)
        i = next((j for j in range(N_THREADS) if free_at[j] <= t0), None)
        if i is None:
            t0 = min(free_at)
            i = next(j for j in range(N_THREADS) if free_at[j] <= t0)
        e = t0 + (200.0 if t0 < t_slow else 1280.0)
        free_at[i] = e
        starts.append(t0); ends.append(e); tid.append(i); prev = t0
    cs = [[] for _ in range(N_THREADS)]
    ce = [[] for _ in range(N_THREADS)]
    for s, e, i in zip(starts, ends, tid):
        cs[i].append(s); ce[i].append(e)
    return arr, starts, sorted(ends), cs, ce


class Vt01Wall(VoiceScene):
    """vt-01, section 0: a 200 ms request that waits 195 ms holds one platform thread the whole time;
    a 200-thread pool tops out at 1,000 a second and the queue grows while the threads mostly wait;
    a slow issuer cuts it to 156 a second; why more platform threads is no way out (stack, system call, scheduling)."""

    def construct(self):
        self.title_card("The thread-per-request wall", "why a blocking service stops at a fixed rate")

        # =============== part 1: one request, one thread ===============
        X0, X1, BY = -6.0, 6.0, 0.9
        PX = (X1 - X0) / 200
        big = stage_bar(120, X0, X1, BY, 0.8)
        names = [None, ("fraud", "40 ms"), ("card issuer", "120 ms"), ("ledger", "35 ms"), None]
        labs = VGroup()
        for r, nm in zip(big, names):
            if nm:
                labs.add(VGroup(T(nm[0], 26), T(nm[1], 22, GREY_A)).arrange(DOWN, buff=0.06).move_to(r))
        parse_l = T("parse 2 ms", 24, GOLD_M).move_to([X0, BY + 0.7, 0], aligned_edge=LEFT)
        reply_l = T("reply 3 ms", 24, GOLD_M).move_to([X1, BY + 0.7, 0], aligned_edge=RIGHT)
        axis = Line([X0, 0.2, 0], [X1, 0.2, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([X0 + m * PX, 0.27, 0], [X0 + m * PX, 0.13, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([X0 + m * PX, -0.12, 0])) for m in (0, 100, 200)])
        cursor = Line([X0, BY + 0.55, 0], [X0, BY - 0.55, 0], stroke_width=3, color=YELLOW_M)
        cur_t = ValueTracker(0.0)
        cursor.add_updater(lambda m: m.set_x(X0 + cur_t.get_value() * PX))

        def grow(i, a, b):
            return GrowFromEdge(big[i], LEFT, run_time=max(0.15, (b - a) / 200 * 4.0), rate_func=linear)
        self.add(cursor)
        seq(self, "A payment authorization takes 200 ms. It parses the request, calls the fraud service, "
                  "the card issuer and the ledger, then replies.",
            ([FadeIn(axis), FadeIn(ticks)], 0.6),
            ([cur_t.animate(rate_func=linear).set_value(200), Succession(grow(0, 0, 2), grow(1, 2, 42), grow(2, 42, 162),
                                                                       grow(3, 162, 197), grow(4, 197, 200))], 4.0),
            ([FadeIn(labs), FadeIn(parse_l), FadeIn(reply_l), FadeOut(cursor)], 0.7))
        cursor.clear_updaters()

        leg = VGroup(
            VGroup(Square(0.3, stroke_width=0).set_fill(GOLD_M, 1), T("running on a CPU: 5 ms", 26)).arrange(RIGHT, buff=0.2),
            VGroup(Square(0.3, stroke_width=0).set_fill(dark(GREY_M, 0.55), 1), T("waiting on the network: 195 ms", 26)).arrange(RIGHT, buff=0.2),
        ).arrange(RIGHT, buff=1.0).move_to([0, -2.4, 0])
        self.beat("Only 5 ms of that runs on a CPU. For the other 195, it waits on the network.",
                  FadeIn(leg[0]), Indicate(VGroup(parse_l, reply_l), color=GOLD_M), run_time=1.4)
        self.play(FadeIn(leg[1]), run_time=0.6)

        thr = Rectangle(width=X1 - X0, height=0.55, stroke_color=BLUE_M, stroke_width=3).set_fill(dark(BLUE_M, 0.3), 1)
        thr.move_to([0, -1.1, 0])
        thr_l = T("one thread, held for all 200 ms", 26, BLUE_M).move_to(thr)
        self.beat("The server gives this request one thread, and the request keeps that thread for all 200 ms.",
                  GrowFromEdge(thr, LEFT), FadeIn(thr_l), run_time=2.2)
        self.beat("While the request waits, its thread waits with it. A blocked thread does no work, "
                  "but no other request can use it.",
                  Indicate(thr_l, color=WHITE, scale_factor=1.04), run_time=1.2)

        # =============== part 2: a pool of 200 threads hits the wall ===============
        SX0, SX1, SY = -4.2, -0.2, 3.15
        strip = stage_bar(120, SX0, SX1, SY, 0.32, min_w=0.05)
        strip_l = T("one request", 24, GREY_B).move_to([-6.3, SY, 0], aligned_edge=LEFT)
        strip_ms = T("200 ms", 24, GREY_A).next_to(strip, RIGHT, buff=0.2)
        self.play(FadeOut(VGroup(labs, parse_l, reply_l, axis, ticks, leg, thr, thr_l)),
                  Transform(big, strip), run_time=0.9)
        self.play(FadeIn(strip_l), FadeIn(strip_ms), run_time=0.4)

        CELL, GAP, GX, GY = 0.26, 0.07, 0.6, -0.2
        pos = []
        for i in range(N_THREADS):
            r, c = divmod(i, 20)
            pos.append(np.array([GX + (c - 9.5) * (CELL + GAP), GY + (4.5 - r) * (CELL + GAP), 0]))
        grid = VGroup()
        for p in pos:
            f = Rectangle(width=CELL, height=CELL, stroke_width=0).set_fill(BLUE_M, 0).move_to(p)
            o = Square(CELL, stroke_color=GREY_D, stroke_width=1.5).move_to(p)
            grid.add(VGroup(f, o))
        pool_l = T("pool: 200 platform threads", 28, BLUE_M).move_to([GX, 2.05, 0])

        # the clock in sim ms; the run is computed up front
        T_FF = T_UP + 9999.5
        arr, starts, ends_sorted, cs, ce = simulate(T_FF, T_FF + 2500.0)
        clk = ValueTracker(0.0)

        def progress(i, t):
            j = bisect.bisect_right(cs[i], t) - 1
            if j >= 0 and t < ce[i][j]:
                return (t - cs[i][j]) / (ce[i][j] - cs[i][j]), ce[i][j] - cs[i][j]
            return None, None

        def queued(t):
            return bisect.bisect_right(arr, t) - bisect.bisect_right(starts, t)

        def busy(t):
            return bisect.bisect_right(starts, t) - bisect.bisect_right(ends_sorted, t)

        def paint(g, t):
            for i, cell in enumerate(g):
                f, o = cell
                p, _ = progress(i, t)
                if p is None:
                    f.set_fill(BLUE_M, 0)
                    o.set_stroke(GREY_D)
                else:
                    h = max(0.004, CELL * p)
                    f.stretch_to_fit_height(h)
                    f.move_to(pos[i] + np.array([0, (h - CELL) / 2, 0]))
                    f.set_fill(BLUE_M, 0.8)
                    o.set_stroke(BLUE_M)

        def grid_upd(g):
            paint(g, clk.get_value())
        paint(grid, 0.0)

        # queue pile: one dot per waiting request, front next to the pool
        QX0, QY0, QD, ROWS, COLS = -3.0, 1.3, 0.13, 24, 26
        pile = VGroup(*[Dot(radius=0.045, color=YELLOW_M).move_to([QX0 - (k // ROWS) * QD, QY0 - (k % ROWS) * QD, 0])
                        for k in range(ROWS * COLS)])

        def pile_upd(g):
            q = queued(clk.get_value())
            for k, d in enumerate(g):
                d.set_opacity(1 if k < q else 0)
        pile_upd(pile)

        arr_l = T("arriving: 800 a second", 26, YELLOW_M).move_to([-6.3, 2.05, 0], aligned_edge=LEFT)
        arr_l2 = T("arriving: 1,500 a second", 26, YELLOW_M).move_to([-6.3, 2.05, 0], aligned_edge=LEFT)
        out_a = arrow(np.array([GX + 3.5, GY, 0]), np.array([5.9, GY, 0]), color=GREY_B)
        out_t = T("finished", 26, GREY_B).move_to([5.0, GY + 0.45, 0])
        out_r = T("800 a second", 26).move_to([5.0, GY - 0.45, 0])
        busy_c = counter("busy threads: {} of 200", lambda: busy(clk.get_value()), [GX, -2.35, 0], 26, BLUE_M)
        q_c = counter("waiting for a thread: {:,}", lambda: queued(clk.get_value()), [-6.3, -2.35, 0], 26, YELLOW_M, edge=LEFT)

        grid.add_updater(grid_upd)
        pile.add_updater(pile_upd)
        self.add(grid)
        seq(self, "A server keeps a pool of 200 such threads. Each square is one thread. It fills up as its request runs. "
                  "When it is full, the request is done, and the thread takes the next one.",
            ([FadeIn(grid), FadeIn(pool_l), clk.animate(rate_func=linear).set_value(60)], 1.0),
            ([clk.animate(rate_func=linear).set_value(400)], 7.0))
        seq(self, "At 800 requests a second, about 160 threads are busy at any moment, and 40 sit idle.",
            ([FadeIn(arr_l), FadeIn(busy_c), GrowArrow(out_a), FadeIn(out_t), FadeIn(out_r),
              clk.animate(rate_func=linear).set_value(470)], 1.2),
            ([clk.animate(rate_func=linear).set_value(T_UP)], 3.0))

        def clock_fn():
            return round((clk.get_value() - T_UP) / 1000.0, 1)
        clock = counter("after {:.1f} s", clock_fn, [6.3, SY, 0], 26, GREY_A, edge=RIGHT)
        self.beat("Now traffic rises to 1,500 a second. What happens?",
                  Transform(arr_l, arr_l2), FadeIn(clock), FadeIn(q_c), run_time=1.0)
        self.wait(2.0)
        seq(self, "The idle threads fill up at once. Then new requests have nowhere to go. They wait in the pool's queue.",
            ([clk.animate(rate_func=linear).set_value(T_UP + 120)], 2.4),
            ([clk.animate(rate_func=linear).set_value(T_UP + 520)], 4.6))
        out_r2 = T("1,000 a second", 26).move_to(out_r)
        seq(self, "Each thread finishes one request every 200 ms, so five a second. "
                  "200 threads finish 1,000 a second, and not one more.",
            ([clk.animate(rate_func=linear).set_value(T_UP + 700)], 3.0),
            ([Transform(out_r, out_r2), clk.animate(rate_func=linear).set_value(T_UP + 820)], 1.0),
            ([clk.animate(rate_func=linear).set_value(T_UP + 1000)], 2.0))
        seq(self, "The other 500 a second pile up. After ten seconds, about 5,000 are waiting, "
                  "and a new request waits five seconds before a thread even picks it up.",
            ([clk.animate(rate_func=smooth).set_value(T_FF)], 6.0))

        # ---- freeze: who is computing right now? ----
        grid.clear_updaters(); pile.clear_updaters()
        t_f = T_FF
        frozen = grid.copy()
        n_cpu = 0
        for i, cell in enumerate(frozen):
            f, o = cell
            p, w = progress(i, t_f)
            el = p * w
            f.stretch_to_fit_height(CELL).move_to(pos[i])
            if el < 2 or el > w - 3:
                f.set_fill(GOLD_M, 1); o.set_stroke(GOLD_M); n_cpu += 1
            else:
                f.set_fill(BLUE_M, 0.28); o.set_stroke(BLUE_M)
        busy_c.clear_updaters()
        leg2 = VGroup(
            VGroup(Square(0.28, stroke_width=0).set_fill(GOLD_M, 1), T(f"running code: {n_cpu}", 26, GOLD_M)).arrange(RIGHT, buff=0.18),
            VGroup(Square(0.28, stroke_width=0).set_fill(BLUE_M, 0.28), T(f"blocked, waiting: {200 - n_cpu}", 26, BLUE_M)).arrange(RIGHT, buff=0.18),
        ).arrange(RIGHT, buff=0.6).move_to([GX, -2.35, 0])
        seq(self, f"Freeze the picture. Of the 200 threads, about {n_cpu} are running code. "
                  f"The other {200 - n_cpu} are blocked, waiting on the network.",
            1.2, ([Transform(grid, frozen), FadeOut(busy_c), FadeIn(leg2)], 1.2))
        rule0 = T("You run out of threads long before you run out of CPU.", 28).move_to([0, -3.15, 0])
        self.beat("You run out of threads long before you run out of CPU.", FadeIn(rule0, shift=UP * 0.15), run_time=1.0)

        # ---- the issuer slows down ----
        strip2 = stage_bar(1200, SX0, SX1, SY, 0.32, min_w=0.05)
        strip2[2].set_fill(dark(RED_M, 0.6), 1)
        strip_ms2 = T("1,280 ms", 24, RED_M).next_to(strip2, RIGHT, buff=0.2)
        live = grid.copy()
        paint(live, t_f)
        self.play(FadeOut(rule0), FadeOut(leg2), Transform(grid, live), run_time=0.7)
        busy_c = counter("busy threads: {} of 200", lambda: busy(clk.get_value()), [GX, -2.35, 0], 26, BLUE_M)
        grid.add_updater(grid_upd); pile.add_updater(pile_upd)
        seq(self, "Now the card issuer has a bad day, and its calls take 1.2 seconds. "
                  "Each request holds its thread for 1.28 seconds.",
            ([Transform(big, strip2), Transform(strip_ms, strip_ms2), FadeIn(busy_c)], 1.0),
            ([clk.animate(rate_func=linear).set_value(T_FF + 900)], 5.5))
        out_r3 = T("156 a second", 26, RED_M).move_to(out_r)
        seq(self, "The same 200 threads now finish only 156 a second. Your code did not change. "
                  "A slow service downstream took your throughput with it.",
            ([Transform(out_r, out_r3), clk.animate(rate_func=linear).set_value(T_FF + 1100)], 1.0),
            ([clk.animate(rate_func=linear).set_value(T_FF + 2300)], 6.5))
        grid.clear_updaters(); pile.clear_updaters(); busy_c.clear_updaters(); q_c.clear_updaters(); clock.clear_updaters()
        self.play(FadeOut(VGroup(grid, pile, pool_l, arr_l, out_a, out_t, out_r, busy_c, q_c, clock, big, strip_l, strip_ms)),
                  run_time=0.8)

        # =============== part 3: why not more threads? ===============
        jt = mbox("java.lang.Thread", BLUE_M, h=0.9, size=26).move_to([-4.0, 2.2, 0])
        ot = box("OS thread", TEAL_M, w=3.0, h=0.9, size=28).move_to([1.6, 2.2, 0])
        a1 = edge_arrow(jt, ot, GREY_B)
        a1_l = T("one to one", 24, GREY_B).next_to(a1, UP, buff=0.12)
        kern = T("the kernel schedules it", 24, TEAL_M).next_to(ot, DOWN, buff=0.18)
        self.beat("Why not raise the pool to 2,000 threads? It does lift the cap, for a while. "
                  "But each of these is a platform thread: one Java thread is one OS thread.",
                  FadeIn(jt), GrowArrow(a1), FadeIn(a1_l), FadeIn(ot), FadeIn(kern), run_time=2.0)

        STX, STY0, STH = 5.0, -1.3, 3.4
        stack = Rectangle(width=1.3, height=STH, stroke_color=TEAL_M, stroke_width=3).set_fill(dark(TEAL_M, 0.1), 1)
        stack.move_to([STX, STY0 + STH / 2, 0])
        used = Rectangle(width=1.3, height=0.45, stroke_width=0).set_fill(TEAL_M, 0.55).move_to([STX, STY0 + 0.225, 0])
        guard = Rectangle(width=1.3, height=0.22, stroke_width=0).set_fill(RED_M, 0.5).move_to([STX, STY0 + STH - 0.11, 0])
        st_l = T("stack: 1 MB", 26, TEAL_M).next_to(stack, LEFT, buff=0.3).shift(UP * 0.9)
        st_l2 = T("reserved up front", 24, GREY_A).next_to(st_l, DOWN, buff=0.12, aligned_edge=RIGHT)
        g_l = T("guard page", 22, RED_M).next_to(guard, LEFT, buff=0.3)
        u_l = T("pages in use", 22, GREY_A).next_to(used, LEFT, buff=0.3)
        lk = link(ot, stack, TEAL_M)
        self.beat("Each one reserves a stack up front: 1 MB by default on 64-bit Linux. "
                  "The kernel adds guard pages and its own bookkeeping for every thread.",
                  Create(lk), FadeIn(stack), FadeIn(used), FadeIn(guard), FadeIn(st_l), FadeIn(st_l2),
                  FadeIn(g_l), FadeIn(u_l), run_time=2.2)
        c1 = T("start: a system call", 28).move_to([-6.2, 0.5, 0], aligned_edge=LEFT)
        c2 = T("switch: kernel time, and cold CPU caches", 28).move_to([-6.2, -0.3, 0], aligned_edge=LEFT)
        seq(self, "Starting one is a system call. And when thousands are runnable, "
                  "switching between them costs the kernel time, and costs you your CPU caches.",
            ([FadeIn(c1, shift=UP * 0.15)], 0.7), 1.2, ([FadeIn(c2, shift=UP * 0.15)], 0.7))
        self.play(FadeOut(VGroup(jt, ot, a1, a1_l, kern, stack, used, guard, st_l, st_l2, g_l, u_l, lk, c1, c2)), run_time=0.7)

        # ---- how many fit in one JVM ----
        def lx(n):
            return -5.4 + (np.log10(n) - 2) * 2.7
        ax = Line([lx(100), -0.6, 0], [lx(1e6), -0.6, 0], stroke_width=2, color=GREY_B)
        tk = VGroup(*[VGroup(Line([lx(n), -0.52, 0], [lx(n), -0.68, 0], stroke_width=2, color=GREY_B),
                             T(s, 22, GREY_B).move_to([lx(n), -0.95, 0]))
                      for n, s in ((100, "100"), (1000, "1,000"), (1e4, "10,000"), (1e5, "100,000"), (1e6, "1,000,000"))])
        head = T("platform threads in one JVM", 28, GREY_A).move_to([0, 2.7, 0])

        def zone(a, b, color):
            return Rectangle(width=lx(b) - lx(a) - 0.06, height=0.32, stroke_width=0).set_fill(color, 0.75).move_to(
                [(lx(a) + lx(b)) / 2, -0.3, 0])
        z1, z2, z3 = zone(100, 1000, GREEN_M), zone(1000, 1e4, GOLD_M), zone(1e4, 1e6 / 1.6, RED_M)
        zl1 = VGroup(T("hundreds", 26, GREEN_M), T("comfortable", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(z1, UP, buff=0.25)
        zl2 = VGroup(T("a few thousand", 26, GOLD_M), T("survives", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(z2, UP, buff=0.25)
        zl3 = VGroup(T("tens of thousands", 26, RED_M), T("fights OS limits, memory,", 24, GREY_A),
                     T("and the scheduler", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(z3, UP, buff=0.25).shift(LEFT * 0.4)
        xm = tick(False, 0.28).move_to([lx(1e6), -0.3, 0])
        zl4 = VGroup(T("a million", 26, RED_M), T("out of reach", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(xm, UP, buff=0.3)
        zl4.shift(LEFT * max(0, zl4.get_right()[0] - 6.4))
        m200 = Triangle(color=BLUE_M, fill_opacity=1, stroke_width=0).scale(0.14).move_to([lx(200), -1.45, 0])
        m200_l = T("our pool: 200", 24, BLUE_M).next_to(m200, DOWN, buff=0.15)
        m2k = Triangle(color=YELLOW_M, fill_opacity=1, stroke_width=0).scale(0.14).move_to([lx(2000), -1.45, 0])
        m2k_l = VGroup(T("2,000 threads", 24, YELLOW_M), T("2 GB of stack reserved", 22, GREY_A)).arrange(DOWN, buff=0.08)
        m2k_l.next_to(m2k, DOWN, buff=0.15)
        self.beat("So a JVM is comfortable with hundreds of platform threads, and survives a few thousand.",
                  FadeIn(head), Create(ax), FadeIn(tk), FadeIn(z1), FadeIn(zl1), FadeIn(z2), FadeIn(zl2),
                  FadeIn(m200), FadeIn(m200_l), FadeIn(m2k), FadeIn(m2k_l), run_time=2.4)
        self.beat("At tens of thousands it fights OS limits, memory and the scheduler. A million is out of reach.",
                  FadeIn(z3), FadeIn(zl3), FadeIn(xm, scale=0.5), FadeIn(zl4), run_time=2.0)
        self.play(FadeOut(VGroup(head, ax, tk, z1, z2, z3, zl1, zl2, zl3, xm, zl4, m200, m200_l, m2k, m2k_l)), run_time=0.7)

        # =============== part 4: name it, the numbers, the code ===============
        name = T("the thread-per-request wall", 40).move_to([0, 2.6, 0])
        f1 = T("requests in flight = arrival rate × time inside", 30).move_to([0, 1.3, 0])
        f2 = T("1,500 / s × 0.2 s = 300 threads needed", 30, YELLOW_M).move_to([0, 0.5, 0])
        f3 = T("200 threads / 0.2 s = at most 1,000 a second", 30, BLUE_M).move_to([0, -0.3, 0])
        f4 = T("Little's law: L = λ × W", 26, GREY_B).move_to([0, -1.3, 0])
        self.beat("This is the thread-per-request wall. Each request holds a thread while it waits, "
                  "and platform threads are too costly to have many.", Write(name), run_time=1.4)
        seq(self, "Little's law puts a number on it. Requests in flight equal arrival rate times time inside. "
                  "1,500 a second for 0.2 seconds is 300 threads. With 200, the most you can serve is 1,000 a second.",
            ([FadeIn(f1, shift=UP * 0.15), FadeIn(f4)], 0.8), 4.4, ([FadeIn(f2, shift=UP * 0.15)], 0.8), 2.6,
            ([FadeIn(f3, shift=UP * 0.15)], 0.8))
        self.play(FadeOut(VGroup(f1, f2, f3, f4)), run_time=0.6)

        jc = code(["var pool = Executors.newFixedThreadPool(200);",
                   "// each task holds one OS thread for 200 ms",
                   "pool.execute(() -> authorize(payment));"], 24)
        kc = code(["val pool = Executors.newFixedThreadPool(200)",
                   "// each task holds one OS thread for 200 ms",
                   "pool.execute { authorize(payment) }"], 24)
        for b in (jc, kc):
            b[1].set_color(GREY_B)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.0, 0])
        self.beat("In code, it is the plain blocking style: a fixed pool, and each task keeps its thread from start to end. "
                  "Kotlin uses the same pool.", FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(VGroup(cg, name)), run_time=0.6)

        w1 = T("Two ways out:", 30, GREY_A).move_to([0, 2.2, 0])
        w2 = T("make each request wait less (often not yours to change)", 28).move_to([0, 1.4, 0])
        w3 = T("hold a waiting request in something cheaper than an OS thread", 28, GREEN_M).move_to([0, 0.7, 0])
        VGroup(w2, w3).scale(min(1, 12 / max(w2.width, w3.width)))
        seq(self, "There are two ways out. Make each request wait less, which you often can't, because the issuer is not yours. "
                  "Or hold a waiting request in something cheaper than an OS thread. Virtual threads take that second way.",
            ([FadeIn(w1)], 0.5), 1.0, ([FadeIn(w2, shift=UP * 0.15)], 0.7), 3.2, ([FadeIn(w3, shift=UP * 0.15)], 0.7))
        self.play(FadeOut(VGroup(w1, w2, w3)), run_time=0.6)

        rule = T("A blocked request still holds its thread.", 34).move_to([0, 2.0, 0])
        rule2 = T("Most you can serve = threads ÷ time per request.", 34, BLUE_M).move_to([0, 1.3, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule2.width))
        self.beat("The rule. A blocked request still holds its thread, so threads divided by time per request is your ceiling.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("200 threads. The issuer slows, and each request takes 2 s.", 30).move_to([0, -0.2, 0])
        chk2 = T("How many requests a second can the service finish?", 30).move_to([0, -0.8, 0])
        self.beat("Check yourself. 200 threads, and each request now takes 2 seconds. How many can the service finish a second?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("200 / 2 s = 100 a second, with the CPU almost idle", 30, GOLD_M).move_to([0, -1.9, 0])
        ans.scale(min(1, 12 / ans.width))
        self.beat("100. 200 threads divided by 2 seconds. The idle CPU does not help.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
