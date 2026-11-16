from fg import *
import fg
import random

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bFX\b", "F X"), (r"\bnewVirtualThreadPerTaskExecutor\b",
              "new virtual thread per task executor"), (r"\bnewFixedThreadPool\b", "new fixed thread pool"),
              (r"\b0\.02\b", "zero point zero two"), (r"\b0\.12\b", "zero point one two")]


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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def panel(w, h, color, center):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color, stroke_width=3)
    return r.set_fill(dark(color, 0.1), 1).move_to(center)


class Vt06Migrate(VoiceScene):
    """vt-06, section 0: a fixed pool of 10 threads also kept the database to 10 callers, a limit nobody wrote down;
    virtual threads drop it, so the next resource (the connection pool) takes the burst; a semaphore writes the limit
    back around the database call only, and Little's law (in flight = throughput x time) finds the bottleneck."""

    def construct(self):
        self.title_card("Moving to virtual threads", "the limit you never wrote down")
        rng = random.Random(6)

        # ---------------- the service, its pool, and two downstreams ----------------
        SX = -1.5
        svc = panel(4.6, 4.0, BLUE_M, [SX, -0.3, 0])
        svc_l = T("quote service", 32, BLUE_M).move_to([SX, 2.15, 0])
        db = panel(3.6, 1.7, TEAL_M, [4.35, 1.1, 0])
        db_l = VGroup(T("database", 30, TEAL_M), T("10 connections", 24, GREY_A)).arrange(DOWN, buff=0.12).move_to(db)
        fx = panel(3.6, 1.7, PURPLE_M, [4.35, -1.5, 0])
        fx_l = VGroup(T("FX API", 30, PURPLE_M), T("100 ms a call", 24, GREY_A)).arrange(DOWN, buff=0.12).move_to(fx)
        l_db = Line([0.8, 0.7, 0], db.get_left(), stroke_width=2, color=GREY_D)
        l_fx = Line([0.8, -1.2, 0], fx.get_left(), stroke_width=2, color=GREY_D)

        slot_p = [np.array([SX + (c - 2) * 0.65, 0.35 - r * 0.7, 0]) for r in range(2) for c in range(5)]
        slots = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.5, height=0.5, stroke_color=GREY_B, stroke_width=2)
                         .move_to(p) for p in slot_p])
        pool_l = T("fixed pool of 10 threads", 26, GREY_B).move_to([SX, -1.55, 0])

        Q = [np.array([-6.15 + c * 0.3, 1.0 - r * 0.3, 0]) for r in range(8) for c in range(5)]
        dots = [Dot(radius=0.085, color=BLUE_M).move_to(p).set_z_index(5) for p in Q]
        req_l = T("300 requests", 26, BLUE_M).move_to([-5.55, 1.6, 0])

        self.beat("A quote service runs on a fixed pool of 10 threads, because the database has 10 connections.",
                  FadeIn(svc), FadeIn(svc_l), FadeIn(slots), FadeIn(pool_l), FadeIn(db), FadeIn(db_l),
                  FadeIn(fx), FadeIn(fx_l), Create(l_db), Create(l_fx), run_time=2.0)
        self.beat("Each request queries the database, then calls an FX API for a rate.",
                  ShowPassingFlash(l_db.copy().set_stroke(TEAL_M, 5), time_width=0.6),
                  ShowPassingFlash(l_fx.copy().set_stroke(PURPLE_M, 5), time_width=0.6), run_time=1.6)

        first = dots[-10:]
        seq(self, "A burst of 300 arrives, and the pool takes 10 at a time.",
            ([LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.02), FadeIn(req_l)], 1.2),
            ([LaggedStart(*[d.animate.move_to(slot_p[i]) for i, d in enumerate(first)], lag_ratio=0.06)], 1.2))
        g_db = T("callers at once: 10", 24, TEAL_M).next_to(db, UP, buff=0.12)
        g_fx = T("calls in flight: 10", 24, PURPLE_M).next_to(fx, DOWN, buff=0.12)
        a_t = T("about 3,200 ms, no failures", 28, WHITE).move_to([SX, -2.75, 0])
        self.beat("So the database never sees more than 10 callers. The burst takes about 3,200 milliseconds.",
                  FadeIn(g_db), FadeIn(g_fx), FadeIn(a_t, shift=UP * 0.1), run_time=1.6)

        # ---------------- one line: virtual threads ----------------
        one = VGroup(M("newFixedThreadPool(10)", 26, GREY_B), T("becomes", 24, GREY_B),
                     M("newVirtualThreadPerTaskExecutor()", 26, BLUE_M)).arrange(RIGHT, buff=0.25)
        fit(one, 12.4).move_to([0, 2.75, 0])
        vt_l = T("one virtual thread per request", 24, BLUE_M).move_to(pool_l)
        seq(self, "The obvious migration is one line: a virtual thread per task. Now all 300 run at once. "
                  "What happens at the database?",
            ([FadeIn(one, shift=DOWN * 0.15), FadeOut(a_t)], 1.0), 1.2,
            ([FadeOut(slots), Transform(pool_l, vt_l), FadeOut(req_l),
              *[d.animate.move_to([rng.uniform(-3.4, 0.4), rng.uniform(-1.15, 1.4), 0]) for d in dots]], 1.4))
        self.wait(1.6)
        door = [np.array([2.05 + rng.uniform(-0.4, 0.4), 1.1 + rng.uniform(-0.75, 0.75), 0]) for _ in dots]
        g_db2 = T("callers at once: 300", 24, RED_M).move_to(g_db)
        self.beat("All 300 ask for a connection at once, and the pool waits only 30 milliseconds for one. "
                  "That timeout was tuned for 10 callers.",
                  *[d.animate.move_to(p) for d, p in zip(dots, door)], Transform(g_db, g_db2),
                  db.animate.set_stroke(RED_M), run_time=1.6)
        fails = [d for i, d in enumerate(dots) if i % 4 != 0]
        b_t = T("one run: 71 ok, 229 failed", 28, RED_M).move_to([SX, -2.75, 0])
        self.beat("Most of them time out. In one run, 71 requests worked and 229 failed.",
                  *[d.animate.set_color(RED_M) for d in fails], FadeIn(b_t, shift=UP * 0.1), run_time=1.2)
        self.play(*[FadeOut(d, shift=DOWN * 0.3) for d in fails], run_time=0.6)

        jobs = VGroup(T("the pool's two jobs:", 28), T("1. run the requests", 28, BLUE_M),
                      T("2. keep the database", 28, TEAL_M), T("    to 10 callers", 28, TEAL_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        jobs.move_to([SX, -0.3, 0])
        keep = [d for d in dots if d not in fails]
        self.play(*[FadeOut(d) for d in keep], FadeOut(pool_l), FadeOut(b_t), FadeOut(g_db), FadeOut(g_fx), run_time=0.5)
        fit(jobs, 4.2)
        self.beat("The pool had two jobs. It ran the requests, and it kept the database to 10 callers. "
                  "Nobody wrote the second job down. Virtual threads take over the first, and drop the second.",
                  FadeIn(jobs), run_time=1.4)
        self.play(Indicate(jobs[2:], color=RED_M, scale_factor=1.05), run_time=1.0)

        # ---------------- write the limit down: a semaphore at the database door ----------------
        self.play(FadeOut(jobs), db.animate.set_stroke(TEAL_M), FadeOut(one), run_time=0.5)
        GX = 1.65
        gate = RoundedRectangle(corner_radius=0.1, width=0.78, height=1.7, stroke_color=GOLD_M, stroke_width=3)
        gate.set_fill(dark(GOLD_M), 1).move_to([GX, 1.1, 0])
        permits = VGroup(*[Square(0.18, stroke_width=0).set_fill(GOLD_M, 1).move_to([GX - 0.17 + (k % 2) * 0.34, 1.66 - (k // 2) * 0.28, 0])
                           for k in range(10)])
        gate_l = VGroup(T("semaphore", 24, GOLD_M), T("10 permits", 24, GOLD_M)).arrange(DOWN, buff=0.06).move_to([GX, -0.15, 0])
        self.beat("So put the second job back, on purpose: a semaphore with 10 permits, around the database call only.",
                  FadeIn(gate), FadeIn(permits), FadeIn(gate_l), run_time=1.4)

        dots2 = [Dot(radius=0.085, color=BLUE_M).move_to([rng.uniform(-3.4, 0.4), rng.uniform(-1.15, 1.4), 0]).set_z_index(5)
                 for _ in range(40)]
        qline = [np.array([0.55 - (i % 4) * 0.24, 1.6 - (i // 4) * 0.22, 0]) for i in range(40)]
        g_db3 = T("callers at once: 10", 24, TEAL_M).next_to(db, UP, buff=0.12)
        self.beat("Requests line up there, and the database gets 10 at a time.",
                  *[FadeIn(d, scale=0.5) for d in dots2], run_time=0.6)
        self.play(*[d.animate.move_to(p) for d, p in zip(dots2[:20], qline)], FadeIn(g_db3), run_time=1.0)
        fx_p = [np.array([rng.uniform(1.0, 2.4), rng.uniform(-2.1, -0.95), 0]) for _ in dots2[20:]]
        g_fx2 = T("calls in flight: about 200", 24, PURPLE_M).next_to(fx, DOWN, buff=0.12)
        self.beat("The FX calls never needed a limit. They now overlap freely: about 200 in flight instead of 10.",
                  *[d.animate.move_to(p).set_color(PURPLE_M) for d, p in zip(dots2[20:], fx_p)], FadeIn(g_fx2),
                  run_time=1.6)
        c_t = T("about 260 ms, no failures", 28, GREEN_M).move_to([SX, -2.75, 0])
        self.beat("The burst now takes about 260 milliseconds, with no failures.", FadeIn(c_t, shift=UP * 0.1), run_time=0.8)
        self.play(FadeOut(VGroup(svc, svc_l, db, db_l, fx, fx_l, l_db, l_fx, gate, permits, gate_l, *dots2, g_db3,
                                 g_fx2, c_t)), run_time=0.7)

        # ---------------- Little's law ----------------
        law = T("in flight = throughput × time", 46, GOLD_M).move_to([0, 2.55, 0])
        self.beat("Little's law tells you where requests wait: requests in flight equal throughput times time.",
                  Write(law), run_time=1.6)
        ex1 = T("400 per second × 0.12 s  =  48 in flight", 34).move_to([0, 1.5, 0])
        self.beat("400 a second, for 0.12 seconds each, is about 48 in flight.",
                  FadeIn(ex1, shift=UP * 0.1), run_time=1.0)
        ex2 = VGroup(T("10 permits, each held 20 ms:", 34, TEAL_M),
                     T("10 / 0.02 s  =  at most 500 per second", 34, TEAL_M)).arrange(DOWN, buff=0.18).move_to([0, 1.2, 0])
        self.beat("Turn it around: 10 permits, held 20 milliseconds each, serve at most 500 requests a second.",
                  FadeOut(ex1), FadeIn(ex2, shift=UP * 0.1), run_time=1.2)
        self.beat("So what happens at 600 a second?")
        self.wait(1.3)

        # queue gauge rising while throughput stays flat
        BX0, BY0 = -4.2, -3.0
        vals = [44, 80, 113, 200]
        qb, ql = [], []
        for j, v in enumerate(vals):
            h = v / 200 * 2.2
            b = Rectangle(width=0.85, height=h, stroke_width=0).set_fill(GOLD_M, 0.85).move_to([BX0 + j * 1.3, BY0 + h / 2, 0])
            qb.append(b)
            ql.append(T("200+" if v == 200 else str(v), 28, GOLD_M).next_to(b, UP, buff=0.1))
        qb_l = T("permit queue", 26, GOLD_M).move_to([BX0 + 1.95, BY0 - 0.3, 0])
        thr = DashedLine([1.0, -1.9, 0], [6.1, -1.9, 0], dash_length=0.12, stroke_width=4, color=TEAL_M)
        thr_l = T("throughput: flat, near 500 a second", 28, TEAL_M).move_to([3.55, -1.4, 0])
        seq(self, "The queue on the semaphore grows on every reading, while throughput stays flat near 500.",
            *[([GrowFromEdge(qb[j], DOWN), FadeIn(ql[j])], 0.5) for j in range(4)],
            ([FadeIn(qb_l), Create(thr), FadeIn(thr_l)], 0.8))
        self.beat("A rising queue with flat throughput is what a full downstream looks like.",
                  Indicate(VGroup(*qb), color=WHITE, scale_factor=1.04), run_time=1.4)
        self.play(FadeOut(VGroup(law, ex2, *qb, *ql, qb_l, thr, thr_l)), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = T("Removing the pool removes a limit. Write it down:", 32).move_to([0, 2.3, 0])
        rule2 = T("one semaphore per downstream, sized from that downstream.", 32, GOLD_M).move_to([0, 1.65, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule2.width))
        self.beat("The rule. Removing the pool removes a limit. Write it down: one semaphore per downstream, "
                  "sized from that downstream.", FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("To make it faster, someone raises the semaphore to 300 permits.", 28).move_to([0, 0.15, 0])
        chk2 = T("The database still has 10 connections. What happens in a burst?", 28).move_to([0, -0.45, 0])
        VGroup(chk, chk2).scale(min(1, 12 / max(chk.width, chk2.width)))
        self.beat("Check yourself. To make it faster, someone raises the semaphore to 300 permits. "
                  "The database still has 10 connections. What happens in a burst?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("The limit is gone again: 300 callers reach 10 connections, and most time out.", 28, GOLD_M).move_to([0, -1.7, 0])
        fit(ans, 12)
        self.beat("The limit is gone again: 300 callers reach 10 connections, and most time out.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.5)
