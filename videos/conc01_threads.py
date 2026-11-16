from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds")]


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


def frame(name, color, local=None, w=2.1, size=24):
    """One stack frame: a call in progress, with an optional local variable."""
    h = 0.95 if local else 0.6 * size / 24
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dark(color), 1)
    t = M(name, size, WHITE)
    g = VGroup(r, t)
    if local:
        v = M(local, 22, GREY_A)
        VGroup(t, v).arrange(DOWN, buff=0.1).move_to(r)
        g.add(v)
    else:
        t.move_to(r)
    return g


def lanes(clock, segs, x0, k, h=0.5):
    """Coloured time slices on core lanes. segs = [(y, t0, t1, colour)], drawn up to the clock's time."""
    def draw():
        t = clock.get_value()
        g = VGroup()
        for (y, a, b, col) in segs:
            if t > a:
                e = min(t, b)
                r = Rectangle(width=max(0.002, (e - a) * k), height=h, stroke_width=0).set_fill(col, 0.85)
                r.move_to([x0 + a * k, y, 0], aligned_edge=LEFT)
                g.add(r)
        return g
    return always_redraw(draw)


class Conc01Threads(VoiceScene):
    """conc-01, section 0: a thread is one walker through your code with its own stack, inside a process
    whose heap every thread shares; cores run threads (taking turns is concurrency, running at the same
    instant is parallelism); start() makes a new thread, run() is a plain call on the current one."""

    def construct(self):
        self.title_card("Threads from zero", "one heap, many paths, a few cores")

        # ---------------- the walker: a page of code and a stack ----------------
        PX = -5.0
        page = RoundedRectangle(corner_radius=0.12, width=2.3, height=5.0, stroke_color=GREY_B, stroke_width=2.5)
        page.set_fill(BLACK, 1).move_to([PX, -0.55, 0])
        page_l = T("your code", 24, GREY_B).move_to([PX, 1.6, 0])
        BX = PX - 0.62                       # left end of every bar
        main_y = [0.85, 0.45, 0.05, -0.35]
        set_y = [-1.35, -1.75, -2.15]
        main_w = [1.3, 0.9, 1.45, 1.1]
        set_w = [1.2, 1.5, 0.8]
        ml = M("main()", 22, GREY_A).move_to([PX, 1.2, 0])
        sl = M("settle()", 22, GREY_A).move_to([PX, -0.85, 0])
        bars = VGroup(*[Line([BX, y, 0], [BX + w, y, 0], stroke_width=7, color=GREY_D)
                        for y, w in zip(main_y + set_y, main_w + set_w)])
        DX = BX - 0.27

        def at(y):
            return np.array([DX, y, 0])

        dot_a = Dot(radius=0.11, color=BLUE_M).move_to(at(main_y[0])).set_z_index(5)

        seq(self, "Picture your program as a page of code, and something that walks through it, one line at a time.",
            ([FadeIn(page), FadeIn(page_l), FadeIn(ml), FadeIn(sl), Create(bars)], 1.2),
            ([FadeIn(dot_a, scale=0.4)], 0.4), ([dot_a.animate.move_to(at(main_y[1]))], 0.6),
            ([dot_a.animate.move_to(at(main_y[2]))], 0.6))

        # stack of the first thread
        SA = -1.9
        STACK_Y0 = -2.45                     # centre of the bottom frame
        f_main = frame("main()", BLUE_M).move_to([SA, STACK_Y0, 0])
        st_a_l = T("its stack", 26, BLUE_M).move_to([SA, -3.05, 0])
        self.beat("It keeps its notes on a stack: one frame per call in progress, with its local variables.",
                  FadeIn(f_main, shift=DOWN * 0.3), FadeIn(st_a_l), run_time=1.2)

        def on_top(f, below):
            return f.next_to(below, UP, buff=0.12)

        f_set_a = on_top(frame("settle()", BLUE_M, "total = 0"), f_main)
        seq(self, "Step into a call, and a frame goes on top. Return, and it comes off.",
            ([dot_a.animate.move_to(at(set_y[0])), FadeIn(f_set_a, shift=DOWN * 0.3)], 0.8),
            ([dot_a.animate.move_to(at(set_y[1]))], 0.4), ([dot_a.animate.move_to(at(set_y[2]))], 0.4),
            ([dot_a.animate.move_to(at(main_y[3])), FadeOut(f_set_a, shift=UP * 0.3)], 0.8))
        name_a = T("thread: main", 30, BLUE_M).move_to([SA, -0.05, 0])
        self.beat("This walker is a thread. The JVM starts this one, called main.",
                  FadeIn(name_a, shift=UP * 0.15), Indicate(dot_a, color=WHITE, scale_factor=1.6), run_time=1.4)

        # ---------------- the process and its heap ----------------
        proc = RoundedRectangle(corner_radius=0.2, width=12.8, height=6.3, stroke_color=WHITE, stroke_width=2.5)
        proc.move_to([0, -0.2, 0])
        proc_l = T("process: one running JVM", 26, WHITE).move_to([3.4, 2.62, 0])
        self.play(FadeOut(name_a), run_time=0.4)
        self.beat("It runs inside a process, one running JVM, with memory of its own.",
                  Create(proc), FadeIn(proc_l), run_time=1.6)

        heap = RoundedRectangle(corner_radius=0.15, width=9.0, height=1.75, stroke_color=GOLD_M, stroke_width=3)
        heap.set_fill(dark(GOLD_M, 0.08), 1).move_to([1.35, 1.2, 0])
        heap_l = VGroup(T("heap", 30, GOLD_M), T("shared", 22, GREY_B)).arrange(DOWN, buff=0.08).move_to([-2.35, 1.2, 0])
        objs = [box(n, GOLD_M, w=2.0, h=0.72, size=26) for n in ("Payment", "HashMap", "Ledger")]
        for o, x in zip(objs, (0.0, 2.45, 4.75)):
            o.move_to([x, 1.2, 0])
        self.beat("Every object you create with new lives in one part of it: the heap.",
                  FadeIn(heap), FadeIn(heap_l), LaggedStart(*[FadeIn(o, scale=0.8) for o in objs], lag_ratio=0.25),
                  run_time=1.6)

        # second thread: its own place in the code, its own stack
        SB = 2.6
        dot_b = Dot(radius=0.11, color=TEAL_M).move_to(at(main_y[0])).set_z_index(5)
        f_run_b = frame("run()", TEAL_M).move_to([SB, STACK_Y0, 0])
        st_b_l = T("its stack", 26, TEAL_M).move_to([SB, -3.05, 0])
        name_b = T("thread: worker", 30, TEAL_M).move_to([SB, -0.05, 0])
        name_a = T("thread: main", 30, BLUE_M).move_to([SA, -0.05, 0])
        f_set_a = on_top(frame("settle()", BLUE_M, "total = 0"), f_main)
        f_set_b = on_top(frame("settle()", TEAL_M, "total = 0"), f_run_b)
        seq(self, "A second thread, a worker, walks the same code with its own stack. "
                  "Both call settle, and each one gets its own frame.",
            ([FadeIn(dot_b, scale=0.4), FadeIn(f_run_b, shift=DOWN * 0.3), FadeIn(st_b_l), FadeIn(name_b),
              FadeIn(name_a)], 1.2), 1.4,
            ([FadeOut(name_a), FadeOut(name_b)], 0.4),
            ([dot_a.animate.move_to(at(set_y[0])), dot_b.animate.move_to(at(main_y[2])),
              FadeIn(f_set_a, shift=DOWN * 0.3)], 0.8),
            ([dot_b.animate.move_to(at(set_y[1])), FadeIn(f_set_b, shift=DOWN * 0.3)], 0.8))

        pay = objs[0]
        ra = Arrow(f_set_a.get_top(), pay.get_bottom() + LEFT * 0.35, buff=0.1, stroke_width=3, color=BLUE_M,
                   max_tip_length_to_length_ratio=0.12)
        rb = Arrow(f_set_b.get_top(), pay.get_bottom() + RIGHT * 0.35, buff=0.1, stroke_width=3, color=TEAL_M,
                   max_tip_length_to_length_ratio=0.12)
        seq(self, "But both can reach the same Payment on the heap. That is how threads share data with no copying, "
                  "and how two of them can change one object at the same moment.",
            ([GrowArrow(ra), GrowArrow(rb)], 1.0), 3.2,
            ([pay[0].animate.set_stroke(RED_M), Flash(pay, color=RED_M, flash_radius=1.25)], 1.0))
        self.play(pay[0].animate.set_stroke(GOLD_M), run_time=0.3)

        tot_a = f_set_a[2]
        new_a = M("total = 3", 22, YELLOW_M).move_to(tot_a)
        self.beat("Main sets its local total to three. Does the worker's total change?",
                  Transform(tot_a, new_a), run_time=1.0)
        self.wait(1.4)
        ok = tick(True, 0.16).next_to(f_set_b, RIGHT, buff=0.15)
        self.beat("No. A local lives on its own thread's stack. Only the heap is shared.",
                  Indicate(f_set_b[2], color=TEAL_M, scale_factor=1.2), Create(ok),
                  Indicate(heap_l[0], color=WHITE, scale_factor=1.15), run_time=1.6)
        self.play(FadeOut(VGroup(page, page_l, ml, sl, bars, dot_a, dot_b, f_main, f_set_a, f_run_b, f_set_b,
                                 st_a_l, st_b_l, proc, proc_l, heap, heap_l, *objs, ra, rb, ok)), run_time=0.7)

        # ---------------- cores: taking turns vs at the same instant ----------------
        X0, K = -3.4, 0.95                    # lane start and units per time step
        LANE_W = 9.4
        Y1, Y2a, Y2b = 1.2, -1.05, -1.85

        def lane_box(y):
            return Rectangle(width=LANE_W, height=0.56, stroke_color=GREY_D, stroke_width=2).move_to(
                [X0 + LANE_W / 2, y, 0])

        lb1 = lane_box(Y1)
        lab1 = T("1 core", 28, WHITE).next_to(lb1, LEFT, buff=0.35)
        leg = VGroup(Dot(radius=0.1, color=BLUE_M), T("main", 26, BLUE_M), Dot(radius=0.1, color=TEAL_M).shift(RIGHT * 0.3),
                     T("worker", 26, TEAL_M)).arrange(RIGHT, buff=0.18).move_to([3.6, 2.7, 0])
        c1 = ValueTracker(0)
        sl_len, gap = 1.3, 0.18
        segs1, t = [], 0.0
        for i in range(6):
            segs1.append((Y1, t, t + sl_len, BLUE_M if i % 2 == 0 else TEAL_M))
            t += sl_len + gap
        top = lanes(c1, segs1, X0, K)
        self.add(top)
        seq(self, "A core of the CPU runs a thread, one thread at a time.",
            ([FadeIn(lb1), FadeIn(lab1), FadeIn(leg)], 1.0), ([c1.animate.set_value(sl_len)], 1.6))
        cs = VGroup(T("context switch", 24, GREY_B)).move_to([X0 + (sl_len + gap / 2) * K, Y1 - 0.75, 0])
        cs_a = Arrow(cs.get_top(), [X0 + (sl_len + gap / 2) * K, Y1 - 0.3, 0], buff=0.05, stroke_width=2.5,
                     color=GREY_B, max_tip_length_to_length_ratio=0.25)
        seq(self, "On one core, the operating system lets main run for a short slice, "
                  "saves its registers, and switches to the worker. That is a context switch, "
                  "thousands of times a second.",
            2.6, ([c1.animate.set_value(sl_len + gap + 0.4)], 1.0), ([FadeIn(cs), GrowArrow(cs_a)], 0.6),
            ([c1.animate.set_value(t)], 4.0))
        conc = T("concurrency: both in progress, taking turns", 28, WHITE).move_to([0.6, 2.05, 0])
        self.beat("Both are in progress, taking turns. That is concurrency.",
                  FadeIn(conc, shift=DOWN * 0.15), run_time=1.0)

        lb2a, lb2b = lane_box(Y2a), lane_box(Y2b)
        lab2 = VGroup(T("core 1", 26), T("core 2", 26))
        lab2[0].next_to(lb2a, LEFT, buff=0.35)
        lab2[1].next_to(lb2b, LEFT, buff=0.35)
        c2 = ValueTracker(0)
        bot = lanes(c2, [(Y2a, 0, t, BLUE_M), (Y2b, 0, t, TEAL_M)], X0, K)
        par = T("parallelism: both running at the same instant", 28, WHITE).move_to([0.6, -0.2, 0])
        self.add(bot)
        seq(self, "Two cores run both at the same instant. That is parallelism.",
            ([FadeIn(lb2a), FadeIn(lb2b), FadeIn(lab2)], 0.5), ([c2.animate.set_value(t)], 2.0),
            ([FadeIn(par, shift=DOWN * 0.15)], 0.6))
        top.clear_updaters(); bot.clear_updaters()
        self.play(FadeOut(VGroup(top, bot, lb1, lab1, lb2a, lb2b, lab2, cs, cs_a, conc, par, leg)), run_time=0.6)

        # ---------------- the wall at the core count ----------------
        head = T("400 million additions on a 4-core machine", 30).move_to([0, 2.3, 0])
        rows = [(1, 510), (2, 257), (4, 121), (8, 125)]
        BX0, BK = -2.6, 7.0 / 510
        bars2, labs, vals = [], [], []
        for j, (n, ms) in enumerate(rows):
            y = 1.1 - j * 1.0
            col = GOLD_M if n == 8 else BLUE_M
            b = Rectangle(width=ms * BK, height=0.55, stroke_width=0).set_fill(col, 0.85).move_to([BX0, y, 0], aligned_edge=LEFT)
            labs.append(T(f"{n} thread" + ("s" if n > 1 else ""), 28).move_to([BX0 - 0.35, y, 0], aligned_edge=RIGHT))
            vals.append(T(f"{ms} ms", 28, col).next_to(b, RIGHT, buff=0.2))
            bars2.append(b)
        seq(self, "So on four cores, is a busy job faster on eight threads than on four?",
            ([FadeIn(head)], 0.8), ([FadeIn(labs[0]), GrowFromEdge(bars2[0], LEFT), FadeIn(vals[0])], 0.6),
            ([FadeIn(labs[1]), GrowFromEdge(bars2[1], LEFT), FadeIn(vals[1])], 0.6),
            ([FadeIn(labs[2]), GrowFromEdge(bars2[2], LEFT), FadeIn(vals[2])], 0.6))
        self.wait(1.3)
        seq(self, "No. In the lesson's demo, four threads took 121 milliseconds, and eight took 125. "
                  "Once every core is busy, extra threads only take turns.",
            1.8, ([FadeIn(labs[3]), GrowFromEdge(bars2[3], LEFT), FadeIn(vals[3])], 0.9))
        self.play(FadeOut(VGroup(head, *bars2, *labs, *vals)), run_time=0.6)

        # ---------------- start() vs run() ----------------
        div = DashedLine([0, 2.4, 0], [0, -2.9, 0], dash_length=0.1, stroke_width=2, color=GREY_D)
        h_run = M("t.run()", 40, BLUE_M).move_to([-3.5, 2.45, 0])
        h_sta = M("t.start()", 40, TEAL_M).move_to([3.5, 2.45, 0])
        LX, RMX, RNX = -3.5, 1.95, 5.05
        FY = -1.2
        fm_l = frame("main()", BLUE_M, w=2.7, size=30).move_to([LX, FY, 0])
        fm_r = frame("main()", BLUE_M, w=2.7, size=30).move_to([RMX, FY, 0])
        sl_l = T("main's stack", 28, BLUE_M).move_to([LX, FY - 0.85, 0])
        sl_r = T("main's stack", 28, BLUE_M).move_to([RMX, FY - 0.85, 0])
        fr_l = on_top(frame("task.run()", BLUE_M, w=2.7, size=30), fm_l)
        seq(self, "Calling run on a thread is a plain method call. "
                  "Main steps into the task itself, on its own stack.",
            ([FadeIn(fm_l), FadeIn(sl_l), FadeIn(h_run)], 0.8), 1.0, ([FadeIn(fr_l, shift=DOWN * 0.3)], 0.8))
        v_l = VGroup(T("one thread: main runs the task", 30, BLUE_M),
                     T("and waits until it returns", 30, BLUE_M)).arrange(DOWN, buff=0.14).move_to([LX, 1.2, 0])
        self.beat("No new thread exists, nothing fails, and the job is just as slow.",
                  FadeIn(v_l, shift=UP * 0.15), run_time=1.0)

        fr_r = frame("task.run()", TEAL_M, w=2.7, size=30).move_to([RNX, FY, 0])
        sn = T("settlement-1", 28, TEAL_M).move_to([RNX, FY - 0.85, 0])
        seq(self, "With start, the JVM asks the operating system for a new thread, with a new stack.",
            ([Create(div), FadeIn(h_sta), FadeIn(fm_r), FadeIn(sl_r)], 0.8), 1.0,
            ([FadeIn(sn), FadeIn(fr_r, scale=0.8)], 0.8))
        v_r = VGroup(T("two threads: the task runs", 30, TEAL_M),
                     T("while main goes on", 30, TEAL_M)).arrange(DOWN, buff=0.14).move_to([3.5, 1.2, 0])
        self.beat("That thread calls run, and main goes on at once.",
                  Indicate(fr_r[1], color=TEAL_M, scale_factor=1.1), Indicate(fm_r[1], color=BLUE_M, scale_factor=1.1),
                  FadeIn(v_r, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(div, h_run, h_sta, fm_l, fm_r, sl_l, sl_r, fr_l, v_l, fr_r, sn, v_r)), run_time=0.7)

        # ---------------- rule and check ----------------
        rule = T("Every thread has its own stack and shares one heap.", 34).move_to([0, 2.3, 0])
        rule2 = T("Only start() makes a new thread.", 34, TEAL_M).move_to([0, 1.6, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule.width))
        self.beat("The rule. Every thread has its own stack, they all share the heap, and only start makes a new thread.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A report is split into four slices, and you call", 28).move_to([0, 0.15, 0])
        chk2 = M("new Thread(slice).run()", 28, BLUE_M).move_to([0, -0.45, 0])
        chk3 = T("for each one, on a 4-core machine. How much faster is it?", 28).move_to([0, -1.05, 0])
        VGroup(chk, chk2, chk3).scale(min(1, 12 / chk3.width))
        self.beat("Check yourself. You split a report into four slices, and call run on a new thread for each. "
                  "On four cores, how much faster is it?", FadeIn(chk), FadeIn(chk2),
                  FadeIn(chk3), run_time=1.4)
        self.wait(2.5)
        ans = T("Not faster at all: run() is a plain call, so main does the slices one by one.", 28, TEAL_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -2.2, 0])
        self.beat("Not faster. Main runs the four slices itself, one after another.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.5)
