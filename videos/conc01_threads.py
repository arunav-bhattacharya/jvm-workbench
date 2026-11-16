from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds")]


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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def frame(name, color, local=None, w=2.1):
    """One stack frame: a call in progress, with an optional local variable."""
    h = 0.95 if local else 0.6
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dark(color), 1)
    t = M(name, 24, WHITE)
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

        self.beat("Picture your program as a page of code.",
                  FadeIn(page), FadeIn(page_l), FadeIn(ml), FadeIn(sl), Create(bars), run_time=1.4)
        seq(self, "Something has to walk through it, one line after another.",
            ([FadeIn(dot_a, scale=0.4)], 0.4), ([dot_a.animate.move_to(at(main_y[1]))], 0.6),
            ([dot_a.animate.move_to(at(main_y[2]))], 0.6))

        # stack of the first thread
        SA = -1.9
        STACK_Y0 = -2.45                     # centre of the bottom frame
        f_main = frame("main()", BLUE_M).move_to([SA, STACK_Y0, 0])
        st_a_l = T("its stack", 26, BLUE_M).move_to([SA, -3.05, 0])
        self.beat("It keeps its own notes on a stack. Every call in progress gets a frame there, "
                  "with that call's local variables.",
                  FadeIn(f_main, shift=DOWN * 0.3), FadeIn(st_a_l), run_time=1.2)

        def on_top(f, below):
            return f.next_to(below, UP, buff=0.12)

        f_set_a = on_top(frame("settle()", BLUE_M, "total = 0"), f_main)
        seq(self, "Step into a call, and a frame goes on top. When the call returns, its frame comes off.",
            ([dot_a.animate.move_to(at(set_y[0])), FadeIn(f_set_a, shift=DOWN * 0.3)], 0.9),
            ([dot_a.animate.move_to(at(set_y[1]))], 0.5), ([dot_a.animate.move_to(at(set_y[2]))], 0.5),
            ([dot_a.animate.move_to(at(main_y[3])), FadeOut(f_set_a, shift=UP * 0.3)], 0.9))
        name_a = T("thread: main", 30, BLUE_M).move_to([SA, -0.05, 0])
        self.beat("This walker, with its place in the code and its own stack, is a thread. "
                  "The JVM starts this one for you. It is called main.",
                  FadeIn(name_a, shift=UP * 0.15), Indicate(dot_a, color=WHITE, scale_factor=1.6), run_time=1.6)

        # ---------------- the process and its heap ----------------
        proc = RoundedRectangle(corner_radius=0.2, width=12.8, height=6.3, stroke_color=WHITE, stroke_width=2.5)
        proc.move_to([0, -0.2, 0])
        proc_l = T("process: one running JVM", 26, WHITE).move_to([3.4, 2.62, 0])
        self.play(FadeOut(name_a), run_time=0.4)
        self.beat("It runs inside a process. A process is a running program with its own memory, like one JVM. "
                  "No other process can read that memory.",
                  Create(proc), FadeIn(proc_l), run_time=1.6)

        heap = RoundedRectangle(corner_radius=0.15, width=9.0, height=1.75, stroke_color=GOLD_M, stroke_width=3)
        heap.set_fill(dark(GOLD_M, 0.08), 1).move_to([1.35, 1.2, 0])
        heap_l = VGroup(T("heap", 30, GOLD_M), T("shared", 22, GREY_B)).arrange(DOWN, buff=0.08).move_to([-2.35, 1.2, 0])
        objs = [box(n, GOLD_M, w=2.0, h=0.72, size=26) for n in ("Payment", "HashMap", "Ledger")]
        for o, x in zip(objs, (0.0, 2.45, 4.75)):
            o.move_to([x, 1.2, 0])
        self.beat("Objects you create with new, and static fields, live in one part of that memory: the heap.",
                  FadeIn(heap), FadeIn(heap_l), LaggedStart(*[FadeIn(o, scale=0.8) for o in objs], lag_ratio=0.25),
                  run_time=1.8)

        # second thread: its own place in the code, its own stack
        SB = 2.6
        dot_b = Dot(radius=0.11, color=TEAL_M).move_to(at(main_y[0])).set_z_index(5)
        f_run_b = frame("run()", TEAL_M).move_to([SB, STACK_Y0, 0])
        st_b_l = T("its stack", 26, TEAL_M).move_to([SB, -3.05, 0])
        name_b = T("thread: worker", 30, TEAL_M).move_to([SB, -0.05, 0])
        name_a2 = T("thread: main", 30, BLUE_M).move_to([SA, -0.05, 0])
        self.beat("Now start a second thread, a worker. It gets its own place in the code and its own stack.",
                  FadeIn(dot_b, scale=0.4), FadeIn(f_run_b, shift=DOWN * 0.3), FadeIn(st_b_l), FadeIn(name_b),
                  FadeIn(name_a2), run_time=1.4)
        name_a, name_b_ = name_a2, name_b

        # both walk into settle(), each pushes its own frame with its own local
        f_set_a = on_top(frame("settle()", BLUE_M, "total = 0"), f_main)
        f_set_b = on_top(frame("settle()", TEAL_M, "total = 0"), f_run_b)
        self.play(FadeOut(name_a), FadeOut(name_b), run_time=0.4)
        seq(self, "Both threads call the same method. Each one gets its own frame, on its own stack.",
            ([dot_a.animate.move_to(at(set_y[0])), dot_b.animate.move_to(at(main_y[2])),
              FadeIn(f_set_a, shift=DOWN * 0.3)], 0.9),
            ([dot_b.animate.move_to(at(set_y[1])), FadeIn(f_set_b, shift=DOWN * 0.3)], 0.9))

        pay = objs[0]
        ra = Arrow(f_set_a.get_top(), pay.get_bottom() + LEFT * 0.35, buff=0.1, stroke_width=3, color=BLUE_M,
                   max_tip_length_to_length_ratio=0.12)
        rb = Arrow(f_set_b.get_top(), pay.get_bottom() + RIGHT * 0.35, buff=0.1, stroke_width=3, color=TEAL_M,
                   max_tip_length_to_length_ratio=0.12)
        self.beat("But they share the heap. Both can reach the same Payment object.",
                  GrowArrow(ra), GrowArrow(rb), run_time=1.2)
        self.beat("That is what makes threads useful. One thread puts a payment in a map, and another reads it, "
                  "with no copying.", Indicate(objs[1][1], color=WHITE, scale_factor=1.15), run_time=1.2)
        self.beat("It is also what makes them dangerous. Two threads can change the same object at the same moment.",
                  pay[0].animate.set_stroke(RED_M), Flash(pay, color=RED_M, flash_radius=1.25), run_time=1.2)
        self.play(pay[0].animate.set_stroke(GOLD_M), run_time=0.4)

        tot_a = f_set_a[2]
        new_a = M("total = 3", 22, YELLOW_M).move_to(tot_a)
        self.beat("Now main changes its local variable total to three. Does the worker's total change too?",
                  Transform(tot_a, new_a), run_time=1.0)
        self.wait(1.8)
        ok = tick(True, 0.16).next_to(f_set_b, RIGHT, buff=0.15)
        self.beat("No. Each total lives on its own stack, where no other thread can reach it. Only the heap is shared.",
                  Indicate(f_set_b[2], color=TEAL_M, scale_factor=1.2), Create(ok),
                  Indicate(heap_l[0], color=WHITE, scale_factor=1.15), run_time=1.8)
        self.play(FadeOut(VGroup(page, page_l, ml, sl, bars, dot_a, dot_b, f_main, f_set_a, f_run_b, f_set_b,
                                 st_a_l, st_b_l, proc, proc_l, heap, heap_l, *objs, ra, rb, ok)), run_time=0.8)

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
        self.beat("So what moves a thread along its code? A core of the CPU. One core runs one thread at a time.",
                  FadeIn(lb1), FadeIn(lab1), FadeIn(leg), run_time=1.2)

        c1 = ValueTracker(0)
        sl_len, gap = 1.3, 0.18
        segs1, t = [], 0.0
        for i in range(6):
            segs1.append((Y1, t, t + sl_len, BLUE_M if i % 2 == 0 else TEAL_M))
            t += sl_len + gap
        top = lanes(c1, segs1, X0, K)
        self.add(top)
        seq(self, "Two threads, one core. The scheduler in the operating system lets main run for a short slice of time.",
            ([c1.animate.set_value(sl_len)], 2.2))
        cs = VGroup(T("context switch", 24, GREY_B)).move_to([X0 + (sl_len + gap / 2) * K, Y1 - 0.75, 0])
        cs_a = Arrow(cs.get_top(), [X0 + (sl_len + gap / 2) * K, Y1 - 0.3, 0], buff=0.05, stroke_width=2.5,
                     color=GREY_B, max_tip_length_to_length_ratio=0.25)
        seq(self, "Then it saves main's registers, and switches to the worker. That is a context switch. "
                  "It happens thousands of times a second.",
            ([c1.animate.set_value(sl_len + gap + 0.4)], 1.2), ([FadeIn(cs), GrowArrow(cs_a)], 0.6),
            ([c1.animate.set_value(t)], 4.2))
        conc = T("concurrency: both in progress, taking turns", 28, WHITE).move_to([0.6, 2.05, 0])
        self.beat("Both threads are in progress, taking turns on one core. That is concurrency.",
                  FadeIn(conc, shift=DOWN * 0.15), run_time=1.0)

        lb2a, lb2b = lane_box(Y2a), lane_box(Y2b)
        lab2 = VGroup(T("core 1", 26), T("core 2", 26))
        lab2[0].next_to(lb2a, LEFT, buff=0.35)
        lab2[1].next_to(lb2b, LEFT, buff=0.35)
        c2 = ValueTracker(0)
        bot = lanes(c2, [(Y2a, 0, t, BLUE_M), (Y2b, 0, t, TEAL_M)], X0, K)
        par = T("parallelism: both running at the same instant", 28, WHITE).move_to([0.6, -0.2, 0])
        self.add(bot)
        seq(self, "Give them two cores, and both run at the same instant. That is parallelism.",
            ([FadeIn(lb2a), FadeIn(lb2b), FadeIn(lab2)], 0.6), ([c2.animate.set_value(t)], 2.6),
            ([FadeIn(par, shift=DOWN * 0.15)], 0.6))
        self.beat("Concurrency is about how you split the work. Parallelism needs real cores.",
                  Indicate(conc, color=WHITE, scale_factor=1.04), Indicate(par, color=WHITE, scale_factor=1.04),
                  run_time=1.6)
        top.clear_updaters(); bot.clear_updaters()
        self.play(FadeOut(VGroup(top, bot, lb1, lab1, lb2a, lb2b, lab2, cs, cs_a, conc, par, leg)), run_time=0.7)

        # ---------------- the wall at the core count ----------------
        head = T("400 million additions on a 4-core machine", 30).move_to([0, 2.55, 0])
        rows = [(1, 510), (2, 257), (4, 121), (8, 125)]
        BX0, BK = -2.6, 7.0 / 510
        bars2, labs, vals = [], [], []
        for j, (n, ms) in enumerate(rows):
            y = 1.35 - j * 0.95
            col = GOLD_M if n == 8 else BLUE_M
            b = Rectangle(width=ms * BK, height=0.55, stroke_width=0).set_fill(col, 0.85).move_to([BX0, y, 0], aligned_edge=LEFT)
            labs.append(T(f"{n} thread" + ("s" if n > 1 else ""), 28).move_to([BX0 - 0.35, y, 0], aligned_edge=RIGHT))
            vals.append(T(f"{ms} ms", 28, col).next_to(b, RIGHT, buff=0.2))
            bars2.append(b)
        self.beat("Now a busy job, all additions, on a machine with four cores. Is it faster on eight threads than on four?",
                  FadeIn(head), run_time=1.0)
        self.wait(1.8)
        seq(self, "In one run of the demo in this lesson, it took 510 milliseconds on one thread, 257 on two, and 121 on four.",
            *[([FadeIn(labs[j]), GrowFromEdge(bars2[j], LEFT), FadeIn(vals[j])], 0.9) for j in range(3)])
        wall = DashedLine([BX0 + 121 * BK, 1.9, 0], [BX0 + 121 * BK, -1.9, 0], dash_length=0.1, stroke_width=2, color=GREY_B)
        seq(self, "And 125 on eight. Once every core is busy, the extra threads only take turns.",
            ([FadeIn(labs[3]), GrowFromEdge(bars2[3], LEFT), FadeIn(vals[3])], 0.9), 0.6, ([Create(wall)], 0.6))
        note = T("A thread that waits on the network uses no core while it waits.", 26, GREY_A).move_to([0, -2.5, 0])
        self.beat("A thread that waits for a network reply uses no core while it waits. "
                  "So waiting work can use many more threads than cores.", FadeIn(note, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(head, *bars2, *labs, *vals, wall, note)), run_time=0.7)

        # ---------------- start() vs run() ----------------
        div = DashedLine([0, 2.4, 0], [0, -2.9, 0], dash_length=0.1, stroke_width=2, color=GREY_D)
        h_run = M("t.run()", 34, BLUE_M).move_to([-3.5, 2.45, 0])
        h_sta = M("t.start()", 34, TEAL_M).move_to([3.5, 2.45, 0])
        LX, RMX, RNX = -3.5, 2.0, 5.0
        FY = -1.6
        fm_l = frame("main()", BLUE_M).move_to([LX, FY, 0])
        fm_r = frame("main()", BLUE_M).move_to([RMX, FY, 0])
        sl_l = T("main's stack", 24, BLUE_M).move_to([LX, FY - 0.7, 0])
        sl_r = T("main's stack", 24, BLUE_M).move_to([RMX, FY - 0.7, 0])
        self.beat("Last question: how do you make a new thread? Here is main, about to run a task on a thread object t.",
                  FadeIn(fm_l), FadeIn(sl_l), FadeIn(h_run), run_time=1.2)
        fr_l = on_top(frame("task.run()", BLUE_M), fm_l)
        seq(self, "Calling run is a plain method call. Main steps into the task itself, and a frame goes on main's own stack.",
            1.6, ([FadeIn(fr_l, shift=DOWN * 0.3)], 0.9))
        v_l = VGroup(T("one thread: main runs the task", 26, BLUE_M),
                     T("and waits until it returns", 26, BLUE_M)).arrange(DOWN, buff=0.12).move_to([LX, 0.95, 0])
        self.beat("No new thread exists. Nothing fails, your tests pass, and the job is exactly as slow as before.",
                  FadeIn(v_l, shift=UP * 0.15), run_time=1.0)

        self.play(Create(div), FadeIn(h_sta), FadeIn(fm_r), FadeIn(sl_r), run_time=0.8)
        fr_r = frame("task.run()", TEAL_M).move_to([RNX, FY, 0])
        sn = T("settlement-1", 24, TEAL_M).move_to([RNX, FY - 0.7, 0])
        seq(self, "Calling start is different. The JVM asks the operating system for a new thread, with a new stack.",
            1.8, ([FadeIn(sn), FadeIn(fr_r, scale=0.8)], 0.9))
        nx = on_top(frame("next line", BLUE_M), fm_r)
        v_r = VGroup(T("two threads: the task runs", 26, TEAL_M),
                     T("while main goes on", 26, TEAL_M)).arrange(DOWN, buff=0.12).move_to([3.5, 0.95, 0])
        self.beat("The new thread calls run on its own stack, and main goes on to its next line at once.",
                  Indicate(fr_r[0], color=TEAL_M, scale_factor=1.06), FadeIn(nx, shift=DOWN * 0.3),
                  FadeIn(v_r, shift=UP * 0.15), run_time=1.6)
        self.play(FadeOut(VGroup(div, h_run, h_sta, fm_l, fm_r, sl_l, sl_r, fr_l, v_l, fr_r, sn, nx, v_r)), run_time=0.7)

        # ---------------- code ----------------
        jc = code(['Thread t = new Thread(task, "settlement-1");', "t.start();", "t.join();", "", "t.run();"], 26)
        kc = code(['val t = Thread(task, "settlement-1")', "t.start()", "t.join()", "", "t.run()"], 26)
        for b in (jc, kc):
            b[1].set_color(TEAL_M)
            b[4].set_color(RED_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin: the same Java class", kc)).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.6, 0])
        self.beat("In code it looks the same in Java and Kotlin. start makes the thread. "
                  "join waits here until that thread has finished.",
                  FadeIn(cg, shift=UP * 0.2), Indicate(jc[1], color=WHITE, scale_factor=1.08),
                  Indicate(kc[1], color=WHITE, scale_factor=1.08), run_time=2.0)
        rn = T("run(), called by you: the task runs on the thread you are already on", 24, RED_M)
        rn.scale(min(1, 12 / rn.width)).move_to([0, -2.1, 0])
        self.beat("And run, called by you, runs the task on the thread you are already on.",
                  FadeIn(rn, shift=UP * 0.15), Indicate(jc[4], color=WHITE, scale_factor=1.1),
                  Indicate(kc[4], color=WHITE, scale_factor=1.1), run_time=1.4)
        self.play(FadeOut(VGroup(cg, rn)), run_time=0.7)

        # ---------------- rule and check ----------------
        rule = T("Every thread has its own stack and shares one heap.", 34).move_to([0, 2.3, 0])
        rule2 = T("Only start() makes a new thread.", 34, TEAL_M).move_to([0, 1.6, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule.width))
        self.beat("The rule. Every thread has its own stack and shares one heap, and only start makes a new thread.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A report is split into four slices, and you call", 28).move_to([0, 0.15, 0])
        chk2 = M("new Thread(slice).run()", 28, BLUE_M).move_to([0, -0.45, 0])
        chk3 = T("for each one, on a 4-core machine. How much faster is it?", 28).move_to([0, -1.05, 0])
        VGroup(chk, chk2, chk3).scale(min(1, 12 / chk3.width))
        self.beat("Check yourself. A report is split into four slices, and you call run on a new thread for each one, "
                  "on a four-core machine. How much faster is it than one thread?", FadeIn(chk), FadeIn(chk2),
                  FadeIn(chk3), run_time=1.4)
        self.wait(2.5)
        ans = T("Not faster at all: run() is a plain call, so main does the slices one by one.", 28, TEAL_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -2.2, 0])
        self.beat("Not faster at all. Each run is a plain call, so main does the four slices one after another, on one core.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
