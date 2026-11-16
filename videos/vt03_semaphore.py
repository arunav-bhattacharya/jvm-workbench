from fg import *
import fg
import random

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\btryAcquire\b", "try acquire"), (r"\b503\b", "five oh three")]


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


# Animations that read the mobject's state when they start, not when they are built,
# so they can sit late in a Succession after other steps changed the same mobject.
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


def along(m, pts, rt):
    pts = [np.array(q, dtype=float) for q in pts]
    segs = [np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])]
    total = sum(segs)

    def fn(mob, s, a):
        d = a * total
        for n, ((p0, p1), L) in enumerate(zip(zip(pts, pts[1:]), segs)):
            if d <= L or n == len(segs) - 1:
                u = min(1.0, d / L) if L else 1.0
                mob.move_to(interpolate(p0, p1, u)); return
            d -= L
    return lazy(m, rt, fn)


def wake(m, rt):
    return lazy(m, rt, lambda mob, s, a: mob.set_fill(BLUE_M, opacity=a))


def park(m, rt):
    return lazy(m, rt, lambda mob, s, a: mob.set_fill(BLUE_M, opacity=1 - a))


def finish(m, rt):
    def fn(mob, s, a):
        mob.become(s.copy().set_fill(GREEN_M, 1).set_stroke(GREEN_M).scale(1 + 0.8 * a).set_opacity(1 - a))
    return lazy(m, rt, fn, rate=linear)


class Vt03Semaphore(VoiceScene):
    """vt-03, section 3: a virtual thread per payment is cheap, the 20 database connections are not;
    a shared Semaphore is a desk of 20 permits in front of the database, waiters park for the price of a heap object."""

    def construct(self):
        self.title_card("Cheap threads, scarce connections", "one shared semaphore in front of the database")
        rng = random.Random(7)
        LY = -0.15

        # ---- the database: 20 connection slots ----
        DX = 3.75
        dbox = RoundedRectangle(corner_radius=0.15, width=3.4, height=2.4, stroke_color=TEAL_M, stroke_width=3)
        dbox.set_fill(dark(TEAL_M), 1).move_to([DX, LY, 0])
        slot_p = [np.array([DX + (c - 2) * 0.62, LY + (1.5 - r) * 0.5, 0]) for r in range(4) for c in range(5)]
        slots = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.5, height=0.36, stroke_color=GREY_D, stroke_width=2)
                         .move_to(p) for p in slot_p])
        db_l = T("ledger database", 30, TEAL_M).move_to([DX, 1.9, 0])
        db_n = T("room for 20 connections", 24, GREY_B).move_to([DX, 1.42, 0])

        # ---- the lobby: one virtual thread per payment ----
        COLS, ROWS, SP, LX = 8, 7, 0.38, -4.7
        lob_p = [np.array([LX + (c - (COLS - 1) / 2) * SP, LY + ((ROWS - 1) / 2 - r) * SP, 0])
                 for r in range(ROWS) for c in range(COLS)]
        th = [Circle(radius=0.1, stroke_color=BLUE_M, stroke_width=2).set_fill(BLUE_M, 1).move_to(p).set_z_index(5)
              for p in lob_p]
        thg = VGroup(*th)
        lob_l = T("5,000 virtual threads", 30, BLUE_M).move_to([LX, 1.9, 0])
        lob_n = T("one per payment", 24, GREY_B).move_to([LX, 1.42, 0])

        self.beat("Every payment has to write a row to the ledger database. It has room for 20 connections, "
                  "so it can serve 20 calls at a time.",
                  FadeIn(dbox), FadeIn(slots), FadeIn(db_l), FadeIn(db_n), run_time=1.6)
        self.beat("You have a batch of 5,000 payments. With virtual threads, each payment gets its own thread.",
                  LaggedStart(*[FadeIn(t, scale=0.5) for t in th], lag_ratio=0.03), FadeIn(lob_l), FadeIn(lob_n),
                  run_time=2.6)
        self.beat("That part is cheap. Each virtual thread is a small object on the heap.",
                  Indicate(lob_l, color=WHITE, scale_factor=1.05), run_time=1.2)
        self.beat("So how many of them ask the database for a connection at the same moment?")
        self.wait(1.8)

        flood_p = [np.array([rng.uniform(DX - 1.5, DX + 1.5), rng.uniform(LY - 1.0, LY + 1.0), 0]) for _ in th]
        flood_t = T("5,000 calls at once", 28, RED_M).move_to([DX, 2.65, 0])
        self.beat("All 5,000. They all go straight for the database.",
                  LaggedStart(*[t.animate.move_to(p) for t, p in zip(th, flood_p)], lag_ratio=0.01),
                  dbox.animate.set_stroke(RED_M), FadeIn(flood_t), run_time=1.8)
        self.beat("That is far more than the 20 it has room for. The threads are cheap. The database is not.",
                  Indicate(db_n, color=RED_M, scale_factor=1.08), run_time=1.4)
        self.play(*[t.animate.move_to(p) for t, p in zip(th, lob_p)], dbox.animate.set_stroke(TEAL_M),
                  FadeOut(flood_t), run_time=1.0)

        # ---- the desk of badges ----
        KX = -0.8
        desk = RoundedRectangle(corner_radius=0.15, width=1.6, height=2.4, stroke_color=GOLD_M, stroke_width=3)
        desk.set_fill(dark(GOLD_M), 1).move_to([KX, LY, 0])
        tok_p = [np.array([KX + (c - 1.5) * 0.34, LY + (2 - r) * 0.4, 0]) for r in range(5) for c in range(4)]
        tok = [Square(0.2, stroke_width=0).set_fill(GOLD_M, 1).move_to(p).set_z_index(4) for p in tok_p]
        desk_l = T("front desk", 30, GOLD_M).move_to([KX, 1.9, 0])
        desk_n = T("20 badges", 24, GREY_B).move_to([KX, 1.42, 0])
        self.beat("Think of the front desk of an office building. It keeps 20 visitor badges, one for each connection.",
                  FadeIn(desk), *[FadeIn(t) for t in tok], FadeIn(desk_l), FadeIn(desk_n), run_time=1.8)

        # counter: how many threads are inside the database right now
        cnt = VGroup()
        state = {"n": -1, "max": 0}

        def count_upd(g):
            n = sum(1 for t in th if t.get_x() > DX - 1.7 and t.get_fill_opacity() > 0.5)
            m = max(state["max"], n)
            if m != state["n"]:
                state["n"] = state["max"] = m
                g.become(T(f"most calls at once: {m}", 28, TEAL_M).move_to([DX, 2.65, 0]))
        count_upd(cnt)

        def L(k):        # where a thread sits in slot k
            return slot_p[k] + LEFT * 0.11

        def R(k):        # where its badge sits
            return slot_p[k] + RIGHT * 0.12

        # first 20: the threads nearest the desk; the far slots and the right badge column fill first
        order = sorted(range(len(th)), key=lambda i: (-lob_p[i][0], abs(lob_p[i][1] - LY)))
        first = order[:20]
        slot_order = sorted(range(20), key=lambda k: (-slot_p[k][0], slot_p[k][1]))
        tok_order = sorted(range(20), key=lambda k: (-tok_p[k][0], -tok_p[k][1]))
        occ = {}           # slot -> thread
        badge = {}         # slot -> token index
        steps = []
        for j, i in enumerate(sorted(first, key=lambda i: -lob_p[i][1])):
            k, b = slot_order[j], tok_order[j]
            occ[k], badge[k] = i, b
            steps.append(Succession(Wait(j * 0.13), mv(th[i], tok_p[b], 0.55),
                                    AnimationGroup(mv(th[i], L(k), 0.75), mv(tok[b], R(k), 0.75))))
        self.add(cnt)
        cnt.add_updater(count_upd)
        g20 = AnimationGroup(*steps)
        seq(self, "To go in, a thread must take a badge. The first 20 each take one, and go in.",
            1.2, ([g20], g20.run_time))

        waiting = [i for i in range(len(th)) if i not in first]
        self.beat("Now the desk is empty. What happens to the next thread?",
                  Indicate(desk_n, color=WHITE, scale_factor=1.1), run_time=1.0)
        self.wait(1.6)
        note = VGroup(T("parked: a small heap object", 24, GREY_A),
                      T("holding no OS thread", 24, GREY_A)).arrange(DOWN, buff=0.12).move_to([LX, -2.85, 0])
        self.beat("It waits. On a virtual thread, that wait parks the thread. A parked thread holds no OS thread. "
                  "It stays a small object on the heap, so 5,000 waiters are cheap too.",
                  *[th[i].animate.set_fill(BLUE_M, opacity=0) for i in waiting], FadeIn(note, shift=UP * 0.15),
                  run_time=1.6)

        LANE = -1.9

        def cycle(k, w, delay):
            """Thread in slot k finishes; its badge goes back along the bottom lane; waiter w wakes, takes it, goes in."""
            o, b = occ[k], badge[k]
            occ[k] = w
            return Succession(Wait(delay), finish(th[o], 0.35),
                              along(tok[b], [R(k), [R(k)[0], LANE, 0], [tok_p[b][0], LANE, 0], tok_p[b]], 0.8),
                              wake(th[w], 0.2), mv(th[w], tok_p[b], 0.5),
                              AnimationGroup(mv(th[w], L(k), 0.55), mv(tok[b], R(k), 0.55)))

        def pick_waiter():
            # any waiter can be woken; take one from the column nearest the desk
            xmax = max(lob_p[i][0] for i in waiting)
            col = [i for i in waiting if abs(lob_p[i][0] - xmax) < 1e-6]
            w = rng.choice(col)
            waiting.remove(w)
            return w

        k0 = slot_order[19]
        seq(self, "When a call finishes, the thread hands its badge back on the way out. "
                  "That wakes one waiter, and it takes the badge in.",
            1.0, ([cycle(k0, pick_waiter(), 0.0)], 2.4))

        cyc = []
        ks = [k for k in rng.sample(range(20), 20) if k != k0] + [k0]
        for j in range(26):
            cyc.append(cycle(ks[j % 20], pick_waiter(), j * 0.24))
        grp = AnimationGroup(*cyc)
        seq(self, "Calls finish, badges come back, waiters go in. The database never sees more than 20.",
            ([grp], grp.run_time))

        sem_l = T("Semaphore", 30, GOLD_M).move_to(desk_l)
        sem_n = T("20 permits", 24, GREY_B).move_to(desk_n)
        self.beat("This desk is a Semaphore. Its badges are called permits.",
                  Transform(desk_l, sem_l), Transform(desk_n, sem_n), run_time=1.2)
        acq_a = Arrow([-3.35, -1.75, 0], [-1.7, -1.75, 0], buff=0, stroke_width=3, color=GOLD_M,
                      max_tip_length_to_length_ratio=0.15)
        acq_t = M("acquire()", 24, GOLD_M).next_to(acq_a, DOWN, buff=0.12)
        lane = DashedLine([DX - 1.2, LANE, 0], [KX + 0.6, LANE, 0], dash_length=0.1, stroke_width=2, color=GOLD_M)
        lane_tip = Triangle(fill_opacity=1, stroke_width=0, color=GOLD_M).scale(0.09).rotate(PI / 2).move_to([KX + 0.55, LANE, 0])
        rel_t = M("release()", 24, GOLD_M).move_to([1.2, LANE - 0.35, 0])
        seq(self, "acquire takes a permit, and waits if none is left. release gives one back, and wakes a waiter.",
            ([GrowArrow(acq_a), FadeIn(acq_t)], 0.8), 1.8, ([Create(lane), FadeIn(lane_tip), FadeIn(rel_t)], 0.8))
        cnt.clear_updaters()
        self.play(FadeOut(VGroup(dbox, slots, db_l, db_n, thg, lob_l, lob_n, desk, *tok, desk_l, desk_n, note,
                                 cnt, acq_a, acq_t, lane, lane_tip, rel_t)), run_time=0.8)

        # ---- code ----
        jc = code(["final Semaphore db = new Semaphore(20);",
                   "",
                   "db.acquire();",
                   "try {",
                   "    return ledger.record(p);",
                   "} finally {",
                   "    db.release();",
                   "}"], 24)
        kc = code(["val db = Semaphore(20)",
                   "",
                   "db.acquire()",
                   "try {",
                   "    return ledger.record(p)",
                   "} finally {",
                   "    db.release()",
                   "}"], 24)
        for b in (jc, kc):
            for n in (0, 2, 6):
                b[n].set_color(GOLD_M)
            b[4].set_color(TEAL_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin: the same Java class", kc)).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.7, 0])
        self.beat("In code, the semaphore is one field on the client, shared by every request.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.beat("acquire comes before the try. If a thread is interrupted while it waits, it never got a permit, "
                  "so it must not give one back.",
                  Indicate(jc[2], color=WHITE, scale_factor=1.08), Indicate(kc[2], color=WHITE, scale_factor=1.08),
                  run_time=1.4)
        self.beat("release goes in finally, so the permit always comes back, even when the call throws.",
                  Indicate(jc[6], color=WHITE, scale_factor=1.08), Indicate(kc[6], color=WHITE, scale_factor=1.08),
                  run_time=1.4)
        ta = M("db.tryAcquire(200, MILLISECONDS)", 24, GOLD_M).move_to([0, -2.25, 0])
        tb = T("false if no permit came in time: answer with a fast 503", 24, GREY_A).next_to(ta, DOWN, buff=0.18)
        self.beat("And tryAcquire with a timeout returns false when no permit came in time, "
                  "so you can answer with a fast 503.",
                  FadeIn(ta, shift=UP * 0.15), FadeIn(tb, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(cg, ta, tb)), run_time=0.7)

        # ---- rule and check ----
        rule = T("One virtual thread per task.", 36).move_to([0, 2.3, 0])
        rule2 = T("One shared semaphore in front of each scarce resource.", 32, GOLD_M).move_to([0, 1.6, 0])
        rule2.scale(min(1, 12 / rule2.width))
        self.beat("The rule. One virtual thread per task, and one shared semaphore in front of each scarce resource.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A handler creates a new Semaphore(20) for each request.", 28).move_to([0, 0.1, 0])
        chk2 = T("How many calls can reach the database at once?", 28).move_to([0, -0.5, 0])
        VGroup(chk, chk2).scale(min(1, 12 / chk.width))
        self.beat("Check yourself. A handler creates a new semaphore with 20 permits for each request. "
                  "How many calls can reach the database at once?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("As many as there are requests: each one has its own 20 badges.", 30, GOLD_M).move_to([0, -1.7, 0])
        ans.scale(min(1, 12 / ans.width))
        self.beat("As many as there are requests. Each request gets its own desk with 20 badges, so no thread ever waits.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
