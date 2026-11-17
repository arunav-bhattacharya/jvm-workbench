from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\btoList\b", "to list"),
    (r"\bflowOn\b", "flow on"), (r"\bonCompletion\b", "on completion"), (r"\bwithContext\b", "with context"),
    (r"\btake\(3\)", "take three"), (r"\breadLine\b", "read line"), (r"\bIllegalStateException\b", "Illegal State Exception"),
    (r"\bIOException\b", "I O Exception"), (r"\bDefaultDispatcher-worker-1\b", "Default Dispatcher worker 1"),
    (r"\bABORTED\b", "aborted"), (r"\bDispatchers\.IO\b", "Dispatchers dot I O"),
]

# every spoken line, in order
N = {
    "open": "Here's one line of Kotlin. aisle returns a Flow, a stream of values that arrive one at a time: here, the "
            "fruit in one aisle of a grocer's online shop.",
    "shy": "So here's a question that's easy to be shy about. When this line returns, has the shop sent anything yet? "
           "And if two readers use the same flow, do they share what came back?",
    "card": "Let's step into the kitchen. A recipe card for lemon cake cooks nothing. It can sit in a drawer for a year, "
            "and the kitchen stays spotless.",
    "card2": "Only when somebody cooks from it does anything happen, from the top, one step at a time. And if two people "
             "cook from one card, every step happens twice: two cakes.",
    "map": "Let's map it. The card is the flow, and writing it is calling aisle. Cooking from it is collecting, with "
           "collect or toList. And each person cooking is a collector, with a run of their own.",
    "shrink": "Now shrink the shop: three pages, two items on each. For every page, the flow prints fetching, gets the "
              "page, and calls emit for each item, which hands it to the collector.",
    "build": "First we build the flow. It prints building, then built, and nothing else. The shop hasn't heard a thing.",
    "twice_q": "Now we collect it twice. How many pages does the shop send in all?",
    "twice_a": "Six. The first collect fetches pages 0, 1 and 2, and the second starts again from the top. Two cooks, "
               "one card, two cakes.",
    "take_q": "Now take(3), which collects only the first three items. How many pages?",
    "take_a": "Two. The third item, cherries, is on page 1. Once take has three, it cancels the flow, so page 2 is never "
              "asked for. Nobody wanted the figs and grapes, so nobody fetched them.",
    "name": "A flow like this is called cold. Building it runs nothing. Each collector runs it again, from the top.",
    "breaks": "Here the picture breaks. In a kitchen, a second cake is a treat. A second run of a flow is just another "
              "trip to the shop, and nothing warns you. Sharing one run is the next lesson.",
    "steps": "Flows have more steps, like recipes. filter and map are intermediate operators: each one returns a new flow "
             "at once and runs nothing. It only writes a line on the card.",
    "scale": "Let's run some steps. The kitchen scale sends 250 grams, minus 40, because nobody zeroed it, and 1,200. "
             "filter keeps the positive ones, and map turns grams into kilograms.",
    "scale_q": "Which line prints first: emit minus 40, or collect 0.25 kilograms?",
    "scale_a": "collect 0.25 kilograms. The first weight goes all the way down before the second is emitted, and minus 40 "
               "stops at the filter. No queues between the steps, and no extra threads.",
    "terminal": "The steps that cook are terminal operators, such as collect, toList and first. They start the flow and "
                "read it to the end. Intermediate steps write. Terminal ones cook.",
    "note": "So far every step ran on the collector's thread. Now a delivery note arrives, one line per item, and the old "
            "reader's readLine blocks, holding its thread. That belongs on the bench by the front door, Dispatchers.IO.",
    "wrong": "The obvious fix is withContext around the emit. Run it, and the flow throws IllegalStateException: Flow "
             "invariant is violated.",
    "wrongjoke": "It has a point. emit runs the collector's own code, so the collector would be dragged to the bench too. "
                 "It's like reading the note on the bench, and making the whole family eat dinner out there with you.",
    "flowon": "The tool is flowOn. Everything above it, the upstream, runs at the bench in a second coroutine, with a "
              "shelf of up to 64 lines between the halves. Everything below it stays put.",
    "flowon_show": "The demo prints each step's thread. read and parse ran on DefaultDispatcher-worker-1, at the bench. "
                   "format and save stayed on main. The collector never moves.",
    "catch": "Last: what if a step fails? catch is a net under the steps above it: whatever falls from up there lands "
             "in it. onCompletion is the flow's finally. It runs once, however the flow ends.",
    "torn": "Tear the note after two lines. onCompletion prints the cause, IOException: delivery note torn. catch emits "
            "ABORTED, the collector gets it, and collect returns normally.",
    "shelf_q": "Now the note is whole, but saving the eggs fails in the collector: the pantry shelf is full. Does catch "
               "see it?",
    "shelf_a": "No. The failure was below catch, so it went straight to the code that called collect. onCompletion saw "
               "it pass, because it sees every ending.",
    "shelf_joke": "A net under the stove can't catch a plate dropped in the dining room. So put work that may fail above "
                  "catch, and never put a try around emit, which runs the collector's code too.",
    "code": "Here it all is in Kotlin, and in Java with a Reactor Flux, which is cold in the same way.",
    "moral": "So, has the shop sent anything when the line returns? Not until someone collects, and every collector cooks "
             "from the top. Steps write on the card, the terminal one cooks, flowOn moves the steps above it, catch "
             "catches what falls from above, and onCompletion sees every ending.",
    "check": "Quick check. flow A, map B, flowOn IO, filter C, collect D, collected on main. Where does each one run?",
    "check_a": "A and B on IO, above flowOn. C and D stay on main, with the collector.",
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


# one colour per thing, for the whole coroutines track (the cook is blue, as in co-01 to co-06)
COOK, COOK2, COOK3, SHOP, MARK, CANCEL, BAD, IOC, CPU, CAKE = (BLUE_M, TEAL_M, GREEN_M, GOLD_M, YELLOW_M, YELLOW_M,
                                                               RED_M, GOLD_M, TEAL_M, GOLD_M)


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def bookmark_tab(color=MARK, w=0.7, h=0.3):
    pts = [[-w / 2, h / 2, 0], [w / 2 - 0.14, h / 2, 0], [w / 2, 0, 0], [w / 2 - 0.14, -h / 2, 0], [-w / 2, -h / 2, 0]]
    return Polygon(*pts).set_stroke(color, 2.5).set_fill(dim(color, 0.45), 1).set_z_index(5)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def chip_t(text, color, size=22, mono=True):
    t = (M if mono else T)(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.46).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def recipe_card(title, steps, w=4.3, size=24, mono_title=False, numbered=True, gap=0.3):
    head = (M if mono_title else T)(title, 28)
    rows = VGroup(*[T((f"{i + 1}   " if numbered else "") + s, size, GREY_A) for i, s in enumerate(steps)])
    rows.arrange(DOWN, aligned_edge=LEFT, buff=gap)
    h = head.height + rows.height + 1.0
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(GREY_A, 2.5).set_fill("#151515", 1)
    head.move_to(r.get_top() + DOWN * 0.45)
    rows.next_to(head, DOWN, buff=0.35)
    rows.align_to(r.get_left() + RIGHT * 0.35, LEFT)
    rule = Line(LEFT * (w / 2 - 0.3), RIGHT * (w / 2 - 0.3), stroke_width=1.5, color=GREY_D).next_to(head, DOWN, buff=0.15)
    return VGroup(r, head, rule, rows)


def cake(s=1.0):
    base = RoundedRectangle(corner_radius=0.06, width=1.0, height=0.36).set_stroke(CAKE, 3).set_fill(dim(CAKE, 0.4), 1)
    top = RoundedRectangle(corner_radius=0.06, width=0.74, height=0.28).set_stroke(CAKE, 3).set_fill(dim(CAKE, 0.55), 1)
    top.next_to(base, UP, buff=0)
    icing = Line(LEFT * 0.37, RIGHT * 0.37, stroke_width=4, color=WHITE).move_to(top.get_top())
    cherry = Circle(radius=0.07).set_stroke(RED_M, 2).set_fill(RED_M, 1).next_to(top, UP, buff=0.0)
    return VGroup(base, top, icing, cherry).scale(s)


def drawer_icon():
    front = RoundedRectangle(corner_radius=0.06, width=4.6, height=0.95).set_stroke(GREY_B, 2.5).set_fill("#101010", 1)
    handle = RoundedRectangle(corner_radius=0.05, width=0.9, height=0.16).set_stroke(GREY_B, 2).set_fill(GREY_D, 1)
    return VGroup(front, handle.move_to(front)).set_z_index(4)


def shop_icon(s=1.0, color=SHOP):
    body = Rectangle(width=1.8, height=1.1).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    stripes = VGroup(*[Polygon([x, 0, 0], [x + 0.3, 0, 0], [x + 0.3, -0.32, 0], [x, -0.32, 0])
                       .set_stroke(color, 2).set_fill(dim(color, 0.6 if i % 2 == 0 else 0.2), 1)
                       for i, x in enumerate(np.arange(-1.05, 0.95, 0.3))])
    stripes.next_to(body, UP, buff=0)
    door = Rectangle(width=0.42, height=0.62).set_stroke(color, 2.5).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.31)
    win = Rectangle(width=0.5, height=0.36).set_stroke(color, 2).set_fill(dim(BLUE_M, 0.25), 1).move_to(body.get_center() + LEFT * 0.52 + UP * 0.12)
    return VGroup(body, stripes, door, win).scale(s)


def page_card(i, items, w=2.45):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=1.15).set_stroke(SHOP, 2.5).set_fill(dim(SHOP, 0.1), 1)
    h = T(f"page {i}", 22, SHOP).move_to(r.get_top() + DOWN * 0.3)
    it = T(", ".join(items), 22, GREY_A).move_to(r.get_center() + DOWN * 0.2)
    return VGroup(r, h, it)


def note_icon(s=1.0, color=GREY_A):
    r = Polygon([-0.32, 0.42, 0], [0.18, 0.42, 0], [0.32, 0.28, 0], [0.32, -0.42, 0], [-0.32, -0.42, 0])
    r.set_stroke(color, 2.2).set_fill("#151515", 1)
    rows = VGroup(*[Line(LEFT * 0.2, RIGHT * 0.2, stroke_width=1.8, color=GREY_B) for _ in range(4)]).arrange(DOWN, buff=0.12)
    return VGroup(r, rows.move_to(r)).scale(s).set_z_index(6)


def call_chip(color=IOC, s=0.36):
    """A blocking call: a small square with an hourglass (as in co-04)."""
    sq = RoundedRectangle(corner_radius=0.05, width=s, height=s).set_stroke(color, 2.2).set_fill(dim(color, 0.3), 1)
    k = s * 0.28
    glass = VGroup(Polygon([-k, k, 0], [k, k, 0], [0, 0, 0]), Polygon([-k, -k, 0], [k, -k, 0], [0, 0, 0]))
    glass.set_stroke(color, 1.6).set_fill(dim(color, 0.7), 1)
    return VGroup(sq, glass.move_to(sq)).set_z_index(7)


def screen_icon(color=GREY_A):
    r = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.72).set_stroke(color, 2.5).set_fill("#121212", 1)
    st = Line(DOWN * 0.36, DOWN * 0.52, stroke_width=3, color=color)
    ft = Line(LEFT * 0.22, RIGHT * 0.22, stroke_width=3, color=color).move_to(DOWN * 0.52)
    return VGroup(r, st, ft)


def op_box(name, gloss, color, w=3.9, h=0.82):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    n = M(name, 24, color)
    g = T(gloss, 22, GREY_A)
    VGroup(n, g).arrange(RIGHT, buff=0.3).move_to(r)
    return VGroup(r, n, g)


# the kitchen from co-04, as it sits on screen
CTR_TOP = -0.1
HELP_Y = 0.42
BENCH_X0, BENCH_X1, SEAT_Y = 1.1, 4.6, -0.75
DOOR_P = np.array([5.75, 0.15, 0])


def kitchen():
    ctr = Rectangle(width=5.3, height=0.5).set_stroke(CPU, 3).set_fill(dim(CPU, 0.12), 1).move_to([-3.55, CTR_TOP - 0.25, 0])
    boards = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.95, height=0.16).set_stroke(CPU, 2.5)
                      .set_fill(dim(CPU, 0.4), 1).move_to([x, CTR_TOP + 0.08, 0]) for x in (-5.5, -4.2, -2.9, -1.6)])
    plank = Rectangle(width=BENCH_X1 - BENCH_X0, height=0.14).set_stroke(IOC, 3).set_fill(dim(IOC, 0.35), 1)
    plank.move_to([(BENCH_X0 + BENCH_X1) / 2, SEAT_Y, 0])
    legs = VGroup(*[Line([x, SEAT_Y - 0.07, 0], [x, SEAT_Y - 0.42, 0], stroke_width=4, color=IOC)
                    for x in (BENCH_X0 + 0.2, BENCH_X1 - 0.2)])
    bench = VGroup(plank, legs)
    dr = Rectangle(width=1.15, height=2.5).set_stroke(GREY_A, 3).set_fill(GREY_E, 1).move_to(DOOR_P)
    win = Rectangle(width=0.6, height=0.5).set_stroke(GREY_B, 2).set_fill(dim(BLUE_M, 0.25), 1).move_to(DOOR_P + UP * 0.75)
    knob = Dot(DOOR_P + LEFT * 0.38 + DOWN * 0.15, radius=0.06, color=GREY_A)
    door = VGroup(dr, win, knob)
    return ctr, boards, bench, door


def seated(x, color=COOK):
    return person(color, 1.0).move_to([x, SEAT_Y + 0.07 + 0.38, 0])


def dining_table(w=2.6):
    top = Rectangle(width=w, height=0.14).set_stroke(GREY_A, 3).set_fill(GREY_D, 1)
    legs = VGroup(*[Line(UP * 0, DOWN * 0.5, stroke_width=4, color=GREY_A).move_to(top.get_bottom() + DOWN * 0.25 + RIGHT * dx)
                    for dx in (-w / 2 + 0.2, w / 2 - 0.2)])
    plate = Ellipse(width=0.5, height=0.12).set_stroke(WHITE, 2).set_fill(GREY_E, 1).next_to(top, UP, buff=0.0)
    return VGroup(top, legs)


class Console:
    """Printed lines, one under the other; leading spaces kept (Text drops them)."""

    def __init__(self, x0, y0, size=22, step=0.42):
        self.x0, self.y0, self.size, self.step = x0, y0, size, step
        self.cw = M("0123456789", size).width / 10
        self.lines = []

    def line(self, text, color=WHITE, t2c=None):
        n = len(text) - len(text.lstrip())
        m = M(text.strip(), self.size, color, t2c=t2c or {})
        m.move_to([self.x0 + n * self.cw, self.y0 - len(self.lines) * self.step, 0], aligned_edge=LEFT)
        self.lines.append(m)
        return m

    def clear(self):
        g = VGroup(*self.lines)
        self.lines = []
        return g


class Co07ColdFlow(Narrated):
    """co-07, section 0 (a short tour of the whole lesson): has anything been fetched when a flow is built? The recipe
    card that cooks nothing, two cooks and two cakes, mapped; the grocer's aisle of three pages (build prints nothing,
    two collects fetch six pages, take(3) fetches two); cold, named, and where the picture breaks; the kitchen scale
    through filter and map, one value at a time; terminal operators cook; the delivery note on the bench by the front
    door, withContext around emit refused, flowOn moving the upstream; catch as a net under the steps above it and
    onCompletion for every ending (torn note, full pantry shelf); the code; the moral and a check."""

    def construct(self):
        self.title_card("A recipe card cooks nothing", "cold flows, their steps, flowOn and catch")

        # ================= hook =================
        hook = VGroup(M('val fruit = aisle("fruit")', 32), M("// returns a Flow<String>", 26, GREY_B))
        hook.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-2.4, 1.5, 0])
        shop = shop_icon(1.1).move_to([4.2, 1.5, 0])
        shop_l = T("the grocer's online shop", 24, SHOP).next_to(shop, DOWN, buff=0.25)
        self.say("open")
        self.play(FadeIn(hook, shift=UP * 0.1), run_time=0.8)
        self.at_text("the fruit", lead=0.4)
        self.play(FadeIn(shop), FadeIn(shop_l), run_time=0.7)
        self.hold()

        q1 = T("When this line returns, has the shop sent anything yet?", 30).move_to([0, -1.25, 0])
        q2 = T("Do two readers of the same flow share what came back?", 30).move_to([0, -2.15, 0])
        self.say("shy")
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(hook, shop, shop_l, q1, q2)), run_time=0.6)

        # ================= the recipe card =================
        card = recipe_card("Lemon cake", ["cream the butter", "beat in two eggs", "fold in the flour",
                                          "bake for 40 minutes"]).move_to([0, 0.75, 0])
        home = card.get_center().copy()
        drawer = drawer_icon().move_to([0, -2.6, 0])
        spot = T("a year later: nothing cooked, not one crumb", 26, GREY_B).move_to([0, -1.55, 0])
        self.say("card")
        self.play(FadeIn(card, shift=DOWN * 0.1), run_time=0.8)
        self.at_text("It can sit", lead=0.3)
        self.play(FadeIn(drawer), run_time=0.4)
        self.play(card.animate.scale(0.22).move_to(drawer.get_center() + UP * 0.05), run_time=0.9)
        self.remove(card)
        self.at_text("and the kitchen", lead=0.4)
        self.play(FadeIn(spot, shift=UP * 0.1), run_time=0.6)
        self.hold()

        card.scale(1 / 0.22).move_to(home)
        rows = card[3]
        ck1 = person(COOK, 1.3).move_to([-4.9, 1.0, 0])
        ck2 = person(COOK2, 1.3).move_to([4.9, 1.0, 0])
        cl = card[0].get_left()[0]
        cr = card[0].get_right()[0]
        tab1 = bookmark_tab(MARK).move_to([cl - 0.45, rows[0].get_y(), 0])
        tab2 = bookmark_tab(MARK).rotate(PI).move_to([cr + 0.45, rows[0].get_y(), 0])
        k1 = cake(1.1).move_to([-4.9, -0.75, 0])
        k2 = cake(1.1).move_to([4.9, -0.75, 0])
        self.say("card2")
        self.play(FadeOut(spot), FadeOut(drawer), FadeIn(card, shift=UP * 0.2), run_time=0.8)
        self.at_text("from the top", lead=0.5)
        self.play(FadeIn(ck1), FadeIn(tab1, shift=RIGHT * 0.2), run_time=0.5)
        for i in range(1, 4):
            self.play(tab1.animate.move_to([cl - 0.45, rows[i].get_y(), 0]), run_time=0.4)
        self.play(FadeIn(k1, shift=UP * 0.15), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ck2), FadeIn(tab2, shift=LEFT * 0.2), run_time=0.5)
        for i in range(1, 4):
            self.play(tab2.animate.move_to([cr + 0.45, rows[i].get_y(), 0]), run_time=0.35)
        self.play(FadeIn(k2, shift=UP * 0.15), run_time=0.5)
        self.hold()

        # map it
        mp = [("the card", M("a Flow", 26)),
              ("writing it", M('calling aisle("fruit")', 26)),
              ("cooking from it", M("collect, toList", 26, COOK3)),
              ("each cook", T("a collector, with its own run", 26, COOK))]
        MX, MY = -1.95, (1.85, 0.85, -0.15, -1.15)
        mrows = []
        for (a, b), y in zip(mp, MY):
            ta = T(a, 26, GREY_A).move_to([MX, y, 0], aligned_edge=LEFT)
            ar = Arrow([MX + 2.6, y, 0], [MX + 3.2, y, 0], buff=0, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.35)
            b.move_to([MX + 3.4, y, 0], aligned_edge=LEFT)
            mrows.append(VGroup(ta, ar, b))
        self.say("map")
        self.play(FadeOut(VGroup(ck1, ck2, tab1, tab2, k1, k2)), card.animate.move_to([-4.35, 0.35, 0]), run_time=0.8)
        for key, row in zip(("The card", "writing it", "Cooking from", "each person"), mrows):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(row, shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(card, *mrows)), run_time=0.6)

        # ================= the aisle: shrink, predict, show =================
        acard = recipe_card('aisle("fruit")', ["for each page:", "print fetching", "get the page", "emit each item"],
                            w=3.2, size=22, mono_title=True, numbered=False, gap=0.22)
        acard.move_to([-4.9, 1.85, 0])
        ar_rows = acard[3]
        for i in (1, 2, 3):
            ar_rows[i].shift(RIGHT * 0.25)
        PX, PY = (-0.3, 2.25, 4.8), 2.05
        pages = [page_card(0, ["apples", "bananas"]), page_card(1, ["cherries", "dates"]), page_card(2, ["figs", "grapes"])]
        for p, x in zip(pages, PX):
            p.move_to([x, PY, 0])
        shop_t = T("the shop's fruit aisle", 24, SHOP).move_to([PX[0] - 1.2, 3.1, 0], aligned_edge=LEFT)
        items_of = [["apples", "bananas"], ["cherries", "dates"], ["figs", "grapes"]]
        cnt = {"n": 0, "m": None}

        def count_m(n, color=SHOP):
            return T(f"pages fetched: {n}", 26, color).move_to([6.0, 3.1, 0], aligned_edge=RIGHT)

        cnt["m"] = count_m(0)
        con_box = RoundedRectangle(corner_radius=0.1, width=13.0, height=3.3).set_stroke(GREY_D, 2).set_fill("#080808", 1)
        con_box.move_to([0, -1.6, 0])
        con = Console(-6.2, -0.25, 22, 0.42)
        CL_X, CL_Y = -2.55, 0.7
        self.say("shrink")
        self.play(FadeIn(acard), run_time=0.7)
        self.at_text("three pages", lead=0.3)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in pages], lag_ratio=0.25), FadeIn(shop_t), run_time=1.0)
        self.play(FadeIn(cnt["m"]), run_time=0.4)
        self.at_text("For every page", lead=0.3)
        self.play(Indicate(ar_rows[1], color=WHITE), run_time=0.6)
        self.play(Indicate(ar_rows[2], color=SHOP), run_time=0.6)
        self.play(Indicate(ar_rows[3], color=COOK), run_time=0.6)
        self.hold()

        self.say("build")
        self.play(FadeIn(con_box), run_time=0.4)
        self.play(FadeIn(con.line("building the flow")), run_time=0.4)
        self.at_text("then built", lead=0.3)
        self.play(FadeIn(con.line("built; nothing fetched yet")), run_time=0.4)
        self.at(2)
        self.play(Indicate(cnt["m"], color=SHOP), run_time=0.8)
        self.hold()

        def bump(color=SHOP):
            cnt["n"] += 1
            new = count_m(cnt["n"], color)
            old = cnt["m"]
            cnt["m"] = new
            return [FadeOut(old, shift=UP * 0.1), FadeIn(new, shift=UP * 0.1)]

        def fetch(i, coll, color, rt=1.0, items=2):
            """The body fetches page i (a dot runs to the page), prints, then emits the items to the collector."""
            start = np.array([acard[0].get_right()[0] + 0.05, ar_rows[2].get_y(), 0])
            y_run = 1.3
            path = VMobject().set_points_as_corners([start, [start[0] + 0.3, y_run, 0], [PX[i], y_run, 0],
                                                     [PX[i], PY - 0.6, 0]])
            d = Dot(radius=0.09, color=SHOP).move_to(start).set_z_index(8)
            self.add(d)
            self.play(MoveAlongPath(d, path), run_time=0.45 * rt)
            self.remove(d)
            ln = con.line(f"  fetching page {i} of the fruit aisle", GREY_A)
            self.play(Indicate(pages[i][1], color=WHITE), FadeIn(ln), *bump(), run_time=0.4 * rt)
            chips = VGroup(*[chip_t(n, color, 22, mono=False) for n in items_of[i][:items]]).arrange(RIGHT, buff=0.1)
            chips.move_to([PX[i], PY - 0.75, 0])
            self.play(FadeIn(chips, scale=0.8), run_time=0.2 * rt)
            self.play(chips.animate.scale(0.5).move_to(coll.get_center()), run_time=0.45 * rt)
            self.play(FadeOut(chips, scale=0.5), Indicate(coll, color=color, scale_factor=1.1), run_time=0.25 * rt)

        coll1 = person(COOK, 1.15).move_to([CL_X, CL_Y, 0])
        self.say("twice_q")
        self.play(FadeIn(coll1), run_time=0.4)
        self.hold(after=0)
        self.predict(pos=(5.7, 0.62), edge=RIGHT)
        self.say("twice_a")
        self.play(FadeIn(con.line("first collect:", COOK)), run_time=0.3)
        for i in range(3):
            fetch(i, coll1, COOK, rt=0.75)
        got = "  got [apples, bananas, cherries, dates, figs, grapes]"
        self.play(FadeIn(con.line(got, COOK)), run_time=0.3)
        self.at_text("and the second", lead=0.2)
        coll2 = person(COOK2, 1.15).move_to([CL_X, CL_Y, 0])
        self.play(FadeOut(con.clear()), FadeOut(coll1), FadeIn(coll2), run_time=0.4)
        self.play(FadeIn(con.line("second collect:", COOK2)), run_time=0.25)
        for i in range(3):
            fetch(i, coll2, COOK2, rt=0.55)
        self.play(FadeIn(con.line(got, COOK2)), run_time=0.25)
        self.at_text("Two cooks", lead=0.3)
        six = SurroundingRectangle(cnt["m"], buff=0.1, color=SHOP, stroke_width=3)
        self.play(Create(six), run_time=0.5)
        self.hold()

        coll3 = person(COOK3, 1.15).move_to([CL_X, CL_Y, 0])
        self.say("take_q")
        cnt["n"] = -1
        self.play(FadeOut(six), FadeOut(con.clear()), FadeOut(coll2), FadeIn(coll3), *bump(), run_time=0.5)
        self.play(FadeIn(con.line("take(3):", COOK3)), run_time=0.3)
        self.hold(after=0)
        self.predict(pos=(5.7, 0.62), edge=RIGHT)
        self.say("take_a")
        fetch(0, coll3, COOK3, rt=0.8)
        fetch(1, coll3, COOK3, rt=0.8, items=1)
        self.play(FadeIn(con.line("  got [apples, bananas, cherries]", COOK3)), run_time=0.3)
        self.at_text("Once take", lead=0.3)
        stop = VGroup(T("cancel", 26, CANCEL), tick(False, 0.18).set_stroke(CANCEL, 5)).arrange(RIGHT, buff=0.15)
        stop.move_to([-2.45, 1.75, 0])
        self.play(FadeIn(stop, scale=0.8), Flash(coll3.get_top(), color=CANCEL, flash_radius=0.4), run_time=0.6)
        never = T("never fetched", 24, GREY_B).move_to([PX[2], PY - 0.85, 0])
        self.play(pages[2].animate.set_opacity(0.3), FadeIn(never), run_time=0.7)
        self.at_text("Nobody wanted", lead=0.3)
        self.play(Indicate(pages[2][2], color=WHITE), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        con.clear()

        # ================= name it, and where the picture breaks =================
        cold = T("cold", 56, COOK).move_to([0, 2.3, 0])
        r1 = T("Building a flow runs nothing.", 32).move_to([0, 1.25, 0])
        r2 = T("Each collector runs it again, from the top.", 32).move_to([0, 0.5, 0])
        self.say("name")
        self.play(Write(cold), run_time=0.9)
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        tr = cake(1.0).move_to([-3.6, -1.15, 0])
        tr_l = T("a second cake: a treat", 26, CAKE).next_to(tr, DOWN, buff=0.25)
        tp = shop_icon(0.6).move_to([3.6, -1.1, 0])
        tp_l = T("a second run: another trip", 26, SHOP).next_to(tp, DOWN, buff=0.25)
        self.say("breaks")
        self.at_text("In a kitchen", lead=0.3)
        self.play(FadeIn(tr), FadeIn(tr_l), run_time=0.6)
        self.at_text("A second run", lead=0.3)
        self.play(FadeIn(tp), FadeIn(tp_l), run_time=0.6)
        self.at_text("and nothing warns", lead=0.3)
        warn = T("nothing warns you", 28, BAD).move_to([0, -3.05, 0])
        self.play(FadeIn(warn), run_time=0.5)
        self.at_text("Sharing one run", lead=0.3)
        nxt = T("one run shared by many: the next lesson", 26, GREY_B).move_to([0, -3.05, 0])
        self.play(FadeOut(warn), FadeIn(nxt), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= steps on the card =================
        CX = -4.35
        src = op_box("flowOf", "250, -40, 1200 g", SHOP).move_to([CX, 2.55, 0])
        flt = op_box("filter", "keeps above 0", CPU).move_to([CX, 1.2, 0])
        mpb = op_box("map", "grams to kg", CPU).move_to([CX, -0.15, 0])
        col = op_box("collect", "the collector", COOK).move_to([CX, -1.5, 0])
        a1 = Arrow(src.get_bottom(), flt.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a2 = Arrow(flt.get_bottom(), mpb.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a3 = Arrow(mpb.get_bottom(), col.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        at_once = T("returns at once: nothing printed", 24, GREY_B).move_to([CX, -2.55, 0])
        con2 = Console(-1.1, 2.55, 22, 0.42)
        self.say("steps")
        self.play(FadeIn(src), run_time=0.5)
        self.at_text("filter and map", lead=0.3)
        self.play(GrowArrow(a1), Write(flt), run_time=0.7)
        self.play(GrowArrow(a2), Write(mpb), run_time=0.7)
        self.at_text("returns a new", lead=0.3)
        self.play(FadeIn(at_once), run_time=0.5)
        self.at_text("It only writes", lead=0.3)
        self.play(Indicate(flt[1], color=CPU), Indicate(mpb[1], color=CPU), run_time=0.9)
        self.hold()

        self.say("scale")
        self.play(Indicate(src[2], color=SHOP), run_time=0.8)
        self.at_text("filter keeps", lead=0.3)
        self.play(Indicate(VGroup(flt[1], flt[2]), color=CPU), run_time=0.6)
        self.play(Indicate(VGroup(mpb[1], mpb[2]), color=CPU), run_time=0.6)
        self.play(GrowArrow(a3), FadeIn(col), FadeOut(at_once), run_time=0.6)
        self.play(FadeIn(con2.line("pipeline built: no line above has printed yet", GREY_B)), run_time=0.4)
        self.hold()

        self.say("scale_q")
        self.hold(after=0)
        self.predict()

        def go(val, out=None):
            c = chip_t(str(val), SHOP).move_to(src.get_bottom() + DOWN * 0.05 + RIGHT * 1.55)
            ln = con2.line(f"emit    {val}", SHOP)
            self.play(FadeIn(c, scale=0.7), FadeIn(ln), run_time=0.35)
            self.play(c.animate.move_to(flt.get_right() + RIGHT * 0.4), run_time=0.4)
            if val < 0:
                self.play(c[0].animate.set_stroke(BAD).set_fill(dim(BAD, 0.35)), run_time=0.25)
                self.play(FadeOut(c, shift=RIGHT * 0.5 + DOWN * 0.2), run_time=0.35)
                return
            self.play(FadeIn(con2.line(f"  filter passed {val}", CPU)), Indicate(flt[1], color=CPU), run_time=0.35)
            self.play(c.animate.move_to(mpb.get_right() + RIGHT * 0.4), run_time=0.4)
            c2 = chip_t(out, COOK).move_to(c)
            self.play(ReplacementTransform(c, c2), FadeIn(con2.line(f"    map   -> {out}", CPU)), run_time=0.35)
            self.play(c2.animate.move_to(col.get_right() + RIGHT * 0.55), run_time=0.4)
            self.play(FadeIn(con2.line(f"      collect {out}", COOK)), FadeOut(c2, scale=0.6), run_time=0.35)

        self.say("scale_a")
        go(250, "0.25 kg")
        self.at_text("and minus 40", lead=0.3)
        go(-40)
        go(1200, "1.20 kg")
        self.at_text("No queues", lead=0.3)
        self.play(Indicate(VGroup(*con2.lines[1:5]), color=WHITE, scale_factor=1.02), run_time=0.9)
        self.hold()

        # terminal operators
        self.say("terminal")
        self.play(FadeOut(VGroup(*con2.clear())), run_time=0.4)
        iw = VGroup(T("intermediate: write a line", 28, CPU), M("map  filter  onEach  take", 26, CPU))
        tw = VGroup(T("terminal: cook", 28, COOK), M("collect  toList  first", 26, COOK))
        for g in (iw, tw):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        iw.move_to([-1.0, 1.4, 0], aligned_edge=LEFT)
        tw.move_to([-1.0, -0.3, 0], aligned_edge=LEFT)
        self.play(Indicate(col[1], color=COOK), run_time=0.7)
        self.play(FadeIn(tw, shift=LEFT * 0.1), run_time=0.6)
        self.at_text("Intermediate steps", lead=0.3)
        self.play(FadeIn(iw, shift=LEFT * 0.1), run_time=0.6)
        self.at_text("Terminal ones", lead=0.3)
        self.play(Circumscribe(tw, color=COOK, buff=0.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= flowOn: the bench by the front door =================
        ctr, boards, bench, door = kitchen()
        ctr_l = T("the counter", 24, CPU).move_to([-3.55, -0.95, 0])
        bch_l = T("the bench by the front door", 24, IOC).move_to([2.85, -1.6, 0])
        tbl = dining_table(2.6).move_to([-3.4, -2.55, 0]).set_z_index(3)
        fam = VGroup(person(COOK2, 0.95), person(COOK2, 0.95)).arrange(RIGHT, buff=0.7).move_to([-3.4, -1.85, 0])
        fam_l = T("the collector, at its own table", 24, COOK2).move_to([-3.4, -3.22, 0])
        rd = person(COOK, 1.0).move_to([-2.9, HELP_Y, 0])
        nt = note_icon(0.8).move_to([-2.15, 0.55, 0])
        blk = call_chip(IOC, 0.42).move_to([-2.9, 1.25, 0])
        blk_l = M("readLine blocks", 22, IOC).next_to(blk, RIGHT, buff=0.2)
        self.say("note")
        self.play(FadeIn(ctr), FadeIn(boards), FadeIn(ctr_l), FadeIn(tbl), FadeIn(fam), run_time=0.7)
        self.play(FadeIn(fam_l), run_time=0.4)
        self.at_text("Now a delivery", lead=0.3)
        self.play(FadeIn(rd), FadeIn(nt, shift=LEFT * 0.2), run_time=0.6)
        self.at_text("blocks", lead=0.3)
        self.play(FadeIn(blk, scale=0.7), FadeIn(blk_l), run_time=0.5)
        self.at_text("That belongs", lead=0.3)
        self.play(FadeIn(bench), FadeIn(door), FadeIn(bch_l), run_time=0.7)
        io_l = M("Dispatchers.IO", 24, IOC).next_to(bch_l, DOWN, buff=0.15)
        self.at_text("Dispatchers.IO", lead=0.4)
        self.play(FadeIn(io_l), run_time=0.4)
        self.hold()

        wcode = M("flow { withContext(Dispatchers.IO) { emit(line) } }", 26, t2c={"withContext(Dispatchers.IO)": IOC})
        wcode.move_to([0, 2.95, 0])
        err = T("IllegalStateException: Flow invariant is violated", 26, BAD).move_to([0, 2.25, 0])
        self.say("wrong")
        self.play(FadeOut(blk), FadeOut(blk_l), FadeIn(wcode, shift=DOWN * 0.1), run_time=0.7)
        self.play(rd.animate.move_to([BENCH_X0 + 0.6, SEAT_Y + 0.45, 0]), nt.animate.move_to([BENCH_X0 + 1.25, SEAT_Y + 0.3, 0]),
                  run_time=1.0)
        self.at_text("the flow throws", lead=0.3)
        self.play(FadeIn(err, shift=UP * 0.1), run_time=0.5)
        self.hold()

        seats = (BENCH_X0 + 1.95, BENCH_X0 + 2.75)
        self.say("wrongjoke")
        self.at_text("dragged", lead=0.4)
        self.play(FadeOut(fam, shift=UP * 0.3), run_time=0.4)
        fam2 = VGroup(seated(seats[0], COOK2), seated(seats[1], COOK2))
        self.play(FadeIn(fam2, shift=DOWN * 0.3), run_time=0.5)
        self.at_text("It's like", lead=0.3)
        self.play(Indicate(fam2, color=COOK2, scale_factor=1.12), run_time=0.8)
        self.play(Indicate(tbl, color=WHITE), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # the wall and its shelf
        BX = -3.3
        rdb = op_box("read", "the note, blocking", IOC, w=4.0).move_to([BX, 2.6, 0])
        psb = op_box("parse", "one line", IOC, w=4.0).move_to([BX, 1.45, 0])
        fmb = op_box("format", "for the book", COOK, w=4.0).move_to([BX, -0.95, 0])
        svb = op_box("save", "in collect", COOK, w=4.0).move_to([BX, -2.1, 0])
        WY = 0.25
        wall_l = Rectangle(width=2.0, height=0.3).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([BX - 2.15, WY, 0])
        wall_r = Rectangle(width=2.0, height=0.3).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([BX + 2.15, WY, 0])
        shelf = VGroup(*[Square(0.2).set_stroke(GREY_A, 1.5).set_fill(BLACK, 1) for _ in range(5)]).arrange(RIGHT, buff=0.06)
        shelf.move_to([BX, WY, 0])
        wall = VGroup(wall_l, wall_r, shelf)
        fo = M(".flowOn(Dispatchers.IO)", 26, IOC).move_to([BX + 3.4, WY, 0], aligned_edge=LEFT)
        sh_l = T("a shelf of up to 64 lines", 24, GREY_A).next_to(fo, DOWN, buff=0.18).align_to(fo, LEFT)
        ar1 = Arrow(rdb.get_bottom(), psb.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        ar2 = Arrow(psb.get_bottom(), shelf.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        ar3 = Arrow(shelf.get_bottom(), fmb.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        ar4 = Arrow(fmb.get_bottom(), svb.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        up_ck = person(IOC, 0.95).move_to([BX - 2.75, 2.05, 0])
        dn_ck = person(COOK, 0.95).move_to([BX - 2.75, -1.5, 0])
        up_l = T("upstream: a second coroutine, at the bench", 24, IOC).move_to([BX + 2.25, 3.25, 0], aligned_edge=LEFT)
        self.say("flowon")
        self.play(FadeIn(rdb), FadeIn(psb), FadeIn(fmb), FadeIn(svb), GrowArrow(ar1), GrowArrow(ar4), run_time=0.8)
        self.play(FadeIn(wall), GrowArrow(ar2), GrowArrow(ar3), FadeIn(fo), run_time=0.7)
        self.at_text("Everything above", lead=0.3)
        self.play(FadeIn(up_ck), Indicate(VGroup(rdb[1], rdb[2], psb[1], psb[2]), color=IOC), run_time=0.8)
        self.at_text("in a second", lead=0.3)
        self.play(FadeIn(up_l), run_time=0.5)
        self.at_text("with a shelf", lead=0.3)
        self.play(FadeIn(sh_l), Indicate(shelf, color=WHITE, scale_factor=1.15), run_time=0.8)
        self.at_text("Everything below", lead=0.3)
        self.play(FadeIn(dn_ck), Indicate(VGroup(fmb[1], fmb[2], svb[1], svb[2]), color=COOK), run_time=0.8)
        self.hold()

        TX = 0.55
        th = [M("DefaultDispatcher-worker-1", 22, IOC).move_to([TX, rdb.get_y(), 0], aligned_edge=LEFT),
              M("DefaultDispatcher-worker-1", 22, IOC).move_to([TX, psb.get_y(), 0], aligned_edge=LEFT),
              M("main", 22, COOK).move_to([TX, fmb.get_y(), 0], aligned_edge=LEFT),
              M("main", 22, COOK).move_to([TX, svb.get_y(), 0], aligned_edge=LEFT)]
        th_h = T("FlowOnDemo, the thread of each step", 22, GREY_B).move_to([TX, -2.95, 0], aligned_edge=LEFT)
        self.say("flowon_show")
        self.play(FadeOut(up_l), FadeIn(th_h), run_time=0.4)
        self.at_text("read and parse", lead=0.3)
        self.play(FadeIn(th[0]), FadeIn(th[1]), run_time=0.6)
        self.at_text("format and save", lead=0.3)
        self.play(FadeIn(th[2]), FadeIn(th[3]), run_time=0.6)
        self.at_text("The collector", lead=0.3)
        self.play(Circumscribe(VGroup(svb, th[3]), color=COOK, buff=0.12), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= catch and onCompletion =================
        CY = 1.85
        bx = [("flow { }", -5.25, 2.0, SHOP), ("map", -2.85, 1.5, CPU), ("onCompletion", -0.25, 2.65, MARK),
              ("catch", 2.4, 1.5, BAD), ("collect { }", 4.95, 2.25, COOK)]
        boxes = {}
        for name, x, w, c in bx:
            r = RoundedRectangle(corner_radius=0.1, width=w, height=0.8).set_stroke(c, 3).set_fill(dim(c, 0.12), 1)
            boxes[name] = VGroup(r, M(name, 24, c).move_to(r)).move_to([x, CY, 0])
        chain = VGroup(*boxes.values())
        arrs = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.05, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.35) for i in range(4)])
        flow_l = T("values go this way", 22, GREY_B).move_to([-1.6, 3.2, 0])
        flow_a = Arrow([-0.2, 3.2, 0], [1.6, 3.2, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        cb = boxes["catch"]
        net = VMobject().set_points_smoothly([[-6.35, CY - 0.45, 0], [-4.0, CY - 1.25, 0], [-1.0, CY - 1.3, 0],
                                              [1.2, CY - 1.05, 0], [cb.get_left()[0] + 0.25, CY - 0.42, 0]])
        net = DashedVMobject(net.set_stroke(BAD, 3), num_dashes=40)
        net_l = T("catch's net: the steps above catch", 24, BAD).move_to([-2.4, CY - 1.75, 0])
        caller = VGroup(RoundedRectangle(corner_radius=0.1, width=2.4, height=1.0).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1),
                        VGroup(T("the code that", 22, GREY_A), T("called collect", 22, GREY_A)).arrange(DOWN, buff=0.1))
        caller[1].move_to(caller[0])
        caller.move_to([4.95, CY - 1.65, 0])
        con3 = Console(-6.2, -0.75, 22, 0.42)
        self.say("catch")
        self.play(LaggedStart(*[FadeIn(b) for b in chain], lag_ratio=0.15), Create(arrs), run_time=1.0)
        self.play(FadeIn(flow_l), GrowArrow(flow_a), run_time=0.5)
        self.at_text("catch is a net", lead=0.3)
        self.play(Create(net), run_time=1.0)
        self.play(FadeIn(net_l), run_time=0.4)
        self.at_text("onCompletion is", lead=0.3)
        self.play(Indicate(boxes["onCompletion"][1], color=MARK), run_time=0.8)
        self.hold()

        def item(name):
            c = chip_t(name, SHOP, 22).move_to(boxes["flow { }"].get_top() + UP * 0.35)
            self.play(FadeIn(c, scale=0.7), run_time=0.25)
            self.play(c.animate.move_to(boxes["collect { }"].get_top() + UP * 0.35), run_time=0.7)
            self.play(FadeIn(con3.line(f"collect {name}", COOK)), FadeOut(c, scale=0.6), run_time=0.3)

        self.say("torn")
        self.play(FadeIn(caller), run_time=0.3)
        item("flour")
        item("eggs")
        tear = chip_t("torn", BAD).move_to(boxes["flow { }"].get_bottom() + DOWN * 0.1)
        self.play(FadeIn(tear, scale=0.7), run_time=0.3)
        self.play(MoveAlongPath(tear, VMobject().set_points_smoothly([tear.get_center(), [-4.0, CY - 1.2, 0],
                                                                       [-1.0, CY - 1.28, 0], [1.2, CY - 1.0, 0],
                                                                       cb.get_bottom() + LEFT * 0.2])), run_time=1.2)
        self.at_text("onCompletion prints", lead=0.3)
        self.play(Indicate(boxes["onCompletion"][1], color=MARK),
                  FadeIn(con3.line("onCompletion: cause = java.io.IOException: delivery note torn", MARK)), run_time=0.6)
        self.at_text("catch emits", lead=0.3)
        self.play(FadeOut(tear, scale=0.5), Indicate(cb[1], color=BAD),
                  FadeIn(con3.line("catch: java.io.IOException: delivery note torn", BAD)), run_time=0.6)
        ab = chip_t("ABORTED", BAD).move_to(cb.get_top() + UP * 0.35)
        self.play(FadeIn(ab, scale=0.7), run_time=0.3)
        self.play(ab.animate.move_to(boxes["collect { }"].get_top() + UP * 0.35), run_time=0.5)
        self.play(FadeOut(ab, scale=0.6), FadeIn(con3.line("collect ABORTED", COOK)), run_time=0.3)
        self.at_text("and collect returns", lead=0.3)
        self.play(FadeIn(con3.line("collect returned normally", GREY_A)), run_time=0.4)
        self.hold()

        self.say("shelf_q")
        self.play(FadeOut(con3.clear()), run_time=0.4)
        item("flour")
        item("eggs")
        full = T("pantry shelf full", 24, BAD).next_to(boxes["collect { }"], UP, buff=0.15)
        self.play(boxes["collect { }"][0].animate.set_stroke(BAD), FadeIn(full), run_time=0.5)
        self.hold(after=0)
        self.predict()
        ex = chip_t("shelf full", BAD).move_to(boxes["collect { }"].get_bottom() + DOWN * 0.1)
        nothing = T("prints nothing", 24, GREY_B).next_to(cb, UP, buff=0.15)
        self.say("shelf_a")
        self.play(FadeIn(ex, scale=0.7), FadeIn(nothing), run_time=0.4)
        self.play(ex.animate.move_to(caller.get_top() + UP * 0.32), run_time=0.7)
        cgot = con3.line("the caller got: java.lang.IllegalStateException: pantry shelf full", BAD)
        self.play(FadeIn(cgot), Indicate(caller[1], color=BAD), run_time=0.6)
        self.play(FadeOut(ex, shift=DOWN * 0.3, scale=0.6), run_time=0.3)
        self.at_text("onCompletion saw", lead=0.3)
        # the onCompletion line was printed before the caller's: it goes in above it
        ocl = con3.line("onCompletion: cause = java.lang.IllegalStateException: pantry shelf full", MARK)
        ocl.move_to(cgot.get_left(), aligned_edge=LEFT)
        self.play(cgot.animate.shift(DOWN * con3.step), Indicate(boxes["onCompletion"][1], color=MARK), run_time=0.6)
        self.play(FadeIn(ocl), run_time=0.5)
        self.hold()

        self.say("shelf_joke")
        self.at_text("So put", lead=0.3)
        self.play(Circumscribe(VGroup(boxes["flow { }"], boxes["map"]), color=BAD, buff=0.12), run_time=1.0)
        self.at_text("never put", lead=0.3)
        tr_x = VGroup(M("try { emit(x) }", 26, BAD), tick(False, 0.2)).arrange(RIGHT, buff=0.3).move_to([0, -3.15, 0])
        self.play(FadeIn(tr_x), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code =================
        khl = {".flowOn(Dispatchers.IO)": IOC, ".onCompletion": MARK, ".catch": BAD, "flow {": SHOP}
        k = code_block(["flow { while (true) emit(parseLine(reader.readLine() ?: break)) }",
                        "    .flowOn(Dispatchers.IO)",
                        "    .map<DeliveryLine, StockEvent> { StockEvent.Stocked(it.item) }",
                        "    .onCompletion { cause -> log(\"delivery ended: $cause\") }",
                        "    .catch { e -> emit(StockEvent.Aborted(e.message ?: \"error\")) }"], 22, khl)
        jhl = {".subscribeOn(Schedulers.boundedElastic())": IOC, ".doFinally": MARK, ".onErrorResume": BAD}
        j = code_block(["Flux.<DeliveryLine>generate(sink -> {",
                        "        String line = reader.readLine();",
                        "        if (line == null) sink.complete(); else sink.next(parseLine(line));",
                        "    })",
                        "    .subscribeOn(Schedulers.boundedElastic())",
                        "    .<StockEvent>map(l -> new Stocked(l.item()))",
                        "    .doFinally(signal -> log(\"delivery ended: \" + signal))",
                        "    .onErrorResume(e -> Flux.just(new Aborted(e.getMessage())));"], 22, jhl)
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(T("Java, with Reactor", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18))
        cols.arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.6).move_to([0, 0, 0])
        self.say("code")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.at_text("and in Java", lead=0.3)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.8)
        self.hold(after=1.2)
        self.play(FadeOut(cols), run_time=0.6)

        # ================= moral and a check =================
        mq = T("Has the shop sent anything? Not until someone collects.", 32).move_to(UP * 2.6)
        m1 = T("A cold flow is a recipe card: every collector cooks it from the top.", 30, COOK).move_to(UP * 1.75)
        m2 = T("Steps write on the card. The terminal one cooks.", 28, CPU).move_to(UP * 1.0)
        m3 = T("flowOn moves the steps above it. catch catches what falls from above.", 28, IOC).move_to(UP * 0.3)
        m4 = T("onCompletion sees every ending.", 28, MARK).move_to(DOWN * 0.4)
        for m in (mq, m1, m2, m3, m4):
            fit(m, 12.6)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("and every collector", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Steps write", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at_text("flowOn moves", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.at_text("and onCompletion", lead=0.3)
        self.play(FadeIn(m4, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qk = M("flow { A }.map { B }.flowOn(Dispatchers.IO).filter { C }.collect { D }", 24)
        fit(qk, 12.4)
        qq = VGroup(T("Check:", 28, MARK), T("collected on main. Where does each letter run?", 28)).arrange(RIGHT, buff=0.25)
        qg = VGroup(qk, qq).arrange(DOWN, buff=0.3).move_to(DOWN * 1.65)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("A and B on IO, above flowOn; C and D on main, with the collector", 28, IOC).move_to(DOWN * 2.95)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
