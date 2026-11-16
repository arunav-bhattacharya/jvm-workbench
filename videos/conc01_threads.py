from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\(\)", ""), (r"\bt\.join\b", "t dot join"), (r"\bms\b", "milliseconds"),
              (r"sales-worker-0", "sales worker zero")]


# ---- helpers for this file ----
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


def think(scene, secs=2.6, pos=(5.85, 2.85)):
    """A small ring that empties while the viewer guesses."""
    c = np.array([*pos, 0])
    q = T("?", 30, GREY_B).move_to(c)
    ring = Arc(radius=0.28, start_angle=PI / 2, angle=TAU, arc_center=c, stroke_width=5, color=GREY_B)
    scene.play(FadeIn(q), FadeIn(ring), run_time=0.3)
    scene.play(UpdateFromAlphaFunc(ring, lambda m, a: m.become(
        Arc(radius=0.28, start_angle=PI / 2, angle=TAU * (1 - a) + 1e-3, arc_center=c, stroke_width=5, color=GREY_B))),
        run_time=secs - 0.6, rate_func=linear)
    scene.play(FadeOut(q), FadeOut(ring), run_time=0.3)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def clerk(color, s=1.0):
    """A clerk: a round head over a half-disc of shoulders."""
    body = Sector(radius=0.38, angle=PI, start_angle=0).set_fill(color, 1).set_stroke(width=0)
    head = Circle(radius=0.19).set_fill(color, 1).set_stroke(width=0).next_to(body, UP, buff=0.07)
    return VGroup(body, head).scale(s)


PAD, PAD_EDGE = "#F3E7B3", "#C9B36A"


def notepad(text, w=1.6, h=0.62):
    r = Rectangle(width=w, height=h).set_fill(PAD, 1).set_stroke(PAD_EDGE, 1.5)
    strip = Rectangle(width=w, height=0.09).set_fill(PAD_EDGE, 1).set_stroke(width=0).align_to(r, UP)
    t = M(text, 22, BLACK).move_to(r).shift(DOWN * 0.03)
    return VGroup(r, strip, t)


def code(lines, size=22, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


MAIN = BLUE_M
WCOL = [TEAL_M, GREEN_M, PURPLE_M, "#F28FB0"]
HEAP = GOLD_M
XM = -5.1
XW = [-2.7, -0.9, 0.9, 2.7]
FIG_Y, NAME_Y, PAD_Y = 0.55, -0.12, -0.8
CAB_C = np.array([0.0, 2.22, 0])


def cabinet():
    outer = RoundedRectangle(corner_radius=0.1, width=5.0, height=1.72, stroke_color=HEAP, stroke_width=3)
    outer.set_fill(dark(HEAP, 0.08), 1).move_to(CAB_C)
    d1 = RoundedRectangle(corner_radius=0.06, width=4.64, height=0.66, stroke_color=HEAP, stroke_width=1.8)
    d2 = d1.copy()
    d1.move_to(CAB_C + UP * 0.38)
    d2.move_to(CAB_C + DOWN * 0.38)
    return VGroup(outer, d1, d2)


def receipts():
    lab = T("receipts", 24, HEAP).move_to(CAB_C + UP * 0.38 + LEFT * 1.55)
    slips = VGroup(*[Rectangle(width=0.26, height=0.4).set_fill(GREY_A, 0.9).set_stroke(GREY_B, 1)
                     for _ in range(7)]).arrange(RIGHT, buff=0.12).move_to(CAB_C + UP * 0.38 + RIGHT * 0.75)
    return VGroup(lab, slips)


def slots():
    lab = M("partial", 22, HEAP).move_to(CAB_C + DOWN * 0.38 + LEFT * 1.6)
    boxes = VGroup()
    for i in range(4):
        b = RoundedRectangle(corner_radius=0.06, width=0.62, height=0.42, stroke_color=WCOL[i], stroke_width=2.5)
        b.set_fill(WCOL[i], 0).move_to(CAB_C + DOWN * 0.38 + RIGHT * (-0.45 + 0.78 * i))
        boxes.add(b)
    return VGroup(lab, boxes)


def bar_for(pad, color):
    """A thin progress bar along the bottom of a notepad, starting empty."""
    r = pad[0]
    b = Rectangle(width=r.width - 0.2, height=0.1).set_fill(color, 1).set_stroke(width=0)
    b.move_to(r.get_bottom() + UP * 0.1)
    b.stretch_to_fit_width(0.01).align_to(r.get_left() + RIGHT * 0.1, LEFT).set_fill(opacity=0)
    return b


def grow(bar, pad, alpha):
    r = pad[0]
    full = r.width - 0.2
    bar.stretch_to_fit_width(max(0.01, full * alpha))
    bar.align_to(r.get_left() + RIGHT * 0.1, LEFT)
    bar.set_fill(opacity=0 if alpha < 0.01 else 1)


class Conc01Threads(VoiceScene):
    """conc-01, section 0: what a thread is, told with the shop's back room. Clerks are threads, the shared
    filing cabinet is the heap, each clerk's notepad is the stack. The JVM already has six threads.
    run() is a plain call on main, start() makes a thread, and join() waits for it (the impatient total)."""

    def construct(self):
        self.title_card("Threads from zero", "a shop, some clerks, and one filing cabinet")

        # ---------------- the question ----------------
        q = T("What is a thread, really?", 48).move_to(UP * 1.4)
        guesses = VGroup(T("your code?", 32, GREY_A), T("the processor?", 32, GREY_A),
                         T("an object in memory?", 32, GREY_A)).arrange(RIGHT, buff=0.9).move_to(DOWN * 0.4)
        fit(guesses, 12)
        seq(self, "People say thread as if you already know what one is. Is it your code? The processor? "
                  "Some object in memory?",
            ([FadeIn(q, shift=UP * 0.2)], 1.0), 1.2, ([FadeIn(guesses[0], shift=UP * 0.15)], 0.5), 0.3,
            ([FadeIn(guesses[1], shift=UP * 0.15)], 0.5), 0.3, ([FadeIn(guesses[2], shift=UP * 0.15)], 0.5))
        self.beat("If you have never been quite sure, you are not alone. Let's find out, with a small shop.",
                  FadeOut(guesses, shift=DOWN * 0.2), q.animate.set_opacity(0.0), run_time=1.0)
        self.remove(q)

        # ---------------- the shop: one clerk, four cores ----------------
        m0 = clerk(MAIN).move_to([XM, FIG_Y, 0])
        pile = VGroup(*[Rectangle(width=1.3, height=0.16).set_fill(GREY_A, 0.9).set_stroke(GREY_B, 1)
                        .shift(UP * 0.12 * i + RIGHT * 0.05 * ((i * 7) % 3 - 1)) for i in range(9)])
        pile.move_to([-2.6, 0.55, 0])
        pile_l = T("1,000,000 sales", 28, GREY_A).next_to(pile, DOWN, buff=0.3)
        seq(self, "The shop records every sale. At the end of the year, the owner wants one number: "
                  "the total of a million sales.",
            ([LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in pile], lag_ratio=0.1)], 1.4), 0.4,
            ([FadeIn(pile_l)], 0.6))
        adding = T("one by one", 26, MAIN).next_to(m0, DOWN, buff=0.35)
        seq(self, "Our program adds them up, one after another.",
            ([FadeIn(m0, shift=UP * 0.2), FadeIn(adding)], 0.8),
            ([Indicate(pile, color=MAIN, scale_factor=1.05)], 1.0))

        lap = RoundedRectangle(corner_radius=0.15, width=3.4, height=2.6, stroke_color=GREY_B, stroke_width=2.5)
        lap.move_to([3.6, 0.35, 0])
        lap_l = T("the owner's laptop: 4 cores", 26, GREY_A).next_to(lap, UP, buff=0.25)
        cores = VGroup(*[RoundedRectangle(corner_radius=0.08, width=1.3, height=0.9, stroke_color=GREY_B,
                                          stroke_width=2).set_fill(BLACK, 1) for _ in range(4)])
        cores.arrange_in_grid(2, 2, buff=0.3).move_to(lap)
        core_note = T("a core: the part of the processor that does the work", 26, GREY_A).move_to([0.6, -2.5, 0])
        fit(core_note, 12)
        seq(self, "The owner's laptop has four cores. A core is the part of the processor that does the work, "
                  "and all four can work at the same moment.",
            ([Create(lap), FadeIn(lap_l), LaggedStart(*[FadeIn(c) for c in cores], lag_ratio=0.2)], 1.4), 0.8,
            ([FadeIn(core_note, shift=UP * 0.15)], 0.7))
        idle = VGroup(*[T("idle", 24, GREY_B).move_to(c) for c in cores[1:]])
        busy = T("busy", 24, WHITE).move_to(cores[0])
        seq(self, "But while our program adds, one core works, and three sit idle.",
            ([cores[0].animate.set_fill(MAIN, 0.75), FadeIn(busy)], 0.8), 0.6,
            ([LaggedStart(*[FadeIn(i) for i in idle], lag_ratio=0.3)], 1.0))
        watchers = VGroup(*[clerk(GREY_C, 0.8) for _ in range(3)]).arrange(RIGHT, buff=0.35)
        watchers.move_to([0.45, -0.95, 0])
        seq(self, "It's like paying four clerks, and letting one do all the adding while three watch.",
            1.2, ([LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in watchers], lag_ratio=0.25)], 1.0))
        # the wish: cut the pile in four
        seq(self, "So why not cut the list into four, and add all four parts at once?",
            ([FadeOut(watchers), FadeOut(core_note), FadeOut(adding)], 0.5),
            ([pile[0:2].animate.move_to([-3.4, 0.35, 0]).scale(0.7), pile[2:4].animate.move_to([-2.4, 0.35, 0]).scale(0.7),
              pile[4:6].animate.move_to([-1.4, 0.35, 0]).scale(0.7), pile[6:9].animate.move_to([-0.4, 0.42, 0]).scale(0.7)],
             1.0))

        # ---------------- the back room ----------------
        cab = cabinet()
        rec = receipts()
        self.play(FadeOut(VGroup(lap, lap_l, cores, idle, busy, pile_l)), run_time=0.6)
        room = RoundedRectangle(corner_radius=0.2, width=12.6, height=6.7, stroke_color=GREY_B, stroke_width=2)
        room_l = T("the back room", 26, GREY_B).move_to([-4.6, 2.95, 0])
        seq(self, "Before computers, a shop gave this job to people. Picture clerks in a back room.",
            ([Create(room), FadeIn(room_l), m0.animate.move_to([XM, FIG_Y, 0])], 1.2))
        workers = VGroup(*[clerk(WCOL[i]).move_to([XW[i], FIG_Y, 0]) for i in range(4)])
        seq(self, "The receipts sit in one filing cabinet that everyone shares.",
            ([FadeIn(cab)], 0.5),
            (lambda: [self.bring_to_front(pile) and None or ReplacementTransform(pile, rec[1]), FadeIn(rec[0])], 1.0),
            ([LaggedStart(*[FadeIn(w, shift=UP * 0.2) for w in workers], lag_ratio=0.2)], 1.0))
        pads = VGroup(*[notepad("total = 0").move_to([x, PAD_Y, 0]) for x in [XM] + XW])
        seq(self, "Each clerk keeps a running total on a notepad of their own.",
            ([LaggedStart(*[FadeIn(p, shift=DOWN * 0.15) for p in pads], lag_ratio=0.15)], 1.4))

        # the map, one label at a time
        RX = 4.85
        l_clerk = VGroup(T("clerk", 26, GREY_A), T("= thread", 30, WHITE)).arrange(DOWN, buff=0.1).move_to([RX, 0.55, 0])
        l_cab = VGroup(T("filing cabinet", 26, GREY_A), T("= heap", 30, HEAP)).arrange(DOWN, buff=0.1).move_to([RX, 2.4, 0])
        l_pad = VGroup(T("notepad", 26, GREY_A), T("= stack", 30, PAD)).arrange(DOWN, buff=0.1).move_to([RX, -0.85, 0])
        self.beat("Let's map it. Each clerk is a thread: one path of work that follows the steps, one by one, "
                  "and always knows where it is.",
                  FadeIn(l_clerk, shift=LEFT * 0.2), Indicate(m0, color=WHITE, scale_factor=1.12), *[Indicate(w, color=WHITE, scale_factor=1.12) for w in workers],
                  run_time=1.6)
        self.beat("The filing cabinet is the heap. Every object you create with new lives there, "
                  "and every thread can reach it.",
                  FadeIn(l_cab, shift=LEFT * 0.2), Circumscribe(cab[0], color=HEAP, buff=0.06), run_time=1.6)
        self.beat("The notepad is the thread's stack: its local variables, and the method calls it is in the "
                  "middle of. Only its owner writes on it.",
                  FadeIn(l_pad, shift=LEFT * 0.2), *[Wiggle(p, scale_value=1.08, rotation_angle=0.015 * TAU) for p in pads],
                  run_time=1.6)
        room_l2 = VGroup(T("the back room", 26, GREY_A), T("= process", 30, WHITE)).arrange(DOWN, buff=0.1,
                                                                                            aligned_edge=LEFT)
        room_l2.align_to(room_l, LEFT).align_to(room_l, UP)
        self.beat("And the whole back room is the process: one running program, with memory of its own.",
                  ReplacementTransform(room_l, room_l2), Indicate(room, color=WHITE, scale_factor=1.0), run_time=1.4)

        # ---------------- predict: does the other notepad change? ----------------
        p1, p2 = pads[1], pads[2]
        seq(self, "Quick guess. One clerk writes total equals 3 on her notepad. "
                  "Does the next clerk's notepad change?",
            1.6, ([Transform(p1[2], M("total = 3", 22, BLACK).move_to(p1[2])), Indicate(p1[0], color=WCOL[0])], 1.0))
        think(self, pos=(5.6, -2.6))
        ok = tick(True, 0.17).next_to(p2, DOWN, buff=0.12)
        self.beat("No. A local variable lives on its own thread's stack.",
                  Create(ok), Indicate(p2[2], color=WCOL[1], scale_factor=1.2), run_time=1.0)
        slip = rec[1][3]
        a1 = Arrow(workers[0][1].get_top(), slip.get_bottom() + LEFT * 0.08, buff=0.08, stroke_width=3, color=WCOL[0],
                   max_tip_length_to_length_ratio=0.12)
        a2 = Arrow(workers[1][1].get_top(), slip.get_bottom() + RIGHT * 0.08, buff=0.08, stroke_width=3, color=WCOL[1],
                   max_tip_length_to_length_ratio=0.12)
        self.beat("But both clerks can open the same drawer and reach the same sale. "
                  "That is what makes threads useful: they share data with no copying.",
                  GrowArrow(a1), GrowArrow(a2), slip.animate.set_fill(WHITE, 1), run_time=1.4)
        self.beat("It is also what makes them risky, because two threads can change one object at the same moment.",
                  Flash(slip, color=RED_M, flash_radius=0.45), slip.animate.set_stroke(RED_M, 3), run_time=1.2)
        rule1 = T("Locals belong to one thread. The heap belongs to all of them.", 30).move_to([0, -2.45, 0])
        fit(rule1, 11.6)
        self.beat("So, locals belong to one thread. The heap belongs to all of them.",
                  FadeIn(rule1, shift=UP * 0.15), run_time=1.0)
        self.wait(0.6)
        self.play(FadeOut(VGroup(room, room_l2, cab, rec, m0, workers, pads, l_clerk, l_cab, l_pad, ok, a1, a2, rule1)),
                  run_time=0.7)

        # ---------------- the threads you already have ----------------
        hq = T("How many threads does the emptiest Java program have?", 34).move_to(UP * 0.6)
        fit(hq, 12)
        self.beat("Before we hire anyone, one more surprise. How many threads does the emptiest Java program have? "
                  "Pause and guess.", FadeIn(hq, shift=UP * 0.15), run_time=1.0)
        think(self, 2.6, pos=(0, -0.8))
        self.play(FadeOut(hq), run_time=0.4)
        names = ["Reference Handler", "Finalizer", "Common-Cleaner", "Signal Dispatcher", "main", "Notification Thread"]
        rows = VGroup(*[M(n, 28, MAIN if n == "main" else GREY_B) for n in names]).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        rows.move_to([-5.4, -0.25, 0], aligned_edge=LEFT)
        head = T("Threads before main starts any (JDK 21)", 26, GREY_A).next_to(rows, UP, buff=0.45)
        head.align_to(rows, LEFT)
        box6 = SurroundingRectangle(VGroup(rows, head), buff=0.35, corner_radius=0.12, color=GREY_D, stroke_width=2)
        seq(self, "The lesson's first demo asks the JVM, the program that runs your Java code. On JDK 21, the list has six.",
            ([FadeIn(box6), FadeIn(head)], 0.8), 1.6,
            ([LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rows], lag_ratio=0.2)], 1.8))
        tag_m = T("runs your main method", 26, MAIN).next_to(rows[4], RIGHT, buff=0.6)
        hk = VGroup(T("the other five:", 26, GREY_A), T("the JVM's housekeepers", 26, GREY_A)).arrange(DOWN, buff=0.1,
                                                                                                    aligned_edge=LEFT)
        hk.next_to(box6, RIGHT, buff=0.45).align_to(rows[0], UP)
        seq(self, "One is main, the thread that runs your main method. The other five are the JVM's housekeepers, "
                  "mostly cleaning up after objects nobody uses any more.",
            ([FadeIn(tag_m, shift=LEFT * 0.2), Indicate(rows[4], color=MAIN, scale_factor=1.15)], 1.0), 1.6,
            ([FadeIn(hk, shift=LEFT * 0.2)], 0.8))
        more = T("and a few more that don't even make the list", 24, GREY_B).next_to(box6, DOWN, buff=0.3)
        self.beat("So your programs had several threads all along. You just never met the cleaning crew.",
                  FadeIn(more, shift=UP * 0.15), run_time=1.0)
        self.wait(0.3)
        self.play(FadeOut(VGroup(box6, head, rows, tag_m, hk, more)), run_time=0.6)

        # ---------------- four workers, with run() ----------------
        room = RoundedRectangle(corner_radius=0.2, width=12.6, height=6.7, stroke_color=GREY_D, stroke_width=2)
        cab = cabinet()
        rec = receipts()
        sl = slots()
        m0 = clerk(MAIN).move_to([XM, FIG_Y, 0])
        workers = VGroup(*[clerk(WCOL[i]).move_to([XW[i], FIG_Y, 0]) for i in range(4)])
        for w in workers:
            w.set_fill(opacity=0.22)
        nm = VGroup(T("main", 26, MAIN).move_to([XM, NAME_Y, 0]),
                    *[T(f"worker {i}", 26, WCOL[i]).move_to([XW[i], NAME_Y, 0]) for i in range(4)])
        pads = VGroup(*[notepad("sum").move_to([x, PAD_Y, 0]) for x in [XM] + XW])
        heap_l = T("heap", 30, HEAP).move_to([4.6, 2.75, 0])
        self.play(FadeIn(VGroup(room, cab, rec, heap_l, m0, nm[0], pads[0])), run_time=0.8)
        con = RoundedRectangle(corner_radius=0.12, width=11.8, height=1.5, stroke_color=GREY_D, stroke_width=2)
        con.move_to([0, -2.4, 0])
        c_java = M('Java:    new Thread(work, "sales-worker-" + w)', 24, WHITE)
        c_kt = M('Kotlin:  Thread(work, "sales-worker-$w")', 24, WHITE)
        cc = VGroup(c_java, c_kt).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(con)
        seq(self, "Now let's hire four clerks. We make four Thread objects, named sales-worker-0 to 3.",
            ([FadeIn(con), FadeIn(cc)], 0.8), 0.4,
            ([LaggedStart(*[FadeIn(VGroup(workers[i], nm[i + 1], pads[i + 1]), shift=UP * 0.15) for i in range(4)],
                          lag_ratio=0.2)], 1.6))
        seq(self, "Each one gets work to do: a lambda that sums one slice of the sales, and puts the result in its own "
                  "slot of an array, here in the cabinet.",
            2.4, ([FadeIn(sl)], 1.0), ([Indicate(sl[1], color=WHITE, scale_factor=1.1)], 1.0))
        run_l = VGroup(M("t.run();", 30, WHITE), T("on each one, in Java and in Kotlin", 24, GREY_A)).arrange(RIGHT, buff=0.4)
        run_l.move_to(con)
        seq(self, "Then we call run() on each one. Which thread will sum each slice? Pause and guess.",
            ([FadeOut(cc), FadeIn(run_l)], 0.8))
        think(self)

        # main does every slice itself: one tracker counts slices done (0 to 4); slots fill in main's colour
        pm = ValueTracker(0)

        def frac(v):
            k = int(np.floor(v + 1e-9))
            f = v - k
            return 1.0 if (f < 1e-6 and v > 0) else f
        bar_m = bar_for(pads[0], MAIN)
        bar_m.add_updater(lambda m: grow(m, pads[0], frac(pm.get_value())))
        for i in range(4):
            sl[1][i].add_updater(lambda m, i=i: m.set_fill(MAIN, 0.85 if pm.get_value() >= i + 1 - 1e-3 else 0))
        self.add(bar_m)
        outs = VGroup(*[M(f"slice {i} summed on main", 24, MAIN) for i in range(4)])
        outs.arrange_in_grid(2, 2, buff=(0.6, 0.18)).move_to(con)
        fit(outs, 11.2)
        steps = [([FadeOut(run_l)], 0.3)]
        for i in range(4):
            steps.append((lambda i=i: [pm.animate(rate_func=linear).set_value(i + 1), FadeIn(outs[i])], 0.85))
        seq(self, "We printed the thread's name inside the work. Every line says: summed on main.", *steps)
        nev = VGroup(*[T("never ran", 22, GREY_B).next_to(pads[i + 1], DOWN, buff=0.12) for i in range(4)])
        self.beat("The total is right, the tests pass, and it is exactly as slow as before. "
                  "Main did all four slices itself.",
                  LaggedStart(*[FadeIn(n) for n in nev], lag_ratio=0.15), Indicate(sl[1], color=MAIN, scale_factor=1.1),
                  run_time=1.6)

        # ---------------- why: run() is a plain call; start() makes a thread ----------------
        why_r = VGroup(M("run()", 30, MAIN), T("a plain method call: the work runs on the caller", 26, WHITE)).arrange(RIGHT, buff=0.4)
        why_r2 = T("named honestly: do it yourself", 26, GREY_A)
        why_s = VGroup(M("start()", 30, WCOL[0]), T("a new thread, which then calls run()", 26, WHITE)).arrange(RIGHT, buff=0.4)
        fit(why_r, 11.2)
        why_r.move_to(con).shift(UP * 0.3)
        why_r2.next_to(why_r, DOWN, buff=0.15)
        why_s.move_to(con)
        seq(self, "Here's why. run() is an ordinary method call, so the work runs right here, on the thread that called it. "
                  "Named honestly, it would be called do it yourself.",
            ([FadeOut(outs), FadeIn(why_r)], 0.8), 3.4, ([FadeIn(why_r2, shift=UP * 0.1)], 0.6))
        seq(self, "The call that makes a thread is start(). The JVM asks the operating system for a new thread, "
                  "and that new thread calls run().",
            ([FadeOut(why_r), FadeOut(why_r2), FadeIn(why_s)], 0.8), 2.0,
            ([LaggedStart(*[w.animate.set_fill(opacity=1) for w in workers], lag_ratio=0.15), FadeOut(nev)], 1.0))

        # ---------------- the workers: one progress tracker each ----------------
        bar_m.clear_updaters()
        for s_ in sl[1]:
            s_.clear_updaters()
        wt = [ValueTracker(0) for _ in range(4)]
        prog = [(lambda i=i: wt[i].get_value()) for i in range(4)]
        bars = [bar_for(pads[i + 1], WCOL[i]) for i in range(4)]
        for i in range(4):
            bars[i].add_updater(lambda m, i=i: grow(m, pads[i + 1], prog[i]()))
            sl[1][i].add_updater(lambda m, i=i: m.set_fill(WCOL[i], 0.85 if prog[i]() > 0.995 else 0))

        def drive(targets, shares):
            """Move each worker's progress from its current value to targets[i], reaching it at shares[i]
            of the step's run time (then it holds)."""
            anims = []
            for i in range(4):
                a0 = wt[i].get_value()

                def u(m, a, a0=a0, to=targets[i], f=shares[i]):
                    m.set_value(a0 + (to - a0) * min(1.0, a / f))
                anims.append(UpdateFromAlphaFunc(wt[i], u))
            return anims

        start_l = VGroup(M("t.start();", 30, WHITE), T("then add up partial at once", 26, GREY_A)).arrange(RIGHT, buff=0.4)
        start_l.move_to(con)
        seq(self, "So we change run() to start(), and add up the four slots right after the loop. Is the total right now?",
            ([FadeOut(why_s), FadeOut(bar_m)], 0.6), ([FadeIn(start_l)], 0.6))
        self.add(*bars)
        think(self, 2.2)
        tot = VGroup(T("total:", 28, MAIN), T("about a quarter of the right answer", 28, RED_M)).arrange(RIGHT, buff=0.3)
        tot.move_to(con)
        read_ar = Arrow(m0[1].get_top(), sl[1][0].get_bottom() + DOWN * 0.02, buff=0.1, stroke_width=3, color=MAIN,
                        max_tip_length_to_length_ratio=0.1)
        tot2 = T("about three quarters", 28, RED_M).next_to(tot[0], RIGHT, buff=0.3)
        seq(self, "The lesson ran it five times. The first total came out at about a quarter of the right answer, "
                  "and the other four at about three quarters.",
            ([FadeOut(start_l)], 0.3),
            (lambda: drive([1.0, 0.6, 0.5, 0.45], [0.8, 1, 1, 1]), 1.3),
            ([GrowArrow(read_ar), FadeIn(tot)], 0.8), 1.4,
            (lambda: drive([1.0, 1.0, 1.0, 0.8], [1, 0.6, 0.9, 1]) + [Transform(tot[1], tot2)], 0.9))
        imp = T("the impatient total", 30, RED_M).move_to(con)
        self.beat("Main added up the slots while the clerks were still adding. Call it the impatient total.",
                  Indicate(read_ar, color=RED_M), FadeOut(tot), FadeIn(imp, shift=UP * 0.1), run_time=1.6)

        # ---------------- the wrong fix: sleep ----------------
        sleep_l = M("Thread.sleep(100);", 30, WHITE).move_to(con).shift(LEFT * 2.4)
        clk_c = np.array([1.4, -2.4, 0])
        clk = Circle(radius=0.42, color=GREY_B, stroke_width=3).move_to(clk_c)
        hand = Line(clk_c, clk_c + UP * 0.34, stroke_width=4, color=WHITE)
        seq(self, "You might be thinking: just sleep for a hundred milliseconds, to give them time.",
            ([FadeOut(imp), FadeOut(read_ar), *[t.animate.set_value(0) for t in wt]], 0.5),
            ([FadeIn(sleep_l), FadeIn(clk), FadeIn(hand)], 0.6))
        busy_l = T("a busier computer", 24, GREY_A).next_to(clk, RIGHT, buff=0.4)
        late = T("not done", 22, RED_M).next_to(pads[4], DOWN, buff=0.12)
        seq(self, "That passes on your laptop, and fails one day on a busier computer. "
                  "Sleep only lets time pass. It's a guess with a number on it.",
            ([FadeIn(busy_l)], 0.5),
            (lambda: [Rotate(hand, -TAU, about_point=clk_c, rate_func=linear)]
             + drive([1.0, 1.0, 1.0, 0.7], [0.6, 0.85, 0.95, 1.0]), 2.4),
            ([FadeIn(late), Indicate(sl[1][3], color=RED_M, scale_factor=1.2)], 0.8))

        # ---------------- join ----------------
        join_l = VGroup(M("t.join();", 30, WHITE), T("wait until thread t has ended", 26, GREY_A)).arrange(RIGHT, buff=0.4)
        join_l.move_to(con)
        self.beat("What we want is to wait for each clerk. That is join().",
                  FadeOut(VGroup(sleep_l, clk, hand, busy_l, late)), FadeIn(join_l), *[t.animate.set_value(0) for t in wt],
                  run_time=1.0)
        seq(self, "t.join() makes the caller wait until thread t has ended. "
                  "And once it returns, the caller sees everything that thread wrote.",
            1.0, ([Indicate(join_l[0], color=WHITE, scale_factor=1.1)], 1.0))
        # one clock for all four; each worker finishes at its own time, main joins them in order
        gt = ValueTracker(0)
        fin = [0.55, 0.8, 0.7, 1.0]
        for i in range(4):
            prog[i] = (lambda i=i: min(1.0, gt.get_value() / fin[i]))
        waits = [DashedVMobject(SurroundingRectangle(VGroup(workers[i], nm[i + 1]), buff=0.12, corner_radius=0.1,
                                                     color=MAIN, stroke_width=3), num_dashes=28) for i in range(4)]
        wl = [T(f"main waits in join() for worker {i}", 26, MAIN).move_to(con) for i in range(4)]
        ticks = VGroup(*[tick(True, 0.17).next_to(pads[i + 1], DOWN, buff=0.12) for i in range(4)])
        done = VGroup(T("total:", 28, MAIN), T("right, every time", 28, GREEN_M)).arrange(RIGHT, buff=0.3)
        done.move_to(con)
        seq(self, "So main starts all four, then joins all four, and only then adds up the slots. "
                  "Now the total is right, every time.",
            ([FadeOut(join_l)], 0.3),
            (lambda: [gt.animate(rate_func=linear).set_value(0.55), Create(waits[0]), FadeIn(wl[0])], 1.1),
            ([Create(ticks[0]), FadeOut(waits[0]), Create(waits[1]), FadeOut(wl[0]), FadeIn(wl[1])], 0.4),
            (lambda: [gt.animate(rate_func=linear).set_value(0.8)], 0.5),
            ([Create(ticks[1]), FadeOut(waits[1]), Create(waits[2]), FadeOut(wl[1]), FadeIn(wl[2])], 0.35),
            ([Create(ticks[2]), FadeOut(waits[2]), Create(waits[3]), FadeOut(wl[2]), FadeIn(wl[3])], 0.35),
            (lambda: [gt.animate(rate_func=linear).set_value(1.0)], 0.5),
            ([Create(ticks[3]), FadeOut(waits[3]), FadeOut(wl[3])], 0.4),
            ([FadeIn(done, shift=UP * 0.1), Indicate(sl[1], color=GREEN_M, scale_factor=1.08)], 0.9))
        self.wait(0.8)
        for b in bars:
            b.clear_updaters()
        for s_ in sl[1]:
            s_.clear_updaters()
        self.play(FadeOut(VGroup(room, cab, rec, sl, heap_l, m0, workers, nm, pads, *bars, ticks, done, con)),
                  run_time=0.7)

        # ---------------- the code, Java and Kotlin ----------------
        jl = ["for (int w = 0; w < 4; w++) {",
              "    int slot = w;",
              "    workers[w] = new Thread(() -> partial[slot] = sumSlice(slot),",
              '                            "sales-worker-" + w);',
              "    workers[w].start();",
              "}",
              "for (Thread t : workers) t.join();   // only now is partial complete"]
        kl = ["val workers = List(4) { w ->",
              '    thread(name = "sales-worker-$w") { partial[w] = sumSlice(w) }',
              "}",
              "workers.forEach { it.join() }        // only now is partial complete"]
        jc, kc = code(jl, 22), code(kl, 22)
        jt, kt = T("Java", 24, GREY_B), T("Kotlin", 24, GREY_B)
        cols = VGroup(VGroup(jt, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.16),
                      VGroup(kt, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.16)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.4)
        cols.move_to(ORIGIN)
        self.beat("Here it is in Java and in Kotlin. Notice the two loops. Start every worker first, then join every worker.",
                  FadeIn(cols, shift=UP * 0.2), run_time=1.4)
        hl_s = SurroundingRectangle(VGroup(*jc[0:6]), buff=0.08, color=WCOL[0], stroke_width=2.5)
        hl_j = SurroundingRectangle(jc[6], buff=0.08, color=MAIN, stroke_width=2.5)
        seq(self, "Join inside the first loop, and main would wait for worker 0 before starting worker 1. "
                  "One clerk at a time again.",
            ([Create(hl_s)], 0.8), 1.2, ([Create(hl_j)], 0.8))
        hl_k = SurroundingRectangle(kc[1], buff=0.08, color=WCOL[0], stroke_width=2.5)
        self.beat("In Kotlin, thread with braces makes the thread and starts it for you, so the run() mistake is hard to make.",
                  FadeOut(hl_s), FadeOut(hl_j), Create(hl_k), run_time=1.2)
        self.wait(0.4)
        self.play(FadeOut(VGroup(cols, hl_k)), run_time=0.6)

        # ---------------- payoff ----------------
        ph = T("a bigger job of the same shape, on 4 cores", 28, GREY_A).move_to([0, 2.3, 0])
        BX0, BK = -3.2, 8.0 / 510
        b1 = Rectangle(width=510 * BK, height=0.6, stroke_width=0).set_fill(MAIN, 0.85).move_to([BX0, 0.9, 0], aligned_edge=LEFT)
        b4 = Rectangle(width=121 * BK, height=0.6, stroke_width=0).set_fill(WCOL[0], 0.85).move_to([BX0, -0.2, 0], aligned_edge=LEFT)
        l1 = T("1 thread", 28).next_to(b1, LEFT, buff=0.35)
        l4 = T("4 threads", 28).next_to(b4, LEFT, buff=0.35)
        v1 = T("510 ms", 28, MAIN).next_to(b1, RIGHT, buff=0.2)
        v4 = T("121 ms", 28, WCOL[0]).next_to(b4, RIGHT, buff=0.2)
        seq(self, "Does it pay? On a bigger job of the same shape, on four cores, the lesson's timing demo took "
                  "510 ms on one thread, and 121 on four.",
            ([FadeIn(ph)], 0.6), 2.6, ([FadeIn(l1), GrowFromEdge(b1, LEFT), FadeIn(v1)], 0.9), 0.6,
            ([FadeIn(l4), GrowFromEdge(b4, LEFT), FadeIn(v4)], 0.8))
        self.wait(0.3)
        self.play(FadeOut(VGroup(ph, b1, b4, l1, l4, v1, v4)), run_time=0.6)

        # ---------------- moral ----------------
        mc = clerk(WCOL[0], 1.5).move_to([-4.4, 1.6, 0])
        mp = notepad("sum").scale(1.1).next_to(mc, DOWN, buff=0.3)
        mcab = cabinet().scale(0.55).move_to([-4.4, -1.15, 0])
        ans = VGroup(T("A thread is one clerk:", 32, WHITE),
                     T("a path of work through your code,", 30, GREY_A),
                     T("with its own notepad (the stack),", 30, PAD),
                     T("sharing one cabinet (the heap).", 30, HEAP)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        ans.move_to([1.3, 1.25, 0])
        seq(self, "So, what is a thread? One clerk: a path of work that follows your code step by step, "
                  "with its own notepad, sharing one cabinet with everyone else.",
            ([FadeIn(mc, shift=UP * 0.2), FadeIn(ans[0])], 0.8), 1.4, ([FadeIn(ans[1])], 0.5), 1.0,
            ([FadeIn(mp), FadeIn(ans[2])], 0.6), 0.6, ([FadeIn(mcab), FadeIn(ans[3])], 0.6))
        rule = VGroup(T("Start every worker, then join every worker.", 30, WCOL[0]),
                      T("Read nothing before the last join.", 30, WCOL[0])).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        rule.next_to(ans, DOWN, buff=0.6).align_to(ans, LEFT)
        self.beat("Start every worker, then join every worker, and read nothing before the last join.",
                  FadeIn(rule, shift=UP * 0.15), run_time=1.2)
        self.wait(0.6)
        self.play(FadeOut(VGroup(mc, mp, mcab, ans, rule)), run_time=0.6)

        # ---------------- check ----------------
        chk = VGroup(T("A friend splits a slow report into four parts", 30),
                     T("and calls run() on a new thread for each part.", 30),
                     T("On four cores, how much faster is it?", 30, YELLOW_M)).arrange(DOWN, buff=0.22).move_to(UP * 0.8)
        fit(chk, 12)
        self.beat("Check yourself. A friend splits a slow report into four parts, and calls run() on a new thread "
                  "for each part. On four cores, how much faster is it?", FadeIn(chk, shift=UP * 0.15), run_time=1.4)
        think(self, 2.6, pos=(0, -1.2))
        ans2 = T("Not faster at all: run() is a plain call, so main does all four parts itself.", 28, WCOL[0])
        fit(ans2, 12).move_to(DOWN * 1.3)
        self.beat("Not faster at all. run() is a plain call, so main does all four parts itself.",
                  FadeIn(ans2, shift=UP * 0.15), run_time=1.0)
        self.wait(1.0)
