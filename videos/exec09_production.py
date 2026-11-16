from fg import *
import fg

fg.SAY[:0] = [(r"\bnewFixedThreadPool\b", "new fixed thread pool"), (r"\bRejectedExecutionException\b", "Rejected Execution Exception"),
              (r"\bAbortPolicy\b", "abort policy"), (r"\bCallerRunsPolicy\b", "caller runs policy"),
              (r"\bDiscardPolicy\b", "discard policy"), (r"\bThreadPoolExecutor\b", "thread pool executor"),
              (r"\bpool-3-thread-1\b", "pool three thread one"), (r"\b503\b", "five oh three")]


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


def mvq(m, p, op, rt):
    """Move to p and fade to opacity op."""
    p = np.array(p, dtype=float)

    def fn(mob, s, a):
        o0 = s.get_fill_opacity()
        mob.move_to(interpolate(s.get_center(), p, a)).set_opacity(interpolate(o0, op, a))
    return lazy(m, rt, fn)


def done(m, rt):
    def fn(mob, s, a):
        mob.become(s.copy().set_stroke(GREEN_M).set_fill(GREEN_M, 0.5).scale(1 + 0.4 * a).set_opacity(1 - a))
    return lazy(m, rt, fn, rate=linear)


def reject(m, rt):
    def fn(mob, s, a):
        mob.become(s.copy().set_stroke(RED_M).set_fill(dark(RED_M, 0.45), 1).shift(DOWN * 0.45 * a).set_opacity(1 - a))
    return lazy(m, rt, fn, rate=linear)


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


def at(log, t):
    v = log[0][1]
    for t0, x in log:
        if t0 <= t + 1e-9:
            v = x
        else:
            break
    return v


class Exec09Production(VoiceScene):
    """exec-09, section 2: payments arrive faster than two threads finish them. An unbounded queue accepts
    everything and time in queue climbs; a bounded queue rejects at once; the four numbers to watch; named threads."""

    def construct(self):
        self.title_card("A pool under load", "a queue with no end, a queue with a wall, and the numbers that show it")

        QY, HEAD, SPC = 1.2, -0.4, 0.5

        def slot(i):
            return np.array([HEAD - SPC * i, QY, 0])

        def vis(i):
            return HEAD - SPC * i > -6.2

        ENTRY = np.array([-6.05, QY, 0])
        WY = [1.85, 0.55]
        wbox = [RoundedRectangle(corner_radius=0.12, width=3.6, height=0.85, stroke_color=TEAL_M, stroke_width=3)
                .set_fill(dark(TEAL_M), 1).move_to([2.9, y, 0]) for y in WY]
        wlab = [M(f"pool-3-thread-{k + 1}", 22, TEAL_M).move_to([3.35, y, 0]) for k, y in enumerate(WY)]
        seat = [np.array([1.55, y, 0]) for y in WY]
        arrive_l = T("payments arrive", 24, GREY_B).move_to([-5.0, 2.05, 0])
        arrive_a = Arrow([-6.3, 1.75, 0], [-5.0, 1.75, 0], buff=0, stroke_width=3, color=GREY_B,
                         max_tip_length_to_length_ratio=0.15)

        # dashboard: four tiles
        TX = [-4.65, -1.55, 1.55, 4.65]
        names = ["queue size", "active / max", "rejected", "time in queue"]
        cols = [GOLD_M, TEAL_M, RED_M, WHITE]
        tiles = VGroup(*[RoundedRectangle(corner_radius=0.12, width=2.85, height=1.5, stroke_color=GREY_D, stroke_width=2)
                         .move_to([x, -2.1, 0]) for x in TX])
        tlab = VGroup(*[T(n, 24, GREY_B).move_to([x, -1.65, 0]) for n, x in zip(names, TX)])
        vals = VGroup(*[T(v0, 40, c).move_to([x, -2.35, 0]) for v0, c, x in zip(["0", "0 of 2", "0", "-"], cols, TX)])
        logs = {"q": [(0, 0)], "r": [(0, 0)], "w": [(0, None)], "a": [(0, 0)]}
        clk = ValueTracker(0.0)
        shown = [None] * 4

        def fmt(k, t):
            if k == 0:
                return str(at(logs["q"], t))
            if k == 1:
                return f"{at(logs['a'], t)} of 2"
            if k == 2:
                return str(at(logs["r"], t))
            w = at(logs["w"], t)
            return "-" if w is None else f"{w:.1f} s"

        def mk_upd(k):
            def upd(m):
                s = fmt(k, clk.get_value())
                if s != shown[k]:
                    shown[k] = s
                    m.become(T(s, 40, cols[k]).move_to([TX[k], -2.35, 0]))
            return upd

        def simulate(t_end, arr_dt, svc, cap):
            """Two workers, one queue. Returns timeline events and fills the dashboard logs."""
            ev, q, land, tarr = [], [], {}, {}
            free, first, last, rej = [0.0, 0.0], [None, None], -1.0, 0
            held = [False, False]      # a worker whose task is still running when the clip ends keeps it
            arrivals = list(np.arange(0.0, t_end, arr_dt))
            for k in logs:
                logs[k] = [(0, 0)] if k != "w" else [(0, None)]
            chips = []
            ends = []          # (time, worker) when a task finishes
            while True:
                ta = arrivals[0] if arrivals else None
                tt, w = None, None
                cand = [k for k in range(2) if not held[k]]
                if q and cand:
                    w = min(cand, key=lambda k: free[k])
                    tt = max(free[w], land[id(q[0])], last + 0.3)
                if ta is None and tt is None:
                    break
                if tt is not None and (ta is None or tt <= ta):
                    c = q.pop(0)
                    last = tt
                    if first[w] is None:
                        first[w] = tt + 0.35
                    ev.append((c, tt, 0.35, lambda rt, c=c, w=w: mvq(c, seat[w], 1, rt)))
                    for i, c2 in enumerate(q):
                        ev.append((c2, tt, 0.25, lambda rt, c2=c2, i=i: mvq(c2, slot(i), 1 if vis(i) else 0, rt)))
                    if tt + 0.35 + svc - 0.3 < t_end - 0.05:      # tasks still running at the end stay in their seats
                        ev.append((c, tt + 0.35 + svc - 0.3, 0.3, lambda rt, c=c: done(c, rt)))
                    else:
                        held[w] = True
                    free[w] = tt + 0.35 + svc
                    ends.append(free[w])
                    logs["q"].append((tt, len(q)))
                    logs["w"].append((tt + 0.35, tt - tarr[id(c)]))
                else:
                    arrivals.pop(0)
                    c = RoundedRectangle(corner_radius=0.07, width=0.4, height=0.4, stroke_color=GOLD_M, stroke_width=2.5)
                    c.set_fill(dark(GOLD_M, 0.45), 1).set_z_index(5).move_to(ENTRY).set_opacity(0)
                    chips.append(c)
                    if cap is None or len(q) < cap:
                        i = len(q)
                        if vis(i):
                            ev.append((c, ta, 0.4, lambda rt, c=c, i=i: mvq(c, slot(i), 1, rt)))
                        else:
                            c.move_to(slot(i))
                        q.append(c)
                        land[id(c)], tarr[id(c)] = ta + 0.4, ta
                        logs["q"].append((ta, len(q)))
                    else:
                        wall = np.array([HEAD - SPC * cap - 0.15, QY, 0])
                        ev.append((c, ta, 0.4, lambda rt, c=c, p=wall: mvq(c, p, 1, rt)))
                        ev.append((c, ta + 0.4, 0.45, lambda rt, c=c: reject(c, rt)))
                        rej += 1
                        logs["r"].append((ta + 0.4, rej))
            # active count: both workers stay busy once they have taken their first task
            logs["a"] = [(0, 0)] + [(t, n + 1) for n, t in enumerate(sorted(x for x in first if x is not None))]
            logs["q"].sort(key=lambda e: e[0]); logs["w"].sort(key=lambda e: e[0]); logs["r"].sort(key=lambda e: e[0])
            return ev, chips

        # ---------------- the picture ----------------
        rails = VGroup(Line([-6.3, QY + 0.33, 0], [0.0, QY + 0.33, 0]), Line([-6.3, QY - 0.33, 0], [0.0, QY - 0.33, 0]),
                       Line([0.0, QY + 0.33, 0], [0.0, QY - 0.33, 0])).set_stroke(GOLD_M, 2.5)
        q_l = T("queue: no limit", 28, GOLD_M).move_to([-2.0, 2.05, 0])
        self.beat("An authorization pool has two threads. Payments come in faster than two threads can finish them.",
                  *[FadeIn(VGroup(b, l)) for b, l in zip(wbox, wlab)], FadeIn(arrive_l), GrowArrow(arrive_a), run_time=1.6)
        self.beat("It came from newFixedThreadPool, so its queue has no limit.", Create(rails), FadeIn(q_l), run_time=1.2)
        self.beat("Below are four numbers a dashboard would show.", FadeIn(tiles), FadeIn(tlab), FadeIn(vals), run_time=1.2)
        shown[:] = ["0", "0 of 2", "0", "-"]
        for k, v in enumerate(vals):
            v.add_updater(mk_upd(k))
        self.beat("What does a caller notice while the queue keeps growing?")
        self.wait(1.5)

        ev, chips1 = simulate(9.0, 0.2, 0.75, None)
        self.add(*chips1)
        tl = timeline(ev)
        T1 = tl.run_time
        clk.set_value(0)
        seq(self, "At first, nothing. Every task is accepted, and nothing fails. But each new task waits behind all the "
                  "others, so time in queue keeps climbing. Every queued task holds memory too.",
            ([tl, clk.animate(rate_func=linear).set_value(T1)], T1))
        for v in vals:
            v.suspend_updating()
        self.beat("Nobody is told. Each caller just waits longer than the last.",
                  Indicate(vals[3], color=WHITE, scale_factor=1.15), Indicate(tlab[2], color=RED_M, scale_factor=1.1),
                  run_time=1.4)

        # ---------------- bounded queue ----------------
        tray = VGroup(Line([-2.15, QY + 0.33, 0], [0.0, QY + 0.33, 0]), Line([-2.15, QY - 0.33, 0], [0.0, QY - 0.33, 0]),
                      Line([0.0, QY + 0.33, 0], [0.0, QY - 0.33, 0])).set_stroke(GOLD_M, 2.5)
        wall = Line([-2.15, QY + 0.33, 0], [-2.15, QY - 0.33, 0], stroke_width=7, color=GOLD_M)
        q_l2 = T("queue: room for 4", 28, GOLD_M).move_to(q_l)
        self.beat("Now give the pool a bounded queue, with room for four.",
                  FadeOut(VGroup(*chips1)), Transform(rails, tray), Create(wall), Transform(q_l, q_l2), run_time=1.4)
        for c in chips1:
            self.remove(c)
        ev, chips2 = simulate(7.0, 0.2, 0.75, 4)
        self.add(*chips2)
        tl = timeline(ev)
        T2 = tl.run_time
        clk.set_value(0)
        for v in vals:
            v.resume_updating()
        rex = M("RejectedExecutionException", 22, RED_M).move_to([-3.5, 0.15, 0]).set_opacity(0)
        self.add(rex)
        rex_in = Succession(Wait(2.0), lazy(rex, 0.5, lambda mob, s, a: mob.set_opacity(a)))
        seq(self, "When it's full, the next task is rejected at once. The default, AbortPolicy, throws a "
                  "RejectedExecutionException.",
            ([tl, clk.animate(rate_func=linear).set_value(T2), rex_in], T2))
        for v in vals:
            v.suspend_updating()
        self.beat("That is what a bounded queue is for. The caller hears about the overload right away, and can answer "
                  "with a fast 503. And time in queue stays short.",
                  Indicate(vals[2], color=RED_M, scale_factor=1.15), Indicate(vals[3], color=WHITE, scale_factor=1.15),
                  run_time=2.0)
        for v in vals:
            v.clear_updaters()

        # ---------------- what to watch ----------------
        self.beat("So watch these four. A queue that keeps growing means tasks arrive faster than they finish.",
                  Indicate(tlab[0], color=GOLD_M, scale_factor=1.1), run_time=1.2)
        self.beat("A pool pinned at its maximum is usually waiting on something downstream.",
                  Indicate(tlab[1], color=TEAL_M, scale_factor=1.1), run_time=1.2)
        cnt_n = T("count them yourself: wrap the handler", 22, GREY_A).move_to([1.55, -3.15, 0])
        self.beat("ThreadPoolExecutor does not count rejections for you. Wrap the handler so it counts, then throws.",
                  Indicate(tlab[2], color=RED_M, scale_factor=1.1), FadeIn(cnt_n), run_time=1.4)
        self.beat("Of the four, time in queue and rejections are what your customers feel.",
                  Indicate(VGroup(tlab[2], vals[2], tlab[3], vals[3]), color=WHITE, scale_factor=1.06), run_time=1.4)

        # ---------------- names ----------------
        new_lab = [M(f"auth-{k}", 26, TEAL_M).move_to(l) for k, l in enumerate(wlab)]
        seq(self, "One more thing. The threads are called pool-3-thread-1 and so on. In a thread dump of a service with "
                  "eight pools, that tells you nothing. Name them after the work they do.",
            ([Indicate(VGroup(*wlab), color=WHITE, scale_factor=1.06)], 1.2), 4.2,
            ([*[Transform(a, b) for a, b in zip(wlab, new_lab)]], 0.9))
        self.play(FadeOut(VGroup(*wbox, *wlab, arrive_l, arrive_a, rails, wall, q_l, tiles, tlab, vals, rex, cnt_n,
                                 *chips2)), run_time=0.8)

        # ---------------- policies and code ----------------
        pn = [M("AbortPolicy", 26, RED_M), M("CallerRunsPolicy", 26, GOLD_M), M("DiscardPolicy", 26, GREY_B)]
        pd = [T("the default: throw, so the caller hears it", 26, GREY_A),
              T("the caller runs the task itself, so it slows down", 26, GREY_A),
              T("drop the task without a word", 26, GREY_A)]
        wmax = max(n.width for n in pn)
        for k, (n, d) in enumerate(zip(pn, pd)):
            n.move_to([0, -0.75 * k, 0], aligned_edge=LEFT)
            d.move_to([wmax + 0.5, -0.75 * k, 0], aligned_edge=LEFT)
        pol = VGroup(*[VGroup(n, d) for n, d in zip(pn, pd)])
        pol.scale(min(1, 12 / pol.width)).move_to([0, 0.5, 0])
        pol_t = T("When the queue is full", 30).move_to([0, 2.4, 0])
        self.beat("When the queue is full, you choose what happens. AbortPolicy throws. CallerRunsPolicy makes the "
                  "submitting thread run the task itself, so the intake slows down. DiscardPolicy drops the task, "
                  "and nobody ever hears about it.",
                  FadeIn(pol_t), LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in pol], lag_ratio=0.9), run_time=6.0)
        self.play(FadeOut(VGroup(pol, pol_t)), run_time=0.6)
        jc = code(["new ThreadPoolExecutor(2, 2, 0, MILLISECONDS,",
                   "    new ArrayBlockingQueue<>(4),",
                   "    Thread.ofPlatform().name(\"auth-\", 0).factory(),",
                   "    countThenAbort);"], 24)
        kc = code(["ThreadPoolExecutor(2, 2, 0, MILLISECONDS,",
                   "    ArrayBlockingQueue(4),",
                   "    Thread.ofPlatform().name(\"auth-\", 0).factory(),",
                   "    countThenAbort)"], 24)
        for b in (jc, kc):
            b[1].set_color(GOLD_M); b[2].set_color(TEAL_M); b[3].set_color(RED_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.3, 0])
        self.beat("Here is the whole pool: two threads, a queue of four, named threads, and a handler that counts, then "
                  "throws.", FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(cg), run_time=0.7)

        # ---------------- rule and check ----------------
        rule = T("Bound the queue, decide what a rejection does,", 32).move_to([0, 2.4, 0])
        rule2 = T("name the threads, and watch time in queue and rejections.", 32).move_to([0, 1.8, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule2.width))
        self.beat("The rule. Bound the queue, decide what a rejection does, name the threads, and watch time in queue "
                  "and rejections.", FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A pool from newFixedThreadPool falls behind during a spike.", 28).move_to([0, 0.2, 0])
        chk2 = T("What does its rejection counter show?", 28).move_to([0, -0.4, 0])
        VGroup(chk, chk2).scale(min(1, 12 / chk.width))
        self.beat("Check yourself. A pool from newFixedThreadPool falls behind during a spike. What does its rejection "
                  "counter show?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("Zero. Its queue has no limit. Watch queue size and time in queue.", 30, GOLD_M).move_to([0, -1.6, 0])
        ans.scale(min(1, 12 / ans.width))
        self.beat("Zero. Its queue has no limit, so nothing is ever rejected. Watch queue size and time in queue instead.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
