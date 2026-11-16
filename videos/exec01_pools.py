from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bshutdownNow\b", "shutdown now"),
              (r"\bawaitTermination\b", "await termination"), (r"\bRejectedExecutionException\b", "Rejected Execution Exception"),
              (r"\b1 MB\b", "one megabyte")]


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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# Animations that read the mobject's state when they start, so they can sit late in a Succession.
def lazy(m, rt, fn, rate=smooth):
    st = {}

    def f(mob, a):
        if "s" not in st:
            st["s"] = mob.copy()
        fn(mob, st["s"], a)
    return UpdateFromAlphaFunc(m, f, run_time=rt, rate_func=rate)


def mv(m, p, rt):
    p = np.array(p, dtype=float)
    return lazy(m, rt, lambda mob, s, a: mob.move_to(interpolate(s.get_center(), p, a)))


def done(m, rt):
    def fn(mob, s, a):
        mob.become(s.copy().set_color(GREEN_M).set_fill(GREEN_M, 0.5 * (1 - a)).set_stroke(opacity=1 - a)
                   .scale(1 + 0.4 * a).set_opacity(1 - a))
    return lazy(m, rt, fn, rate=linear)


def stopped(m, rt):
    def fn(mob, s, a):
        mob.become(s.copy().set_stroke(RED_M).scale(1 + 0.3 * a).set_opacity(1 - a))
    return lazy(m, rt, fn, rate=linear)


def restyle(m, rt, color, opacity=1.0):
    def fn(mob, s, a):
        c = s.copy()
        if isinstance(s, Text):
            c.set_color(interpolate_color(s.get_color(), ManimColor(color), a))
        else:
            c.set_stroke(interpolate_color(s.get_stroke_color(), ManimColor(color), a))
        mob.become(c.set_opacity(interpolate(1.0, opacity, a)))
    return lazy(m, rt, fn)


def timeline(events):
    """events: (mobject, start, run_time, factory(rt)). One Succession per mobject, gaps filled with Wait."""
    by = {}
    for mob, t0, rt, fac in events:
        by.setdefault(id(mob), (mob, []))[1].append((t0, rt, fac))
    out = []
    for mob, evs in by.values():
        evs.sort(key=lambda e: e[0])
        parts, t = [], 0.0
        for t0, rt, fac in evs:
            if t0 > t + 1e-6:
                parts.append(Wait(t0 - t))
            parts.append(fac(rt))
            t = max(t, t0) + rt
        out.append(Succession(*parts))
    return AnimationGroup(*out)


def chip_task(color=GOLD_M):
    return RoundedRectangle(corner_radius=0.08, width=0.5, height=0.5, stroke_color=color, stroke_width=2.5) \
        .set_fill(dark(color, 0.45), 1).set_z_index(5)


class Exec01Pools(VoiceScene):
    """exec-01: a new platform thread per task costs a system call, a stack and a scheduler entry, and has no ceiling;
    a pool is a queue plus a few workers that loop take, run; shutdown closes the door and lets the queue drain,
    shutdownNow hands the queue back and interrupts, and only awaitTermination waits."""

    def construct(self):
        self.title_card("Why pools, and how they stop", "a few threads, kept and reused, then shut down on purpose")

        # =============== part 1: what a new thread costs ===============
        top = T("one tiny task on a brand-new thread", 28, GREY_B).move_to([0, 3.0, 0])
        X0, Y = -6.0, 2.0
        seg_setup = Rectangle(width=6.2, height=0.6, stroke_color=GREY_B, stroke_width=2).set_fill(GREY_D, 0.6)
        seg_setup.move_to([X0 + 3.1, Y, 0])
        seg_task = Rectangle(width=0.12, height=0.6, stroke_width=0).set_fill(GOLD_M, 1).next_to(seg_setup, RIGHT, buff=0)
        seg_down = Rectangle(width=4.2, height=0.6, stroke_color=GREY_B, stroke_width=2).set_fill(GREY_D, 0.3)
        seg_down.next_to(seg_task, RIGHT, buff=0)
        s_lbl = VGroup(T("a system call to the OS", 24, GREY_A), T("a new stack: 1 MB reserved (64-bit Linux)", 24, GREY_A),
                       T("an entry in the OS scheduler", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        s_lbl.next_to(seg_setup, DOWN, buff=0.3).align_to(seg_setup, LEFT)
        t_lbl = T("the task", 24, GOLD_M).next_to(seg_task, DOWN, buff=0.3)
        t_arr = Arrow(t_lbl.get_top(), seg_task.get_bottom(), buff=0.06, stroke_width=3, color=GOLD_M,
                      max_tip_length_to_length_ratio=0.3)
        d_lbl = T("all torn down again", 24, GREY_A).next_to(seg_down, DOWN, buff=0.3).align_to(seg_down, RIGHT)
        self.beat("Your service has 5,000 tiny tasks. Run each one on a brand-new thread, and look at what one costs.",
                  FadeIn(top), run_time=1.0)
        seq(self, "Starting a platform thread means a system call to the OS, a new stack, and an entry in the OS scheduler.",
            ([GrowFromEdge(seg_setup, LEFT)], 1.6), ([LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in s_lbl], lag_ratio=0.5)], 2.4))
        seq(self, "Then the task runs, for a few microseconds. Then all of it is torn down again.",
            ([FadeIn(seg_task), FadeIn(t_lbl), GrowArrow(t_arr)], 0.6), 1.4,
            ([GrowFromEdge(seg_down, LEFT), FadeIn(d_lbl)], 1.4))

        # bars: the lesson's measurement
        BX = -2.6
        PX = 5.6 / 1.5         # units per second
        b1_l = T("new thread each", 26, GREY_A).move_to([BX - 0.3, -1.5, 0], aligned_edge=RIGHT)
        b2_l = T("4 reused threads", 26, TEAL_M).move_to([BX - 0.3, -2.5, 0], aligned_edge=RIGHT)
        b1 = Rectangle(width=0.5 * PX, height=0.5, stroke_width=0).set_fill(GREY_B, 0.9).move_to([BX, -1.5, 0], aligned_edge=LEFT)
        b1x = Rectangle(width=1.0 * PX, height=0.5, stroke_color=GREY_B, stroke_width=2).set_fill(GREY_B, 0.25)
        b1x.next_to(b1, RIGHT, buff=0)
        b1_v = T("0.5 to 1.5 s", 26, GREY_A).next_to(b1x, RIGHT, buff=0.2)
        b2 = Rectangle(width=0.025 * PX, height=0.5, stroke_width=0).set_fill(TEAL_M, 1).move_to([BX, -2.5, 0], aligned_edge=LEFT)
        b2_v = T("6 to 25 ms", 26, TEAL_M).next_to(b2, RIGHT, buff=0.2)
        b_t = T("5,000 tasks, 4-core machine", 24, GREY_B).move_to([0.2, -0.8, 0])
        self.beat("Most of that time goes to the thread, not the work. Now do it 5,000 times, and compare four threads "
                  "that are kept and reused. How big is the gap?", FadeIn(b_t), FadeIn(b1_l), FadeIn(b2_l), run_time=1.2)
        self.wait(1.4)
        seq(self, "On a 4-core machine: half a second to a second and a half with a new thread each time. "
                  "6 to 25 ms on four reused threads.",
            ([GrowFromEdge(b1, LEFT), GrowFromEdge(b1x, LEFT), FadeIn(b1_v)], 1.6), 2.2,
            ([GrowFromEdge(b2, LEFT), FadeIn(b2_v)], 0.6))
        self.play(FadeOut(VGroup(top, seg_setup, seg_task, seg_down, s_lbl, t_lbl, t_arr, d_lbl, b1_l, b2_l, b1, b1x,
                                 b1_v, b2, b2_v, b_t)), run_time=0.7)

        # =============== part 2: a pool is a queue and a few workers ===============
        QY = 0.3
        tray = RoundedRectangle(corner_radius=0.12, width=5.3, height=0.85, stroke_color=GOLD_M, stroke_width=2.5)
        tray.move_to([-3.0, QY, 0])
        q_l = T("queue", 28, GOLD_M).next_to(tray, UP, buff=0.25)

        def slot(i):
            return np.array([-0.75 - 0.72 * i, QY, 0])
        WY = [1.95, 0.85, -0.25, -1.35]
        wbox = [RoundedRectangle(corner_radius=0.12, width=3.0, height=0.8, stroke_color=TEAL_M, stroke_width=3)
                .set_fill(dark(TEAL_M), 1).move_to([3.4, y, 0]) for y in WY]
        wlab = [T(f"worker {k + 1}", 26, TEAL_M).move_to([4.1, y, 0]) for k, y in enumerate(WY)]
        seat = [np.array([2.45, y, 0]) for y in WY]
        workers = VGroup(*wbox, *wlab)
        state = T("pool: running", 28, GREY_A).move_to([3.4, 3.0, 0])
        self.beat("A thread pool fixes this. It starts a few threads once, and keeps them.",
                  LaggedStart(*[FadeIn(VGroup(b, l)) for b, l in zip(wbox, wlab)], lag_ratio=0.25), run_time=1.6)

        def fill_queue(n):
            cs = [chip_task().move_to(slot(i)) for i in range(n)]
            return cs, LaggedStart(*[FadeIn(c, shift=RIGHT * 0.4) for c in reversed(cs)], lag_ratio=0.15)

        def drain(chips, free, runs, t_gap=0.35, after_empty=None):
            """Workers take chips from the head in order; the rest shift forward. Returns (events, free times)."""
            ev, q, last = [], list(chips), -1.0
            free = list(free)
            while q:
                w = min(range(4), key=lambda k: free[k])
                t = max(free[w], last + t_gap)
                last = t
                c = q.pop(0)
                ev.append((c, t, 0.45, lambda rt, c=c, w=w: mv(c, seat[w], rt)))
                for i, c2 in enumerate(q):
                    ev.append((c2, t, 0.3, lambda rt, c2=c2, i=i: mv(c2, slot(i), rt)))
                r = runs.pop(0)
                ev.append((c, t + 0.45 + r, 0.35, lambda rt, c=c: done(c, rt)))
                free[w] = t + 0.45 + r + 0.35
            return ev, free

        cs, fin = fill_queue(7)
        ex_l = M("execute(task)", 24, GOLD_M).move_to([-4.9, 1.05, 0])
        q_l.move_to([-2.0, 1.05, 0])
        tl0 = timeline(drain(cs, [0, 0, 0, 0], [1.0, 1.25, 0.9, 1.15, 0.95, 1.05, 0.8])[0])
        seq(self, "Tasks go into a queue. Each worker runs one loop: take a task, run it, take the next.",
            ([FadeIn(tray), FadeIn(q_l), FadeIn(ex_l), fin], 1.6), 0.4, ([tl0], tl0.run_time))
        blocked = [M("take()", 22, GREY_B).move_to([2.45, y, 0]) for y in WY]
        self.beat("Four workers, so at most four tasks run at once. When the queue is empty, take blocks, and they wait.",
                  *[FadeIn(b) for b in blocked], *[w.animate.set_stroke(GREY_B) for w in wbox], run_time=1.2)

        # =============== part 3: shutdown, awaitTermination ===============
        self.remove(*cs)

        def start_state():
            cs = [chip_task().move_to(slot(i)) for i in range(5)]
            rs = [chip_task().move_to(seat[k]) for k in range(4)]
            return cs, rs
        cs, rs = start_state()
        self.beat("Now the service is stopping. Five tasks are queued, and four are running.",
                  *[FadeOut(b) for b in blocked], *[w.animate.set_stroke(TEAL_M) for w in wbox],
                  *[FadeIn(c) for c in cs + rs], FadeIn(state), run_time=1.2)
        main = box("main", BLUE_M, w=1.6, h=0.7, size=28).move_to([-5.4, -2.6, 0])
        mcall = M("pool.shutdown()", 26, BLUE_M).next_to(main, RIGHT, buff=0.35)
        self.beat("main calls shutdown. Does it wait for those tasks?", FadeIn(main), FadeIn(mcall), run_time=1.0)
        self.wait(1.6)

        door = Line([-5.8, QY - 0.55, 0], [-5.8, QY + 0.55, 0], stroke_width=8, color=RED_M)
        ret = T("returns at once", 24, GREY_A).next_to(mcall, RIGHT, buff=0.3)
        late = chip_task().move_to([-6.3, QY, 0])
        rej = M("RejectedExecutionException", 22, RED_M).move_to([-3.6, -0.6, 0])
        st2 = T("pool: shutting down", 28, GREY_A).move_to(state)
        seq(self, "No. shutdown closes the door and returns at once. A new task is rejected.",
            ([Create(door), FadeIn(ret), Transform(state, st2)], 0.9), 0.6,
            ([FadeIn(late)], 0.2), ([late.animate.move_to([-6.05, QY, 0]).set_stroke(RED_M)], 0.4),
            ([FadeOut(late, shift=LEFT * 0.3), FadeIn(rej)], 0.6))

        ev, free = drain(cs, [0.5, 1.0, 0.3, 0.8], [1.2, 1.0, 1.3, 1.1, 0.9])
        for k, c in enumerate(rs):
            ev.append((c, [0.5, 1.0, 0.3, 0.8][k] - 0.35, 0.35, lambda rt, c=c: done(c, rt)))
        for k in range(4):           # a worker that finds the queue empty and shut down exits
            ev.append((wbox[k], free[k], 0.4, lambda rt, k=k: restyle(wbox[k], rt, GREY_D, 0.5)))
            ev.append((wlab[k], free[k], 0.4, lambda rt, k=k: restyle(wlab[k], rt, GREY_D, 0.5)))
        t_end = max(free) + 0.4
        await_c = M("pool.awaitTermination(20, SECONDS)", 24, BLUE_M).next_to(main, RIGHT, buff=0.35)
        wbar = Rectangle(width=0.01, height=0.16, stroke_width=0).set_fill(BLUE_M, 0.8)
        wbar.move_to(await_c.get_corner(DL) + DOWN * 0.25, aligned_edge=LEFT)
        wfull = await_c.width
        ev.append((wbar, 0.0, t_end, lambda rt: lazy(wbar, rt, lambda mob, s, a: mob.stretch_to_fit_width(max(0.01, a * wfull))
                                                      .move_to(await_c.get_corner(DL) + DOWN * 0.25, aligned_edge=LEFT),
                                                      rate=linear)))
        tl = timeline(ev)
        st3 = T("pool: terminated", 28, GREY_A).move_to(state)
        tru = M("true", 26, GREEN_M).next_to(await_c, RIGHT, buff=0.3)
        seq(self, "The queued and running tasks still finish. To wait for that, main calls awaitTermination, "
                  "with a timeout.",
            ([FadeOut(mcall), FadeOut(ret), FadeOut(rej)], 0.4), ([FadeIn(await_c)], 0.4), 1.1, ([tl], tl.run_time))
        self.beat("When the last worker exits, the pool is terminated, and awaitTermination returns true. "
                  "If the timeout runs out first, it returns false.",
                  Transform(state, st3), FadeIn(tru), run_time=1.0)

        # =============== part 4: shutdownNow ===============
        for c in cs + rs:
            self.remove(c)
        cs, rs = start_state()
        st0 = T("pool: running", 28, GREY_A).move_to(state)
        now_c = M("pool.shutdownNow()", 26, BLUE_M).next_to(main, RIGHT, buff=0.35)
        self.play(FadeOut(VGroup(await_c, wbar, tru, door)), Transform(state, st0),
                  *[w.animate.set_stroke(TEAL_M, opacity=1).set_fill(dark(TEAL_M), 1) for w in wbox],
                  *[l.animate.set_color(TEAL_M).set_opacity(1) for l in wlab],
                  *[FadeIn(c) for c in cs + rs], run_time=0.8)
        lst = RoundedRectangle(corner_radius=0.1, width=3.8, height=0.75, stroke_color=BLUE_M, stroke_width=2)
        lst.move_to([-2.19, -1.0, 0])
        lst_l = M("returned: List<Runnable>", 22, BLUE_M).next_to(lst, DOWN, buff=0.12)
        lst_pos = [np.array([-0.75 - 0.72 * i, -1.0, 0]) for i in range(5)]
        st4 = T("pool: stopping", 28, GREY_A).move_to(state)
        seq(self, "shutdownNow is the hard stop. It closes the door, empties the queue, "
                  "and hands back the five tasks that never ran.",
            ([FadeIn(now_c), Create(door), Transform(state, st4)], 0.8), 1.2,
            ([FadeIn(lst), FadeIn(lst_l)], 0.5),
            ([LaggedStart(*[c.animate.move_to(p) for c, p in zip(cs, lst_pos)], lag_ratio=0.12)], 1.6))
        intr = [T("interrupt", 22, RED_M).next_to(b, RIGHT, buff=0.15) for b in wbox]
        keep = T("never checks: keeps running", 22, GOLD_M).move_to([3.4, -2.2, 0])
        seq(self, "Then it interrupts the four running tasks. An interrupt is only a request. "
                  "Three were blocked in calls that check it, and stop. One is in a loop that never checks, and keeps running.",
            ([*[FadeIn(i, shift=LEFT * 0.15) for i in intr], *[r.animate.set_stroke(RED_M) for r in rs]], 0.8), 2.6,
            ([stopped(rs[0], 0.5), stopped(rs[1], 0.5), stopped(rs[2], 0.5)], 0.5), 2.0,
            ([FadeIn(keep), Indicate(rs[3], color=GOLD_M, scale_factor=1.3)], 1.0))
        self.play(FadeOut(VGroup(tray, q_l, ex_l, workers, main, now_c, door, lst, lst_l, *cs, *rs, *intr, keep, state)),
                  run_time=0.8)

        # =============== part 5: idiom, rule, check ===============
        jc = code(["pool.shutdown();",
                   "if (!pool.awaitTermination(20, SECONDS))",
                   "    pool.shutdownNow();"], 26)
        kc = code(["pool.shutdown()",
                   "if (!pool.awaitTermination(20, SECONDS))",
                   "    pool.shutdownNow()"], 26)
        for b in (jc, kc):
            b[0].set_color(BLUE_M); b[1].set_color(GREEN_M); b[2].set_color(RED_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, 1.2, 0])
        self.beat("The usual idiom puts them together. shutdown, wait a while, then shutdownNow for the stragglers.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        rule = VGroup(T("shutdown: no new work, the queue still drains.", 28),
                      T("shutdownNow: also drops the queue and interrupts.", 28),
                      T("Neither one waits. awaitTermination does.", 28, GOLD_M)).arrange(DOWN, buff=0.18).move_to([0, -2.1, 0])
        rule.scale(min(1, 12 / rule.width))
        self.beat("The rule. shutdown stops new work, and the queue still drains. shutdownNow also drops the queue, and "
                  "interrupts. Neither one waits. awaitTermination does.",
                  LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rule], lag_ratio=0.6), run_time=4.0)
        self.play(FadeOut(VGroup(cg, rule)), run_time=0.6)
        chk = T("main returns, and nobody called shutdown on a fixed pool.", 30).move_to([0, 1.0, 0])
        chk2 = T("Does the JVM exit?", 30).move_to([0, 0.35, 0])
        VGroup(chk, chk2).scale(min(1, 12 / chk.width))
        self.beat("Check yourself. main returns, and nobody called shutdown on a fixed pool. Does the JVM exit?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.0)
        self.wait(2.5)
        ans = T("No. Its workers are not daemon threads: they wait in take() and keep the JVM alive.", 28, GOLD_M)
        ans.move_to([0, -0.9, 0]).scale(min(1, 12 / ans.width))
        self.beat("No. Its workers are not daemon threads. They wait in take forever, and keep the JVM alive.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.6)
