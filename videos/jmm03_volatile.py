from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"3\.7 million", "three point seven million"),
    (r"\bAtomicInteger\.incrementAndGet\b", "atomic integer dot increment and get"),
    (r"\bAtomicInteger\b", "atomic integer"),
    (r"max = Math\.max\(max, x\)", "max equals math dot max of max and x"),
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


T1C, T2C, VOL = BLUE_M, TEAL_M, GOLD_M


def tpanel(name, color, pos):
    r = RoundedRectangle(corner_radius=0.15, width=3.9, height=2.9, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.1), opacity=1).move_to(pos)
    head = T(name, 30, color).move_to(r.get_top() + DOWN * 0.42)
    return VGroup(r, head)


def regbox(color):
    r = RoundedRectangle(corner_radius=0.1, width=1.7, height=0.75, stroke_color=color, stroke_width=2.5)
    r.set_fill(BLACK, opacity=1)
    return r


def vchip(text="volatile", size=24):
    t = M(text, size, BLACK)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.5, stroke_width=0).set_fill(VOL, 1)
    return VGroup(r, t.move_to(r))


class Jmm03Volatile(VoiceScene):
    """jmm-03, section 1: what volatile gives (a fresh read every time, a write that carries the writes before it)
    and what it does not (retries++ stays three steps: two fresh reads of 41, two visible writes of 42, one update
    lost); incrementAndGet as one atomic step; volatile, atomic or lock; the rule and a check question."""

    def construct(self):
        self.title_card("volatile", "fresh and ordered, but not one step")

        # ---- the problem: a volatile counter that loses retries ----
        board = RoundedRectangle(corner_radius=0.15, width=3.4, height=1.15, stroke_color=WHITE, stroke_width=3)
        board.set_fill(BLACK, opacity=1).move_to([0, 2.2, 0])
        b_lab = T("retries, in memory", 24, GREY_B).next_to(board, UP, buff=0.2)
        val = M("0", 44).move_to(board)
        tag = vchip().next_to(board, LEFT, buff=0.3)

        ths = VGroup(*[box(f"thread {i}", GREY_B, w=2.2, h=0.75, size=26) for i in range(1, 5)]).arrange(RIGHT, buff=0.55)
        ths.move_to([0, -0.2, 0])
        ups = VGroup(*[Arrow(t.get_top(), board.get_bottom() + RIGHT * (t.get_x() * 0.25), buff=0.12, stroke_width=3,
                             color=GREY_B, max_tip_length_to_length_ratio=0.12) for t in ths])
        ups_l = T("each does retries++, a million times", 26, GREY_A).next_to(ths, DOWN, buff=0.4)
        self.beat("This service counts retries to the card issuer. The counter field is volatile, so it looks safe.",
                  FadeIn(VGroup(board, b_lab, val)), FadeIn(tag, shift=RIGHT * 0.2), run_time=1.4)
        self.beat("Four threads each add one, a million times. What total do you expect?",
                  LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in ths], lag_ratio=0.2), Create(ups), FadeIn(ups_l),
                  run_time=2.2, after=1.6)
        exp = VGroup(T("expected", 28, GREY_B), M("4,000,000", 30)).arrange(RIGHT, buff=0.4)
        got = VGroup(T("one run", 28, GREY_B), M("3,681,731", 30, RED_M)).arrange(RIGHT, buff=0.4)
        res = VGroup(exp, got).arrange(DOWN, aligned_edge=RIGHT, buff=0.3).move_to([0, -2.75, 0])
        counter = ValueTracker(0)
        val.add_updater(lambda m: m.become(M(f"{int(counter.get_value()):,}", 40, RED_M if counter.get_value() > 3.6e6 else WHITE).move_to(board)))
        seq(self, "One measured run ended near 3.7 million. Over three hundred thousand retries vanished, and nothing threw.",
            ([FadeIn(exp)], 0.5), ([counter.animate.set_value(3681731)], 2.4), ([FadeIn(got, shift=UP * 0.1)], 0.6))
        val.clear_updaters()
        self.beat("First, take volatile away for a moment.",
                  FadeOut(VGroup(ths, ups, ups_l, res)), FadeOut(tag, shift=LEFT * 0.2), run_time=1.0)

        # ---- plain field: a copy in a register ----
        p1 = tpanel("Thread 1", T1C, [-4.45, -1.05, 0])
        p2 = tpanel("Thread 2", T2C, [4.45, -1.05, 0])
        r1, r2 = regbox(T1C).move_to(p1[0].get_center() + DOWN * 0.15), regbox(T2C).move_to(p2[0].get_center() + DOWN * 0.15)
        rl1 = T("register", 22, GREY_B).next_to(r1, DOWN, buff=0.15)
        rl2 = T("register", 22, GREY_B).next_to(r2, DOWN, buff=0.15)
        rv1, rv2 = M("41", 30).move_to(r1).set_opacity(0), M("41", 30).move_to(r2).set_opacity(0)
        rd = edge_arrow(board, p2[0], GREY_B)
        wr = edge_arrow(p1[0], board, T1C)

        def set_val(v, color=WHITE):
            return Transform(val, M(str(v), 44, color).move_to(board))

        def set_reg(rv, reg, v, color=WHITE):
            return Transform(rv, M(str(v), 30, color).move_to(reg))

        def fly(text, arr, color, extra=None, rt=0.9):
            tok = M(text, 30, color).move_to(arr.get_start()).set_z_index(6)
            grp = VGroup(tok) if extra is None else VGroup(tok, extra.next_to(tok, DOWN, buff=0.08))
            self.add(grp)
            self.play(grp.animate.move_to(arr.get_end()), run_time=rt)
            return grp

        self.play(Transform(val, M("41", 44).move_to(board)), FadeIn(p1), FadeIn(p2), FadeIn(VGroup(r2, rl2)),
                  run_time=0.8)
        self.add(rv2)
        loop = Arc(radius=0.3, start_angle=PI / 2, angle=-1.6 * PI, color=T2C, stroke_width=3).add_tip(tip_length=0.14)
        loop.next_to(r2, RIGHT, buff=0.2)

        def speak(text):
            path, dur = voice(text)
            self._cue(text, dur)
            self.add_sound(path)
            return dur, self.renderer.time

        def finish(dur, t0, after=0.25):
            rest = dur - (self.renderer.time - t0)
            if rest > 0.02:
                self.wait(rest)
            if after:
                self.wait(after)

        dur, t0 = speak("With a plain field, the JIT may keep a copy in a register, "
                        "and thread 2 reads that copy again and again.")
        self.play(GrowArrow(rd), run_time=0.6)
        g = fly("41", rd, GREY_A)
        self.play(FadeOut(g), set_reg(rv2, r2, "41"), run_time=0.4)
        self.wait(0.6)
        self.play(Create(loop), run_time=0.6)
        self.play(Rotate(loop, -2 * PI, about_point=loop.get_center()),
                  run_time=max(0.5, dur - (self.renderer.time - t0) - 0.1))
        finish(dur, t0)

        dur, t0 = speak("Thread 1 writes 42. Thread 2 may never see it.")
        self.play(GrowArrow(wr), run_time=0.5)
        g = fly("42", wr, T1C, rt=0.8)
        self.play(FadeOut(g), set_val(42, T1C), run_time=0.4)
        self.play(Rotate(loop, -2 * PI, about_point=loop.get_center()), r2.animate.set_stroke(RED_M),
                  rv2.animate.set_color(RED_M), run_time=max(0.6, dur - (self.renderer.time - t0) - 0.1))
        finish(dur, t0, after=0.5)

        # ---- volatile: every read goes to the field; the write carries what came before ----
        dur, t0 = speak("Put volatile back, and replay. Every read now goes back to the field, "
                        "so thread 2's next read sees 42.")
        self.play(FadeIn(tag, shift=RIGHT * 0.2), FadeOut(loop), set_val(41), r2.animate.set_stroke(T2C),
                  set_reg(rv2, r2, "41"), run_time=0.9)
        self.wait(0.5)
        ride_t = T("earlier writes", 20)
        ride = VGroup(RoundedRectangle(corner_radius=0.08, width=ride_t.width + 0.26, height=0.4, stroke_color=GREY_B,
                                       stroke_width=2).set_fill(interpolate_color(ManimColor("#000000"), ManimColor(GREY_B), 0.25), 1),
                      ride_t)
        g = fly("42", wr, T1C, extra=ride, rt=1.1)
        self.play(set_val(42, T1C), g.animate.next_to(board, DOWN, buff=0.12), run_time=0.5)
        g2 = g.copy()
        self.add(g2)
        self.play(g2.animate.move_to(rd.get_end() + UP * 0.2), run_time=1.0)
        self.play(FadeOut(g2[0]), set_reg(rv2, r2, "42", T2C), g2[1].animate.next_to(r2, UP, buff=0.1), run_time=0.5)
        finish(dur, t0)

        dur, t0 = speak("And the write carries what came before it. Plain writes thread 1 made before setting 42 "
                        "are visible to whoever reads 42.")
        self.wait(1.4)
        self.play(Indicate(g[1], color=WHITE, scale_factor=1.15), run_time=0.9)
        self.wait(0.8)
        self.play(Indicate(g2[1], color=WHITE, scale_factor=1.15), run_time=0.9)
        finish(dur, t0)
        self.play(FadeOut(VGroup(g, g2[1], rd, wr, r2, rl2, rv2)), set_val(41), run_time=0.7)

        # ---- the race: retries++ is three steps ----
        def row(p, k, text, color=WHITE):
            m = M(text, 26, color)
            return m.move_to([0, p[0].get_top()[1] - 1.05 - 0.55 * k, 0]).set_x(p[0].get_left()[0] + 0.5, LEFT)

        def ok(m, text):
            c = VGroup(tick(True, 0.13), T(text, 20, GREEN_M)).arrange(RIGHT, buff=0.1)
            return c.next_to(m, RIGHT, buff=0.25)

        steps = VGroup(*[M(s, 30) for s in ("read", "add one", "write")]).arrange(RIGHT, buff=0.9).move_to([0, 0.35, 0])
        seq(self, "So the field is always fresh. Now both threads run retries++. That is three steps: read, add one, write.",
            2.6, ([LaggedStart(*[FadeIn(s, shift=UP * 0.15) for s in steps], lag_ratio=0.5)], 1.6))
        self.play(steps.animate.scale(0.8).move_to([0, 0.05, 0]).set_color(GREY_B), run_time=0.5)

        rd1, rd2 = edge_arrow(board, p1[0], GREY_B), edge_arrow(board, p2[0], GREY_B)
        wr1, wr2 = edge_arrow(p1[0], board, T1C).shift(UP * 0.25 + RIGHT * 0.1), edge_arrow(p2[0], board, T2C).shift(UP * 0.25 + LEFT * 0.1)
        a1, a2 = row(p1, 0, "read 41"), row(p2, 0, "read 41")
        b1, b2 = row(p1, 1, "add one: 42"), row(p2, 1, "add one: 42")
        c1, c2 = row(p1, 2, "write 42"), row(p2, 2, "write 42")
        ok_a1, ok_a2 = ok(a1, "fresh"), ok(a2, "fresh")
        ok_c1, ok_c2 = ok(c1, "visible"), ok(c2, "visible")

        def readv(arr, rowm, okm, color):
            def f():
                g = M("41", 30, GREY_A).move_to(arr.get_start()).set_z_index(6)
                self.add(g)
                return [Succession(g.animate(run_time=0.8).move_to(arr.get_end()), FadeOut(g, run_time=0.2)),
                        Succession(Wait(0.6), FadeIn(rowm), FadeIn(okm))]
            return f

        seq(self, "Thread 1 reads 41. A fresh volatile read.",
            ([GrowArrow(rd1)], 0.5), (readv(rd1, a1, ok_a1, T1C), 1.0))
        seq(self, "Thread 2 reads too. Also fresh, also 41.",
            ([GrowArrow(rd2)], 0.5), (readv(rd2, a2, ok_a2, T2C), 1.0))
        self.beat("Both add one. Both hold 42.", FadeIn(b1, shift=RIGHT * 0.1), FadeIn(b2, shift=RIGHT * 0.1), run_time=0.9)

        def writev(arr, rowm, okm, color, v):
            def f():
                g = M("42", 30, color).move_to(arr.get_start()).set_z_index(6)
                self.add(g)
                return [FadeIn(rowm), FadeIn(okm), Succession(g.animate(run_time=0.8).move_to(arr.get_end()), FadeOut(g, run_time=0.2))]
            return f

        seq(self, "Thread 1 writes 42, visible at once. Now thread 2 writes. What does the field hold?",
            ([GrowArrow(wr1)], 0.4), (writev(wr1, c1, ok_c1, T1C, 42), 1.0), ([set_val(42, T1C)], 0.4), 1.2,
            ([GrowArrow(wr2)], 0.4), after=1.6)
        lost = T("two increments, one lost", 30, RED_M).move_to([0, -3.15, 0])
        seq(self, "42. Two increments, and one is lost.",
            (writev(wr2, c2, ok_c2, T2C, 42), 1.0), ([set_val(42, RED_M), Flash(board, color=RED_M, flash_radius=1.9)], 0.6),
            ([FadeIn(lost, shift=UP * 0.15)], 0.6))
        gap = Brace(VGroup(a2, c2), LEFT, color=RED_M, buff=0.12)
        gap_t = T("the gap", 26, RED_M).next_to(gap, LEFT, buff=0.4)
        seq(self, "Every access was a correct volatile access. volatile made each one visible, "
                  "and did nothing about the gap between them.",
            ([Indicate(VGroup(ok_a1, ok_a2, ok_c1, ok_c2), color=GREEN_M, scale_factor=1.2)], 1.2), 1.6,
            ([GrowFromCenter(gap), FadeIn(gap_t)], 0.8))

        # ---- the fix: one atomic step ----
        self.play(FadeOut(VGroup(a1, a2, b1, b2, c1, c2, ok_a1, ok_a2, ok_c1, ok_c2, gap, gap_t, lost, rd1, rd2, wr1, wr2, steps)),
                  FadeOut(tag), set_val(41), run_time=0.8)
        f1 = VGroup(M("incrementAndGet()", 24, GREEN_M), T("41 to 42, one step", 24)).arrange(DOWN, buff=0.18)
        f2 = VGroup(M("incrementAndGet()", 24, GREEN_M), T("42 to 43, one step", 24)).arrange(DOWN, buff=0.18)
        f1.move_to(p1[0].get_center() + DOWN * 0.25)
        f2.move_to(p2[0].get_center() + DOWN * 0.25)
        atom = Text("AtomicInteger", font=MONO, font_size=26, color=GREEN_M).next_to(board, LEFT, buff=0.3)

        def one_step(p, f, v, color):
            def go():
                pa = board.get_bottom() + (LEFT if p is p1 else RIGHT) * 0.6
                pb = p[0].get_top() + DOWN * 0.05 + (RIGHT if p is p1 else LEFT) * 0.6
                loop_path = VMobject().set_points_smoothly([pa, (pa + pb) / 2 + (LEFT if p is p1 else RIGHT) * 0.3, pb,
                                                            (pa + pb) / 2 + (RIGHT if p is p1 else LEFT) * 0.3, pa])
                d = Dot(radius=0.11, color=color).move_to(pa)
                self.add(d)
                return [FadeIn(f), MoveAlongPath(d, loop_path, rate_func=smooth),
                        board.animate.set_stroke(color), Succession(Wait(1.0), FadeOut(d, run_time=0.2))]
            return go

        seq(self, "The fix is one step that reads and writes together. AtomicInteger.incrementAndGet is that step.",
            ([FadeIn(atom, shift=RIGHT * 0.2)], 0.7), 1.6, (one_step(p1, f1, 42, T1C), 1.2), ([set_val(42, T1C)], 0.4))
        seq(self, "Thread 2 goes before it or after it, never inside. The count ends at 43.",
            (one_step(p2, f2, 43, T2C), 1.2), ([set_val(43, GREEN_M), board.animate.set_stroke(GREEN_M)], 0.5),
            ([Indicate(val, color=GREEN_M, scale_factor=1.2)], 0.8))
        self.play(FadeOut(VGroup(board, b_lab, val, atom, p1, p2, f1, f2)), run_time=0.8)

        # ---- which tool ----
        title = T("Which tool?", 40).to_edge(UP, buff=0.7)

        def trow(shape, eg, tool, color):
            left = VGroup(T(shape, 28), T(eg, 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            c = chip(tool, color, size=26, mono=True)
            return VGroup(left, c)

        rows = [trow("one writer, readers want the latest", "a shutdown flag, a heartbeat time", "volatile", VOL),
                trow("many writers, one variable", "a retry counter, a running total", "AtomicInteger, LongAdder", GREEN_M),
                trow("two or more fields under one rule", "status and captured amount", "a lock", PURPLE_M)]
        for i, r in enumerate(rows):
            r[0].move_to([-6.0, 1.45 - 1.45 * i, 0], aligned_edge=LEFT)
            r[1].move_to([1.4, r[0].get_center()[1], 0], aligned_edge=LEFT)
        ax = max(r[0].get_right()[0] for r in rows) + 0.25
        arrs = VGroup(*[Arrow(np.array([ax, r[1].get_center()[1], 0]), r[1].get_left() + LEFT * 0.08, buff=0, stroke_width=3,
                              color=GREY_B, max_tip_length_to_length_ratio=0.2) for r in rows])
        seq(self, "So which tool? One writer, and readers want the latest value: volatile is enough, like a shutdown flag.",
            ([Write(title)], 0.8), 0.6, ([FadeIn(rows[0][0]), GrowArrow(arrs[0]), FadeIn(rows[0][1])], 1.0))
        seq(self, "Many writers updating one variable from its old value: an atomic. Several fields under one rule: a lock.",
            ([FadeIn(rows[1][0]), GrowArrow(arrs[1]), FadeIn(rows[1][1])], 1.0), 1.6,
            ([FadeIn(rows[2][0]), GrowArrow(arrs[2]), FadeIn(rows[2][1])], 1.0))
        self.play(FadeOut(VGroup(title, *rows, arrs)), run_time=0.7)

        # ---- code ----
        title = T("One step, not three", 40).to_edge(UP, buff=0.7)
        jc = code(["private final AtomicInteger retries = new AtomicInteger();",
                   "retries.incrementAndGet();   // one atomic step"], 26)
        kc = code(["private val retries = AtomicInteger()",
                   "retries.incrementAndGet()    // one atomic step"], 26)
        for b in (jc, kc):
            b[1][:25].set_color(GREEN_M)
        cols = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        cols.scale(min(1, 12 / cols.width)).next_to(title, DOWN, buff=0.6)
        self.beat("In code, that is an AtomicInteger, in Java and in Kotlin.",
                  Write(title), FadeIn(cols, shift=UP * 0.2), run_time=1.6)
        rule = T("volatile: each access fresh and ordered, never two accesses as one step", 26, VOL)
        rule.scale(min(1, 12 / rule.width)).next_to(cols, DOWN, buff=0.7)
        self.beat("The rule: volatile makes each read and write visible and ordered. It never joins them into one step.",
                  FadeIn(rule, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(title, cols, rule)), run_time=0.7)

        # ---- check question ----
        q = M("max = Math.max(max, x);", 36).move_to(UP * 0.6)
        qv = VGroup(vchip(), M("int max;", 30)).arrange(RIGHT, buff=0.3).next_to(q, UP, buff=0.6)
        qn = T("many threads run this", 26, GREY_B).next_to(q, DOWN, buff=0.45)
        self.beat("Quick check. Many threads run max = Math.max(max, x) on a volatile field. Is that safe?",
                  FadeIn(qv), FadeIn(q, shift=UP * 0.15), FadeIn(qn), run_time=1.2, after=2.2)
        rd_u = Underline(q[4:19], color=GREY_A, buff=0.1)
        wr_u = Underline(q[0:3], color=RED_M, buff=0.1)
        ans = T("reads, decides, then writes: the same gap", 28, RED_M).next_to(qn, DOWN, buff=0.45)
        seq(self, "No. It reads, decides, then writes, with the same gap. Use an atomic, or a lock.",
            ([Create(rd_u)], 0.5), ([Create(wr_u)], 0.5), ([FadeIn(ans, shift=UP * 0.1)], 0.7))
        self.wait(0.8)
