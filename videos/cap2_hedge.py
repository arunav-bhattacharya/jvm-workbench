from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bp50\b", "p fifty"), (r"\bp99\b", "p ninety-nine"), (r"\bp95\b", "p ninety-five"),
    (r"\bcoroutineScope\b", "coroutine scope"), (r"\bcancelChildren\b", "cancel children"),
]

# every spoken line, in order
N = {
    "open": "It's the last day before the holidays, and the post office queue runs out of the door. Our quote service "
            "already gives each courier its own limit, and it asks again when a call fails.",
    "open2": "But Northline has a different habit. Most of the time it answers in 40 milliseconds. One call in twenty "
             "takes 600. Nothing fails. Northline is just lost in thought now and then.",
    "retry": "So a retry doesn't help. A retry fires when a call fails, and this call hasn't failed. It's only slow.",
    "pct": "Let's draw twenty calls, and add one more word. A percentile says how slow the slow ones are. p50 is the "
           "time half the calls beat: here, 40 milliseconds. p99 is the time 99 calls in 100 beat: here, 600.",
    "tail": "The slowest few calls are the tail, and tail latency is what the unluckiest customers see. One customer "
            "in twenty isn't rare. It's somebody in every queue.",
    "shyq": "So here's a question that feels a bit like cheating. If Northline is slow, why not just ask it again? And "
            "if we do, don't we double the work?",
    "naive": "Let's try the bold version first. Ask twice, every time. Send the second question after 30 milliseconds, "
             "before Northline would normally have answered.",
    "naive2": "The lesson's demo counted. For 200 prices, 400 calls to Northline. Twice the load, every single time, "
              "to rescue one call in twenty.",
    "naive_joke": "That's like posting every parcel twice because the postman once took a long lunch. The second "
                  "question should go only to the calls that are actually late.",
    "analogy": "Back to the cook. She texts a shop, and shops nearly always reply within a few moments. If this one "
               "hasn't replied by then, she texts the other branch of the same shop. Whichever branch answers first, "
               "she takes, and she tells the other one: never mind.",
    "map": "Let's map it. The first text is the first call. The few moments are the hedge time, taken from "
           "Northline's measured speed. The demo uses 80 milliseconds. The second text is the hedge, one more "
           "identical call. Taking the first answer is select. And never mind is cancelling the loser.",
    "predict": "Now the slow call. The first question goes out at zero and would take 600. What's the longest a "
               "customer waits now?",
    "show": "At 80 milliseconds, still nothing. So the hedge goes out. It's a normal call, so it answers 40 "
            "milliseconds later, at 120. The hedge wins, and the slow first call is cancelled.",
    "show2": "80 of waiting, plus 40 for the hedge. 120 milliseconds instead of 600.",
    "demo": "The demo asked Northline for 200 prices, without a hedge and with a hedge at 80. p50 stays at 40. p99 "
            "falls from 600 to 120. And the calls: 210 instead of 200.",
    "cost": "Ten extra calls, 5 percent more, because only the slow 5 percent ever got a hedge. That's the answer to "
            "our question. We don't double the work. We spend a little, exactly where it hurts.",
    "name": "This move is called a hedge, like hedging a bet: a small second bet, so that one bad outcome can't hurt "
            "you much.",
    "code": "In Kotlin: start the first call. Wait for it, but only until the hedge time. If nothing came back, start "
            "the second call, and select whichever answers first. Then cancel the children, which stops the loser. "
            "Java with Reactor says it in one line: the first with a value, of the call, and the same call after a "
            "delay.",
    "code_joke": "Forget that cancel line, and coroutineScope waits for the slow call anyway, which undoes the whole "
                 "hedge. It's like getting your answer from the second branch, and then standing by the phone for "
                 "the first one anyway.",
    "g1": "Now the guardrails, because a hedge is a duplicate request. One. Hedge only a call that's safe to repeat. "
          "Northline and Eastgate only look up a price. Fjord's price is a booking: each call holds a seat on one of "
          "its vans. Hedge Fjord, and you book two vans for one parcel.",
    "g2": "Two. Hedge only the courier whose tail hurts, here Northline, at a time taken from its measured speed. Too "
          "early, and every request gets hedged. That's the 400 calls we saw.",
    "g3": "Three. The hedge takes its own permit, a token from Northline's limit of ten calls at a time. And here the "
          "cook's picture breaks. The other branch of a shop has its own staff, but our second call goes to the same "
          "Northline.",
    "g3b": "When Northline is swamped, a hedge only joins the queue that made it slow. So under full load, the hedge "
           "waits for a permit, and the first call usually wins.",
    "moral": "So, is a second question cheating? Not if it goes only to the slow tail. Wait until the usual time, ask "
             "once more, take the first answer, and cancel the other. A hedge is a duplicate request. Spend it on the "
             "slow tail, and only where a duplicate is harmless.",
    "check": "Quick check. You hedge Fjord instead of Northline. What goes wrong?",
    "check_a": "Every hedge holds a second seat on a van. Fjord's call is a booking, not safe to repeat, so it's asked "
               "exactly once.",
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



HEDGE = "#C9A0DC"     # the hedge: a lighter purple, apart from the clerk


def shop(name, color, s=1.0):
    body = Rectangle(width=1.3, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.14), 1)
    awn = Polygon([-0.78, 0, 0], [0.78, 0, 0], [0.62, 0.3, 0], [-0.62, 0.3, 0]).set_stroke(color, 2.5)
    awn.set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0)
    door = Rectangle(width=0.3, height=0.42).set_stroke(color, 2).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.21)
    lab = T(name, 22, color).next_to(body, DOWN, buff=0.15)
    return VGroup(body, awn, door, lab).scale(s)


def van(color=FJ, s=1.0):
    cargo = Rectangle(width=1.2, height=0.7).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    cab = Polygon([0, 0, 0], [0.45, 0, 0], [0.45, 0.3, 0], [0.3, 0.5, 0], [0, 0.5, 0]).set_stroke(color, 3).set_fill(dim(color, 0.4), 1)
    cab.next_to(cargo, RIGHT, buff=0.04).align_to(cargo, DOWN)
    wheels = VGroup(*[Circle(radius=0.13).set_stroke(GREY_B, 3).set_fill(BLACK, 1) for _ in range(2)])
    wheels[0].move_to(cargo.get_corner(DL) + RIGHT * 0.3)
    wheels[1].move_to(cab.get_bottom())
    return VGroup(cargo, cab, wheels).scale(s)


def span(line, sub):
    """Slice of a Text's glyphs (spaces are not glyphs) that spells sub."""
    flat = line.replace(" ", "")
    a = flat.index(sub.replace(" ", ""))
    return slice(a, a + len(sub.replace(" ", "")))


def token(color=OK, r=0.13):
    return Circle(radius=r).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)


# a time axis: x(ms)
X0, PX = -4.3, 0.0125


def tx(ms):
    return X0 + ms * PX


def axis(y, ticks, end):
    ln = Arrow([tx(0) - 0.1, y, 0], [tx(end), y, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.02)
    tk = VGroup(*[VGroup(Line([tx(m), y - 0.07, 0], [tx(m), y + 0.07, 0], stroke_width=2, color=GREY_B),
                         T(f"{m}", 20, GREY_B).move_to([tx(m), y - 0.3, 0])) for m in ticks])
    ms = T("ms", 20, GREY_B).next_to(ln, RIGHT, buff=0.1)
    return VGroup(ln, tk, ms)


def hbar(ms0, ms1, y, color, h=0.1, op=0.6):
    r = Rectangle(width=max(0.03, (ms1 - ms0) * PX), height=h).set_stroke(color, 1.5).set_fill(dim(color, op), 1)
    return r.move_to([(tx(ms0) + tx(ms1)) / 2, y, 0])


def vline(ms, y0, y1, color, text, size=24, side=UP, sw=2.5):
    ln = DashedLine([tx(ms), y0, 0], [tx(ms), y1, 0], dash_length=0.08).set_stroke(color, sw)
    t = T(text, size, color).next_to(ln, side, buff=0.08)
    return VGroup(ln, t)


class Cap2Hedge(Narrated):
    """cap2-03, section 2: hedge Northline's slow tail. The busiest day; Northline at 40 ms with one call in twenty
    at 600; a retry never fires; twenty calls with p50 and p99; the tail; the shy question (isn't asking twice
    cheating, and doesn't it double the work?); ask twice every time (30 ms: 400 calls); the cook texts the other
    branch, mapped; predict; the slow call rescued at 80 + 40 = 120 ms with the loser cancelled; the demo lines
    (p99 600 to 120, 200 to 210 calls, 5%); named; the code in Kotlin and Java with the cancel line; three guardrails
    (Fjord's two vans, a measured time, its own permit, where the picture breaks); moral; check."""

    def construct(self):
        self.title_card("A second question for the slow one", "hedging Northline's slow tail")

        # ================= hook: the busiest day =================
        counter = Rectangle(width=2.2, height=0.4).set_stroke(GREY_B, 2.5).set_fill("#151515", 1).move_to([-3.0, -1.0, 0])
        clerk = person(CLERK, 1.2).next_to(counter, UP, buff=0.05)
        queue = VGroup(*[person(CUST, 0.75) for _ in range(9)]).arrange(LEFT, buff=0.12).next_to(counter, LEFT, buff=0.25)
        queue.align_to(counter, DOWN)
        fit(queue, 1.9)
        queue.next_to(counter, LEFT, buff=0.2).align_to(counter, DOWN)
        nl = depot("Northline", NL, 1.1).move_to([3.8, 0.0, 0])
        has = VGroup(VGroup(token(OK), T("a limit for each courier", 24)).arrange(RIGHT, buff=0.2),
                     VGroup(Arc(radius=0.15, angle=1.6 * PI, stroke_width=3, color=OK).add_tip(tip_length=0.1),
                            T("a retry when a call fails", 24)).arrange(RIGHT, buff=0.2))
        has.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-2.6, 2.2, 0])
        self.say("open")
        self.play(FadeIn(counter), FadeIn(clerk), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.2) for p in queue], lag_ratio=0.1), run_time=1.0)
        self.at_text("Our quote", lead=0.3)
        self.play(FadeIn(nl), run_time=0.5)
        self.at_text("its own limit", lead=0.4)
        self.play(FadeIn(has[0]), run_time=0.5)
        self.at_text("and it asks", lead=0.3)
        self.play(FadeIn(has[1]), run_time=0.5)
        self.hold()

        usual = T("usually: 40 ms", 26, NL).next_to(nl, DOWN, buff=0.25)
        rare = T("one call in twenty: 600 ms", 26, BAD).next_to(usual, DOWN, buff=0.15)
        bubble = VGroup(*[Circle(radius=r).set_stroke(GREY_B, 2) for r in (0.07, 0.11, 0.3)])
        bubble[0].move_to(nl.get_corner(UR) + RIGHT * 0.1 + UP * 0.05)
        bubble[1].move_to(bubble[0].get_center() + UR * 0.22)
        bubble[2].move_to(bubble[1].get_center() + UR * 0.4)
        dots3 = T("...", 26, GREY_B).move_to(bubble[2])
        self.say("open2")
        self.at_text("Most of the time", lead=0.3)
        self.play(FadeIn(usual), run_time=0.5)
        self.at_text("One call", lead=0.3)
        self.play(FadeIn(rare), run_time=0.5)
        self.at_text("Northline is just", lead=0.3)
        self.play(FadeIn(bubble, lag_ratio=0.3), FadeIn(dots3), run_time=0.8)
        self.hold()
        nofail = VGroup(tick(False, 0.2), T("fires only after a failure; nothing failed", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        nofail.next_to(has[1], DOWN, buff=0.2).align_to(has, LEFT)
        self.say("retry")
        self.play(Indicate(has[1][1], color=TICKET, scale_factor=1.05), run_time=0.7)
        self.play(FadeIn(nofail), run_time=0.5)
        self.hold()
        self.clear()

        # ================= twenty calls, percentiles, the tail =================
        ax = axis(-1.25, [0, 100, 200, 300, 400, 500, 600, 700], 760)
        ys = [2.55 - 0.17 * i for i in range(20)]
        calls = VGroup(*[hbar(0, 600 if i == 13 else 40, ys[i], BAD if i == 13 else NL) for i in range(20)])
        cl_l = VGroup(T("20 calls", 24, GREY_B), T("to Northline", 24, GREY_B)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
        cl_l.move_to([tx(0) - 0.2, 1.0, 0], aligned_edge=RIGHT)
        self.say("pct")
        self.play(FadeIn(ax), FadeIn(cl_l), run_time=0.5)
        self.play(LaggedStart(*[GrowFromEdge(c, LEFT) for c in calls], lag_ratio=0.08), run_time=2.0)
        p50 = vline(40, 2.75, -1.15, OK, "p50: 40 ms")
        p50[1].shift(RIGHT * 0.55)
        p99 = vline(600, 2.75, -1.15, BAD, "p99: 600 ms")
        self.at_text("p50 is", lead=0.3)
        self.play(Create(p50[0]), FadeIn(p50[1]), run_time=0.7)
        self.at_text("p99 is", lead=0.3)
        self.play(Create(p99[0]), FadeIn(p99[1]), run_time=0.7)
        self.hold()
        tail_b = SurroundingRectangle(calls[13], buff=0.08, color=BAD, stroke_width=3)
        tail_l = T("the tail: what the unluckiest customers see", 26, BAD).move_to([0.6, -2.4, 0])
        self.say("tail")
        self.play(Create(tail_b), FadeIn(tail_l), run_time=0.8)
        self.hold()

        q = VGroup(T("If Northline is slow, why not just ask again?", 30, TICKET),
                   T("Don't we double the work?", 30, TICKET)).arrange(DOWN, buff=0.15).move_to([0.4, -2.6, 0])
        self.say("shyq")
        self.play(FadeOut(tail_l), run_time=0.3)
        self.at_text("If Northline", lead=0.3)
        self.play(FadeIn(q[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("And if we do", lead=0.3)
        self.play(FadeIn(q[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(1.8, pos=(-6.4, -3.5), edge=LEFT)
        self.play(FadeOut(q), run_time=0.4)

        # ================= break it: ask twice, every time =================
        h30 = vline(30, 2.75, -1.15, HEDGE, "", sw=2)
        twice = VGroup(*[hbar(30, 70, ys[i] - 0.0, HEDGE, h=0.06) for i in range(20)])
        for t in twice:
            t.shift(DOWN * 0.07)
        self.say("naive")
        self.play(FadeOut(tail_b), FadeOut(p50), run_time=0.4)
        self.at_text("Send the second", lead=0.3)
        self.play(Create(h30[0]), LaggedStart(*[GrowFromEdge(t, LEFT) for t in twice], lag_ratio=0.05), run_time=1.6)
        lab30 = T("second question at 30 ms", 24, HEDGE).move_to([tx(80), 2.95, 0], aligned_edge=LEFT)
        self.play(FadeIn(lab30), run_time=0.4)
        self.hold()
        cnt = VGroup(T("200 prices:", 30), T("400 calls", 30, BAD), T("twice the load", 30, GREY_A)).arrange(RIGHT, buff=0.3)
        cnt.move_to([0.4, -2.4, 0])
        self.say("naive2")
        self.at_text("For 200", lead=0.3)
        self.play(FadeIn(cnt[:2], shift=UP * 0.1), run_time=0.6)
        self.at_text("Twice", lead=0.3)
        self.play(FadeIn(cnt[2]), run_time=0.5)
        self.hold()
        jk = T("only the calls that are actually late should get a second question", 26, TICKET).move_to([0.4, -3.15, 0])
        fit(jk, 12.4)
        self.say("naive_joke")
        self.at_text("The second", lead=0.3)
        self.play(FadeIn(jk, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the cook and the other branch =================
        cook = person(CLERK, 1.3).move_to([-5.0, 0.6, 0])
        ph = phone(0.9, CLERK).next_to(cook, RIGHT, buff=0.15)
        b1 = shop("branch 1", NL, 1.1).move_to([2.6, 1.9, 0])
        b2 = shop("branch 2", NL, 1.1).move_to([2.6, -0.6, 0])
        same = T("the same shop", 24, NL).next_to(VGroup(b1, b2), RIGHT, buff=0.5)
        t1 = Arrow(ph.get_right(), b1[0].get_left(), buff=0.2, stroke_width=3, color=NL, max_tip_length_to_length_ratio=0.06)
        t2 = Arrow(ph.get_right(), b2[0].get_left(), buff=0.2, stroke_width=3, color=HEDGE, max_tip_length_to_length_ratio=0.06)
        wait = T("no reply in the usual few moments...", 24, GREY_B).next_to(t1, UP, buff=0.1).shift(LEFT * 0.3)
        reply = Arrow(b2[0].get_left(), ph.get_right(), buff=0.25, stroke_width=3, color=OK, max_tip_length_to_length_ratio=0.06)
        reply.shift(DOWN * 0.3)
        nm = T("\"never mind\"", 24, BAD).next_to(b1, LEFT, buff=0.4).shift(UP * 0.55)
        self.say("analogy")
        self.play(FadeIn(cook), FadeIn(ph), FadeIn(b1), FadeIn(b2), FadeIn(same), run_time=0.8)
        self.at_text("She texts a shop", lead=0.3)
        self.play(GrowArrow(t1), run_time=0.6)
        self.at_text("If this one", lead=0.3)
        self.play(FadeIn(wait), run_time=0.5)
        self.at_text("she texts the other", lead=0.3)
        self.play(GrowArrow(t2), run_time=0.6)
        self.at_text("Whichever", lead=0.3)
        self.play(GrowArrow(reply), run_time=0.6)
        self.at_text("never mind", lead=0.3)
        self.play(FadeOut(wait), FadeIn(nm), t1.animate.set_color(BAD), run_time=0.6)
        self.hold()

        def maprow(a, b, ca):
            g = VGroup(T(a, 24, ca), Arrow(LEFT * 0.4, RIGHT * 0.4, stroke_width=3, color=GREY_B, buff=0,
                                           max_tip_length_to_length_ratio=0.3), T(b, 24)).arrange(RIGHT, buff=0.2)
            return g

        mrows = VGroup(maprow("the first text", "the first call", NL),
                       maprow("the few moments", "the hedge time: the demo uses 80 ms", TICKET),
                       maprow("the second text", "the hedge: one more identical call", HEDGE),
                       maprow("take the first answer", "select", OK),
                       maprow("\"never mind\"", "cancel the loser", BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        mrows.move_to([0.3, -2.55, 0])
        fit(mrows, 12.4)
        if mrows.get_bottom()[1] < -3.35:
            mrows.shift(UP * (-3.35 - mrows.get_bottom()[1]))
        self.say("map")
        self.play(VGroup(cook, ph, b1, b2, same, t1, t2, reply, nm).animate.scale(0.7).move_to([0, 1.85, 0]), run_time=0.7)
        for i, key in enumerate(["The first text", "The few moments", "The second text", "Taking the first", "And never mind"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(mrows[i], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.clear()

        # ================= predict, then the slow call rescued =================
        ax = axis(-1.0, [0, 100, 200, 300, 400, 500, 600, 700], 760)
        y1, y2 = 1.3, 0.3
        l1 = T("first call", 26, NL).move_to([tx(0) - 0.3, y1, 0], aligned_edge=RIGHT)
        l2 = T("hedge", 26, HEDGE).move_to([tx(0) - 0.3, y2, 0], aligned_edge=RIGHT)
        ghost = hbar(0, 600, y1, GREY_D, h=0.42, op=0.3)
        ghost_l = T("would take 600", 22, GREY_B).next_to(ghost, RIGHT, buff=0.15)
        self.say("predict")
        self.play(FadeIn(ax), FadeIn(l1), run_time=0.6)
        self.at_text("would take", lead=0.3)
        self.play(FadeIn(ghost), FadeIn(ghost_l), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        tr = ValueTracker(0)
        first = hbar(0, 1, y1, NL, h=0.42, op=0.5).add_updater(lambda m: m.become(hbar(0, max(1, min(tr.get_value(), 600)), y1, NL, h=0.42, op=0.5)))
        m80 = vline(80, 2.0, -0.9, TICKET, "hedge time: 80 ms", size=22)
        m80[1].shift(RIGHT * 0.9)
        self.say("show")
        self.add(first)
        self.play(tr.animate.set_value(80), run_time=1.2, rate_func=linear)
        self.play(Create(m80[0]), FadeIn(m80[1]), run_time=0.5)
        self.at_text("So the hedge", lead=0.3)
        hedge = hbar(80, 81, y2, HEDGE, h=0.42, op=0.5)
        self.play(FadeIn(l2), run_time=0.4)
        tr2 = ValueTracker(80)
        hedge.add_updater(lambda m: m.become(hbar(80, max(81, tr2.get_value()), y2, HEDGE, h=0.42, op=0.5)))
        self.add(hedge)
        self.at_text("It's a normal", lead=0.3)
        self.play(tr.animate.set_value(120), tr2.animate.set_value(120), run_time=1.2, rate_func=linear)
        first.clear_updaters()
        hedge.clear_updaters()
        win = chip_m("wins", OK, 22).next_to(hedge, RIGHT, buff=0.15)
        self.at_text("The hedge wins", lead=0.3)
        self.play(FadeIn(win), hedge.animate.set_stroke(OK, 3), run_time=0.5)
        cut = chip_m("cancelled", BAD, 22).move_to([tx(400), y1, 0])
        self.at_text("and the slow", lead=0.3)
        self.play(first.animate.set_stroke(BAD, 3), ghost.animate.set_opacity(0.08), FadeOut(ghost_l), FadeIn(cut), run_time=0.7)
        self.hold()
        m120 = vline(120, 2.0, -0.9, OK, "", size=24)
        sum_t = VGroup(T("80 of waiting + 40 for the hedge =", 30), T("120 ms", 30, OK), T("instead of 600", 30, GREY_B))
        sum_t.arrange(RIGHT, buff=0.2).move_to([0, -2.3, 0])
        fit(sum_t, 12.4)
        self.say("show2")
        self.play(Create(m120[0]), FadeIn(sum_t, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.clear()

        # ================= the demo, and the cost =================
        out_t = T("HedgeDemo: 200 prices from Northline", 24, GREY_B)
        o1 = M("no hedge        p50  40 ms   p99 600 ms   max 600 ms   calls to Northline: 200", 22)
        o2 = M("hedge at 80 ms  p50  40 ms   p99 120 ms   max 120 ms   calls to Northline: 210", 22, OK)
        og = VGroup(out_t, o1, o2).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, 1.6, 0])
        fit(og, 12.6)
        self.say("demo")
        self.play(FadeIn(out_t), FadeIn(o1), run_time=0.7)
        self.at_text("p50 stays", lead=0.3)
        self.play(FadeIn(o2, shift=UP * 0.1), run_time=0.7)
        self.at_text("p99 falls", lead=0.3)
        L1 = "no hedge        p50  40 ms   p99 600 ms   max 600 ms   calls to Northline: 200"
        L2 = "hedge at 80 ms  p50  40 ms   p99 120 ms   max 120 ms   calls to Northline: 210"
        self.play(Circumscribe(VGroup(o1[span(L1, "p99 600 ms")], o2[span(L2, "p99 120 ms")]), color=OK, buff=0.06), run_time=1.0)
        self.at_text("And the calls", lead=0.3)
        self.play(Circumscribe(VGroup(o1[-3:], o2[-3:]), color=TICKET, buff=0.06), run_time=1.0)
        self.hold()
        cost = VGroup(T("10 extra calls:", 34), T("5% more", 34, TICKET)).arrange(RIGHT, buff=0.3).move_to([0, -0.6, 0])
        why5 = T("only the slow 5% ever got a hedge", 28, GREY_A).next_to(cost, DOWN, buff=0.3)
        ans = T("not double the work: a little, exactly where it hurts", 30, OK).next_to(why5, DOWN, buff=0.5)
        fit(ans, 12.4)
        self.say("cost")
        self.play(FadeIn(cost, shift=UP * 0.1), run_time=0.6)
        self.at_text("because only", lead=0.3)
        self.play(FadeIn(why5), run_time=0.5)
        self.at_text("We don't", lead=0.3)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= name it, then the code =================
        nm1 = T("a hedge", 52, HEDGE).move_to([0, 0.8, 0])
        nm2 = T("like hedging a bet: a small second bet, so one bad outcome can't hurt you much", 28, GREY_A)
        nm2.next_to(nm1, DOWN, buff=0.4)
        fit(nm2, 12.4)
        self.say("name")
        self.play(Write(nm1), run_time=0.9)
        self.at_text("like hedging", lead=0.3)
        self.play(FadeIn(nm2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear(0.5)

        kt = T("Kotlin", 24, GREY_B)
        kc = code_block(["suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T =",
                         "    coroutineScope {",
                         "        val first = async { call() }",
                         "        val early = withTimeoutOrNull(after) { first.await() }",
                         "        if (early != null) return@coroutineScope early",
                         "        val second = async { call() }                // the hedge",
                         "        val winner = select { first.onAwait { it }; second.onAwait { it } }",
                         "        coroutineContext.cancelChildren()            // stop the loser",
                         "        winner",
                         "    }"], 22, hl={"// the hedge": HEDGE, "cancelChildren()": BAD, "// stop the loser": BAD,
                                          "select": OK, "withTimeoutOrNull(after)": TICKET})
        jt = T("Java, with Reactor", 24, GREY_B)
        jc = code_block(["Mono<Quote> hedged(Duration after, Mono<Quote> call) {",
                         "    return Mono.firstWithValue(call, Mono.delay(after).then(call));",
                         "}"], 22, hl={"Mono.firstWithValue": OK, "Mono.delay(after)": TICKET})
        cg = VGroup(VGroup(kt, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                    VGroup(jt, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(cg, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(kt), FadeIn(kc[:2]), run_time=0.6)
        for idx, key in ((2, "start the first"), (3, "Wait for it"), (5, "start the second"), (6, "and select"),
                         (7, "Then cancel")):
            self.at_text(key, lead=0.3)
            extra = [FadeIn(kc[4])] if idx == 5 else []
            self.play(FadeIn(kc[idx], shift=RIGHT * 0.1), *extra, run_time=0.5)
        self.play(FadeIn(kc[8:]), run_time=0.3)
        self.at_text("Java with", lead=0.3)
        self.play(FadeIn(cg[1], shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.say("code_joke")
        self.play(Circumscribe(kc[7], color=BAD, buff=0.06), run_time=1.0)
        self.at_text("It's like", lead=0.3)
        self.play(kc[7].animate.set_opacity(0.25), run_time=0.6)
        self.hold()
        self.play(kc[7].animate.set_opacity(1), run_time=0.3)
        self.clear()

        # ================= guardrails =================
        def card(n, title, color, w=4.0, h=4.3):
            r = RoundedRectangle(corner_radius=0.15, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.08), 1)
            b = VGroup(Circle(radius=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1), T(str(n), 26))
            b[1].move_to(b[0])
            b.move_to(r.get_corner(UL) + RIGHT * 0.42 + DOWN * 0.42)
            t = T(title, 26, color).next_to(b, RIGHT, buff=0.2)
            return VGroup(r, b, t)

        c1 = card(1, "safe to repeat only", FJ)
        c2 = card(2, "only the tail", TICKET)
        c3 = card(3, "its own permit", OK)
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.3).move_to([0, 0.2, 0])
        head = T("a hedge is a duplicate request", 30, HEDGE).move_to([0, 3.0, 0])
        self.say("g1")
        self.play(FadeIn(head), run_time=0.5)
        self.at_text("One.", lead=0.3)
        self.play(FadeIn(c1), run_time=0.6)
        g1a = VGroup(T("Northline, Eastgate:", 22, GREY_A), T("look up a price", 22, GREY_A)).arrange(DOWN, buff=0.06)
        g1a.next_to(c1[1], DOWN, buff=0.3).align_to(c1[1], LEFT)
        v1 = van(FJ, 0.7)
        v2 = van(FJ, 0.7)
        vans = VGroup(v1, v2).arrange(RIGHT, buff=0.2).move_to(c1[0].get_center() + DOWN * 0.55)
        vl = T("Fjord, hedged: two vans", 22, BAD).next_to(vans, DOWN, buff=0.2)
        self.at_text("Northline and", lead=0.3)
        self.play(FadeIn(g1a), run_time=0.5)
        self.at_text("Fjord's price", lead=0.3)
        self.play(FadeIn(v1), run_time=0.5)
        self.at_text("Hedge Fjord", lead=0.3)
        self.play(FadeIn(v2, shift=LEFT * 0.2), FadeIn(vl), run_time=0.6)
        self.hold()

        g2a = VGroup(T("Northline only,", 22, GREY_A), T("at a measured time", 22, GREY_A)).arrange(DOWN, buff=0.06)
        g2a.next_to(c2[1], DOWN, buff=0.3).align_to(c2[1], LEFT)
        g2b = VGroup(T("too early (30 ms):", 22, BAD), T("every request hedged,", 22, GREY_A),
                     T("400 calls", 22, BAD)).arrange(DOWN, buff=0.06).move_to(c2[0].get_center() + DOWN * 0.8)
        self.say("g2")
        self.play(FadeIn(c2), run_time=0.6)
        self.at_text("Hedge only", lead=0.3)
        self.play(FadeIn(g2a), run_time=0.5)
        self.at_text("Too early", lead=0.3)
        self.play(FadeIn(g2b), run_time=0.6)
        self.hold()

        toks = VGroup(*[token(OK, 0.12) for _ in range(10)]).arrange_in_grid(2, 5, buff=0.12)
        jar = SurroundingRectangle(toks, buff=0.15, corner_radius=0.08).set_stroke(GREY_B, 2)
        permit = VGroup(jar, toks).move_to(c3[0].get_center() + UP * 0.35)
        pl = VGroup(T("Northline:", 22, GREY_A), T("10 calls at a time", 22, GREY_A)).arrange(DOWN, buff=0.06)
        pl.next_to(permit, DOWN, buff=0.15)
        hchip = chip_m("hedge", HEDGE, 22).next_to(pl, DOWN, buff=0.3)
        self.say("g3")
        self.play(FadeIn(c3), run_time=0.6)
        self.at_text("a token from", lead=0.3)
        self.play(FadeIn(permit), FadeIn(pl), run_time=0.6)
        self.play(FadeIn(hchip), run_time=0.4)
        self.at_text("And here", lead=0.3)
        brk = T("the picture breaks: the other branch has its own staff; our hedge goes to the same Northline", 24, TICKET)
        fit(brk, 12.4).move_to([0, -2.6, 0])
        self.play(FadeIn(brk), run_time=0.6)
        self.hold()
        busy = T("swamped: no permit free, so the hedge waits; the first call usually wins", 24, GREY_A)
        fit(busy, 12.4).move_to([0, -3.2, 0])
        self.say("g3b")
        self.play(*[t.animate.set_fill(GREY_D, 1).set_stroke(GREY_D) for t in toks], run_time=0.8)
        self.at_text("So under", lead=0.3)
        self.play(FadeIn(busy), Wiggle(hchip), run_time=0.8)
        self.hold()
        self.clear()

        # ================= moral and check =================
        mq = T("Is a second question cheating?", 34, TICKET).move_to([0, 2.8, 0])
        m1 = T("not if it goes only to the slow tail", 30).next_to(mq, DOWN, buff=0.25)
        steps = VGroup(*[T(s, 25, c) for s, c in (("wait the usual time", TICKET), ("ask once more", HEDGE),
                                                  ("take the first answer", OK), ("cancel the other", BAD))])
        steps.arrange(RIGHT, buff=0.75).move_to([0, 0.9, 0])
        fit(steps, 12.4)
        arrs = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.08, stroke_width=2.5, color=GREY_B,
                              max_tip_length_to_length_ratio=0.3) for i in range(3)])
        rule = T("Spend a duplicate on the slow tail, and only where a duplicate is harmless.", 28, HEDGE).move_to([0, -0.1, 0])
        fit(rule, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at_text("Not if", lead=0.3)
        self.play(FadeIn(m1), run_time=0.5)
        self.at_text("Wait until", lead=0.3)
        self.play(LaggedStart(*[FadeIn(s) for s in steps], *[GrowArrow(a) for a in arrs], lag_ratio=0.25), run_time=2.2)
        self.at_text("Spend it", lead=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qa = T("Check: you hedge Fjord instead of Northline. What goes wrong?", 28, YELLOW_M).move_to([0, -1.3, 0])
        fit(qa, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(VGroup(van(FJ, 0.55), van(FJ, 0.55)).arrange(RIGHT, buff=0.15),
                     T("a second van seat per hedge: a booking is asked exactly once", 26, OK)).arrange(RIGHT, buff=0.35)
        fit(ans, 12.4).move_to([0, -2.5, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
