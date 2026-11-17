from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"cancel\(true\)", "cancel true"), (r"\bThread\.stop\b", "Thread dot stop"),
    (r"\bInterruptedException\b", "Interrupted Exception"), (r"\bisCancelled\b", "is cancelled"),
    (r"\bisDone\b", "is done"), (r"\bTimeoutDemo\b", "Timeout Demo"), (r"\bCancelDemo\b", "Cancel Demo"),
    (r"\bpleaseStop\b", "please stop"),
]

# every spoken line, in order
N = {
    "counter": "Picture a takeaway counter. You order a burger, pay, and the cashier hands you a ticket with the number 42 on it. "
               "The burger doesn't exist yet. The ticket promises that it will, and lets you collect it.",
    "three": "With the ticket, you can do three things. Wait at the counter until 42 is called. "
             "Wait only five minutes, because your bus is coming. Or glance at the screen to see whether it's ready.",
    "map": "A thread pool hands out the same ticket. You give it a task with submit, and you get a Future back at once, "
           "a promise of a result that doesn't exist yet. get is the wait at the counter. "
           "get with a time limit is the five minutes before the bus. And isDone is the glance at the screen.",
    "bus": "Now say you give up after five minutes and catch your bus. Here's a question most of us never ask. "
           "What happens to the burger?",
    "burger": "Nobody tells the kitchen. At minute seven, it's ready. Hot, paid for, and nobody to eat it. "
              "Somewhere, a burger is having a very lonely evening.",
    "demo": "Java behaves the same way. The lesson's TimeoutDemo starts a task that takes 600 milliseconds, and waits only 200. "
            "main gives up at 285 milliseconds. The task never hears about it, and finishes at 771.",
    "rule1": "So the point is, a time limit ends your wait, not the work. If the work should stop, somebody has to say so.",
    "cancelq": "A Future has a method for that, cancel(true). So here's the question we're shy to ask. "
               "Does cancel(true) kill the task?",
    "stop": "It can't. Java has no safe way to kill a thread from outside. "
            "The old Thread.stop was marked don't use for decades, and JDK 26 removed it.",
    "note": "Here's what really happens. Picture the manager walking over to a cook's station and sticking a note on it. "
            "Please stop order 42. Then the manager walks away.",
    "mapnote": "Let's map it. The cook is the pool thread running your task. "
               "The note is an interrupt, a request to a thread to stop what it's doing. "
               "And the note on the station is the interrupt flag, a true or false value inside every thread. "
               "cancel(true) sets it to true, and that's all.",
    "cooks": "Whether a note works depends on the cook. Our kitchen has three. The first is waiting for the oven. "
             "The second is chopping onions, and looks up after each one. The third is chopping too, and never looks up.",
    "code3": "The lesson's CancelDemo builds all three. The first sleeps for five seconds. "
             "The second does 400 slices of arithmetic, and checks the flag before each slice. "
             "The third does the same 400 slices, and never checks.",
    "predq": "After 100 milliseconds, main calls cancel(true) on all three. Which ones stop?",
    "reveal": "The oven cook stops at once. A thread that waits, in sleep or on a queue, is woken by the note, "
              "with an InterruptedException. The checker sees the note the next time it looks up, after 51 slices, "
              "and returns. The third cook chops on, all 400 slices, and finishes 769 milliseconds after the cancel.",
    "focus": "Focus is a wonderful quality in a cook, and a terrible one in a task you're trying to stop. "
             "The note only works on a cook who waits, or who looks.",
    "tickets": "Now glance at the tickets. Right after the cancel, all three said cancelled and done. "
               "Even the third one, while its cook was still chopping. "
               "A Future changes its state the moment you call cancel. It doesn't wait for the task to stop. "
               "So that burger gets made anyway, under a ticket that says cancelled.",
    "breaks": "And here the kitchen picture breaks, twice. A real cook hears you shout across the room, "
              "but a thread hears nothing unless it waits or looks. "
              "And a real kitchen knows whether the dish was made. A cancelled Future doesn't.",
    "name": "This is called cooperative cancellation. It works only if the task helps. "
            "If I could rename cancel(true), I'd call it pleaseStop.",
    "timeout": "That's why the cancel run of TimeoutDemo worked. main gave up at 257 milliseconds, "
               "and the task stopped at 260. Its cook was waiting for the oven, in sleep.",
    "code": "So a long computing loop should look up now and then, like the checker. In Java and Kotlin, "
            "it's one check at the top of the loop. Is this thread interrupted? Then stop. "
            "Calls that wait, like sleep, already look for you.",
    "moral": "So, does cancel stop a task? It asks. A time limit ends your wait. cancel puts a note on the station. "
             "Only a cook who waits or looks up will read it, and the ticket can't tell you which.",
    "check": "Quick check. A task runs a computing loop that never checks the flag, and you call cancel(true). "
             "What does isCancelled return, and when does the task stop?",
    "check_a": "True, at once. And the task stops only when its loop ends.",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at()/at_text() wait for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def left(self, until=None):
        """Seconds from now to the start of sentence `until`, or to the end of the line."""
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
YOU, COOK, NOTE, PAPER, RULE = YELLOW_M, TEAL_M, RED_M, GREY_A, YELLOW_M
OVEN_C, CHECK_C, IGN_C = PURPLE_M, TEAL_M, GOLD_M
BUN, PATTY = "#C9935A", "#9A4A3A"


def person(color, s=1.0, op=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def cook(color=COOK, s=1.0):
    """A person with a white cook's hat."""
    p = person(color)
    band = Rectangle(width=0.26, height=0.08).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1)
    band.next_to(p[1], UP, buff=0.0)
    puff = Circle(radius=0.12).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1).next_to(band, UP, buff=-0.08)
    return VGroup(p[0], p[1], VGroup(puff, band)).scale(s)


def burger(s=1.0, op=1.0):
    top = Sector(radius=0.42, angle=PI).stretch(0.75, 1).set_stroke(BUN, 2).set_fill(dim(BUN, 0.6), 1)
    patty = RoundedRectangle(corner_radius=0.07, width=0.92, height=0.16).set_stroke(PATTY, 2).set_fill(dim(PATTY, 0.7), 1)
    bottom = RoundedRectangle(corner_radius=0.07, width=0.84, height=0.17).set_stroke(BUN, 2).set_fill(dim(BUN, 0.6), 1)
    g = VGroup(top, patty, bottom).arrange(DOWN, buff=0.03).scale(s)
    g.set_opacity(op)
    return g


def ticket(text="42", w=0.75, h=0.5, size=28):
    r = RoundedRectangle(corner_radius=0.05, width=w, height=h).set_stroke(PAPER, 2).set_fill(dim(PAPER, 0.22), 1)
    return VGroup(r, T(text, size).move_to(r))


def future_tag(state, color, w=3.0):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.5).set_stroke(PAPER, 2).set_fill(dim(PAPER, 0.18), 1)
    t = VGroup(T("ticket:", 22, GREY_A), M(state, 22, color)).arrange(RIGHT, buff=0.15).move_to(r)
    return VGroup(r, t)


def note(s=1.0):
    r = Rectangle(width=0.95, height=0.5).set_stroke(NOTE, 2).set_fill(dim(NOTE, 0.45), 1)
    return VGroup(r, T("stop 42", 20).move_to(r)).scale(s).set_z_index(6)


def station(x, y, w=3.0):
    return Rectangle(width=w, height=0.5).set_stroke(GREY_B, 2).set_fill(GREY_E, 1).move_to([x, y, 0])


def oven(color=OVEN_C):
    r = RoundedRectangle(corner_radius=0.06, width=0.95, height=0.75).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    win = RoundedRectangle(corner_radius=0.04, width=0.6, height=0.32).set_stroke(color, 1.5).set_fill(dim(color, 0.5), 1)
    win.move_to(r).shift(DOWN * 0.08)
    knobs = VGroup(*[Dot(radius=0.04, color=color) for _ in range(3)]).arrange(RIGHT, buff=0.12).move_to(r).shift(UP * 0.24)
    return VGroup(r, win, knobs)


def onions(color):
    g = VGroup(*[Circle(radius=0.12).set_stroke(color, 2).set_fill(dim(color, 0.3), 1) for _ in range(5)])
    g.arrange_in_grid(rows=2, cols=3, buff=0.05)
    knife = Line(LEFT * 0.25, RIGHT * 0.25, stroke_width=4, color=GREY_B).next_to(g, RIGHT, buff=0.1)
    return VGroup(g, knife)


def counter(fmt, fn, pos, size=24, color=WHITE, edge=ORIGIN):
    """Text that shows fmt.format(fn()); it changes in place with become()."""
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = T(fmt.format(n), size, color).move_to(pos, aligned_edge=edge)
        return cache[n]
    n0 = fn()
    holder = get(n0).copy()
    holder.shown = n0

    def upd(m):
        n = fn()
        if n != m.shown:
            m.become(get(n))
            m.shown = n
    holder.add_updater(upd)
    return holder


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Exec04Cancel(Narrated):
    """exec-04, section 1: a takeaway ticket is the Future; the burger nobody collects is a time limit that ends the
    wait, not the work (285 / 771 ms); cancel(true) is a manager's note on a cook's station, the interrupt flag; three
    cooks (oven, looks up, never looks up) at 100 ms: stops at once, after 51 slices, 769 ms later; every ticket says
    cancelled at once; cooperative cancellation; the cancel run (257 / 260 ms); the checking loop in Java and Kotlin."""

    def construct(self):
        self.title_card("Ticket 42", "what a time limit and cancel(true) really do to a task")

        # ================= the takeaway counter =================
        you = person(YOU, 1.0).move_to([-5.2, -0.35, 0])
        you_l = T("you", 24, YOU).next_to(you, DOWN, buff=0.15)
        desk = Rectangle(width=2.2, height=0.5).set_stroke(GREY_B, 2).set_fill(GREY_E, 1).move_to([-2.3, -0.5, 0])
        cashier = person(GREY_B, 0.9).next_to(desk, UP, buff=0.0)
        desk_l = T("counter", 22, GREY_B).next_to(desk, DOWN, buff=0.15)
        screen = RoundedRectangle(corner_radius=0.06, width=1.9, height=0.6).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
        screen.move_to([-2.3, 1.55, 0])
        scr_t = T("42: cooking", 22, GREY_A).move_to(screen)
        kitchen = RoundedRectangle(corner_radius=0.15, width=4.6, height=3.0).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)
        kitchen.move_to([3.8, 0.35, 0])
        k_lab = T("kitchen", 26, GREY_A).next_to(kitchen, UP, buff=0.15)
        k_cook = cook(COOK, 1.0).move_to([2.6, 0.3, 0])
        grill = Rectangle(width=1.6, height=0.4).set_stroke(GREY_B, 2).set_fill(GREY_E, 1).move_to([4.4, -0.35, 0])
        ghost = DashedVMobject(burger(1.0)[0].copy().set_fill(opacity=0), num_dashes=14).set_stroke(GREY_B, 2)
        ghost = VGroup(ghost, DashedVMobject(burger(1.0)[2].copy().set_fill(opacity=0), num_dashes=10).set_stroke(GREY_B, 2))
        ghost.arrange(DOWN, buff=0.22).next_to(grill, UP, buff=0.12)
        tk = ticket().move_to(cashier.get_center() + DOWN * 0.05).set_z_index(3)
        self.say("counter")
        self.play(FadeIn(you), FadeIn(you_l), FadeIn(desk), FadeIn(cashier), FadeIn(desk_l),
                  FadeIn(kitchen), FadeIn(k_lab), FadeIn(k_cook), FadeIn(grill), run_time=1.0)
        self.at(1)
        self.play(FadeIn(tk, scale=0.6), run_time=0.4)
        self.play(tk.animate.move_to(you.get_center() + RIGHT * 0.75 + UP * 0.05), run_time=1.0)
        self.at(2)
        self.play(Create(ghost), run_time=1.0)
        self.at(3)
        self.play(Indicate(tk, color=WHITE, scale_factor=1.15), run_time=0.9)
        self.hold()

        rows = VGroup(T("1. wait until 42 is called", 26), T("2. wait five minutes, then the bus", 26),
                      T("3. glance at the screen", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        rows.move_to([-6.2, -2.45, 0], aligned_edge=LEFT)
        self.say("three")
        self.at(1)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rows[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[2], shift=UP * 0.1), FadeIn(screen), FadeIn(scr_t), run_time=0.6)
        self.hold()

        pool_l = T("thread pool", 26, COOK).move_to(k_lab)
        cook_l = T("pool thread", 22, COOK).next_to(k_cook, DOWN, buff=0.15)
        sub = M("pool.submit(task)", 24, WHITE).move_to([-2.3, 2.55, 0])
        fut = M("Future", 24, PAPER).next_to(tk, UP, buff=0.15)
        codes = VGroup(M("get()", 24, YOU), M("get(200, MILLISECONDS)", 24, YOU), M("isDone()", 24, YOU))
        for c, r in zip(codes, rows):
            c.move_to([1.2, r.get_y(), 0], aligned_edge=LEFT)
        arrows = VGroup(*[Arrow([0.2, r.get_y(), 0], [1.05, r.get_y(), 0], buff=0, stroke_width=3, color=GREY_B,
                                max_tip_length_to_length_ratio=0.3) for r in rows])
        self.say("map")
        self.play(Transform(k_lab, pool_l), FadeIn(cook_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(sub, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(fut, shift=UP * 0.1), Indicate(tk, color=WHITE, scale_factor=1.1), run_time=0.8)
        for i in range(3):
            self.at(i + 2)
            self.play(GrowArrow(arrows[i]), FadeIn(codes[i], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        # ================= the bus =================
        self.play(FadeOut(VGroup(rows, codes, arrows, sub, screen, scr_t)), run_time=0.5)
        bus = VGroup(RoundedRectangle(corner_radius=0.18, width=2.6, height=0.95).set_stroke(GREY_A, 3).set_fill(GREY_E, 1))
        bus.add(*[Square(0.3).set_stroke(GREY_A, 2).set_fill(BLACK, 1).move_to([-0.9 + 0.45 * k, 0.15, 0]) for k in range(5)])
        bus.add(*[Circle(radius=0.15).set_stroke(GREY_A, 3).set_fill(BLACK, 1).move_to([x, -0.48, 0]) for x in (-0.75, 0.75)])
        bus.move_to([-9.0, -2.3, 0])
        clock5 = T("minute 5", 30, YOU).move_to([-2.3, 2.3, 0])
        q = T("What happens to the burger?", 32, RULE).move_to([0, -3.1, 0])
        self.say("bus")
        self.play(FadeIn(clock5), run_time=0.5)
        self.play(bus.animate.move_to([-4.9, -2.3, 0]), run_time=1.2)
        self.play(VGroup(you, tk, fut).animate.move_to([-4.9, -2.1, 0]).scale(0.6), FadeOut(you_l), run_time=0.8)
        self.play(VGroup(bus, you, tk, fut).animate.shift(LEFT * 4.5), run_time=1.0, rate_func=rush_into)
        self.remove(bus, you, tk, fut)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        bg = burger(1.0).move_to(ghost)
        clock7 = T("minute 7", 30, YOU).move_to(clock5)
        steam = VGroup(*[FunctionGraph(lambda t: 0.06 * np.sin(6 * t), x_range=[0, 0.5]).rotate(PI / 2).set_stroke(GREY_B, 2)
                         .move_to(bg.get_top() + UP * 0.35 + RIGHT * dx) for dx in (-0.22, 0, 0.22)])
        tag42 = ticket("42", 0.6, 0.4, 22).next_to(bg, RIGHT, buff=0.2)
        empty = DashedVMobject(person(YOU, 1.0)[0].copy().set_fill(opacity=0), num_dashes=16).set_stroke(GREY_B, 2)
        empty.move_to([-5.2, -0.5, 0])
        nobody = T("nobody", 24, GREY_B).next_to(empty, DOWN, buff=0.15)
        self.say("burger")
        self.play(FadeOut(q), run_time=0.3)
        self.at(1)
        self.play(Transform(clock5, clock7), FadeOut(ghost), FadeIn(bg, scale=0.8), FadeIn(tag42), run_time=0.9)
        self.play(Create(steam), run_time=0.6)
        self.at(2)
        self.play(FadeIn(empty), FadeIn(nobody), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(desk, cashier, desk_l, kitchen, k_lab, k_cook, cook_l, grill, bg, steam, tag42, empty,
                                 nobody, clock5)), run_time=0.6)

        # ================= TimeoutDemo on a timeline =================
        X0, X1 = -2.6, 6.0
        PX = (X1 - X0) / 800

        def tx(ms):
            return X0 + ms * PX
        MY, KY, AY = 1.6, 0.0, -1.2
        m_l = VGroup(T("main", 28, YOU), M("get(200 ms)", 22, YOU)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        m_l.move_to([-6.3, MY, 0], aligned_edge=LEFT)
        k_l = VGroup(T("pool thread", 28, COOK), T("a 600 ms task", 22, COOK)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        k_l.move_to([-6.3, KY, 0], aligned_edge=LEFT)
        def make_axis():
            a = Line([tx(0), AY, 0], [tx(800), AY, 0], stroke_width=2, color=GREY_B)
            t = VGroup(*[VGroup(Line([tx(m), AY + 0.07, 0], [tx(m), AY - 0.07, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([tx(m), AY - 0.32, 0])) for m in (0, 200, 400, 600, 800)])
            return a, t
        axis, ticks = make_axis()

        def bar(a, b, y, color):
            return Rectangle(width=(b - a) * PX, height=0.5, stroke_color=color, stroke_width=2.5).set_fill(dim(color, 0.3), 1) \
                .move_to([tx((a + b) / 2), y, 0])
        mb = bar(0, 285, MY, YOU)
        kb = bar(86, 771, KY, COOK)
        cur = Line([0, MY + 0.45, 0], [0, KY - 0.45, 0], stroke_width=3, color=WHITE)
        tt = ValueTracker(0.0)
        cur.add_updater(lambda m: m.set_x(tx(tt.get_value())))
        m_part = mb.copy()
        k_part = kb.copy().stretch_to_fit_width(0.01, about_edge=LEFT)
        gave = T("gave up: 285 ms", 24, YOU).next_to(mb, UP, buff=0.12).align_to(mb, RIGHT).shift(RIGHT * 0.9)
        done = T("finished: 771 ms", 24, COOK).next_to(kb, DOWN, buff=0.12).align_to(kb, RIGHT)
        self.say("demo")
        self.play(FadeIn(m_l), FadeIn(k_l), FadeIn(axis), FadeIn(ticks), run_time=0.8)
        self.add(cur)
        self.at(1)
        self.play(GrowFromEdge(m_part, LEFT, rate_func=linear), tt.animate(rate_func=linear).set_value(285),
                  UpdateFromAlphaFunc(k_part, lambda m, a: m.become(kb.copy().stretch_to_fit_width(
                      max(0.01, (min(285, max(86, 285 * a)) - 86) * PX), about_edge=LEFT).align_to(kb, LEFT))),
                  run_time=self.left(2))
        self.play(FadeIn(gave, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(tt.animate(rate_func=linear).set_value(771),
                  UpdateFromAlphaFunc(k_part, lambda m, a: m.become(kb.copy().stretch_to_fit_width(
                      (285 - 86 + (771 - 285) * a) * PX, about_edge=LEFT).align_to(kb, LEFT))),
                  run_time=2.2)
        self.play(FadeIn(done, shift=DOWN * 0.1), FadeOut(cur), run_time=0.5)
        cur.clear_updaters()
        self.hold()
        rule1 = T("A time limit ends your wait, not the work.", 34, RULE).move_to([0, -2.6, 0])
        self.say("rule1")
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.8)
        self.hold()
        tl = VGroup(m_l, k_l, axis, ticks, m_part, k_part, gave, done)
        self.play(FadeOut(tl), FadeOut(rule1), run_time=0.6)

        # ================= cancel(true): does it kill? =================
        cc = M("future.cancel(true)", 34, YOU).move_to([0, 2.2, 0])
        kq = T("Does it kill the task?", 34, RULE).move_to([0, 1.2, 0])
        self.say("cancelq")
        self.play(FadeIn(cc, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        nos = T("No safe way to kill a thread from outside.", 30).move_to([0, 0.0, 0])
        st = M("Thread.stop()", 30, GREY_B).move_to([0, -1.2, 0])
        strike = Line(st.get_left() + LEFT * 0.12, st.get_right() + RIGHT * 0.12, stroke_width=4, color=NOTE)
        st_n = T("\"don't use\" for decades, removed in JDK 26", 24, GREY_B).next_to(st, DOWN, buff=0.2)
        self.say("stop")
        self.at(1)
        self.play(FadeIn(nos, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(st), run_time=0.5)
        self.play(Create(strike), FadeIn(st_n), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(kq, nos, st, strike, st_n)), cc.animate.move_to([-4.3, 2.6, 0]).scale(0.8), run_time=0.7)

        # ================= the manager's note =================
        mgr = person(YOU, 1.0).move_to([-4.3, 0.6, 0])
        mgr_l = T("manager", 24, YOU).next_to(mgr, DOWN, buff=0.15)
        stn = station(2.6, -0.4, 3.4)
        c1 = cook(COOK, 1.0).next_to(stn, UP, buff=0.0).shift(LEFT * 0.7)
        on1 = onions(COOK).scale(0.9).next_to(stn, UP, buff=0.05).shift(RIGHT * 0.65)
        n1 = note().move_to(mgr.get_right() + RIGHT * 0.6)
        N_ON = stn.get_center() + RIGHT * 0.9
        self.say("note")
        self.play(FadeIn(mgr), FadeIn(mgr_l), FadeIn(stn), FadeIn(c1), FadeIn(on1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(n1, scale=0.6), run_time=0.4)
        self.play(n1.animate(path_arc=-0.6).move_to(N_ON), VGroup(mgr, mgr_l).animate.shift(RIGHT * 1.6), run_time=1.4)
        self.at(3)
        self.play(VGroup(mgr, mgr_l).animate.shift(LEFT * 1.6), run_time=1.0)
        self.hold()

        lab_c = T("cook = pool thread", 24, COOK).next_to(c1, UP, buff=0.2)
        lab_n = T("note = interrupt", 24, NOTE).next_to(stn, DOWN, buff=0.2).set_x(N_ON[0])
        flag = VGroup(T("interrupt flag:", 26), M("false", 26, GREY_B)).arrange(RIGHT, buff=0.2).move_to([2.6, -2.1, 0])
        flag_t = M("true", 26, NOTE).move_to(flag[1], aligned_edge=LEFT)
        only = T("nothing else happens", 24, GREY_B).next_to(flag, DOWN, buff=0.2)
        self.say("mapnote")
        self.at(1)
        self.play(FadeIn(lab_c, shift=UP * 0.1), Indicate(c1[0], color=COOK, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(lab_n, shift=UP * 0.1), Indicate(n1[1], color=WHITE, scale_factor=1.15), run_time=0.8)
        self.at(3)
        self.play(n1.animate.shift(UP * 1.3 + RIGHT * 1.3).set_opacity(0.35), run_time=0.6)
        self.play(FadeIn(flag), run_time=0.5)
        self.at(4)
        self.play(n1.animate.move_to(N_ON).set_opacity(1), Transform(flag[1], flag_t), run_time=0.8)
        self.play(FadeIn(only), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(mgr, mgr_l, stn, c1, on1, n1, lab_c, lab_n, flag, only, cc)), run_time=0.6)

        # ================= three cooks =================
        CX = [-4.4, 0.0, 4.4]
        COLS = [OVEN_C, CHECK_C, IGN_C]
        SY = 0.55
        stns = [station(x, SY, 3.4) for x in CX]
        cks = [cook(c, 0.95).next_to(s, UP, buff=0.0).shift(LEFT * 0.8) for c, s in zip(COLS, stns)]
        props = [oven().next_to(stns[0], UP, buff=0.0).shift(RIGHT * 0.6),
                 onions(CHECK_C).scale(0.9).next_to(stns[1], UP, buff=0.05).shift(RIGHT * 0.6),
                 onions(IGN_C).scale(0.9).next_to(stns[2], UP, buff=0.05).shift(RIGHT * 0.6)]
        names = [T(t, 24, c).next_to(s, DOWN, buff=0.18) for t, c, s in
                 zip(["waits for the oven", "looks up after each one", "never looks up"], COLS, stns)]
        CODE_Y = -0.6
        codes3 = [M("Thread.sleep(5_000)", 22, OVEN_C).move_to([CX[0], CODE_Y, 0]),
                  T("400 slices, checks the flag", 22, GREY_A).move_to([CX[1], CODE_Y, 0]),
                  T("400 slices, never checks", 22, GREY_A).move_to([CX[2], CODE_Y, 0])]
        sl = {1: ValueTracker(0), 2: ValueTracker(0)}
        CNT_Y = -1.3
        cnts = {k: counter("slices done: {}", (lambda k=k: int(round(sl[k].get_value()))), [CX[k], CNT_Y, 0], 24, COLS[k])
                for k in (1, 2)}
        asleep = T("asleep, 5 s timer", 24, OVEN_C).move_to([CX[0], CNT_Y, 0])
        tks = [future_tag("RUNNING", GREY_A).move_to([x, -2.85, 0]) for x in CX]
        self.say("cooks")
        self.at(1)
        self.play(*[FadeIn(s) for s in stns], run_time=0.6)
        for i in range(3):
            self.at(i + 2)
            self.play(FadeIn(cks[i], shift=UP * 0.1), FadeIn(props[i]), FadeIn(names[i]), run_time=0.7)
        self.hold()

        self.say("code3")
        self.at(1)
        self.play(FadeIn(codes3[0]), FadeIn(asleep), run_time=0.6)
        self.at(2)
        self.play(FadeIn(codes3[1]), FadeIn(cnts[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(codes3[2]), FadeIn(cnts[2]), run_time=0.6)
        self.play(*[FadeIn(t, shift=UP * 0.1) for t in tks], run_time=0.6)
        self.hold()

        boss = person(YOU, 0.85).move_to([-0.9, 2.95, 0])
        boss_l = M("main: cancel(true) on all three", 24, YOU).next_to(boss, RIGHT, buff=0.3)
        notes = [note(0.85).move_to(boss.get_center()) for _ in range(3)]
        NPOS = [s.get_center() + RIGHT * 0.05 for s in stns]
        tks_c = [future_tag("CANCELLED", NOTE).move_to(t) for t in tks]
        self.say("predq")
        self.play(FadeIn(boss), FadeIn(boss_l), sl[1].animate(rate_func=linear).set_value(51),
                  sl[2].animate(rate_func=linear).set_value(51), run_time=self.left(1) - 1.1)
        for n in notes:
            self.add(n)
        self.play(*[n.animate(path_arc=0.4 * (1 - k)).move_to(p) for k, (n, p) in enumerate(zip(notes, NPOS))],
                  *[Transform(a, b) for a, b in zip(tks, tks_c)], run_time=1.0)
        self.hold(after=0)
        self.predict(2.4)

        exc = T("InterruptedException", 24, NOTE).move_to([CX[0], CNT_Y, 0])
        o1 = T("stops at once", 24, OVEN_C).move_to([CX[0], -1.85, 0])
        look = DashedLine(cks[1][1].get_top() + UP * 0.05, notes[1].get_top() + UP * 0.05, dash_length=0.08, stroke_width=2.5,
                          color=CHECK_C).set_z_index(7)
        o2 = T("saw it after 51: returns", 24, CHECK_C).move_to([CX[1], -1.85, 0])
        o3 = T("769 ms after the cancel", 24, IGN_C).move_to([CX[2], -1.85, 0])
        self.say("reveal")
        self.play(Indicate(props[0][1], color=NOTE, scale_factor=1.15), run_time=0.6)
        self.play(ReplacementTransform(notes[0], exc), FadeOut(asleep), FadeIn(o1), run_time=0.8)
        self.at(2)
        self.play(Create(look), cks[1][1].animate.shift(UP * 0.06), run_time=0.7)
        self.play(FadeIn(o2), run_time=0.5)
        self.at(3)
        self.play(sl[2].animate(rate_func=linear).set_value(400), Wiggle(props[2][1], scale_value=1.1, n_wiggles=12),
                  run_time=self.left() - 0.7)
        self.play(FadeIn(o3), run_time=0.5)
        self.hold()

        top_f = T("The note only works on a cook who waits, or who looks.", 28, RULE).move_to([0, 2.95, 0])
        self.say("focus")
        self.play(Indicate(cks[2], color=IGN_C, scale_factor=1.1), run_time=1.0)
        self.at(1)
        self.play(FadeOut(VGroup(boss, boss_l)), FadeIn(top_f, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        out = M("after cancel: isCancelled=true/true/true isDone=true/true/true", 22, GREY_A).move_to([0, 2.95, 0])
        self.say("tickets")
        self.play(FadeOut(top_f), Indicate(VGroup(*tks), color=NOTE, scale_factor=1.05), run_time=1.0)
        self.at(1)
        self.play(FadeIn(out, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(VGroup(tks[2], cks[2]), color=IGN_C, scale_factor=1.06), run_time=1.0)
        self.at(5)
        b3 = burger(0.6).next_to(stns[2], UP, buff=0.05).shift(RIGHT * 0.6)
        self.play(FadeOut(props[2]), FadeIn(b3, scale=0.7), Indicate(tks[2], color=NOTE, scale_factor=1.08), run_time=1.0)
        self.hold()
        kitchen3 = VGroup(*stns, *cks, props[0], props[1], b3, *names, *codes3, cnts[1], cnts[2], *tks, exc, notes[1], notes[2],
                          o1, o2, o3, look, out)
        for c in cnts.values():
            c.clear_updaters()
        self.play(FadeOut(kitchen3), run_time=0.7)

        # ================= where the picture breaks =================
        r1 = VGroup(T("A real cook hears you shout across the room.", 28, GREY_A),
                    T("A thread hears nothing unless it waits or looks.", 28, COOK)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        r2 = VGroup(T("A real kitchen knows whether the dish was made.", 28, GREY_A),
                    T("A cancelled Future doesn't.", 28, COOK)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        tbl = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([0, 1.0, 0])
        hd = T("Where the kitchen picture breaks", 30, RULE).move_to([0, 3.0, 0])
        sep = VGroup()
        self.say("breaks")
        self.play(FadeIn(hd), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r1[0]), run_time=0.5)
        self.at_text("but a thread", lead=0.3)
        self.play(FadeIn(r1[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r2[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r2[1]), run_time=0.5)
        self.hold()

        self.play(FadeOut(VGroup(hd, r1, r2)), run_time=0.6)
        nm = T("cooperative cancellation", 40, RULE).move_to([0, 1.8, 0])
        nm_s = T("it works only if the task helps", 26, GREY_A).next_to(nm, DOWN, buff=0.2)
        ren = VGroup(M("cancel(true)", 32, YOU), T("could be called", 26, GREY_A), M("pleaseStop()", 32, RULE)).arrange(RIGHT, buff=0.35)
        ren.move_to([0, -0.6, 0])
        ren_n = T("(not a real method)", 22, GREY_B).next_to(ren[2], DOWN, buff=0.15)
        self.say("name")
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nm_s), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ren[0]), run_time=0.5)
        self.at_text("I'd call", lead=0.3)
        self.play(FadeIn(ren[1]), FadeIn(ren[2], shift=LEFT * 0.1), FadeIn(ren_n), run_time=0.7)
        self.hold(after=0.6)

        # ================= the cancel run of TimeoutDemo =================
        self.play(FadeOut(VGroup(ren, ren_n, nm, nm_s)), run_time=0.5)
        mb2 = bar(0, 257, MY, YOU)
        kb2 = bar(60, 260, KY, COOK)
        n_hit = note(0.7).move_to([tx(257), MY, 0])
        gave2 = T("gave up: 257 ms", 24, YOU).next_to(mb2, UP, buff=0.12).align_to(mb2, RIGHT).shift(RIGHT * 0.9)
        stop2 = T("stopped: 260 ms, it was waiting in sleep", 24, COOK).next_to(kb2, DOWN, buff=0.12).align_to(kb2, LEFT)
        k_l2 = VGroup(T("pool thread", 28, COOK), T("the oven cook", 22, OVEN_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        k_l2.move_to([-6.3, KY, 0], aligned_edge=LEFT)
        m_l2 = VGroup(T("main", 28, YOU), M("cancel(true)", 22, YOU)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        m_l2.move_to([-6.3, MY, 0], aligned_edge=LEFT)
        axis, ticks = make_axis()
        self.say("timeout")
        self.play(FadeIn(m_l2), FadeIn(k_l2), FadeIn(axis), FadeIn(ticks), run_time=0.7)
        self.at(1)
        self.play(GrowFromEdge(mb2, LEFT), GrowFromEdge(kb2, LEFT), run_time=1.0)
        self.play(FadeIn(gave2), FadeIn(n_hit, scale=0.6), run_time=0.5)
        self.play(n_hit.animate.move_to([tx(260) + 0.5, KY, 0]), run_time=0.6)
        self.play(FadeIn(stop2, shift=DOWN * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(mb2, kb2, n_hit, gave2, stop2, k_l2, m_l2, axis, ticks)), run_time=0.6)

        # ================= the guardrail: look up now and then =================
        jsrc = ["void chop() {", "    Thread me = Thread.currentThread();", "    for (int s = 0; s < 400; s++) {",
                "        if (me.isInterrupted()) return;", "        x = slice(x);", "    }", "}"]
        ksrc = ["fun chop() {", "    val me = Thread.currentThread()", "    for (s in 0 until 400) {",
                "        if (me.isInterrupted) return", "        x = slice(x)", "    }", "}"]
        jc, kc = code_block(jsrc, 22), code_block(ksrc, 22)
        jc[3].set_color(CHECK_C)
        kc[3].set_color(CHECK_C)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        cols = VGroup(jcol, kcol).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        fit(cols, 12.8).move_to([0, 0.75, 0])
        note2 = T("calls that wait, like sleep, look at the flag for you", 26, GREY_A).move_to([0, -2.2, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[3], kc[3]), color=CHECK_C, scale_factor=1.04), run_time=1.0)
        self.at(3)
        self.play(FadeIn(note2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cols, note2)), run_time=0.6)

        # ================= the moral and a check =================
        mo = VGroup(T("A time limit ends your wait, not the work.", 32),
                    T("cancel(true) only puts a note on the station.", 32),
                    T("Only a cook who waits or looks up will read it.", 32, RULE)).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        fit(mo, 12.4)
        self.say("moral")
        for i in range(3):
            self.at(i + 2)
            self.play(FadeIn(mo[i], shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, RULE), T("a loop that never checks the flag, then cancel(true).", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("What does isCancelled() return, and when does the task stop?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.18)
        fit(qg, 12.4).move_to(DOWN * 0.7)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("true, at once. The task stops only when its loop ends.", 30, GOLD_M).move_to(DOWN * 2.1)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
