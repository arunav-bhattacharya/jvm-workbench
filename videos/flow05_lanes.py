from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bflatMapConcat\b", "flat map concat"), (r"\bflatMapMerge\b", "flat map merge"),
    (r"\bflatMapLatest\b", "flat map latest"), (r"\bflatMap\b", "flat map"), (r"\bstove\.cook\b", "stove dot cook"),
    (r"\bpart a\b", "part A"), (r"\bpart b\b", "part B"),
    (r"\b([1-3])([ab])\b", lambda m: f"{m.group(1)} {m.group(2).upper()}"),
]

# every spoken line, in order
N = {
    "open": "A table orders ten dishes on one ticket, each with a small recipe card of its own. At the pass, the "
            "counter where orders come in, the head cook reads the ticket line by line and hands each dish to a "
            "helper at a free burner.",
    "rounds": "The stove has four burners, so four dishes cook at once. At 100 milliseconds a dish, ten dishes take "
              "three rounds. About 300 milliseconds.",
    "shyq": "Kotlin has an operator for exactly this kitchen: flatMapMerge. Here's a question that's easy to be "
            "shy about. If I give it four burners, doesn't everything inside it run four at a time?",
    "code": "A flow is a recipe card for values, so the ticket is a flow of dish names. stove.cook is a suspend "
            "call: it pauses for 100 milliseconds without holding a thread. The helper's lambda cooks the dish, "
            "then returns a flow of that one plate. Ten dishes, four burners. How long?",
    "slow": "1,000 milliseconds. One dish on the stove at a time, more than three times as long as we planned.",
    "joke": "Picture it. Four helpers at four warm burners, each holding an empty pan. The calmest kitchen in town. "
            "So the cap of four wasn't the problem. Something before the burners was.",
    "headcook": "Watch the head cook. She does whatever the lambda says before she hands anything to a burner. This "
                "lambda says: cook it. So she cooks every dish herself.",
    "map": "Let's map it. The ticket is the outer flow. The flow the lambda returns is the dish's recipe card: "
           "the inner flow. The burners are lanes, and concurrency counts them. The head cook is the one "
           "coroutine that runs your lambda.",
    "byhand": "Built by hand, it's short. One coroutine collects the ticket. For each dish, it calls your lambda, "
              "right here. Then it takes a permit from a semaphore, a counter of free burners. And it launches a "
              "lane that collects the inner flow.",
    "byhand2": "So the lambda runs in the one reading coroutine, before a burner is even asked for. Only the flow it "
               "returns gets a lane.",
    "fix": "So the slow call goes inside the returned flow. Now the head cook only writes the recipe card, and the "
           "helpers do the cooking. Reactor's flatMap in Java has the same trap.",
    "small": "Let's shrink it to five dishes on two burners. Soup takes 300 milliseconds, salad 100, roast 200, bread "
             "50 and pie 150, on the lesson's fake clock.",
    "small_q": "With the fix, the lambda runs for soup, salad and roast at 0. So when does roast start cooking?",
    "small_a": "At 100, when the salad frees a burner. The order is ready at 450, with two on the stove at most. And "
               "plates leave as they're ready: salad, soup, roast, bread, pie. That's completion order.",
    "small_bad": "Now put the cooking back in the lambda. 800 milliseconds: the sum of all five, what a plain map "
                 "would take. The burners did nothing.",
    "rule1": "The rule: the lambda only builds the inner flow. Put the slow work inside it.",
    "setup3": "flatMapMerge is one of three ways to run inner flows. To compare them, a table sends three orders, "
              "100 milliseconds apart, and each opens a recipe in two parts: part a after 50 milliseconds, part b "
              "150 later.",
    "concat_q": "flatMapConcat cooks one order at a time. So when does order 2 come in?",
    "concat_a": "Most people say 100. It's 300, and the whole run takes 800.",
    "concat_why": "flatMapConcat has no second coroutine and no shelf: each recipe runs inside the outer flow's emit. "
                  "Like the cook from the first lesson, the waiter stands at the pass until both parts are done. Only "
                  "then does his 100 millisecond wait begin.",
    "breaks": "Here the kitchen picture breaks. A real waiter would walk back while the dish cooks. This one can't: "
              "even his waiting happens inside emit. Put buffer in front, and he leaves orders on a shelf: 600 "
              "milliseconds.",
    "merge3": "flatMapMerge gives each order its own burner. Orders come in at 0, 100 and 200. Parts come out as "
              "they're ready, so 1b comes after 2a. Done at 400.",
    "latest3": "flatMapLatest keeps only the newest. Each new order cancels the recipe in flight, waits for it to "
               "stop, and starts the next. So 1b and 2b never arrive. Done at 400.",
    "latest_joke": "The table changed its mind twice, and the kitchen binned two half made dishes without a word. "
                   "Every waiter knows that table. It's the shape you want for a search box, where each new letter "
                   "makes the old search worthless.",
    "names": "Three operators, three promises. flatMapConcat: one at a time, and the outer waits. flatMapMerge: side "
             "by side, in completion order. flatMapLatest: only the newest.",
    "guard": "Three rules. Set the burners from what the stove can take: the default is 16, Reactor's is 256. Keep "
             "a cancelled recipe's cleanup short: the next one waits for it. And if one after another is fine, a "
             "plain map reads better.",
    "limit": "One limit: a burnt dish in any lane cancels all the others. That's the next lesson.",
    "moral": "So, does everything inside flatMapMerge run four at a time? No. The head cook runs your lambda one "
             "dish at a time, and only the recipe it returns gets a burner. Cook there, and ten dishes take 300 "
             "milliseconds.",
    "check": "Quick check. The outer emits a value, then waits 100 milliseconds, three times. Each inner gives one "
             "value after 200. How long does flatMapConcat take?",
    "check_a": "900 milliseconds: three times 200 plus 100, because the outer waits inside emit. With buffer in "
               "front, 600.",
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

    def hold(self, after=0.12):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.0, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing (the cook and helpers are blue, as in the coroutines track; failure red, cancel yellow)
COOK, ORDER, CARD, HEAT, BAD, CANCEL, NOTE = BLUE_M, PURPLE_M, TEAL_M, GOLD_M, RED_M, YELLOW_M, GREY_B


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def head_cook(s=1.0):
    p = person(COOK)
    band = RoundedRectangle(corner_radius=0.03, width=0.26, height=0.08).set_stroke(GREY_A, 2).set_fill("#2a2a2a", 1)
    band.next_to(p[1], UP, buff=0.0)
    puff = Circle(radius=0.12).set_stroke(GREY_A, 2).set_fill("#2a2a2a", 1).next_to(band, UP, buff=-0.05)
    return VGroup(p, puff, band).scale(s)


def pot(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    return VGroup(body, rim, hl, hr).scale(s)


def pan(s=1.0):
    dish = Ellipse(width=0.46, height=0.13).set_stroke(GREY_B, 2.5).set_fill("#1b1b1b", 1)
    handle = Line(dish.get_right(), dish.get_right() + RIGHT * 0.28 + DOWN * 0.05, stroke_width=3.5, color=GREY_B)
    return VGroup(dish, handle).scale(s)


def flame(s=1.0):
    outer = VMobject().set_points_smoothly([[0, 0.45, 0], [0.2, 0.1, 0], [0.22, -0.15, 0], [0, -0.3, 0],
                                            [-0.22, -0.15, 0], [-0.2, 0.1, 0], [0, 0.45, 0]])
    outer.set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.6), 1)
    inner = VMobject().set_points_smoothly([[0, 0.15, 0], [0.09, -0.05, 0], [0, -0.2, 0], [-0.09, -0.05, 0], [0, 0.15, 0]])
    inner.set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.7), 1)
    return VGroup(outer, inner).scale(s).set_z_index(5)


def recipe_card(s=1.0):
    r = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.54).set_stroke(CARD, 2.2).set_fill(dim(CARD, 0.25), 1)
    lines = VGroup(*[Line(LEFT * 0.12, RIGHT * 0.12, stroke_width=2, color=CARD) for _ in range(3)]).arrange(DOWN, buff=0.1)
    return VGroup(r, lines.move_to(r)).scale(s).set_z_index(6)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# ---- the kitchen, as it sits on screen ----
TICKET_P = np.array([-5.65, -0.45, 0])
PASS_P = np.array([-3.0, -1.1, 0])
COOK_P = np.array([-3.0, -0.42, 0])
STOVE_Y = -1.35
BURNER_X = (0.3, 1.95, 3.6, 5.25)
BURNER_Y = STOVE_Y + 0.35
HELP_Y = -0.05


def ticket():
    paper = RoundedRectangle(corner_radius=0.06, width=1.25, height=2.5).set_stroke(ORDER, 2.5).set_fill("#151515", 1)
    rows = VGroup()
    for k in range(10):
        y = 1.0 - k * 0.22
        rows.add(VGroup(Dot([-0.38, y, 0], radius=0.04, color=ORDER),
                        Line([-0.26, y, 0], [0.4, y, 0], stroke_width=2.2, color=GREY_B)))
    rows.move_to(paper.get_center() + DOWN * 0.02)
    return VGroup(paper, rows).move_to(TICKET_P)


def stove():
    body = RoundedRectangle(corner_radius=0.08, width=6.6, height=0.7).set_stroke(GREY_A, 3).set_fill("#121212", 1)
    body.move_to([2.78, STOVE_Y, 0])
    knobs = VGroup(*[Circle(radius=0.07).set_stroke(GREY_B, 2).move_to([x, STOVE_Y - 0.12, 0]) for x in BURNER_X])
    rings = VGroup(*[Ellipse(width=1.05, height=0.24).set_stroke(GREY_C, 3).set_fill("#222222", 1).move_to([x, BURNER_Y, 0])
                     for x in BURNER_X])
    return VGroup(body, knobs), rings


def light(ring, on=True):
    return ring.animate.set_stroke(HEAT if on else GREY_C).set_fill(dim(HEAT, 0.55) if on else "#222222", 1)


def pot_on(i):
    return pot(CARD, 0.62).move_to([BURNER_X[i], BURNER_Y + 0.27, 0])


class Flow05Lanes(Narrated):
    """flow-05, section 1, told from the lesson's kitchen: a ticket of ten dishes, the head cook at the pass and a
    stove of four burners. The shy question (does everything inside flatMapMerge run four at a time?); the helper's
    lambda that cooks (1,000 ms, not 300); the head cook mapped part by part; mergeLanes by hand and the fix; five
    dishes on two burners (roast starts at 100, done at 450, completion order; 800 when the lambda cooks); the three
    flattening operators on the three-order timeline (800, 400, 400; buffer gives 600); names, guardrails, the limit;
    the moral and a check (900 ms)."""

    def construct(self):
        self.title_card("Ten dishes, four burners", "flatMapConcat, flatMapMerge and flatMapLatest in Kotlin Flow")

        # ================= the ticket, the pass and the stove =================
        tk = ticket()
        tk_l = T("the ticket", 22, ORDER).next_to(tk, UP, buff=0.18)
        counter = Rectangle(width=2.1, height=0.4).set_stroke(GREY_A, 3).set_fill("#141414", 1).move_to(PASS_P).set_z_index(2)
        hc = head_cook().move_to(COOK_P)
        pass_l = T("the pass", 24, GREY_A).next_to(counter, DOWN, buff=0.2)
        hc_l = T("head cook", 22, COOK).next_to(hc, UP, buff=0.12)
        sbody, rings = stove()
        helpers = VGroup(*[person(COOK, 0.9).move_to([x, HELP_Y, 0]) for x in BURNER_X])
        st_l = T("four burners", 24, HEAT).next_to(sbody, DOWN, buff=0.2)
        self.say("open")
        self.play(FadeIn(tk), FadeIn(tk_l), run_time=0.7)
        self.at_text("small recipe card", lead=0.3)
        cards0 = VGroup(*[recipe_card(0.55).next_to(tk.get_right(), RIGHT, buff=0.1).shift(UP * (0.8 - 0.32 * k))
                          for k in range(3)])
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in cards0], lag_ratio=0.25), run_time=0.8)
        self.at(1)
        self.play(FadeOut(cards0), FadeIn(counter), FadeIn(hc), FadeIn(pass_l), FadeIn(hc_l), run_time=0.7)
        self.at_text("hands each dish", lead=0.4)
        self.play(FadeIn(sbody), FadeIn(rings), FadeIn(helpers), FadeIn(st_l), run_time=0.8)
        self.hold()

        # round 1: four lines read, four recipe cards carried to four burners
        rows = tk[1]
        clock = M("0 ms", 26, GREY_A).move_to([-5.65, -2.35, 0])
        rnd = T("4 + 4 + 2: three rounds, about 300 ms", 28, HEAT).move_to([0, -2.95, 0])
        self.say("rounds")
        flights, pots1 = [], []
        for i in range(4):
            c = recipe_card(0.55).move_to(COOK_P + UP * 0.1)
            flights.append(c)
        self.play(*[rows[i].animate.set_color(ORDER) for i in range(4)], FadeIn(clock), run_time=0.5)
        self.play(LaggedStart(*[Succession(FadeIn(flights[i], run_time=0.1),
                                           flights[i].animate(run_time=0.8).move_to([BURNER_X[i], BURNER_Y + 0.3, 0]))
                                for i in range(4)], lag_ratio=0.18), run_time=1.6)
        pots1 = [pot_on(i) for i in range(4)]
        self.play(*[FadeOut(f) for f in flights], *[FadeIn(p) for p in pots1], *[light(r) for r in rings], run_time=0.5)
        self.at_text("At 100 milliseconds", lead=0.2)
        # round 2 and 3, quickly
        self.play(*[rows[i].animate.set_opacity(0.3) for i in range(4)], *[rows[i].animate.set_color(ORDER) for i in range(4, 8)],
                  Transform(clock, M("100 ms", 26, GREY_A).move_to(clock)), run_time=0.6)
        self.play(*[Indicate(p, color=HEAT, scale_factor=1.08) for p in pots1], run_time=0.6)
        self.play(*[rows[i].animate.set_opacity(0.3) for i in range(4, 8)], *[rows[i].animate.set_color(ORDER) for i in (8, 9)],
                  FadeOut(pots1[2]), FadeOut(pots1[3]), light(rings[2], False), light(rings[3], False),
                  Transform(clock, M("200 ms", 26, GREY_A).move_to(clock)), run_time=0.6)
        self.play(*[rows[i].animate.set_opacity(0.3) for i in (8, 9)], FadeOut(pots1[0]), FadeOut(pots1[1]),
                  light(rings[0], False), light(rings[1], False),
                  Transform(clock, M("300 ms", 26, HEAT).move_to(clock)), run_time=0.6)
        self.at_text("About 300", lead=0.4)
        self.play(FadeIn(rnd, shift=UP * 0.1), run_time=0.6)
        self.hold()

        q = T("If I give it four burners, does everything inside it run four at a time?", 30).move_to([0, 2.8, 0])
        fit(q, 12.4)
        fmm = M("flatMapMerge", 30, CARD).move_to([0, 2.0, 0])
        self.say("shyq")
        self.play(FadeOut(rnd), FadeOut(clock), rows.animate.set_opacity(1).set_color(GREY_B), run_time=0.5)
        self.play(*[r[0].animate.set_color(ORDER) for r in rows], run_time=0.2)
        self.play(FadeIn(fmm, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(q), FadeOut(fmm), run_time=0.5)

        # ================= the helper's code, and the 1,000 ms =================
        c_hl = {"flatMapMerge": CARD, "concurrency = 4": HEAT, "stove.cook(dish)": BAD, "flowOf(plate)": CARD,
                "// 100 ms": GREY_B}
        csrc = ["dishes.flatMapMerge(concurrency = 4) { dish ->", "    val plate = stove.cook(dish)   // 100 ms",
                "    flowOf(plate)", "}"]
        cc = code_block(csrc, 24, c_hl).move_to([0.6, 2.45, 0])
        cc_l = T("Kotlin", 22, GREY_B).next_to(cc, LEFT, buff=0.5).align_to(cc, UP)
        self.say("code")
        self.at_text("so the ticket", lead=0.3)
        self.play(Indicate(tk[0], color=ORDER, scale_factor=1.04), run_time=0.8)
        self.at_text("stove.cook is", lead=0.3)
        self.play(FadeIn(cc_l), FadeIn(cc[0]), FadeIn(cc[3]), run_time=0.5)
        self.play(FadeIn(cc[1]), run_time=0.5)
        self.at_text("The helper's lambda", lead=0.3)
        self.play(FadeIn(cc[2]), run_time=0.5)
        self.at_text("Ten dishes, four", lead=0.3)
        self.play(Indicate(cc[0], color=HEAT, scale_factor=1.03), run_time=0.8)
        self.hold(after=0)
        self.predict(pos=(6.4, -2.4), edge=RIGHT)

        # she cooks every dish herself, one at a time
        mine = pot(CARD, 0.62).move_to(PASS_P + UP * 0.43 + RIGHT * 0.6)
        clock = M("0 ms", 26, GREY_A).move_to([-5.65, -2.35, 0])
        big = T("1,000 ms", 40, BAD).move_to([-1.5, -2.55, 0])
        one = T("one dish on the stove at a time", 26, GREY_A).next_to(big, RIGHT, buff=0.45)
        self.say("slow")
        self.play(FadeIn(mine), FadeIn(clock), hc.animate.shift(LEFT * 0.25), run_time=0.5)
        steps = []
        for k in range(10):
            steps.append(AnimationGroup(rows[k].animate.set_opacity(0.3),
                                        Transform(clock, M(f"{(k + 1) * 100:,} ms", 26, BAD if k == 9 else GREY_A).move_to(clock)),
                                        Indicate(mine, color=HEAT, scale_factor=1.06)))
        self.play(Succession(*steps, run_time=3.0))
        self.play(FadeIn(big, shift=UP * 0.1), FadeIn(one), run_time=0.6)
        self.hold()

        pans = VGroup(*[pan(0.9).next_to(h, RIGHT, buff=0.02).shift(DOWN * 0.08) for h in helpers])
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in pans], lag_ratio=0.15), run_time=1.0)
        self.play(Wiggle(pans, scale_value=1.08), run_time=1.0)
        self.at(3)
        self.play(Indicate(sbody[0], color=HEAT, scale_factor=1.02), run_time=0.8)
        self.at(4)
        self.play(Circumscribe(VGroup(hc, mine, counter), color=BAD, buff=0.12), run_time=1.0)
        self.hold()
        self.play(FadeOut(big), FadeOut(one), FadeOut(clock), run_time=0.4)

        # ================= the head cook, mapped =================
        self.say("headcook")
        self.at_text("She does", lead=0.3)
        self.play(rows.animate.set_opacity(1), run_time=0.3)
        self.play(rows[0].animate.set_color(ORDER), Indicate(hc, color=COOK), run_time=0.7)
        self.at_text("This lambda", lead=0.3)
        self.play(Indicate(cc[1], color=BAD, scale_factor=1.03), run_time=0.8)
        self.at_text("So she cooks", lead=0.3)
        self.play(Indicate(mine, color=HEAT), Wiggle(pans, scale_value=1.05), run_time=1.0)
        self.hold()

        self.play(FadeOut(cc), FadeOut(cc_l), FadeOut(mine), FadeOut(pans), hc.animate.move_to(COOK_P),
                  rows.animate.set_color(GREY_B), run_time=0.6)
        for r in rows:
            r[0].set_color(ORDER)
        mp = VGroup(
            VGroup(T("the ticket", 26, ORDER), T("the outer flow; each line is one value", 26)),
            VGroup(T("a recipe card", 26, CARD), T("the inner flow the lambda returns", 26)),
            VGroup(T("the burners", 26, HEAT), T("lanes; concurrency says how many", 26)),
            VGroup(T("the head cook", 26, COOK), T("the one coroutine that reads the ticket and runs your lambda", 26)))
        for r in mp:
            r.arrange(RIGHT, buff=0.35)
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 2.5, 0])
        fit(mp, 12.6)
        cards_t = VGroup(*[recipe_card(0.55).move_to([BURNER_X[i], BURNER_Y + 0.3, 0]) for i in range(4)])
        self.say("map")
        self.play(FadeIn(mp[0]), Indicate(tk, color=ORDER, scale_factor=1.03), run_time=0.8)
        self.at_text("The flow the lambda", lead=0.3)
        self.play(FadeIn(mp[1]), FadeIn(cards_t, shift=DOWN * 0.1), run_time=0.8)
        self.at_text("The burners are", lead=0.3)
        self.play(FadeIn(mp[2]), *[light(r) for r in rings], run_time=0.8)
        self.at_text("The head cook is", lead=0.3)
        self.play(FadeIn(mp[3]), Indicate(hc, color=COOK), run_time=0.8)
        self.hold()
        kitchen = VGroup(tk, tk_l, counter, hc, pass_l, hc_l, sbody, rings, helpers, st_l, cards_t)
        self.play(FadeOut(kitchen), FadeOut(mp), run_time=0.7)

        # ================= flatMapMerge, built by hand =================
        b_hl = {"transform(value)": BAD, "Semaphore(lanes)": HEAT, "permits.acquire()": HEAT, "launch": CARD,
                "permits.release()": HEAT, "channelFlow": CARD, "send(it)": CARD}
        bsrc = ["fun <T, R> Flow<T>.mergeLanes(lanes: Int,",
                "        transform: suspend (T) -> Flow<R>) = channelFlow {",
                "    val permits = Semaphore(lanes)",
                "    collect { value ->",
                "        val inner = transform(value)   // runs here, one at a time",
                "        permits.acquire()              // wait for a free burner",
                "        launch {                       // one lane",
                "            try { inner.collect { send(it) } }",
                "            finally { permits.release() }",
                "        }",
                "    }",
                "}"]
        bc = code_block(bsrc, 22, b_hl)
        bc.move_to([0, 0.35, 0])
        b_t = T("flatMapMerge, built by hand (Kotlin)", 26, GREY_B).next_to(bc, UP, buff=0.35).align_to(bc, LEFT)
        hl_line = SurroundingRectangle(bc[4], buff=0.08, color=BAD, corner_radius=0.06)
        self.say("byhand")
        self.play(FadeIn(b_t), FadeIn(bc[0]), FadeIn(bc[1]), FadeIn(bc[11]), run_time=0.7)
        self.at_text("One coroutine", lead=0.3)
        self.play(FadeIn(bc[3]), FadeIn(bc[10]), run_time=0.5)
        self.at_text("For each dish", lead=0.3)
        self.play(FadeIn(bc[4]), run_time=0.5)
        self.at_text("Then it takes", lead=0.3)
        self.play(FadeIn(bc[2]), FadeIn(bc[5]), run_time=0.6)
        self.at_text("And it launches", lead=0.3)
        self.play(FadeIn(bc[6]), FadeIn(bc[7]), FadeIn(bc[8]), FadeIn(bc[9]), run_time=0.7)
        self.hold()
        before = T("it runs before a burner is even asked for", 26, BAD).move_to([0, -3.05, 0])
        self.say("byhand2")
        self.play(Create(hl_line), run_time=0.7)
        self.play(FadeIn(before, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(bc[6], bc[7], bc[8], bc[9]), color=CARD, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(bc, b_t, hl_line, before)), run_time=0.5)

        # ================= the fix, Kotlin and Java =================
        f_hl = {"flatMapMerge": CARD, "concurrency = 4": HEAT, "flow { emit(stove.cook(dish)) }": CARD,
                "// the cooking runs in the lane": GREY_B}
        fsrc = ["dishes.flatMapMerge(concurrency = 4) { dish ->", "    flow { emit(stove.cook(dish)) }   // the cooking runs in the lane",
                "}"]
        jsrc = ["dishes.flatMap(dish -> stove.cook(dish), 4);   // cook returns a lazy Mono"]
        fk = code_block(fsrc, 24, f_hl)
        fj = code_block(jsrc, 24, {"flatMap": CARD, "// cook returns a lazy Mono": GREY_B})
        cols = VGroup(VGroup(T("Kotlin Flow", 24, GREY_B), fk).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java, with Reactor", 24, GREY_B), fj).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(cols, 12.6).move_to([0, 0.9, 0])
        trap = T("block inside the mapper, and Reactor cooks one at a time too", 24, BAD).move_to([0, -1.6, 0])
        self.say("fix")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(fk[1], color=CARD, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(trap), run_time=0.5)
        self.hold()
        self.play(FadeOut(cols), FadeOut(trap), run_time=0.5)

        # ================= five dishes, two burners, on a chart =================
        X0, KX = -3.6, 9.6 / 800

        def X(ms):
            return X0 + KX * ms

        RY = {"cook": 0.95, 0: -0.2, 1: -1.35}
        AXY = -2.15
        dish_ms = {"soup": 300, "salad": 100, "roast": 200, "bread": 50, "pie": 150}
        legend = T("soup 300 ms, salad 100, roast 200, bread 50, pie 150", 26, GREY_A).move_to([0, 3.15, 0])
        code2 = M("dishes.flatMapMerge(concurrency = 2) { d -> flow { emit(stove.cook(d)) } }", 22,
                  t2c={"flatMapMerge": CARD, "concurrency = 2": HEAT, "flow { emit(stove.cook(d)) }": CARD}).move_to([0, 2.4, 0])
        fit(code2, 12.6)
        row_l = VGroup(T("head cook", 24, COOK).move_to([-6.4, RY["cook"], 0], aligned_edge=LEFT),
                       T("burner 1", 24, HEAT).move_to([-6.4, RY[0], 0], aligned_edge=LEFT),
                       T("burner 2", 24, HEAT).move_to([-6.4, RY[1], 0], aligned_edge=LEFT))
        guides = VGroup(*[DashedLine([X(0), y, 0], [X(800), y, 0], dash_length=0.06, stroke_width=1.2, color=GREY_D)
                          for y in (RY["cook"], RY[0], RY[1])])
        axis = VGroup(Line([X(0), AXY, 0], [X(800), AXY, 0], stroke_width=1.5, color=GREY_C))
        for ms in range(0, 801, 200):
            axis.add(Line([X(ms), AXY - 0.07, 0], [X(ms), AXY + 0.07, 0], stroke_width=1.5, color=GREY_C))
            axis.add(T(f"{ms} ms" if ms == 0 else str(ms), 20, NOTE).move_to([X(ms), AXY - 0.32, 0]))

        def bar(name, a, row, color=CARD):
            b = dish_ms[name]
            r = Rectangle(width=KX * b - 0.04, height=0.55).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
            r.move_to([X(a) + 0.02, RY[row], 0], aligned_edge=LEFT)
            t = T(name, 20, WHITE)
            if t.width > r.width - 0.08:
                t.next_to(r, UP, buff=0.08)
            else:
                t.move_to(r)
            return VGroup(r, t)

        def grow(b, rt=0.6):
            return Succession(GrowFromEdge(b[0], LEFT, run_time=rt), FadeIn(b[1], run_time=0.2))

        self.say("small")
        self.play(FadeIn(row_l), Create(guides), FadeIn(axis), run_time=0.8)
        self.at_text("Soup takes", lead=0.3)
        self.play(FadeIn(legend), run_time=0.6)
        self.at_text("on the lesson's", lead=0.3)
        self.play(FadeIn(code2), run_time=0.6)
        self.hold()

        soup, salad = bar("soup", 0, 0), bar("salad", 0, 1)
        lam = VGroup(Line([X(0), RY["cook"] - 0.25, 0], [X(0), RY["cook"] + 0.25, 0], stroke_width=4, color=COOK),
                     T("the lambda runs for soup, salad, roast", 22, COOK))
        lam[1].next_to(lam[0], RIGHT, buff=0.15)
        self.say("small_q")
        self.play(Create(lam[0]), FadeIn(lam[1]), run_time=0.6)
        self.play(grow(soup, 0.9), grow(salad, 0.5), run_time=0.9)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)

        roast, bread, pie = bar("roast", 100, 1), bar("bread", 300, 0), bar("pie", 300, 1)
        rwait = DashedLine([X(0) + 0.05, RY[1] + 0.42, 0], [X(100), RY[1] + 0.42, 0], dash_length=0.06,
                           stroke_width=2.5, color=HEAT)
        rw_l = T("roast waits for a burner", 20, HEAT).next_to(rwait, UP, buff=0.06).align_to(rwait, LEFT)
        done = VGroup(DashedLine([X(450), RY[0] + 0.45, 0], [X(450), AXY, 0], dash_length=0.06, stroke_width=2, color=GREEN_M),
                      T("ready at 450", 22, GREEN_M))
        done[1].next_to(done[0], UP, buff=0.08).shift(RIGHT * 0.25)
        most = T("most on the stove at once: 2", 22, HEAT).move_to([4.3, RY["cook"], 0])
        self.say("small_a")
        self.play(Create(rwait), FadeIn(rw_l), run_time=0.5)
        self.play(grow(roast, 0.8), run_time=0.8)
        self.play(grow(bread, 0.4), grow(pie, 0.7), run_time=0.8)
        self.at_text("The order is ready", lead=0.3)
        self.play(Create(done[0]), FadeIn(done[1]), run_time=0.6)
        self.play(FadeIn(most), run_time=0.5)
        order = VGroup(T("plates leave:", 22, GREY_B), *[T(n, 22, CARD) for n in ("salad", "soup", "roast", "bread", "pie")])
        order.arrange(RIGHT, buff=0.25).move_to([0, -3.1, 0])
        self.at_text("And plates", lead=0.3)
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in order], lag_ratio=0.2), run_time=1.6)
        self.hold()

        # the cooking back in the lambda: every bar moves into the head cook's row
        code_bad = M("dishes.flatMapMerge(concurrency = 2) { d -> val p = stove.cook(d); flowOf(p) }", 22,
                     t2c={"flatMapMerge": CARD, "concurrency = 2": HEAT, "stove.cook(d)": BAD}).move_to(code2)
        fit(code_bad, 12.6)
        RY["cook2"] = RY["cook"]
        seq = [("soup", 0), ("salad", 300), ("roast", 400), ("bread", 600), ("pie", 650)]
        new_bars = [bar(n, a, "cook") for n, a in seq]
        for nb in new_bars:
            nb[0].set_stroke(BAD)
        # the bread label sits above its bar; keep labels inside the chart for the cook row
        sum_l = T("ready at 800 = 300 + 100 + 200 + 50 + 150", 24, BAD).move_to([1.2, -3.1, 0])
        self.say("small_bad")
        self.play(Transform(code2, code_bad), FadeOut(lam), FadeOut(rwait), FadeOut(rw_l), FadeOut(most), FadeOut(done),
                  FadeOut(order), run_time=0.7)
        self.play(*[Transform(o, n) for o, n in zip((soup, salad, roast, bread, pie), new_bars)], run_time=1.4)
        self.at_text("the sum of all", lead=0.3)
        self.play(FadeIn(sum_l, shift=UP * 0.1), run_time=0.6)
        self.at_text("The burners did", lead=0.3)
        self.play(Indicate(VGroup(row_l[1], row_l[2]), color=HEAT), run_time=0.8)
        self.hold()

        rule = T("The lambda only builds the inner flow. Put the slow work inside it.", 30, CARD).move_to([0, 2.4, 0])
        fit(rule, 12.6)
        self.say("rule1")
        self.play(FadeOut(code2), FadeOut(legend), run_time=0.4)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(rule, row_l, guides, axis, soup, salad, roast, bread, pie, sum_l)), run_time=0.6)

        # ================= three ways to run the inner flows =================
        TX0, TK = -3.0, 8.9 / 800

        def tx(ms):
            return TX0 + TK * ms

        YR = (1.45, -0.05, -1.55)
        AY = -2.65
        PART_C = {1: TEAL_M, 2: GREEN_M, 3: PURPLE_M}

        def order_dot(n, ms, y):
            c = Circle(radius=0.19).set_stroke(ORDER, 2.5).set_fill(dim(ORDER, 0.45), 1)
            return VGroup(c, T(str(n), 20)).move_to([tx(ms), y + 0.4, 0])

        def part(lbl, ms, y):
            r = RoundedRectangle(corner_radius=0.06, width=0.48, height=0.34).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.35), 1)
            return VGroup(r, T(lbl, 20)).move_to([tx(ms), y - 0.4, 0])

        def ghost(lbl, ms, y):
            r = DashedVMobject(RoundedRectangle(corner_radius=0.06, width=0.48, height=0.34), num_dashes=14).set_stroke(CANCEL, 2)
            g = VGroup(r, T(lbl, 20, GREY_C)).move_to([tx(ms), y - 0.4, 0])
            g.add(tick(False, 0.08).set_stroke(CANCEL, 4).move_to(r.get_corner(UR) + UP * 0.02 + RIGHT * 0.02).set_z_index(4))
            return g

        def row(name, y, end):
            line = Line([tx(0), y, 0], [tx(end), y, 0], stroke_width=2.5, color=GREY_B)
            nm = M(name, 24, CARD).move_to([-6.4, y, 0], aligned_edge=LEFT)
            endt = VGroup(Line([tx(end), y - 0.12, 0], [tx(end), y + 0.12, 0], stroke_width=2.5, color=GREY_B),
                          T(f"done {end}", 20, GREEN_M).move_to([tx(end), y + 0.42, 0]))
            return line, nm, endt

        tax = VGroup(Line([tx(0), AY, 0], [tx(800), AY, 0], stroke_width=1.5, color=GREY_C))
        for ms in range(0, 801, 200):
            tax.add(Line([tx(ms), AY - 0.07, 0], [tx(ms), AY + 0.07, 0], stroke_width=1.5, color=GREY_C))
            tax.add(T(f"{ms} ms" if ms == 0 else str(ms), 20, NOTE).move_to([tx(ms), AY - 0.32, 0]))
        head3 = T("three orders, 100 ms apart; part a after 50 ms, part b 150 ms later", 24, GREY_A).move_to([0, 3.2, 0])
        fit(head3, 12.6)

        self.say("setup3")
        self.play(FadeIn(tax), run_time=0.5)
        self.at(1)
        sample = VGroup(*[order_dot(n, 100 * (n - 1), YR[1]) for n in (1, 2, 3)])
        self.play(LaggedStart(*[FadeIn(s, scale=0.6) for s in sample], lag_ratio=0.3), run_time=1.0)
        self.at_text("and each opens", lead=0.3)
        sp = VGroup(part("1a", 50, YR[1]), part("1b", 200, YR[1]))
        self.play(FadeIn(head3), LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in sp], lag_ratio=0.4), run_time=1.0)
        self.hold()
        self.play(FadeOut(sample), FadeOut(sp), run_time=0.4)

        # flatMapConcat
        cl, cn, ce = row("flatMapConcat", YR[0], 800)
        c_orders = [order_dot(1, 0, YR[0]), order_dot(2, 300, YR[0]), order_dot(3, 600, YR[0])]
        c_parts = [part(l, ms, YR[0]) for l, ms in (("1a", 50), ("1b", 200), ("2a", 350), ("2b", 500), ("3a", 650), ("3b", 800))]
        self.say("concat_q")
        self.play(FadeIn(cn), Create(cl), FadeIn(c_orders[0], scale=0.6), run_time=0.7)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)
        self.say("concat_a")
        self.at(1)
        self.play(FadeIn(c_parts[0]), FadeIn(c_parts[1]), run_time=0.5)
        self.play(FadeIn(c_orders[1], scale=0.6), run_time=0.4)
        self.play(Indicate(c_orders[1], color=ORDER), FadeIn(c_parts[2]), FadeIn(c_parts[3]), run_time=0.6)
        self.play(FadeIn(c_orders[2], scale=0.6), FadeIn(c_parts[4]), FadeIn(c_parts[5]), run_time=0.6)
        self.play(FadeIn(ce), run_time=0.4)
        self.hold()

        paused = VGroup(DashedLine([tx(0) + 0.25, YR[0] + 0.85, 0], [tx(300) - 0.25, YR[0] + 0.85, 0], dash_length=0.07,
                                   stroke_width=2.2, color=ORDER),
                        T("the waiter stands at the pass, inside emit", 20, ORDER))
        paused[1].next_to(paused[0], UP, buff=0.06)
        self.say("concat_why")
        self.at_text("each recipe runs", lead=0.3)
        self.play(Create(paused[0]), run_time=0.6)
        self.at_text("the waiter", lead=0.3)
        self.play(FadeIn(paused[1]), run_time=0.6)
        self.at_text("Only then", lead=0.3)
        self.play(Indicate(c_orders[1], color=ORDER), run_time=0.8)
        self.hold()
        buf = T("buffer() in front: done at 600", 22, GREY_A).move_to([3.6, YR[0] + 1.2, 0])
        self.say("breaks")
        self.at_text("Put buffer", lead=0.3)
        self.play(FadeIn(buf, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # flatMapMerge
        ml, mn, me = row("flatMapMerge", YR[1], 400)
        m_orders = [order_dot(n, 100 * (n - 1), YR[1]) for n in (1, 2, 3)]
        m_parts = [part(l, ms, YR[1]) for l, ms in (("1a", 50), ("2a", 150), ("1b", 200), ("3a", 250), ("2b", 300), ("3b", 400))]
        self.say("merge3")
        self.play(FadeIn(mn), Create(ml), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(o, scale=0.6) for o in m_orders], lag_ratio=0.3), run_time=0.9)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in m_parts], lag_ratio=0.25), run_time=1.4)
        self.play(Indicate(VGroup(m_parts[1], m_parts[2]), color=CARD, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(me), run_time=0.4)
        self.hold()

        # flatMapLatest
        ll, ln, le = row("flatMapLatest", YR[2], 400)
        l_orders = [order_dot(n, 100 * (n - 1), YR[2]) for n in (1, 2, 3)]
        l_parts = [part(l, ms, YR[2]) for l, ms in (("1a", 50), ("2a", 150), ("3a", 250), ("3b", 400))]
        l_ghost = [ghost("1b", 200, YR[2]), ghost("2b", 300, YR[2])]
        self.say("latest3")
        self.play(FadeIn(ln), Create(ll), FadeIn(l_orders[0], scale=0.6), FadeIn(l_parts[0]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(l_orders[1], scale=0.6), FadeIn(l_ghost[0]), run_time=0.6)
        self.play(FadeIn(l_parts[1]), FadeIn(l_orders[2], scale=0.6), FadeIn(l_ghost[1]), run_time=0.6)
        self.play(FadeIn(l_parts[2]), FadeIn(l_parts[3]), run_time=0.5)
        self.at(2)
        self.play(*[Indicate(g, color=CANCEL) for g in l_ghost], run_time=0.8)
        self.at(3)
        self.play(FadeIn(le), run_time=0.4)
        self.hold()
        self.say("latest_joke")
        self.play(*[Wiggle(g, scale_value=1.15) for g in l_ghost], run_time=1.0)
        self.at(2)
        sb = T("the shape for a search box as you type", 22, GREY_A).move_to([4.2, YR[2] + 0.75, 0])
        self.play(FadeIn(sb, shift=UP * 0.1), run_time=0.6)
        self.hold()

        timeline = VGroup(tax, head3, cl, cn, ce, *c_orders, *c_parts, paused, buf, ml, mn, me, *m_orders, *m_parts,
                          ll, ln, le, *l_orders, *l_parts, *l_ghost, sb)
        self.play(FadeOut(timeline), run_time=0.7)

        # ================= names, guardrails and the limit =================
        nrows = VGroup()
        for k, (a, b) in enumerate((("flatMapConcat", "one at a time, and the outer waits"),
                                    ("flatMapMerge", "side by side, in completion order"),
                                    ("flatMapLatest", "only the newest; the old one is cancelled"))):
            y = 2.6 - 0.62 * k
            nrows.add(VGroup(M(a, 26, CARD).move_to([-5.9, y, 0], aligned_edge=LEFT),
                             T(b, 26).move_to([-2.2, y, 0], aligned_edge=LEFT)))
        self.say("names")
        self.at_text("flatMapConcat:", lead=0.3)
        self.play(FadeIn(nrows[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("flatMapMerge:", lead=0.3)
        self.play(FadeIn(nrows[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("flatMapLatest:", lead=0.3)
        self.play(FadeIn(nrows[2], shift=UP * 0.1), run_time=0.6)
        self.hold()

        grows = VGroup(
            VGroup(T("1", 26, HEAT), T("set the burners from the stove: the default is 16, Reactor's 256", 26)),
            VGroup(T("2", 26, HEAT), T("keep a cancelled recipe's cleanup short: the next one waits", 26)),
            VGroup(T("3", 26, HEAT), T("one after another is fine? a plain map reads better", 26)))
        for r in grows:
            r.arrange(RIGHT, buff=0.3)
        grows.arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to([0, -0.9, 0])
        fit(grows, 12.6)
        self.say("guard")
        self.at_text("Set the burners", lead=0.3)
        self.play(FadeIn(grows[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("Keep a cancelled", lead=0.3)
        self.play(FadeIn(grows[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("And if one after", lead=0.3)
        self.play(FadeIn(grows[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(nrows), FadeOut(grows), run_time=0.5)

        sbody2, rings2 = stove()
        sv = VGroup(sbody2, rings2).move_to([0, -0.6, 0])
        bx = [r.get_center()[0] for r in rings2]
        pots2 = [pot(CARD, 0.62).move_to([x, rings2[0].get_center()[1] + 0.27, 0]) for x in bx]
        fl = flame(0.7).move_to(pots2[1].get_top() + UP * 0.35)
        lim_t = T("a burnt dish in any lane cancels all the others", 28, BAD).move_to([0, 1.9, 0])
        nxt = T("what a failure costs: the next lesson", 24, GREY_B).move_to([0, -2.3, 0])
        self.say("limit")
        self.play(FadeIn(sv), *[FadeIn(p) for p in pots2], *[r.animate.set_stroke(HEAT).set_fill(dim(HEAT, 0.55), 1) for r in rings2],
                  run_time=0.7)
        self.play(FadeIn(fl, scale=0.5), pots2[1][0].animate.set_stroke(BAD), FadeIn(lim_t), run_time=0.6)
        self.play(*[pots2[k].animate.set_opacity(0.3) for k in (0, 2, 3)],
                  *[Create(tick(False, 0.18).move_to(pots2[k])) for k in (0, 2, 3)], run_time=0.8)
        self.at(1)
        self.play(FadeIn(nxt), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does everything inside flatMapMerge run four at a time? No.", 32).move_to(UP * 2.5)
        m1 = T("The head cook runs your lambda, one dish at a time.", 28, COOK).move_to(UP * 1.7)
        m2 = T("Only the recipe it returns gets a burner.", 28, CARD).move_to(UP * 1.05)
        m3 = T("Cook inside it, and ten dishes take 300 ms.", 28, HEAT).move_to(UP * 0.4)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("and only the recipe", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M), T("the outer emits, then waits 100 ms, three times;", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("each inner gives one value after 200 ms. flatMapConcat takes?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.0, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("900 ms: 3 x (200 + 100), the outer waits inside emit; with buffer() first, 600", 26, GREEN_M)
        fit(ans, 12.4).move_to(DOWN * 2.45)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(1.5)
