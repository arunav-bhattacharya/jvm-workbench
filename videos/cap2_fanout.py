from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bwithTimeoutOrNull\b", "with timeout or null"), (r"\bawaitAll\b", "await all"), (r"\bcoroutineScope\b", "coroutine scope"),
    (r"\basync\b", "a-sink"), (r"\bMono\.zip\b", "Mono dot zip"), (r"\b12\.45\b", "twelve forty-five"),
    (r"\b12\.43\b", "twelve forty-three"), (r"\b12\.41\b", "twelve forty-one"),
]

# every spoken line, in order
N = {
    "open": "Remember the home cook from the coroutines track? When she needed tomatoes, she texted three shops at once, "
            "and waited only as long as the slowest reply.",
    "open2": "Now she works the post office counter. A customer asks what it costs to send a parcel to Lisbon. She "
             "texts three couriers, Northline, Eastgate and Fjord, and passes on the cheapest reply.",
    "times": "Say Northline needs 120 milliseconds to answer, Eastgate 300, and Fjord 200.",
    "pain": "The first version anyone writes asks one courier, waits for the answer, then asks the next. Northline, "
            "120. Then Eastgate, 300 more. Then Fjord, 200 more.",
    "pain2": "620 milliseconds for three numbers, and most of that time the cook is just staring at her phone. "
             "Meanwhile the customer is staring at the cook.",
    "wish": "What we'd like is obvious. Send all three texts, then read the replies.",
    "coro": "The tool is the coroutine: a piece of work that can pause without holding its thread, like a dish the "
            "cook leaves to simmer while she starts the next one.",
    "map": "Let's map the texting. Sending a text is async. It starts a coroutine for one courier and hands back a "
           "ticket at once, called a Deferred. Reading the replies is awaitAll. It waits until every ticket has its "
           "answer.",
    "predict": "So all three texts go out together. How long until she has all three prices?",
    "show": "Northline replies at 120. Fjord at 200. Eastgate at 300. She has everything at 300 milliseconds. The "
            "slowest decides, not the sum.",
    "show2": "The lesson's demo prints exactly that on a fake clock: 620 milliseconds one after another, 300 all at "
             "once, and the same three prices.",
    "code": "In Kotlin, that's one line inside coroutineScope: text all three, then read the replies. coroutineScope "
            "is the parent that waits for every call it started, so none of them can outlive the function. The Java "
            "twin uses Reactor. Mono.zip asks all three at once and waits for a value from each.",
    "deadline": "That was a good day. But a customer standing at a counter won't wait two seconds for a price. So the "
                "cook sets a kitchen timer: 250 milliseconds. That's the deadline, the moment by which the request "
                "must answer, whatever the couriers are doing.",
    "shyq": "And here's the question people are shy to ask, because it sounds too simple. Where does the timer go? "
            "One timer around the whole job? Or one timer for each text?",
    "one_timer": "Let's try the obvious one first. One timer around everything. At 250 milliseconds it rings. "
                 "Eastgate is still typing. So the timer cancels the whole job.",
    "one_timer2": "And the whole job includes the replies that already came in. Northline answered at 120, Fjord at "
                  "200, and both get thrown away. The customer gets nothing.",
    "joke": "Well. That's two good prices in the bin, because a third shop types slowly. So the point is: the timer "
            "should cancel only the one who is late.",
    "per_call": "Now one timer per text. At 250, Eastgate's timer rings, and only Eastgate's call is cancelled. Its "
                "answer becomes null, which means no answer. Northline and Fjord still count.",
    "per_call2": "The demo shows it: 250 milliseconds, Northline 12.45, null, Fjord 12.43. The customer gets Fjord's "
                 "12.43, on time. Eastgate's 12.41 would have been cheaper, but a price that misses the deadline is "
                 "no price at all.",
    "why": "And because all three texts start together, a timer per text is also a timer for the whole request. "
           "Nobody waits past 250.",
    "name": "The Kotlin word for a timer per call is withTimeoutOrNull. It's a cancel with a timer. At the deadline, "
            "it cancels the late call and gives back null instead. Java's Reactor does the same with a timeout that "
            "turns into an empty answer.",
    "breaks": "Here the kitchen picture bends a little. A shop that gets a never-mind text stops typing at once. A "
              "cancelled coroutine stops only at its next pause, its next suspension point. A courier call stuck in "
              "a blocking wait keeps going until that wait ends.",
    "guard": "Let's test the rule at its edge. Make the timer 100 milliseconds. Nobody is that fast. What does the "
             "customer get?",
    "guard_a": "At 100 milliseconds, three nulls. That's not a bug in the timer. It's a real day: nobody answered in "
               "time. Later in the lesson, the service serves the last good price, marked stale, so the customer "
               "still gets something honest.",
    "loop": "And a bad day has one more surprise. A courier doesn't just run late, it fails with an error. Inside "
            "coroutineScope, one failure cancels the other two. That's the next section's fix.",
    "moral": "So, where does the timer go? On each call, not around the job. Text everyone at once, let the slowest "
             "decide, and let a late courier drop out alone, without taking the good answers with it.",
    "check": "Quick check. One timer around the whole job, and this time all three couriers answer before it rings. "
             "Does the one-timer version lose anything?",
    "check_a": "No. Nothing was late, so nothing was cancelled. One timer only throws answers away when someone is "
               "late, and that's the day you needed it.",
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

    def clear(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, the same in all three Part 2 capstone videos
NL, EG, FJ = BLUE_M, GOLD_M, TEAL_M          # Northline, Eastgate, Fjord
CLERK, TICKET, BAD, OK = PURPLE_M, YELLOW_M, RED_M, GREEN_M
CUST = GREY_A


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def phone(s=1.0, color=GREY_A):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(BLUE_M, 0.5), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def parcel(s=1.0):
    b = Square(0.5).set_stroke(GOLD_E, 3).set_fill(dim(GOLD_E, 0.4), 1)
    st = VGroup(Line(b.get_top(), b.get_bottom()), Line(b.get_left(), b.get_right())).set_stroke(GOLD_E, 2)
    return VGroup(b, st).scale(s)


def depot(name, color, s=1.0):
    body = Rectangle(width=1.5, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.14), 1)
    roof = Polygon([-0.85, 0, 0], [0.85, 0, 0], [0, 0.36, 0]).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    roof.next_to(body, UP, buff=0)
    door = Rectangle(width=0.5, height=0.4).set_stroke(color, 2).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.2)
    lab = T(name, 24, color).next_to(body, DOWN, buff=0.12)
    return VGroup(body, roof, door, lab).scale(s)


def letter(color=GREY_A, s=1.0):
    r = Rectangle(width=0.36, height=0.24).set_stroke(color, 2).set_fill(BLACK, 1)
    v = VMobject().set_points_as_corners([r.get_corner(UL), r.get_bottom() + UP * 0.08, r.get_corner(UR)]).set_stroke(color, 2)
    return VGroup(r, v).scale(s)


def mailbox(s=1.0):
    return Square(0.5).set_stroke(GREY_B, 2).set_fill("#101010", 1).scale(s)


def stub(n=None, color=TICKET, size=24):
    """A coat-check stub; with no number it is a plain ticket."""
    t = M(str(n), size, color) if n is not None else None
    r = RoundedRectangle(corner_radius=0.06, width=max(0.55, t.width + 0.3) if t else 0.55, height=0.48).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.18), 1)
    holes = VGroup(Dot(radius=0.04, color=BLACK).move_to(r.get_left() + RIGHT * 0.02),
                   Dot(radius=0.04, color=BLACK).move_to(r.get_right() + LEFT * 0.02))
    if t is None:
        return VGroup(r, Line(LEFT * 0.12, RIGHT * 0.12, stroke_width=2, color=color).move_to(r), holes)
    return VGroup(r, t.move_to(r), holes)


def chip_m(text, color, size=24):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.07, width=t.width + 0.34, height=max(0.52, t.height + 0.26)).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines



def shop(name, color, s=1.0):
    body = Rectangle(width=1.3, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.14), 1)
    awn = Polygon([-0.78, 0, 0], [0.78, 0, 0], [0.62, 0.3, 0], [-0.62, 0.3, 0]).set_stroke(color, 2.5)
    awn.set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0)
    door = Rectangle(width=0.3, height=0.42).set_stroke(color, 2).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.21)
    lab = T(name, 22, color).next_to(body, DOWN, buff=0.15)
    return VGroup(body, awn, door, lab).scale(s)


def timer_icon(color=TICKET, s=1.0):
    face = Circle(radius=0.3).set_stroke(color, 3).set_fill(dim(color, 0.2), 1)
    knob = Rectangle(width=0.14, height=0.1).set_stroke(color, 2).set_fill(color, 1).next_to(face, UP, buff=0.0)
    hand = Line(ORIGIN, UP * 0.2, stroke_width=3, color=color)
    return VGroup(face, knob, hand).scale(s)


# the timeline of one request: x(ms)
X0, PX = -3.6, 0.0118
LANES = {"northline": 1.35, "eastgate": 0.65, "fjord": -0.05}
CC = {"northline": NL, "eastgate": EG, "fjord": FJ}
MSV = {"northline": 120, "eastgate": 300, "fjord": 200}
PRICE = {"northline": "12.45", "eastgate": "12.41", "fjord": "12.43"}


def tx(ms):
    return X0 + ms * PX


def axis(y, ticks, end):
    ln = Arrow([tx(0) - 0.1, y, 0], [tx(end), y, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.02)
    tk = VGroup(*[VGroup(Line([tx(m), y - 0.07, 0], [tx(m), y + 0.07, 0], stroke_width=2, color=GREY_B),
                         T(f"{m}", 20, GREY_B).move_to([tx(m), y - 0.3, 0])) for m in ticks])
    ms = T("ms", 20, GREY_B).next_to(ln, RIGHT, buff=0.1)
    return VGroup(ln, tk, ms)


def lbar(name, ms0, ms1, h=0.42, op=0.45, color=None):
    color = color or CC[name]
    r = Rectangle(width=max(0.03, (ms1 - ms0) * PX), height=h).set_stroke(color, 2).set_fill(dim(color, op), 1)
    return r.move_to([(tx(ms0) + tx(ms1)) / 2, LANES[name], 0])


def lane_label(name):
    return T(name.capitalize(), 26, CC[name]).move_to([tx(0) - 0.3, LANES[name], 0], aligned_edge=RIGHT)


def price_chip(name, text=None, color=None):
    return chip_m(text or PRICE[name], color or CC[name], 22)


class Cap2Fanout(Narrated):
    """cap2-02, section 0: three couriers, one kitchen timer. Callback to co-02's cook texting three shops; the
    couriers at 120, 300 and 200 ms; one after another (620 ms) with the pain; async and awaitAll mapped to texts and
    tickets; predict; all at once (300 ms) with the demo line; the code in Kotlin and Java; the deadline; the shy
    question (where does the timer go?); one timer around the job breaks (two good prices in the bin); one timer per
    call keeps Northline and Fjord (demo line, Eastgate's cheaper 12.41 missed); withTimeoutOrNull named, Kotlin and
    Java; where the picture bends; the 100 ms edge (three nulls, then the stale price); the open loop (a courier
    that fails); moral; check."""

    def construct(self):
        self.title_card("Three couriers, one kitchen timer", "ask everyone at once, and let a late one drop out alone")

        # ================= hook: the cook texts three shops =================
        cook = person(CLERK, 1.4).move_to([-4.6, 0.2, 0])
        ph = phone(1.0, CLERK).next_to(cook, RIGHT, buff=0.15)
        shops = VGroup(shop("greengrocer", GREEN_M), shop("market", GOLD_M), shop("farm stand", TEAL_M)).arrange(DOWN, buff=0.35)
        shops.move_to([3.6, 0.2, 0])
        tom = T("the coroutines track: tomatoes", 24, GREY_B).move_to([-4.0, 2.9, 0])
        texts = VGroup(*[DashedLine(ph.get_right() + RIGHT * 0.1, sh[0].get_left() + LEFT * 0.15, dash_length=0.1)
                         .set_stroke(GREY_B, 2) for sh in shops])
        self.say("open")
        self.play(FadeIn(cook), FadeIn(ph), FadeIn(tom), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(sh, shift=LEFT * 0.2) for sh in shops], lag_ratio=0.25), run_time=1.0)
        self.at_text("she texted", lead=0.3)
        self.play(LaggedStart(*[Create(t) for t in texts], lag_ratio=0.15), run_time=0.8)
        self.hold()

        deps = VGroup(depot("Northline", NL), depot("Eastgate", EG), depot("Fjord", FJ)).arrange(DOWN, buff=0.35)
        deps.move_to(shops)
        counter = Rectangle(width=2.2, height=0.4).set_stroke(GREY_B, 2.5).set_fill("#151515", 1).next_to(cook, DOWN, buff=0.05)
        cust = person(CUST, 1.2).move_to([-6.1, 0.0, 0])
        ask = T("Lisbon: how much?", 24, CUST).move_to([-5.0, 2.0, 0])
        texts2 = VGroup(*[DashedLine(ph.get_right() + RIGHT * 0.1, d[0].get_left() + LEFT * 0.15, dash_length=0.1)
                          .set_stroke(d[0].get_stroke_color(), 2) for d in deps])
        self.say("open2")
        self.play(FadeOut(tom), FadeOut(texts), FadeIn(counter), run_time=0.5)
        self.at_text("A customer", lead=0.3)
        self.play(FadeIn(cust, shift=RIGHT * 0.2), FadeIn(ask), run_time=0.6)
        self.at_text("She texts", lead=0.3)
        self.play(*[ReplacementTransform(a, b) for a, b in zip(shops, deps)], run_time=1.0)
        self.play(LaggedStart(*[Create(t) for t in texts2], lag_ratio=0.15), run_time=0.7)
        self.hold()
        tms = VGroup(*[T(f"{MSV[n]} ms", 26, CC[n]).next_to(d, RIGHT, buff=0.3) for n, d in zip(LANES, deps)])
        self.say("times")
        self.play(LaggedStart(*[FadeIn(t, shift=LEFT * 0.1) for t in tms], lag_ratio=0.5), run_time=1.6)
        self.hold()
        self.clear()

        # ================= pain: one after another =================
        ax = axis(-0.95, [0, 100, 200, 300, 400, 500, 600, 700], 760)
        labs = VGroup(*[lane_label(n) for n in LANES])
        seq = {"northline": lbar("northline", 0, 120), "eastgate": lbar("eastgate", 120, 420), "fjord": lbar("fjord", 420, 620)}
        title = T("one after another", 30, GREY_A).move_to([0, 2.8, 0])
        self.say("pain")
        self.play(FadeIn(ax), FadeIn(labs), FadeIn(title), run_time=0.7)
        self.at_text("Northline, 120", lead=0.3)
        self.play(GrowFromEdge(seq["northline"], LEFT), run_time=0.7)
        self.at_text("Then Eastgate", lead=0.3)
        self.play(GrowFromEdge(seq["eastgate"], LEFT), run_time=1.0)
        self.at_text("Then Fjord", lead=0.3)
        self.play(GrowFromEdge(seq["fjord"], LEFT), run_time=0.8)
        self.hold()
        m620 = DashedLine([tx(620), 1.75, 0], [tx(620), -0.85, 0], dash_length=0.08).set_stroke(BAD, 2.5)
        m620_t = T("620 ms", 26, BAD).next_to(m620, UP, buff=0.08)
        stare = VGroup(person(CLERK, 0.9), phone(0.6, CLERK)).arrange(RIGHT, buff=0.08)
        stare_c = person(CUST, 0.9)
        st_g = VGroup(stare_c, stare).arrange(RIGHT, buff=0.5).move_to([-3.5, -2.45, 0])
        st_l = T("staring at the phone; staring at the cook", 24, GREY_B).next_to(st_g, RIGHT, buff=0.4)
        self.say("pain2")
        self.play(Create(m620), FadeIn(m620_t), run_time=0.6)
        self.at_text("most of that", lead=0.3)
        self.play(FadeIn(stare), run_time=0.5)
        self.at_text("Meanwhile", lead=0.3)
        self.play(FadeIn(stare_c), FadeIn(st_l), run_time=0.5)
        self.hold()
        wish = T("wish: send all three texts, then read the replies", 28, TICKET).move_to([0, -3.15, 0])
        self.say("wish")
        self.play(FadeOut(VGroup(st_g, st_l)), FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(*seq.values(), m620, m620_t, wish, title)), run_time=0.6)

        # ================= the coroutine, and the map =================
        pot_c = VGroup(Circle(radius=0.35).set_stroke(CLERK, 3).set_fill(dim(CLERK, 0.3), 1))
        steam = VGroup(*[ArcBetweenPoints([x, 0.45, 0], [x + 0.08, 0.8, 0], angle=0.6).set_stroke(GREY_B, 2) for x in (-0.15, 0.0, 0.15)])
        simmer = VGroup(pot_c, steam).move_to([-4.6, 2.6, 0])
        coro_l = T("a coroutine: work that can pause without holding its thread", 26).next_to(simmer, RIGHT, buff=0.4)
        fit(coro_l, 9.5)
        self.say("coro")
        self.play(FadeIn(simmer), FadeIn(coro_l), run_time=0.8)
        self.hold()

        rows = VGroup(
            VGroup(T("send a text", 26, CLERK), T("=", 26), M("async", 26, CLERK), T(": starts it, hands back a ticket,", 26),
                   M("Deferred", 26, TICKET)),
            VGroup(T("read the replies", 26, CLERK), T("=", 26), M("awaitAll()", 26, CLERK), T(": waits for every ticket", 26)))
        for r in rows:
            r.arrange(RIGHT, buff=0.18)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -2.6, 0])
        fit(rows, 12.4)
        self.say("map")
        self.play(FadeOut(VGroup(simmer, coro_l)), run_time=0.4)
        self.at_text("Sending a text", lead=0.3)
        self.play(FadeIn(rows[0][:3]), run_time=0.6)
        self.at_text("It starts", lead=0.3)
        self.play(FadeIn(rows[0][3:]), run_time=0.6)
        self.at_text("Reading", lead=0.3)
        self.play(FadeIn(rows[1]), run_time=0.6)
        self.hold()

        title = T("all at once", 30, GREY_A).move_to([0, 2.8, 0])
        tix = VGroup(*[stub(None, TICKET).scale(0.6).move_to([tx(0) + 0.0, LANES[n], 0]) for n in LANES])
        self.say("predict")
        self.play(FadeIn(title), LaggedStart(*[FadeIn(t, scale=0.6) for t in tix], lag_ratio=0.2), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        tog = {n: lbar(n, 0, MSV[n]) for n in LANES}
        chips = {n: price_chip(n).next_to(tog[n], RIGHT, buff=0.15) for n in LANES}
        self.say("show")
        self.play(FadeOut(tix), run_time=0.3)
        tracker = ValueTracker(0)

        def grower(n):
            def upd(m):
                ms = min(MSV[n], tracker.get_value())
                m.become(lbar(n, 0, max(ms, 1)))
            return upd

        live = {n: lbar(n, 0, 1).add_updater(grower(n)) for n in LANES}
        self.add(*live.values())
        for n, key in (("northline", "Northline replies"), ("fjord", "Fjord at"), ("eastgate", "Eastgate at")):
            self.at_text(key, lead=0.1)
            self.play(tracker.animate.set_value(MSV[n]), run_time=0.7, rate_func=linear)
            self.play(FadeIn(chips[n], shift=LEFT * 0.1), run_time=0.3)
        for m in live.values():
            m.clear_updaters()
        m300 = DashedLine([tx(300), 1.75, 0], [tx(300), -0.85, 0], dash_length=0.08).set_stroke(OK, 2.5)
        m300_t = T("300 ms: the slowest decides", 26, OK).next_to(m300, UP, buff=0.08)
        self.at_text("She has", lead=0.3)
        self.play(Create(m300), FadeIn(m300_t), run_time=0.6)
        self.hold()

        out = VGroup(M("one after another:     620 ms  [northline 12.45, eastgate 12.41, fjord 12.43]", 22),
                     M("async, all at once:    300 ms  [northline 12.45, eastgate 12.41, fjord 12.43]", 22, OK))
        out.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        out_t = T("FanOutDemo, on a fake clock:", 22, GREY_B)
        out_g = VGroup(out_t, out).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -2.6, 0])
        fit(out_g, 12.6)
        self.say("show2")
        self.play(FadeOut(rows), run_time=0.4)
        self.play(FadeIn(out_g, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the code =================
        kt = T("Kotlin", 24, GREY_B)
        kc = code_block(["suspend fun allPrices(d: String): List<Quote> = coroutineScope {",
                         "    providers.map { p -> async { p.quote(d) } }.awaitAll()   // text, then read",
                         "}"], 22, hl={"coroutineScope": CLERK, "async": CLERK, "awaitAll()": CLERK})
        jt = T("Java, with Reactor", 24, GREY_B)
        jc = code_block(["Mono<List<Quote>> allPrices(String d) {",
                         "    return Mono.zip(northline.quote(d), eastgate.quote(d), fjord.quote(d))",
                         "            .map(t -> List.of(t.getT1(), t.getT2(), t.getT3()));",
                         "}"], 22, hl={"Mono.zip": CLERK})
        cg = VGroup(VGroup(kt, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                    VGroup(jt, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(cg, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(cg[0], shift=UP * 0.1), run_time=0.8)
        self.at_text("coroutineScope is", lead=0.3)
        self.play(Circumscribe(kc[0], color=CLERK, buff=0.05), run_time=1.0)
        self.at_text("The Java", lead=0.3)
        self.play(FadeIn(cg[1], shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.clear()

        # ================= the deadline, and the shy question =================
        ax = axis(-0.95, [0, 100, 200, 300, 400], 450)
        labs = VGroup(*[lane_label(n) for n in LANES])
        timer = timer_icon(BAD, 1.1).move_to([5.3, 2.6, 0])
        dl = DashedLine([tx(250), 1.8, 0], [tx(250), -0.85, 0], dash_length=0.08).set_stroke(BAD, 3)
        dl_t = T("deadline: 250 ms", 26, BAD).next_to(dl, UP, buff=0.1)
        never = T("no customer waits two seconds for a price", 24, GREY_B).move_to([0, -2.0, 0])
        self.say("deadline")
        self.play(FadeIn(ax), FadeIn(labs), run_time=0.6)
        self.at_text("won't wait", lead=0.3)
        self.play(FadeIn(never), run_time=0.5)
        self.at_text("So the cook", lead=0.3)
        self.play(FadeIn(timer), run_time=0.5)
        self.play(Create(dl), FadeIn(dl_t), run_time=0.7)
        self.hold()
        q1 = T("Where does the timer go?", 34, TICKET).move_to([0, -2.6, 0])
        q2 = VGroup(T("one around the whole job", 28), T("or", 28, GREY_B), T("one for each text?", 28)).arrange(RIGHT, buff=0.3)
        q2.next_to(q1, DOWN, buff=0.25)
        self.say("shyq")
        self.play(FadeOut(never), run_time=0.3)
        self.at_text("Where does", lead=0.3)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at_text("One timer", lead=0.3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.2, pos=(-6.4, 3.3), edge=LEFT)
        self.play(FadeOut(VGroup(q1, q2)), run_time=0.4)

        # ================= one timer around the job: break it =================
        job = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=tx(450) - tx(0) + 0.5, height=2.15), num_dashes=70)
        job.set_stroke(BAD, 2.5).move_to([(tx(0) + tx(450)) / 2 + 0.15, LANES["eastgate"], 0])
        job_l = T("one timer around everything", 24, BAD).next_to(job, UP, buff=0.12).align_to(job, LEFT)
        bars = {n: lbar(n, 0, 1) for n in LANES}
        tracker = ValueTracker(0)

        def grower2(n, stop):
            def upd(m):
                ms = min(MSV[n], tracker.get_value(), stop)
                m.become(lbar(n, 0, max(ms, 1)))
            return upd

        for n in LANES:
            bars[n].add_updater(grower2(n, 250))
        nl_c = price_chip("northline")
        fj_c = price_chip("fjord")
        self.say("one_timer")
        self.play(FadeOut(dl_t), Create(job), FadeIn(job_l), run_time=0.8)
        self.add(*bars.values())
        self.at_text("At 250", lead=0.3)
        self.play(tracker.animate.set_value(120), run_time=0.8, rate_func=linear)
        nl_c.next_to(bars["northline"], RIGHT, buff=0.15)
        self.add(nl_c)
        self.play(tracker.animate.set_value(200), run_time=0.6, rate_func=linear)
        fj_c.next_to(bars["fjord"], RIGHT, buff=0.15)
        self.add(fj_c)
        self.play(tracker.animate.set_value(250), run_time=0.4, rate_func=linear)
        for b in bars.values():
            b.clear_updaters()
        self.play(Wiggle(timer, scale_value=1.2), run_time=0.6)
        self.at_text("Eastgate is", lead=0.3)
        typing = T("still typing...", 22, EG).next_to(bars["eastgate"], RIGHT, buff=0.15)
        self.play(FadeIn(typing), run_time=0.4)
        self.at_text("So the timer", lead=0.3)
        self.play(job.animate.set_stroke(BAD, 5), *[b.animate.set_stroke(BAD, 3).set_fill(dim(BAD, 0.4), 1) for b in bars.values()],
                  run_time=0.7)
        self.hold()
        bin_ = VGroup(Polygon([-0.45, 0.4, 0], [0.45, 0.4, 0], [0.35, -0.45, 0], [-0.35, -0.45, 0]).set_stroke(GREY_B, 3)
                      .set_fill("#151515", 1), Line([-0.55, 0.45, 0], [0.55, 0.45, 0], stroke_width=4, color=GREY_B))
        bin_.move_to([4.6, -2.3, 0])
        nothing = T("the customer gets: nothing", 28, BAD).move_to([-1.0, -2.3, 0])
        self.say("one_timer2")
        self.play(Indicate(nl_c, color=OK), Indicate(fj_c, color=OK), run_time=0.8)
        self.at_text("both get thrown", lead=0.3)
        self.play(FadeIn(bin_), run_time=0.3)
        self.play(nl_c.animate.scale(0.6).move_to(bin_.get_center() + UP * 0.05 + LEFT * 0.15),
                  fj_c.animate.scale(0.6).move_to(bin_.get_center() + DOWN * 0.15 + RIGHT * 0.15), run_time=0.9)
        self.at_text("The customer", lead=0.3)
        self.play(FadeIn(nothing), run_time=0.5)
        self.hold()
        cash = T("the timer should cancel only the one who is late", 28, TICKET).move_to([-1.0, -3.15, 0])
        self.say("joke")
        self.at_text("So the point", lead=0.3)
        self.play(FadeIn(cash, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(job, job_l, *bars.values(), typing, nl_c, fj_c, bin_, nothing, cash)), run_time=0.6)

        # ================= one timer per call =================
        small = VGroup(*[timer_icon(BAD, 0.55).move_to([tx(0) - 0.15, LANES[n], 0]) for n in LANES])
        for sm, n in zip(small, LANES):
            sm.next_to(labs[list(LANES).index(n)], LEFT, buff=0.2)
        bars = {n: lbar(n, 0, 1) for n in LANES}
        tracker = ValueTracker(0)
        for n in LANES:
            bars[n].add_updater(grower2(n, 250))
        nl_c = price_chip("northline")
        fj_c = price_chip("fjord")
        self.say("per_call")
        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in small], lag_ratio=0.2), FadeIn(dl_t), run_time=0.8)
        self.add(*bars.values())
        self.at_text("At 250", lead=0.5)
        self.play(tracker.animate.set_value(120), run_time=0.6, rate_func=linear)
        self.add(nl_c.next_to(bars["northline"], RIGHT, buff=0.15))
        self.play(tracker.animate.set_value(200), run_time=0.45, rate_func=linear)
        self.add(fj_c.next_to(bars["fjord"], RIGHT, buff=0.15))
        self.play(tracker.animate.set_value(250), run_time=0.3, rate_func=linear)
        for b in bars.values():
            b.clear_updaters()
        self.play(Wiggle(small[1], scale_value=1.3), bars["eastgate"].animate.set_stroke(BAD, 3).set_fill(dim(BAD, 0.4), 1),
                  run_time=0.7)
        null = chip_m("null", GREY_B, 22).next_to(bars["eastgate"], RIGHT, buff=0.15)
        self.at_text("Its answer", lead=0.3)
        self.play(FadeIn(null), run_time=0.4)
        self.at_text("Northline and Fjord", lead=0.3)
        self.play(Indicate(nl_c, color=OK), Indicate(fj_c, color=OK), run_time=0.8)
        self.hold()
        out = M("with a 250 ms deadline: 250 ms  [northline 12.45, null, fjord 12.43]", 22, OK).move_to([0, -2.0, 0])
        best = VGroup(T("the customer gets", 26), M("fjord 12.43", 26, FJ), T("on time", 26)).arrange(RIGHT, buff=0.2)
        best.move_to([0, -2.62, 0])
        missed = VGroup(T("Eastgate's", 24, EG), M("12.41", 24, EG), T("would have been cheaper: too late is no price", 24, GREY_B))
        missed.arrange(RIGHT, buff=0.15).move_to([0, -3.2, 0])
        for m in (out, best, missed):
            fit(m, 12.4)
        self.say("per_call2")
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at_text("The customer gets", lead=0.3)
        self.play(FadeIn(best), Circumscribe(fj_c, color=FJ, buff=0.05), run_time=0.8)
        self.at_text("Eastgate's", lead=0.3)
        self.play(FadeIn(missed), run_time=0.6)
        self.hold()
        why = T("all three start together, so a timer per call is a timer for the request", 26, TICKET).move_to([0, 2.85, 0])
        fit(why, 12.4)
        self.say("why")
        self.play(FadeOut(timer), FadeIn(why, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= name it: withTimeoutOrNull =================
        kt = T("Kotlin", 24, GREY_B)
        kc = code_block(["providers.map { p ->",
                         "    async { withTimeoutOrNull(deadline) { p.quote(d) } }   // null if late",
                         "}"], 22, hl={"withTimeoutOrNull": BAD, "async": CLERK})
        jt = T("Java, with Reactor", 24, GREY_B)
        jc = code_block(["call.timeout(DEADLINE)",
                         "    .map(Optional::of)",
                         "    .onErrorResume(TimeoutException.class, e -> Mono.just(Optional.empty()));"], 22,
                        hl={"timeout": BAD, "Optional.empty()": GREY_B})
        cg = VGroup(VGroup(kt, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                    VGroup(jt, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(cg, 12.6).move_to(ORIGIN)
        self.say("name")
        self.play(FadeIn(cg[0], shift=UP * 0.1), run_time=0.8)
        self.at_text("At the deadline", lead=0.3)
        self.play(Circumscribe(kc[1], color=BAD, buff=0.05), run_time=1.0)
        self.at_text("Java's Reactor", lead=0.3)
        self.play(FadeIn(cg[1], shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.clear()

        # ================= where the picture bends =================
        left = VGroup(shop("a shop", GREY_B, 1.1), T("gets \"never mind\":", 26), T("stops typing at once", 26, OK)).arrange(DOWN, buff=0.25)
        right = VGroup(timer_icon(CLERK, 1.1), T("a cancelled coroutine:", 26),
                       T("stops at its next pause,", 26, TICKET), T("its next suspension point", 26, TICKET)).arrange(DOWN, buff=0.2)
        left.move_to([-3.4, 0.6, 0])
        right.move_to([3.4, 0.6, 0])
        stuck = T("a call stuck in a blocking wait keeps going until the wait ends", 26, GREY_A).move_to([0, -2.4, 0])
        fit(stuck, 12.4)
        self.say("breaks")
        self.at_text("A shop", lead=0.3)
        self.play(FadeIn(left), run_time=0.7)
        self.at_text("A cancelled", lead=0.3)
        self.play(FadeIn(right), run_time=0.7)
        self.at_text("A courier call", lead=0.3)
        self.play(FadeIn(stuck), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the edge: 100 ms =================
        ax = axis(-0.95, [0, 100, 200, 300, 400], 450)
        labs = VGroup(*[lane_label(n) for n in LANES])
        dl1 = DashedLine([tx(100), 1.8, 0], [tx(100), -0.85, 0], dash_length=0.08).set_stroke(BAD, 3)
        dl1_t = T("deadline: 100 ms", 26, BAD).next_to(dl1, UP, buff=0.1)
        self.say("guard")
        self.play(FadeIn(ax), FadeIn(labs), run_time=0.6)
        self.at_text("Make the timer", lead=0.3)
        self.play(Create(dl1), FadeIn(dl1_t), run_time=0.6)
        self.hold(after=0)
        self.predict(2.2, pos=(6.4, 3.3), edge=RIGHT)
        bars = {n: lbar(n, 0, 100, color=BAD) for n in LANES}
        nulls = VGroup(*[chip_m("null", GREY_B, 22).next_to(bars[n], RIGHT, buff=0.15) for n in LANES])
        stale = chip_m("7 STALE LISBON 12.41 eastgate", TICKET, 24).move_to([0, -2.5, 0])
        stale_l = T("later in the lesson: the last good price, marked stale", 24, GREY_B).next_to(stale, DOWN, buff=0.2)
        self.say("guard_a")
        self.play(*[GrowFromEdge(b, LEFT) for b in bars.values()], run_time=0.6)
        self.play(LaggedStart(*[FadeIn(n) for n in nulls], lag_ratio=0.15), run_time=0.6)
        self.at_text("Later in", lead=0.3)
        self.play(FadeIn(stale, shift=UP * 0.1), FadeIn(stale_l), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the open loop: a courier that fails =================
        three = VGroup(*[lbar(n, 0, MSV[n]) for n in LANES])
        labs = VGroup(*[lane_label(n) for n in LANES])
        err = chip_m("IOException", BAD, 22)
        self.say("loop")
        self.play(FadeIn(labs), FadeIn(three), run_time=0.6)
        self.at_text("it fails", lead=0.3)
        bad = lbar("northline", 0, 50, color=BAD)
        self.play(Transform(three[0], bad), FadeIn(err.next_to(bad, RIGHT, buff=0.15)), run_time=0.6)
        self.at_text("Inside", lead=0.3)
        self.play(three[1].animate.set_opacity(0.2), three[2].animate.set_opacity(0.2), run_time=0.7)
        nxt = T("next section: let each courier fail alone", 26, TICKET).move_to([0, -1.9, 0])
        self.at_text("That's the next", lead=0.3)
        self.play(FadeIn(nxt), run_time=0.5)
        self.hold()
        self.clear()

        # ================= moral and check =================
        mq = T("Where does the timer go?", 34, TICKET).move_to([0, 2.7, 0])
        m1 = T("on each call, not around the job", 30).next_to(mq, DOWN, buff=0.3)
        recap = VGroup(VGroup(phone(0.7, CLERK), T("text everyone at once", 26)).arrange(RIGHT, buff=0.25),
                       VGroup(Rectangle(width=0.6, height=0.25).set_stroke(EG, 2).set_fill(dim(EG, 0.45), 1),
                              T("the slowest decides", 26)).arrange(RIGHT, buff=0.25),
                       VGroup(timer_icon(BAD, 0.6), T("a late one drops out alone", 26)).arrange(RIGHT, buff=0.25))
        recap.arrange(RIGHT, buff=0.6).move_to([0, 0.6, 0])
        fit(recap, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("On each", lead=0.3)
        self.play(FadeIn(m1), run_time=0.6)
        self.at_text("Text everyone", lead=0.3)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in recap], lag_ratio=0.5), run_time=2.0)
        self.hold()

        qa = T("Check: one timer around the whole job, and all three answer before it rings.", 28).move_to([0, -0.9, 0])
        qb = T("Does the one-timer version lose anything?", 28, YELLOW_M).next_to(qa, DOWN, buff=0.2)
        for m in (qa, qb):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = T("No: nothing was late, so nothing was cancelled.", 28, OK).move_to([0, -2.7, 0])
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
