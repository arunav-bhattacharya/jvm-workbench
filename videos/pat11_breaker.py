from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bCallNotPermitted\b", "call not permitted"), (r"\bAtomicReference\b", "atomic reference"),
    (r"\b10:00:00\b", "ten o'clock"), (r"\b10:00:31\b", "ten o'clock and thirty-one seconds"),
    (r"\bcompare-and-set\b", "compare and set"), (r"\bhalf-open\b", "half open"),
]


# ---- local helpers ----
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

    def predict(self, secs=2.4, pos=(-6.4, 3.2), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole patterns track (the small town and its corner shop)
HALL, SHOP, PRICE, TA, TB, KEEP, BAD, OK = BLUE_M, TEAL_M, GOLD_M, YELLOW_M, PURPLE_M, GREY_A, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def shop(s=1.0, color=SHOP):
    b = Rectangle(width=2.4, height=1.6).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    aw = VGroup(*[Rectangle(width=0.4, height=0.32).set_stroke(color, 1.5).set_fill(color if i % 2 == 0 else dim(color, 0.3), 1)
                  for i in range(6)]).arrange(RIGHT, buff=0).next_to(b, UP, buff=0)
    win = Rectangle(width=1.0, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_center() + LEFT * 0.45 + DOWN * 0.1)
    door = Rectangle(width=0.5, height=0.9).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * 0.65 + UP * 0.45)
    sign = T("corner shop", 22, color).next_to(aw, UP, buff=0.1)
    return VGroup(b, aw, win, door, sign).scale(s)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def lbl_box(title, sub, color, w=3.4, h=1.5, mono=True):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    t = (M if mono else T)(title, 24, color)
    st = T(sub, 20, GREY_A)
    g = VGroup(t, st).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, g)


def vchip(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=0.56).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))



class Bar(VGroup):
    """A progress bar: an outline and a fill that grows from the left."""

    def __init__(self, w, color, label=None, h=0.34):
        super().__init__()
        self.w, self.frac = w, 0.0
        self.box = Rectangle(width=w, height=h).set_stroke(color, 2)
        self.fill = Rectangle(width=0.001, height=h).set_stroke(width=0).set_fill(color, 0.6)
        self.fill.align_to(self.box, LEFT)
        self.add(self.box, self.fill)
        if label:
            self.lab = M(label, 20, color).next_to(self.box, UP, buff=0.1)
            self.add(self.lab)

    def to(self, frac, run_time=1.0):
        a = self.frac
        self.frac = frac

        def upd(m, t):
            f = a + (frac - a) * t
            m.fill.stretch_to_fit_width(max(0.001, self.w * f))
            m.fill.align_to(m.box, LEFT)

        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=linear)



CLOSEDC, OPENC, HALFC, VANS, ASK = OK, BAD, GOLD_M, PURPLE_M, YELLOW_M


def state_box(name, sub, color, w=3.0, h=1.4):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3.5).set_fill(dim(color, 0.16), 1)
    g = VGroup(M(name, 28, color), T(sub, 22, GREY_A)).arrange(DOWN, buff=0.12).move_to(r)
    return VGroup(r, g)


def vans_box(s=1.0):
    r = RoundedRectangle(corner_radius=0.14, width=3.0, height=1.6).set_stroke(VANS, 3).set_fill(dim(VANS, 0.16), 1)
    van = VGroup(Rectangle(width=0.9, height=0.45).set_stroke(VANS, 2.5).set_fill(dim(VANS, 0.4), 1),
                 Rectangle(width=0.35, height=0.32).set_stroke(VANS, 2.5).set_fill(dim(VANS, 0.4), 1))
    van[1].next_to(van[0], RIGHT, buff=0).align_to(van[0], DOWN)
    wheels = VGroup(Circle(radius=0.09), Circle(radius=0.09)).set_stroke(VANS, 2.5).set_fill(BLACK, 1).arrange(RIGHT, buff=0.55)
    wheels.next_to(van, DOWN, buff=-0.08)
    v = VGroup(van, wheels)
    t = T("Big Blue Vans booking", 22, VANS)
    VGroup(v, t).arrange(DOWN, buff=0.15).move_to(r)
    return VGroup(r, v, t).scale(s)


def fuse_box(s=1.0):
    case = RoundedRectangle(corner_radius=0.1, width=2.0, height=2.6).set_stroke(GREY_B, 3).set_fill("#141414", 1)
    slot = Rectangle(width=0.5, height=1.2).set_stroke(GREY_B, 2).set_fill(BLACK, 1).move_to(case)
    lever = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.55).set_stroke(CLOSEDC, 2.5).set_fill(dim(CLOSEDC, 0.6), 1)
    lever.move_to(slot.get_top() + DOWN * 0.33)
    bolt = VMobject(stroke_color=ASK, stroke_width=4).set_points_as_corners([[0.1, 0.3, 0], [-0.12, 0.0, 0], [0.08, 0.0, 0], [-0.1, -0.3, 0]])
    bolt.move_to(case.get_top() + DOWN * 0.3)
    g = VGroup(case, slot, lever, bolt).scale(s)
    g.slot, g.lever = slot, lever
    return g


def trip_down(fb):
    return fb.lever.animate.move_to(fb.slot.get_bottom() + UP * 0.33 * (fb.slot.height / 1.2)).set_stroke(OPENC).set_fill(dim(OPENC, 0.6))


N = {
    "open": "Ten o'clock on a busy Saturday at the corner shop. The Big Blue Vans booking service goes quiet. Every call "
            "to it hangs for two seconds, and then fails. And each time, a customer at the counter stands there and "
            "waits.",
    "svc": "A service, here, is another program the shop's program calls over the network, like the van company's "
           "booking line.",
    "shyq": "So here's a question that's easy to be shy about. The van company is the one that's broken. So why is my "
            "shop the one that's slow?",
    "pain": "Because the shop keeps dialing. The first customer waits two seconds, for a no. The next one waits two "
            "seconds, for the same no. Every call holds a thread, and the queue at the counter grows.",
    "retry": "And the usual cure makes it worse. Retry three times, and each customer waits three times as long, for an "
             "answer that was never coming.",
    "joke": "It's like phoning a shop that's closed for the day, and deciding the fix is to phone it faster.",
    "wish": "What we'd like is for the shop to notice that the line is dead, stop dialing for a while, and now and then, "
            "check whether it's back.",
    "fuse": "The shop's back room already has a thing that does exactly that: the fuse box. When something goes wrong in "
            "the wiring, the circuit breaker trips and cuts the power, so the fault can't do more damage.",
    "map": "Let's map it. The wire is the call to the van company. Closed means the power flows, so calls go through. "
           "After a run of failures, it trips to open: calls fail at once, without even trying the vans. After a "
           "cool-down, it goes half-open, and lets one test call through, called a probe. If the probe works, it "
           "closes. If not, it opens again.",
    "joke2": "Yes, closed means the calls go through. Think of a closed loop of wire: the current can get all the way "
             "round. Open means there's a gap.",
    "shrink": "Let's use small numbers. The breaker opens after three failures in a row, and stays open for thirty "
              "seconds. A booking fails: closed, one. Another one: closed, two. A third: that's three, so it trips. "
              "Open, for the next thirty seconds.",
    "next": "Now the next booking arrives. The breaker is open, so it's turned away at once, with CallNotPermitted. No "
            "call to the van company, and no waiting. The customer hears no right away, and can try Pedal Post.",
    "pred": "Now the tricky moment. The breaker opened at 10:00:00, with a thirty second cool-down. At 10:00:31, eight "
            "threads call at the same moment. How many calls reach the van company? Pause and guess.",
    "naive": "Let's be fair to the obvious code first. Each thread reads the state, sees that the cool-down is over, and "
             "sets it to half-open. But two threads can both read open before either one sets it. Then several "
             "probes go out together, to a service that's barely back on its feet.",
    "cas": "So the move from open to half-open is a compare-and-set. Read it as: update it only if nobody beat me to "
           "it. All eight try. Exactly one wins, and runs the probe. The other seven find the state already changed, "
           "and are turned away. So the answer is one.",
    "name": "Now look at what it's made of: three patterns from this track, in one class. Its states are sealed records "
            "with a transition, as in the State lesson. Its call wraps any operation and keeps its shape, like a "
            "decorator. And its state lives in an AtomicReference, a holder that threads can swap safely.",
    "code": "Here's the transition after a failed call, applied in one atomic step. A failed probe opens it again. A "
            "closed breaker that reaches the threshold trips. A closed one below it counts one more. And an open one "
            "stays open.",
    "kotlin": "Kotlin says the same thing with a when.",
    "clock": "One more choice makes it testable. Time comes from a Clock passed in through the constructor. So a test "
             "hands it a fake clock, and moves time forward 31 seconds at once, instead of sleeping.",
    "joke3": "A test that sleeps for thirty seconds is a test that nobody runs twice.",
    "breaks": "The fuse box picture breaks in two places. A real breaker stays off until a person resets it. The software "
              "one tries again by itself, after the cool-down. And a real breaker reacts to the current in the wire. "
              "The software one only counts failures, so you must tell it which errors mean the service is sick.",
    "polite": "A van company that answers, no vans free in your area, is working perfectly. That's a polite no, not a "
              "sick service, and it must not trip the breaker.",
    "rule": "So here's the rule. Count only the failures that mean the service is sick, and let one probe, chosen by "
            "compare-and-set, decide when it has recovered.",
    "guard": "Two guardrails. Retry in one layer only, outside the breaker, and never retry a rejection: that's the "
             "breaker doing its job. And a breaker lives in one program's memory: two copies of the program have two "
             "breakers, so a limit for the whole shop needs something they share.",
    "moral": "So, why was my shop slow? Because it kept dialing. A breaker counts the sick failures, trips, turns "
             "callers away at once, and lets one probe find out when the line is back.",
    "check": "Quick check. The breaker is closed, with two failures counted, and the threshold is three. The next call "
             "succeeds. What's the state now?",
    "check_a": "Closed, with zero failures. A success resets the count. Only three failures in a row trip it.",
}


class Pat11CircuitBreaker(Narrated):
    """pat-11, section 3: the circuit breaker. Big Blue Vans goes quiet at ten (two second hangs); the shy question
    (they're broken, why is my shop slow?); dialing and retrying make it worse; the fuse box mapped to closed, open,
    half-open and the probe; small numbers (three failures, thirty seconds) traced; the next booking turned away;
    eight threads at 10:00:31 predicted; the naive check-then-set vs compare-and-set (one probe); State + Decorator +
    AtomicReference; the failure transition in Java and Kotlin; the injected Clock; where the fuse box breaks; the
    rule; guardrails; moral and a check (a success resets the count)."""

    def construct(self):
        self.title_card("A fuse box for the van company", "The circuit breaker: State, Decorator and compare-and-set")

        # ================= hook: the van company goes quiet =================
        sh = shop(0.95).move_to([-4.7, 0.9, 0])
        vb = vans_box().move_to([4.4, 0.9, 0])
        wire = Line(sh.get_right() + RIGHT * 0.1, vb.get_left() + LEFT * 0.1, stroke_width=3, color=GREY_B)
        clock10 = T("10:00, Saturday", 26, GREY_B).move_to([0, 3.0, 0])
        queue = VGroup(*[person(ASK, 0.9) for _ in range(3)]).arrange(RIGHT, buff=0.25).move_to([-4.7, -1.6, 0])
        self.say("open")
        self.play(FadeIn(sh), FadeIn(vb), Create(wire), FadeIn(clock10), run_time=0.9)
        self.at(1)
        self.play(vb[0].animate.set_stroke(GREY_D), vb[1].animate.set_opacity(0.35), run_time=0.7)
        self.at(2)
        dot = Dot(radius=0.11, color=ASK).move_to(wire.get_start())
        bar = Bar(2.4, OPENC, "2 s").move_to([0, 1.8, 0])
        self.play(FadeIn(dot), FadeIn(bar), run_time=0.3)
        self.play(dot.animate.move_to(wire.get_end()), run_time=0.6)
        self.play(bar.to(1.0, run_time=1.6))
        x = tick(False, 0.3).move_to(wire.get_center() + DOWN * 0.5)
        self.play(FadeOut(dot), FadeIn(x, scale=0.5), run_time=0.4)
        self.at(3)
        self.play(FadeIn(queue[0], shift=UP * 0.2), run_time=0.5)
        self.hold()
        self.play(FadeOut(x), FadeOut(bar), run_time=0.3)
        svc = T("a service: another program the shop calls over the network", 24, GREY_A).move_to([0, -3.1, 0])
        self.say("svc")
        self.play(FadeIn(svc), Indicate(vb[2], color=VANS), run_time=0.8)
        self.hold()
        self.play(FadeOut(svc), run_time=0.3)

        # ================= shy question =================
        shy = T("a question that's easy to be shy about", 24, GREY_B).move_to([0, -2.4, 0])
        q1 = T("The van company is the one that's broken.", 30)
        q2 = T("So why is my shop the one that's slow?", 30, ASK)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.15).next_to(shy, DOWN, buff=0.15)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(shy, q1, q2)), run_time=0.4)

        # ================= the pain: dialing and retrying =================
        def call_once(rt=1.0):
            d = Dot(radius=0.11, color=ASK).move_to(wire.get_start())
            b = Bar(2.4, OPENC, "2 s").move_to([0, 1.8, 0])
            self.play(FadeIn(d), FadeIn(b), run_time=0.2)
            self.play(d.animate.move_to(wire.get_end()), run_time=0.4 * rt)
            self.play(b.to(1.0, run_time=1.0 * rt))
            xx = tick(False, 0.3).move_to(wire.get_center() + DOWN * 0.5)
            self.play(FadeOut(d), FadeIn(xx, scale=0.5), run_time=0.3)
            self.play(FadeOut(xx), FadeOut(b), run_time=0.2)
        self.say("pain")
        self.at(1)
        call_once()
        self.at(2)
        self.play(FadeIn(queue[1], shift=UP * 0.2), run_time=0.4)
        call_once()
        self.at(3)
        self.play(FadeIn(queue[2], shift=UP * 0.2), run_time=0.4)
        more = VGroup(*[person(ASK, 0.9) for _ in range(3)]).arrange(RIGHT, buff=0.25).next_to(queue, RIGHT, buff=0.25)
        self.play(LaggedStart(*[FadeIn(m_, shift=UP * 0.2) for m_ in more], lag_ratio=0.3), run_time=1.0)
        self.hold()
        x3 = T("retry x3", 28, OPENC).move_to([-2.4, 1.8, 0])
        self.say("retry")
        self.play(FadeIn(x3), run_time=0.4)
        self.at(1)
        for _ in range(3):
            call_once(rt=0.55)
        self.hold()
        sign = card_t = VGroup(RoundedRectangle(corner_radius=0.08, width=1.9, height=0.6).set_stroke(OPENC, 2.5).set_fill(dim(OPENC, 0.3), 1),
                               T("CLOSED today", 22, WHITE))
        sign[1].move_to(sign[0])
        sign.next_to(vb, DOWN, buff=0.2)
        phone = VGroup(*[Arc(radius=0.2 + 0.15 * i, start_angle=-PI / 4, angle=PI / 2, stroke_width=3, color=ASK) for i in range(3)])
        phone.next_to(sh, RIGHT, buff=0.15)
        self.say("joke")
        self.play(FadeIn(sign, shift=DOWN * 0.1), run_time=0.5)
        self.play(LaggedStart(*[Create(a) for a in phone], lag_ratio=0.2), run_time=0.6)
        self.play(FadeOut(phone), run_time=0.2)
        self.play(LaggedStart(*[Create(a) for a in phone], lag_ratio=0.1), run_time=0.3)
        self.play(FadeOut(phone), run_time=0.2)
        self.hold()
        wish = T("Wish: notice the line is dead, stop dialing for a while, check now and then.", 28, ASK).move_to([0, -3.2, 0])
        wish.scale(min(1, 12.6 / wish.width))
        self.say("wish")
        self.play(FadeOut(x3), FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the fuse box =================
        fb = fuse_box(1.3).move_to([-4.4, 0.4, 0])
        fbl = T("the fuse box", 26, GREY_A).next_to(fb, DOWN, buff=0.25)
        self.say("fuse")
        self.play(FadeIn(fb), FadeIn(fbl), run_time=0.8)
        self.at(1)
        spark = VMobject(stroke_color=ASK, stroke_width=5).set_points_as_corners([[0, 0, 0], [0.3, 0.2, 0], [0.2, -0.05, 0], [0.55, 0.15, 0]]).next_to(fb, RIGHT, buff=0.2)
        self.play(Create(spark), run_time=0.4)
        self.play(trip_down(fb), FadeOut(spark), fb[3].animate.set_opacity(0.2), run_time=0.7)
        self.hold()

        # ================= map it: the three states =================
        cl = state_box("Closed", "calls go through", CLOSEDC).move_to([-1.2, 1.4, 0])
        op = state_box("Open", "turn away at once", OPENC).move_to([3.8, 1.4, 0])
        ho = state_box("HalfOpen", "one probe", HALFC).move_to([3.8, -1.6, 0])
        a1 = Arrow(cl.get_right(), op.get_left(), buff=0.12, stroke_width=3.5, color=OPENC, max_tip_length_to_length_ratio=0.12)
        a1t = T("a run of failures", 22, OPENC).next_to(a1, UP, buff=0.1)
        a2 = Arrow(op.get_bottom() + LEFT * 0.6, ho.get_top() + LEFT * 0.6, buff=0.1, stroke_width=3.5, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a2t = T("cool-down over", 22, GREY_A).next_to(a2, LEFT, buff=0.15)
        a3 = Arrow(ho.get_top() + RIGHT * 0.6, op.get_bottom() + RIGHT * 0.6, buff=0.1, stroke_width=3.5, color=OPENC, max_tip_length_to_length_ratio=0.12)
        a3t = T("probe fails", 22, OPENC).next_to(a3, RIGHT, buff=0.15)
        a4 = Arrow(ho.get_left(), cl.get_bottom() + DOWN * 0.0, buff=0.12, stroke_width=3.5, color=CLOSEDC, max_tip_length_to_length_ratio=0.1)
        a4t = T("probe works", 22, CLOSEDC).next_to(a4.get_center(), DOWN + LEFT, buff=0.15)
        wl = VGroup(T("the wire =", 22, GREY_A), T("the call to the vans", 22, GREY_A)).arrange(DOWN, buff=0.08)
        self.say("map")
        self.play(VGroup(fb, fbl).animate.scale(0.75).move_to([-5.0, 1.0, 0]), run_time=0.5)
        wl.next_to(VGroup(fb, fbl), DOWN, buff=0.3)
        self.at(1)
        self.play(FadeIn(wl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cl), fb.lever.animate.move_to(fb.slot.get_top() + DOWN * 0.25).set_stroke(CLOSEDC).set_fill(dim(CLOSEDC, 0.6)), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(a1), FadeIn(a1t), FadeIn(op), trip_down(fb), run_time=0.8)
        self.at(4)
        self.play(GrowArrow(a2), FadeIn(a2t), FadeIn(ho), run_time=0.8)
        self.at(5)
        self.play(GrowArrow(a4), FadeIn(a4t), run_time=0.7)
        self.at(6)
        self.play(GrowArrow(a3), FadeIn(a3t), run_time=0.7)
        self.hold()
        loop = VGroup(Circle(radius=0.55).set_stroke(CLOSEDC, 4), Dot(radius=0.08, color=ASK))
        loop.move_to([-5.0, -2.2, 0])
        loop[1].move_to(loop[0].point_at_angle(0))
        gap = VGroup(Arc(radius=0.55, start_angle=0.5, angle=2 * PI - 1.0, stroke_width=4, color=OPENC)).move_to([-3.4, -2.2, 0])
        lt = VGroup(T("closed: round and round", 20, CLOSEDC).next_to(loop, DOWN, buff=0.1), T("open: a gap", 20, OPENC).next_to(gap, DOWN, buff=0.1))
        self.say("joke2")
        self.play(FadeIn(loop[0]), FadeIn(lt[0]), run_time=0.5)
        self.play(MoveAlongPath(loop[1], loop[0]), run_time=1.2, rate_func=linear)
        self.at(2)
        self.play(FadeIn(gap), FadeIn(lt[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= small numbers: three failures, thirty seconds =================
        lim = T("opens after 3 failures in a row, for 30 seconds", 28, GREY_A).move_to([0, 3.0, 0])
        st = state_box("Closed(0)", "calls go through", CLOSEDC, w=3.6).move_to([0, 1.2, 0])
        log = VGroup()
        def set_state(name, sub, color):
            n = state_box(name, sub, color, w=3.6).move_to(st)
            return Transform(st, n)
        self.say("shrink")
        self.at(1)
        self.play(FadeIn(lim), FadeIn(st), run_time=0.7)
        fails = VGroup(*[VGroup(tick(False, 0.22), T("booking %d fails" % (i + 1), 24, GREY_A)).arrange(RIGHT, buff=0.2) for i in range(3)])
        fails.arrange(RIGHT, buff=0.7).move_to([0, -0.6, 0])
        self.at(2)
        self.play(FadeIn(fails[0]), set_state("Closed(1)", "one failure", CLOSEDC), run_time=0.6)
        self.at(3)
        self.play(FadeIn(fails[1]), set_state("Closed(2)", "two failures", CLOSEDC), run_time=0.6)
        self.at(4)
        self.play(FadeIn(fails[2]), set_state("Open(until)", "until 30 seconds from now", OPENC), run_time=0.7)
        self.hold()
        vb2 = vans_box(0.8).move_to([4.6, -2.3, 0])
        cnp = vchip("CallNotPermitted", OPENC, 24).move_to([-1.4, -2.3, 0])
        bk = Dot(radius=0.12, color=ASK).move_to([-5.8, -2.3, 0])
        alt = T("try Pedal Post instead", 24, CLOSEDC).move_to([-3.6, -3.2, 0])
        self.say("next")
        self.play(FadeOut(fails), FadeIn(vb2), FadeIn(bk), run_time=0.5)
        self.play(bk.animate.move_to([-0.2, -2.3, 0]), run_time=0.6)
        self.at(1)
        self.play(Indicate(st[0], color=OPENC, scale_factor=1.04), run_time=0.5)
        self.play(bk.animate.move_to([-4.6, -2.3, 0]), FadeIn(cnp, shift=LEFT * 0.2), run_time=0.6)
        self.at(2)
        self.play(Indicate(vb2[2], color=VANS), run_time=0.6)
        self.at(3)
        self.play(FadeIn(alt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= predict: eight threads at 10:00:31 =================
        tl = VGroup(T("opened 10:00:00", 26, OPENC), T("cool-down 30 s", 26, GREY_A), T("now 10:00:31", 26, ASK)).arrange(RIGHT, buff=0.9).move_to([0, 3.0, 0])
        st2 = state_box("Open(until)", "cool-down is over", OPENC, w=3.6).move_to([0.6, 0.4, 0])
        vb3 = vans_box(0.8).move_to([5.0, 0.4, 0])
        thr = VGroup(*[Dot(radius=0.13, color=ASK) for _ in range(8)]).arrange(DOWN, buff=0.22).move_to([-5.2, 0.4, 0])
        thl = T("8 threads", 24, ASK).next_to(thr, UP, buff=0.2)
        self.say("pred")
        self.play(FadeIn(tl[0]), FadeIn(st2), FadeIn(vb3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tl[1]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(tl[2]), LaggedStart(*[FadeIn(d) for d in thr], lag_ratio=0.1), FadeIn(thl), run_time=0.9)
        self.hold(after=0)
        self.predict(2.8, pos=(6.4, -3.4), edge=RIGHT)

        # the obvious code: read, then set
        nc = VGroup(M("if (s instanceof Open && cool-down over)", 22, GREY_A), M("    state.set(new HalfOpen());   // read, then set", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        nc.move_to([0, -2.6, 0])
        nctag = T("the obvious code (a sketch)", 20, GREY_B).next_to(nc, UP, buff=0.1).align_to(nc, LEFT)
        self.say("naive")
        self.play(FadeIn(nc), FadeIn(nctag), run_time=0.6)
        self.at(1)
        self.play(*[d.animate.shift(RIGHT * 2.2) for d in thr], run_time=0.8)
        self.at(2)
        self.play(Indicate(thr[1], color=ASK, scale_factor=1.6), Indicate(thr[5], color=ASK, scale_factor=1.6), run_time=0.8)
        self.at(3)
        probes = [thr[1], thr[5], thr[3]]
        self.play(*[d.animate.move_to(vb3.get_left() + LEFT * 0.2 + UP * (0.4 - 0.4 * k)) for k, d in enumerate(probes)],
                  Indicate(vb3[0], color=OPENC, scale_factor=1.03), run_time=1.0)
        sev = T("more than one probe", 26, OPENC).next_to(vb3, UP, buff=0.3)
        self.play(FadeIn(sev), run_time=0.4)
        self.hold()
        self.play(FadeOut(VGroup(nc, nctag, sev, thr)), run_time=0.4)

        # compare-and-set: one winner
        thr = VGroup(*[Dot(radius=0.13, color=ASK) for _ in range(8)]).arrange(DOWN, buff=0.22).move_to([-5.2, 0.4, 0])
        cc = VGroup(M("state.compareAndSet(s, new HalfOpen())", 24, HALFC), M("state.compareAndSet(s, State.HalfOpen)", 24, HALFC)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cct = VGroup(T("Java", 20, GREY_B), T("Kotlin", 20, GREY_B))
        for t_, c_ in zip(cct, cc):
            t_.next_to(c_, LEFT, buff=0.3)
        ccg = VGroup(cc, cct).move_to([0, -2.7, 0])
        self.say("cas")
        self.play(FadeIn(thr), FadeIn(ccg), run_time=0.6)
        self.at(1)
        self.play(Indicate(cc[0], color=HALFC, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(*[d.animate.shift(RIGHT * 2.2) for d in thr], run_time=0.7)
        self.at(3)
        win = thr[4]
        ho2 = state_box("HalfOpen", "one probe", HALFC, w=3.6).move_to(st2)
        self.play(Transform(st2, ho2), win.animate.set_color(CLOSEDC).scale(1.3), run_time=0.6)
        self.play(win.animate.move_to(vb3.get_left() + LEFT * 0.25), run_time=0.7)
        self.at(4)
        rest = VGroup(*[d for k, d in enumerate(thr) if k != 4])
        self.play(rest.animate.set_color(OPENC).shift(LEFT * 1.6), run_time=0.8)
        self.at(5)
        one = T("1", 72, CLOSEDC).next_to(vb3, UP, buff=0.3)
        self.play(FadeIn(one, scale=0.5), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= name it: three patterns in one class =================
        cards = VGroup(lbl_box("State", "sealed states, one transition", CLOSEDC, w=4.0, h=1.6, mono=False),
                       lbl_box("Decorator", "call(op) wraps any operation", HALFC, w=4.0, h=1.6, mono=False),
                       lbl_box("compare-and-set", "state in an AtomicReference", BLUE_M, w=4.0, h=1.6, mono=False)).arrange(RIGHT, buff=0.3)
        cards.scale(min(1, 12.6 / cards.width)).move_to([0, 0.4, 0])
        title = T("one circuit breaker", 32, WHITE).move_to([0, 2.5, 0])
        self.say("name")
        self.play(FadeIn(title), run_time=0.5)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(cards[i], shift=UP * 0.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the transition in code =================
        cj = titled(code_block([
            "sealed interface State permits Closed, Open, HalfOpen {}",
            "record Closed(int consecutiveFailures) implements State {}",
            "record Open(Instant until) implements State {}",
            "record HalfOpen() implements State {}",
            "",
            "private final AtomicReference<State> state =",
            "        new AtomicReference<>(new Closed(0));",
            "",
            "// after a failed call: one pure transition, applied atomically",
            "state.updateAndGet(cur -> switch (cur) {",
            "    case HalfOpen h -> new Open(clock.instant().plus(openFor));",
            "    case Closed(var n) when n + 1 >= threshold ->",
            "        new Open(clock.instant().plus(openFor));",
            "    case Closed(var n) -> new Closed(n + 1);",
            "    case Open o -> o;",
            "});"], 22), "Java")
        cj.scale(min(1, 12.6 / cj.width, 6.7 / cj.height)).move_to([0, 0, 0])
        L = cj[1]
        self.say("code")
        self.play(FadeIn(cj, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(L[10], color=OPENC, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(Indicate(VGroup(L[11], L[12]), color=OPENC, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(Indicate(L[13], color=CLOSEDC, scale_factor=1.03), run_time=0.7)
        self.at(4)
        self.play(Indicate(L[14], color=OPENC, scale_factor=1.03), run_time=0.7)
        self.hold()
        ck = titled(code_block([
            "sealed interface State {",
            "    data class Closed(val consecutiveFailures: Int) : State",
            "    data class Open(val until: Instant) : State",
            "    data object HalfOpen : State",
            "}",
            "private val state = AtomicReference<State>(State.Closed(0))",
            "",
            "state.updateAndGet { cur ->",
            "    when (cur) {",
            "        State.HalfOpen -> State.Open(clock.instant() + openFor)",
            "        is State.Closed if cur.consecutiveFailures + 1 >= threshold ->",
            "            State.Open(clock.instant() + openFor)",
            "        is State.Closed -> State.Closed(cur.consecutiveFailures + 1)",
            "        is State.Open -> cur",
            "    }",
            "}"], 22), "Kotlin")
        ck.scale(min(1, 12.6 / ck.width, 6.7 / ck.height)).move_to([0, 0, 0])
        self.say("kotlin")
        self.play(FadeOut(cj), FadeIn(ck), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the injected clock =================
        cl1 = titled(code_block(["CircuitBreaker(int failureThreshold, Duration openFor, Clock clock)"], 24), "the clock comes in through the constructor")
        cl1.scale(min(1, 12.6 / cl1.width)).move_to([0, 2.3, 0])
        face = VGroup(Circle(radius=0.9).set_stroke(GREY_B, 3), Dot(radius=0.06, color=WHITE))
        hand = Line(ORIGIN, UP * 0.75, stroke_width=4, color=ASK)
        face.add(hand)
        face.move_to([-3.0, -0.6, 0])
        ft = T("a fake clock", 24, ASK).next_to(face, DOWN, buff=0.2)
        jump = T("+31 seconds, at once", 30, ASK).move_to([2.2, -0.6, 0])
        self.say("clock")
        self.at(1)
        self.play(FadeIn(cl1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(face), FadeIn(ft), run_time=0.5)
        self.play(Rotate(hand, angle=-PI * 31 / 30, about_point=face[1].get_center()), FadeIn(jump), run_time=0.6)
        self.hold()
        zz = T("z z z", 34, GREY_B).move_to([2.2, -2.2, 0])
        self.say("joke3")
        self.play(FadeIn(zz, shift=UP * 0.3), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= where the fuse box breaks =================
        fb2 = fuse_box(1.1).move_to([-5.0, 1.2, 0])
        fb2.lever.move_to(fb2.slot.get_bottom() + UP * 0.33 * (fb2.slot.height / 1.2)).set_stroke(OPENC).set_fill(dim(OPENC, 0.6))
        hand_p = who(GREY_A, "real: a person resets it", 0.9, 20).next_to(fb2, RIGHT, buff=1.5)
        sw = VGroup(T("software:", 26, HALFC), T("tries again by itself after the cool-down", 26, WHITE)).arrange(RIGHT, buff=0.2).move_to([2.0, 1.9, 0])
        sw.scale(min(1, 7.6 / sw.width))
        cnt = VGroup(T("real: reacts to the current in the wire", 26, GREY_A), T("software: only counts failures", 26, HALFC),
                     T("so tell it which errors mean the service is sick", 26, ASK)).arrange(DOWN, buff=0.18).move_to([1.0, -0.6, 0])
        self.say("breaks")
        self.play(FadeIn(fb2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hand_p), run_time=0.5)
        self.at(2)
        self.play(FadeIn(sw), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cnt[0]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(cnt[1]), run_time=0.5)
        self.at_text("so you must", lead=0.3)
        self.play(FadeIn(cnt[2]), run_time=0.5)
        self.hold()
        nv = vchip("no vans free in your area", CLOSEDC, 24).move_to([0, -2.6, 0])
        nvt = T("a polite no: working perfectly, must not trip", 24, CLOSEDC).next_to(nv, DOWN, buff=0.15)
        self.say("polite")
        self.play(FadeIn(nv, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(nvt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= rule and guardrails =================
        r1 = T("Count only the failures that mean the service is sick,", 30)
        r2 = T("and let one probe, chosen by compare-and-set, decide when it has recovered.", 30, ASK)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.2).move_to([0, 2.5, 0])
        rg.scale(min(1, 12.6 / rg.width))
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        lay = VGroup(lbl_box("retry", "outermost", GREY_B, w=6.6, h=2.6, mono=False), lbl_box("breaker", "inside", CLOSEDC, w=3.6, h=1.2, mono=False))
        lay[0][1].move_to(lay[0][0].get_top() + DOWN * 0.45)
        lay[1].move_to(lay[0][0].get_center() + DOWN * 0.35)
        lay.move_to([-2.6, -1.0, 0])
        nr = VGroup(T("never retry a rejection:", 24, OPENC), M("CallNotPermitted", 24, OPENC), T("is the breaker doing its job", 24, GREY_A)).arrange(DOWN, buff=0.12)
        nr.move_to([3.6, -0.2, 0])
        two = VGroup(lbl_box("copy 1", "its own breaker", BLUE_M, w=2.5, h=1.1, mono=False), lbl_box("copy 2", "its own breaker", BLUE_M, w=2.5, h=1.1, mono=False)).arrange(RIGHT, buff=0.3)
        two.move_to([3.6, -2.6, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(lay), run_time=0.7)
        self.at_text("never retry", lead=0.3)
        self.play(FadeIn(nr), run_time=0.6)
        self.at(2)
        self.play(FadeIn(two), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why was my shop slow?", 34)
        m1 = T("Because it kept dialing.", 30, OPENC)
        m2 = T("A breaker counts the sick failures, trips, turns callers away at once,", 28)
        m3 = T("and lets one probe find out when the line is back.", 28, ASK)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.22).move_to(UP * 2.0)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qa = VGroup(T("Check: the breaker is", 28), M("Closed(2)", 28, CLOSEDC), T(", the threshold is 3.", 28)).arrange(RIGHT, buff=0.15)
        qb = T("The next call succeeds. What's the state now?", 28, ASK)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to(DOWN * 0.9)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(M("Closed(0)", 30, CLOSEDC), T("A success resets the count. Only three failures in a row trip it.", 26, GREY_A)).arrange(DOWN, buff=0.15).move_to(DOWN * 2.6)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
