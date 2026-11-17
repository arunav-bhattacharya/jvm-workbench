from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bflow \{ \}", "flow"),
    (r"\bcollect \{ \}", "collect"), (r"\bemit\((\w+)\)", r"emit \1"), (r"\bDinnerOrder\b", "Dinner Order"),
]

# every spoken line, in order
N = {
    "open": "Remember the home cook from the coroutines track? Tonight, her recipe card lists three dishes: soup, "
            "salad and roast. The card on its own cooks nothing.",
    "diner": "Then a diner sits down at the table and asks to be served. Only now does the cook start, at the top of "
             "the card.",
    "shyq": "Here's a question that's easy to be shy about. In a Kotlin flow, the cook hands over each dish with emit. "
            "So when she hands over the soup, does she put it down and get on with the salad? Or does she wait?",
    "map1": "First, let's map the kitchen onto code. A flow is a stream of values, handed over one at a time. "
            "flow { } is the recipe card: it stores the cooking, and runs none of it.",
    "map2": "The cook is the producer, the code inside flow { }. The diner is the collector, the code inside "
            "collect { }. Calling collect is the diner asking to be served. And emit hands one dish to the diner.",
    "order_q": "The lesson's DinnerOrder makes this visible. The cook prints a line before and after each emit, and the "
               "diner prints a line for each dish. In what order do the lines come out?",
    "guess1": "Two guesses are tempting. One: all three cook lines come first, as if emit put each dish on a shelf "
              "for later.",
    "guess2": "Two: emit(soup) returned comes before eat soup, as if the cook handed the bowl over and walked off.",
    "real": "Here's what it really prints. flow built comes first, so building the flow ran nothing at all. And eat "
            "soup comes before emit(soup) returned. The diner ate while emit was still running.",
    "cold": "That first line is what cold means: no collect, no cooking. And a second collect cooks the whole card "
            "again, from the top. Two diners, two dinners. Nobody gets leftovers.",
    "noshelf": "So why can't the cook put the bowl down? Look around this kitchen. No counter, no shelf, not even a "
               "windowsill. Whoever designed it never cooked for guests. But that's the point: the only place a "
               "dish can go is into the diner's hands.",
    "call": "In code, emit is a plain function call into the collector. The diner's code runs inside emit, and emit "
            "returns only when the diner's code returns.",
    "stack": "Draw each call that's still running as a box. main calls collect. collect runs the flow block: that's "
             "the cook. The cook calls emit: her walk to the table. And inside emit runs your collect lambda: the "
             "diner, eating the soup.",
    "stack2": "It's all one thread, the worker that runs the code, and one call stack. emit can't return until the "
              "innermost box closes. So the cook stands at the table.",
    "time_q": "Now let's put numbers on it. The cook needs 100 milliseconds to cook a dish. The diner needs 300 "
              "milliseconds to eat it. The first emit comes at 100. When does the second one come?",
    "t1": "At 100, the cook calls emit with the soup, and stands at the table while the diner eats. The diner "
          "finishes at 400, and only then does emit return.",
    "t2": "Then the cook needs 100 more for the salad. So the second emit comes at 500, not 200. The roast goes out "
          "at 900, and the last bite is at 1,200.",
    "t200": "The answer 200 pictures emit dropping the dish in a queue while the cook carries on. A plain flow never "
            "does that.",
    "seq": "Now read the rules off the picture. A flow is sequential: one value at a time. The salad can't start while "
           "emit(soup) is still open, and the diner never holds two plates at once.",
    "bp": "And a slow collector slows the producer. The cook could serve a dish every 100 milliseconds. Here she "
          "serves one every 400, because she waits at the table.",
    "bp_name": "That has a name: backpressure. A slow consumer slows the producer down, so values don't pile up in "
               "memory. A plain flow gets it for free, with no extra machinery.",
    "three": "Cold, one at a time, and slowed by the diner. Three rules, and all three come from one fact: emit is a "
             "plain call.",
    "cost": "But free isn't fast. Three dishes took 1,200 milliseconds, where the slower side alone needs only 900. "
            "In a plain flow the times add up: each dish costs the cook's time plus the diner's.",
    "stove": "And careful where you put a stopwatch. Say the cook wraps a timer around emit. It says 300 milliseconds "
             "per dish, so she goes shopping for a faster stove. But a timer around emit measures the diner. The "
             "stove was never the problem.",
    "shelf": "If you want the cook to work ahead, you need a shelf between the kitchen and the table. Lesson 4 of this "
             "track adds one, called a buffer, and pays for it in memory.",
    "breaks": "Here the picture breaks. A real cook standing at the table is lost to the kitchen. A coroutine is "
              "luckier. A coroutine, remember, is work that can pause and carry on later, and while it's paused, it "
              "holds no thread.",
    "breaks2": "So while the diner waits, say on a delay or a slow answer, the thread goes off and runs other "
               "coroutines. Only this one dinner is held up.",
    "code": "Here's the dinner in code. In Kotlin, emit sits in the middle of the cook's loop. Java has no Flow, so "
            "the cook calls the diner's Consumer instead. accept is a plain call too, and the line after it runs "
            "when the call returns.",
    "moral": "So, does the cook put the soup down and carry on? No. There's nowhere to put it. A plain flow is one "
             "call stack, and the collector runs inside emit. That's why a flow is cold, serves one dish at a "
             "time, and moves at the speed of its diner.",
    "check": "Quick check. The cook needs 50 milliseconds per dish, and the diner 200 to eat it. No buffer. How long "
             "do four dishes take?",
    "check_a": "1,000 milliseconds. Each dish costs 50 plus 200, because the cook waits inside emit while the diner "
               "eats.",
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


# one colour per thing, for the whole flow track (the cook is the coroutines track's cook)
COOK, DINER, EMIT, CARD, BAD = BLUE_M, TEAL_M, PURPLE_M, GREY_A, RED_M
SOUP, SALAD, ROAST = YELLOW_M, GREEN_M, GOLD_M


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def pot(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    return VGroup(body, rim, hl, hr).scale(s)


def stove(s=1.0):
    body = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.95).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    door = RoundedRectangle(corner_radius=0.05, width=1.0, height=0.45).set_stroke(GREY_C, 2).set_fill(BLACK, 1)
    door.move_to(body.get_center() + DOWN * 0.12)
    knobs = VGroup(*[Circle(radius=0.05).set_stroke(GREY_B, 2).set_fill(GREY_D, 1) for _ in range(3)]).arrange(RIGHT, buff=0.2)
    knobs.move_to(body.get_top() + DOWN * 0.15)
    g = VGroup(body, door, knobs)
    p = pot(SOUP, 0.7).next_to(body, UP, buff=0.02)
    return VGroup(g, p).scale(s)


def dish(kind, s=1.0):
    """soup: a bowl; salad: a bowl of leaves; roast: a plate with a roast on it."""
    if kind == "salad":
        arc = Arc(radius=0.36, start_angle=PI, angle=PI).set_stroke(SALAD, 3)
        top = Line(LEFT * 0.36, RIGHT * 0.36, stroke_width=3, color=SALAD)
        leaves = VGroup(*[Circle(radius=0.08).set_stroke(SALAD, 2).set_fill(dim(SALAD, 0.5), 1).move_to([dx, 0.06, 0])
                          for dx in (-0.2, -0.04, 0.12, 0.26)])
        g = VGroup(leaves, arc, top)
    elif kind == "roast":
        plate = Ellipse(width=0.86, height=0.26).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1).shift(DOWN * 0.12)
        meat = Ellipse(width=0.5, height=0.3).set_stroke(ROAST, 3).set_fill(dim(ROAST, 0.5), 1).shift(UP * 0.02)
        g = VGroup(plate, meat)
    else:
        arc = Arc(radius=0.36, start_angle=PI, angle=PI).set_stroke(SOUP, 3)
        top = Line(LEFT * 0.36, RIGHT * 0.36, stroke_width=3, color=SOUP)
        fill = Polygon(*[arc.point_from_proportion(a) for a in np.linspace(0, 1, 16)]).set_stroke(width=0)
        fill.set_fill(dim(SOUP, 0.45), 1)
        g = VGroup(fill, arc, top)
    return g.scale(s).set_z_index(3)


def table(w=2.6):
    top = Line(LEFT * w / 2, RIGHT * w / 2, stroke_width=6, color=GREY_B)
    legs = VGroup(Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_left() + RIGHT * 0.2 + DOWN * 0.35),
                  Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_right() + LEFT * 0.2 + DOWN * 0.35))
    return VGroup(top, legs)


def recipe_card():
    r = RoundedRectangle(corner_radius=0.1, width=2.7, height=2.25).set_stroke(CARD, 2.5).set_fill("#141414", 1)
    head = T("Tonight", 28).move_to(r.get_top() + DOWN * 0.38)
    ln = Line(LEFT * 1.0, RIGHT * 1.0, stroke_width=1.5, color=GREY_D).next_to(head, DOWN, buff=0.12)
    rows = VGroup()
    for i, (name, c) in enumerate((("soup", SOUP), ("salad", SALAD), ("roast", ROAST))):
        d = Dot(radius=0.07, color=c)
        rows.add(VGroup(T(f"{i + 1}", 24, GREY_B), d, T(name, 26, c)).arrange(RIGHT, buff=0.18))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(ln, DOWN, buff=0.2)
    return VGroup(r, head, ln, rows)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


# the clock: a horizontal time axis, x(ms)
X0, PX = -4.2, 9.6 / 1200


def tx(ms):
    return X0 + ms * PX


def bar(ms0, ms1, y, color, h=0.46, label=None, size=20, k=0.45, tc=WHITE):
    r = Rectangle(width=max(0.04, (ms1 - ms0) * PX), height=h).set_stroke(color, 2).set_fill(dim(color, k), 1)
    r.move_to([(tx(ms0) + tx(ms1)) / 2, y, 0])
    if label:
        return VGroup(r, T(label, size, tc).move_to(r))
    return VGroup(r)


def axis(y, ticks):
    ln = Arrow([tx(0) - 0.1, y, 0], [tx(max(ticks)) + 0.5, y, 0], buff=0, stroke_width=2.5, color=GREY_B,
               max_tip_length_to_length_ratio=0.03)
    tk = VGroup(*[VGroup(Line([tx(m), y - 0.07, 0], [tx(m), y + 0.07, 0], stroke_width=2, color=GREY_B),
                         T(f"{m:,}", 20, GREY_B).move_to([tx(m), y - 0.3, 0])) for m in ticks])
    ms = T("ms", 20, GREY_B).next_to(ln, RIGHT, buff=0.1)
    return VGroup(ln, tk, ms)


def nest(l, r, t, b, color, label, size=22, mono_part=None, k=0.1):
    box_ = RoundedRectangle(corner_radius=0.14, width=r - l, height=t - b).set_stroke(color, 2.5)
    box_.set_fill(dim(color, k), 1).move_to([(l + r) / 2, (t + b) / 2, 0])
    lab = T(label, size, color).move_to([(l + r) / 2, t - 0.27, 0])
    return VGroup(box_, lab)


class Flow01InsideEmit(Narrated):
    """flow-01, section 3: the collector runs inside emit. The home cook, tonight's card (soup, salad, roast), a diner
    who asks to be served; the shy question (does she put the plate down?); the map (card = flow { }, cook = producer,
    diner = collector); DinnerOrder's print order, two wrong guesses broken; cold (two diners, two dinners); no shelf,
    a plain call, the nested boxes; 100 ms to cook, 300 to eat: emit 2 at 500, not 200; sequential and backpressure
    named; the cost (1,200 vs 900) and the timer around emit; the picture breaks (no thread held); code; check."""

    def construct(self):
        self.title_card("The cook waits at the table", "what emit really does in a Kotlin flow")

        # ================= hook: the kitchen, the card, the diner =================
        stv = stove(1.0).move_to([-5.3, -0.95, 0])
        cook = person(COOK, 1.3).move_to([-3.95, -0.9, 0])
        card = recipe_card().move_to([-0.7, 1.75, 0])
        tbl = table(2.6).move_to([4.5, -1.55, 0])
        diner = person(DINER, 1.3).move_to([5.25, -0.85, 0])
        floor = Line([-6.5, -1.95, 0], [6.5, -1.95, 0], stroke_width=1.5, color=GREY_D)
        self.say("open")
        self.play(FadeIn(floor), FadeIn(stv), FadeIn(cook), FadeIn(tbl), run_time=0.8)
        self.at_text("her recipe card", lead=0.3)
        self.play(FadeIn(card, shift=DOWN * 0.15), run_time=0.7)
        self.at_text("soup,", lead=0.3)
        self.play(LaggedStart(*[Indicate(r[2], color=WHITE, scale_factor=1.15) for r in card[3]], lag_ratio=0.45), run_time=1.6)
        self.at(2)
        idle = T("nothing cooking", 24, GREY_B).next_to(card, DOWN, buff=0.22)
        self.play(FadeIn(idle), run_time=0.5)
        self.hold()

        self.say("diner")
        self.play(FadeIn(diner, shift=DOWN * 0.3), run_time=0.8)
        asks = T("\"serve me, please\"", 24, DINER).next_to(diner, UP, buff=0.25).shift(LEFT * 0.4)
        self.play(FadeIn(asks, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        arrow1 = Arrow(card[3][0].get_left() + LEFT * 0.75, card[3][0].get_left() + LEFT * 0.12, buff=0, stroke_width=4,
                       color=COOK, max_tip_length_to_length_ratio=0.3)
        self.play(FadeOut(idle), GrowArrow(arrow1), Indicate(card[3][0][2], color=SOUP, scale_factor=1.2), run_time=0.9)
        self.hold()

        q1 = T("emit hands the soup over. Does the cook put it down and get on with the salad?", 28)
        q2 = T("Or does she wait?", 28, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.18).move_to([0, -2.85, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeOut(asks), run_time=0.3)
        self.at_text("So when", lead=0.3)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(qg), FadeOut(arrow1), run_time=0.5)

        # ================= the map =================
        m_card = VGroup(M("flow { }", 24, CARD), T("stores the cooking, runs none of it", 22, GREY_A)).arrange(DOWN, buff=0.1)
        m_card.next_to(card, DOWN, buff=0.22)
        m_flow = T("a flow: values handed over one at a time", 24, WHITE).move_to([-0.7, 3.25, 0])
        self.say("map1")
        self.at(1)
        self.play(FadeIn(m_flow, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m_card[0]), Indicate(card[0], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at_text("it stores", lead=0.3)
        self.play(FadeIn(m_card[1]), run_time=0.5)
        self.hold()

        m_cook = VGroup(T("the producer", 24, COOK), M("code in flow { }", 20, GREY_A)).arrange(DOWN, buff=0.08)
        m_cook.move_to([-4.6, -2.55, 0])
        m_diner = VGroup(T("the collector", 24, DINER), M("code in collect { }", 20, GREY_A)).arrange(DOWN, buff=0.08)
        m_diner.move_to([4.5, -2.55, 0])
        m_ask = VGroup(M("collect", 24, DINER), T("asks to be served", 22, GREY_A)).arrange(DOWN, buff=0.08)
        m_ask.next_to(diner, UP, buff=0.3)
        walk = Arrow([-3.1, -0.55, 0], [2.6, -0.55, 0], buff=0, stroke_width=4, color=EMIT, max_tip_length_to_length_ratio=0.04)
        m_emit = VGroup(M("emit(dish)", 24, EMIT), T("hands one dish to the diner", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        m_emit.next_to(walk, DOWN, buff=0.18)
        self.say("map2")
        self.play(FadeIn(m_cook), Indicate(cook, color=COOK), run_time=0.8)
        self.at(1)
        self.play(FadeIn(m_diner), Indicate(diner, color=DINER), run_time=0.8)
        self.at(2)
        self.play(FadeIn(m_ask, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(walk), FadeIn(m_emit), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= DinnerOrder: predict the print order =================
        CK, ET, RT, GR = COOK, DINER, EMIT, GREY_A

        def printout(rows, title, x, title_color=WHITE):
            hd = T(title, 26, title_color)
            ls = VGroup(*[M(s, 22, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            g = VGroup(hd, ls).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
            g.move_to([x, 0, 0]).align_to([0, 2.15, 0], UP)
            return g

        kinds = VGroup(M("cook    soup", 24, CK), M("eat     soup", 24, ET), M("emit(soup) returned", 24, RT)).arrange(RIGHT, buff=0.7)
        kinds.move_to([0, 3.05, 0])
        self.say("order_q")
        self.at(1)
        self.play(FadeIn(kinds[0], shift=DOWN * 0.1), run_time=0.5)
        self.at_text("after each", lead=0.3)
        self.play(FadeIn(kinds[2], shift=DOWN * 0.1), run_time=0.5)
        self.at_text("and the", lead=0.3)
        self.play(FadeIn(kinds[1], shift=DOWN * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.2), edge=RIGHT)

        g1 = printout([("cook    soup", CK), ("cook    salad", CK), ("cook    roast", CK), ("eat     soup", ET),
                       ("eat     salad", ET), ("eat     roast", ET)], "guess 1: a shelf", -4.55)
        g2 = printout([("cook    soup", CK), ("emit(soup) returned", RT), ("eat     soup", ET), ("cook    salad", CK)],
                      "guess 2: hand over, walk off", -0.55)
        fit(g2, 3.6)
        x1, x2 = cross(g1[0], 0.18, 0.2), cross(g2[0], 0.18, 0.2)
        self.say("guess1")
        self.play(FadeIn(g1[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in g1[1]], lag_ratio=0.25), run_time=1.6)
        self.hold()
        self.say("guess2")
        self.play(FadeIn(g2[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in g2[1]], lag_ratio=0.25), run_time=1.2)
        self.hold()

        real_rows = [("flow built", GR)]
        for d in ("soup", "salad", "roast"):
            real_rows += [(f"cook    {d}", CK), (f"eat     {d}", ET), (f"emit({d}) returned", RT)]
        real_rows.append(("collect returned", GR))
        g3 = printout(real_rows, "what it really prints", 3.75, YELLOW_M)
        self.say("real")
        self.play(Create(x1), Create(x2), FadeIn(g3[0]), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in g3[1]], lag_ratio=0.15), run_time=2.2)
        self.at_text("flow built comes", lead=0.3)
        b1 = SurroundingRectangle(g3[1][0], buff=0.07, color=YELLOW_M, stroke_width=2.5)
        self.play(Create(b1), FadeOut(VGroup(g1, x1), shift=LEFT * 0.2), run_time=0.7)
        n1 = T("building the flow ran nothing", 24, YELLOW_M).move_to([-6.2, 1.6, 0], aligned_edge=LEFT)
        self.play(FadeIn(n1, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("And eat", lead=0.3)
        b2 = SurroundingRectangle(VGroup(g3[1][2], g3[1][3]), buff=0.07, color=DINER, stroke_width=2.5)
        self.play(Create(b2), FadeOut(VGroup(g2, x2), shift=LEFT * 0.2), run_time=0.7)
        n2 = VGroup(T("eat soup comes before emit(soup) returned:", 24, WHITE),
                    T("the diner ate inside emit", 24, DINER)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        n2.move_to([-6.2, 0.5, 0], aligned_edge=LEFT)
        self.at(2)
        self.play(FadeIn(n2, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        # cold: two diners, two dinners
        mini = recipe_card().scale(0.62).move_to([-5.0, -1.75, 0])
        d1 = person(DINER, 0.8).move_to([-1.25, -1.15, 0])
        d2 = person(DINER, 0.8).move_to([-1.25, -2.45, 0])
        a1 = Arrow(mini.get_right(), d1.get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a2 = Arrow(mini.get_right(), d2.get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        c1 = T("collect: from the top", 20, GREY_A).next_to(a1, UP, buff=0.02).shift(LEFT * 0.1)
        c2 = T("collect again: from the top", 20, GREY_A).next_to(a2, DOWN, buff=0.02).shift(LEFT * 0.1)
        coldw = VGroup(T("cold:", 26, YELLOW_M), T("no collect, no cooking", 26)).arrange(RIGHT, buff=0.2)
        coldw.move_to([-6.2, -0.45, 0], aligned_edge=LEFT)
        self.say("cold")
        self.play(Indicate(g3[1][0], color=YELLOW_M), FadeIn(coldw, shift=RIGHT * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(mini), FadeIn(d1), GrowArrow(a1), FadeIn(c1), run_time=0.8)
        self.play(FadeIn(d2), GrowArrow(a2), FadeIn(c2), run_time=0.8)
        self.at(3)
        self.play(Indicate(VGroup(d1, d2), color=DINER, scale_factor=1.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= no shelf: a plain call, and the boxes =================
        KX = 3.6                                     # the kitchen, on the right half
        stv2 = stove(0.85).move_to([KX - 2.35, -1.1, 0])
        tbl2 = table(2.2).move_to([KX + 1.65, -1.6, 0])
        din2 = person(DINER, 1.1).move_to([KX + 2.2, -0.95, 0])
        cook2 = person(COOK, 1.1).move_to([KX - 1.3, -1.05, 0])
        floor2 = Line([0.6, -1.98, 0], [6.4, -1.98, 0], stroke_width=1.5, color=GREY_D)
        bowl = dish("soup", 0.8).next_to(cook2, RIGHT, buff=0.08).shift(UP * 0.05)
        shelf = DashedVMobject(Rectangle(width=1.4, height=0.18), num_dashes=24).set_stroke(GREY_B, 2).move_to([KX + 0.25, 0.75, 0])
        shelf_l = T("no shelf", 22, GREY_B).next_to(shelf, UP, buff=0.15)
        counter = DashedVMobject(Rectangle(width=1.0, height=0.8), num_dashes=24).set_stroke(GREY_B, 2).move_to([KX + 0.05, -1.55, 0])
        counter_l = T("no counter", 22, GREY_B).next_to(counter, UP, buff=0.12)
        xs, xc = tick(False, 0.15).next_to(shelf, RIGHT, buff=0.15), tick(False, 0.15).next_to(counter_l, RIGHT, buff=0.12)
        self.say("noshelf")
        self.play(FadeIn(VGroup(floor2, stv2, tbl2, din2, cook2)), FadeIn(bowl), run_time=0.8)
        self.at(1)
        self.play(Create(counter), FadeIn(counter_l), Create(xc), run_time=0.7)
        self.play(Create(shelf), FadeIn(shelf_l), Create(xs), run_time=0.7)
        self.at(3)
        self.play(FadeOut(VGroup(counter, counter_l, xc, shelf, shelf_l, xs)), run_time=0.5)
        self.play(VGroup(cook2, bowl).animate.shift(RIGHT * 2.0), run_time=1.0)
        self.play(bowl.animate.move_to(tbl2[0].get_center() + RIGHT * 0.15 + UP * 0.2), run_time=0.7)
        self.hold()

        call_t = VGroup(M("emit(dish)", 26, EMIT), T("is a plain function call into the collector", 26)).arrange(RIGHT, buff=0.2)
        call_t.move_to([0, 3.15, 0])
        fit(call_t, 12.4)
        self.say("call")
        self.play(FadeIn(call_t, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        # the nested boxes, on the left half
        L, R, Tp, B = -6.4, -0.3, 2.55, -3.25
        bx = [nest(L, R, Tp, B, GREY_B, "main calls collect"),
              nest(L + 0.25, R - 0.25, Tp - 0.6, B + 0.2, COOK, "the flow { } block: the cook"),
              nest(L + 0.5, R - 0.5, Tp - 1.2, B + 0.4, EMIT, "emit(soup): her walk to the table"),
              nest(L + 0.75, R - 0.75, Tp - 1.8, B + 0.6, DINER, "your collect lambda: the diner")]
        eat = M("eat(soup)", 24, SOUP).move_to([(L + R) / 2, -1.05, 0])
        closes = T("emit returns when this box closes", 22, GREY_A).move_to([(L + R) / 2, -1.85, 0])
        self.say("stack")
        self.play(FadeIn(bx[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bx[1]), Indicate(cook2, color=COOK), run_time=0.7)
        self.at(3)
        self.play(FadeIn(bx[2]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(bx[3]), Indicate(din2, color=DINER), run_time=0.7)
        self.play(FadeIn(eat), run_time=0.5)
        self.hold()

        one = T("one thread, one call stack", 26, YELLOW_M).move_to([KX + 0.2, 1.3, 0])
        here = T("still inside emit", 24, EMIT).next_to(cook2, UP, buff=0.3)
        self.say("stack2")
        self.play(FadeIn(one, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(closes), Indicate(bx[3][0], color=DINER, scale_factor=1.02), run_time=0.9)
        self.at(2)
        self.play(FadeIn(here, shift=DOWN * 0.1), Indicate(cook2, color=COOK), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the numbers: 100 ms to cook, 300 to eat =================
        CY, DY, AY = 0.75, -0.25, -1.1
        head = VGroup(person(COOK, 0.75), T("100 ms to cook a dish", 26, COOK), person(DINER, 0.75),
                      T("300 ms to eat it", 26, DINER)).arrange(RIGHT, buff=0.25)
        head[2].shift(RIGHT * 0.6)
        head[3].shift(RIGHT * 0.6)
        head.move_to([0, 3.05, 0])
        ax = axis(AY, [0, 100, 400, 500, 800, 900, 1200])
        rl = VGroup(T("cook", 24, COOK).move_to([tx(0) - 0.3, CY, 0], aligned_edge=RIGHT),
                    T("diner", 24, DINER).move_to([tx(0) - 0.3, DY, 0], aligned_edge=RIGHT))
        cooks = [bar(a, a + 100, CY, COOK) for a in (0, 400, 800)]
        waits = [bar(a, a + 300, CY, EMIT, k=0.18, label="at the table", tc=EMIT) for a in (100, 500, 900)]
        eats = [bar(a, a + 300, DY, DINER, label=f"eats the {d}") for a, d in ((100, "soup"), (500, "salad"), (900, "roast"))]

        def emark(ms, name):
            tri = Triangle(color=EMIT).set_fill(EMIT, 1).scale(0.09).rotate(PI).move_to([tx(ms), CY + 0.38, 0])
            t = M(f"emit({name})", 20, EMIT).next_to(tri, UP, buff=0.08)
            return VGroup(tri, t)

        em = [emark(100, "soup"), emark(500, "salad"), emark(900, "roast")]
        qq = VGroup(T("first emit at 100 ms.", 28), T("second emit at ?", 28, YELLOW_M)).arrange(RIGHT, buff=0.3)
        qq.move_to([0, -2.4, 0])
        self.say("time_q")
        self.play(FadeIn(head[:2]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(head[2:]), run_time=0.6)
        self.at(3)
        self.play(Create(ax), FadeIn(rl), FadeIn(cooks[0]), FadeIn(em[0]), run_time=0.9)
        self.at(4)
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)

        self.say("t1")
        self.play(FadeOut(qq), Indicate(em[0], color=EMIT), run_time=0.6)
        self.at_text("and stands", lead=0.3)
        self.play(GrowFromEdge(waits[0], LEFT), GrowFromEdge(eats[0], LEFT), run_time=1.6)
        self.at(1)
        ret = DashedLine([tx(400), CY + 0.3, 0], [tx(400), AY, 0], dash_length=0.08).set_stroke(EMIT, 2)
        ret_t = T("emit returns", 20, EMIT).next_to(ret, DOWN, buff=0.45)
        self.play(Create(ret), FadeIn(ret_t), run_time=0.6)
        self.hold()

        ghost = DashedLine([tx(200), CY + 0.35, 0], [tx(200), AY + 0.1, 0], dash_length=0.06).set_stroke(GREY_B, 2)
        ghost_t = T("200?", 24, GREY_B).move_to([tx(200), 1.95, 0])
        self.say("t2")
        self.play(FadeOut(ret_t), FadeIn(cooks[1]), run_time=0.6)
        self.play(FadeIn(em[1], shift=DOWN * 0.1), run_time=0.5)
        self.at_text("not 200", lead=0.3)
        self.play(Create(ghost), FadeIn(ghost_t), run_time=0.5)
        self.at(2)
        self.play(GrowFromEdge(waits[1], LEFT), GrowFromEdge(eats[1], LEFT), run_time=0.8)
        self.play(FadeIn(cooks[2]), FadeIn(em[2], shift=DOWN * 0.1), run_time=0.5)
        self.play(GrowFromEdge(waits[2], LEFT), GrowFromEdge(eats[2], LEFT), run_time=0.8)
        self.hold()

        gx = tick(False, 0.14).next_to(ghost_t, RIGHT, buff=0.1)
        qnote = T("a queue: the cook carries on", 22, GREY_B).move_to([tx(200) + 0.2, 1.55, 0], aligned_edge=LEFT)
        self.say("t200")
        self.play(FadeIn(qnote), run_time=0.5)
        self.at(1)
        self.play(Create(gx), FadeOut(qnote), FadeOut(ghost), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(ghost_t, gx, ret)), run_time=0.4)

        # ================= the rules, read off the picture =================
        r1 = VGroup(T("one at a time:", 26, YELLOW_M), T("the salad waits for", 26), M("emit(soup)", 24, EMIT),
                    T("to return", 26)).arrange(RIGHT, buff=0.18).move_to([0, -2.35, 0])
        fit(r1, 12.4)
        span = SurroundingRectangle(VGroup(waits[0], eats[0]), buff=0.06, color=YELLOW_M, stroke_width=2.5)
        self.say("seq")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Create(span), run_time=0.6)
        self.play(Indicate(cooks[1], color=COOK, scale_factor=1.1), run_time=0.8)
        self.hold()

        could = BraceBetweenPoints([tx(0), CY + 1.0, 0], [tx(100), CY + 1.0, 0], direction=UP, color=COOK)
        could_t = T("could: one every 100 ms", 22, COOK).next_to(could, UP, buff=0.08).shift(RIGHT * 0.6)
        does = BraceBetweenPoints([tx(100), -1.75, 0], [tx(500), -1.75, 0], direction=DOWN, color=YELLOW_M)
        does_t = T("does: one every 400 ms", 22, YELLOW_M).next_to(does, DOWN, buff=0.08)
        self.say("bp")
        self.play(FadeOut(r1), FadeOut(span), FadeOut(head), run_time=0.5)
        self.at(1)
        self.play(FadeIn(could), FadeIn(could_t), run_time=0.6)
        self.at(2)
        self.play(FadeIn(does), FadeIn(does_t), run_time=0.6)
        self.hold()

        bpn = VGroup(T("backpressure", 32, YELLOW_M),
                     T("a slow consumer slows the producer, so values don't pile up", 24, GREY_A)).arrange(DOWN, buff=0.12)
        bpn.move_to([1.6, -2.85, 0])
        fit(bpn, 7.6)
        self.say("bp_name")
        self.play(FadeOut(VGroup(could, could_t)), FadeIn(bpn[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bpn[1]), run_time=0.5)
        self.at(2)
        free = T("free: no extra machinery", 24, GREEN_M).move_to([0, 2.6, 0])
        self.play(FadeIn(free, shift=DOWN * 0.1), run_time=0.5)
        self.hold()

        three = VGroup(T("cold", 30, YELLOW_M), T("one at a time", 30, YELLOW_M), T("slowed by the diner", 30, YELLOW_M))
        three.arrange(RIGHT, buff=0.7).move_to([0, 2.95, 0])
        dots = VGroup(*[Dot(radius=0.05, color=GREY_B).move_to((three[i].get_right() + three[i + 1].get_left()) / 2) for i in range(2)])
        fact = VGroup(T("all from one fact:", 26), M("emit", 26, EMIT), T("is a plain call", 26)).arrange(RIGHT, buff=0.18)
        fact.move_to([0, 2.2, 0])
        self.say("three")
        self.play(FadeOut(free), FadeOut(VGroup(does, does_t, bpn)), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in three], lag_ratio=0.4), FadeIn(dots), run_time=1.4)
        self.at(1)
        self.play(FadeIn(fact, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the guardrail: free isn't fast =================
        tot = BraceBetweenPoints([tx(0), -1.75, 0], [tx(1200), -1.75, 0], direction=DOWN, color=WHITE)
        tot_t = T("plain flow: 1,200 ms", 24).next_to(tot, DOWN, buff=0.08)
        alone = bar(0, 900, -2.85, DINER, h=0.36, k=0.2, label="the diner alone: 900 ms", size=20, tc=DINER)
        add = VGroup(T("the times add up:", 26, YELLOW_M), T("100 + 300 for every dish", 26)).arrange(RIGHT, buff=0.2)
        add.move_to([0, 2.2, 0])
        self.say("cost")
        self.play(FadeOut(VGroup(three, dots, fact)), run_time=0.4)
        self.at_text("Three dishes", lead=0.3)
        self.play(FadeIn(tot), FadeIn(tot_t), run_time=0.6)
        self.at_text("where the slower", lead=0.3)
        self.play(GrowFromEdge(alone, LEFT), run_time=0.7)
        self.at(2)
        self.play(FadeIn(add, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        tmr = VGroup(Circle(radius=0.3).set_stroke(GREY_A, 3).set_fill(BLACK, 1),
                     Line(ORIGIN, UP * 0.2, stroke_width=3, color=GREY_A),
                     RoundedRectangle(corner_radius=0.03, width=0.16, height=0.1).set_stroke(GREY_A, 2))
        tmr[2].next_to(tmr[0], UP, buff=0)
        tmr.move_to([tx(250), CY + 1.05, 0])
        tbox = SurroundingRectangle(waits[0], buff=0.08, color=GREY_A, stroke_width=3)
        t_says = T("timer around emit: 300 ms", 22, GREY_A).next_to(tmr, RIGHT, buff=0.25)
        new_stove = VGroup(stove(0.5), T("faster stove?", 22, GREY_B)).arrange(RIGHT, buff=0.15).move_to([3.4, 2.75, 0])
        meas = T("it measures the diner", 24, DINER).next_to(t_says, DOWN, buff=0.12).align_to(t_says, LEFT)
        self.say("stove")
        self.play(FadeOut(add), FadeIn(tmr), Create(tbox), run_time=0.7)
        self.at_text("It says", lead=0.3)
        self.play(FadeIn(t_says), run_time=0.5)
        self.at_text("so she goes", lead=0.3)
        self.play(FadeIn(new_stove, shift=LEFT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(meas), Indicate(eats[0], color=DINER, scale_factor=1.05), run_time=0.8)
        self.at(3)
        sx = tick(False, 0.16).next_to(new_stove, RIGHT, buff=0.15)
        self.play(Create(sx), run_time=0.5)
        self.hold()

        sh = VGroup(T("a shelf between kitchen and table:", 26), M("buffer", 26, YELLOW_M),
                    T("(lesson 4, paid for in memory)", 24, GREY_B)).arrange(RIGHT, buff=0.2)
        sh.move_to([0, 2.2, 0])
        fit(sh, 12.4)
        self.say("shelf")
        self.play(FadeOut(VGroup(tmr, tbox, t_says, meas, new_stove, sx)), run_time=0.5)
        self.play(FadeIn(sh, shift=DOWN * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= where the picture breaks =================
        lc = person(COOK, 1.1).move_to([-4.6, 0.15, 0])
        lt = table(1.8).move_to([-3.1, -0.55, 0])
        ld = person(DINER, 1.1).move_to([-2.6, 0.15, 0])
        lstove = stove(0.75).move_to([-5.4, -2.2, 0])
        lost = VGroup(T("a real cook at the table", 26, COOK), T("is lost to the kitchen", 26, GREY_A)).arrange(DOWN, buff=0.1)
        lost.move_to([-3.6, 2.3, 0])
        cold_st = T("the stove stands idle", 22, GREY_B).next_to(lstove, RIGHT, buff=0.3)
        divider = DashedLine([0, 2.9, 0], [0, -3.0, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        rt = VGroup(T("a paused coroutine", 26, EMIT), T("holds no thread", 26, GREY_A)).arrange(DOWN, buff=0.1)
        rt.move_to([3.4, 2.3, 0])
        self.say("breaks")
        self.play(FadeIn(VGroup(lc, lt, ld)), FadeIn(lost), run_time=0.8)
        self.at(1)
        self.play(FadeIn(lstove), FadeIn(cold_st), run_time=0.6)
        self.at(2)
        self.play(Create(divider), FadeIn(rt), run_time=0.7)
        self.hold()

        dinner = RoundedRectangle(corner_radius=0.12, width=2.4, height=1.1).set_stroke(EMIT, 2.5).set_fill(dim(EMIT, 0.15), 1)
        dinner.move_to([1.9, 0.5, 0])
        dinner_t = VGroup(T("this dinner", 22, EMIT), T("waits on delay", 20, GREY_A)).arrange(DOWN, buff=0.08).move_to(dinner)
        thread = VGroup(Circle(radius=0.32).set_stroke(GREY_A, 3).set_fill(GREY_E, 1), T("thread", 20, GREY_A))
        thread[1].next_to(thread[0], DOWN, buff=0.1)
        thread.move_to([3.4, -1.2, 0])
        others = VGroup(*[RoundedRectangle(corner_radius=0.1, width=1.3, height=0.6).set_stroke(GREEN_M, 2).set_fill(dim(GREEN_M, 0.15), 1)
                          for _ in range(3)]).arrange(DOWN, buff=0.15).move_to([5.6, -0.5, 0])
        others_t = T("other coroutines", 22, GREEN_M).next_to(others, DOWN, buff=0.15)
        held = T("only this one dinner is held up", 24, YELLOW_M).move_to([3.3, -2.9, 0])
        self.say("breaks2")
        self.play(FadeIn(dinner), FadeIn(dinner_t), FadeIn(thread), run_time=0.7)
        self.at_text("the thread goes", lead=0.3)
        self.play(FadeIn(others), FadeIn(others_t), run_time=0.5)
        self.play(thread.animate.move_to([5.6, 1.15, 0]), run_time=0.8)
        self.play(thread.animate.move_to([5.6, -0.5, 0]).set_opacity(1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(held, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code, last =================
        khl = {"emit(dish)": EMIT, "// the diner eats in here": DINER, "flow": COOK, "collect": DINER}
        k = code_block(["flow {", "    for (dish in card) {", "        println(\"cook $dish\")",
                        "        emit(dish)     // the diner eats in here", "        println(\"emit($dish) returned\")",
                        "    }", "}.collect { dish -> println(\"eat $dish\") }"], 22, khl)
        jhl = {"diner.accept(dish);": EMIT, "// the diner eats in here": DINER}
        j = code_block(["for (String dish : card) {", "    System.out.println(\"cook \" + dish);",
                        "    diner.accept(dish);      // the diner eats in here",
                        "    System.out.println(\"accept(\" + dish + \") returned\");", "}"], 22, jhl)
        kcol = VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        jcol = VGroup(T("Java: no Flow, so the diner is a Consumer<String>", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(kcol, jcol).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(kcol, shift=UP * 0.1), run_time=0.8)
        self.at_text("emit sits", lead=0.3)
        self.play(Circumscribe(k[3], color=EMIT, buff=0.06), run_time=1.0)
        self.at(1)
        self.play(FadeIn(jcol, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Circumscribe(j[2], color=EMIT, buff=0.06), run_time=1.0)
        self.play(Indicate(j[3], color=EMIT, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does the cook put the soup down? No: there's nowhere to put it.", 32).move_to(UP * 2.5)
        m1 = T("A plain flow is one call stack. The collector runs inside emit.", 32, EMIT).move_to(UP * 1.65)
        m2 = T("Cold, one dish at a time, at the speed of its diner.", 32, YELLOW_M).move_to(UP * 0.85)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("50 ms to cook, 200 ms to eat, no buffer.", 28)).arrange(RIGHT, buff=0.25)
        qb = T("How long do four dishes take?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("1,000 ms: each dish costs 50 + 200, the cook waits inside emit", 30, YELLOW_M).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
