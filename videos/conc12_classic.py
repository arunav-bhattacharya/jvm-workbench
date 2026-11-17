from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bBlockingQueue\b", "blocking queue"), (r"===", "triple equals"), (r"==", "double equals"),
    (r"\bPILL\b", "pill"), (r"\bWAITING\b", "waiting"),
]

# every spoken line, in order
N = {
    "open": "Back to the kitchen. Waiters clip tickets to the rail, and cooks take them off. In code, each waiter "
            "and each cook is a thread, a path of work running beside the others, and the rail is a queue.",
    "names": "A thread that puts work in is a producer. A thread that takes work out is a consumer. "
             "One side makes work at one speed, the other does it at another. Most programs have this shape somewhere.",
    "bounded": "Java's rail is a BlockingQueue. put adds a ticket, and take removes one, waiting while the rail is empty. "
               "Give it a limit, here room for four. When the rail is full, put waits too, so a fast waiter slows "
               "to the cooks' pace, instead of piling up tickets until memory runs out. That push back is called backpressure.",
    "close": "Now it's closing time. The waiters have stopped, a few tickets are left, and three cooks work through them. "
             "Then the rail is empty, and each cook waits for the next ticket. Tonight, there won't be one.",
    "shy": "So here's a question that sounds too simple to ask. Why can't a cook just see the empty rail, and go home?",
    "late": "Because empty doesn't mean over. It can also mean the next ticket is late. And a cook waiting in take "
            "is asleep on the bench, like in the wait and notify lesson. Only a put rings its bell, "
            "and once the waiters have gone home, nobody ever will.",
    "interrupt": "The quickest fix is to interrupt every cook: stop, right now. It's fast. But take checks for the "
                 "interrupt before it looks at the rail, so the cooks leave with tickets still clipped up. "
                 "Three cooks go home, and table 12 is still waiting for its soup.",
    "poll": "Or each cook could check every second: anything yet, and should I stop? That works, but a cook may wait "
            "a whole second to notice, and every loop must check the flag just right.",
    "pill": "The clean answer is a card on the rail that says: kitchen closed. It's called a poison pill, "
            "a special item that means no more work. A cook that takes it stops.",
    "pred1": "The head chef waits until both waiters are done, then clips one card to the rail. Three cooks. What happens?",
    "show1": "One cook takes the card and goes home. The card was just an item, and now it's gone. "
             "The other two find an empty rail, and wait. In the demo, a second later, two cooks were still WAITING "
             "inside take. And whatever waits for them, like the program's shutdown, hangs too.",
    "fix": "So, one card per cook. Three cooks, three cards, and each cook stops at its own. "
           "The demo's cooks handled 511, 177 and 1,312 orders. That's 2,000, every order the waiters put, "
           "and nobody was left waiting.",
    "rules": "Three rules make pills work. One: put them only after every producer is done, "
             "so they land behind every real ticket. Two: one pill per consumer, because each pill is taken once.",
    "identity": "Three: recognize the pill by identity, with == in Java and === in Kotlin, not by what it says. "
                "A real ticket that happens to read PILL is still a ticket. Somebody ordered the pill special. Cook it.",
    "classics": "The lesson has two more classics, and you've met both. Five philosophers at a round table each pick up "
                "the fork on their left, and wait for the one on their right. That's Ana and Ben's circle, with five people. "
                "In the demo they ate 0 of 1,000 meals, and with the same cure, one lock order, all 1,000. "
                "And readers who keep a price board busy can starve the owner who wants to change it.",
    "code": "Here are the pills in code, Java on the left and Kotlin on the right. Each cook takes tickets until it "
            "gets its pill. The head chef puts one pill per cook, after the last waiter is done.",
    "moral": "So, why can't a cook go home when the rail is empty? Because empty might only mean late. "
             "Send the end of work down the rail itself: one pill per consumer, after the last producer, "
             "recognized by identity.",
    "check": "Quick check. The head chef puts the three pills on the rail while one waiter is still clipping tickets. "
             "What goes wrong?",
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

    def predict(self, secs=2.4):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, -3.2, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# one colour per thing, for the whole video (cooks and waiters as in the kitchen of wait and notify)
CCOL = [BLUE_M, TEAL_M, GREEN_M]
WCOL = [PURPLE_M, "#E88AB8"]
PILLC, BELL, BAD, GOOD = RED_M, YELLOW_M, RED_M, GREEN_M

RAIL_Y = 1.95
SLOTS = [np.array([x, 1.42, 0]) for x in (-1.65, -0.55, 0.55, 1.65)]   # left to right; cooks take from the right
WPOS = [np.array([-5.15, 2.0, 0]), np.array([-5.15, 0.9, 0])]
CPOS = [np.array([5.2, 2.45, 0]), np.array([5.2, 1.5, 0]), np.array([5.2, 0.55, 0])]
SEATS = [np.array([x, -0.95, 0]) for x in (-1.9, 0.0, 1.9)]
BENCH_Y = -1.45
NOTE_Y = [-2.35, -2.85, -3.35]


def ticket(n, color=WHITE):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55, stroke_color=color, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    return VGroup(r, M(f"#{n}", 22, color).move_to(r), clip).set_z_index(4)


def pill():
    r = RoundedRectangle(corner_radius=0.05, width=0.9, height=0.55, stroke_color=PILLC, stroke_width=3)
    r.set_fill(dim(PILLC, 0.3), 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    return VGroup(r, M("closed", 20, PILLC).move_to(r), clip).set_z_index(4)


def tch(text, color):
    return chip(text, color, size=24).set_z_index(5)


def bell_icon():
    body = VMobject(stroke_color=BELL, stroke_width=4).set_fill(dim(BELL, 0.3), 1)
    body.set_points_smoothly([[-0.42, -0.3, 0], [-0.32, 0.05, 0], [-0.2, 0.32, 0], [0, 0.4, 0], [0.2, 0.32, 0],
                              [0.32, 0.05, 0], [0.42, -0.3, 0]])
    body.add_line_to(np.array([-0.42, -0.3, 0]))
    knob = Dot([0, 0.47, 0], radius=0.07, color=BELL)
    clap = Dot([0, -0.4, 0], radius=0.08, color=BELL)
    return VGroup(body, knob, clap).scale(0.6)


def note(i, *parts):
    g = VGroup(*parts).arrange(RIGHT, buff=0.25)
    return g.move_to([-6.2, NOTE_Y[i], 0], aligned_edge=LEFT)


class Conc12Classic(Narrated):
    """conc-12, section 0: the kitchen at closing time. Producers and consumers around a BlockingQueue; a bounded rail
    gives backpressure. An empty rail can't tell over from late, and a cook in take() sleeps on the bench until a put.
    Interrupting drops queued tickets; polling is slow; a poison pill is the clean answer. One pill: one cook goes home,
    two wait in take() forever. One per cook (511 + 177 + 1,312 = 2,000). The three rules, identity (a ticket that
    reads PILL is still a ticket), the other two classics as callbacks, the code, the moral and a check."""

    def construct(self):
        self.title_card("Closing the kitchen", "producers, consumers, and one poison pill per cook")

        rail = Line([-2.35, RAIL_Y, 0], [2.35, RAIL_Y, 0]).set_stroke(GREY_A, 6)
        rail_l = T("the rail: a queue", 24, GREY_A).next_to(rail, UP, buff=0.18)
        waiters = [tch(f"waiter {i}", c).move_to(p) for i, (c, p) in enumerate(zip(WCOL, WPOS))]
        cooks = [tch(f"cook {i}", c).move_to(p) for i, (c, p) in enumerate(zip(CCOL, CPOS))]

        on_rail = []                      # tickets on the rail, left to right in arrival order

        def place():
            """Where each ticket on the rail sits: the oldest at the right, nearest the cooks."""
            k = len(on_rail)
            return [SLOTS[3 - (k - 1 - j)] for j in range(k)]

        def put(t, src, rt=0.6):
            t.move_to(src.get_right() + RIGHT * 0.55)
            self.add(t)
            on_rail.insert(0, t)
            pos = place()
            self.play(*[m.animate.move_to(p) for m, p in zip(on_rail, pos)], run_time=rt)

        def take(cook, rt=0.6, keep=False):
            t = on_rail.pop()
            self.play(t.animate.move_to(cook.get_left() + LEFT * 0.55), run_time=rt)
            if not keep:
                self.play(FadeOut(t, scale=0.6), run_time=0.25)
            return t

        # ================= the kitchen =================
        self.say("open")
        self.play(Create(rail), FadeIn(rail_l), run_time=0.8)
        self.play(*[FadeIn(w, shift=RIGHT * 0.2) for w in waiters], *[FadeIn(c, shift=LEFT * 0.2) for c in cooks],
                  run_time=0.7)
        self.at(2)
        self.play(*[Indicate(m[1], color=m[0].get_stroke_color()) for m in waiters + cooks], run_time=0.8)
        put(ticket(1), waiters[0])
        take(cooks[0])
        self.hold()

        prod = T("producers", 26, WCOL[0]).move_to(WPOS[0] + UP * 0.85)
        cons = T("consumers", 26, CCOL[0]).move_to(CPOS[0] + UP * 0.7)
        self.say("names")
        self.play(FadeIn(prod, shift=DOWN * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cons, shift=DOWN * 0.1), run_time=0.5)
        self.hold()

        bq = M("BlockingQueue", 24, GREY_A).next_to(rail, UP, buff=0.18)
        put_l = M("put", 24, WCOL[0]).move_to([-3.1, RAIL_Y + 0.75, 0])
        take_l = M("take", 24, CCOL[0]).move_to([3.15, RAIL_Y + 0.75, 0])
        cap = T("room for 4", 22, GREY_B).next_to(rail, DOWN, buff=0.95)
        self.say("bounded")
        self.play(Transform(rail_l, bq), FadeIn(put_l), FadeIn(take_l), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cap), run_time=0.4)
        for n in range(2, 6):
            put(ticket(n), waiters[n % 2], rt=0.4)
        self.at(3)
        extra = ticket(6).move_to(waiters[0].get_right() + RIGHT * 0.6)
        wait_l = T("put waits: rail full", 22, BAD).next_to(extra, DOWN, buff=0.15)
        self.play(FadeIn(extra), FadeIn(wait_l), run_time=0.5)
        self.play(Wiggle(extra), run_time=0.7)
        self.at_text("That push back", lead=0.6)
        take(cooks[1], rt=0.5)
        on_rail.insert(0, extra)
        self.play(FadeOut(wait_l), *[m.animate.move_to(p) for m, p in zip(on_rail, place())], run_time=0.6)
        bp = T("backpressure", 28, YELLOW_M).move_to([0, -0.15, 0])
        self.play(FadeIn(bp, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ================= closing time =================
        bench = VGroup(RoundedRectangle(corner_radius=0.08, width=6.4, height=0.22).set_fill(GREY_D, 1)
                       .set_stroke(GREY_B, 2).move_to([0, BENCH_Y, 0]),
                       *[Line([x, BENCH_Y - 0.11, 0], [x, BENCH_Y - 0.45, 0]).set_stroke(GREY_B, 3) for x in (-2.8, 2.8)])
        bench_l = T("the bench", 22, GREY_B).next_to(bench, LEFT, buff=0.3)
        self.say("close")
        self.play(FadeOut(bp), FadeOut(cap), run_time=0.3)
        self.at_text("The waiters", lead=0.3)
        self.play(*[w.animate.set_opacity(0.25) for w in waiters], prod.animate.set_opacity(0.25),
                  FadeOut(put_l), run_time=0.6)
        while len(on_rail) > 1:
            take(cooks[len(on_rail) % 3], rt=0.4)
        take(cooks[0], rt=0.4)
        self.at(1)
        self.play(FadeIn(bench), FadeIn(bench_l), run_time=0.5)
        self.play(*[c.animate.move_to(s) for c, s in zip(cooks, SEATS)], run_time=0.9)
        wt = M("waiting in take()", 22, GREY_B).next_to(bench, DOWN, buff=0.55)
        self.play(FadeIn(wt), run_time=0.4)
        self.at(2)
        self.play(Indicate(rail, color=WHITE), run_time=0.8)
        self.hold()

        q = T("Why can't a cook just see the empty rail, and go home?", 30, YELLOW_M).move_to([0, -3.0, 0])
        self.say("shy")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()

        late_t = ticket("?", GREY_B).move_to([-3.4, 0.45, 0]).set_opacity(0.5)
        late_l = T("late, or never?", 22, GREY_B).next_to(late_t, DOWN, buff=0.15)
        bell = bell_icon().move_to([3.6, -0.3, 0])
        self.say("late")
        self.play(FadeOut(q), run_time=0.3)
        self.at(1)
        self.play(FadeIn(late_t), FadeIn(late_l), run_time=0.6)
        self.at(2)
        self.play(Indicate(bench, color=WHITE), run_time=0.8)
        self.at(3)
        self.play(FadeIn(bell), run_time=0.4)
        self.play(Wiggle(bell, rotation_angle=0.05 * TAU), run_time=0.6)
        self.play(bell.animate.set_opacity(0.25), run_time=0.6)
        self.hold()

        # ================= three ways out =================
        self.play(FadeOut(VGroup(late_t, late_l, bell, wt)), *[c.animate.move_to(p) for c, p in zip(cooks, CPOS)],
                  run_time=0.6)
        left = [ticket(n) for n in (7, 8, 9)]
        for t in left:
            put(t, waiters[1], rt=0.3)
        zap = VGroup(*[T("stop!", 24, BAD).next_to(p, LEFT, buff=1.05) for p in CPOS[:1]])
        t12 = T("table 12 is still waiting for its soup", 24, BAD).move_to([0, -0.15, 0])
        self.say("interrupt")
        self.at_text("stop, right now", lead=0.3)
        self.play(*[Flash(c.get_left(), color=BAD, flash_radius=0.35) for c in cooks], FadeIn(zap), run_time=0.7)
        self.at(2)
        self.play(*[c.animate.shift(RIGHT * 0.3).set_opacity(0.2) for c in cooks], FadeOut(zap), run_time=0.7)
        self.play(*[Indicate(t, color=BAD) for t in on_rail], run_time=0.8)
        self.at(3)
        self.play(FadeIn(t12, shift=UP * 0.1), run_time=0.6)
        self.hold()

        clock = VGroup(Circle(radius=0.22).set_stroke(GREY_B, 2.5), Line(ORIGIN, UP * 0.15).set_stroke(GREY_B, 2.5),
                       Line(ORIGIN, RIGHT * 0.12).set_stroke(GREY_B, 2.5))
        clocks = VGroup(*[clock.copy().move_to(p + LEFT * 1.15) for p in CPOS])
        poll_l = M("poll(1, SECONDS)", 22, GREY_B).move_to([3.2, -0.15, 0])
        self.say("poll")
        self.play(FadeOut(t12), *[c.animate.shift(LEFT * 0.3).set_opacity(1) for c in cooks], run_time=0.5)
        self.play(FadeIn(clocks), FadeIn(poll_l), run_time=0.5)
        self.play(*[Rotate(c[1], -TAU, about_point=c[0].get_center()) for c in clocks], run_time=1.2)
        self.at(1)
        self.play(*[Rotate(c[1], -TAU, about_point=c[0].get_center()) for c in clocks], run_time=1.2)
        self.hold()

        pl = pill().move_to([0, -0.2, 0]).scale(1.5)
        pl_l = T("poison pill: no more work", 24, PILLC).next_to(pl, DOWN, buff=0.2)
        self.say("pill")
        self.play(FadeOut(clocks), FadeOut(poll_l), run_time=0.4)
        self.play(FadeIn(pl, scale=0.7), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pl_l), run_time=0.5)
        self.hold()

        # ================= one pill for three cooks =================
        self.say("pred1")
        self.play(FadeOut(pl_l), run_time=0.3)
        for t in list(on_rail):
            take(cooks[len(on_rail) % 3], rt=0.35)
        self.play(FadeOut(pl), run_time=0.3)
        p1 = pill()
        put(p1, waiters[0], rt=0.6)
        self.at(1)
        self.play(Indicate(on_rail[0], color=PILLC), run_time=0.7)
        self.hold(after=0)
        self.predict()

        out1 = note(0, M("cook-1 got its pill after 1004 orders", 22, GREY_A))
        out2 = note(1, M("cooks still waiting: 2 (WAITING in take)", 22, BAD))
        self.say("show1")
        take(cooks[1], rt=0.5, keep=True)
        self.play(FadeOut(p1), cooks[1].animate.shift(RIGHT * 0.3).set_opacity(0.2), FadeIn(out1), run_time=0.6)
        self.at(2)
        self.play(cooks[0].animate.move_to(SEATS[0]), cooks[2].animate.move_to(SEATS[2]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(out2), run_time=0.5)
        self.at(4)
        sd = T("shutdown: hangs", 22, BAD).move_to([3.4, -0.15, 0])
        self.play(FadeIn(sd), run_time=0.5)
        self.hold()

        # ================= one pill per cook =================
        self.play(FadeOut(VGroup(out1, out2, sd)), *[c.animate.move_to(p).set_opacity(1) for c, p in zip(cooks, CPOS)],
                  run_time=0.7)
        pills = [pill() for _ in range(3)]
        outs = [note(0, M("cook-1 got its pill after 511 orders", 22, GREY_A)),
                note(1, M("cook-2 got its pill after 177 orders", 22, GREY_A)),
                note(2, M("cook-0 got its pill after 1312 orders", 22, GREY_A))]
        tot = VGroup(T("511 + 177 + 1,312 = 2,000", 24, GOOD), T("still waiting: 0", 24, GOOD)).arrange(DOWN, buff=0.15)
        tot.move_to([3.6, -2.85, 0])
        self.say("fix")
        put(ticket(10), waiters[0], rt=0.35)
        for p in pills:
            put(p, waiters[1], rt=0.35)
        self.at(1)
        take(cooks[0], rt=0.35)
        for ci, o in zip((1, 2, 0), outs):
            t = take(cooks[ci], rt=0.4, keep=True)
            self.play(FadeOut(t), cooks[ci].animate.set_opacity(0.25), FadeIn(o), run_time=0.45)
        self.at(2)
        self.play(FadeIn(tot[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(tot[1]), run_time=0.5)
        self.hold()

        # ================= the three rules =================
        r1 = T("1. Pills go in after every producer is done.", 26)
        r2 = T("2. One pill per consumer.", 26)
        r3 = T("3. Recognize the pill by identity, not by what it says.", 26)
        rules = VGroup(r1, r2, r3).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, -2.55, 0])
        fit(rules, 12.4)
        self.say("rules")
        self.play(FadeOut(VGroup(*outs, tot, bench, bench_l)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        fake = ticket("PILL").scale(1.3).move_to([-1.3, -0.15, 0])
        real = pill().scale(1.3).move_to([1.3, -0.15, 0])
        eq = M("ticket == PILL ?", 24, GREY_A).move_to([0, 0.75, 0])
        no = VGroup(tick(False, 0.14), T("not the pill: cook it", 22, GOOD)).arrange(RIGHT, buff=0.15).next_to(fake, DOWN, buff=0.2)
        yes = VGroup(tick(True, 0.16), T("the pill", 22, PILLC)).arrange(RIGHT, buff=0.15).next_to(real, DOWN, buff=0.2)
        self.say("identity")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(fake), FadeIn(real), FadeIn(eq), run_time=0.6)
        self.at(1)
        self.play(FadeIn(no), FadeIn(yes), run_time=0.6)
        self.at(2)
        self.play(Wiggle(fake), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the other two classics =================
        TC = np.array([-3.3, 0.4, 0])
        table = Circle(radius=1.15).set_stroke(GREY_A, 3).set_fill(dim(GREY_B, 0.12), 1).move_to(TC)
        phils = VGroup(*[Dot(radius=0.2, color=TEAL_M).move_to(on_circle(TC, 1.65, 90 + 72 * k)) for k in range(5)])
        forks = VGroup(*[Line(on_circle(TC, 0.7, 90 + 72 * k + 36), on_circle(TC, 1.05, 90 + 72 * k + 36))
                         .set_stroke(GREY_A, 4) for k in range(5)])
        circ = VGroup(*[CurvedArrow(on_circle(TC, 2.05, 90 + 72 * k + 8), on_circle(TC, 2.05, 90 + 72 * k + 64),
                                    angle=-0.5, color=BAD, stroke_width=3) for k in range(5)])
        meals0 = VGroup(T("0 of 1,000 meals", 24, BAD), T("one lock order: 1,000", 24, GOOD)).arrange(DOWN, buff=0.15)
        meals0.next_to(table, DOWN, buff=1.0)
        ab = T("Ana and Ben's circle, five people", 24, BAD).next_to(table, UP, buff=1.15)
        bd = VGroup(RoundedRectangle(corner_radius=0.1, width=2.4, height=1.6).set_stroke(GREY_A, 3)
                    .set_fill(dim(GREY_B, 0.1), 1), T("prices", 24, GREY_A)).move_to([3.4, 1.0, 0])
        rdrs = VGroup(*[Dot(radius=0.15, color=TEAL_M) for _ in range(4)]).arrange(RIGHT, buff=0.3).next_to(bd, DOWN, buff=0.3)
        ownr = Dot(radius=0.17, color=GOLD_M).move_to([5.6, 1.0, 0])
        ow_l = T("owner waits", 22, GOLD_M).next_to(ownr, DOWN, buff=0.15)
        self.say("classics")
        self.at(1)
        self.play(FadeIn(table), FadeIn(phils), FadeIn(forks), run_time=0.8)
        self.at(2)
        self.play(Create(circ), FadeIn(ab), run_time=1.0)
        self.at(3)
        self.play(FadeIn(meals0[0]), run_time=0.5)
        self.at_text("with the same cure", lead=0.3)
        self.play(FadeIn(meals0[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(bd), FadeIn(rdrs), run_time=0.6)
        self.play(FadeIn(ownr), FadeIn(ow_l), run_time=0.5)
        self.play(Wiggle(ownr), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"t == PILL": PILLC, "t === PILL": PILLC, "rail.put(PILL)": PILLC}
        jsrc = ["// each cook", "while (true) {", "    String t = rail.take();", "    if (t == PILL) break;",
                "    cook(t);", "}", "", "// head chef, after the last waiter", "for (int i = 0; i < cooks; i++)",
                "    rail.put(PILL);"]
        ksrc = ["// each cook", "while (true) {", "    val t = rail.take()", "    if (t === PILL) break",
                "    cook(t)", "}", "", "// head chef, after the last waiter", "repeat(cooks) {",
                "    rail.put(PILL)", "}"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        for c in (jc[0], jc[7], kc[0], kc[7]):
            c.set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=1.2, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.1)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[2:4], kc[2:4]), color=PILLC, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[8:10], kc[8:11]), color=PILLC, scale_factor=1.04), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Why not go home at the empty rail? Empty might only mean late.", 30, YELLOW_M)
        m1 = T("Send the end of work down the rail itself:", 30)
        m2 = T("one pill per consumer, after the last producer, recognized by identity.", 30)
        moral = VGroup(mq, m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 1.4)
        fit(moral, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("the head chef puts the three pills on the rail", 28),
                    T("while one waiter is still clipping tickets. What goes wrong?", 28)).arrange(DOWN, buff=0.18)
        qq.move_to(DOWN * 1.9)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at_text("one pill per", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
