from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bThreadLocal\b", "Thread Local"), (r"\bContextDemo\b", "Context Demo"), (r"\bMetricsDemo\b", "Metrics Demo"),
    (r"\bDeadlockDemo\b", "Deadlock Demo"), (r"\bnewFixedThreadPool\b", "new Fixed Thread Pool"),
    (r"\bthenApply\b", "then apply"), (r"\breq-(\d+)\b", r"request \1"), (r"\bgrill-(\d)\b", r"grill \1"),
    (r"\bpool-3-thread-7\b", "pool 3 thread 7"), (r"\b1\.2\b", "one point two"),
]

# every spoken line, in order
N = {
    "shyq": "Here's a question we rarely ask. Every thread in a pool is busy. Is that good news, or bad news?",
    "sat": "Picture the kitchen on a Saturday night, when orders stop coming out. Which cook is stuck? "
           "They all wear the same white jacket. Which table was the burned dish for? The note stayed with the waiter. "
           "How long has the rail been this full? Nobody kept count. "
           "And at closing, the lights go off with two dishes still in the oven.",
    "sat2": "A thread pool meets the same questions, and its defaults answer none of them.",
    "names": "First, name tags. A thread dump is a snapshot of every thread in a running program: its name, its state, "
             "and the line it's on. The ready-made pools name their threads like pool-3-thread-7. "
             "In a dump with eight pools, that tells you as much as a white jacket.",
    "names2": "So give the pool a thread factory, the object it asks for new threads, that names them after the work: "
              "grill-0, grill-1.",
    "note": "Second, the note. A request id is a short label, like req-42, that a program prints on every log line about one request. "
            "Programs often keep it in a ThreadLocal, a variable with a separate value for each thread. "
            "Picture a note pinned to the waiter's jacket instead of clipped to the order.",
    "note_q": "ContextDemo has a pool of one thread. main sets req-42, then submits three tasks. "
              "What does the first, plain task see?",
    "note_a": "null. The note stayed on main's jacket. And the third task sees req-7, "
              "an old note that an earlier task left pinned to the worker. "
              "Now every log line blames request 7, which went home long ago and did nothing wrong.",
    "note_fix": "The fix: copy the note onto the ticket at the hand-off, pin it on whichever cook takes it, "
                "and take it off when the dish leaves. In code: capture, install, and restore in finally.",
    "note_break": "Here the picture breaks. A paper note falls off sooner or later. "
                  "A ThreadLocal stays on its thread until code removes it. So a ThreadLocal belongs to a thread, not to a task.",
    "board": "Third, the board by the pass. Four numbers tell you most of what you need. The queue size: tickets on the rail. "
             "The active count: busy cooks, against the most you can have. Rejections: orders turned away, which you count yourself. "
             "And time in queue: how long each ticket waited for a cook.",
    "board_q": "MetricsDemo sends 10 tasks of 300 milliseconds to a pool of two threads, named orders, "
               "with room for four on the rail. Predict the first row of the board.",
    "board_a": "Two active, four queued, four rejected at once, because two plus four is all it can hold. "
               "Then every 300 milliseconds two more finish. The queue goes four, two, zero, and done climbs to six.",
    "board_fixed": "Run the same burst on newFixedThreadPool, whose rail has no end, and rejected says zero. "
                   "The last two tickets wait 1.2 seconds before a cook even looks at them. Only time in queue shows it.",
    "board_rule": "So watch the queue, not just the threads, and count every rejection. "
                  "A pool with an empty queue and no rejections is healthy, however busy its cooks look.",
    "freeze_q": "Now a board where everything froze. All threads active, the queue full and not moving, nothing done, "
                "and the CPU idle. What happened?",
    "freeze": "At closing, a job prints every table's bill. Each bill task submits a fetch of that table's orders to the same pool, "
              "and waits for it. With 20 threads and 400 tables, the first 20 bills take every thread, "
              "and their 20 fetches queue behind 380 bills.",
    "freeze2": "In the kitchen, every cook has pinned a ticket at the back of the rail and stands waiting for it. "
               "No cook is left to take it. Nothing throws, and nothing will ever finish. "
               "It's the politest jam a kitchen ever had: everyone waiting, nobody complaining, and no error to read.",
    "freeze_name": "That's pool-induced deadlock: every thread in a bounded pool waits for a task queued in that same pool. "
                   "DeadlockDemo's smallest case shows it on two threads: active two, queued two, completed zero, forever.",
    "freeze_fix": "The fixes: don't wait inside the pool, compose with thenApply instead. Or fetch inline, in the same task. "
                  "Or give each stage its own pool.",
    "close": "Last, closing time. A good restaurant locks the front door first, then finishes its orders, "
             "upstream stations first, all before a deadline.",
    "close2": "In code: stop taking requests. Shut down the kitchen pool before the billing pool it feeds. "
              "Give the whole thing one deadline inside the 30 second grace period. And whatever didn't finish, log it.",
    "close_joke": "Do it backwards, and billing closes first. The dishes still cooking get cooked and served, and never billed. "
                  "A free dinner nobody planned.",
    "moral": "So, is a pool with every thread busy good news? It depends on the board. "
             "Name the cooks, clip the note to the ticket, and watch the queue and the rejections. "
             "And never let a cook wait for a ticket behind him.",
    "check": "Quick check. The board says: active two of two, queued two, done zero, and the CPU is idle. Busy, or stuck?",
    "check_a": "Stuck. Nothing finishes. Look for a task that waits on another task in its own pool.",
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

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
COOK, WAITER, NOTE, PAPER, RULE, BAD, GOOD, FETCH = TEAL_M, YELLOW_M, GOLD_M, GREY_A, YELLOW_M, RED_M, GREEN_M, PURPLE_M


def person(color, s=1.0, op=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def cook(color=COOK, s=1.0):
    p = person(color)
    band = Rectangle(width=0.26, height=0.08).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1)
    band.next_to(p[1], UP, buff=0.0)
    puff = Circle(radius=0.12).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1).next_to(band, UP, buff=-0.08)
    return VGroup(p[0], p[1], VGroup(puff, band)).scale(s)


def ticket(text="", w=0.8, h=0.5, size=20, color=PAPER):
    r = RoundedRectangle(corner_radius=0.05, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.25), 1)
    g = VGroup(r)
    if text:
        g.add(T(text, size).move_to(r))
    return g.set_z_index(3)


def note(text, color=NOTE, size=20):
    t = T(text, size, WHITE)
    r = Rectangle(width=t.width + 0.22, height=t.height + 0.18).set_stroke(color, 2).set_fill(dim(color, 0.5), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def name_tag(text, color=COOK, size=18):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.04, width=t.width + 0.16, height=t.height + 0.14).set_stroke(color, 1.5).set_fill(dim(color, 0.4), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def panel(w, h, title):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(GREY_D, 2)
    t = T(title, 24, RULE).move_to(r.get_top() + DOWN * 0.3)
    return VGroup(r, t)


def oven(w=1.2, h=0.9, color=GREY_B):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.15), 1)
    win = RoundedRectangle(corner_radius=0.05, width=w * 0.7, height=h * 0.45).set_stroke(color, 2).move_to(r.get_center() + DOWN * 0.08)
    knobs = VGroup(*[Dot(radius=0.04, color=color).move_to(r.get_top() + DOWN * 0.13 + RIGHT * dx) for dx in (-0.25, 0, 0.25)])
    return VGroup(r, win, knobs)


def rail(x0, x1, y):
    return Line([x0, y, 0], [x1, y, 0]).set_stroke(GREY_B, 7)


def cross(m, s=0.25, color=BAD):
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(color, 5).move_to(m)


def board_box(w, h):
    return RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)


class Exec09Production(Narrated):
    """exec-09, section 2 (with the other sections as the evening around it): a stuck Saturday night; name tags (named
    thread factory); a note pinned to the waiter's jacket (ContextDemo: null, req-42, req-7; capture, install, restore);
    the board by the pass (queue, active, rejections, time in queue; MetricsDemo rows; a fixed pool shows rejected 0);
    the frozen board: cooks waiting for tickets behind them (20 threads, 400 tables; DeadlockDemo 2/2/0); closing in order."""

    def construct(self):
        self.title_card("A stuck Saturday night", "names, context, the board, deadlock and closing time")

        # ================= the shy question =================
        pool = RoundedRectangle(corner_radius=0.15, width=6.0, height=2.2).set_stroke(GREY_B, 2.5).move_to([0, 0.9, 0])
        pcs = VGroup(*[cook(COOK, 1.0) for _ in range(4)]).arrange(RIGHT, buff=0.8).move_to(pool.get_center() + UP * 0.15)
        busy = VGroup(*[T("busy", 22, COOK).next_to(c_, DOWN, buff=0.12) for c_ in pcs])
        q = T("Good news, or bad news?", 34, RULE).move_to([0, -1.2, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(pool), FadeIn(pcs), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(b_) for b_ in busy], lag_ratio=0.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(pool, pcs, busy, q)), run_time=0.5)

        # ================= Saturday night: four questions =================
        PW, PH = 6.4, 2.75
        pos = [np.array([-3.35, 1.55, 0]), np.array([3.35, 1.55, 0]), np.array([-3.35, -1.5, 0]), np.array([3.35, -1.5, 0])]
        p1 = panel(PW, PH, "Which cook is stuck?").move_to(pos[0])
        p2 = panel(PW, PH, "Which table was it for?").move_to(pos[1])
        p3 = panel(PW, PH, "How long has the rail been full?").move_to(pos[2])
        p4 = panel(PW, PH, "Closing time").move_to(pos[3])
        c1 = VGroup(*[cook(GREY_A, 0.95) for _ in range(3)]).arrange(RIGHT, buff=0.7).move_to(pos[0] + DOWN * 0.35)
        q1 = T("?", 40, RULE).next_to(c1, RIGHT, buff=0.4)
        wt = person(WAITER, 0.95).move_to(pos[1] + LEFT * 1.6 + DOWN * 0.35)
        wt_n = note("table 4", NOTE, 18).move_to(wt[0].get_center() + RIGHT * 0.05).scale(0.9)
        wt_l = T("waiter", 20, WAITER).next_to(wt, DOWN, buff=0.1)
        ck2 = cook(COOK, 0.95).move_to(pos[1] + RIGHT * 1.0 + DOWN * 0.35)
        dish = Ellipse(width=0.8, height=0.25).set_stroke(GREY_A, 2).set_fill(GREY_E, 1).next_to(ck2, RIGHT, buff=0.15)
        q2 = T("?", 36, RULE).next_to(dish, UP, buff=0.1)
        rl = rail(pos[2][0] - 2.4, pos[2][0] + 2.4, pos[2][1] + 0.1)
        rts = VGroup(*[ticket("", 0.55, 0.4).move_to([pos[2][0] - 2.0 + 0.62 * k, pos[2][1] - 0.2, 0]) for k in range(7)])
        q3 = T("count: nobody kept one", 22, GREY_B).move_to(pos[2] + DOWN * 0.7)
        ov = oven(1.3, 0.95).move_to(pos[3] + LEFT * 1.0 + DOWN * 0.3)
        dishes = VGroup(*[Ellipse(width=0.35, height=0.14).set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.5), 1) for _ in range(2)])
        dishes.arrange(RIGHT, buff=0.08).move_to(ov[1])
        lights = T("lights off", 24, GREY_B).move_to(pos[3] + RIGHT * 1.5 + DOWN * 0.3)
        self.say("sat")
        self.at(1)
        self.play(FadeIn(p1), FadeIn(c1), FadeIn(q1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(p2), FadeIn(wt), FadeIn(wt_n), FadeIn(wt_l), FadeIn(ck2), FadeIn(dish), FadeIn(q2), run_time=0.7)
        self.at(5)
        self.play(FadeIn(p3), FadeIn(rl), FadeIn(rts), FadeIn(q3), run_time=0.7)
        self.at(7)
        self.play(FadeIn(p4), FadeIn(ov), FadeIn(dishes), run_time=0.6)
        self.play(FadeIn(lights), p4[0].animate.set_fill(GREY_E, 0.9), run_time=0.6)
        self.hold()
        none = VGroup(*[T("defaults: no answer", 20, BAD).move_to(p_.get_bottom() + UP * 0.25) for p_ in (p1, p2, p3, p4)])
        self.say("sat2")
        self.play(LaggedStart(*[FadeIn(n_) for n_ in none], lag_ratio=0.2), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(p1, p2, p3, p4, c1, q1, wt, wt_n, wt_l, ck2, dish, q2, rl, rts, q3, ov, dishes, lights, none)),
                  run_time=0.6)

        # ================= 1. name tags =================
        h1 = T("Name tags", 32, RULE).move_to([0, 3.0, 0])
        cks = VGroup(*[cook(COOK, 1.2) for _ in range(3)]).arrange(RIGHT, buff=2.4).move_to([0, 1.0, 0])
        old = ["pool-3-thread-7", "pool-5-thread-2", "pool-8-thread-1"]
        tags_old = VGroup(*[name_tag(o, GREY_B, 20).next_to(c_, DOWN, buff=0.18) for o, c_ in zip(old, cks)])
        dump = VGroup(T("thread dump:", 24, GREY_A), T("every thread's name, state and line of code", 24)).arrange(RIGHT, buff=0.25)
        dump.move_to([0, -0.9, 0])
        same = T("as much as a white jacket", 24, GREY_B).move_to([0, -1.5, 0])
        self.say("names")
        self.play(FadeIn(h1), FadeIn(cks), run_time=0.6)
        self.at(1)
        self.play(FadeIn(dump), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(t_, shift=UP * 0.1) for t_ in tags_old], lag_ratio=0.25), run_time=0.9)
        self.at(3)
        cks_w = VGroup(*[cook(GREY_A, 1.2).move_to(c_) for c_ in cks])
        self.play(FadeIn(same), *[ReplacementTransform(a_, b_) for a_, b_ in zip(cks, cks_w)], run_time=0.7)
        cks = VGroup(*[cook(COOK, 1.2).move_to(c_) for c_ in cks_w])
        self.hold()
        tags_new = VGroup(*[name_tag(f"grill-{k}", COOK, 22).next_to(c_, DOWN, buff=0.18) for k, c_ in enumerate(cks)])
        code = VGroup(T("Java and Kotlin, JDK 21+:", 22, GREY_B),
                      M("Thread.ofPlatform().name(\"grill-\", 0).factory()", 26, RULE)).arrange(DOWN, buff=0.15)
        code.move_to([0, -1.6, 0])
        self.say("names2")
        self.play(FadeOut(same), FadeOut(dump), run_time=0.4)
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.6)
        self.at_text("grill-0", lead=0.4)
        self.play(*[ReplacementTransform(a_, b_) for a_, b_ in zip(tags_old, tags_new)],
                  *[ReplacementTransform(a_, b_) for a_, b_ in zip(cks_w, cks)], run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(h1, cks, tags_new, code)), run_time=0.5)

        # ================= 2. the note on the jacket =================
        h2 = T("The note", 32, RULE).move_to([0, 3.0, 0])
        wtr = person(WAITER, 1.3).move_to([-5.0, 1.0, 0])
        wtr_l = VGroup(T("main", 22, WAITER), T("the waiter", 20, GREY_B)).arrange(DOWN, buff=0.05).next_to(wtr, DOWN, buff=0.15)
        n42 = note("req-42").move_to(wtr[0].get_center())
        tl_l = VGroup(T("ThreadLocal:", 24, NOTE), T("one value per thread, a note pinned to a jacket", 24)).arrange(RIGHT, buff=0.2)
        tl_l.move_to([0, 2.3, 0])
        self.say("note")
        self.play(FadeIn(h2), FadeIn(wtr), FadeIn(wtr_l), run_time=0.6)
        self.at_text("like req-42", lead=0.4)
        self.play(FadeIn(n42, scale=0.6), run_time=0.5)
        self.at(1)
        self.play(FadeIn(tl_l), run_time=0.6)
        self.at(2)
        self.play(Indicate(n42[1], color=NOTE, scale_factor=1.2), run_time=0.8)
        self.hold()

        pl = RoundedRectangle(corner_radius=0.15, width=3.4, height=2.6).set_stroke(GREY_B, 2.5).move_to([3.9, 0.6, 0])
        pl_l = T("a pool of one thread", 22, GREY_B).next_to(pl, UP, buff=0.12)
        wk = cook(COOK, 1.3).move_to(pl.get_center() + LEFT * 0.6 + UP * 0.1)
        wk_l = T("worker", 22, COOK).next_to(wk, DOWN, buff=0.12)
        T_Y = [1.1, 0.4, -0.3]
        tks = [ticket("task 1", 1.2, 0.48, 20), ticket("task 2", 1.2, 0.48, 20), ticket("task 3", 1.2, 0.48, 20)]
        for t_, y in zip(tks, T_Y):
            t_.move_to([-2.4, y, 0])
        outs = VGroup(M("1. plain task sees:   null", 22), M("2. wrapped task sees: req-42", 22),
                      M("3. next task sees:    req-7  (left over from an earlier task)", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        outs.move_to([-6.2, -2.3, 0], aligned_edge=LEFT)
        self.say("note_q")
        self.play(FadeOut(tl_l), FadeIn(pl), FadeIn(pl_l), FadeIn(wk), FadeIn(wk_l), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(t_, shift=RIGHT * 0.2) for t_ in tks], lag_ratio=0.3), run_time=0.9)
        self.hold(after=0)
        self.predict()

        seat = pl.get_center() + RIGHT * 0.85 + UP * 0.1
        self.say("note_a")
        self.play(tks[0].animate.move_to(seat), run_time=0.6)
        self.play(FadeIn(outs[0]), Indicate(wk, color=COOK, scale_factor=1.08), run_time=0.6)
        self.at(1)
        self.play(Indicate(n42, color=NOTE, scale_factor=1.15), run_time=0.7)
        self.at(2)
        n7 = note("req-7", GREY_B).move_to(wk[0].get_center())
        self.play(FadeOut(tks[0]), tks[2].animate.move_to(seat), FadeIn(n7, scale=0.6), run_time=0.7)
        self.play(FadeIn(outs[2]), run_time=0.5)
        self.at(3)
        self.play(Indicate(n7[1], color=BAD, scale_factor=1.3), run_time=0.8)
        self.hold()

        fixl = VGroup(T("1. capture: copy the note onto the ticket", 24),
                      T("2. install: pin it on the cook who takes it", 24),
                      T("3. restore in finally: take it off when the dish leaves", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fixl.move_to([-6.2, 2.3, 0], aligned_edge=LEFT)
        n42c = n42.copy()
        self.say("note_fix")
        self.play(FadeOut(h2), FadeOut(tks[2]), FadeOut(n7), run_time=0.5)
        self.play(FadeIn(fixl[0]), run_time=0.5)
        self.add(n42c)
        self.play(n42c.animate.scale(0.85).move_to(tks[1].get_right() + LEFT * 0.05 + UP * 0.22), run_time=0.7)
        t2 = VGroup(tks[1], n42c)
        self.at_text("pin it", lead=0.3)
        self.play(FadeIn(fixl[1]), t2.animate.move_to(seat), run_time=0.8)
        self.play(n42c.animate.move_to(wk[0].get_center()), run_time=0.5)
        self.play(FadeIn(outs[1]), run_time=0.5)
        self.at_text("and take it off", lead=0.3)
        self.play(FadeIn(fixl[2]), run_time=0.5)
        self.play(FadeOut(n42c, shift=DOWN * 0.3), FadeOut(tks[1]), run_time=0.6)
        self.hold()

        rule2 = T("A ThreadLocal belongs to a thread, not to a task.", 30, RULE).move_to([0, -0.2, 0])
        self.say("note_break")
        self.play(FadeOut(VGroup(fixl, wtr, wtr_l, n42, pl, pl_l, wk, wk_l)), outs.animate.move_to([0, -2.3, 0]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(outs, rule2)), run_time=0.5)

        # ================= 3. the board by the pass =================
        h3 = T("The board by the pass", 32, RULE).move_to([0, 3.0, 0])
        rows = [("queue size", "tickets on the rail"), ("active / max", "busy cooks"),
                ("rejections", "orders turned away: count them yourself"), ("time in queue", "how long a ticket waited")]
        brd = VGroup(*[VGroup(T(a, 28, WHITE), T(b, 24, GREY_A)) for a, b in rows])
        for r_ in brd:
            r_[1].next_to(r_[0], RIGHT, buff=0.4)
        brd.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        for r_ in brd:
            r_[1].move_to([r_[0].get_left()[0] + 3.0, r_[0].get_y(), 0], aligned_edge=LEFT)
        bb = board_box(11.4, brd.height + 0.7)
        brd.move_to([0, 0.7, 0])
        bb.move_to(brd)
        brd.shift(RIGHT * 0.2)
        self.say("board")
        self.play(FadeIn(h3), FadeIn(bb), run_time=0.6)
        for i, key in enumerate(["The queue size", "The active count", "Rejections", "And time in queue"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(brd[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        # the burst: 10 tasks, 2 threads, room for 4
        self.play(FadeOut(VGroup(bb, brd)), run_time=0.5)
        RY = 1.7
        rl2 = rail(-3.2, 0.4, RY + 0.35)
        slots = [np.array([-2.75 + 0.85 * k, RY, 0]) for k in range(4)]
        sl_box = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.05, width=0.72, height=0.5), num_dashes=16)
                          .set_stroke(GREY_B, 2).move_to(p_) for p_ in slots])
        rl_l = T("rail: room for 4", 22, GREY_B).next_to(rl2, UP, buff=0.12)
        ocks = VGroup(*[cook(COOK, 1.0).move_to([2.0 + 1.6 * k, RY, 0]) for k in range(2)])
        otags = VGroup(*[name_tag(f"orders-{k + 1}", COOK, 18).next_to(c_, DOWN, buff=0.12) for k, c_ in enumerate(ocks)])
        cook_seat = [c_.get_center() + RIGHT * 0.62 for c_ in ocks]
        door = Line([-4.2, RY - 0.6, 0], [-4.2, RY + 0.6, 0]).set_stroke(GREY_B, 5)
        self.say("board_q")
        self.play(FadeOut(h3), FadeIn(rl2), FadeIn(sl_box), FadeIn(rl_l), FadeIn(ocks), FadeIn(otags), FadeIn(door), run_time=0.8)
        self.hold(after=0)
        self.predict()

        hdr = M("  ms  threads  active  queued  done  rejected", 22, GREY_A)
        data = ["   0        2       2       4     0         4",
                " 244        2       2       4     0         4",
                " 446        2       2       2     2         4",
                " 647        2       2       0     4         4",
                " 849        2       2       0     4         4",
                "1050        2       0       0     6         4"]
        tbl = VGroup(hdr, *[M(d, 22) for d in data]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cw = M("0123456789", 22).width / 10
        for ln, src in zip(tbl, ["  ms  threads  active  queued  done  rejected"] + data):
            ln.shift(RIGHT * (len(src) - len(src.lstrip())) * cw)
        tbl.move_to([0.0, -1.35, 0])
        tk10 = [ticket("", 0.6, 0.42) for _ in range(10)]
        for k, t_ in enumerate(tk10):
            t_.move_to([-6.0, RY + 0.55 - 0.12 * k, 0])
        self.say("board_a")
        self.play(LaggedStart(*[FadeIn(t_) for t_ in tk10], lag_ratio=0.05), run_time=0.5)
        self.play(*[tk10[k].animate.move_to(cook_seat[k]) for k in range(2)],
                  *[tk10[2 + k].animate.move_to(slots[k]) for k in range(4)], run_time=0.8)
        rej = VGroup(*tk10[6:])
        self.play(rej.animate.set_color(BAD).shift(DOWN * 1.0), run_time=0.5)
        self.play(FadeOut(rej, shift=DOWN * 0.3), FadeIn(tbl[0]), FadeIn(tbl[1]), run_time=0.5)
        self.at(1)
        for k in range(2):
            self.play(FadeOut(VGroup(tk10[2 * k], tk10[2 * k + 1])),
                      *[tk10[2 + 2 * k + j].animate.move_to(cook_seat[j]) for j in range(2)],
                      *[tk10[4 + 2 * k + j].animate.move_to(slots[j]) for j in range(2) if 4 + 2 * k + j < 6],
                      FadeIn(tbl[2 + 2 * k]), FadeIn(tbl[3 + 2 * k]), run_time=0.8)
        self.at(2)
        self.play(FadeOut(VGroup(tk10[4], tk10[5])), FadeIn(tbl[6]), run_time=0.7)
        self.hold()

        fx_l = VGroup(M("newFixedThreadPool(2)", 24, GREY_A), T("rail with no end:", 24),
                      T("rejected 0, queued 8, the last two wait 1.2 s", 24, BAD)).arrange(RIGHT, buff=0.25)
        fit(fx_l, 12.4).move_to([0, -1.35, 0])
        rl3 = rail(-6.2, 0.4, RY + 0.35)
        tk8 = VGroup(*[ticket("", 0.6, 0.42).move_to([-6.0 + 0.78 * k, RY, 0]) for k in range(8)])
        tq = T("time in queue", 24, RULE).next_to(tk8[:2], DOWN, buff=0.2)
        self.say("board_fixed")
        self.play(FadeOut(tbl), FadeOut(sl_box), FadeOut(rl_l), FadeOut(door), ReplacementTransform(rl2, rl3), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(t_, shift=RIGHT * 0.1) for t_ in tk8], lag_ratio=0.1), FadeIn(fx_l), run_time=1.0)
        self.at(1)
        self.play(Indicate(tk8[:2], color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(tq, shift=UP * 0.1), run_time=0.5)
        self.hold()

        rule3 = VGroup(T("Watch the queue, not just the threads. Count every rejection.", 30, RULE),
                       T("Empty queue, no rejections: healthy, however busy the cooks look.", 26, GOOD)).arrange(DOWN, buff=0.2)
        fit(rule3, 12.4).move_to([0, -2.5, 0])
        self.say("board_rule")
        self.play(FadeIn(rule3[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rule3[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(rl3, tk8, tq, fx_l, rule3, ocks, otags)), run_time=0.6)

        # ================= 4. the frozen board =================
        ICE = BLUE_M
        fb = VGroup(T("active: all", 28), T("queue: full, not moving", 28), T("done: 0", 28), T("CPU: idle", 28))
        fb.arrange(RIGHT, buff=0.7)
        fit(fb, 11.6)
        fbb = board_box(fb.width + 0.8, 1.0).set_stroke(ICE, 2.5)
        fz = VGroup(fbb, fb.move_to(fbb)).move_to([0, 2.65, 0])
        self.say("freeze_q")
        self.play(FadeIn(fz), run_time=0.8)
        self.at(1)
        self.play(Indicate(fb, color=ICE, scale_factor=1.04), run_time=0.9)
        self.hold()

        # two cooks, each holding a bill, each waiting for a fetch queued behind
        FY = 0.6
        rl4 = rail(-6.0, -0.4, FY + 0.42)
        fck = VGroup(*[cook(COOK, 1.1).move_to([1.6 + 2.6 * k, FY - 0.05, 0]) for k in range(2)])
        bills = VGroup(*[ticket(f"bill {k + 1}", 1.0, 0.48, 20).next_to(fck[k], RIGHT, buff=0.12) for k in range(2)])
        fetches = VGroup(*[ticket(f"fetch {k + 1}", 1.1, 0.48, 20, FETCH).move_to([-5.2 + 1.3 * k, FY, 0]) for k in range(2)])
        trace = VGroup(T("20 threads, 400 tables:", 24, GREY_A),
                       T("20 bills hold every thread; their 20 fetches wait behind 380 bills", 24)).arrange(DOWN, buff=0.12)
        fit(trace, 12.4).move_to([0, -1.2, 0])
        self.say("freeze")
        self.play(FadeIn(fck), FadeIn(rl4), run_time=0.6)
        self.at_text("Each bill task", lead=0.3)
        self.play(FadeIn(bills, shift=LEFT * 0.1), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(f_, shift=LEFT * 0.2) for f_ in fetches], lag_ratio=0.3), run_time=0.8)
        self.at_text("With 20 threads", lead=0.3)
        self.play(FadeIn(trace), run_time=0.7)
        self.hold()

        waits = VGroup(*[DashedVMobject(ArcBetweenPoints(fck[k][2].get_top() + UP * 0.08, fetches[k].get_top() + UP * 0.32,
                                                         angle=PI / 4), num_dashes=36).set_stroke(FETCH, 2.5) for k in range(2)])
        wl = VGroup(*[T("waiting", 22, FETCH).next_to(fck[k], DOWN, buff=0.12) for k in range(2)])
        self.say("freeze2")
        self.play(Create(waits), FadeIn(wl), run_time=1.0)
        self.at(1)
        self.play(Indicate(fetches, color=FETCH, scale_factor=1.1), run_time=0.8)
        self.hold()

        dd = VGroup(M("after 300 ms: active=2, queued=2, completed=0", 22),
                    M("no bill after 2 s: both threads wait for fetches that can never start", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        fit(dd, 12.4).move_to([0, -2.4, 0])
        nm = VGroup(T("pool-induced deadlock", 30, BAD), T("(also called thread starvation deadlock)", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        nm.move_to([0, -1.2, 0])
        self.say("freeze_name")
        self.play(FadeOut(trace), FadeIn(nm, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(dd), run_time=0.7)
        self.hold()

        fixes = VGroup(VGroup(T("1. compose, don't wait:", 26), M("supplyAsync(fetch, pool).thenApply(render)", 22, GOOD)).arrange(RIGHT, buff=0.25),
                       T("2. fetch inline, in the same task", 26),
                       T("3. give each stage its own pool", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(fixes, 12.4).move_to([0, -1.6, 0])
        rule4 = T("No task may wait for another task in its own bounded pool.", 28, RULE).move_to([0, -3.05, 0])
        fit(rule4, 12.4)
        self.say("freeze_fix")
        self.play(FadeOut(VGroup(nm, dd)), run_time=0.4)
        self.play(FadeIn(fixes[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(fixes[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(fixes[2]), FadeIn(rule4), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(fz, rl4, fck, bills, fetches, waits, wl, fixes, rule4)), run_time=0.6)

        # ================= 5. closing in order =================
        h5 = T("Closing time", 32, RULE).move_to([0, 3.0, 0])
        SY = 1.2
        door2 = VGroup(Rectangle(width=0.9, height=1.4).set_stroke(GREY_B, 3).set_fill(GREY_E, 1),
                       Dot(radius=0.06, color=GREY_B)).move_to([-5.2, SY, 0])
        door2[1].move_to(door2[0].get_center() + RIGHT * 0.28)
        lock = VGroup(Rectangle(width=0.36, height=0.28).set_stroke(GOLD_M, 2.5).set_fill(dim(GOLD_M, 0.5), 1),
                      Arc(radius=0.12, start_angle=0, angle=PI).set_stroke(GOLD_M, 2.5))
        lock[1].next_to(lock[0], UP, buff=0)
        lock.move_to(door2[0].get_center() + RIGHT * 0.25 + DOWN * 0.1)
        d_l = T("1. lock the door", 22).next_to(door2, DOWN, buff=0.15)
        kp = VGroup(RoundedRectangle(corner_radius=0.12, width=2.4, height=1.1).set_stroke(COOK, 2.5).set_fill(dim(COOK, 0.12), 1),
                    T("kitchen pool", 24, COOK)).move_to([-1.9, SY, 0])
        kp[1].move_to(kp[0])
        bp = VGroup(RoundedRectangle(corner_radius=0.12, width=2.4, height=1.1).set_stroke(GOLD_M, 2.5).set_fill(dim(GOLD_M, 0.12), 1),
                    T("billing pool", 24, GOLD_M)).move_to([1.6, SY, 0])
        bp[1].move_to(bp[0])
        feed = Arrow(kp.get_right(), bp.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        feed_l = T("feeds", 20, GREY_B).next_to(feed, UP, buff=0.08)
        o_l = T("2. upstream first", 22).move_to([-0.15, SY - 0.95, 0])
        clk = VGroup(Circle(radius=0.45).set_stroke(GREY_A, 3), Line(ORIGIN, UP * 0.3, stroke_width=3, color=RULE),
                     Line(ORIGIN, RIGHT * 0.22, stroke_width=3, color=RULE)).move_to([4.75, SY, 0])
        c_l = VGroup(T("3. one deadline:", 22), T("20 s inside the 30 s grace period", 20, GREY_A)).arrange(DOWN, buff=0.06)
        c_l.next_to(clk, DOWN, buff=0.15)
        lost = VGroup(T("4. log what never ran:", 24), M("shutdownNow()", 24, GREY_A),
                      T("returns the tasks that never started", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        fit(lost, 12.4).move_to([0, -0.9, 0])
        self.say("close")
        self.play(FadeIn(h5), FadeIn(door2), FadeIn(kp), FadeIn(bp), FadeIn(feed), FadeIn(feed_l), FadeIn(clk), run_time=0.8)
        self.at_text("locks the front", lead=0.3)
        self.play(FadeIn(lock, scale=0.6), FadeIn(d_l), run_time=0.6)
        self.at_text("upstream", lead=0.3)
        self.play(FadeIn(o_l), Indicate(kp[1], color=COOK, scale_factor=1.1), run_time=0.7)
        self.at_text("all before", lead=0.3)
        self.play(FadeIn(c_l), Rotate(clk[1], -PI / 3, about_point=clk[0].get_center()), run_time=0.8)
        self.hold()

        self.say("close2")
        self.at(1)
        self.play(kp.animate.set_opacity(0.35), run_time=0.6)
        self.play(bp.animate.set_opacity(0.35), run_time=0.6)
        self.at(3)
        self.play(FadeIn(lost, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.play(kp.animate.set_opacity(1), bp.animate.set_opacity(1), FadeOut(lost), run_time=0.5)
        dsh = Ellipse(width=0.55, height=0.2).set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.5), 1).move_to(kp.get_center() + DOWN * 0.3)
        rej = M("RejectedExecutionException", 22, BAD).move_to([1.6, -0.5, 0])
        free = T("cooked, served, never billed: a free dinner nobody planned", 26, GREY_A).move_to([0, -1.5, 0])
        fit(free, 12.4)
        self.say("close_joke")
        self.play(bp.animate.set_opacity(0.35), FadeIn(dsh), run_time=0.6)
        self.play(dsh.animate.move_to(bp.get_left() + LEFT * 0.35), run_time=0.7)
        self.play(FadeIn(rej, shift=DOWN * 0.1), Wiggle(dsh), run_time=0.8)
        self.at(1)
        self.play(FadeIn(free, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(h5, door2, lock, d_l, kp, bp, feed, feed_l, o_l, clk, c_l, dsh, rej, free)), run_time=0.6)

        # ================= moral and check =================
        mo = VGroup(T("Busy threads alone say nothing: read the board.", 30, RULE),
                    T("Name the cooks. Clip the note to the ticket.", 30),
                    T("Watch the queue and count the rejections.", 30),
                    T("Never let a cook wait for a ticket behind him.", 30, BAD)).arrange(DOWN, buff=0.32)
        fit(mo, 12.4).move_to([0, 0.5, 0])
        self.say("moral")
        self.at(1)
        self.play(FadeIn(mo[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mo[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("and watch", lead=0.3)
        self.play(FadeIn(mo[2], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mo[3], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(mo), run_time=0.5)

        cb = VGroup(T("active 2 of 2", 30), T("queued 2", 30), T("done 0", 30), T("CPU idle", 30)).arrange(RIGHT, buff=0.7)
        cbb = board_box(cb.width + 0.8, 1.0)
        chk = VGroup(cbb, cb.move_to(cbb)).move_to([0, 1.2, 0])
        chk_t = T("Check:", 28, RULE).next_to(chk, UP, buff=0.3)
        cq = T("Busy, or stuck?", 32, RULE).move_to([0, -0.3, 0])
        self.say("check")
        self.play(FadeIn(chk_t), FadeIn(chk), run_time=0.7)
        self.at(1)
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("Stuck. Look for a task waiting on a task in its own pool.", 30, GOLD_M).move_to([0, -1.6, 0])
        self.say("check_a")
        self.play(cbb.animate.set_stroke(BAD), FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.0)
