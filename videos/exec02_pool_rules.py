from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bThreadPoolExecutor\b", "thread pool executor"), (r"\bArrayBlockingQueue\b", "array blocking queue"),
    (r"\bLinkedBlockingQueue\b", "linked blocking queue"), (r"\bAbortPolicy\b", "abort policy"),
    (r"\bRejectedExecutionException\b", "rejected execution exception"), (r"\bnewFixedThreadPool\b", "new fixed thread pool"),
    (r"\bnewCachedThreadPool\b", "new cached thread pool"), (r"\bkeep-alive\b", "keep alive"),
]

# every spoken line, in order
N = {
    "open": "Last time, one line gave us a kitchen: four cooks, taking tickets from one rail. "
            "Then comes a busy evening. Orders arrive faster than four cooks can cook them, "
            "and the rail grows by a few tickets every second.",
    "sixtyfour": "So someone rebuilds the pool with a maximum of 64 threads, and keeps the same rail. "
                 "The code compiles. The setting is right there. And not one extra cook turns up.",
    "shyq": "So here's a question many of us are too shy to ask. What is a maximum for, if it never brings anyone?",
    "kitchen": "To find out, let's visit a kitchen with a thrifty manager. It has two permanent cooks. "
               "Its rail has room for two tickets. When the rail is full, the manager may phone for temporary cooks, "
               "up to two of them. And when every cook is busy and the rail is full, "
               "a door policy decides what happens to the next customer.",
    "map": "ThreadPoolExecutor, the class behind that one line, has a setting for each part. "
           "The core pool size is the permanent cooks: 2. "
           "The maximum pool size counts permanent and temporary together: 4. "
           "The work queue is the rail, an ArrayBlockingQueue with room for 2. "
           "And the rejection handler is the door policy. The default, AbortPolicy, simply refuses.",
    "seven": "Now seven orders arrive at once, and each one takes 500 milliseconds to cook. "
             "Most of us expect the obvious. Four cooks start right away, two orders wait on the rail, "
             "and one is turned away. Is that what happens?",
    "r1": "Let's follow the rules, one order at a time. Order 1: there are fewer cooks than the core size, "
          "so it gets a new permanent cook. That's rule 1. Order 2 gets the second one.",
    "r2": "Order 3: we're at the core size, so the manager clips it to the rail. That's rule 2. "
          "Order 4 joins it, and now the rail is full.",
    "r3": "Order 5 finds the rail full. Only now does the manager pick up the phone, and a temporary cook takes it. "
          "That's rule 3. Order 6 gets the second temp, and the kitchen is at its maximum of four.",
    "r4": "Order 7 finds every cook busy and the rail full. That's rule 4: the door policy turns it away, "
          "with a RejectedExecutionException.",
    "thrifty": "So the obvious guess was wrong. The pool doesn't grow first and queue second. "
               "It queues first, and grows second. And that's the thrifty manager. A ticket on the rail costs nothing. "
               "A temporary cook costs wages. So he phones only when the rail has no room left.",
    "order": "One more surprise. Orders 1, 2, 5 and 6 come out at about 500 milliseconds, "
             "and orders 3 and 4 only at 1,000. A new cook takes the ticket that made the manager call him, "
             "not the oldest ticket on the rail.",
    "breaks": "Here the restaurant picture breaks. A real kitchen would cook the oldest ticket first, "
              "or hear about it from tables 3 and 4. A pool makes no such promise.",
    "back64": "Now back to our 64 cooks who never came. newFixedThreadPool builds this same class, "
              "with a LinkedBlockingQueue that has no limit. A rail with no end.",
    "never": "So rule 2 always succeeds. Rule 3 never runs, and no temp is ever called. "
             "Rule 4 never runs either, so nobody is ever turned away. "
             "The maximum of 64 is dead code: it compiles, and it never does anything.",
    "demo2": "Run the same seven orders with that queue, and the pool stays at two threads, with five tickets on the rail. "
             "All seven finish after about 2,000 milliseconds: four rounds of 500 on two cooks.",
    "safe": "That looks safe. It isn't. Say orders arrive at 400 a second, and the kitchen can finish 300. "
            "The rail grows by 100 every second. After ten minutes, 60,000 tickets are waiting, "
            "and a new order waits more than three minutes before a cook even looks at it.",
    "dinner": "The customer left long ago, and the kitchen is busy cooking dinners nobody will eat. "
              "And nothing complains until the heap, the memory where Java keeps its objects, runs out.",
    "cached": "newCachedThreadPool fails the other way. Its rail has no room at all, so under a burst, "
              "every order gets a new thread. That's last lesson's manager, hiring a cook for every salad.",
    "shape": "The shape that pushes back is a rail with a limit, and a maximum that isn't endless. "
             "Then rule 4 can fire, and overload becomes something you can see, and choose how to handle.",
    "code": "Here's our kitchen in Java and Kotlin. Core 2, max 4, and a keep-alive of 60 seconds, "
            "which is how long an idle temp may stay before he's sent home. Then the rail of 2, and the door policy.",
    "moral": "So, what is a maximum for? It's the relief valve for a full rail. The pool queues first, and grows second. "
             "Give the queue a limit, or the maximum is just a number in your code.",
    "check": "Quick check. Core 2, max 4, and a rail with room for 10. Eight orders arrive, and each takes a minute. "
             "How many cooks are cooking?",
    "check_a": "Two. The other six wait on the rail, which never fills, so the manager never phones.",
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

    def left_text(self, sub, lead=0.3):
        text, t0, dur = self._line
        return max(0.3, t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2, pos=(6.4, -3.25)):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def person(color=BLUE_M, s=1.0, hat=False, op=1.0):
    """A little figure. With hat=True it is a cook."""
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3)
    body.set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head)
    if hat:
        brim = Rectangle(width=0.28, height=0.06, stroke_width=0).set_fill(GREY_A, 1).next_to(head, UP, buff=0.015)
        top = RoundedRectangle(corner_radius=0.05, width=0.24, height=0.15, stroke_width=0).set_fill(GREY_A, 1)
        top.next_to(brim, UP, buff=0)
        g.add(brim, top)
    g.scale(s)
    if op < 1:
        g.set_opacity(op)
    return g


def cook(color=BLUE_M, s=1.0):
    return person(color, s, hat=True)


def ticket(n=None, s=1.0, color=WHITE):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55, stroke_color=color, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    mark = M(f"#{n}", 22).move_to(r) if n is not None else Line(LEFT * 0.2, RIGHT * 0.2, stroke_width=2, color=GREY_B)
    return VGroup(r, mark, clip).scale(s).set_z_index(4)


def stove(w=1.3):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.42).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    b = VGroup(*[Circle(radius=0.11).set_stroke(GREY_C, 2).move_to(r.get_center() + RIGHT * dx) for dx in (-w * 0.22, w * 0.22)])
    return VGroup(r, b)


def rail_line(x0, x1, y):
    return Line([x0, y, 0], [x1, y, 0]).set_stroke(GREY_B, 9)


def code_block(src, size=22, hl=None, grey=()):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        if i in grey:
            lines[i].set_color(GREY_B)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def counter(fmt, fn, pos, size=30, color=WHITE, edge=ORIGIN):
    """Text that shows fmt.format(fn()); it changes in place with become(), so no stale copy is ever drawn."""
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


def legend(color, text, size=24, op=0.9):
    return VGroup(Square(0.28, stroke_width=0).set_fill(color, op), T(text, size)).arrange(RIGHT, buff=0.15)


# one colour per thing, for the whole video
PERM, TEMP, MGR, PHONE, DOOR, GOOD, BAD = BLUE_M, TEAL_M, PURPLE_M, GOLD_M, RED_M, GREEN_M, RED_M


def phone(color=PHONE):
    body = RoundedRectangle(corner_radius=0.06, width=0.3, height=0.52).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    scr = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.28).set_stroke(color, 1.5).move_to(body.get_center() + UP * 0.04)
    return VGroup(body, scr)


def spot(color, s=1.0):
    """A dashed outline where a cook could stand."""
    p = cook(color, s)
    return VGroup(*[DashedVMobject(m, num_dashes=16).set_stroke(color, 2) for m in p[:2]]).set_opacity(0.55)


def slot_box(p):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55)
    return DashedVMobject(r, num_dashes=18).set_stroke(GREY_B, 2).move_to(p + DOWN * 0.07)


def strike(m, color=BAD):
    return Line(m.get_left() + LEFT * 0.08, m.get_right() + RIGHT * 0.08, stroke_width=3, color=color)


# the kitchen
MGR_P, PHONE_P, IN_P = np.array([-5.4, 1.65, 0]), np.array([-4.6, 2.05, 0]), np.array([-5.4, 3.0, 0])
RAIL_Y = 2.75
SLOTS2 = [np.array([-3.05, RAIL_Y - 0.36, 0]), np.array([-1.75, RAIL_Y - 0.36, 0])]
SLOTS5 = [np.array([-3.35 + 0.65 * i, RAIL_Y - 0.33, 0]) for i in range(5)]
CKP = [np.array([x, 1.6, 0]) for x in (0.3, 1.7, 3.3, 4.7)]
STP = [p + DOWN * 0.85 for p in CKP]
HEADP = [p + UP * 0.85 for p in CKP]
LOGX = 0.6


def counter2(fmt, fn, pos, size=30, color=WHITE, edge=ORIGIN):
    """Like counter(), for a format with several fields: fn returns a tuple."""
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = T(fmt.format(*n), size, color).move_to(pos, aligned_edge=edge)
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


def along(t, path, s_end=1.0):
    """Move t along path (by length) while scaling it to s_end of its width."""
    w0 = t.width

    def f(m, a):
        m.scale_to_fit_width(w0 * (1 + (s_end - 1) * a))
        m.move_to(path.point_from_proportion(smooth(a)))
    return UpdateFromAlphaFunc(t, f)


class Exec02PoolRules(Narrated):
    """exec-02, section 0: the thrifty manager's kitchen (2 permanent cooks, a rail of 2, up to 2 temps, a door policy)
    is ThreadPoolExecutor(2, 4, ..., ArrayBlockingQueue(2), AbortPolicy); seven orders through the four rules break the
    'grow first' guess; temps take the ticket that called them; an endless rail makes max 64 dead code (2,019 ms, the
    60,000-ticket rail); the cached pool hires for every salad; a bounded queue with a finite max pushes back."""

    def construct(self):
        self.title_card("The thrifty manager", "where every task goes in a ThreadPoolExecutor")

        # ================= the busy evening, and 64 cooks who never come =================
        rail0 = rail_line(-5.6, 5.6, 2.7)
        SL0 = [np.array([-5.05 + 0.8 * i, 2.34, 0]) for i in range(14)]
        CX0 = [-2.4, -0.8, 0.8, 2.4]
        ck0 = VGroup(*[cook(PERM).move_to([x, 1.0, 0]) for x in CX0])
        st0 = VGroup(*[stove(1.2).move_to([x, 0.1, 0]) for x in CX0])
        ck0_l = T("four cooks, one rail", 26, PERM).move_to([0, -0.5, 0])
        tk0 = [ticket(s=0.85).move_to(SL0[i]) for i in range(14)]
        self.say("open")
        self.play(Create(rail0), FadeIn(ck0), FadeIn(st0), FadeIn(ck0_l), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in tk0[:3]], lag_ratio=0.3), run_time=0.8)
        self.at(1)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in tk0[3:9]], lag_ratio=0.35), run_time=self.left() * 0.9)
        self.hold()

        spots0 = VGroup(*[spot(TEMP, 0.55) for _ in range(30)]).arrange_in_grid(rows=2, cols=15, buff=(0.32, 0.18))
        spots0.move_to([0, -1.55, 0])
        mx0 = T("maximum: 64 threads", 28, TEMP).move_to([0, -2.6, 0])
        still = T("cooks working: still 4", 28, PERM).move_to([0, -0.5, 0])
        self.say("sixtyfour")
        self.play(FadeIn(mx0), LaggedStart(*[FadeIn(s) for s in spots0], lag_ratio=0.02), run_time=1.4)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in tk0[9:12]], lag_ratio=0.3), run_time=0.9)
        self.at(3)
        self.play(Transform(ck0_l, still), LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in tk0[12:]], lag_ratio=0.3),
                  run_time=1.0)
        self.play(Indicate(ck0_l, color=PERM), run_time=0.8)
        self.hold()

        sq = T("What is a maximum for, if it never brings anyone?", 34, YELLOW_M).move_to([0, -3.15, 0])
        fit(sq, 12.4)
        self.say("shyq")
        self.play(FadeOut(mx0), FadeIn(sq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(pos=(6.4, -2.45))
        self.play(FadeOut(VGroup(rail0, ck0, st0, ck0_l, *tk0, spots0, sq)), run_time=0.7)

        # ================= the thrifty manager's kitchen =================
        mgr = person(MGR).move_to(MGR_P)
        mgr_l = T("the manager", 24, MGR).next_to(mgr, DOWN, buff=0.18)
        ph = phone().move_to(PHONE_P)
        rail = rail_line(-3.7, -1.1, RAIL_Y)
        slots = VGroup(*[slot_box(p) for p in SLOTS2])
        rail_l = T("the rail: room for 2", 24, GREY_A).move_to([-2.4, 1.7, 0])
        pspots = VGroup(*[spot(PERM) .move_to(CKP[i]) for i in (0, 1)])
        tspots = VGroup(*[spot(TEMP).move_to(CKP[i]) for i in (2, 3)])
        stoves = VGroup(*[stove(1.1).move_to(p) for p in STP])
        perm_l = T("permanent: 2", 24, PERM).move_to([1.0, 0.2, 0])
        temp_l = T("temporary: up to 2", 24, TEMP).move_to([4.0, 0.2, 0])
        brace = Brace(Line([-0.25, 0.02, 0], [5.25, 0.02, 0]), DOWN, color=GREY_B, buff=0.05)
        max_l = T("at most 4 cooks", 24, GREY_A).next_to(brace, DOWN, buff=0.06)
        door = box("door policy", DOOR, h=0.7, size=24).move_to([-5.2, 0.2, 0])
        self.say("kitchen")
        self.play(FadeIn(mgr), FadeIn(mgr_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pspots), FadeIn(stoves[:2]), FadeIn(perm_l), run_time=0.7)
        self.at(2)
        self.play(Create(rail), FadeIn(slots), FadeIn(rail_l), run_time=0.8)
        self.at(3)
        self.play(FadeIn(ph, shift=UP * 0.1), run_time=0.4)
        self.at_text("temporary cooks", lead=0.3)
        self.play(FadeIn(tspots), FadeIn(stoves[2:]), FadeIn(temp_l), run_time=0.7)
        self.play(GrowFromCenter(brace), FadeIn(max_l), run_time=0.6)
        self.at(4)
        self.at_text("a door policy", lead=0.3)
        self.play(FadeIn(door, shift=UP * 0.1), run_time=0.6)
        self.hold()

        tpe = M("ThreadPoolExecutor", 26).move_to([LOGX, -1.15, 0], aligned_edge=LEFT)
        perm_m = T("core pool size: 2", 24, PERM).move_to(perm_l)
        max_m = T("maximum pool size: 4", 24, GREY_A).move_to(max_l)
        rail_m = VGroup(T("work queue:", 22, GREY_A), M("ArrayBlockingQueue(2)", 22, GREY_A)).arrange(DOWN, buff=0.08).move_to([-2.4, 1.65, 0])
        door_m = VGroup(T("rejection handler:", 22, DOOR), M("AbortPolicy", 22, DOOR)).arrange(DOWN, buff=0.08)
        door_m.next_to(door, RIGHT, buff=0.25)
        refuse = T("simply refuses", 22, GREY_A).next_to(door_m, DOWN, buff=0.08)
        self.say("map")
        self.play(FadeIn(tpe), run_time=0.6)
        self.at(1)
        self.play(Transform(perm_l, perm_m), Indicate(pspots, color=PERM), run_time=0.8)
        self.at(2)
        self.play(Transform(max_l, max_m), run_time=0.7)
        self.at(3)
        self.play(Transform(rail_l, rail_m), run_time=0.7)
        self.at(4)
        self.play(FadeIn(door_m), run_time=0.6)
        self.at(5)
        self.play(FadeIn(refuse), run_time=0.5)
        self.hold()

        # ---- the rules list, which stays ----
        rules = VGroup(T("1. Below core? Start a new thread.", 24, PERM), T("2. Otherwise, put it in the queue.", 24),
                       T("3. Queue full? Add a thread, up to max.", 24, TEMP), T("4. Still no room? Reject it.", 24, DOOR)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([-6.4, -1.75, 0], aligned_edge=LEFT)
        hl = SurroundingRectangle(rules[0], buff=0.08, corner_radius=0.06, color=PERM, stroke_width=2.5)
        rule_c = [PERM, WHITE, TEMP, DOOR]

        def rule_hl(i):
            return hl.animate.become(SurroundingRectangle(rules[i], buff=0.08, corner_radius=0.06, color=rule_c[i], stroke_width=2.5))

        seven = T("7 orders at once, 500 ms each", 26).move_to([LOGX, -1.1, 0], aligned_edge=LEFT)
        ghosts = VGroup(*[ticket(i + 1, s=0.8).move_to(HEADP[i]) for i in range(4)],
                        *[ticket(i + 5).move_to(SLOTS2[i]) for i in range(2)], ticket(7).move_to(IN_P)).set_opacity(0.45)
        gx = tick(False, 0.25).move_to(IN_P).set_z_index(7)
        guess_l = VGroup(T("the obvious guess:", 26, GREY_A), T("4 cooking, 2 on the rail, 1 turned away", 26, GREY_A)
                         ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([LOGX, -1.85, 0], aligned_edge=LEFT)
        self.say("seven")
        self.play(FadeOut(VGroup(tpe, door_m, refuse)), FadeIn(seven), run_time=0.7)
        self.at(1)
        self.play(FadeIn(guess_l[0]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(ghosts[:4]), run_time=0.6)
        self.at_text("two orders wait", lead=0.3)
        self.play(FadeIn(ghosts[4:6]), run_time=0.5)
        self.at_text("one is turned", lead=0.3)
        self.play(FadeIn(ghosts[6]), FadeIn(gx), FadeIn(guess_l[1]), run_time=0.6)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.25))

        # ---- the real run, one order at a time ----
        logh = T("what PoolPuzzleDemo prints", 22, GREY_B).move_to([LOGX, -1.05, 0], aligned_edge=LEFT)
        logs_t = ["task 1 accepted: threads=1 queued=0", "task 2 accepted: threads=2 queued=0",
                  "task 3 accepted: threads=2 queued=1", "task 4 accepted: threads=2 queued=2",
                  "task 5 accepted: threads=3 queued=2", "task 6 accepted: threads=4 queued=2",
                  "task 7 REJECTED: threads=4 queued=2"]
        logs = [M(s, 22, BAD if "REJ" in s else GREY_A).move_to([LOGX, -1.42 - 0.3 * i, 0], aligned_edge=LEFT)
                for i, s in enumerate(logs_t)]
        tk = {}
        cooks = {}

        def arrive(n):
            t = ticket(n).move_to(IN_P)
            tk[n] = t
            self.play(FadeIn(t, shift=DOWN * 0.2), run_time=0.35)

        def to_cook(n, ci, color, extra=()):
            """the order goes under the stoves to cook ci, who appears (a new thread)."""
            t = tk[n]
            path = VMobject().set_points_as_corners([IN_P, np.array([-5.0, 3.05, 0]), np.array([HEADP[ci][0], 3.05, 0]), HEADP[ci]])
            c = cook(color).move_to(CKP[ci])
            cooks[ci] = c
            sp = pspots[ci] if ci < 2 else tspots[ci - 2]
            self.play(along(t, path, 0.8), FadeOut(sp), FadeIn(c, scale=0.8), *extra, run_time=0.9)

        def to_rail(n, si, extra=()):
            t = tk[n]
            path = VMobject().set_points_as_corners([IN_P, np.array([SLOTS2[si][0], 3.05, 0]), SLOTS2[si]])
            self.play(MoveAlongPath(t, path), *extra, run_time=0.7)

        self.say("r1")
        self.play(FadeOut(VGroup(ghosts, gx, guess_l)), FadeOut(seven), FadeIn(rules), FadeIn(logh), run_time=0.7)
        self.at(1)
        arrive(1)
        self.play(Create(hl), run_time=0.4)
        self.at_text("new permanent", lead=0.3)
        to_cook(1, 0, PERM, (FadeIn(logs[0]),))
        self.at(3)
        arrive(2)
        to_cook(2, 1, PERM, (FadeIn(logs[1]),))
        self.hold()

        self.say("r2")
        arrive(3)
        self.at_text("clips it", lead=0.3)
        self.play(rule_hl(1), run_time=0.4)
        to_rail(3, 0, (FadeIn(logs[2]),))
        self.at(2)
        arrive(4)
        to_rail(4, 1, (FadeIn(logs[3]),))
        self.play(Indicate(rail_l, color=WHITE), run_time=0.7)
        self.hold()

        ring = lambda: [Wiggle(ph, scale_value=1.25, rotation_angle=0.08 * TAU),
                        Flash(ph, color=PHONE, line_length=0.15, flash_radius=0.45)]
        self.say("r3")
        arrive(5)
        self.play(Indicate(slots, color=BAD, scale_factor=1.05), run_time=0.6)
        self.at(1)
        self.play(rule_hl(2), *ring(), run_time=0.9)
        self.at_text("a temporary cook", lead=0.3)
        to_cook(5, 2, TEMP, (FadeIn(logs[4]),))
        self.at(3)
        arrive(6)
        self.play(*ring(), run_time=0.7)
        to_cook(6, 3, TEMP, (FadeIn(logs[5]),))
        self.play(Indicate(max_l, color=WHITE), run_time=0.7)
        self.hold()

        x7 = tick(False, 0.25).move_to(IN_P).set_z_index(7)
        self.say("r4")
        arrive(7)
        self.at(1)
        self.play(rule_hl(3), run_time=0.4)
        self.play(FadeIn(x7, scale=0.5), Indicate(door[1], color=DOOR), Circumscribe(door, color=DOOR, buff=0.08),
                  FadeIn(logs[6]), run_time=1.0)
        self.hold()

        wrong = T("grows first, queues second?", 28, GREY_A).move_to([LOGX, -1.05, 0], aligned_edge=LEFT)
        wrong_x = strike(wrong)
        right = T("It queues first, and grows second.", 30, YELLOW_M).move_to([LOGX, -1.7, 0], aligned_edge=LEFT)
        cost1 = VGroup(ticket(s=0.6), T("a ticket on the rail: costs nothing", 24)).arrange(RIGHT, buff=0.25)
        cost2 = VGroup(cook(TEMP, 0.6), T("a temporary cook: costs wages", 24, TEMP)).arrange(RIGHT, buff=0.25)
        cost1.move_to([LOGX, -2.4, 0], aligned_edge=LEFT)
        cost2.move_to([LOGX, -3.0, 0], aligned_edge=LEFT)
        self.say("thrifty")
        self.play(FadeOut(VGroup(logh, *logs, x7, tk[7])), FadeOut(hl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wrong), run_time=0.5)
        self.play(Create(wrong_x), run_time=0.4)
        self.at(2)
        self.play(FadeIn(right, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(mgr, color=MGR, scale_factor=1.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(cost1, shift=UP * 0.1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(cost2, shift=UP * 0.1), run_time=0.5)
        self.at(6)
        self.play(Indicate(ph, color=PHONE, scale_factor=1.2), Indicate(slots, color=WHITE), run_time=0.9)
        self.hold()

        # ---- who finished first ----
        o500 = T("about 500 ms: orders 1, 2, 5, 6", 26, GOOD).move_to([LOGX, -1.1, 0], aligned_edge=LEFT)
        o1000 = T("about 1,000 ms: orders 3, 4", 26, GOOD).move_to([LOGX, -1.65, 0], aligned_edge=LEFT)

        def done(ns):
            return [*[tk[n].animate.scale(1.2).set_opacity(0) for n in ns],
                    *[Flash(tk[n].get_center(), color=GOLD_M, line_length=0.15, flash_radius=0.45) for n in ns]]
        self.say("order")
        self.play(FadeOut(VGroup(wrong, wrong_x, right, cost1, cost2)), run_time=0.5)
        self.at(1)
        self.play(*done((1, 2, 5, 6)), FadeIn(o500), run_time=0.8)
        self.play(tk[3].animate.scale(0.8).move_to(HEADP[0]), tk[4].animate.scale(0.8).move_to(HEADP[3]), run_time=0.8)
        self.at_text("and orders 3", lead=0.2)
        self.play(*done((3, 4)), FadeIn(o1000), run_time=0.8)
        self.at(2)
        self.play(Indicate(VGroup(cooks[2], cooks[3]), color=TEMP, scale_factor=1.1), run_time=1.0)
        self.hold()

        br1 = VGroup(T("a real kitchen: oldest ticket first", 26), tick(True, 0.2)).arrange(RIGHT, buff=0.3)
        br2 = VGroup(T("a pool: no such promise", 26, YELLOW_M), tick(False, 0.2)).arrange(RIGHT, buff=0.3)
        br1.move_to([LOGX, -2.3, 0], aligned_edge=LEFT)
        br2.move_to([LOGX, -2.9, 0], aligned_edge=LEFT)
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(br1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(br2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= a rail with no end =================
        long_rail = rail_line(-3.8, -0.4, RAIL_Y)
        more = T("...", 30, GREY_B).move_to([-4.1, RAIL_Y + 0.05, 0])
        max64 = T("maximum pool size: 64", 24, GREY_A).move_to(max_l)
        temp64 = T("temporary: up to 62", 24, TEMP).move_to(temp_l)
        rail_u = VGroup(T("work queue: no limit", 22, GOLD_M), M("LinkedBlockingQueue", 22, GOLD_M)).arrange(DOWN, buff=0.08).move_to([-2.4, 1.65, 0])
        self.say("back64")
        self.play(FadeOut(VGroup(o500, o1000, br1, br2)), *[FadeOut(c) for c in cooks.values()], FadeIn(pspots),
                  FadeIn(tspots), run_time=0.7)
        self.play(Transform(max_l, max64), Transform(temp_l, temp64), run_time=0.7)
        self.at(1)
        self.play(Transform(rail_l, rail_u), run_time=0.7)
        self.at(2)
        self.play(Transform(rail, long_rail), FadeOut(slots), FadeIn(more), run_time=0.9)
        self.hold()

        s3, s4 = strike(rules[2]), strike(rules[3])
        dead = T("dead code", 28, BAD).next_to(max_l, RIGHT, buff=0.3)
        self.say("never")
        self.play(rules[1].animate.set_color(GOLD_M), run_time=0.5)
        self.at(1)
        self.play(Create(s3), rules[2].animate.set_opacity(0.4), tspots.animate.set_opacity(0.25), ph.animate.set_opacity(0.35),
                  run_time=0.7)
        self.at(2)
        self.play(Create(s4), rules[3].animate.set_opacity(0.4), door.animate.set_opacity(0.35), run_time=0.7)
        self.at(3)
        self.play(FadeIn(dead, scale=1.2), Indicate(max_l, color=BAD), run_time=0.8)
        self.hold()

        max4 = T("maximum pool size: 4", 24, GREY_A).move_to(max_l)
        u_logs = ["task 5 accepted: threads=2 queued=3", "task 6 accepted: threads=2 queued=4",
                  "task 7 accepted: threads=2 queued=5", "...", "all done in 2019 ms, completed tasks: 7"]
        ulog = [M(s, 22, GOOD if "all" in s else GREY_A).move_to([LOGX, -1.4 - 0.33 * i, 0], aligned_edge=LEFT)
                for i, s in enumerate(u_logs)]
        uh = T("the same seven orders, with that queue", 22, GREY_B).move_to([LOGX, -1.05, 0], aligned_edge=LEFT)
        u2 = {}
        self.say("demo2")
        self.play(FadeOut(dead), Transform(max_l, max4), FadeIn(uh), run_time=0.6)
        for n in (1, 2):
            u2[n] = ticket(n, s=0.8).move_to(HEADP[n - 1])
        ucooks = VGroup(*[cook(PERM).move_to(CKP[i]) for i in (0, 1)])
        self.play(FadeOut(pspots), FadeIn(ucooks), FadeIn(u2[1]), FadeIn(u2[2]), run_time=0.6)
        for n in range(3, 8):
            u2[n] = ticket(n, s=0.85).move_to(SLOTS5[n - 3])
        self.play(LaggedStart(*[FadeIn(u2[n], shift=DOWN * 0.15) for n in range(3, 8)], lag_ratio=0.25),
                  LaggedStart(*[FadeIn(l) for l in ulog[:3]], lag_ratio=0.4), run_time=1.6)
        self.at(1)
        for a, b in ((3, 4), (5, 6), (7, None)):
            prev = [n for n in u2 if u2[n] is not None and u2[n].get_x() > -0.5]
            anims = [u2[n].animate.scale(1.2).set_opacity(0) for n in prev]
            self.play(*anims, run_time=0.35)
            for n in prev:
                u2[n] = None
            mv = [u2[a].animate.scale(0.8 / 0.85).move_to(HEADP[0])]
            if b:
                mv.append(u2[b].animate.scale(0.8 / 0.85).move_to(HEADP[1]))
            self.play(*mv, run_time=0.45)
        self.play(*[u2[n].animate.set_opacity(0) for n in u2 if u2[n] is not None], FadeIn(ulog[3]), FadeIn(ulog[4]),
                  run_time=0.6)
        self.hold()

        # ---- overload ----
        a1 = T("orders arrive: 400 a second", 26).move_to([LOGX, -1.1, 0], aligned_edge=LEFT)
        a2 = T("the kitchen finishes: 300 a second", 26, PERM).move_to([LOGX, -1.6, 0], aligned_edge=LEFT)
        a3 = T("the rail grows: 100 every second", 26, GOLD_M).move_to([LOGX, -2.1, 0], aligned_edge=LEFT)
        mins = ValueTracker(0)
        cnt = counter2("after {:.1f} min: {:,} waiting", lambda: (round(mins.get_value(), 1), int(round(mins.get_value() * 10) * 600)),
                       [LOGX, -2.65, 0], 26, BAD, edge=LEFT)
        PILE = [np.array([-3.45 + 0.27 * (k % 10), 1.05 + 0.22 * (k // 10), 0]) for k in range(50)]
        pile = VGroup(*[ticket(s=0.3).move_to(PILE[k]) for k in range(50)])
        wait3 = T("a new order waits over 3 minutes", 26, BAD).move_to([LOGX, -3.15, 0], aligned_edge=LEFT)
        self.say("safe")
        self.play(FadeOut(VGroup(uh, *ulog)), FadeOut(rail_l), run_time=0.5)
        self.at(2)
        self.play(FadeIn(a1), run_time=0.5)
        self.at_text("can finish", lead=0.3)
        self.play(FadeIn(a2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(a3), run_time=0.5)
        self.at(4)
        self.add(cnt)

        def pile_upd(g):
            n = int(min(50, mins.get_value() / 10 * 50))
            for k, t in enumerate(g):
                t.set_opacity(1 if k < n else 0)
        pile.set_opacity(0)
        pile.add_updater(pile_upd)
        self.add(pile)
        self.play(mins.animate.set_value(10), run_time=self.left_text("and a new") , rate_func=linear)
        pile.clear_updaters()
        self.play(FadeIn(wait3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        heap_b = Rectangle(width=4.0, height=0.36, stroke_color=GREY_B, stroke_width=2).move_to([4.0, -1.5, 0])
        heap_f = Rectangle(width=0.01, height=0.36, stroke_width=0).set_fill(BAD, 0.85).move_to(heap_b.get_left(), aligned_edge=LEFT)
        heap_l = T("heap", 24, GREY_A).next_to(heap_b, LEFT, buff=0.2)
        nobody = T("dinners nobody will eat", 24, GOLD_M).move_to([-2.2, 0.5, 0])
        self.say("dinner")
        self.play(FadeIn(nobody), run_time=0.6)
        self.at(1)
        self.play(FadeOut(VGroup(a1, a2, a3)), run_time=0.4)
        self.play(FadeIn(heap_b), FadeIn(heap_l), run_time=0.4)
        self.play(heap_f.animate.stretch_to_fit_width(4.0).move_to(heap_b), run_time=self.left() * 0.8, rate_func=rate_functions.ease_in_quad)
        self.hold()

        # ---- the cached pool, the other way ----
        kitchen = VGroup(mgr, mgr_l, ph, rail, more, tspots, ucooks, stoves, perm_l, temp_l, brace, max_l, door,
                         pile, nobody, heap_b, heap_f, heap_l, cnt, wait3, rules, s3, s4)
        cached = M("newCachedThreadPool()", 28, TEMP).move_to([0, 2.7, 0])
        nroom = T("a rail with no room at all", 26, GREY_A).move_to([0, 2.05, 0])
        crowd = VGroup(*[cook(TEMP, 0.55) for _ in range(24)]).arrange_in_grid(rows=3, cols=8, buff=(0.45, 0.3))
        crowd.move_to([0, 0.1, 0])
        salad = T("last lesson's manager, hiring a cook for every salad", 28, MGR).move_to([0, -2.0, 0])
        cnt.clear_updaters()
        self.say("cached")
        self.play(FadeOut(kitchen), run_time=0.7)
        self.play(FadeIn(cached), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nroom), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in crowd], lag_ratio=0.06), run_time=2.0)
        self.at(2)
        self.play(FadeIn(salad, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the shape that pushes back =================
        rail_b = rail_line(-3.7, -1.1, RAIL_Y)
        slots_b = VGroup(*[slot_box(p) for p in SLOTS2])
        rail_lb = T("a rail with a limit: 2", 24, GREY_A).move_to([-2.4, 1.7, 0])
        max_b = T("a maximum that isn't endless: 4", 24, GREY_A).move_to(max_l)
        temp_b = T("temporary: up to 2", 24, TEMP).move_to(temp_l)
        pcooks = VGroup(*[cook(PERM).move_to(CKP[i]) for i in (0, 1)])
        tsp2 = VGroup(*[spot(TEMP).move_to(CKP[i]) for i in (2, 3)])
        door2 = box("door policy", DOOR, h=0.7, size=24).move_to([-5.2, 0.2, 0])
        ph2 = phone().move_to(PHONE_P)
        rule = VGroup(T("An unbounded queue never says no:", 28), T("the pool never grows, and never rejects.", 28),
                      T("Give the queue a limit.", 28, YELLOW_M)).arrange(DOWN, buff=0.15)
        rule_b = SurroundingRectangle(rule, buff=0.22, corner_radius=0.12, color=YELLOW_M, stroke_width=2.5)
        rule_g = VGroup(rule_b, rule).move_to([2.3, -1.85, 0])
        self.say("shape")
        self.play(FadeOut(VGroup(cached, nroom, crowd, salad)), run_time=0.6)
        self.play(FadeIn(VGroup(mgr, mgr_l, ph2, rail_b, slots_b, rail_lb, pcooks, tsp2, stoves, perm_l, brace, door2)),
                  FadeIn(max_b), FadeIn(temp_b), run_time=0.9)
        self.at(1)
        self.play(Circumscribe(door2, color=DOOR, buff=0.08), run_time=0.9)
        self.play(FadeIn(rule_g, shift=UP * 0.1), run_time=0.8)
        self.hold()

        # ================= the code, last =================
        hl_c = {"2, 4,": PERM, "ArrayBlockingQueue": GOLD_M, "AbortPolicy": DOOR}
        jsrc = ["new ThreadPoolExecutor(", "    2, 4,         // core, max", "    60, SECONDS,  // keep-alive",
                "    new ArrayBlockingQueue<>(2),", "    new AbortPolicy());"]
        ksrc = ["ThreadPoolExecutor(", "    2, 4,         // core, max", "    60, SECONDS,  // keep-alive",
                "    ArrayBlockingQueue(2),", "    AbortPolicy())"]
        jc, kc = code_block(jsrc, 24, hl_c), code_block(ksrc, 24, hl_c)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.6)
        notes = VGroup(T("keep-alive: how long an idle temp stays before he's sent home", 24, TEMP),
                       T("SECONDS and AbortPolicy are imported from TimeUnit and ThreadPoolExecutor", 20, GREY_B)
                       ).arrange(DOWN, buff=0.2).move_to([0, -2.2, 0])
        self.say("code")
        self.play(FadeOut(VGroup(mgr, mgr_l, ph2, rail_b, slots_b, rail_lb, pcooks, tsp2, stoves, perm_l, brace, door2, max_b,
                                 temp_b, rule_g)), run_time=0.6)
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.8)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=PERM, scale_factor=1.03), run_time=0.8)
        self.at_text("and a keep-alive", lead=0.3)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=TEMP, scale_factor=1.03), FadeIn(notes[0]), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[3], kc[3]), color=GOLD_M, scale_factor=1.03), run_time=0.7)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=DOOR, scale_factor=1.03), FadeIn(notes[1]), run_time=0.7)
        self.hold()

        # ================= the moral and a check =================
        mo1 = T("A maximum is the relief valve for a full rail.", 32)
        mo2 = T("The pool queues first, and grows second.", 32, YELLOW_M)
        mo3 = T("Give the queue a limit, or the maximum is just a number.", 32)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.play(FadeOut(cols), FadeOut(notes), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("core 2, max 4, a rail with room for 10. Eight orders, a minute each. How many cooking?", 28))
        qq.arrange(RIGHT, buff=0.25)
        fit(qq, 12.4).move_to(DOWN * 0.5)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("Two. Six wait on the rail, which never fills, so nobody phones.", 30, GOOD).move_to(DOWN * 1.6)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
