from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"Thread\.currentThread\(\)\.interrupt\(\)", "thread dot current thread dot interrupt"),
    (r"Thread\.interrupted\(\)", "thread dot interrupted"),
    (r"\brelay\.interrupt\(\)", "relay dot interrupt"), (r"\brelay\.join\(\)", "relay dot join"),
    (r"\bgetState\(\)", "get state"), (r"\bisInterrupted\(\)", "is interrupted"),
    (r"\bIllegalThreadStateException\b", "illegal thread state exception"),
    (r"\bInterruptedException\b", "interrupted exception"), (r"\bThreadStates\b", "thread states"),
    (r"Ctrl\+C", "control C"), (r"\(\)", ""),
    (r"\bTIMED_WAITING\b", "timed waiting"), (r"\bRUNNABLE\b", "runnable"), (r"\bBLOCKED\b", "blocked"),
    (r"\bWAITING\b", "waiting"), (r"\bTERMINATED\b", "terminated"), (r"\bNEW\b", "new"),
]


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


def code(lines, size=24, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def clerk(color, s=1.0):
    body = Sector(radius=0.38, angle=PI, start_angle=0).set_fill(color, 1).set_stroke(width=0)
    head = Circle(radius=0.19).set_fill(color, 1).set_stroke(width=0).next_to(body, UP, buff=0.07)
    return VGroup(body, head).scale(s)


def envelope(s=1.0):
    r = Rectangle(width=0.56, height=0.36).set_fill("#E8E8E8", 1).set_stroke(GREY_B, 1.2)
    v = VMobject(stroke_color=GREY_C, stroke_width=1.5).set_points_as_corners(
        [r.get_corner(UL), r.get_center() + DOWN * 0.04, r.get_corner(UR)])
    return VGroup(r, v).scale(s)


def note(text="finish up"):
    t = T(text, 20, BLACK)
    r = Rectangle(width=t.width + 0.25, height=0.44, stroke_width=0).set_fill(YELLOW_M, 1)
    return VGroup(r, t.move_to(r)).rotate(-6 * DEGREES).set_z_index(8)


def place(name, phrase, color, w, h, pos):
    """A state drawn as a place: name on top, the everyday phrase under it, room for tokens below."""
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.10), opacity=1).move_to(pos)
    t = M(name, 26, color).move_to(r.get_top() + DOWN * 0.28)
    p = fit(T(phrase, 22, GREY_A), w - 0.3).move_to(r.get_top() + DOWN * 0.68)
    return VGroup(r, t, p)


def slot(p, dx=0.0):
    return p[0].get_bottom() + UP * 0.36 + RIGHT * dx


def token(label, color, w=1.3, h=0.5):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.32), opacity=1)
    return VGroup(r, T(label, 26)).set_z_index(5)


def edge(a, b):
    return Arrow(np.array([*a, 0]), np.array([*b, 0]), buff=0, stroke_width=3, color=GREY_B,
                 tip_length=0.18, max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=10)


def lab(text, anchor, side, mono=False, color=GREY_A):
    m = (M(text, 22, color) if mono else T(text, 22, color))
    return m.move_to(np.array([*anchor, 0]), aligned_edge=side)


def go(tok, arr, dest, rt):
    p = VMobject().set_points_as_corners([tok.get_center(), arr.get_start(), arr.get_end(), dest])
    return MoveAlongPath(tok, p, rate_func=smooth, run_time=rt)


RELAY, MAINC = TEAL_M, BLUE_M
C_RUN, C_BLK, C_WAIT, C_DIM = GREEN_M, RED_M, PURPLE_M, GREY_B


class Conc02States(VoiceScene):
    """conc-02, section 0: the mail-room relay that won't stop. A clerk's day as the six Thread.State places,
    walked in order (NEW, RUNNABLE, TIMED_WAITING, WAITING, BLOCKED, TERMINATED) with the call behind each move;
    the ThreadStates output; interrupt as a note on the desk that sleep tears off; put it back."""

    def construct(self):
        self.title_card("A thread's life", "six places to be, and a note that's easy to lose")

        # ---------------- the mail room ----------------
        tray = Polygon([-5.6, -0.1, 0], [-3.4, -0.1, 0], [-3.7, -0.65, 0], [-5.3, -0.65, 0],
                       stroke_color=GREY_B, stroke_width=3).set_fill(GREY_E, 1)
        tray_l = T("out tray", 26, GREY_A).next_to(tray, DOWN, buff=0.3)
        envs = VGroup(*[envelope().move_to([-4.5 + 0.12 * k, -0.05 + 0.1 * k, 0]) for k in range(3)])
        relay = clerk(RELAY, 1.2).move_to([-1.3, 0.1, 0])
        relay_l = T("the relay", 28, RELAY).next_to(relay, DOWN, buff=0.3)
        sent = VGroup(Arrow([0.4, 0.1, 0], [2.0, 0.1, 0], buff=0, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.2), T("sent", 26, GREY_A).move_to([1.2, 0.45, 0]))
        seq(self, "Picture a program with a mail room. Other parts of the program drop messages into an out tray.",
            ([FadeIn(tray), FadeIn(tray_l)], 0.8), 1.2,
            ([LaggedStart(*[FadeIn(e, shift=DOWN * 0.4) for e in envs], lag_ratio=0.4)], 1.4))

        def send(e):
            return [(lambda: [e.animate.move_to(relay.get_center() + RIGHT * 0.6 + UP * 0.2)], 0.5),
                    (lambda: [e.animate.move_to([2.6, 0.1, 0]).set_opacity(0)], 0.6)]
        seq(self, "A helper thread, the relay, empties the tray and sends what it finds.",
            ([FadeIn(relay, shift=UP * 0.2), FadeIn(relay_l), FadeIn(sent)], 0.8),
            *send(envs[2]), *send(envs[1]), *send(envs[0]))
        self.remove(envs)
        zz = T("z z z", 28, GREY_B).next_to(relay, UR, buff=0.05)
        seq(self, "When the tray is empty, it naps, then looks again.",
            ([relay.animate.rotate(-12 * DEGREES), FadeIn(zz, shift=UP * 0.2)], 1.0))

        mn = clerk(MAINC, 1.2).move_to([4.6, 0.1, 0])
        mn_l = T("main", 28, MAINC).next_to(mn, DOWN, buff=0.3)
        bub = VGroup(RoundedRectangle(corner_radius=0.2, width=2.4, height=0.7, stroke_color=MAINC, stroke_width=2.5),
                     T("please stop", 26, WHITE)).move_to([4.2, 1.6, 0])
        bub[1].move_to(bub[0])
        seq(self, "One day you try to quit. The main thread asks the relay to stop, and waits.",
            ([FadeIn(mn, shift=LEFT * 0.2), FadeIn(mn_l)], 0.8), 0.8, ([FadeIn(bub, shift=UP * 0.15)], 0.6))
        con = RoundedRectangle(corner_radius=0.12, width=9.0, height=1.0, stroke_color=GREY_D, stroke_width=2)
        con.move_to([-0.6, -2.5, 0])
        line = M("relay interrupted, carrying on", 26, GREY_A).move_to(con)
        e2 = envelope().move_to([-4.5, -0.05, 0])
        key = VGroup(RoundedRectangle(corner_radius=0.1, width=1.4, height=0.75, stroke_color=WHITE, stroke_width=2.5),
                     M("Ctrl+C", 24)).next_to(con, RIGHT, buff=0.4)
        key[1].move_to(key[0])
        seq(self, "The relay prints one line, relay interrupted, carrying on. And it carries on, until you press Ctrl+C.",
            ([FadeIn(con), relay.animate.rotate(12 * DEGREES), FadeOut(zz)], 0.6), ([Write(line)], 1.4), 0.6,
            ([FadeIn(e2, shift=DOWN * 0.3)], 0.5), *send(e2), 0.4, ([FadeIn(key, scale=0.8)], 0.5))
        self.remove(e2)
        self.beat("Polite, honest, and no help at all. It heard the request, and then it lost it.",
                  Indicate(line, color=RED_M, scale_factor=1.05), FadeOut(bub), run_time=1.4)
        self.play(FadeOut(VGroup(tray, tray_l, relay, relay_l, sent, mn, mn_l, con, line, key)), run_time=0.6)

        # ---------------- the shy questions ----------------
        q1 = T("When a thread isn't running, where is it?", 38).move_to(UP * 0.8)
        q2 = T("When you ask it to stop, where does the request go?", 38).move_to(DOWN * 0.4)
        fit(q2, 12)
        seq(self, "So, two questions you might be shy to ask. When a thread isn't running, where is it? "
                  "And when you ask it to stop, where does the request go?",
            2.2, ([FadeIn(q1, shift=UP * 0.15)], 0.6), 1.4, ([FadeIn(q2, shift=UP * 0.15)], 0.6))
        self.wait(0.5)
        self.play(FadeOut(q1), FadeOut(q2), run_time=0.5)

        # ---------------- a clerk's day: six places ----------------
        new = place("NEW", "not in yet", C_DIM, 2.3, 1.6, [-5.25, 0.15, 0])
        run = place("RUNNABLE", "at a desk, or next in line", C_RUN, 5.0, 1.8, [0, 0.15, 0])
        tim = place("TIMED_WAITING", "napping, alarm set", C_WAIT, 3.6, 1.6, [3.0, -2.5, 0])
        wai = place("WAITING", "waiting for the doorbell", C_WAIT, 3.8, 1.6, [-3.0, -2.5, 0])
        blk = place("BLOCKED", "outside a locked door", C_BLK, 3.4, 1.6, [0, 2.5, 0])
        ter = place("TERMINATED", "gone home", C_DIM, 2.3, 1.6, [5.25, 0.15, 0])
        desk = DashedVMobject(RoundedRectangle(corner_radius=0.08, width=1.9, height=0.62, stroke_color=GREY_B,
                                               stroke_width=2), num_dashes=34).move_to([1.15, -0.37, 0])
        desk_l = T("desk", 22, GREY_B).move_to(desk)
        DESK, NEXT = np.array([1.15, -0.37, 0]), np.array([-1.15, -0.37, 0])
        order = [new, run, tim, wai, blk, ter]
        self.beat("Think of the relay as a clerk. A clerk's day has a few places to be.", run_time=1.0)
        seq(self, "Not in yet. At a desk, working. Napping with an alarm set. Waiting for the doorbell. "
                  "Stuck outside a locked door. Gone home.",
            ([FadeIn(VGroup(new[0], new[2]))], 0.6), 0.5, ([FadeIn(VGroup(run[0], run[2])), FadeIn(desk), FadeIn(desk_l)], 0.6),
            0.6, ([FadeIn(VGroup(tim[0], tim[2]))], 0.6), 0.7, ([FadeIn(VGroup(wai[0], wai[2]))], 0.6), 0.7,
            ([FadeIn(VGroup(blk[0], blk[2]))], 0.6), 0.7, ([FadeIn(VGroup(ter[0], ter[2]))], 0.6))
        seq(self, "A thread has six places just like these. Java calls them states, and getState() tells you "
                  "which one a thread is in.",
            1.2, ([LaggedStart(*[FadeIn(p[1], shift=DOWN * 0.1) for p in order], lag_ratio=0.2)], 1.6))
        self.beat("The clerk is the thread, and a desk is a core, the part of the processor that runs one thread at a time.",
                  Indicate(desk_l, color=WHITE, scale_factor=1.3), run_time=1.2)

        # ---------------- the walk ----------------
        w = token("relay", RELAY).move_to(slot(new))
        nl = lab("new Thread(...)", (-5.25, 1.62), ORIGIN, mono=True, color=WHITE)
        na = edge((-5.25, 1.36), (-5.25, 0.98))
        seq(self, "new Thread gives us an object and nothing more: no real thread yet. That's NEW.",
            ([FadeIn(nl), GrowArrow(na)], 0.7), ([FadeIn(w, scale=0.8)], 0.6), 2.0,
            ([Indicate(new[1], color=WHITE, scale_factor=1.15)], 0.8))
        a_start = edge((-4.1, 0.15), (-2.5, 0.15))
        l_start = lab("start()", (-3.3, 0.47), ORIGIN, mono=True, color=WHITE)
        seq(self, "start() asks the operating system for a real thread, which calls run(). "
                  "Now the relay is RUNNABLE, at a desk.",
            ([GrowArrow(a_start), FadeIn(l_start)], 0.7), 1.2, ([go(w, a_start, DESK, 1.3)], 1.3))
        oth = token("other", GREY_B).move_to(DESK + RIGHT * 4.5).set_opacity(0)
        seq(self, "RUNNABLE also covers a thread that's ready, but waiting for a free desk.",
            0.6, (lambda: [w.animate.move_to(NEXT), oth.animate.move_to(DESK).set_opacity(1)], 1.1), 1.0,
            (lambda: [FadeOut(oth, shift=RIGHT * 0.5), w.animate.move_to(DESK)], 0.9))
        a_t = edge((1.95, -0.75), (1.95, -1.7))
        a_tb = edge((1.6, -1.7), (1.6, -0.75))
        l_t = lab("sleep(200)", (2.12, -1.27), LEFT, mono=True, color=WHITE)
        l_tb = lab("time up", (1.43, -1.27), RIGHT)
        seq(self, "The tray is empty, so the relay calls sleep, for 200 milliseconds. Where does it go?",
            1.8, ([GrowArrow(a_t), FadeIn(l_t)], 0.7))
        think(self, 2.4)
        seq(self, "TIMED_WAITING: a wait with a time limit. When the time is up, it's RUNNABLE again.",
            ([go(w, a_t, slot(tim), 1.1)], 1.1), 1.4, ([GrowArrow(a_tb), FadeIn(l_tb)], 0.6),
            (lambda: [go(w, a_tb, DESK, 1.0)], 1.0))
        a_w = edge((-1.95, -0.75), (-1.95, -1.7))
        a_wb = edge((-1.6, -1.7), (-1.6, -0.75))
        l_w = lab("take(), join()", (-2.12, -1.27), RIGHT, mono=True, color=WHITE)
        l_wb = lab("woken", (-1.43, -1.27), LEFT)
        seq(self, "Now say the relay reads from a queue, whose take() waits until there's something to take. "
                  "On an empty queue, there's no clock, only a doorbell: another thread adding a message.",
            2.6, ([GrowArrow(a_w), FadeIn(l_w)], 0.7), 0.4, (lambda: [go(w, a_w, slot(wai, 0.75), 1.2)], 1.2), 2.4,
            ([GrowArrow(a_wb), FadeIn(l_wb)], 0.6))
        seq(self, "That's WAITING, and join() with no time limit waits the same way.",
            ([Indicate(wai[1], color=C_WAIT, scale_factor=1.15)], 1.0))
        mt = token("main", MAINC).move_to(slot(wai, -0.75))
        self.beat("So where was main, the whole time it sat in relay.join()?")
        think(self, 2.4)
        self.beat("WAITING, right there, until the relay ends.", FadeIn(mt, scale=0.7), run_time=0.8)
        seq(self, "The relay goes back to its desk.", ([go(w, a_wb, DESK, 1.0)], 1.0))
        a_up = edge((-0.5, 1.05), (-0.5, 1.7))
        a_dn = edge((0.5, 1.7), (0.5, 1.05))
        l_up = lab("synchronized", (-0.66, 1.42), RIGHT, mono=True, color=WHITE)
        l_dn = lab("gets the lock", (0.66, 1.42), LEFT)
        seq(self, "It also writes each message into a shared logbook, inside a synchronized block. "
                  "That block is a door with one key, called a lock.",
            3.0, ([GrowArrow(a_up), FadeIn(l_up)], 0.7))
        seq(self, "If another thread holds the key, the relay waits outside the door. That's BLOCKED. "
                  "When the key comes free, it takes it and goes back.",
            ([go(w, a_up, slot(blk), 1.1)], 1.1), 1.6, ([GrowArrow(a_dn), FadeIn(l_dn)], 0.6), 0.6,
            (lambda: [go(w, a_dn, DESK, 1.0)], 1.0))
        a_end = edge((2.5, 0.15), (4.1, 0.15))
        l_end = lab("run() ends", (3.3, 0.47), ORIGIN, color=WHITE)
        seq(self, "And when run() returns, the thread is TERMINATED. That's final, "
                  "and it's the one place our relay never gets to.",
            ([GrowArrow(a_end), FadeIn(l_end)], 0.7), 0.6, ([Indicate(ter[1], color=WHITE, scale_factor=1.15)], 0.9),
            1.2, ([Wiggle(w, scale_value=1.15)], 0.9))
        board = VGroup(*order, desk, desk_l, nl, na, a_start, l_start, a_t, a_tb, l_t, l_tb, a_w, a_wb, l_w, l_wb,
                       a_up, a_dn, l_up, l_dn, a_end, l_end)
        self.play(FadeOut(board), FadeOut(w), FadeOut(mt), run_time=0.7)

        # ---------------- proof: the ThreadStates output ----------------
        rows = [("before start():", "NEW", C_DIM), ("inside sleep(2000):", "TIMED_WAITING", C_WAIT),
                ("in a busy loop:", "RUNNABLE", C_RUN), ("inside wait():", "WAITING", C_WAIT),
                ("entering a held lock:", "BLOCKED", C_BLK), ("waiter interrupted, flag now false", "", YELLOW_M),
                ("after join():", "TERMINATED", C_DIM)]
        left = VGroup(*[M(a, 26, YELLOW_M if not b else GREY_A) for a, b, _ in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        right = []
        for (a, b, c), l in zip(rows, left):
            if b:
                right.append(M(b, 26, c).move_to([0, l.get_y(), 0]).align_to(left, LEFT).shift(RIGHT * 4.6))
            else:
                right.append(VGroup())
        out = VGroup(left, *right)
        out.move_to([0, -0.2, 0])
        head = T("ThreadStates, on JDK 21", 26, GREY_B).next_to(out, UP, buff=0.45).align_to(out, LEFT)
        frame_ = SurroundingRectangle(VGroup(out, head), buff=0.35, corner_radius=0.12, color=GREY_D, stroke_width=2)
        seq(self, "Let's not take my word for it. The lesson's ThreadStates demo asks getState() at each stop. "
                  "On JDK 21, it printed this.",
            ([FadeIn(frame_), FadeIn(head)], 0.7), 2.4,
            ([LaggedStart(*[FadeIn(VGroup(l, r), shift=RIGHT * 0.2) for l, r in zip(left, right)], lag_ratio=0.25)], 2.4))
        seq(self, "Each state shows up where the walk said. Notice the odd line out: waiter interrupted, flag now false. "
                  "Hold on to it.",
            2.6, ([Circumscribe(left[5], color=YELLOW_M, buff=0.08)], 1.4))
        self.play(FadeOut(VGroup(frame_, head, out)), run_time=0.6)

        # ---------------- the desk: interrupt as a note ----------------
        DY = 0.85                                     # desk top
        top = Rectangle(width=4.4, height=0.16).set_fill(GREY_D, 1).set_stroke(GREY_B, 1.5).move_to([-2.4, DY - 0.08, 0])
        legs = VGroup(Line([-4.3, DY - 0.16, 0], [-4.3, 0.05, 0]), Line([-0.5, DY - 0.16, 0], [-0.5, 0.05, 0])).set_stroke(GREY_B, 3)
        rc = clerk(RELAY, 1.3)
        rc.move_to([-2.4, 0, 0]).align_to(top, DOWN).shift(UP * 0.16)
        rc_l = T("the relay", 26, RELAY).move_to([-2.4, -0.25, 0])
        clk_c = np.array([-3.85, DY + 0.27, 0])
        clk = VGroup(Circle(radius=0.25, color=GREY_B, stroke_width=3).move_to(clk_c),
                     Line(clk_c, clk_c + UP * 0.18, stroke_width=3, color=WHITE),
                     Line(clk_c, clk_c + RIGHT * 0.13, stroke_width=3, color=WHITE))
        clk_l = M("sleep(200)", 22, GREY_A).next_to(clk, UP, buff=0.15)
        SPOT = np.array([-0.95, DY + 0.24, 0])
        st = M("TIMED_WAITING", 26, C_WAIT).move_to([-2.4, 3.0, 0])
        zz2 = T("z z z", 28, GREY_B).next_to(rc, UR, buff=0.0).shift(DOWN * 0.15)

        def nap():
            return [rc.animate.rotate(-12 * DEGREES, about_point=rc.get_bottom()), FadeIn(zz2, shift=UP * 0.15)]

        def wake():
            return [rc.animate.rotate(12 * DEGREES, about_point=rc.get_bottom()), FadeOut(zz2)]
        self.beat("And our relay spends nearly its whole life asleep. Honestly, relatable. "
                  "But it means a stop request has to reach it while it sleeps.",
                  FadeIn(VGroup(top, legs, rc, rc_l, clk, clk_l, st)), run_time=1.2)
        self.play(*nap(), run_time=0.6)
        mc = clerk(MAINC, 1.3).move_to([3.4, rc.get_y(), 0])
        mc_l = T("main", 26, MAINC).move_to([3.4, -0.25, 0])
        nt = note().move_to(mc.get_center() + LEFT * 0.7 + UP * 0.3)
        seq(self, "Java can't drag a thread away from its desk. It can only ask. relay.interrupt() is the asking.",
            ([FadeIn(mc, shift=LEFT * 0.2), FadeIn(mc_l)], 0.8), 3.0, ([FadeIn(nt, scale=0.6)], 0.6))
        seq(self, "Picture a note on the clerk's desk: please finish up.",
            ([mc.animate.shift(LEFT * 1.6), mc_l.animate.shift(LEFT * 1.6), nt.animate.move_to(SPOT)], 1.2))
        st_r = M("RUNNABLE", 26, C_RUN).move_to(st)
        seq(self, "If the clerk is napping, the note wakes them: sleep throws an InterruptedException. "
                  "If they're busy, they see it the next time they look up.",
            1.4, (lambda: wake() + [Transform(st, st_r), Wiggle(nt, scale_value=1.15)], 0.9))
        mw = M("WAITING in join()", 22, C_WAIT).next_to(mc_l, DOWN, buff=0.15)
        self.play(mc.animate.shift(RIGHT * 1.6), mc_l.animate.shift(RIGHT * 1.6), run_time=0.6)
        mw.next_to(mc_l, DOWN, buff=0.15)
        self.play(FadeIn(mw), run_time=0.4)

        # the catch block, and where the note went
        jl = ["try { Thread.sleep(idleMillis); }",
              "catch (InterruptedException e) {",
              '    System.err.println("relay interrupted, carrying on");',
              "}"]
        fl = ["try { Thread.sleep(idleMillis); }",
              "catch (InterruptedException e) {",
              "    Thread.currentThread().interrupt();   // put the note back",
              "    return;",
              "}"]
        jc, fc = code(jl, 24), code(fl, 24)
        jc.move_to([-5.6, -1.0, 0], aligned_edge=UL)
        fc.move_to(jc.get_corner(UL), aligned_edge=UL)
        kn = T("Java (Kotlin's version is the same)", 22, GREY_B).move_to([6.4, jc[0].get_y(), 0], aligned_edge=RIGHT)
        seq(self, "Here's the relay's catch block. The note wakes the relay, and it lands in the catch.",
            ([FadeIn(jc), FadeIn(kn)], 0.8), 1.6,
            ([Indicate(jc[1], color=YELLOW_M, scale_factor=1.04)], 1.0))
        self.beat("Is the note still on the desk?")
        think(self, 2.4)
        gone = T("flag now false", 24, RED_M).move_to(SPOT + UP * 0.5 + RIGHT * 0.3)
        seq(self, "No. Waking up tears the note off: sleep clears the flag before it throws. "
                  "That's the demo's line, flag now false.",
            ([nt.animate.shift(DOWN * 1.2 + RIGHT * 0.3).rotate(-40 * DEGREES).set_opacity(0)], 1.0), 2.4,
            ([FadeIn(gone, shift=UP * 0.1)], 0.6))
        outl = M("relay interrupted, carrying on", 22, GREY_A).move_to([2.6, 2.95, 0])
        st_t = M("TIMED_WAITING", 26, C_WAIT).move_to(st)
        seq(self, "So the relay prints, goes back to sleep, and nothing remembers the request.",
            ([Indicate(jc[2], color=RED_M, scale_factor=1.03), FadeIn(outl)], 1.0), 0.4,
            (lambda: nap() + [Transform(st, st_t), FadeOut(gone)], 0.8))

        # put it back
        self.remove(nt)
        nt = note().move_to(SPOT)
        seq(self, "Once you've caught the exception, you hold the only copy of the request. "
                  "So either let it travel up to your caller, or stick the note back on: "
                  "Thread.currentThread().interrupt(), then return.",
            3.4, ([FadeOut(jc[2:]), FadeIn(fc[2:]), FadeOut(outl)], 1.0), 1.2,
            ([Indicate(fc[2], color=GREEN_M, scale_factor=1.03)], 1.0))
        flag_l = T("the interrupt flag", 26, YELLOW_M).move_to(SPOT + RIGHT * 0.65, aligned_edge=LEFT)
        seq(self, "Put back, the note stays where the relay can see it. Its proper name is the interrupt flag.",
            ([FadeIn(nt, scale=1.3)], 0.8), 2.2, ([FadeIn(flag_l, shift=UP * 0.1)], 0.6))
        st_e = M("TERMINATED", 26, C_DIM).move_to(st)
        mw2 = M("RUNNABLE again", 22, C_RUN).move_to(mw)
        seq(self, "Now the relay sees the note, finishes the batch in hand, and returns. "
                  "TERMINATED at last, and main's join returns.",
            (lambda: wake() + [FadeOut(flag_l)], 0.8), 0.6,
            ([Indicate(nt, color=YELLOW_M, scale_factor=1.25)], 0.8), 0.6,
            ([FadeOut(rc, shift=LEFT * 0.6), FadeOut(rc_l), FadeOut(nt), Transform(st, st_e)], 1.0), 0.4,
            ([Transform(mw, mw2)], 0.6))
        self.beat("The relay goes home on time. Somebody in that mail room should.", run_time=0.8)
        self.play(FadeOut(VGroup(top, legs, clk, clk_l, st, mc, mc_l, mw, jc[:2], fc[2:], kn)), run_time=0.6)

        # ---------------- the code, Java and Kotlin, and the rule ----------------
        jf = code(["try { Thread.sleep(idleMillis); }",
                   "catch (InterruptedException e) {",
                   "    Thread.currentThread().interrupt();   // put the note back",
                   "    return;",
                   "}"], 24)
        kf = code(["try { Thread.sleep(idleMillis) }",
                   "catch (e: InterruptedException) {",
                   "    Thread.currentThread().interrupt()    // put the note back",
                   "    return",
                   "}"], 24)
        for b in (jf, kf):
            b[2].set_color(GREEN_M)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jf).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Kotlin", 24, GREY_B), kf).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.4)
        fit(cols, 12.4)
        cols.move_to(UP * 0.45)
        self.beat("Here is the fix in Java and in Kotlin. "
                  "Kotlin doesn't force you to catch this exception, so add the try on purpose.",
                  FadeIn(cols, shift=UP * 0.2), run_time=2.0)
        rule = T("Never swallow an interrupt. Rethrow it, or restore it.", 32, YELLOW_M)
        fit(rule, 12).move_to([0, cols.get_bottom()[1] - 0.55, 0])
        self.beat("The rule: never swallow an interrupt. Rethrow it, or restore it.",
                  FadeIn(rule, shift=UP * 0.15), run_time=1.0)
        self.wait(0.5)
        self.play(FadeOut(VGroup(cols, rule)), run_time=0.6)

        # ---------------- two more traps ----------------
        c1 = VGroup(T("A relay that's always busy never reaches sleep.", 28, WHITE),
                    VGroup(M("Thread.currentThread().isInterrupted()", 26, GREEN_M),
                           T("look for the note, once per batch", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        c2 = VGroup(T("The static one does two things at once.", 28, WHITE),
                    VGroup(M("Thread.interrupted()", 26, RED_M),
                           T("reads the note, and tears it off", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        cards = VGroup(c1, c2).arrange(DOWN, aligned_edge=LEFT, buff=0.8).move_to(UP * 0.3)
        same = T("the same calls in Java and in Kotlin", 22, GREY_B).next_to(cards, DOWN, buff=0.5).align_to(cards, LEFT)
        seq(self, "Two more traps. A relay that's always busy never reaches sleep, so no exception arrives. "
                  "It must look for the note itself, once per batch, with isInterrupted().",
            ([FadeIn(c1[0])], 0.6), 2.6, ([FadeIn(c1[1], shift=UP * 0.1), FadeIn(same)], 0.8))
        seq(self, "And the static Thread.interrupted() reads the note, and tears it off.",
            ([FadeIn(c2, shift=UP * 0.1)], 0.9))
        self.wait(0.4)
        self.play(FadeOut(VGroup(cards, same)), run_time=0.6)

        # ---------------- moral and check, on the map ----------------
        self.play(FadeIn(board), run_time=0.8)
        seq(self, "So where is a thread when it isn't running? In one of six places, and the call it made decides which. "
                  "And a stop request is a note on a desk. It's easy to lose, so put it back.",
            1.4, ([LaggedStart(*[Indicate(p[1], color=WHITE, scale_factor=1.12) for p in order], lag_ratio=0.15)], 2.4))
        chk = VGroup(T("A thread is inside", 28, YELLOW_M), M("wait(5_000)", 26, YELLOW_M),
                     T("Which place?", 28, YELLOW_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        chk.move_to([-6.4, 2.65, 0], aligned_edge=LEFT)
        self.beat("Quick check. A thread is inside wait, with a five second limit. Which place?",
                  FadeIn(chk, shift=DOWN * 0.1), run_time=1.0)
        think(self, 2.6, pos=(5.8, 2.4))
        self.beat("TIMED_WAITING. Same call, plus a time limit, and the thread moves to the other box.",
                  Circumscribe(tim[0], color=YELLOW_M, buff=0.08), Indicate(tim[1], color=YELLOW_M, scale_factor=1.2),
                  run_time=1.6)
        self.wait(1.0)
