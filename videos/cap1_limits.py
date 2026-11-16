from fg import *
import fg

fg.SAY[:0] = [(r"\b50\.00\b", "fifty"), (r"\b40\.00\b", "forty"), (r"\b503\b", "five oh three")]


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


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def frame_box(w, h, color, fill=True):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dark(color) if fill else BLACK, 1)
    return r


TOK = np.array([-5.2, 0.6, 0])           # where the request waits while it is screened
GATE = np.array([-1.6, 1.6, 0])          # the fraud bulkhead: 20 permits
SERV = np.array([2.2, 1.6, 0])           # the fraud service
LIM = np.array([-1.6, -0.8, 0])          # the limits check
POOL = np.array([4.6, -0.8, 0])          # the ledger pool
BAR_W = 2.4


def grid(center, dy=0.0):
    """20 slots in two rows of ten."""
    return [center + np.array([(i % 10 - 4.5) * 0.26, dy + (0.13 if i < 10 else -0.13), 0]) for i in range(20)]


class Cap1Limits(VoiceScene):
    """cap1-03, sections 0 and 1: one request's path through every limit. Its own virtual thread, one 300 ms
    deadline for all of its screening, the shared 20-permit fraud bulkhead whose wait uses the time left, an
    interrupt at the deadline that gives the permit back, the stand-in rule, and the 8 + 80 ledger pool."""

    def construct(self):
        self.title_card("Every limit on one request", "virtual threads, a bulkhead and one deadline")

        # ---------------- why limits ----------------
        f0 = T("in flight = rate x time", 32).move_to([0, 2.0, 0])
        f1 = M("2,000/s x 150 ms = 300", 30).move_to([0, 0.9, 0])
        f2 = M("2,000/s x 2 s = 4,000", 30, RED_M).move_to([0, 0.1, 0])
        self.beat("A transfer request mostly waits. At 2,000 requests a second and 150 milliseconds each, 300 are in "
                  "flight.", FadeIn(f0), FadeIn(f1, shift=UP * 0.15), run_time=1.6)
        self.beat("If the fraud service slows to 2 seconds, 4,000 are.", FadeIn(f2, shift=UP * 0.15), run_time=1.0)
        c1 = T("4,000 waiting virtual threads: cheap", 28, TEAL_M).move_to([0, -1.2, 0])
        c2 = T("4,000 calls to the fraud service: not", 28, RED_M).move_to([0, -1.9, 0])
        seq(self, "Virtual threads make that many waiting threads cheap. But unlimited threads mean unlimited calls to "
                  "the fraud service.", ([FadeIn(c1)], 0.6), 1.6, ([FadeIn(c2)], 0.6))
        self.play(FadeOut(VGroup(f0, f1, f2, c1, c2)), run_time=0.5)

        # ---------------- one request ----------------
        left = ValueTracker(300)
        tcache = {}

        def cd_text():
            k = int(round(left.get_value()))
            if k not in tcache:
                tcache[k] = M(f"{k} ms left", 28, YELLOW_M)
            return tcache[k].copy().move_to(TOK + UP * 1.2)

        cd = always_redraw(cd_text)
        bar_bg = Rectangle(width=BAR_W, height=0.14, stroke_color=GREY_D, stroke_width=1.5).move_to(TOK + UP * 0.75)
        bar = always_redraw(lambda: Rectangle(width=max(0.001, BAR_W * left.get_value() / 300), height=0.14,
                                              stroke_width=0).set_fill(YELLOW_M, 1)
                            .move_to(bar_bg.get_left(), aligned_edge=LEFT))

        def token(amount):
            return box(f"request {amount}", TEAL_M, w=2.4, h=0.8, size=26).move_to(TOK)

        tok = token("40.00")
        vt = T("own virtual thread", 22, TEAL_M).move_to(TOK + DOWN * 0.65)
        seq(self, "Follow one request. It gets its own virtual thread, and one deadline: 300 milliseconds for all of "
                  "its screening.", ([FadeIn(tok), FadeIn(vt)], 0.8), 1.6, ([FadeIn(bar_bg), FadeIn(bar), FadeIn(cd)], 0.8))

        gate = frame_box(2.8, 1.3, PURPLE_M).move_to(GATE)
        gate_l = T("bulkhead: 20 permits", 24, PURPLE_M).move_to(GATE + UP * 1.05)
        serv = frame_box(2.8, 1.3, WHITE, fill=False).move_to(SERV)
        serv_t = T("fraud service", 26).move_to(SERV + UP * 0.35)
        stat = T("20 ms a call", 24, GREY_B).move_to(SERV + UP * 1.05)
        lim = box("limits check", WHITE, w=2.8, h=0.8, size=26).move_to(LIM)
        gs, ss = grid(GATE), grid(SERV, dy=-0.18)
        permits = [Dot(p, radius=0.085, color=PURPLE_M) for p in gs]
        l1 = link(tok, gate, GREY_C); l2 = link(gate, serv, GREY_C); l3 = link(tok, lim, GREY_C)
        seq(self, "It runs the fraud and limits checks at the same time. Fraud is slow and shared, so each call needs "
                  "one of 20 permits.",
            ([FadeIn(lim), Create(l3), Create(l1), FadeIn(gate), FadeIn(gate_l)], 0.9),
            ([FadeIn(serv), FadeIn(serv_t), Create(l2), FadeIn(stat)], 0.7), 0.6,
            ([LaggedStart(*[FadeIn(p, scale=0.5) for p in permits], lag_ratio=0.08)], 1.6))

        # a normal day
        ring = Circle(radius=0.14, color=TEAL_M, stroke_width=3).move_to(tok.get_right())
        ldot = Dot(tok.get_right(), radius=0.09, color=TEAL_M)
        ok_l = T("limits: ok", 22, GREEN_M).move_to(TOK + DOWN * 1.15)
        ok_f = T("fraud: ok", 22, GREEN_M).move_to(TOK + DOWN * 1.55)
        p0 = permits[0]
        pool = frame_box(3.0, 1.1, BLUE_M).move_to(POOL)
        pool_t = VGroup(T("ledger pool", 26, BLUE_M), T("8 threads, 80 slots", 22, WHITE)).arrange(DOWN, buff=0.1)
        pool_t.move_to(POOL)
        full = T("full: a 503 at once", 22, RED_M).next_to(pool, DOWN, buff=0.2)
        appr = T("approved", 26, GREEN_M).next_to(pool, UP, buff=0.2)
        seq(self, "On a normal day, fraud answers in 20 milliseconds. The permit goes back, both checks pass, and the "
                  "transfer goes on to the ledger pool.",
            ([FadeIn(ring), FadeIn(ldot)], 0.3),
            ([ring.animate.move_to(gs[0]), ldot.animate.move_to(LIM + LEFT * 1.1), left.animate.set_value(296)], 0.8),
            ([ring.animate.move_to(ss[0]), p0.animate.move_to(ss[0]), ldot.animate.move_to(tok.get_right()),
              left.animate.set_value(290)], 0.8),
            ([FadeOut(ldot), FadeIn(ok_l)], 0.3),
            ([ring.animate.move_to(gs[0]), p0.animate.move_to(gs[0]), left.animate.set_value(284)], 0.7),
            ([ring.animate.move_to(tok.get_right()), FadeIn(ok_f), left.animate.set_value(280)], 0.6),
            ([FadeOut(ring), FadeIn(pool), FadeIn(pool_t), FadeOut(VGroup(bar, bar_bg, cd))], 0.6),
            ([tok.animate.scale(0.6).move_to(POOL).set_opacity(0), FadeOut(vt), FadeOut(ok_l), FadeOut(ok_f),
              FadeOut(l1), FadeOut(l3), FadeIn(appr)], 1.0))
        self.beat("That pool is a limit too: 8 threads and 80 slots, and a 503 when it's full.",
                  FadeIn(full, shift=UP * 0.1), Indicate(pool_t[1], color=BLUE_M), run_time=1.4)
        self.remove(tok)
        self.play(FadeOut(appr), run_time=0.3)

        # ---------------- an outage ----------------
        stat2 = T("2 s a call", 24, RED_M).move_to(stat)
        others = [permits[i] for i in range(20)]
        seq(self, "Now an outage. Every fraud call takes 2 seconds. Twenty calls hold all 20 permits.",
            ([Transform(stat, stat2), serv.animate.set_stroke(RED_M)], 0.6), 1.0,
            ([LaggedStart(*[p.animate.move_to(ss[i]) for i, p in enumerate(others)], lag_ratio=0.08)], 2.0))

        left.set_value(300)
        tok = token("40.00")
        ring = Circle(radius=0.14, color=TEAL_M, stroke_width=3).move_to(tok.get_right())
        ldot = Dot(tok.get_right(), radius=0.09, color=TEAL_M)
        wait_at = np.array([-3.35, 1.12, 0])
        seq(self, "A new request arrives, for 40.00. Its limits check passes. Its fraud call waits for a permit, but "
                  "only as long as its deadline allows.",
            ([FadeIn(tok), FadeIn(vt), FadeIn(bar_bg), FadeIn(bar), FadeIn(cd), Create(l1), Create(l3)], 0.6),
            ([FadeIn(ring), FadeIn(ldot)], 0.3),
            ([ldot.animate.move_to(LIM + LEFT * 1.1), ring.animate.move_to(wait_at), left.animate.set_value(290)], 0.8),
            ([ldot.animate.move_to(tok.get_right()), left.animate.set_value(282)], 0.6),
            ([FadeOut(ldot), FadeIn(ok_l)], 0.3),
            ([left.animate(rate_func=linear).set_value(230)], None))

        j = 7
        pj = permits[j]
        intr = T("interrupted", 22, RED_M).move_to(SERV + DOWN * 0.95)
        seq(self, "Another request runs out of time. It interrupts its own fraud call, and that call's finally block "
                  "hands the permit back. Ours takes it.",
            ([pj.animate.set_color(RED_M), FadeIn(intr), left.animate(rate_func=linear).set_value(220)], 0.8), 0.8,
            ([pj.animate.move_to(gs[j]).set_color(PURPLE_M), FadeOut(intr), left.animate(rate_func=linear).set_value(205)],
             1.0), 1.4,
            ([ring.animate.move_to(gs[j]), left.animate(rate_func=linear).set_value(195)], 0.6),
            ([ring.animate.move_to(ss[j]), pj.animate.move_to(ss[j]), left.animate(rate_func=linear).set_value(180)], 0.8))
        self.beat("Our clock keeps running. What happens at zero?", left.animate(rate_func=linear).set_value(25),
                  run_time=2.4)
        self.wait(1.2)
        intr2 = T("interrupted", 22, RED_M).move_to(SERV + DOWN * 0.95)
        seq(self, "The same thing. It interrupts its call, and the permit goes back.",
            ([left.animate(rate_func=linear).set_value(0)], 0.5),
            ([ring.animate.set_color(RED_M), FadeIn(intr2)], 0.5),
            ([pj.animate.move_to(gs[j]), FadeOut(ring), FadeOut(intr2)], 1.0))

        si = VGroup(T("up to 50.00: stand-in, accepted", 26, GOLD_M),
                    T("more than 50.00: a fast try again", 26, RED_M)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        si.move_to([-1.0, -2.45, 0])
        seq(self, "Then the stand-in rule decides. Up to 50.00 goes through without a fraud answer, so our 40.00 is "
                  "accepted. Larger amounts get a fast try again.",
            ([FadeIn(si[0], shift=UP * 0.1)], 0.6), 2.0,
            ([FadeOut(VGroup(bar, bar_bg, cd, vt, ok_l, l1, l3)), tok.animate.scale(0.6).move_to(POOL).set_opacity(0)],
             1.0), 0.6,
            ([FadeIn(si[1], shift=UP * 0.1)], 0.6))
        self.remove(tok)
        demo = VGroup(T("demo, outage: every reply within about 320 ms", 24, GREY_A),
                      T("fraud never sees more than 20 calls at once", 24, GREY_A),
                      T("stand-in: 290 of 1,200 in one run", 24, GREY_A)).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        demo.move_to([0, -2.55, 0])
        self.play(FadeOut(full), FadeOut(si), run_time=0.4)
        self.beat("In the lesson's demo, during the outage, every reply came within about 320 milliseconds, and fraud "
                  "never saw more than 20 calls at once.", FadeIn(demo, shift=UP * 0.1), run_time=1.2)
        self.wait(0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- the code ----------------
        jc = code(["// once per request",
                   "long deadline =",
                   "    System.nanoTime() + budgetNanos;",
                   "// the permit wait uses what is left",
                   "if (!inFlight.tryAcquire(",
                   "        waitNanos, NANOSECONDS))",
                   "    throw new TimeoutException();",
                   "try { return block.call(); }",
                   "finally { inFlight.release(); }"])
        kc = code(["// once per request",
                   "val deadline =",
                   "    System.nanoTime() + budgetNanos",
                   "// the permit wait uses what is left",
                   "if (!inFlight.tryAcquire(",
                   "        waitNanos, NANOSECONDS))",
                   "    throw TimeoutException()",
                   "try { return block() }",
                   "finally { inFlight.release() }"])
        for c in (jc, kc):
            c[0].set_color(GREY_B); c[3].set_color(GREY_B)
            c[1].set_color(YELLOW_M); c[2].set_color(YELLOW_M)
            c[4].set_color(PURPLE_M); c[5].set_color(PURPLE_M)
            c[8].set_color(PURPLE_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.5, 0])
        note = T("at the deadline: interrupt the call, then stand-in or try again", 24, GOLD_M).move_to([0, -2.5, 0])
        self.beat("In code, the deadline is computed once, and the permit wait uses what is left of it. Java and Kotlin "
                  "match.", FadeIn(cg, shift=UP * 0.2), FadeIn(note), run_time=1.4)
        self.wait(1.0)
        self.play(FadeOut(cg), FadeOut(note), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Threads are free, so every limit sits on a resource:", 30),
                      T("20 permits for fraud, 8 threads and 80 slots for the journal,", 30),
                      T("and one deadline per request.", 30)).arrange(DOWN, buff=0.18)
        rule.scale(min(1, 12 / rule.width)).move_to([0, 2.1, 0])
        self.beat("The rule. Threads are free, so every limit sits on a resource: 20 permits for fraud, 8 threads and "
                  "80 slots for the journal, and one deadline per request.", FadeIn(rule, shift=UP * 0.15), run_time=1.8)
        chk = VGroup(T("Drop the interrupt at the deadline.", 28),
                     T("During the outage, what happens to the 20 permits?", 28)).arrange(DOWN, buff=0.16)
        chk.scale(min(1, 12 / chk.width)).move_to([0, -0.1, 0])
        self.beat("Check yourself. Drop the interrupt at the deadline. During the outage, what happens to the 20 "
                  "permits?", FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = VGroup(T("Orphaned fraud calls keep them for the full 2 s, so new requests", 28, GOLD_M),
                     T("get no permit, even for a call that would succeed.", 28, GOLD_M)).arrange(DOWN, buff=0.16)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.9, 0])
        self.beat("Orphaned fraud calls keep them for the full 2 seconds, so new requests get no permit, even for a "
                  "call that would succeed.", FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
