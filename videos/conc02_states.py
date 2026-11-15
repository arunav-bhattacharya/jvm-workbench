from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bTIMED_WAITING\b", "timed waiting"), (r"\bRUNNABLE\b", "runnable"), (r"\bBLOCKED\b", "blocked"),
    (r"\bWAITING\b", "waiting"), (r"\bTERMINATED\b", "terminated"), (r"\bNEW\b", "new"),
    (r"\bReentrantLock\b", "re-entrant lock"), (r"\bInterruptedException\b", "interrupted exception"),
    (r"\bisInterrupted\b", "is interrupted"), (r"\btryLock\b", "try lock"), (r"\bunpark\b", "un-park"),
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


def place(name, color, w, h, pos):
    """A state drawn as a place: a box with its name at the top and room for a thread below."""
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.10), opacity=1).move_to(pos)
    t = M(name, 26, color).move_to(r.get_top() + DOWN * 0.3).set_z_index(2)
    return VGroup(r, t)


def slot(p):
    return p[0].get_bottom() + UP * 0.42


def token(label, color, w=1.5, h=0.56):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.32), opacity=1)
    return VGroup(r, T(label, 26)).set_z_index(5)


def sticky():
    r = Rectangle(width=0.72, height=0.4, stroke_width=0).set_fill(YELLOW_M, 1)
    return VGroup(r, T("stop?", 20, BLACK)).rotate(-8 * DEGREES).set_z_index(7)


def edge(a, b):
    return Arrow(np.array([*a, 0]), np.array([*b, 0]), buff=0, stroke_width=3, color=GREY_B,
                 tip_length=0.18, max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=10)


def lab(text, anchor, side, mono=False, color=GREY_A):
    m = (M(text, 22, color) if mono else T(text, 24, color))
    return m.move_to(np.array([*anchor, 0]), aligned_edge=side)


WORKER, OTHER, SHUT = BLUE_M, GREY_B, GOLD_M
C_RUN, C_BLK, C_WAIT, C_DIM = GREEN_M, RED_M, PURPLE_M, GREY_B


class Conc02States(VoiceScene):
    """conc-02, section 0: six Thread.State values as places on a map; one worker thread travels the edges
    (start, core and scheduler, synchronized, wait/join/park, ReentrantLock parks, sleep); interrupt as a
    sticky note: sleep throws and clears it, the catch must put it back, run ends, TERMINATED."""

    def construct(self):
        self.title_card("A thread's life", "six states, and the calls that move it")

        # ---- the problem: a thread dump ----
        rows = [('"auth-worker-1"', "RUNNABLE", C_RUN), ('"auth-worker-2"', "BLOCKED", C_BLK),
                ('"ledger-writer"', "WAITING", C_WAIT)]
        names = VGroup(*[M(n, 30) for n, _, _ in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        states = VGroup(*[M(s, 30, c) for _, s, c in rows])
        for s, n in zip(states, names):
            s.move_to(n, aligned_edge=LEFT).shift(RIGHT * 4.6)
        dump = VGroup(names, states).move_to(DOWN * 0.1)
        dump_t = T("thread dump", 26, GREY_B).next_to(dump, UP, buff=0.55).align_to(dump, LEFT)
        frame = SurroundingRectangle(VGroup(dump, dump_t), buff=0.4, corner_radius=0.12, color=GREY_D, stroke_width=2)
        self.beat("Your payment service stops answering. You take a thread dump. "
                  "Next to every thread, the JVM prints one word.",
                  FadeIn(frame), FadeIn(dump_t), LaggedStart(*[FadeIn(VGroup(n, s), shift=UP * 0.15)
                                                               for n, s in zip(names, states)], lag_ratio=0.4),
                  run_time=2.4)
        self.beat("Which of these threads is doing work?",
                  LaggedStart(*[Indicate(s, color=s.get_color(), scale_factor=1.15) for s in states], lag_ratio=0.3),
                  run_time=1.6, after=1.5)

        # ---- the map: six places ----
        new = place("NEW", C_DIM, 2.0, 1.4, [-5.3, 0.3, 0])
        run = place("RUNNABLE", C_RUN, 4.6, 1.75, [0, 0.3, 0])
        term = place("TERMINATED", C_DIM, 2.3, 1.4, [5.3, 0.3, 0])
        blk = place("BLOCKED", C_BLK, 2.7, 1.4, [0, 2.68, 0])
        wait = place("WAITING", C_WAIT, 2.7, 1.4, [-3.0, -2.68, 0])
        timed = place("TIMED_WAITING", C_WAIT, 3.2, 1.4, [3.0, -2.68, 0])
        core = RoundedRectangle(corner_radius=0.1, width=1.75, height=0.72, stroke_color=GREY_B, stroke_width=2)
        core = DashedVMobject(core, num_dashes=36).move_to([1.0, 0.03, 0])
        core_t = T("core", 22, GREY_B).move_to(core)
        CORE, READY = np.array([1.0, 0.03, 0]), np.array([-1.1, 0.03, 0])

        self.beat("Each word names a place. There are six.",
                  FadeOut(frame), FadeOut(dump_t), FadeOut(names),
                  ReplacementTransform(states[0], run[1]), ReplacementTransform(states[1], blk[1]),
                  ReplacementTransform(states[2], wait[1]),
                  FadeIn(VGroup(run[0], blk[0], wait[0])), FadeIn(new), FadeIn(term), FadeIn(timed),
                  run_time=2.0)
        self.play(FadeIn(core), FadeIn(core_t), run_time=0.5)

        # ---- NEW, start, RUNNABLE and the core ----
        w = token("worker", WORKER).move_to(slot(new))
        self.beat("A new thread sits in NEW. Nothing runs yet.", FadeIn(w, scale=0.8), run_time=1.0)
        a_start = edge((-4.3, 0.3), (-2.3, 0.3))
        l_start = lab("start()", (-3.3, 0.66), ORIGIN, mono=True, color=WHITE)

        def go(tok, arr, dest, rt):
            p = VMobject().set_points_as_corners([tok.get_center(), arr.get_start(), arr.get_end(), dest])
            return MoveAlongPath(tok, p, rate_func=smooth, run_time=rt)

        seq(self, "start hands it to the operating system. Now it is RUNNABLE, and it gets a core.",
            ([GrowArrow(a_start), FadeIn(l_start)], 0.8), 0.6, ([go(w, a_start, CORE, 1.4)], 1.4))
        o = token("other", OTHER).move_to(CORE + RIGHT * 3.0).set_opacity(0)
        seq(self, "But cores are few. When another thread gets the core, ours waits its turn. "
                  "It is still RUNNABLE.",
            1.0, ([w.animate.move_to(READY), o.animate.move_to(CORE).set_opacity(1)], 1.2), 1.0,
            ([Indicate(run[1], color=C_RUN, scale_factor=1.15)], 1.0))
        seq(self, "So RUNNABLE in a dump does not prove a thread is working.",
            1.8, ([FadeOut(o, shift=RIGHT * 0.4), w.animate.move_to(CORE)], 1.0))

        # ---- BLOCKED ----
        a_up = edge((-0.45, 1.175), (-0.45, 1.98))
        a_dn = edge((0.45, 1.98), (0.45, 1.175))
        l_up = lab("lock is held", (-0.62, 1.58), RIGHT)
        l_dn = lab("gets the lock", (0.62, 1.58), LEFT)
        self.beat("Next, it reaches a synchronized block whose lock another thread holds. "
                  "Where does it go?", after=1.6)
        seq(self, "Up to BLOCKED. When the lock comes free, it takes it and goes back.",
            ([GrowArrow(a_up), FadeIn(l_up)], 0.6), ([go(w, a_up, slot(blk), 1.1)], 1.1), 1.2,
            ([GrowArrow(a_dn), FadeIn(l_dn)], 0.6), (lambda: [go(w, a_dn, CORE, 1.1)], 1.1))

        # ---- WAITING ----
        a_w = edge((-2.1, -0.575), (-2.1, -1.98))
        a_wb = edge((-1.8, -1.98), (-1.8, -0.575))
        l_w = lab("wait(), join(), park()", (-2.28, -1.3), RIGHT, mono=True, color=WHITE)
        l_wb = lab("notify, unpark, end", (-1.62, -1.05), LEFT)
        seq(self, "wait, join or park, with no time limit, puts it in WAITING, "
                  "until a notify, an unpark, or the joined thread ends.",
            ([GrowArrow(a_w), FadeIn(l_w)], 0.7), ([go(w, a_w, slot(wait), 1.3)], 1.3), 1.4,
            ([GrowArrow(a_wb), FadeIn(l_wb)], 0.7), (lambda: [go(w, a_wb, CORE, 1.2)], 1.2))

        # ---- the ReentrantLock surprise ----
        self.beat("Now it asks for a ReentrantLock that another thread holds. Which box this time?", after=1.6)
        only = T("synchronized only", 22, C_BLK).next_to(blk[0], LEFT, buff=0.3)
        seq(self, "WAITING. ReentrantLock is plain Java code that parks the thread. BLOCKED is only for synchronized.",
            ([go(w, a_w, slot(wait), 1.2), Indicate(l_w[-6:], color=YELLOW_M, scale_factor=1.3)], 1.4), 1.6,
            ([FadeIn(only, shift=LEFT * 0.2), Indicate(blk[1], color=C_BLK, scale_factor=1.15)], 1.0), 0.6,
            (lambda: [go(w, a_wb, CORE, 1.0)], 1.0))

        # ---- TIMED_WAITING ----
        a_t = edge((2.1, -0.575), (2.1, -1.98))
        a_tb = edge((1.75, -1.98), (1.75, -0.575))
        l_t = lab("sleep(ms), wait(ms)", (2.28, -1.3), LEFT, mono=True, color=WHITE)
        l_tb = lab("time up, or woken", (1.57, -1.55), RIGHT)
        seq(self, "With a time limit, like sleep for two hundred milliseconds, it goes to TIMED_WAITING. "
                  "It sleeps here between retries.",
            ([GrowArrow(a_t), FadeIn(l_t)], 0.7), ([go(w, a_t, slot(timed), 1.3)], 1.3), 1.4,
            ([GrowArrow(a_tb), FadeIn(l_tb)], 0.7))

        # ---- interrupt: a note the thread must notice ----
        sh = token("shutdown", SHUT, w=1.75).move_to([5.2, 2.68, 0])
        self.beat("Now the service shuts down. Java cannot kill a thread safely. It can only ask.",
                  FadeIn(sh, shift=LEFT * 0.3), run_time=1.0)
        nt = sticky().move_to(sh.get_corner(DR) + LEFT * 0.2)
        stuck = lambda: w[0].get_right() + np.array([0.15, 0.1, 0])

        def follow(m):
            m.add_updater(lambda x: x.move_to(stuck()))
            return Wait(0.01)

        def unfollow(m):
            m.clear_updaters()
            return Wait(0.01)
        seq(self, "interrupt sticks a note on the thread: a flag that says, please stop.",
            1.0, ([FadeIn(nt, scale=0.6)], 0.5),
            ([MoveAlongPath(nt, ArcBetweenPoints(nt.get_center(), stuck(), angle=-PI / 3))], 1.4))
        self.beat("The worker is asleep. What happens?", after=1.5)
        cleared = T("cleared", 22, RED_M).move_to(READY + DOWN * 0.02)
        seq(self, "sleep throws InterruptedException, and the worker runs again, in its catch block. "
                  "But sleep took the note off first. The flag is cleared.",
            ([Wiggle(w, scale_value=1.08), Indicate(nt, color=YELLOW_M)], 0.9),
            (lambda: [go(w, a_tb, CORE, 1.0), follow(nt)], 1.0), 2.2,
            (lambda: [unfollow(nt), nt.animate.move_to(READY).set_opacity(0.0), FadeIn(cleared)], 1.0))
        self.remove(nt)
        seq(self, "If the catch block only logs it, the request is gone. The loop sleeps again, and never stops.",
            1.4, ([FadeOut(cleared), w[0].animate.set_stroke(RED_M)], 0.4), (lambda: [go(w, a_t, slot(timed), 1.2)], 1.2))
        nt2 = sticky()
        seq(self, "Rewind. This time the catch block puts the note back.",
            ([go(w, a_tb, CORE, 0.9)], 0.9), (lambda: [w[0].animate.set_stroke(WORKER)], 0.3), 0.6,
            (lambda: [FadeIn(nt2.move_to(stuck()), shift=DOWN * 0.3, scale=1.4)], 0.8))
        nt2.add_updater(lambda x: x.move_to(stuck()))
        chk = M("isInterrupted()", 20, GREEN_M).move_to([-1.09, 0.03, 0])
        seq(self, "The loop checks isInterrupted, sees the note, and returns. "
                  "A loop that never blocks must make this check itself, or the note just sits there.",
            ([FadeIn(chk, shift=RIGHT * 0.2)], 0.7), 0.5, ([Indicate(nt2, color=YELLOW_M, scale_factor=1.3)], 0.9))
        a_end = edge((2.3, 0.3), (4.15, 0.3))
        l_end = lab("run() ends", (3.225, 0.64), ORIGIN)
        seq(self, "run ends. TERMINATED is final. A thread can never start again.",
            (lambda: [nt2.clear_updaters(), FadeOut(chk), FadeOut(nt2), GrowArrow(a_end), FadeIn(l_end)][1:], 0.6),
            ([go(w, a_end, slot(term), 1.1), FadeOut(sh)], 1.1), 0.8,
            ([Indicate(term[1], color=WHITE, scale_factor=1.12)], 0.9))

        board = VGroup(new, run, term, blk, wait, timed, core, core_t, a_start, l_start, a_up, a_dn, l_up, l_dn,
                       a_w, a_wb, l_w, l_wb, only, a_t, a_tb, l_t, l_tb, a_end, l_end)
        self.play(FadeOut(board), FadeOut(w), run_time=0.8)

        # ---- the code: put the flag back ----
        title = T("Put the note back", 40).to_edge(UP, buff=0.6)
        jc = code(["try { Thread.sleep(backoff); }", "catch (InterruptedException e) {",
                   "    Thread.currentThread().interrupt();", "    return;", "}"], 26)
        kc = code(["try { Thread.sleep(backoff) }", "catch (e: InterruptedException) {",
                   "    Thread.currentThread().interrupt()", "    return", "}"], 26)
        for b in (jc, kc):
            b[2].set_color(GREEN_M)
        cols = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        cols.scale(min(1, 12 / cols.width)).next_to(title, DOWN, buff=0.45)
        self.beat("In code, it is one line, in Java and in Kotlin.",
                  Write(title), FadeIn(cols, shift=UP * 0.2), run_time=1.8)
        self.beat("The rule: interrupt only asks. Whoever catches it puts the flag back, and stops.",
                  Indicate(VGroup(jc[2], kc[2]), color=GREEN_M, scale_factor=1.04))
        self.play(FadeOut(VGroup(title, cols)), run_time=0.7)

        # ---- check question on the map ----
        board.remove(only)
        self.play(FadeIn(board), run_time=0.8)
        self.beat("Quick check. A thread waits in tryLock with a one second timeout. Which box?", after=2.5)
        self.beat("TIMED_WAITING. ReentrantLock parks it, with a time limit.",
                  Circumscribe(timed[0], color=YELLOW_M, buff=0.08), Indicate(timed[1], color=YELLOW_M, scale_factor=1.2),
                  run_time=1.4)
        self.wait(0.6)
