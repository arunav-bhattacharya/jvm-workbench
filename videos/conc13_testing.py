from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bjcstress\b", "J C stress"), (r"(\d)\.00\b", r"\1"), (r"\bcountDown\b", "count down"),
]

# every spoken line, in order
N = {
    "open": "Picture the refund desk at a shop. A customer brings something back and gets money back, sometimes in "
            "several parts. The rule: the refunds for one sale must never add up to more than the sale.",
    "test": "The shop's program handles refunds on several threads. So the team wrote a test: two threads ask for "
            "refunds at once, and the total must stay within the sale. It has passed every day for a year.",
    "coat": "Then, on the first busy day of a sale, a coat that sold for 100.00 is refunded 160.00. "
            "The customer is delighted. The shop is not.",
    "shy": "So here's the question we're shy to ask. Was the test lying? And if it wasn't, what is a passing test worth?",
    "never": "The test wasn't lying. Its two threads never met. A small test like this takes a few microseconds, "
             "about as long as starting a thread, so the first thread is often done before the second one starts. "
             "As the race lesson put it, a race is shy around small numbers.",
    "quiet": "It's like testing the refund desk on a quiet Tuesday. One customer at a time, and the clerk never "
             "gets confused. The bug needs the first morning of the sale.",
    "rush": "So let's build that morning. A crowd waits outside, and at nine the doors open, and everyone rushes in "
            "at once. That's the start latch from the synchronizers lesson, a latch of 1. "
            "Every thread waits in await, and one countDown lets them all in together.",
    "map": "Three more habits. More customers than clerks: more threads than cores, the parts of the processor that "
           "each run one thread, so the system must switch between them. Each customer brings many returns: "
           "many operations per thread, so they overlap for a long time. And many sale days: many rounds, "
           "each with fresh state.",
    "inv": "At closing time, the till must balance. That's the invariant, a fact that must hold whatever the timing. "
           "Check it after every thread has finished, and never check how long something took.",
    "pred": "The lesson ran the usual test twenty times: two threads, a thousand hits each, no start line. "
            "Then the stress test twenty times: eight threads, a hundred thousand hits each, and a start latch. "
            "Same counter, same bug. How many runs fail?",
    "show": "The usual test failed once in twenty. The stress test failed all twenty. "
            "And in another run, the usual test never failed at all.",
    "refund": "Now the refund desk, under stress. Eight threads each try 2,000 one-cent refunds against a sale "
              "of 10,000 cents. A correct ledger approves exactly 10,000. The racy one approved 16,000. "
              "That's our coat: 160.00 back on a 100.00 sale.",
    "guard": "Two more rules. Give every concurrency test a timeout, so a deadlock fails in seconds instead of "
             "hanging the whole test run for an hour. And read a pass for what it is: not found this time. Never: can't happen.",
    "sleep": "Tests also love a nap. Hand some work to a background thread, sleep a little, then check. "
             "In the lesson, eight busy threads kept every core working, like a build server on a busy afternoon. "
             "The work took about 2 milliseconds, and the test slept 3. How often did it fail?",
    "sleep2": "45 times out of 100. A nap half as long again as the work was a coin toss. "
              "The latch version waits for the event itself, with 5 seconds only as a deadline: "
              "zero failures, and as fast as the work allows.",
    "jcs": "Some races need millions of tries. jcstress, a Java tool from the people who build Java, runs a tiny test "
           "millions of times and counts every outcome. Two actors bump one refund counter and keep what they saw. "
           "1 and 2, or 2 and 1, is fine. 1 and 1 means a refund was lost.",
    "jcs2": "In one run of almost two billion samples, 1 and 1 came up 36 percent of the time. "
            "Mark an outcome forbidden, and a single sighting fails the test.",
    "code": "The lab packs the habits into a small helper called Stress. Java on the left, Kotlin on the right. "
            "Rounds, threads and hits. A setup for fresh state. The actor every thread runs. And the invariant.",
    "moral": "So, what is a passing test worth? Only as much as the collisions it forced. "
             "Open the doors at nine, crowd the desk, run it for many days, and balance the till. "
             "And when it passes, read it as: not found this time.",
    "check": "Quick check. A test starts two threads, each makes one refund, and it has never failed. "
             "Is the ledger safe?",
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

    def clear(self, rt=0.6):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


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


# one colour per thing, for the whole video
TA, TB = TEAL_M, PURPLE_M                    # the two test threads
CROWD = [TEAL_M, PURPLE_M, BLUE_M, "#F28FB0"] * 2
MONEY, LIMIT, BAD, GOOD, COUNT = GOLD_M, RED_M, RED_M, GREEN_M, GOLD_M

# the refund meter
MX0, MU, MY = -4.6, 0.055, -1.75             # x of 0.00, units per 1.00, y


def mx(v):
    return MX0 + MU * v


def meter_bar(v, color=MONEY):
    return Rectangle(width=max(0.01, MU * v), height=0.38).set_stroke(width=0).set_fill(color, 0.9).move_to(
        [mx(v / 2), MY, 0])


def squares(n_bad, n, cols, side=0.24, gap=0.08, seed=3):
    rng = np.random.default_rng(seed)
    bad = set(rng.choice(n, n_bad, replace=False).tolist()) if n_bad else set()
    g = VGroup(*[Square(side).set_stroke(width=0).set_fill(BAD if k in bad else GOOD, 0.9) for k in range(n)])
    return g.arrange_in_grid(n // cols, cols, buff=gap)


class Conc13Testing(Narrated):
    """conc-13, section 0: the refund desk whose test passed for a year while a coat sold for 100.00 was refunded
    160.00. Its two threads never met. The first morning of the sale: a start latch is the doors at nine (the gate with
    a counter from the synchronizers lesson), more threads than cores, many operations, many rounds, an invariant.
    1 of 20 vs 20 of 20; the refund ledger approves 16,000 of 10,000 cents. Timeouts, and what a pass means. Sleep
    vs latch (45 of 100 vs 0), jcstress counting outcomes (1, 1 in 36%), the Stress helper, the moral and a check."""

    def construct(self):
        self.title_card("Make them collide", "a test that passes is only as good as the collisions it forced")

        # ================= the refund desk =================
        sale = VGroup(RoundedRectangle(corner_radius=0.1, width=3.2, height=1.1, stroke_color=GREY_A, stroke_width=3)
                      .set_fill(dim(GREY_B, 0.12), 1),
                      VGroup(T("a coat", 28), T("sold for 100.00", 24, GREY_A)).arrange(DOWN, buff=0.12))
        sale[1].move_to(sale[0])
        sale.move_to([-4.3, 1.9, 0])
        track = Line([mx(0), MY, 0], [mx(175), MY, 0]).set_stroke(GREY_D, 14)
        m_lab = T("refunded so far", 24, MONEY).move_to([mx(0), MY + 0.55, 0], aligned_edge=LEFT)
        lim = DashedLine([mx(100), MY - 0.5, 0], [mx(100), MY + 0.5, 0], dash_length=0.08).set_stroke(LIMIT, 3)
        lim_l = T("the sale: 100.00", 22, LIMIT).next_to(lim, DOWN, buff=0.12)
        rule = T("Refunds for one sale must never add up to more than the sale.", 26).move_to([0, -3.15, 0])
        self.say("open")
        self.play(FadeIn(sale, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(track), FadeIn(m_lab), run_time=0.6)
        bar = [meter_bar(0.01)]
        for v in (30, 55):
            nb = meter_bar(v)
            self.play(Transform(bar[0], nb), run_time=0.5)
        self.at(2)
        self.play(Create(lim), FadeIn(lim_l), FadeIn(rule), run_time=0.8)
        self.hold()

        ta = chip("thread A", TA, size=24).move_to([1.2, 2.2, 0])
        tb = chip("thread B", TB, size=24).move_to([1.2, 1.3, 0])
        test = T("the test", 24, GREY_B).next_to(VGroup(ta, tb), UP, buff=0.2)
        ok = VGroup(tick(True, 0.2), T("passed every day for a year", 24, GOOD)).arrange(RIGHT, buff=0.2)
        ok.next_to(VGroup(ta, tb), RIGHT, buff=0.5)
        self.say("test")
        self.play(Transform(bar[0], meter_bar(0.01)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(test), FadeIn(ta), FadeIn(tb), run_time=0.6)
        self.play(Transform(bar[0], meter_bar(40)), Indicate(ta, color=TA), run_time=0.6)
        self.play(Transform(bar[0], meter_bar(70)), Indicate(tb, color=TB), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ok, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        over = T("refunded 160.00", 26, BAD).move_to([mx(160), MY + 0.55, 0])
        self.say("coat")
        self.play(Transform(bar[0], meter_bar(160, BAD)), run_time=1.0)
        self.play(FadeIn(over), Indicate(lim, color=LIMIT), run_time=0.6)
        self.at(1)
        self.play(Wiggle(over), run_time=0.8)
        self.hold()

        q1 = T("Was the test lying?", 32, YELLOW_M)
        q2 = T("And if it wasn't, what is a passing test worth?", 30)
        qs = VGroup(q1, q2).arrange(DOWN, buff=0.25).move_to([0, 0.15, 0])
        self.say("shy")
        self.play(FadeOut(VGroup(ta, tb, test, ok)), FadeOut(sale), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the threads never met =================
        LX0 = -4.2
        lanes = VGroup(*[Line([LX0, y, 0], [5.6, y, 0]).set_stroke(GREY_D, 2) for y in (1.4, 0.2)])
        la = chip("thread A", TA, size=24).next_to(lanes[0], LEFT, buff=0.25)
        lb = chip("thread B", TB, size=24).next_to(lanes[1], LEFT, buff=0.25)
        wa = Rectangle(width=2.4, height=0.36).set_stroke(width=0).set_fill(TA, 0.9).move_to([LX0 + 1.2, 1.4, 0])
        sb = DashedLine([LX0, 0.2, 0], [LX0 + 2.7, 0.2, 0], dash_length=0.1).set_stroke(GREY_B, 3)
        sb_l = T("starting up", 22, GREY_B).next_to(sb, DOWN, buff=0.15)
        wb = Rectangle(width=2.4, height=0.36).set_stroke(width=0).set_fill(TB, 0.9).move_to([LX0 + 2.75 + 1.2, 0.2, 0])
        done = T("done", 22, TA).next_to(wa, UP, buff=0.12)
        gap = DashedLine([LX0 + 2.45, 1.8, 0], [LX0 + 2.45, -0.2, 0], dash_length=0.08).set_stroke(YELLOW_M, 2.5)
        never = T("they never meet", 26, YELLOW_M).move_to([2.6, 1.0, 0])
        self.say("never")
        self.play(Create(lanes), FadeIn(la), FadeIn(lb), run_time=0.7)
        self.at(1)
        self.play(GrowFromEdge(wa, LEFT), Create(sb), run_time=1.2)
        self.play(FadeIn(done), FadeIn(sb_l), run_time=0.4)
        self.play(GrowFromEdge(wb, LEFT), run_time=1.0)
        self.play(Create(gap), FadeIn(never), run_time=0.6)
        self.at(3)
        shy = T("a race is shy around small numbers", 26, GREY_A).move_to([0, -1.2, 0])
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.6)
        self.hold()

        tue = T("a quiet Tuesday", 28, GREY_A).move_to([0, 2.6, 0])
        morning = T("the bug needs: the first morning of the sale", 28, YELLOW_M).move_to([0, -2.2, 0])
        self.say("quiet")
        self.play(FadeIn(tue), run_time=0.6)
        self.at(2)
        self.play(FadeIn(morning, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the first morning of the sale: a start latch =================
        GX = -0.6
        gate = Line([GX, -1.9, 0], [GX, 0.7, 0]).set_stroke(RED_M, 11)
        cnt = VGroup(RoundedRectangle(corner_radius=0.08, width=0.8, height=0.6, stroke_color=COUNT, stroke_width=3)
                     .set_fill(BLACK, 1), M("1", 32, COUNT)).move_to([GX, 1.15, 0])
        cnt[1].move_to(cnt[0])
        latch_l = M("CountDownLatch(1)", 24, COUNT).next_to(cnt, UP, buff=0.2)
        crowd = VGroup(*[clerk(c, 0.55) for c in CROWD]).arrange_in_grid(4, 2, buff=(0.35, 0.3)).move_to([-3.4, -0.6, 0])
        aw = T("each waits in await()", 22, GREY_B).next_to(crowd, DOWN, buff=0.3)
        desks = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.9, height=0.35).set_stroke(GREY_A, 2.5)
                         .set_fill(dim(GREY_B, 0.2), 1) for _ in range(4)]).arrange(DOWN, buff=0.55).move_to([3.6, -0.6, 0])
        d_l = T("4 cores", 22, GREY_B).next_to(desks, UP, buff=0.25)
        self.say("rush")
        self.play(Create(gate), FadeIn(desks), FadeIn(d_l), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in crowd], lag_ratio=0.08), run_time=1.0)
        self.at(2)
        self.play(FadeIn(cnt, scale=0.7), FadeIn(latch_l), run_time=0.6)
        self.at(3)
        self.play(FadeIn(aw), run_time=0.4)
        self.at_text("one countDown", lead=0.3)
        self.play(Transform(cnt[1], M("0", 32, COUNT).move_to(cnt[0])), run_time=0.3)
        self.play(gate.animate.set_stroke(GREEN_M, width=4, opacity=0.35), FadeOut(aw), run_time=0.5)
        targets = []
        for k in range(8):
            d = desks[k % 4]
            targets.append(d.get_center() + LEFT * (0.85 if k < 4 else 1.55) + UP * 0.05)
        self.play(*[c.animate.move_to(p) for c, p in zip(crowd, targets)], run_time=0.9)
        self.hold()

        rows = [("more customers than clerks", "more threads than cores"),
                ("many returns each", "many operations per thread"),
                ("many sale days", "many rounds, fresh state each time"),
                ("the till must balance", "an invariant, checked after join()")]
        habits = VGroup()
        for k, (a, b) in enumerate(rows):
            y = -2.2 - 0.0 * k
            habits.add(VGroup(T(a, 24, GREY_A), T(b, 24, YELLOW_M)))
        self.say("map")
        self.play(FadeOut(VGroup(cnt, latch_l, gate)), crowd.animate.shift(RIGHT * 1.4), desks.animate.shift(RIGHT * 1.4),
                  d_l.animate.shift(RIGHT * 1.4), run_time=0.6)
        tab = VGroup()
        for k, (a, b) in enumerate(habits):
            y = 2.5 - 0.95 * k
            a.move_to([-6.2, y, 0], aligned_edge=LEFT)
            arr = Arrow([-2.75, y, 0], [-2.05, y, 0], buff=0, stroke_width=3, color=GREY_B,
                        max_tip_length_to_length_ratio=0.3)
            b.move_to([-1.85, y, 0], aligned_edge=LEFT)
            tab.add(VGroup(a, arr, b))
        self.at(1)
        self.play(FadeIn(tab[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tab[1], shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(tab[2], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        self.say("inv")
        self.play(FadeIn(tab[3], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        never_t = T("never: how long it took", 22, BAD).next_to(tab[3][2], DOWN, buff=0.2).align_to(tab[3][2], LEFT)
        self.play(FadeIn(never_t), run_time=0.5)
        self.hold()
        self.clear()

        # ================= predict: the usual test vs the stress test =================
        r1l = VGroup(T("the usual test", 26), T("2 threads x 1,000, no start line", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        r2l = VGroup(T("the stress test", 26), T("8 threads x 100,000, a start latch", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        r1l.move_to([-6.2, 1.5, 0], aligned_edge=LEFT)
        r2l.move_to([-6.2, -0.4, 0], aligned_edge=LEFT)
        g1, g2 = squares(1, 20, 20, seed=5), squares(20, 20, 20)
        g1.move_to([2.3, 1.5, 0])
        g2.move_to([2.3, -0.4, 0])
        q1m, q2m = M("? of 20 failed", 24, GREY_B).next_to(g1, DOWN, buff=0.2), M("? of 20 failed", 24, GREY_B).next_to(g2, DOWN, buff=0.2)
        same = T("same counter, same bug", 24, GREY_A).move_to([0, 2.8, 0])
        self.say("pred")
        self.play(FadeIn(r1l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(same), FadeIn(q1m), FadeIn(q2m), run_time=0.6)
        self.hold(after=0)
        self.predict()

        a1 = M("1 of 20 failed", 24, BAD).move_to(q1m)
        a2 = M("20 of 20 failed", 24, BAD).move_to(q2m)
        self.say("show")
        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in g1], lag_ratio=0.05), Transform(q1m, a1), run_time=1.0)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in g2], lag_ratio=0.05), Transform(q2m, a2), run_time=1.0)
        self.at(2)
        other = T("another run: 0 of 20", 22, GREY_B).next_to(q1m, RIGHT, buff=0.4)
        self.play(FadeIn(other), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the refund desk under stress =================
        MU2 = 9.0 / 16000

        def rb(v, color):
            return Rectangle(width=MU2 * v, height=0.45).set_stroke(width=0).set_fill(color, 0.9).move_to(
                [-4.6 + MU2 * v / 2, 0, 0])

        setup = T("8 threads x 2,000 one-cent refunds, against a sale of 10,000 cents", 26).move_to([0, 2.3, 0])
        fit(setup, 12.4)
        lim2 = DashedLine([-4.6 + MU2 * 10000, -1.0, 0], [-4.6 + MU2 * 10000, 1.4, 0], dash_length=0.08).set_stroke(LIMIT, 3)
        lim2_l = T("the sale", 22, LIMIT).next_to(lim2, UP, buff=0.12)
        good = rb(10000, GOOD).shift(UP * 0.55)
        bad = rb(16000, BAD).shift(DOWN * 0.55)
        good_l = VGroup(T("correct ledger", 24, GOOD), M("10,000", 24, GOOD)).arrange(RIGHT, buff=0.3).next_to(good, LEFT, buff=0.3)
        bad_l = VGroup(T("racy ledger", 24, BAD), M("16,000", 24, BAD)).arrange(RIGHT, buff=0.3).next_to(bad, LEFT, buff=0.3)
        for b, l in ((good, good_l), (bad, bad_l)):
            l.next_to(b, DOWN, buff=0.15).align_to(b, LEFT)
        coat2 = T("160.00 back on a 100.00 sale", 28, BAD).move_to([0, -2.6, 0])
        self.say("refund")
        self.at(1)
        self.play(FadeIn(setup), Create(lim2), FadeIn(lim2_l), run_time=0.8)
        self.at(2)
        self.play(GrowFromEdge(good, LEFT), FadeIn(good_l), run_time=0.8)
        self.at(3)
        self.play(GrowFromEdge(bad, LEFT), FadeIn(bad_l), run_time=1.0)
        self.at(4)
        self.play(FadeIn(coat2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= guardrails =================
        clock = VGroup(Circle(radius=0.45).set_stroke(GREY_A, 4), Line(ORIGIN, UP * 0.3).set_stroke(GREY_A, 4),
                       Line(ORIGIN, RIGHT * 0.22).set_stroke(GREY_A, 4)).move_to([-4.6, 1.3, 0])
        g1t = VGroup(T("every concurrency test gets a timeout", 28),
                     T("a deadlock fails in seconds, not after an hour", 24, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        g1t.next_to(clock, RIGHT, buff=0.5)
        stamp = VGroup(RoundedRectangle(corner_radius=0.1, width=1.6, height=0.8, stroke_color=GOOD, stroke_width=4),
                       T("PASS", 28, GOOD)).move_to([-4.6, -1.0, 0])
        stamp[1].move_to(stamp[0])
        g2t = VGroup(T("means: not found this time", 28, YELLOW_M), T("never: can't happen", 28, BAD)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15).next_to(stamp, RIGHT, buff=0.5)
        self.say("guard")
        self.at(1)
        self.play(FadeIn(clock), FadeIn(g1t), run_time=0.7)
        self.play(Rotate(clock[1], -TAU, about_point=clock[0].get_center()), run_time=1.0)
        self.at(2)
        self.play(FadeIn(stamp), FadeIn(g2t[0]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(g2t[1]), run_time=0.5)
        self.hold()
        self.clear()

        # ================= sleep vs latch =================
        s1 = VGroup(M("sleep(3), then check", 24), squares(45, 100, 10, side=0.22, gap=0.07, seed=11))
        s2 = VGroup(M("latch.await(5 s), then check", 24), squares(0, 100, 10, side=0.22, gap=0.07))
        for s, x in ((s1, -3.2), (s2, 3.2)):
            s.arrange(DOWN, buff=0.3).move_to([x, 0.1, 0])
        s1q = M("? of 100 failed", 24, GREY_B).next_to(s1, DOWN, buff=0.25)
        busy = T("8 busy threads, like a build server on a busy afternoon; the work takes about 2 ms", 22, GREY_B)
        fit(busy, 12.4).move_to([0, 2.75, 0])
        self.say("sleep")
        self.at(1)
        self.play(FadeIn(s1[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(busy), run_time=0.6)
        self.at(4)
        self.play(FadeIn(s1q), run_time=0.4)
        self.hold(after=0)
        self.predict()

        s1a = M("45 of 100 failed", 24, BAD).move_to(s1q)
        s2a = M("0 of 100 failed", 24, GOOD).next_to(s2, DOWN, buff=0.25)
        self.say("sleep2")
        self.play(LaggedStart(*[FadeIn(q, scale=0.5) for q in s1[1]], lag_ratio=0.01), Transform(s1q, s1a), run_time=1.2)
        self.at(2)
        self.play(FadeIn(s2[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(q, scale=0.5) for q in s2[1]], lag_ratio=0.01), FadeIn(s2a), run_time=1.2)
        self.hold()
        self.clear()

        # ================= jcstress =================
        a1 = VGroup(T("actor 1", 24, TA), M("r1 = ++refunds", 22)).arrange(DOWN, buff=0.12)
        a2 = VGroup(T("actor 2", 24, TB), M("r2 = ++refunds", 22)).arrange(DOWN, buff=0.12)
        acts = VGroup(a1, a2).arrange(RIGHT, buff=1.6).move_to([0, 2.3, 0])
        jl = T("jcstress: a Java tool, millions of tries", 24, GREY_B).move_to([0, 3.15, 0])
        rows = [("1, 2", "acceptable", 34.65, GOOD), ("2, 1", "acceptable", 29.01, GOOD),
                ("1, 1", "interesting: a refund lost", 36.34, BAD)]
        bars = VGroup()
        for k, (o, lab, pct, col) in enumerate(rows):
            y = 0.95 - 0.85 * k
            bars.add(VGroup(M(o, 26).move_to([-5.6, y, 0]),
                            Rectangle(width=0.165 * pct, height=0.45).set_stroke(width=0).set_fill(col, 0.85)
                            .move_to([-4.7 + 0.0825 * pct, y, 0]),
                            T(lab, 24, col).move_to([-4.7 + 0.165 * pct + 0.25, y, 0], aligned_edge=LEFT)))
        pcts = VGroup(*[M(f"{p}%", 22, GREY_A).next_to(b[2], RIGHT, buff=0.3) for b, (_, _, p, _) in zip(bars, rows)])
        self.say("jcs")
        self.play(FadeIn(jl), run_time=0.6)
        self.at(2)
        self.play(FadeIn(acts, shift=DOWN * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(bars[0][0]), FadeIn(bars[0][2]), FadeIn(bars[1][0]), FadeIn(bars[1][2]), run_time=0.6)
        self.at(4)
        self.play(FadeIn(bars[2][0]), FadeIn(bars[2][2]), run_time=0.6)
        self.hold()

        samples = T("almost two billion samples", 24, GREY_A).move_to([0, -1.75, 0])
        forb = VGroup(M("FORBIDDEN", 24, BAD), T("seen once: the test fails", 24)).arrange(RIGHT, buff=0.3).move_to([0, -2.6, 0])
        self.say("jcs2")
        self.play(FadeIn(samples), *[GrowFromEdge(b[1], LEFT) for b in bars], run_time=1.0)
        self.play(FadeIn(pcts), Indicate(bars[2][1], color=BAD), run_time=0.7)
        self.at(1)
        self.play(FadeIn(forb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the code, last =================
        hl = {"Stress.failingRounds": COUNT}
        jsrc = ["int failed = Stress.failingRounds(", "    20, 8, 100_000,", "    Counter::new,", "    Counter::hit,",
                "    c -> c.count == 800_000);", "assertEquals(0, failed);"]
        ksrc = ["val failed = Stress.failingRounds(", "    20, 8, 100_000,", "    { Counter() },", "    { it.hit() },",
                "    { it.count == 800_000 })", "assertEquals(0, failed)"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.6)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        for k in range(4):
            self.at(k + 2)
            self.play(Indicate(VGroup(jc[k + 1], kc[k + 1]), color=COUNT, scale_factor=1.05), run_time=0.7)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("What is a passing test worth? Only the collisions it forced.", 30, YELLOW_M)
        m1 = T("Open the doors at nine, crowd the desk, run many days, balance the till.", 30)
        m2 = T("A pass means: not found this time.", 30)
        moral = VGroup(mq, m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 1.4)
        fit(moral, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a test starts two threads, each makes one refund, and it has never failed.", 28),
                    T("Is the ledger safe?", 28)).arrange(DOWN, buff=0.18).move_to(DOWN * 1.9)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
