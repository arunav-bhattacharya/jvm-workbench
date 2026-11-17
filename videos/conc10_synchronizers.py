from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bCountDownLatch\b", "count down latch"), (r"\bcountDown\b", "count down"),
    (r"\bCyclicBarrier\b", "cyclic barrier"), (r"\bTimeoutException\b", "timeout exception"),
    (r"\bBrokenBarrierException\b", "broken barrier exception"), (r"0\.00", "zero point zero zero"),
]

# every spoken line, in order
N = {
    "open": "Picture a small shop that opens at nine. Before the doors open, its program loads three lists: "
            "the price list, the stock counts and today's offers. Three threads load them side by side. "
            "A thread is one path of work, like one clerk in the back room.",
    "door": "A fourth thread opens the doors, once all three lists are in.",
    "early": "One morning, the doors open early, and the first customer buys a loaf of bread for 0.00. "
             "Great news for the customer. The price list was still loading.",
    "nap": "The fix most of us try first is a nap. In the lesson's demo, the lists take 200, 300 and 400 milliseconds, "
           "and the door thread sleeps for 250. Will all three be in?",
    "nap2": "No. The doors opened at 271 milliseconds, with two lists still loading. "
            "As the clerks taught us in the first lesson, a sleep is a guess with a number on it.",
    "wish": "We don't want to wait for a time. We want to wait for three events.",
    "shy": "Java has four tools for waiting: a latch, a barrier, a semaphore and a phaser. "
           "So here's the question we're shy to ask. Why four? Isn't waiting just waiting?",
    "gate": "The first is a gate with a counter on it. Java calls it a CountDownLatch. "
            "Ours starts at 3, one for each list.",
    "map": "Each loading thread calls countDown when its list is in, and the counter drops by one. "
           "The door thread calls await, and waits at the gate until the counter reads zero.",
    "run": "Price list at 228 milliseconds: two left. Offers at 328: one. Stock counts at 428: zero. "
           "The gate opens, and so do the doors. Not a moment early, and not a moment late.",
    "oneshot": "The counter only goes down. So a latch opens once and stays open, "
               "and a later await walks straight through. There's no reset.",
    "stuck": "But say a loader throws before it counts down. The counter stops at 1, and the door thread waits forever, "
             "with no error and no log line.",
    "habits": "So, two habits. Count down in a finally block, which runs even when loading fails. "
              "And await with a deadline, say two seconds, so a load that hangs gets a clear no.",
    "tills": "Now the evening. The clerks add up the shop's three tills, one thread per till, one day at a time. "
             "Each day's three subtotals make the day's total, and nobody starts the next day before that.",
    "t_latch": "Let's try a latch of 3 again. Day 1 works. On day 2, thread 0 finishes first and calls await. "
               "Does it wait for the others?",
    "t_break": "It doesn't. The latch is still open from yesterday. So thread 0 adds up day 2 with old numbers "
               "for two tills, and runs off into day 3 alone.",
    "bus": "We want a meeting point that closes again by itself, like a tour bus. At every stop, it leaves "
           "only when everyone is back on board, and the guide counts heads first.",
    "bus_map": "That's a CyclicBarrier, built for 3. Each thread calls await when it's back on board, and waits. "
               "The head count is the barrier action: it runs once, on the last thread to arrive, "
               "and adds up the day. Then the door closes for the next stop. That's the cyclic part.",
    "bus_show": "The demo ran three days: 6,000, then 12,000, then 18,000. "
                "Till 2 closed every day, because it was the slowest, and always got back last.",
    "bus_lost": "And a tourist who never comes back? A guide would go and look. A barrier just waits. "
                "On day 4, till 2 never arrives, and the other two wait at most 300 milliseconds. "
                "One gets a TimeoutException, which breaks the barrier, and the other a BrokenBarrierException. "
                "So give await a timeout.",
    "phaser": "For a group that changes size, there's the Phaser. At the yearly stocktake, helper 2 only counts, "
              "then goes home. A barrier of 3 would wait for it forever. A phaser lets a party leave, "
              "like a guide crossing a name off the list: 3 parties, then 2.",
    "bank": "Last, card payments. The bank checks each one over the network, about 120 milliseconds a call, "
            "and it allows five calls at once. On a busy Saturday, twenty customers pay together, "
            "and fifteen are refused.",
    "park": "Think of a car park with five spaces, and a sign that shows how many are free. "
            "A car that comes in takes a space, and one that leaves gives it back. "
            "At zero, the next car waits at the entrance.",
    "park_map": "That's a Semaphore. The spaces are permits, here 5. acquire takes one, or waits. "
                "release gives one back. Each call to the bank is a car.",
    "park_pred": "Twenty calls through five permits, 120 milliseconds each. How many at once, and how long in all?",
    "park_show": "At most five, and 502 milliseconds: four waves of five.",
    "stray_q": "Now a car that was never inside tells the sign it's leaving. What does the sign show?",
    "stray": "Six free spaces, in a car park built for five. Good luck parking in the sixth. "
             "Permits have no owner: release adds one, whoever calls it.",
    "drift": "So a stray release, say from a payment cancelled while it waited, quietly raises the limit. "
             "Five drifts to eight, then twelve. Release only the permits you took.",
    "code": "The latch in code, Java on the left and Kotlin on the right. Count down in finally. "
            "Wait two seconds at most, then open.",
    "moral": "So, why four tools? Because each waits for something different. A latch waits for events, once. "
             "A barrier waits for the whole group, every round, and a phaser lets that group change. "
             "A semaphore waits for a free place. Ask what you're waiting for, and the tool picks itself.",
    "check": "Quick check. Three helpers move stock every day for a week, and nobody starts a new day "
             "until all three finish. Latch or barrier?",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.0):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, -3.2, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def clerk(color, s=1.0):
    """A clerk, as in the first lesson's back room: a round head over a half-disc of shoulders."""
    body = Sector(radius=0.38, angle=PI, start_angle=0).set_fill(color, 1).set_stroke(width=0)
    head = Circle(radius=0.19).set_fill(color, 1).set_stroke(width=0).next_to(body, UP, buff=0.07)
    return VGroup(body, head).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def tag(text):
    """The tool's name, top left, for the whole stretch about it."""
    return M(text, 26, COUNT).move_to([-6.3, 3.2, 0], aligned_edge=LEFT)


# one colour per thing, for the whole video
COLS = [TEAL_M, PURPLE_M, "#F28FB0"]   # the three worker threads: loaders, tills, helpers
DOOR, COUNT, BAD, GOOD, CALL = BLUE_M, GOLD_M, RED_M, GREEN_M, BLUE_M
BREAD = "#C8925A"

# ---- the shop, morning ----
ROWS = [1.75, 0.55, -0.65]            # the three loaders
CX, CARD_X, CARD_W = -5.75, -3.0, 3.5
FLOOR = -1.5
DOOR_C = np.array([5.15, -0.15, 0])   # the shop door
DT_HOME = np.array([0.85, -1.05, 0])  # the door thread
DT_WAIT = np.array([2.0, -1.05, 0])   # waiting at the gate
GX = 2.9                              # the gate


def list_card(name, color):
    r = RoundedRectangle(corner_radius=0.1, width=CARD_W, height=0.82, stroke_color=color, stroke_width=2.5)
    r.set_fill(BLACK, 1)
    t = T(name, 24).move_to(r).align_to(r, LEFT).shift(RIGHT * 0.22 + UP * 0.12)
    a = r.get_left() + RIGHT * 0.22 + DOWN * 0.23
    b = r.get_right() + LEFT * 0.22 + DOWN * 0.23
    track = Line(a, b).set_stroke(GREY_D, 6)
    return VGroup(r, t, track)


def shop_door():
    frame = Rectangle(width=1.5, height=2.7).set_stroke(GREY_A, 4).move_to(DOOR_C)
    panel = Rectangle(width=1.38, height=2.6).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.35), 1).move_to(DOOR_C)
    knob = Dot(radius=0.06, color=GREY_A).move_to(DOOR_C + RIGHT * 0.5 + DOWN * 0.1)
    return frame, VGroup(panel, knob)


def sign(text, color):
    t = T(text, 24, color)
    r = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.5, stroke_color=color, stroke_width=2.5)
    r.set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r)).move_to(DOOR_C + UP * 1.75)


def loaf():
    body = RoundedRectangle(corner_radius=0.2, width=0.95, height=0.45).set_fill(BREAD, 1).set_stroke(width=0)
    cuts = VGroup(*[Line([x - 0.06, -0.12, 0], [x + 0.06, 0.12, 0]).set_stroke("#8A5A2E", 3) for x in (-0.25, 0, 0.25)])
    return VGroup(body, cuts.move_to(body))


def counter_box(n):
    r = RoundedRectangle(corner_radius=0.08, width=0.8, height=0.6, stroke_color=COUNT, stroke_width=3)
    r.set_fill(BLACK, 1).move_to([GX, 0.05, 0])
    return VGroup(r, M(str(n), 32, COUNT).move_to(r))


# ---- the evening: a timeline ----
TROWS = [1.25, 0.45, -0.35]
X0, U = -4.45, 0.0113                # x of 0 ms, units per ms


def tx(ms):
    return X0 + U * ms


def work(t0, t1, row, color):
    return Rectangle(width=U * (t1 - t0) - 0.08, height=0.26).set_stroke(width=0).set_fill(color, 0.95).move_to(
        [(tx(t0) + tx(t1)) / 2, TROWS[row], 0])


def waiting(t0, t1, row):
    return DashedLine([tx(t0) + 0.04, TROWS[row], 0], [tx(t1), TROWS[row], 0], dash_length=0.08).set_stroke(GREY_B, 2.5)


def day_line(ms, color=COUNT):
    return Line([tx(ms), 1.62, 0], [tx(ms), -0.72, 0]).set_stroke(color, 3.5)


def total_chip(text, ms, color=COUNT):
    return chip(text, color, size=22).move_to([tx(ms), -1.22, 0])


def bus():
    body = RoundedRectangle(corner_radius=0.18, width=2.7, height=0.95, stroke_color=GREY_A, stroke_width=3)
    body.set_fill(dim(GREY_B, 0.2), 1)
    wins = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.42, height=0.36, stroke_color=GREY_B, stroke_width=2)
                    .set_fill(BLACK, 1) for _ in range(3)]).arrange(RIGHT, buff=0.18)
    wins.move_to(body).shift(RIGHT * 0.3 + UP * 0.12)
    door = Rectangle(width=0.36, height=0.62).set_stroke(GREY_B, 2).move_to(body.get_left() + RIGHT * 0.38 + DOWN * 0.08)
    wheels = VGroup(*[Circle(radius=0.15).set_stroke(GREY_A, 3).set_fill(BLACK, 1).move_to(body.get_bottom() + RIGHT * x)
                      for x in (-0.8, 0.8)])
    riders = VGroup(*[Dot(radius=0.11, color=c).move_to(w) for c, w in zip(COLS, wins)])
    return VGroup(body, wins, door, wheels, riders)


# ---- the car park ----
BAY_X = [-0.6, 0.55, 1.7, 2.85, 4.0]
BAY_Y = 1.95
ROAD_Y = 0.35
SIGN_C = np.array([-2.75, 1.95, 0])


def bay(x, dashed=False):
    pts = [[x - 0.52, BAY_Y - 0.78, 0], [x - 0.52, BAY_Y + 0.78, 0], [x + 0.52, BAY_Y + 0.78, 0], [x + 0.52, BAY_Y - 0.78, 0]]
    v = VMobject().set_points_as_corners(pts)
    if dashed:
        return DashedVMobject(v, num_dashes=18).set_stroke(GREY_B, 2.5)
    return v.set_stroke(GREY_A, 3)


def car(color=CALL, ghost=False):
    r = RoundedRectangle(corner_radius=0.12, width=0.58, height=0.9)
    if ghost:
        return DashedVMobject(r, num_dashes=20).set_stroke(GREY_A, 2.5)
    r.set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    glass = RoundedRectangle(corner_radius=0.05, width=0.4, height=0.2).set_fill(dim(color, 0.8), 1).set_stroke(width=0)
    return VGroup(r, glass.move_to(r).shift(UP * 0.22))


def park_sign(n, color=COUNT):
    r = RoundedRectangle(corner_radius=0.1, width=1.7, height=1.0, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    t1 = T("free", 22, GREY_B).move_to(r).shift(UP * 0.22)
    t2 = M(str(n), 34, color).move_to(r).shift(DOWN * 0.15)
    return VGroup(r, t1, t2).move_to(SIGN_C)


class Conc10Synchronizers(Narrated):
    """conc-10, section 0: the shop that opens at nine. A nap opens the doors at 271 ms with two lists loading; a
    CountDownLatch is a gate with a counter (228, 328, 428 ms), one-shot, and hangs on a missed countDown. Every evening
    the till threads meet: a latch lets thread 0 run ahead, a CyclicBarrier is a tour bus whose head count is the
    barrier action (6,000, 12,000, 18,000), and a missing till needs a timeout. A Phaser lets a helper leave. A
    Semaphore is a car park with five spaces (peak 5, 502 ms), and a stray release makes six. Code, moral, check."""

    def construct(self):
        self.title_card("Four ways to wait", "a latch, a barrier, a semaphore and a phaser")
        tm = ValueTracker(0)
        durs = [220, 420, 320]

        # ================= the shop at nine =================
        clerks = VGroup(*[clerk(c, 0.75).move_to([CX, y, 0]) for c, y in zip(COLS, ROWS)])
        cards = VGroup(*[list_card(n, c).move_to([CARD_X, y, 0])
                         for n, c, y in zip(["price list", "stock counts", "today's offers"], COLS, ROWS)])

        def mkbar(i):
            a, b = cards[i][2].get_start(), cards[i][2].get_end()
            return always_redraw(lambda: Line(a, a + (b - a) * max(0.004, min(1.0, tm.get_value() / durs[i])))
                                 .set_stroke(COLS[i], 7))

        bars = VGroup(*[mkbar(i) for i in range(3)])
        th_lab = T("threads", 24, GREY_B).move_to([CX, ROWS[0] + 0.75, 0])
        frame, panel = shop_door()
        closed = sign("CLOSED", BAD)
        dthread = clerk(DOOR, 0.75).move_to(DT_HOME)
        dt_lab = T("door thread", 22, DOOR).next_to(dthread, DOWN, buff=0.2)
        dt_lab.add_updater(lambda m: m.next_to(dthread, DOWN, buff=0.2))

        self.say("open")
        self.play(FadeIn(frame), FadeIn(panel), FadeIn(closed), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in cards], lag_ratio=0.3), run_time=1.2)
        self.add(bars)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, scale=0.7) for c in clerks], lag_ratio=0.2), run_time=0.9)
        self.play(tm.animate.set_value(110), run_time=1.6, rate_func=linear)
        self.at(3)
        self.play(FadeIn(th_lab), Indicate(clerks[0], color=COLS[0]), run_time=0.8)
        self.hold()

        self.say("door")
        self.play(FadeIn(dthread, shift=UP * 0.2), FadeIn(dt_lab), run_time=0.7)
        self.hold()

        # the doors open early
        opened = sign("OPEN", GOOD)
        cust = clerk(GREY_B, 0.75).move_to(DOOR_C + DOWN * 0.9)
        bread = loaf().move_to([2.35, 0.55, 0])
        price = chip("0.00", BAD, size=26, mono=True).next_to(bread, RIGHT, buff=0.2)
        self.say("early")
        self.play(panel.animate.stretch(0.08, 0, about_edge=LEFT), Transform(closed, opened), run_time=0.9)
        self.play(FadeIn(cust), run_time=0.3)
        self.play(cust.animate.move_to([3.2, -1.05, 0]), run_time=0.8)
        self.play(FadeIn(bread, shift=DOWN * 0.15), FadeIn(price), run_time=0.6)
        self.at(1)
        self.play(Indicate(price, color=BAD, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(Circumscribe(cards[0], color=BAD, buff=0.08), run_time=1.0)
        self.hold()

        # ================= the nap =================
        nap = chip("sleep(250)", DOOR, size=22, mono=True).next_to(dthread, UP, buff=0.25)
        q = M("?", 34, GREY_B).move_to(DOOR_C + UP * 1.75 + LEFT * 1.25)
        self.say("nap")
        self.play(FadeOut(cust), FadeOut(bread), FadeOut(price), run_time=0.5)
        self.play(panel.animate.stretch(1 / 0.08, 0, about_edge=LEFT), Transform(closed, sign("CLOSED", BAD)),
                  tm.animate.set_value(0), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nap, shift=DOWN * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q), run_time=0.4)
        self.hold(after=0)
        self.predict()

        t220 = M("220 ms", 22, GREY_A).move_to(cards[0][0]).align_to(cards[0][0], RIGHT).shift(LEFT * 0.2 + UP * 0.12)
        t271 = M("271 ms", 24, GOOD).next_to(frame, DOWN, buff=0.2)
        still = VGroup(*[T("still loading", 22, BAD).next_to(cards[i][0], RIGHT, buff=0.2) for i in (1, 2)])
        guess = T("a sleep is a guess with a number on it", 28, GREY_A).move_to([0, -2.75, 0])
        self.say("nap2")
        self.play(FadeOut(q), tm.animate.set_value(220), run_time=1.6, rate_func=linear)
        self.play(FadeIn(t220), tm.animate.set_value(271), run_time=0.4, rate_func=linear)
        self.play(panel.animate.stretch(0.08, 0, about_edge=LEFT), Transform(closed, sign("OPEN", GOOD)), FadeIn(t271),
                  FadeOut(nap), run_time=0.7)
        self.play(FadeIn(still), run_time=0.5)
        self.at(2)
        self.play(FadeIn(guess, shift=UP * 0.1), run_time=0.7)
        self.hold()

        events = VGroup(*[chip(t, YELLOW_M, size=24) for t in ("prices in", "stock in", "offers in")])
        events.arrange(RIGHT, buff=0.4).move_to([0, -2.75, 0])
        self.say("wish")
        self.play(FadeOut(guess), FadeOut(t220), FadeOut(t271), FadeOut(still), tm.animate.set_value(0),
                  panel.animate.stretch(1 / 0.08, 0, about_edge=LEFT), Transform(closed, sign("CLOSED", BAD)), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(e, shift=UP * 0.15) for e in events], lag_ratio=0.3), run_time=1.0)
        self.hold()

        tools = VGroup(*[M(t, 28, COUNT) for t in ("latch", "barrier", "semaphore", "phaser")]).arrange(RIGHT, buff=0.7)
        tools.move_to([0, -2.6, 0])
        why = T("Why four? Isn't waiting just waiting?", 28, YELLOW_M).move_to([0, -3.2, 0])
        self.say("shy")
        self.play(FadeOut(events), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in tools], lag_ratio=0.25), run_time=1.2)
        self.at(2)
        self.play(FadeIn(why), run_time=0.6)
        self.hold()

        # ================= the latch: a gate with a counter =================
        gate = Line([GX, FLOOR, 0], [GX, -0.25, 0]).set_stroke(BAD, 11)
        cnt = counter_box(3)
        latch_lab = M("CountDownLatch", 24, COUNT).next_to(cnt, UP, buff=0.22)
        ttag = tag("CountDownLatch")
        self.say("gate")
        self.play(FadeOut(why), FadeOut(tools[1:]), tools[0].animate.move_to(ttag).scale(26 / 28), run_time=0.7)
        self.remove(tools[0])
        self.add(ttag)
        self.play(Create(gate), run_time=0.6)
        self.at(1)
        self.play(FadeIn(latch_lab), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cnt, scale=0.7), run_time=0.6)
        self.hold()

        leg1 = VGroup(M("countDown()", 24, COUNT), T("the counter drops by one", 24))
        leg2 = VGroup(M("await()", 24, DOOR), T("wait at the gate until it reads 0", 24))
        for row, y in ((leg1, -2.5), (leg2, -3.1)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([-3.6, y, 0], aligned_edge=LEFT)
        self.say("map")
        self.play(FadeIn(leg1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(leg2, shift=UP * 0.1), run_time=0.6)
        self.play(dthread.animate.move_to(DT_WAIT), run_time=0.9)
        self.hold()

        def spark(i):
            d = Dot(radius=0.09, color=COUNT).move_to(cards[i][0].get_right()).set_z_index(8)
            self.add(d)
            self.play(d.animate.move_to(cnt.get_left()), run_time=0.45)
            self.remove(d)

        def recount(n, color=COUNT):
            return Transform(cnt[1], M(str(n), 32, color).move_to(cnt[0]))

        durs[:] = [228, 428, 328]
        tl = [M(f"{ms} ms", 22, GREY_A).move_to(cards[i][0]).align_to(cards[i][0], RIGHT).shift(LEFT * 0.2 + UP * 0.12)
              for i, ms in ((0, 228), (2, 328), (1, 428))]
        self.say("run")
        for k, (i, ms, n) in enumerate(((0, 228, 2), (2, 328, 1), (1, 428, 0))):
            if k:
                self.at(k)
            self.play(tm.animate.set_value(ms), run_time=0.55 if k else 1.0, rate_func=linear)
            self.play(FadeIn(tl[k]), run_time=0.2)
            spark(i)
            self.play(recount(n), run_time=0.3)
        self.at(3)
        self.play(Rotate(gate, -PI / 2, about_point=gate.get_end()), run_time=0.6)
        self.play(gate.animate.set_stroke(GOOD), run_time=0.2)
        t428 = M("428 ms", 24, GOOD).next_to(frame, DOWN, buff=0.2)
        self.play(FadeOut(dt_lab), run_time=0.2)
        self.play(dthread.animate.move_to(DOOR_C + DOWN * 0.9 + LEFT * 0.4), run_time=0.9)
        self.play(panel.animate.stretch(0.08, 0, about_edge=LEFT), Transform(closed, sign("OPEN", GOOD)), FadeIn(t428),
                  run_time=0.6)
        self.hold()

        # one-shot
        late = clerk(DOOR, 0.6).move_to(DT_HOME + LEFT * 0.4)
        late_lab = T("a later await()", 22, DOOR).next_to(late, DOWN, buff=0.18)
        noreset = T("no reset", 24, COUNT).next_to(cnt, LEFT, buff=0.3)
        self.say("oneshot")
        self.play(FadeOut(dthread), run_time=0.4)
        self.play(Indicate(cnt[1], color=COUNT, scale_factor=1.3), run_time=0.7)
        self.at(1)
        self.play(FadeIn(late), FadeIn(late_lab), run_time=0.4)
        self.play(late.animate.move_to(DOOR_C + DOWN * 0.9 + LEFT * 0.4), FadeOut(late_lab), run_time=1.2)
        self.play(FadeOut(late), run_time=0.3)
        self.at(2)
        self.play(FadeIn(noreset), run_time=0.5)
        self.hold()

        # ================= the latch that never opens =================
        durs[:] = [228, 1e9, 328]
        dthread.move_to(DT_WAIT)
        dt_lab.clear_updaters().next_to(dthread, DOWN, buff=0.2)
        throws = VGroup(T("throws", 22, BAD), tick(False, 0.14)).arrange(RIGHT, buff=0.15)
        throws.next_to(cards[1][0], RIGHT, buff=0.2)
        forever = T("waits forever", 22, BAD).next_to(dthread, DOWN, buff=0.2)
        self.say("stuck")
        self.play(FadeOut(VGroup(*tl, t428, noreset)), tm.animate.set_value(0), Transform(cnt[1], M("3", 32, COUNT).move_to(cnt[0])),
                  Rotate(gate, PI / 2, about_point=gate.get_end()),
                  panel.animate.stretch(1 / 0.08, 0, about_edge=LEFT), Transform(closed, sign("CLOSED", BAD)), run_time=0.8)
        self.play(FadeIn(dthread), FadeIn(dt_lab), gate.animate.set_stroke(BAD), run_time=0.4)
        self.play(tm.animate.set_value(200), run_time=0.8, rate_func=linear)
        self.play(cards[1][0].animate.set_stroke(BAD), FadeIn(throws), run_time=0.4)
        self.play(tm.animate.set_value(228), run_time=0.2, rate_func=linear)
        spark(0)
        self.play(recount(2), run_time=0.25)
        self.play(tm.animate.set_value(328), run_time=0.5, rate_func=linear)
        spark(2)
        self.play(recount(1), run_time=0.25)
        self.at(1)
        self.play(Indicate(cnt, color=BAD, scale_factor=1.15), run_time=0.8)
        self.play(FadeOut(dt_lab), FadeIn(forever), run_time=0.5)
        self.hold()

        h1 = VGroup(M("countDown()", 24, COUNT), T("in a finally block: it runs even when loading fails", 24))
        h2 = VGroup(M("await(2, SECONDS)", 24, DOOR), T("a deadline: a hang gets a clear no", 24))
        for row, y in ((h1, -2.5), (h2, -3.1)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].next_to(row[0], RIGHT, buff=0.35)
        self.say("habits")
        self.play(FadeOut(leg1), FadeOut(leg2), run_time=0.4)
        self.at(1)
        self.play(FadeIn(h1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(h2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.remove(bars)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= every evening: the till threads meet =================
        rlabs = VGroup()
        for i, y in enumerate(TROWS):
            rlabs.add(VGroup(clerk(COLS[i], 0.45), T(f"till {i}", 24, COLS[i])).arrange(RIGHT, buff=0.2)
                      .move_to([-6.25, y, 0], aligned_edge=LEFT))
        axis = Line([tx(0), -0.72, 0], [tx(850), -0.72, 0]).set_stroke(GREY_D, 2)
        self.say("tills")
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rlabs], lag_ratio=0.25), FadeIn(axis), run_time=1.2)
        self.at(1)
        d1w = VGroup(*[work(0, 50 * (i + 1), i, COLS[i]) for i in range(3)])
        self.play(*[GrowFromEdge(b, LEFT, run_time=0.5 * (i + 1)) for i, b in enumerate(d1w)])
        self.at(2)
        d1l = day_line(150)
        d1t = total_chip("day 1", 150)
        self.play(Create(d1l), FadeIn(d1t, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # try a latch
        ltag = tag("CountDownLatch (3)")
        d1d = VGroup(waiting(50, 150, 0), waiting(100, 150, 1))
        latch_l = T("latch: open", 22, GOOD).next_to(d1l, UP, buff=0.12)
        self.say("t_latch")
        self.play(FadeIn(ltag), Create(d1d), run_time=0.7)
        self.at(1)
        self.play(d1l.animate.set_color(GOOD), FadeIn(latch_l), run_time=0.6)
        self.at(2)
        d2w0 = work(150, 200, 0, COLS[0])
        self.play(GrowFromEdge(d2w0, LEFT), run_time=0.6)
        self.hold(after=0)
        self.predict()

        d2w12 = VGroup(work(150, 250, 1, COLS[1]), work(150, 300, 2, COLS[2]))
        old = total_chip("old numbers", 200, BAD).shift(DOWN * 0.72)
        d3w0 = work(200, 250, 0, COLS[0]).set_fill(BAD, 0.95)
        alone = T("day 3, alone", 22, BAD).next_to(d3w0, UP, buff=0.12)
        self.say("t_break")
        self.at(1)
        self.play(Indicate(latch_l, color=GOOD), run_time=0.8)
        self.at(2)
        self.play(GrowFromEdge(d2w12[0], LEFT, run_time=0.8), GrowFromEdge(d2w12[1], LEFT, run_time=1.2),
                  FadeIn(old, shift=UP * 0.1, run_time=0.6))
        self.play(GrowFromEdge(d3w0, LEFT), FadeIn(alone), run_time=0.7)
        self.hold()

        # the bus
        bpic = bus().move_to([4.7, 2.6, 0])
        guide = clerk(COUNT, 0.5).move_to([3.0, 2.55, 0])
        g_lab = T("guide", 22, COUNT).next_to(guide, LEFT, buff=0.15)
        self.say("bus")
        self.play(FadeOut(VGroup(d1d, d2w0, d2w12, old, d3w0, alone, latch_l, d1w, d1l, d1t)), FadeOut(ltag), run_time=0.6)
        self.play(FadeIn(bpic, shift=LEFT * 0.3), run_time=0.8)
        self.at(1)
        self.play(Indicate(bpic[4], color=WHITE), run_time=0.8)
        self.at_text("the guide")
        self.play(FadeIn(guide), FadeIn(g_lab), run_time=0.5)
        self.hold()

        btag = tag("CyclicBarrier (3)")
        m1 = VGroup(T("back on board", 24), M("await()", 24, GREY_A))
        m2 = VGroup(T("the head count", 24, COUNT), T("the barrier action: once, on the last to arrive", 24))
        for row, y in ((m1, -2.15), (m2, -2.75)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([-2.9, y, 0], aligned_edge=LEFT)
        self.say("bus_map")
        self.play(FadeIn(btag), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        dw = [VGroup(*[work(150 * d, 150 * d + 50 * (i + 1), i, COLS[i]) for i in range(3)]) for d in range(3)]
        dd = [VGroup(waiting(150 * d + 50, 150 * d + 150, 0), waiting(150 * d + 100, 150 * d + 150, 1)) for d in range(3)]
        self.play(AnimationGroup(*[Succession(GrowFromEdge(dw[0][i], LEFT, run_time=0.45 * (i + 1)),
                                              *([Create(dd[0][i], run_time=0.45 * (2 - i))] if i < 2 else []))
                                   for i in range(3)]))
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        dl = [day_line(150 * (d + 1)) for d in range(3)]
        tot = [total_chip(s, 150 * (d + 1)) for d, s in enumerate(("6,000", "12,000", "18,000"))]
        self.play(Create(dl[0]), Indicate(dw[0][2], color=COUNT), run_time=0.6)
        self.play(Indicate(guide, color=COUNT), FadeIn(tot[0], shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(Flash(dl[0].get_top(), color=COUNT, flash_radius=0.3), run_time=0.6)
        self.hold()

        out = VGroup(*[M(f"day {d + 1} closed by till-2: sales {s}", 22, GREY_A)
                       for d, s in enumerate(("6,000", "12,000", "18,000"))]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        out.move_to([-6.2, -2.55, 0], aligned_edge=LEFT)
        self.say("bus_show")
        self.play(FadeOut(m1), FadeOut(m2), run_time=0.4)
        self.play(FadeIn(out[0]), run_time=0.3)
        for d in (1, 2):
            self.play(AnimationGroup(*[Succession(GrowFromEdge(dw[d][i], LEFT, run_time=0.35 * (i + 1)),
                                                  *([Create(dd[d][i], run_time=0.35 * (2 - i))] if i < 2 else []))
                                       for i in range(3)]))
            self.play(Create(dl[d]), FadeIn(tot[d], shift=UP * 0.1), FadeIn(out[d]), run_time=0.5)
        self.at(1)
        self.play(*[Indicate(dw[d][2], color=WHITE, scale_factor=1.15) for d in range(3)], run_time=0.9)
        self.hold()

        # the tourist who never comes back
        d4 = VGroup(work(450, 500, 0, COLS[0]), work(450, 550, 1, COLS[1]))
        d4d = VGroup(waiting(500, 800, 0), waiting(550, 800, 1))
        never = T("never arrives", 22, GREY_B).move_to([tx(470), TROWS[2], 0], aligned_edge=LEFT)
        seat = M("?", 26, COLS[2]).move_to(bpic[4][2])
        ex0 = M("TimeoutException", 22, BAD).move_to([tx(800), TROWS[0] + 0.36, 0], aligned_edge=RIGHT)
        ex1 = M("BrokenBarrierException", 22, BAD).move_to([tx(800), TROWS[1] + 0.36, 0], aligned_edge=RIGHT)
        x0, x1 = tick(False, 0.12).move_to([tx(800) + 0.2, TROWS[0], 0]), tick(False, 0.12).move_to([tx(800) + 0.2, TROWS[1], 0])
        d4lab = T("day 4", 22, GREY_B).move_to([tx(625), -1.05, 0])
        self.say("bus_lost")
        self.play(bpic[4][2].animate.set_opacity(0), FadeIn(seat), run_time=0.5)
        self.at(3)
        self.play(FadeIn(d4lab), GrowFromEdge(d4[0], LEFT, run_time=0.4), GrowFromEdge(d4[1], LEFT, run_time=0.8),
                  FadeIn(never, run_time=0.6))
        self.at_text("wait at most", lead=0.4)
        self.play(Create(d4d[0]), Create(d4d[1]), run_time=1.6)
        self.at(4)
        self.play(FadeIn(ex0), Create(x0), run_time=0.5)
        self.at_text("and the other", lead=0.2)
        self.play(FadeIn(ex1), Create(x1), run_time=0.5)
        self.at(5)
        self.play(Circumscribe(VGroup(d4d, x0, x1), color=COUNT, buff=0.1), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the phaser =================
        ptag = tag("Phaser")
        PY = [1.0, 0.0, -1.0]
        helpers = VGroup()
        for i, y in enumerate(PY):
            helpers.add(VGroup(clerk(COLS[i], 0.55), T(f"helper {i}", 24, COLS[i])).arrange(RIGHT, buff=0.2)
                        .move_to([-6.2, y, 0], aligned_edge=LEFT))
        PX = [-1.6, 1.5, 4.6]
        phases = VGroup(*[chip(n, GREY_B, size=26) .move_to([x, 2.1, 0]) for n, x in zip(("count", "check", "report"), PX)])
        dots = [VGroup(*[Dot(radius=0.14, color=COLS[i]).move_to([x, PY[i], 0]) for i in range(3)]) for x in PX]
        parties = [M(f"{n} parties", 24, COUNT).move_to([x, -1.9, 0]) for n, x in zip((3, 2, 2), PX)]
        strike = Line(helpers[2].get_left() + LEFT * 0.05, helpers[2].get_right() + RIGHT * 0.05).set_stroke(BAD, 4)
        home = T("goes home", 22, BAD).next_to(helpers[2], DOWN, buff=0.15)
        wait3 = T("a barrier of 3 waits here forever", 22, BAD).move_to([PX[1], -2.6, 0])
        self.say("phaser")
        self.play(FadeIn(ptag), FadeIn(helpers), FadeIn(phases), run_time=0.8)
        self.play(FadeIn(dots[0]), FadeIn(parties[0]), run_time=0.6)
        self.at(1)
        self.play(Indicate(helpers[2], color=COLS[2]), run_time=0.7)
        self.play(Create(strike), FadeIn(home), run_time=0.5)
        self.at(2)
        ghost = DashedVMobject(Circle(radius=0.14), num_dashes=10).set_stroke(COLS[2], 2).move_to([PX[1], PY[2], 0])
        self.play(FadeIn(dots[1][:2]), FadeIn(ghost), FadeIn(wait3), run_time=0.6)
        self.at(3)
        self.play(FadeOut(ghost), FadeOut(wait3), FadeIn(parties[1]), run_time=0.6)
        self.play(FadeIn(dots[2][:2]), FadeIn(parties[2]), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the semaphore: a car park =================
        bankb = VGroup(RoundedRectangle(corner_radius=0.12, width=2.2, height=1.5, stroke_color=GREY_A, stroke_width=3)
                       .set_fill(dim(GREY_B, 0.15), 1), T("bank", 28)).move_to([4.6, 0.3, 0])
        bankb[1].shift(UP * 0.32)
        bank_n = T("5 calls at once", 22, GREY_B).next_to(bankb, DOWN, buff=0.2)
        calls = VGroup(*[Dot(radius=0.12, color=CALL) for _ in range(20)]).arrange_in_grid(4, 5, buff=0.35).move_to([-3.6, 0.3, 0])
        ms120 = T("120 ms a call", 22, GREY_B).next_to(bankb, UP, buff=0.2)
        self.say("bank")
        self.play(FadeIn(bankb), run_time=0.6)
        self.at_text("about 120", lead=0.4)
        self.play(FadeIn(ms120), run_time=0.4)
        self.at_text("and it allows", lead=0.3)
        self.play(FadeIn(bank_n), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, scale=0.5) for c in calls], lag_ratio=0.04), run_time=0.9)
        ins = [bankb.get_center() + DOWN * 0.3 + RIGHT * (0.36 * (k - 2)) for k in range(5)]
        self.play(*[calls[k].animate.move_to(ins[k]) for k in range(5)],
                  *[calls[k].animate.shift(RIGHT * 2.4) for k in range(5, 20)], run_time=0.8)
        refused = T("15 refused", 26, BAD).move_to([-1.2, -1.6, 0])
        self.play(*[calls[k].animate.set_color(BAD) for k in range(5, 20)], FadeIn(refused), run_time=0.5)
        self.hold()

        stag = tag("Semaphore (5)")
        bays = VGroup(*[bay(x) for x in BAY_X])
        road = DashedLine([-6.3, ROAD_Y - 0.62, 0], [5.9, ROAD_Y - 0.62, 0], dash_length=0.2).set_stroke(GREY_D, 2)
        ps = [park_sign(5)]
        cars = [car() for _ in range(6)]
        QX = [-5.5, -4.8, -4.1, -3.4, -2.7, -2.0]
        for c, x in zip(cars, QX[::-1]):
            c.move_to([x, ROAD_Y - 0.15, 0])

        def set_sign(n, color=COUNT):
            new = park_sign(n, color)
            old = ps[0]
            ps[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("park")
        self.play(FadeOut(VGroup(bankb, bank_n, calls, refused, ms120)), run_time=0.5)
        self.play(Create(bays), FadeIn(road), FadeIn(ps[0]), FadeIn(stag), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in cars], lag_ratio=0.1), run_time=0.7)
        self.at(1)
        for k in range(5):
            self.play(cars[k].animate.move_to([BAY_X[k], BAY_Y, 0]), *set_sign(4 - k), run_time=0.45)
        self.at(2)
        wl = T("waits", 22, GREY_B).next_to(cars[5], DOWN, buff=0.15)
        self.play(cars[5].animate.move_to([-1.45, ROAD_Y - 0.15, 0]), run_time=0.5)
        wl.next_to(cars[5], DOWN, buff=0.15)
        self.play(FadeIn(wl), run_time=0.3)
        self.play(cars[2].animate.move_to([BAY_X[2], ROAD_Y - 0.15, 0]), run_time=0.5)
        self.play(cars[2].animate.move_to([6.0, ROAD_Y - 0.15, 0]).set_opacity(0), *set_sign(1), run_time=0.6)
        self.play(FadeOut(wl), cars[5].animate.move_to([BAY_X[2], BAY_Y, 0]), *set_sign(0), run_time=0.6)
        self.hold()

        p1 = VGroup(T("a space", 24), T("a permit", 24, COUNT))
        p2 = VGroup(M("acquire()", 24, COUNT), T("take one, or wait for one", 24))
        p3 = VGroup(M("release()", 24, COUNT), T("give one back", 24))
        p4 = VGroup(T("a car", 24), T("a call to the bank", 24, CALL))
        for row, y in ((p1, -1.15), (p2, -1.7), (p3, -2.25), (p4, -2.8)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([-3.7, y, 0], aligned_edge=LEFT)
        self.say("park_map")
        self.at(1)
        self.play(FadeIn(p1, shift=UP * 0.1), Indicate(bays, color=COUNT), run_time=0.8)
        self.at(2)
        self.play(FadeIn(p2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(p3, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(p4, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # twenty calls, five permits: four waves
        WX0, WU = -4.4, 8.6 / 502
        lanes_y = [-0.95 - 0.36 * k for k in range(5)]
        wl_lab = T("5 permits", 22, GREY_B).move_to([-5.6, (lanes_y[0] + lanes_y[-1]) / 2, 0])
        lanes = VGroup(*[Line([WX0, y, 0], [WX0 + 8.6, y, 0]).set_stroke(GREY_D, 1.5) for y in lanes_y])
        waves = [VGroup(*[Rectangle(width=WU * 120 - 0.05, height=0.24).set_stroke(width=0).set_fill(CALL, 0.9)
                          .move_to([WX0 + WU * (2 + 125 * w + 60), y, 0]) for y in lanes_y]) for w in range(4)]
        wq = M("?", 30, GREY_B).move_to([5.3, lanes_y[2], 0])
        self.say("park_pred")
        self.play(FadeOut(VGroup(p1, p2, p3, p4)), run_time=0.4)
        self.play(FadeIn(wl_lab), Create(lanes), run_time=0.8)
        self.at(1)
        self.play(FadeIn(wq), run_time=0.3)
        self.hold(after=0)
        self.predict()

        peak = M("peak 5", 26, COUNT).move_to([5.45, lanes_y[1], 0])
        took = M("502 ms", 26, GOOD).move_to([5.45, lanes_y[3], 0])
        self.say("park_show")
        self.play(FadeOut(wq), LaggedStart(*[FadeIn(w) for w in waves], lag_ratio=0.6), run_time=2.0)
        self.play(FadeIn(peak), FadeIn(took), run_time=0.5)
        self.hold()

        # the car that was never inside
        ghostc = car(ghost=True).move_to([5.25, ROAD_Y - 0.15, 0])
        gl = T("never inside", 22, GREY_B).next_to(ghostc, DOWN, buff=0.15)
        rel = M("release()", 22, COUNT).next_to(ghostc, UP, buff=0.18)
        self.say("stray_q")
        self.play(FadeOut(VGroup(wl_lab, lanes, *waves, peak, took)), run_time=0.4)
        parked = [cars[k] for k in (0, 1, 3, 4)] + [cars[5]]
        self.play(*[c.animate.move_to([6.0, ROAD_Y - 0.15, 0]).set_opacity(0) for c in parked], *set_sign(5), run_time=0.9)
        self.play(FadeIn(ghostc), FadeIn(gl), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rel, shift=UP * 0.1), run_time=0.4)
        self.hold(after=0)
        self.predict()

        bay6 = bay(5.15, dashed=True)
        nobody = T("?", 30, GREY_B).move_to([5.15, BAY_Y, 0])
        self.say("stray")
        d = Dot(radius=0.09, color=COUNT).move_to(rel.get_center()).set_z_index(8)
        self.add(d)
        self.play(d.animate.move_to(SIGN_C), run_time=0.7)
        self.remove(d)
        self.play(*set_sign(6, BAD), run_time=0.4)
        self.play(Create(bay6), FadeIn(nobody), run_time=0.7)
        self.at(2)
        own = T("permits have no owner", 26, COUNT).move_to([0.5, -1.4, 0])
        self.play(FadeIn(own, shift=UP * 0.1), run_time=0.6)
        self.hold()

        drift = VGroup(M("5", 30, COUNT), M("8", 30, BAD), M("12", 30, BAD)).arrange(RIGHT, buff=1.0).move_to([0.5, -2.2, 0])
        arrs = VGroup(*[Arrow(drift[k].get_right(), drift[k + 1].get_left(), buff=0.15, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.25) for k in range(2)])
        rule = T("Release only the permits you took.", 30).move_to([0.5, -3.0, 0])
        self.say("drift")
        self.at(1)
        self.play(FadeIn(drift[0]), run_time=0.3)
        self.play(GrowArrow(arrs[0]), FadeIn(drift[1]), *set_sign(8, BAD), run_time=0.5)
        self.play(GrowArrow(arrs[1]), FadeIn(drift[2]), *set_sign(12, BAD), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"countDown": COUNT, "await": DOOR, "finally": COUNT}
        jsrc = ["var loaded = new CountDownLatch(3);", "", "// each loading thread:", "try { load(list); }",
                "finally { loaded.countDown(); }", "", "// the door thread:", "if (!loaded.await(2, SECONDS))",
                "    throw new IllegalStateException();", "openDoors();"]
        ksrc = ["val loaded = CountDownLatch(3)", "", "// each loading thread:", "try { load(list) }",
                "finally { loaded.countDown() }", "", "// the door thread:", "if (!loaded.await(2, SECONDS))",
                "    throw IllegalStateException()", "openDoors()"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        for c in (jc[2], jc[6], kc[2], kc[6]):
            c.set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.2)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=COUNT, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[7:9], kc[7:9]), color=DOOR, scale_factor=1.04), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Why four? Each one waits for something different.", 32, YELLOW_M).move_to(UP * 2.8)
        rows = [("CountDownLatch", "events, once", "countDown() in finally, a deadline"),
                ("CyclicBarrier", "the whole group, every round", "await with a timeout"),
                ("Phaser", "a group that changes size", "parties join and leave"),
                ("Semaphore", "a free place", "release only what you took")]
        table = VGroup()
        for k, (a, b, c) in enumerate(rows):
            y = 1.6 - 0.75 * k
            table.add(VGroup(M(a, 24, COUNT).move_to([-6.3, y, 0], aligned_edge=LEFT),
                             T(b, 24).move_to([-3.45, y, 0], aligned_edge=LEFT),
                             T(c, 22, GREY_B).move_to([0.75, y, 0], aligned_edge=LEFT)))
        fit(table, 12.6)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("three helpers move stock every day for a week, and nobody starts", 28),
                    T("a new day until all three finish. Latch or barrier?", 28)).arrange(DOWN, buff=0.18).move_to(DOWN * 2.35)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(table[0], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(table[1], shift=UP * 0.1), run_time=0.5)
        self.at_text("and a phaser", lead=0.2)
        self.play(FadeIn(table[2], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(table[3], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
