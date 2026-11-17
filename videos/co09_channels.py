from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bUNLIMITED\b", "unlimited"),
    (r"\bCONFLATED\b", "conflated"), (r"\bBlockingQueue\b", "Blocking Queue"), (r"\bfan-out\b", "fan out"),
    (r"\bfan-in\b", "fan in"),
]

# every spoken line, in order
N = {
    "open": "Between the kitchen and the dining room of an old house there's a hatch: a small window in the wall, with a "
            "shelf. The cook puts a plate on the shelf, and on the other side a helper takes it to the table.",
    "open2": "The shelf holds two plates. When it's full, the cook waits. When it's empty, the helper waits. And unlike "
             "a ring of the bell, a plate is eaten only once.",
    "shy": "Last lesson, the board and the bell sent every value to everyone. So here's a question that's easy to be shy "
           "about. How do you hand each plate to exactly one coroutine? And when the cook is done, how does the helper "
           "know that nothing more is coming?",
    "map": "Kotlin's hatch is a Channel. The cook calls send to put a plate in, and the helper calls receive to take one "
           "out. Each element is received exactly once. The shelf is the capacity: how many plates can wait before "
           "send has to pause. And waiting here means suspending: a helper at an empty hatch holds no thread at all.",
    "shrink": "Let's time it. The cook puts five plates through as fast as she can, and the helper needs 100 milliseconds "
              "per plate. The shelf holds two.",
    "q": "When does each send return?",
    "a": "The first three return at once: plate 1 goes straight into the waiting helper's hands, and plates 2 and 3 sit "
         "on the shelf. Plate 4 finds the shelf full, so the cook waits. Then one send returns every 100 milliseconds: "
         "at 101, then 201.",
    "bp": "The slow helper set the cook's pace. That's called backpressure, and it keeps plates from piling up.",
    "caps": "The shelf size changes everything. With no shelf at all, the default, called rendezvous, the cook hands "
            "each plate over directly, one every 100 milliseconds. UNLIMITED never makes her wait. And CONFLATED keeps "
            "one spot, where each new plate replaces the old one: the helper got plates 1 and 5.",
    "unl_joke": "UNLIMITED sounds generous, until the dining room is full of plates and the program runs out of memory, "
                "some hours later. So be suspicious of a shelf with no end.",
    "last": "Now the trap: the last plate. The helper loops: for each dish in the hatch, serve it. When does that loop "
            "end? Only when the channel is closed and empty. Delete the close, and the program never ends.",
    "last_joke": "The helper stands at the hatch all night with an empty tray, waiting for a plate that will never come. "
                 "Here the picture breaks: a real helper would see the cook take off her apron. A coroutine can't tell "
                 "later from never, until someone calls close. Or let produce close it for you, when its block ends.",
    "team": "One helper carries one plate at a time, so twenty dishes of about 100 milliseconds take two seconds. The "
            "fix in a real kitchen is plain: more helpers at the same hatch.",
    "fanout": "That's fan-out: several coroutines receive from one channel, and each plate still goes to exactly one of "
              "them. With four helpers, the twenty dishes took 614 milliseconds. One helper took 2,181, and ten took "
              "324.",
    "fanin": "And fan-in is the way back: every helper sends finished plates into a second channel, read at one table. "
             "Close it after the whole team is done, from a coroutine of its own, or that table waits all night too.",
    "cap_joke": "Why not start an async for every dish? Because ordering 5,000 loaves that way means 5,000 phone calls "
                "in the same second, and the baker takes the phone off the hook. A team of N helpers caps the work at N.",
    "select": "Last, a race. The cook phones two bakeries for bread. The corner bakery takes 300 milliseconds to answer, "
              "the market bakery 120. She takes the first answer and hangs up on the other. If neither answers in 500, "
              "she bakes her own.",
    "select_q": "Which answer does select return?",
    "select_a": "The market bakery's: plenty of sourdough, after 213 milliseconds on a cold, busy machine, not quite 120. "
                "select waits for the first clause that's ready, runs it, and drops the rest. With a budget of 100 "
                "milliseconds, the timer wins, and she bakes her own bread.",
    "select_rule": "Two rules. If two clauses are ready at once, the first one listed wins. And hanging up is your job: "
                   "cancel the losers yourself.",
    "code": "Here's the hatch in Kotlin, with Java's BlockingQueue below. A queue can't be closed, so Java sends an end "
            "marker instead.",
    "moral": "So, how do you hand each plate to exactly one coroutine? Through a channel, the hatch. The shelf sets the "
             "pace, a team of helpers caps the work, select takes whichever answer comes first, and close is the cook's "
             "word that the last plate is through.",
    "check": "Quick check. A hatch with no shelf, a fast cook, and a helper who needs 100 milliseconds per plate. How "
             "often does send return?",
    "check_a": "About once every 100 milliseconds. With no shelf, each send waits for the helper's hands.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole coroutines track (the cook is blue, helpers teal, waiting purple)
COOK, HELPER, SHELF, SUSP, BAD, CANCEL, TIMER, BAKERY, BELL, OK_ = (BLUE_M, TEAL_M, GOLD_M, PURPLE_M, RED_M, YELLOW_M,
                                                                    GREEN_M, GOLD_M, GOLD_M, GREEN_M)


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def plate(n, s=1.0, color=WHITE):
    rim = Circle(radius=0.3).set_stroke(color, 3).set_fill(GREY_E, 1)
    inner = Circle(radius=0.19).set_stroke(GREY_B, 1.5)
    t = T(str(n), 22, color).move_to(rim)
    return VGroup(rim, inner, t).scale(s).set_z_index(6)


def tag(text, color=SUSP, size=22):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.42).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def timer(color=TIMER, s=1.0):
    face = Circle(radius=0.36).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    knob = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.13).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    knob.next_to(face, UP, buff=0)
    hand = Line(ORIGIN, UP * 0.25, stroke_width=3, color=color)
    ticks = VGroup(*[Line(UP * 0.28, UP * 0.34, stroke_width=2, color=color).rotate(a, about_point=ORIGIN)
                     for a in np.arange(0, TAU, TAU / 8)])
    return VGroup(face, knob, ticks, hand).scale(s)


def bell_icon(color=BELL, s=1.0):
    body = VMobject().set_points_smoothly([[-0.5, -0.32, 0], [-0.36, 0.0, 0], [-0.3, 0.3, 0], [0, 0.48, 0],
                                           [0.3, 0.3, 0], [0.36, 0.0, 0], [0.5, -0.32, 0]])
    body.add_line_to(np.array([-0.5, -0.32, 0]))
    body.set_stroke(color, 3).set_fill(dim(color, 0.45), 1)
    rim = Line([-0.56, -0.33, 0], [0.56, -0.33, 0], stroke_width=5, color=color)
    clap = Circle(radius=0.08).set_stroke(color, 2).set_fill(color, 1).move_to([0, -0.45, 0])
    hang = Line([0, 0.48, 0], [0, 0.65, 0], stroke_width=4, color=color)
    return VGroup(hang, body, rim, clap).scale(s)


def shop_icon(s=1.0, color=BAKERY):
    body = Rectangle(width=1.8, height=1.1).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    stripes = VGroup(*[Polygon([x, 0, 0], [x + 0.3, 0, 0], [x + 0.3, -0.32, 0], [x, -0.32, 0])
                       .set_stroke(color, 2).set_fill(dim(color, 0.6 if i % 2 == 0 else 0.2), 1)
                       for i, x in enumerate(np.arange(-1.05, 0.95, 0.3))])
    stripes.next_to(body, UP, buff=0)
    door = Rectangle(width=0.42, height=0.62).set_stroke(color, 2.5).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.31)
    return VGroup(body, stripes, door).scale(s)


def table_icon(w=1.6, color=GREY_A):
    top = Rectangle(width=w, height=0.14).set_stroke(color, 3).set_fill(GREY_D, 1)
    legs = VGroup(*[Line(UP * 0, DOWN * 0.55, stroke_width=4, color=color).move_to(top.get_bottom() + DOWN * 0.28 + RIGHT * dx)
                    for dx in (-w / 2 + 0.18, w / 2 - 0.18)])
    return VGroup(top, legs)


def moon(s=1.0):
    c = Circle(radius=0.38).set_stroke(YELLOW_M, 2.5).set_fill(dim(YELLOW_M, 0.5), 1)
    cut = Circle(radius=0.34).set_stroke(width=0).set_fill(BLACK, 1).move_to([0.2, 0.12, 0])
    return VGroup(c, cut).scale(s)


def phone_off(s=1.0, color=GREY_A):
    base = RoundedRectangle(corner_radius=0.08, width=0.9, height=0.4).set_stroke(color, 2.5).set_fill("#151515", 1)
    hand = RoundedRectangle(corner_radius=0.1, width=0.9, height=0.2).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    hand.rotate(0.5).next_to(base, UP + RIGHT, buff=0.02)
    return VGroup(base, hand).scale(s)


# the hatch, as it sits on screen
WALL_X = 0.0
OPEN_LO, OPEN_HI = 0.35, 1.95
SPOT_Y = 0.78
COOK_P = np.array([-2.3, 0.85, 0])
HELP_P = np.array([2.3, 0.85, 0])
HAND_C = np.array([-1.55, 0.78, 0])
HAND_H = np.array([1.55, 0.78, 0])


def hatch(x=WALL_X, spots=2):
    up = Rectangle(width=0.45, height=3.15 - OPEN_HI).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    up.move_to([x, (3.15 + OPEN_HI) / 2, 0])
    lo = Rectangle(width=0.45, height=OPEN_LO + 0.75).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    lo.move_to([x, (OPEN_LO - 0.75) / 2, 0])
    plank = Rectangle(width=2.1, height=0.12).set_stroke(SHELF, 2.5).set_fill(dim(SHELF, 0.5), 1)
    plank.move_to([x, OPEN_LO + 0.06, 0])
    return VGroup(up, lo, plank)


def spot_xy(i, x=WALL_X):
    return np.array([x - 0.45 + 0.9 * i, SPOT_Y, 0])


class Co09Channels(Narrated):
    """co-09, section 0 (a short tour of the lesson): the hatch between kitchen and dining room with a shelf for two
    plates; the shy question (each plate to exactly one coroutine, and how the helper knows nothing more is coming);
    Channel, send, receive, capacity, suspending; five plates through a two-plate shelf (0, 0, 0, 101, 201) and
    backpressure; four shelf sizes from ChannelCapacities; unlimited and memory; the last plate (no close: the helper
    waits all night; produce closes it); a team of helpers (614, 2,181 and 324 ms), fan-in to one table, why not async
    for everything; select on two bakeries (213 ms, the market) and the kitchen timer; the code; moral; check."""

    def construct(self):
        self.title_card("The hatch and the last plate", "channels, a team of helpers, and select")

        # ================= the hatch =================
        wall = hatch()
        k_l = T("kitchen", 26, GREY_A).move_to([-3.6, 2.9, 0])
        d_l = T("dining room", 26, GREY_A).move_to([3.6, 2.9, 0])
        cook = person(COOK, 1.3).move_to(COOK_P)
        helper = person(HELPER, 1.3).move_to(HELP_P)
        tbl = table_icon(1.6).move_to([5.2, 0.1, 0])
        self.say("open")
        self.play(FadeIn(wall), FadeIn(k_l), FadeIn(d_l), run_time=0.8)
        self.at_text("The cook puts", lead=0.3)
        self.play(FadeIn(cook), FadeIn(helper), FadeIn(tbl), run_time=0.6)
        p0 = plate("", 1.0).move_to(HAND_C)
        self.play(FadeIn(p0, scale=0.7), run_time=0.3)
        self.play(p0.animate.move_to(spot_xy(0)), run_time=0.6)
        self.at_text("on the other side", lead=0.3)
        self.play(p0.animate.move_to(HAND_H), run_time=0.6)
        self.play(p0.animate.move_to(tbl[0].get_top() + UP * 0.32), run_time=0.7)
        self.hold()

        pa, pb, pc = plate("", 1.0).move_to(spot_xy(0)), plate("", 1.0).move_to(spot_xy(1)), plate("", 1.0).move_to(HAND_C)
        full_t = tag("full: the cook waits", SUSP).move_to([-2.3, -0.65, 0])
        empty_t = tag("empty: the helper waits", SUSP).move_to([2.6, -0.65, 0])
        bl = bell_icon(BELL, 0.7).move_to([-4.6, -2.0, 0])
        bl_t = T("a ring: heard by everyone", 24, BELL).next_to(bl, RIGHT, buff=0.3)
        pl = plate("", 0.8).move_to([1.4, -2.0, 0])
        pl_t = T("a plate: eaten once", 24, WHITE).next_to(pl, RIGHT, buff=0.3)
        self.say("open2")
        self.play(FadeOut(p0), FadeIn(pa, scale=0.7), FadeIn(pb, scale=0.7), run_time=0.6)
        self.at_text("When it's full", lead=0.3)
        self.play(FadeIn(pc, scale=0.7), FadeIn(full_t), run_time=0.5)
        self.at_text("When it's empty", lead=0.3)
        self.play(FadeOut(pa), FadeOut(pb), FadeOut(pc), FadeOut(full_t), FadeIn(empty_t), run_time=0.6)
        self.at_text("And unlike", lead=0.3)
        self.play(FadeIn(bl), FadeIn(bl_t), run_time=0.5)
        self.play(FadeIn(pl), FadeIn(pl_t), run_time=0.5)
        self.hold()

        q1 = T("How do you hand each plate to exactly one coroutine?", 30).move_to([0, -2.0, 0])
        q2 = T("And how does the helper know that nothing more is coming?", 30).move_to([0, -2.85, 0])
        self.say("shy")
        self.play(FadeOut(VGroup(bl, bl_t, pl, pl_t, empty_t)), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(q1, q2)), run_time=0.5)

        # ================= map it =================
        ch_l = M("Channel", 26, SHELF).move_to([WALL_X, 3.35, 0])
        snd = Arrow(HAND_C + UP * 0.55, spot_xy(0) + UP * 0.55, buff=0.05, stroke_width=3, color=COOK, max_tip_length_to_length_ratio=0.25)
        snd_l = M("send", 24, COOK).next_to(snd, UP, buff=0.1)
        rcv = Arrow(spot_xy(1) + UP * 0.55, HAND_H + UP * 0.55, buff=0.05, stroke_width=3, color=HELPER, max_tip_length_to_length_ratio=0.25)
        rcv_l = M("receive", 24, HELPER).next_to(rcv, UP, buff=0.1)
        cap_l = T("the shelf: capacity = 2", 24, SHELF).move_to([WALL_X, -0.85, 0])
        once = T("each element is received exactly once", 26, WHITE).move_to([0, -1.75, 0])
        nothr = T("waiting = suspending: an empty hatch holds no thread", 26, SUSP).move_to([0, -2.55, 0])
        code0 = M("val hatch = Channel<Int>(capacity = 2)", 26, t2c={"Channel": SHELF}).move_to([0, -3.25, 0])
        self.say("map")
        self.play(FadeIn(ch_l), run_time=0.5)
        self.at_text("The cook calls", lead=0.3)
        self.play(GrowArrow(snd), FadeIn(snd_l), run_time=0.6)
        self.at_text("and the helper", lead=0.3)
        self.play(GrowArrow(rcv), FadeIn(rcv_l), run_time=0.6)
        self.at_text("Each element", lead=0.3)
        self.play(FadeIn(once), run_time=0.5)
        self.at_text("The shelf is", lead=0.3)
        self.play(FadeIn(cap_l), Indicate(wall[2], color=SHELF), run_time=0.7)
        self.at_text("And waiting", lead=0.3)
        self.play(FadeIn(nothr), run_time=0.5)
        self.play(FadeIn(code0), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(snd, snd_l, rcv, rcv_l, once, nothr, code0, cap_l)), run_time=0.5)

        # ================= five plates through a shelf of two =================
        stack = [plate(i, 1.0) for i in range(1, 6)]
        for i, p in enumerate(stack):
            p.move_to([-4.5 + 0.0 * i, -0.45 + 0.13 * i, 0])
        stack_l = T("five plates, as fast as she can", 22, COOK).move_to([-4.5, -1.15, 0])
        hl_l = T("100 ms per plate", 22, HELPER).move_to([2.3, -0.15, 0])
        clock = {"m": T("t = 0 ms", 26, GREY_A).move_to([4.6, 2.3, 0])}
        ret = M("send() returned at", 24, COOK).move_to([-4.6, -2.3, 0], aligned_edge=LEFT)
        slots_x = [-0.65 + 1.05 * i for i in range(5)]
        ret_v = [M(v, 24, COOK).move_to([x, -2.3, 0]) for v, x in zip(("0", "0", "0", "101", "201"), slots_x)]
        ret_q = [M("?", 24, GREY_B).move_to([x, -2.3, 0]) for x in slots_x]
        ms_l = M("ms", 24, COOK).move_to([slots_x[-1] + 0.75, -2.3, 0])
        self.say("shrink")
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in stack], lag_ratio=0.15), FadeIn(stack_l), run_time=0.9)
        self.at_text("and the helper", lead=0.3)
        self.play(FadeIn(hl_l), FadeIn(clock["m"]), run_time=0.5)
        self.at_text("The shelf holds", lead=0.3)
        self.play(Indicate(wall[2], color=SHELF), run_time=0.7)
        self.hold()

        self.say("q")
        self.play(FadeIn(ret), *[FadeIn(r) for r in ret_q], FadeIn(ms_l), run_time=0.5)
        self.hold(after=0)
        self.predict()

        def set_clock(t):
            new = T(f"t = {t} ms", 26, GREY_A).move_to([4.6, 2.3, 0])
            old = clock["m"]
            clock["m"] = new
            return [FadeOut(old), FadeIn(new)]

        wait_t = tag("waits", SUSP).move_to(COOK_P + UP * 1.05)
        self.say("a")
        # plate 1 straight to the waiting helper, 2 and 3 onto the shelf: three sends return at 0
        self.play(stack[0].animate.move_to(HAND_H), FadeTransform(ret_q[0], ret_v[0]), run_time=0.6)
        self.at_text("and plates 2", lead=0.3)
        self.play(stack[1].animate.move_to(spot_xy(0)), FadeTransform(ret_q[1], ret_v[1]), run_time=0.45)
        self.play(stack[2].animate.move_to(spot_xy(1)), FadeTransform(ret_q[2], ret_v[2]), run_time=0.45)
        self.at_text("Plate 4", lead=0.3)
        self.play(stack[3].animate.move_to(HAND_C), FadeIn(wait_t), run_time=0.6)
        self.at_text("Then one send", lead=0.3)
        # 100 ms: plate 1 reaches the table; plate 2 to the helper; the shelf moves up; plate 4 goes on
        self.play(stack[0].animate.move_to(tbl[0].get_top() + UP * 0.32), *set_clock(101), run_time=0.5)
        self.play(stack[1].animate.move_to(HAND_H), stack[2].animate.move_to(spot_xy(0)), run_time=0.4)
        self.play(stack[3].animate.move_to(spot_xy(1)), FadeTransform(ret_q[3], ret_v[3]), run_time=0.4)
        self.play(stack[4].animate.move_to(HAND_C), run_time=0.3)
        self.at_text("then 201", lead=0.4)
        self.play(FadeOut(stack[0]), stack[1].animate.move_to(tbl[0].get_top() + UP * 0.32), *set_clock(201), run_time=0.5)
        self.play(stack[2].animate.move_to(HAND_H), stack[3].animate.move_to(spot_xy(0)), run_time=0.4)
        self.play(stack[4].animate.move_to(spot_xy(1)), FadeTransform(ret_q[4], ret_v[4]), FadeOut(wait_t), run_time=0.4)
        self.hold()

        self.say("bp")
        self.play(Indicate(VGroup(*ret_v[3:]), color=WHITE), run_time=0.8)
        self.at_text("That's called", lead=0.3)
        bp_l = T("backpressure: the slow side sets the pace", 26, SUSP).move_to([0, -3.05, 0])
        self.play(FadeIn(bp_l, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= four shelves =================
        rows = [("RENDEZVOUS", "[38, 142, 247, 348, 448]", "[1, 2, 3, 4, 5]"),
                ("capacity 2", "[0, 0, 0, 101, 201]", "[1, 2, 3, 4, 5]"),
                ("UNLIMITED", "[0, 0, 0, 0, 0]", "[1, 2, 3, 4, 5]"),
                ("CONFLATED", "[3, 3, 3, 3, 3]", "[1, 5]")]
        C1, C2, C3, TY = -5.6, -2.6, 2.5, -1.0
        hdr = VGroup(T("the shelf", 22, GREY_B).move_to([C1, TY, 0], aligned_edge=LEFT),
                     T("send() returned at, in ms", 22, GREY_B).move_to([C2, TY, 0], aligned_edge=LEFT),
                     T("the helper got", 22, GREY_B).move_to([C3, TY, 0], aligned_edge=LEFT))
        trs = []
        for i, (a, b, c) in enumerate(rows):
            y = TY - 0.5 * (i + 1)
            trs.append(VGroup(M(a, 22, SHELF).move_to([C1, y, 0], aligned_edge=LEFT),
                              M(b, 22, COOK).move_to([C2, y, 0], aligned_edge=LEFT),
                              M(c, 22, HELPER).move_to([C3, y, 0], aligned_edge=LEFT)))
        self.say("caps")
        rest = [s for s in stack[1:]]
        self.play(FadeOut(VGroup(*rest, stack_l, hl_l, ret, *ret_v, ms_l, bp_l, clock["m"])), run_time=0.5)
        self.play(FadeIn(hdr), FadeIn(trs[1]), run_time=0.5)
        self.at_text("With no shelf", lead=0.3)
        self.play(FadeIn(trs[0]), wall[2].animate.set_opacity(0.2), run_time=0.6)
        self.at_text("UNLIMITED never", lead=0.3)
        self.play(FadeIn(trs[2]), wall[2].animate.set_opacity(1), run_time=0.6)
        self.at_text("And CONFLATED", lead=0.3)
        self.play(FadeIn(trs[3]), run_time=0.5)
        c1 = plate(1, 1.0).move_to(spot_xy(0) + RIGHT * 0.45)
        self.play(FadeIn(c1, scale=0.7), run_time=0.3)
        for n in (2, 3, 4, 5):
            cn = plate(n, 1.0).move_to(HAND_C)
            self.play(FadeIn(cn, scale=0.7), run_time=0.12)
            self.play(cn.animate.move_to(c1), c1.animate.shift(DOWN * 0.6).set_opacity(0), run_time=0.3)
            self.remove(c1)
            c1 = cn
        self.at_text("the helper got", lead=0.3)
        self.play(Indicate(trs[3][2], color=WHITE), run_time=0.8)
        self.hold()

        pile = VGroup(*[plate("", 0.6).move_to([1.2 + 0.45 * (i % 9), -0.2 + 0.32 * (i // 9) + 0.0, 0]) for i in range(18)])
        oom = T("OutOfMemoryError, some hours later", 26, BAD).move_to([3.0, 2.3, 0])
        self.say("unl_joke")
        self.play(FadeOut(c1), Indicate(trs[2], color=WHITE), run_time=0.7)
        self.at_text("until the dining", lead=0.3)
        self.play(FadeOut(helper), FadeOut(tbl), LaggedStart(*[FadeIn(p, scale=0.6) for p in pile], lag_ratio=0.06), run_time=1.3)
        self.at_text("runs out", lead=0.3)
        self.play(FadeIn(oom), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the last plate =================
        wall = hatch()
        cook = person(COOK, 1.3).move_to(COOK_P)
        helper = person(HELPER, 1.3).move_to(HELP_P)
        apron = RoundedRectangle(corner_radius=0.05, width=0.38, height=0.36).set_stroke(WHITE, 2).set_fill(GREY_C, 1)
        apron.move_to(cook[0].get_center() + DOWN * 0.03).set_z_index(3)
        src = ["launch {", "    for (dish in dinner) hatch.send(dish)", "    hatch.close()   // the last plate", "}",
               "for (dish in hatch) serve(dish)   // until closed and empty"]
        lp = code_block(src, 24, {"hatch.close()": CANCEL, "// the last plate": GREY_B, "// until closed and empty": GREY_B})
        lp.move_to([0, -2.05, 0])
        self.say("last")
        self.play(FadeIn(wall), FadeIn(cook), FadeIn(apron), FadeIn(helper), run_time=0.6)
        self.at_text("The helper loops", lead=0.3)
        self.play(FadeIn(lp[4]), run_time=0.6)
        self.play(FadeIn(lp[:4]), run_time=0.6)
        self.at_text("Only when", lead=0.3)
        self.play(Indicate(lp[2], color=CANCEL), run_time=0.9)
        self.at_text("Delete the close", lead=0.3)
        strike = Line(lp[2].get_left() + LEFT * 0.05, lp[2].get_right() + RIGHT * 0.05, stroke_width=4, color=BAD)
        self.play(Create(strike), lp[2].animate.set_opacity(0.4), run_time=0.6)
        self.hold()

        tray = RoundedRectangle(corner_radius=0.04, width=0.7, height=0.08).set_stroke(GREY_A, 2).set_fill(GREY_D, 1)
        tray.move_to(HAND_H)
        mn = moon(1.0).move_to([4.6, 2.5, 0])
        night = T("all night", 26, YELLOW_M).next_to(mn, DOWN, buff=0.2)
        apron_l = T("a real helper sees this", 24, GREY_A).move_to([-2.3, -0.35, 0])
        produce = M("val hatch = produce { for (dish in dinner) send(dish) }", 24, t2c={"produce": CANCEL}).move_to([0, -3.15, 0])
        pr_l = T("closes the hatch when its block ends", 24, CANCEL).move_to([0, 3.4, 0])
        self.say("last_joke")
        self.play(FadeIn(tray), FadeIn(mn), FadeIn(night), run_time=0.7)
        self.play(Wiggle(helper, scale_value=1.05, rotation_angle=0.03 * TAU), run_time=0.8)
        self.at_text("Here the picture", lead=0.3)
        self.play(apron.animate.shift(LEFT * 0.9 + DOWN * 0.4).set_opacity(0.5), FadeIn(apron_l), run_time=0.8)
        self.at_text("A coroutine can't", lead=0.3)
        self.play(Uncreate(strike), lp[2].animate.set_opacity(1), run_time=0.6)
        self.play(Indicate(lp[2], color=CANCEL), run_time=0.8)
        self.at_text("Or let produce", lead=0.3)
        self.play(FadeOut(lp), FadeIn(produce), run_time=0.6)
        self.play(FadeIn(pr_l), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= a team of helpers =================
        WX = -2.6
        wall = hatch(WX)
        cook = person(COOK, 1.2).move_to([WX - 2.2, 0.85, 0])
        HX = [WX + 1.6, WX + 2.6, WX + 3.6, WX + 4.6]
        helpers = [person(HELPER, 1.1).move_to([HX[0], 0.85, 0])] + [person(HELPER, 1.1).move_to([x, 0.85, 0]) for x in HX[1:]]
        tbl = table_icon(1.4).move_to([5.4, 0.1, 0])
        tbl_l = T("one table", 22, GREY_A).next_to(tbl, DOWN, buff=0.15)
        one_l = T("one helper: 20 dishes, about 2 seconds", 24, HELPER).move_to([1.5, 2.85, 0])
        self.say("team")
        self.play(FadeIn(wall), FadeIn(cook), FadeIn(helpers[0]), FadeIn(tbl), run_time=0.6)
        for n in range(1, 4):
            d = plate(n, 0.8).move_to(spot_xy(0, WX))
            self.play(FadeIn(d, scale=0.7), run_time=0.15)
            self.play(d.animate.move_to(helpers[0].get_center() + UP * 0.65), run_time=0.3)
            self.play(d.animate.move_to(tbl[0].get_top() + UP * 0.25), run_time=0.45)
            self.play(FadeOut(d), run_time=0.12)
        self.play(FadeIn(one_l), run_time=0.5)
        self.at_text("more helpers", lead=0.3)
        self.play(LaggedStart(*[FadeIn(h, shift=LEFT * 0.2) for h in helpers[1:]], lag_ratio=0.2), run_time=0.8)
        self.hold()

        fo_l = T("fan-out: each plate goes to exactly one helper", 24, HELPER).move_to([1.5, 2.85, 0])
        BY0, BS = -1.45, 0.6
        bars = []
        for i, (lab, ms) in enumerate((("1 helper", 2181), ("4 helpers", 614), ("10 helpers", 324))):
            y = BY0 - BS * i
            r = Rectangle(width=ms * 0.0042, height=0.34).set_stroke(HELPER, 2).set_fill(dim(HELPER, 0.4), 1)
            r.move_to([-4.2, y, 0], aligned_edge=LEFT)
            bars.append(VGroup(T(lab, 22, GREY_A).move_to([-4.4, y, 0], aligned_edge=RIGHT), r,
                               T(f"{ms:,} ms", 22, WHITE).next_to(r, RIGHT, buff=0.15)))
        self.say("fanout")
        self.play(FadeOut(one_l), FadeIn(fo_l), run_time=0.5)
        for n in range(1, 9):
            h = helpers[(n - 1) % 4]
            d = plate(n, 0.8).move_to(spot_xy(0, WX))
            self.play(FadeIn(d, scale=0.7), run_time=0.08)
            self.play(d.animate.move_to(h.get_center() + UP * 0.65), run_time=0.25)
            self.play(FadeOut(d, shift=RIGHT * 0.3), run_time=0.1)
        self.at_text("With four helpers", lead=0.3)
        self.play(FadeIn(bars[1]), run_time=0.6)
        self.at_text("One helper took", lead=0.3)
        self.play(FadeIn(bars[0]), run_time=0.6)
        self.at_text("and ten took", lead=0.3)
        self.play(FadeIn(bars[2]), run_time=0.6)
        self.hold()

        fi_l = T("fan-in: every helper brings plates to one table", 24, GREY_A).move_to([1.5, 2.85, 0])
        closer = VGroup(M("launch { team.joinAll(); table.close() }", 22, CANCEL)).move_to([1.3, -0.45, 0])
        self.say("fanin")
        self.play(FadeOut(fo_l), FadeIn(fi_l), FadeIn(tbl_l), run_time=0.5)
        ds = [plate(n, 0.8).move_to(h.get_center() + UP * 0.65) for n, h in zip((5, 6, 7, 8), helpers)]
        self.play(*[FadeIn(d, scale=0.7) for d in ds], run_time=0.3)
        self.play(*[d.animate.move_to(tbl[0].get_top() + UP * 0.25) for d in ds], run_time=0.8)
        self.play(*[FadeOut(d) for d in ds], run_time=0.2)
        self.at_text("Close it", lead=0.3)
        self.play(FadeIn(closer, shift=UP * 0.1), run_time=0.6)
        self.hold()

        calls = T("5,000 calls in the same second", 26, BAD).move_to([2.6, -0.45, 0])
        ph = phone_off(1.0).next_to(calls, LEFT, buff=0.35)
        capn = T("a team of N: at most N at once", 26, HELPER).move_to([1.5, 2.85, 0])
        self.say("cap_joke")
        self.play(FadeOut(closer), FadeOut(fi_l), run_time=0.4)
        self.at_text("Because ordering", lead=0.3)
        self.play(FadeIn(calls), run_time=0.5)
        self.at_text("and the baker", lead=0.3)
        self.play(FadeIn(ph, shift=UP * 0.1), run_time=0.5)
        self.at_text("A team of N", lead=0.3)
        self.play(FadeIn(capn), Indicate(VGroup(*helpers), color=HELPER, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= select: whichever answers first =================
        ck = person(COOK, 1.3).move_to([-4.9, 1.4, 0])
        tm = timer(TIMER, 0.9).move_to([-4.9, 2.95, 0]).shift(RIGHT * 1.0)
        corner = shop_icon(0.65).move_to([1.6, 2.55, 0])
        market = shop_icon(0.65).move_to([1.6, 0.6, 0])
        corner_l = T("corner bakery: 300 ms", 24, BAKERY).next_to(corner, RIGHT, buff=0.3)
        market_l = T("market bakery: 120 ms", 24, BAKERY).next_to(market, RIGHT, buff=0.3)
        l1 = DashedLine(ck.get_right() + RIGHT * 0.1, corner.get_left() + LEFT * 0.1, dash_length=0.1).set_stroke(GREY_B, 2.5)
        l2 = DashedLine(ck.get_right() + RIGHT * 0.1, market.get_left() + LEFT * 0.1, dash_length=0.1).set_stroke(GREY_B, 2.5)
        tm_l = T("500 ms: bake our own", 22, TIMER).next_to(tm, RIGHT, buff=0.25)

        def sx(ms):
            return -4.6 + ms * 0.0175

        TL = -1.3
        axis = Line([sx(0), TL - 1.45, 0], [sx(520), TL - 1.45, 0], stroke_width=2, color=GREY_B)
        tks = VGroup(*[VGroup(Line([sx(m), TL - 1.52, 0], [sx(m), TL - 1.38, 0], stroke_width=2, color=GREY_B),
                              T(str(m), 20, GREY_B).move_to([sx(m), TL - 1.75, 0])) for m in (0, 100, 200, 300, 400, 500)])
        ms_t = T("ms", 20, GREY_B).move_to([sx(520) + 0.4, TL - 1.75, 0])

        def tbar(ms, y, color, lab):
            r = Rectangle(width=ms * 0.0175, height=0.3).set_stroke(color, 2).set_fill(dim(color, 0.4), 1)
            r.move_to([sx(0), y, 0], aligned_edge=LEFT)
            return VGroup(T(lab, 22, color).move_to([sx(0) - 0.2, y, 0], aligned_edge=RIGHT), r)

        b_corner = tbar(300, TL, BAKERY, "corner")
        b_market = tbar(120, TL - 0.45, BAKERY, "market")
        b_timer = tbar(500, TL - 0.9, TIMER, "timer")
        self.say("select")
        self.play(FadeIn(ck), run_time=0.4)
        self.at_text("The cook phones", lead=0.3)
        self.play(FadeIn(corner), FadeIn(market), Create(l1), Create(l2), run_time=0.8)
        self.at_text("The corner bakery", lead=0.3)
        self.play(FadeIn(corner_l), FadeIn(b_corner), Create(axis), FadeIn(tks), FadeIn(ms_t), run_time=0.7)
        self.at_text("the market bakery", lead=0.3)
        self.play(FadeIn(market_l), FadeIn(b_market), run_time=0.6)
        self.at_text("If neither", lead=0.3)
        self.play(FadeIn(tm), FadeIn(tm_l), FadeIn(b_timer), run_time=0.6)
        self.hold()

        self.say("select_q")
        self.hold(after=0)
        self.predict(pos=(6.4, 3.15), edge=RIGHT)

        won = T("after 213 ms: market bakery: plenty of sourdough", 26, BAKERY).move_to([0, -3.35, 0])
        mark = DashedLine([sx(213), TL + 0.3, 0], [sx(213), TL - 1.2, 0], dash_length=0.08).set_stroke(WHITE, 2)
        hang = VGroup(T("hang up", 22, CANCEL), tick(False, 0.15).set_stroke(CANCEL, 4)).arrange(RIGHT, buff=0.12)
        hang.move_to(l1.get_center() + UP * 0.35)
        self.say("select_a")
        self.play(Indicate(b_market[1], color=WHITE), l2.animate.set_stroke(BAKERY, 4), run_time=0.7)
        self.play(Create(mark), FadeIn(won), run_time=0.7)
        self.at_text("select waits", lead=0.3)
        self.play(l1.animate.set_stroke(opacity=0.25), FadeIn(hang), run_time=0.6)
        self.at_text("With a budget", lead=0.3)
        b_t100 = tbar(100, TL - 0.9, TIMER, "timer")
        own = T("nobody answered within 100 ms: we bake our own bread", 26, TIMER).move_to([0, -3.35, 0])
        self.play(Transform(b_timer, b_t100), FadeOut(won), FadeOut(mark), FadeOut(hang), l1.animate.set_stroke(opacity=1),
                  l2.animate.set_stroke(GREY_B, 2.5), run_time=0.8)
        self.play(Wiggle(tm, scale_value=1.2, rotation_angle=0.08 * TAU), FadeIn(own), run_time=0.9)
        self.hold()

        r1 = T("1. Two ready at once? The first one listed wins.", 26, WHITE)
        r2 = T("2. Hanging up is your job: cancel the losers.", 26, CANCEL)
        rl = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.0, 0])
        self.say("select_rule")
        self.play(FadeOut(VGroup(b_corner, b_market, b_timer, axis, tks, ms_t, own)), run_time=0.5)
        self.at_text("If two", lead=0.3)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("And hanging", lead=0.3)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code =================
        k = code_block(["val hatch = Channel<String>(capacity = 2)",
                        "launch {",
                        "    for (dish in dinner) hatch.send(dish)   // suspends while the shelf is full",
                        "    hatch.close()                           // the last plate: the loop will end",
                        "}",
                        "for (dish in hatch) serve(dish)             // until closed and empty"], 22,
                       {"Channel": SHELF, "hatch.close()": CANCEL, "// suspends while the shelf is full": GREY_B,
                        "// the last plate: the loop will end": GREY_B, "// until closed and empty": GREY_B})
        j = code_block(["BlockingQueue<String> hatch = new ArrayBlockingQueue<>(2);",
                        "Thread.ofVirtual().start(() -> {",
                        "    for (String dish : dinner) putQuietly(hatch, dish);   // blocks while full",
                        "    putQuietly(hatch, LAST);                              // the end marker",
                        "});",
                        "for (String dish = hatch.take(); !dish.equals(LAST); dish = hatch.take()) serve(dish);"], 22,
                       {"ArrayBlockingQueue": SHELF, "LAST": CANCEL, "// blocks while full": GREY_B, "// the end marker": GREY_B})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18))
        cols.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.6).move_to([0, 0, 0])
        self.say("code")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.at_text("with Java's", lead=0.3)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.8)
        self.at_text("A queue can't", lead=0.3)
        self.play(Indicate(j[3], color=CANCEL, scale_factor=1.03), Indicate(k[3], color=CANCEL, scale_factor=1.03), run_time=1.0)
        self.hold(after=1.2)
        self.play(FadeOut(cols), run_time=0.6)

        # ================= moral and a check =================
        mq = T("Each plate to exactly one coroutine: a channel, the hatch.", 32).move_to(UP * 2.6)
        m1 = T("The shelf sets the pace. A team of helpers caps the work.", 28, HELPER).move_to(UP * 1.75)
        m2 = T("select takes whichever answer comes first.", 28, BAKERY).move_to(UP * 1.05)
        m3 = T("close is the cook's word that the last plate is through.", 28, CANCEL).move_to(UP * 0.35)
        for m in (mq, m1, m2, m3):
            fit(m, 12.6)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at_text("The shelf sets", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("select takes", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and close", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qq = VGroup(T("Check:", 28, CANCEL), T("no shelf, a fast cook, a helper who needs 100 ms a plate.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("How often does send return?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2).move_to(DOWN * 1.2)
        fit(qq, 12.6)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("about every 100 ms: each send waits for the helper's hands", 30, HELPER).move_to(DOWN * 2.55)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
