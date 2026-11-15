from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"cancel\(true\)", "cancel true"), (r"\bThread\.stop\b", "Thread dot stop"),
              (r"\bInterruptedException\b", "Interrupted Exception"), (r"\bTimeoutException\b", "Timeout Exception"),
              (r"\bisCancelled\b", "is cancelled")]


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
            if rt is None:                       # stretch this step to the end of the line
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


class Flag(VGroup):
    """A thread's interrupt flag: a pole with a cloth that is grey and down (false) or red and up (true)."""

    def __init__(self, x, y0, h=0.85, cw=0.5, ch=0.3):
        self.fx, self.fy0, self.fh, self.cw, self.ch = x, y0, h, cw, ch
        pole = Line([x, y0, 0], [x, y0 + h, 0], stroke_width=3, color=GREY_B)
        cloth = Rectangle(width=cw, height=ch, stroke_width=0).set_fill(GREY_D, 1)
        cloth.move_to([x + cw / 2, y0 + ch / 2, 0])
        super().__init__(pole, cloth)

    def up(self):
        return self[1].animate.set_fill(RED_M, 1).move_to([self.fx + self.cw / 2, self.fy0 + self.fh - self.ch / 2, 0])

    def down(self):
        return self[1].animate.set_fill(GREY_D, 1).move_to([self.fx + self.cw / 2, self.fy0 + self.ch / 2, 0])


class Exec04Cancel(VoiceScene):
    """exec-04, section 1: get(timeout) ends the wait, not the task; cancel(true) only interrupts, and an interrupt
    only sets a flag; a task blocked in sleep stops, a loop that checks the flag stops, a loop that never looks runs on;
    the Future says cancelled at once either way."""

    def construct(self):
        self.title_card("Cancel is a request", "what cancel(true) really does to a running task")

        # =============== part 1: the timeout ends the wait, not the task ===============
        TX0, TX1 = -3.4, 5.6
        PX = (TX1 - TX0) / 700
        def tx(ms):
            return TX0 + ms * PX
        RY, PY = 1.3, -0.5
        req_l = T("request thread", 28, BLUE_M).move_to([-6.3, RY, 0], aligned_edge=LEFT)
        pool_l = T("pool thread", 28, TEAL_M).move_to([-6.3, PY, 0], aligned_edge=LEFT)
        axis = Line([tx(0), -1.55, 0], [tx(700), -1.55, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([tx(m), -1.48, 0], [tx(m), -1.62, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([tx(m), -1.88, 0])) for m in (0, 200, 400, 600)])
        wait_bar = Rectangle(width=200 * PX, height=0.55, stroke_color=BLUE_M, stroke_width=2.5).set_fill(dark(BLUE_M, 0.3), 1)
        wait_bar.move_to([tx(100), RY, 0])
        wait_t = T("waits", 24, BLUE_M).move_to(wait_bar)
        wait_c = M("auth.get(200, MILLISECONDS)", 22, BLUE_M).next_to(wait_bar, UP, buff=0.15).align_to(wait_bar, LEFT)
        task_bar = Rectangle(width=(648 - 16) * PX, height=0.55, stroke_color=TEAL_M, stroke_width=2.5).set_fill(dark(TEAL_M, 0.3), 1)
        task_bar.move_to([tx((16 + 648) / 2), PY, 0])
        task_t = T("calling the card issuer", 26, TEAL_M).next_to(task_bar, UP, buff=0.15).align_to(task_bar, LEFT)
        part = task_bar.copy().stretch_to_fit_width((200 - 16) * PX, about_edge=LEFT)
        cursor = Line([0, RY + 0.55, 0], [0, PY - 0.55, 0], stroke_width=3, color=YELLOW_M)
        tt = ValueTracker(0.0)
        cursor.add_updater(lambda m: m.set_x(tx(tt.get_value())))

        self.beat("A request hands a card charge to a pool, and waits up to 200 ms for the answer.",
                  FadeIn(req_l), FadeIn(pool_l), FadeIn(axis), FadeIn(ticks), FadeIn(wait_c), FadeIn(task_t), run_time=1.6)
        to = T("TimeoutException", 26, RED_M).next_to(wait_bar, RIGHT, buff=0.25)
        fail = T("tells the customer: failed", 24, GREY_A).next_to(to, DOWN, buff=0.12, aligned_edge=LEFT)
        self.add(cursor)
        seq(self, "The issuer takes 600. At 200 ms, get throws a TimeoutException, and the request reports a failure.",
            ([GrowFromEdge(wait_bar, LEFT, rate_func=linear), tt.animate(rate_func=linear).set_value(200),
              GrowFromEdge(part, LEFT, rate_func=linear)], 2.6),
            ([FadeIn(to, shift=RIGHT * 0.2), FadeIn(wait_t)], 0.6), 0.6, ([FadeIn(fail)], 0.5))
        self.beat("What happens to the charge?", Indicate(task_t, color=WHITE, scale_factor=1.04), run_time=0.8)
        self.wait(2.0)
        ok = T("APPROVED: the card is charged", 26, GOLD_M).move_to([6.3, PY - 0.75, 0], aligned_edge=RIGHT)
        dotok = Dot(radius=0.1, color=GOLD_M).move_to([tx(648), PY, 0]).set_z_index(3)
        seq(self, "Nothing stopped it. At about 650 ms the issuer approves, and the card is charged.",
            ([Transform(part, task_bar, rate_func=linear), tt.animate(rate_func=linear).set_value(648)], 3.2),
            ([FadeIn(dotok, scale=0.5), FadeIn(ok, shift=UP * 0.15), FadeOut(cursor)], 0.7))
        cursor.clear_updaters()
        lesson = T("A timeout ends your wait, not the task.", 32).move_to([0, -2.8, 0])
        self.beat("A timeout ends your wait, not the task.", FadeIn(lesson, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(req_l, pool_l, axis, ticks, wait_bar, wait_t, wait_c, part, task_t, to, fail, ok, dotok,
                                 lesson)), run_time=0.7)

        # =============== part 2: cancel(true) sets one flag ===============
        main = box("main", BLUE_M, w=2.4, h=0.9, size=30).move_to([-4.6, -0.5, 0])
        main_c = M("auth.cancel(true)", 24, BLUE_M).next_to(main, DOWN, buff=0.2)
        th = box("pool thread", TEAL_M, w=3.6, h=1.1, size=32).move_to([1.2, -0.5, 0])
        fl = Flag(3.2, 0.05, 1.7, cw=0.8, ch=0.5)
        fl_l = T("interrupt flag", 26, GREY_A).next_to(fl, UP, buff=0.2).shift(RIGHT * 0.4)
        fl_v = M("false", 26, GREY_A).move_to([4.35, 0.3, 0], aligned_edge=LEFT)
        stop = M("thread.stop()", 28, GREY_B).move_to([-4.3, 2.3, 0])
        strike = Line(stop.get_left() + LEFT * 0.1, stop.get_right() + RIGHT * 0.1, stroke_width=4, color=RED_M)
        stop_n = T("removed in JDK 26", 24, GREY_B).next_to(stop, DOWN, buff=0.15)
        self.beat("So you call cancel(true) on its Future. Does that kill the thread?",
                  FadeIn(main), FadeIn(main_c), FadeIn(th), run_time=1.4)
        self.wait(1.2)
        self.beat("No. Java has no safe way to kill a thread.",
                  FadeIn(stop), Create(strike), FadeIn(stop_n), run_time=1.4)
        a = arrow(main.get_right() + RIGHT * 0.1, th.get_left() + LEFT * 0.1, color=RED_M)
        a_l = M("interrupt()", 26, RED_M).next_to(a, UP, buff=0.12)
        fl_v2 = M("true", 26, RED_M).move_to([4.35, 1.5, 0], aligned_edge=LEFT)
        seq(self, "cancel(true) calls interrupt on the task's thread. And interrupt only sets a flag on that thread, "
                  "from false to true.",
            ([GrowArrow(a), FadeIn(a_l)], 0.8), 1.0, ([FadeIn(fl), FadeIn(fl_l), FadeIn(fl_v)], 0.6), 1.0,
            ([fl.up(), Transform(fl_v, fl_v2)], 0.8))
        self.wait(0.6)
        self.play(FadeOut(VGroup(main, main_c, th, fl, fl_l, fl_v, stop, strike, stop_n, a, a_l)), run_time=0.7)

        # =============== part 3: three tasks, one cancel ===============
        CX = [-4.4, 0.0, 4.4]
        COL = [PURPLE_M, TEAL_M, GOLD_M]
        NAMES = ["sleeper", "checker", "ignorer"]
        NY, SY, OY, FY = 2.2, 0.3, -1.35, -2.45
        names = VGroup(*[T(n, 32, c).move_to([x - 0.35, NY, 0]) for n, x, c in zip(NAMES, CX, COL)])
        flags = [Flag(x + 1.15, NY - 0.45, 0.9) for x in CX]
        caller = M("main: cancel(true) on all three", 24, BLUE_M).move_to([0, 3.1, 0])

        # sleeper: blocked in sleep, with a 5 s timer
        sl_box = mbox("Thread.sleep(5_000)", PURPLE_M, h=0.85, size=24).move_to([CX[0], SY + 0.45, 0])
        track = Rectangle(width=3.0, height=0.2, stroke_color=GREY_D, stroke_width=1.5).move_to([CX[0], SY - 0.35, 0])
        tfill = Rectangle(width=0.01, height=0.2, stroke_width=0).set_fill(PURPLE_M, 0.9).move_to(track.get_left(), aligned_edge=LEFT)
        st = {"asleep": True}

        def tfill_upd(m, dt):
            if st["asleep"]:
                w = min(3.0, m.width + 3.0 * dt / 5.0 / 120.0)
                m.stretch_to_fit_width(w).move_to(track.get_left(), aligned_edge=LEFT)
        tfill.add_updater(tfill_upd)
        track_l = T("asleep, would wake at 5 s", 22, GREY_A).next_to(track, DOWN, buff=0.15)

        # two loops: one dot per thread going round, one lap = one pass of the loop body
        R = 0.8
        loops, dots, ang, gate = [], [], {}, None
        LAP = 1.1          # laps per second
        for k in (1, 2):
            c = Circle(radius=R, stroke_color=COL[k], stroke_width=3).move_to([CX[k], SY, 0])
            lab = M("slice()", 24).move_to(c)
            loops.append(VGroup(c, lab))
        gate = VGroup(RoundedRectangle(corner_radius=0.08, width=1.3, height=0.5, stroke_color=TEAL_M, stroke_width=2.5)
                      .set_fill(BLACK, 1), M("flag?", 22, TEAL_M)).move_to([CX[1], SY + R, 0]).set_z_index(4)
        gate[1].move_to(gate[0])
        look = DashedLine(gate.get_right() + RIGHT * 0.05, flags[1][0].get_bottom() + UP * 0.1, dash_length=0.08,
                          stroke_width=2, color=TEAL_M)
        flag_up = {"v": False}
        state = {1: "run", 2: "run"}
        ang = {1: 0.55, 2: 0.15}
        vis = {1: ValueTracker(0.0), 2: ValueTracker(0.0)}
        ex = {"t": 0.0}
        out2 = VGroup(T("saw the flag", 24, TEAL_M), T("returns", 24, GREY_A)).arrange(DOWN, buff=0.1).move_to([CX[1], OY - 0.12, 0])
        out2.set_opacity(0)

        def make_dot(k):
            d = Dot(radius=0.11, color=COL[k]).set_z_index(5)

            def upd(m, dt):
                if state[k] == "run":
                    a0 = ang[k]
                    a1 = a0 + LAP * dt
                    if k == 1 and flag_up["v"] and np.floor(a1) > np.floor(a0):   # reached the gate with the flag up
                        a1 = np.floor(a1)
                        state[k] = "exit"
                    ang[k] = a1
                th_ = 2 * PI * ang[k]
                p = np.array([CX[k] + R * np.sin(th_), SY + R * np.cos(th_), 0])
                op = vis[k].get_value()
                if state[k] == "exit":                 # leave the loop through the gate, then show why
                    ex["t"] += dt
                    u = min(1.0, ex["t"] / 0.6)
                    p = p + UP * 0.7 * u
                    op = 1 - u
                    out2.set_opacity(min(1.0, ex["t"] / 0.5))
                    loops[0][0].set_stroke(GREY_B)
                m.move_to(p).set_opacity(op)
            d.add_updater(upd)
            upd(d, 0)
            return d
        dots = {1: make_dot(1), 2: make_dot(2)}

        def gate_upd(g, dt):
            th_ = 2 * PI * (ang[1] % 1.0)
            near = min(th_, 2 * PI - th_) < 0.35 and state[1] == "run"
            g[0].set_stroke(WHITE if near else TEAL_M)
        gate.add_updater(gate_upd)

        def ticket(text, color):
            t = M(text, 22, color)
            r = RoundedRectangle(corner_radius=0.08, width=3.7, height=0.55, stroke_color=color, stroke_width=2)
            return VGroup(r, t.move_to(r))
        tickets = VGroup(*[ticket("Future: RUNNING", GREY_A).move_to([x, FY, 0]) for x in CX])

        self.add(tfill)
        seq(self, "Three tasks, on three pool threads. The sleeper sleeps for 5 seconds.",
            ([FadeIn(names[0]), FadeIn(flags[0]), FadeIn(sl_box), FadeIn(track), FadeIn(track_l)], 1.0))
        self.add(dots[1], dots[2], out2)
        seq(self, "The checker loops over slices of CPU work, and checks the flag before each slice.",
            ([FadeIn(names[1]), FadeIn(flags[1]), FadeIn(loops[0]), vis[1].animate.set_value(1)], 1.0), 0.6,
            ([FadeIn(gate), Create(look)], 0.8))
        seq(self, "The ignorer runs the same loop, and never looks at the flag.",
            ([FadeIn(names[2]), FadeIn(flags[2]), FadeIn(loops[1]), vis[2].animate.set_value(1), FadeIn(tickets)], 1.2))
        self.beat("At 100 ms, main calls cancel(true) on all three. Which ones stop?", FadeIn(caller), run_time=1.0)
        self.wait(2.0)

        # ---- cancel: three interrupts, three flags up, three futures say CANCELLED ----
        pulses = VGroup(*[Dot(radius=0.09, color=RED_M).move_to(caller.get_bottom()) for _ in range(3)]).set_z_index(6)
        paths = [Line(caller.get_bottom(), f[0].get_top()) for f in flags]
        new_t = VGroup(*[ticket("Future: CANCELLED", RED_M).move_to([x, FY, 0]) for x in CX])
        exc = T("InterruptedException", 24, RED_M).move_to([CX[0], OY, 0])
        out1 = T("stops", 24, GREY_A).next_to(exc, DOWN, buff=0.1)

        def wake():
            st["asleep"] = False
            return [Indicate(sl_box[1], color=RED_M, scale_factor=1.05), flags[0].down(), FadeIn(exc, shift=DOWN * 0.2),
                    FadeIn(out1), sl_box[0].animate.set_stroke(GREY_B)]

        def flags_up():
            flag_up["v"] = True
            return [f.up() for f in flags] + [FadeOut(pulses)] + [Transform(a_, b_) for a_, b_ in zip(tickets, new_t)]
        seq(self, "All three flags go up. The sleeper stops at once. The checker stops at its next check. "
                  "The ignorer keeps going.",
            ([FadeIn(pulses)], 0.2),
            ([MoveAlongPath(p, ln) for p, ln in zip(pulses, paths)], 0.6),
            (flags_up, 0.5),
            (wake, 0.9))
        dots[1].clear_updaters(); gate.clear_updaters()

        seq(self, "Why? The sleeper was blocked in sleep, which watches the flag. "
                  "It wakes up, clears the flag, and throws InterruptedException.",
            ([Indicate(sl_box[0], color=PURPLE_M, scale_factor=1.04)], 1.0), 2.4,
            ([Indicate(flags[0][1], color=GREY_B, scale_factor=1.3), Indicate(exc, color=RED_M)], 1.2))
        self.beat("The checker looked at the flag before its next slice, and returned.",
                  Indicate(gate[1], color=WHITE, scale_factor=1.2), ShowPassingFlash(look.copy().set_stroke(WHITE, 4)), run_time=1.4)
        fin = VGroup(T("never looked", 24, GOLD_M), T("ran all 400 slices", 24, GREY_A)).arrange(DOWN, buff=0.1).move_to([CX[2], OY - 0.12, 0])
        seq(self, "The ignorer never looks. Nothing outside can stop a running loop, so it runs all 400 slices.",
            2.4, ([Indicate(loops[1][0], color=GOLD_M, scale_factor=1.05)], 1.0), 1.0,
            ([FadeIn(fin)], 0.6))
        dots[2].clear_updaters()
        self.play(dots[2].animate.move_to(loops[1][0].get_bottom() + DOWN * 0.5).set_opacity(0),
                  loops[1][0].animate.set_stroke(GREY_B), run_time=0.6)
        seq(self, "And the futures? All three said cancelled the moment cancel was called, even the ignorer's. "
                  "If its work posted to a ledger, the post happened.",
            ([Indicate(tickets, color=RED_M, scale_factor=1.03)], 1.2), 2.8,
            ([Indicate(VGroup(tickets[2], fin), color=GOLD_M, scale_factor=1.04)], 1.2))
        tfill.clear_updaters()
        self.play(FadeOut(VGroup(names, *flags, caller, sl_box, track, tfill, track_l, *loops, gate, look, tickets,
                                 exc, out1, out2, fin, dots[1], dots[2])), run_time=0.8)

        # =============== part 4: code, rule, check ===============
        jc = code(["Thread me = Thread.currentThread();",
                   "for (Slice s : slices) {",
                   "    if (me.isInterrupted()) return;",
                   "    work(s);",
                   "}"], 26)
        kc = code(["val me = Thread.currentThread()",
                   "for (s in slices) {",
                   "    if (me.isInterrupted) return",
                   "    work(s)",
                   "}"], 26)
        for b in (jc, kc):
            b[2].set_color(TEAL_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.6, 0])
        note = T("blocking calls like sleep, wait and BlockingQueue.take check the flag for you", 24, GREY_B).move_to([0, -1.6, 0])
        note.scale(min(1, 12 / note.width))
        self.beat("So a long CPU loop should check the flag itself, in Java or in Kotlin. Blocking calls like sleep already do.",
                  FadeIn(cg, shift=UP * 0.2), FadeIn(note), run_time=1.4)
        self.play(FadeOut(VGroup(cg, note)), run_time=0.6)

        rule = T("cancel(true) is a request, not a kill.", 36).move_to([0, 2.2, 0])
        rule2 = T("A task stops only if it blocks in an interruptible call or checks the flag.", 28, GREY_A).move_to([0, 1.45, 0])
        rule2.scale(min(1, 12 / rule2.width))
        self.beat("The rule. cancel(true) is a request, not a kill. A task stops only if it blocks in an interruptible call, "
                  "or checks the flag.", FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A task runs a CPU loop that never checks the flag. You call cancel(true).", 28).move_to([0, -0.1, 0])
        chk2 = T("What does isCancelled() return, and when does the task stop?", 28).move_to([0, -0.7, 0])
        VGroup(chk, chk2).scale(min(1, 12 / chk.width))
        self.beat("Check yourself. A task runs a CPU loop that never checks the flag, and you call cancel(true). "
                  "What does isCancelled return, and when does the task stop?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("true, at once. The task stops only when its loop ends.", 30, GOLD_M).move_to([0, -1.8, 0])
        ans.scale(min(1, 12 / ans.width))
        self.beat("True, at once. And the task stops only when its loop ends.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
