from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bMono\.zip\b", "Mono dot zip"), (r"\bmergeSequential\b", "merge sequential"), (r"\bcombineLatest\b", "combine latest"),
    (r"\bdefaultIfEmpty\b", "default if empty"), (r"\bswitchIfEmpty\b", "switch if empty"),
    (r"24\.00, 3\.50, 0\.00", "24, 3 fifty, and zero"), (r"\bfan-out\b", "fan out"),
]

# every spoken line, in order
N = {
    "open": "At the end of the bakery line there's a packing table, and two belts arrive at it. "
            "One brings loaves from the oven. The other brings jars of jam from the jam kitchen.",
    "ways": "The packer can work in four ways. Box whatever arrives first. Finish all the loaves before the jam. "
            "Make gift boxes, one loaf and one jar in each. Or keep the price board on the wall up to date.",
    "shy": "Reactor has an operator for each. And here's the question that's easy to be shy about: "
           "aren't they all just names for, put these together?",
    "two_q": "They're not, and two questions tell them apart. First: when is each belt switched on? "
             "Switching a belt on means subscribing to it, signing its order form. "
             "Second: when does something come out?",
    "screen": "Let's try the first two. The kitchen has a screen for new orders from two belts. "
              "The shop counter sends one every 30 milliseconds, the website one every 40, three each.",
    "merge_q": "First, the packer who boxes whatever comes first. Both belts are switched on at once. What comes out?",
    "merge_a": "Orders as they arrive: counter, web, counter, web, counter, web. "
               "Done at about 130 milliseconds. That's merge.",
    "concat_q": "Now the packer who finishes one belt before she touches the other. "
                "The counter belt runs until its end-of-day bell. When is the web belt switched on?",
    "concat_a": "When the bell rings: the demo printed 92 milliseconds. "
                "Only then does the web belt start its own clock, so its orders land at about 130, 170 and 210. "
                "One belt, then the other. That's concat.",
    "endless": "Now make the counter belt endless, like a live feed that never closes. The bell never rings, "
               "so the web belt is never switched on. Not late. Never.",
    "endless_joke": "It's the customer ahead of you at the till who keeps saying: oh, and one more thing. "
                    "You never get served. So behind an endless source, concat never starts the next one. "
                    "For live feeds, use merge.",
    "mseq": "And the clerk at the exit of the icing room? That's mergeSequential: both belts on at once, "
            "early web orders held until the bell. concat's order, at merge's speed.",
    "gift": "Now the gift boxes. Three loaves, two jars. The packer takes one of each, boxes them, and repeats. "
            "Then the jam belt rings its bell, and she stops. Loaf 3 is never boxed.",
    "gift_name": "That's zip. It pairs by position, first with first, second with second, "
                 "and it's done as soon as either belt is done.",
    "fanout": "You'll meet it most as Mono.zip. The order page builds a quote from three lookups: "
              "a price that takes 200 milliseconds, a delivery fee that takes 100, and a discount.",
    "fanout2": "Mono.zip switches all three on at once, so the quote is ready when the slowest is, "
               "at about 200 milliseconds. That's called fan-out.",
    "empty_q": "Now the trap. This customer has no discount, so that lookup completes empty: "
               "no value, just the bell. What does the zip do? Fail? Leave a gap? Wait forever?",
    "empty_a": "None of those. It completes empty, at once, and cancels the lookups still running. "
               "The demo printed: price lookup cancelled, then: Mono.zip result: null. "
               "Here null means completed empty. No quote, no error, no log.",
    "empty_joke": "And here the gift box picture breaks. A real packer with no jam would shout: we're out of jam! "
                  "Mono.zip just turns off the light and goes home. "
                  "So decide what empty means for each source, and say it in code.",
    "fix": "Where empty has a sensible meaning, like no discount, write defaultIfEmpty: 24.00, 3.50, 0.00. "
           "Where empty is a real problem, write switchIfEmpty with an error, and the demo says: missing discount.",
    "board": "Last, the price board: a cake's weight times the price per kilo. "
             "The weight is 1.5 kilos, then 2 at 300 milliseconds. "
             "The price per kilo is 20, then 22, then 21.",
    "board_q": "With zip, what does the board show?",
    "board_zip": "Just two prices: 30, then 44. First with first, second with second. "
                 "The board never showed 1.5 times 22, and it never saw the 21.",
    "board_cl_q": "Now combineLatest. Once each belt has sent something, every new item goes out "
                  "with the latest from the other belt. How many prices now?",
    "board_cl": "Four: 30, 33, 44, 42. Every state the inputs passed through. That's what a price board is for.",
    "board_joke": "A zip board would be the politest board in town: it waits for the customer and the owner to take turns. "
                  "combineLatest shows every change. zip shows only matched pairs.",
    "table": "So, by our two questions. merge: all on at once, out as they arrive. "
             "concat: the next one on after the bell. zip: all on at once, one from each. "
             "combineLatest: all on at once, out on every change.",
    "code": "Here's the safe quote in Java and Kotlin: a missing discount means zero, a missing price is an error.",
    "moral": "So, are they all names for, put these together? No. Ask when each belt is switched on, "
             "and when something comes out. And with zip, ask: what if a belt arrives empty?",
    "check": "Quick check. Mono.zip of saving the order, a Mono of Void that completes after 20 milliseconds, "
             "and the cake's price, which takes 100. What does the zip emit, and when?",
    "check_a": "Nothing, at about 20 milliseconds. A Mono of Void is always empty, "
               "so the zip completes empty, and cancels the price lookup. Use then instead: save, then price.",
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

    def predict(self, secs=2.4, pos=(6.4, -3.25), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole reactive track
OVEN_C, PACK_C, SLIP_C, LOAF_C, BELL_C, BAD_C, CAKE_C = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
JAM_C = "#E58FB4"          # the second belt: jam, web orders, the price per kilo
DISC_C = PURPLE_M          # the discount lookup


def person(color=PACK_C, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def oven(s=1.0):
    body = RoundedRectangle(corner_radius=0.14, width=1.9, height=1.55).set_stroke(OVEN_C, 3).set_fill(dim(OVEN_C, 0.16), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.62).set_stroke(OVEN_C, 2).set_fill(dim(LOAF_C, 0.5), 1)
    win.move_to(body.get_center() + DOWN * 0.22)
    knobs = VGroup(*[Circle(radius=0.07).set_stroke(OVEN_C, 2).set_fill(dim(OVEN_C, 0.5), 1) for _ in range(3)])
    knobs.arrange(RIGHT, buff=0.18).move_to(body.get_top() + DOWN * 0.27)
    return VGroup(body, win, knobs).scale(s)


def pot(s=1.0):
    """The jam kitchen: a pot on a stove."""
    body = RoundedRectangle(corner_radius=0.18, width=1.5, height=0.95).set_stroke(JAM_C, 3).set_fill(dim(JAM_C, 0.2), 1)
    rim = Line(body.get_corner(UL) + LEFT * 0.12, body.get_corner(UR) + RIGHT * 0.12, stroke_width=4, color=JAM_C)
    hl = Line(body.get_left() + UP * 0.2, body.get_left() + UP * 0.2 + LEFT * 0.28, stroke_width=4, color=JAM_C)
    hr = Line(body.get_right() + UP * 0.2, body.get_right() + UP * 0.2 + RIGHT * 0.28, stroke_width=4, color=JAM_C)
    steam = VGroup(*[VMobject().set_points_smoothly([body.get_top() + RIGHT * dx + UP * (0.12 + 0.12 * k) + RIGHT * 0.06 * (-1) ** k
                                                    for k in range(4)]).set_stroke(GREY_B, 2) for dx in (-0.3, 0.05, 0.4)])
    return VGroup(body, rim, hl, hr, steam).scale(s)


def loaf(label="", s=1.0, color=LOAF_C):
    body = RoundedRectangle(corner_radius=0.2, width=1.05, height=0.46).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    if label:
        return VGroup(body, M(label, 20, color).move_to(body)).scale(s).set_z_index(4)
    cuts = VGroup(*[Line(LEFT * 0.07 + DOWN * 0.1, RIGHT * 0.07 + UP * 0.1, stroke_width=2.5, color=color)
                    .move_to(body.get_center() + RIGHT * dx) for dx in (-0.26, 0, 0.26)])
    return VGroup(body, cuts).scale(s).set_z_index(4)


def jar(label="", s=1.0, color=JAM_C):
    body = RoundedRectangle(corner_radius=0.1, width=0.5, height=0.52).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    lid = RoundedRectangle(corner_radius=0.04, width=0.56, height=0.13).set_stroke(GREY_A, 2).set_fill(GREY_D, 1)
    lid.next_to(body, UP, buff=0)
    g = VGroup(body, lid)
    if label:
        g.add(M(label, 20, WHITE).move_to(body))
    return g.scale(s).set_z_index(4)


def belt(x0, x1, y):
    """A conveyor belt: its top surface at y, rollers underneath."""
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=GREY_B)
    bot = Line([x0, y - 0.24, 0], [x1, y - 0.24, 0], stroke_width=2, color=GREY_D)
    n = int((x1 - x0) / 0.55)
    rollers = VGroup(*[Circle(radius=0.08, stroke_width=1.5, color=GREY_C).move_to([x0 + 0.25 + i * (x1 - x0 - 0.5) / max(1, n - 1), y - 0.12, 0])
                       for i in range(n)])
    return VGroup(top, bot, rollers)


def bell(s=1.0, color=BELL_C):
    body = VMobject().set_points_smoothly([[-0.3, -0.22, 0], [-0.24, 0.02, 0], [-0.17, 0.2, 0], [0, 0.27, 0],
                                           [0.17, 0.2, 0], [0.24, 0.02, 0], [0.3, -0.22, 0]])
    body.add_line_to(np.array([-0.3, -0.22, 0]))
    body.set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    lip = Line([-0.36, -0.22, 0], [0.36, -0.22, 0], stroke_width=4, color=color)
    clap = Dot([0, -0.3, 0], radius=0.06, color=color)
    loop = Circle(radius=0.06, stroke_width=3, color=color).move_to([0, 0.33, 0])
    return VGroup(body, lip, clap, loop).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def scribble(p, w=1.0, color=SLIP_C):
    """A hand-written signature, drawn as a smooth wavy stroke starting at p."""
    xs = np.linspace(0, w, 9)
    ys = [0.0, 0.12, -0.06, 0.15, -0.09, 0.1, -0.03, 0.08, 0.0]
    return VMobject().set_points_smoothly([p + np.array([x, y, 0]) for x, y in zip(xs, ys)]).set_stroke(color, 3)


def gift(contents, color=PACK_C):
    """A gift box drawn around the given items, with a ribbon across the top."""
    r = SurroundingRectangle(contents, buff=0.16, corner_radius=0.08).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    r.set_z_index(3)
    rib = Line(r.get_top() + DOWN * 0.0, r.get_bottom(), stroke_width=3, color=SLIP_C).set_z_index(5)
    bow = VGroup(Circle(radius=0.09).move_to(r.get_top() + LEFT * 0.1 + UP * 0.07),
                 Circle(radius=0.09).move_to(r.get_top() + RIGHT * 0.1 + UP * 0.07)).set_stroke(SLIP_C, 3).set_z_index(5)
    return VGroup(r, rib, bow)


def marble(text, color, r=0.28, size=20):
    c = Circle(radius=r).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    return VGroup(c, M(text, size, WHITE).move_to(c)).set_z_index(5)


def chip_n(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.62, t.width + 0.28), height=0.5).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def end_bar(x, y, color=BELL_C):
    return Line([x, y + 0.32, 0], [x, y - 0.32, 0], stroke_width=5, color=color).set_z_index(4)


def on_tag(x, y):
    """Where a belt is switched on (subscribed): a yellow signature mark."""
    ln = Line([x, y + 0.38, 0], [x, y - 0.38, 0], stroke_width=3, color=SLIP_C).set_z_index(4)
    t = T("on", 20, SLIP_C).move_to([x, y + 0.55, 0])
    return VGroup(ln, t)


def cross_at(p, s=0.28):
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(BAD_C, 5).scale(s).move_to(p).set_z_index(8)


# the packing table, as it sits on screen
TOP_Y, BOT_Y = 2.0, -0.3
TBL_X = 4.55


def packing_table():
    ov = oven(0.72).move_to([-5.45, TOP_Y + 0.55, 0])
    ov_l = T("oven", 22, OVEN_C).next_to(ov, DOWN, buff=0.15)
    bt = belt(-4.5, 3.4, TOP_Y)
    pt = pot(0.8).move_to([-5.45, BOT_Y + 0.42, 0])
    pt_l = T("jam kitchen", 22, JAM_C).next_to(pt, DOWN, buff=0.15)
    bb = belt(-4.5, 3.4, BOT_Y)
    top = Line([TBL_X - 0.85, 0.85, 0], [TBL_X + 0.85, 0.85, 0], stroke_width=6, color=GREY_A)
    legs = VGroup(Line([TBL_X - 0.7, 0.85, 0], [TBL_X - 0.7, 0.15, 0]), Line([TBL_X + 0.7, 0.85, 0], [TBL_X + 0.7, 0.15, 0])).set_stroke(GREY_B, 3)
    pk = person(PACK_C, 1.25).move_to([6.15, 1.2, 0])
    pk_l = T("packer", 22, PACK_C).next_to(pk, DOWN, buff=0.15)
    return dict(ov=VGroup(ov, ov_l), bt=bt, pt=VGroup(pt, pt_l), bb=bb, table=VGroup(top, legs), pk=VGroup(pk, pk_l))


class Rx04Combine(Narrated):
    """rx-04, section 0 (with sections 1 and 2): the packing table with two belts; two questions (when is each belt
    switched on, when does something come out); merge and concat on the kitchen screen (92 ms, endless belt),
    mergeSequential as the clerk; zip as gift boxes; Mono.zip fan-out and the empty discount; defaultIfEmpty and
    switchIfEmpty; combineLatest as the price board; the table; the code; Mono<Void> in a zip."""

    def construct(self):
        self.title_card("The packing table", "zip, merge, concat and combineLatest")

        # ================= the packing table =================
        pt = packing_table()
        loaves = [loaf(s=0.8).move_to([-3.6 + 1.2 * i, TOP_Y + 0.22, 0]) for i in range(3)]
        jars = [jar(s=0.9).move_to([-3.4 + 1.3 * i, BOT_Y + 0.36, 0]) for i in range(3)]
        self.say("open")
        self.play(FadeIn(pt["table"]), FadeIn(pt["pk"]), run_time=0.7)
        self.at_text("two belts", lead=0.3)
        self.play(Create(pt["bt"]), Create(pt["bb"]), run_time=0.9)
        self.at(1)
        self.play(FadeIn(pt["ov"]), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in loaves], lag_ratio=0.2), run_time=1.0)
        self.at(2)
        self.play(FadeIn(pt["pt"]), LaggedStart(*[FadeIn(j, shift=RIGHT * 0.2) for j in jars], lag_ratio=0.2), run_time=1.0)
        self.play(*[l.animate.shift(RIGHT * 1.2) for l in loaves], *[j.animate.shift(RIGHT * 1.3) for j in jars], run_time=1.2)
        self.hold()

        # four ways of working, as four small pictures
        PY, LY = -1.95, -2.75

        def mini(kind):
            if kind == "first":
                return VGroup(loaf(s=0.42), jar(s=0.5), loaf(s=0.42), jar(s=0.5)).arrange(RIGHT, buff=0.1)
            if kind == "turns":
                return VGroup(loaf(s=0.42), loaf(s=0.42), jar(s=0.5), jar(s=0.5)).arrange(RIGHT, buff=0.1)
            if kind == "gift":
                inner = VGroup(loaf(s=0.5), jar(s=0.55)).arrange(RIGHT, buff=0.12)
                return VGroup(gift(inner), inner)
            board = RoundedRectangle(corner_radius=0.06, width=1.7, height=0.75).set_stroke(GREY_A, 3).set_fill(GREY_E, 1)
            return VGroup(board, M("30.00", 26, SLIP_C).move_to(board))

        kinds = [("first", "whatever comes first"), ("turns", "all loaves, then the jam"),
                 ("gift", "gift boxes: one of each"), ("board", "the price board")]
        panels = []
        for i, (k, lab) in enumerate(kinds):
            x = -4.95 + 3.3 * i
            pic = mini(k).move_to([x, PY, 0])
            tl = T(lab, 24).move_to([x, LY, 0])
            panels.append(VGroup(pic, tl))
        self.say("ways")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(panels[i], shift=UP * 0.1), run_time=0.6)
        self.hold()

        shy = T("Aren't they all just names for “put these together”?", 32).move_to([0, -2.35, 0])
        fit(shy, 12.4)
        self.say("shy")
        self.play(FadeOut(VGroup(*panels)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.7)
        self.hold()

        q1 = VGroup(T("1.", 28, SLIP_C), T("When is each belt switched on?", 28)).arrange(RIGHT, buff=0.2)
        q2 = VGroup(T("2.", 28, SLIP_C), T("When does something come out?", 28)).arrange(RIGHT, buff=0.2)
        qs = VGroup(q1, q2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-1.3, -2.3, 0])
        sig_t = scribble(np.array([-4.4, TOP_Y - 0.55, 0]))
        sig_b = scribble(np.array([-4.4, BOT_Y - 0.55, 0]))
        on_l = T("switched on = subscribed: the order form, signed", 22, SLIP_C).move_to([0.2, 0.55, 0])
        self.say("two_q")
        self.play(FadeOut(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Create(sig_t), Create(sig_b), FadeIn(on_l), run_time=0.9)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the kitchen screen: merge and concat =================
        X0, K = -3.0, 8.9 / 220
        X = lambda ms: X0 + K * ms
        YC, YW, YO = 2.05, 0.95, -0.4
        axis = VGroup()
        for ms in (0, 50, 100, 150, 200):
            axis.add(DashedLine([X(ms), YC + 0.45, 0], [X(ms), YO - 0.45, 0], dash_length=0.06).set_stroke(GREY_D, 1.5))
            axis.add(M(str(ms), 20, GREY_B).move_to([X(ms), 2.85, 0]))
        axis.add(T("ms", 20, GREY_B).move_to([X(200) + 0.6, 2.85, 0]))

        def lane(y, label, color):
            ln = Arrow([X(0) - 0.2, y, 0], [X(225), y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.02)
            return VGroup(ln, T(label, 24, color).move_to([X(0) - 0.45, y, 0], aligned_edge=RIGHT))

        l_c, l_w, l_o = lane(YC, "counter", LOAF_C), lane(YW, "web", JAM_C), lane(YO, "screen", GREY_A)
        CT, WT = [30, 60, 90], [40, 80, 120]
        cm = [marble(f"c{i}", LOAF_C).move_to([X(t), YC, 0]) for i, t in enumerate(CT)]
        wm = [marble(f"w{i}", JAM_C).move_to([X(t), YW, 0]) for i, t in enumerate(WT)]
        c_end = end_bar(X(90) + 0.4, YC)
        w_end = end_bar(X(120) + 0.4, YW)
        tm = ValueTracker(0)
        cur = always_redraw(lambda: Line([X(tm.get_value()), YC + 0.45, 0], [X(tm.get_value()), YO - 0.45, 0], stroke_width=2,
                                         color=WHITE).set_opacity(0.3 if tm.get_value() > 0.5 else 0).set_z_index(1))

        def to_t(t, speed=110.0):
            dt = t - tm.get_value()
            if dt > 0.5:
                self.play(tm.animate.set_value(t), run_time=dt / speed, rate_func=linear)

        def drop(m, x, rt=0.35):
            c = m.copy()
            self.add(c)
            self.play(c.animate.move_to([x, YO, 0]), run_time=rt)
            return c

        self.say("screen")
        self.play(FadeIn(axis), FadeIn(l_c), FadeIn(l_w), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in cm], FadeIn(c_end), lag_ratio=0.3), run_time=1.1)
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in wm], FadeIn(w_end), lag_ratio=0.3), run_time=1.1)
        self.hold()

        head = T("whatever comes first", 28, PACK_C).move_to([0, -1.55, 0])
        on_c, on_w = on_tag(X(0), YC), on_tag(X(0), YW)
        self.say("merge_q")
        self.play(FadeIn(l_o), FadeIn(head), run_time=0.6)
        self.at(1)
        self.play(FadeIn(on_c), FadeIn(on_w), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.add(cur)

        self.say("merge_a")
        events = sorted([(t, m) for t, m in zip(CT, cm)] + [(t, m) for t, m in zip(WT, wm)], key=lambda e: e[0])
        outs = []
        for t, m in events:
            to_t(t)
            outs.append(drop(m, X(t)))
        to_t(130)
        o_end = end_bar(X(130), YO, WHITE)
        self.play(FadeIn(o_end), run_time=0.3)
        self.at(1)
        n1 = T("done at about 130 ms", 24, GREY_B).move_to([0, -2.25, 0])
        self.play(FadeIn(n1), run_time=0.4)
        self.at(2)
        nm = M("Flux.merge(counter, web)", 26, PACK_C).move_to([0, -2.9, 0])
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(*outs, o_end, n1, nm, on_w)), FadeOut(head), *[FadeOut(m) for m in wm], FadeOut(w_end),
                  run_time=0.5)
        tm.set_value(0)

        # concat: the web belt is switched on only at the counter's bell
        head2 = T("all loaves, then the jam", 28, PACK_C).move_to([0, -1.55, 0])
        off = DashedLine([X(0) - 0.2, YW, 0], [X(225), YW, 0], dash_length=0.1).set_stroke(GREY_D, 2.5).set_z_index(2)
        bl = bell(0.5).move_to([X(90) + 0.9, YC, 0])
        self.say("concat_q")
        self.play(FadeIn(head2), FadeIn(off), run_time=0.6)
        self.at_text("end-of-day bell", lead=0.4)
        self.play(FadeIn(bl, shift=DOWN * 0.1), Indicate(c_end, color=BELL_C), run_time=0.8)
        self.at(1)
        qw = T("?", 40).move_to([X(60), YW, 0]).set_z_index(5)
        self.play(FadeIn(qw), run_time=0.4)
        self.hold(after=0)
        self.predict()

        WT2 = [132, 172, 212]
        wm2 = [marble(f"w{i}", JAM_C).move_to([X(t), YW, 0]) for i, t in enumerate(WT2)]
        on_w2 = on_tag(X(92), YW)
        n92 = T("92 ms", 20, SLIP_C).next_to(on_w2[0], DOWN, buff=0.08).shift(RIGHT * 0.38)
        self.say("concat_a")
        self.play(FadeOut(qw), run_time=0.2)
        outs = []
        for t, m in zip(CT, cm):
            to_t(t)
            outs.append(drop(m, X(t), rt=0.3))
        to_t(92)
        self.play(Wiggle(bl, scale_value=1.25, rotation_angle=0.15 * TAU), FadeIn(on_w2), FadeIn(n92), run_time=0.8)
        self.at(1)
        live = Line([X(92), YW, 0], [X(225), YW, 0], stroke_width=2.5, color=GREY_C).set_z_index(3)
        self.play(FadeIn(live), run_time=0.3)
        for t, m in zip(WT2, wm2):
            to_t(t)
            self.play(FadeIn(m, scale=0.6), run_time=0.25)
            outs.append(drop(m, X(t), rt=0.3))
        o_end = end_bar(X(212) + 0.4, YO, WHITE)
        w_end2 = end_bar(X(212) + 0.4, YW)
        self.play(FadeIn(o_end), FadeIn(w_end2), run_time=0.3)
        self.at(2)
        nm2 = M("Flux.concat(counter, web)", 26, PACK_C).move_to([0, -2.9, 0])
        n2 = T("done at about 210 ms", 24, GREY_B).move_to([0, -2.25, 0])
        self.play(FadeIn(n2), FadeIn(nm2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # the endless counter belt
        more = [marble(f"c{i}", LOAF_C).move_to([X(90 + 30 * (i - 2)), YC, 0]) for i in range(3, 7)]
        never = T("never switched on", 24, BAD_C).move_to([X(150), YW + 0.45, 0])
        dots = T("...", 30, LOAF_C).move_to([X(222) + 0.2, YC + 0.1, 0])
        self.say("endless")
        self.play(FadeOut(VGroup(*outs, o_end, n2, nm2, n92, on_w2, live, w_end2, *wm2)), FadeOut(head2), run_time=0.5)
        cur.clear_updaters()
        self.remove(cur)
        self.play(FadeOut(c_end), FadeOut(bl), LaggedStart(*[FadeIn(m, scale=0.6) for m in more], lag_ratio=0.25),
                  FadeIn(dots), run_time=1.2)
        self.at(1)
        self.play(FadeIn(never, shift=UP * 0.1), off.animate.set_stroke(BAD_C, 2.5), run_time=0.7)
        self.at(2)
        self.play(Indicate(never, color=BAD_C, scale_factor=1.12), run_time=0.7)
        self.hold()

        till = T("“oh, and one more thing...”", 28, LOAF_C).move_to([0, -1.6, 0])
        rule1 = T("Behind an endless source, concat never starts the next one.", 28, SLIP_C).move_to([0, -2.35, 0])
        rule1b = T("For live feeds, use merge.", 28, SLIP_C).move_to([0, -2.95, 0])
        fit(rule1, 12.4)
        self.say("endless_joke")
        self.play(FadeIn(till, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rule1b, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(till, rule1, rule1b, *more, dots, never, off, on_c, *cm, axis, l_c, l_w, l_o)), run_time=0.6)

        # mergeSequential: the clerk at the exit
        clerk = VGroup(person(PACK_C, 1.0), T("clerk", 24, PACK_C)).arrange(DOWN, buff=0.15).move_to([0, 1.9, 0])
        ms_l = M("Flux.mergeSequential(counter, web)", 26, PACK_C).move_to([0, 0.6, 0])
        ms_o = VGroup(M("[counter-0, counter-1, counter-2, web-0, web-1, web-2]", 22),
                      M("done at about 120 ms", 22, GREY_B)).arrange(DOWN, buff=0.15).move_to([0, -0.45, 0])
        fit(ms_o, 12.4)
        held = VGroup(marble("w0", JAM_C), marble("w1", JAM_C)).arrange(RIGHT, buff=0.12).next_to(clerk[0], RIGHT, buff=0.3)
        held_l = T("held", 20, GREY_B).next_to(held, UP, buff=0.1)
        self.say("mseq")
        self.play(FadeIn(clerk, shift=UP * 0.1), run_time=0.6)
        self.at_text("That's", lead=0.3)
        self.play(FadeIn(ms_l), run_time=0.5)
        self.at_text("early web", lead=0.3)
        self.play(FadeIn(held), FadeIn(held_l), run_time=0.6)
        self.at_text("concat's order", lead=0.3)
        self.play(FadeIn(ms_o, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(clerk, ms_l, ms_o, held, held_l)), run_time=0.5)

        # ================= gift boxes: zip =================
        pt = packing_table()
        gl = [loaf(str(i), s=0.85).move_to([-0.9 - 1.25 * (i - 1), TOP_Y + 0.22, 0]) for i in (1, 2, 3)]
        gj = [jar(c, s=1.0).move_to([-0.9 - 1.25 * k, BOT_Y + 0.38, 0]) for k, c in enumerate("ab")]
        jbell = bell(0.55).move_to([3.0, BOT_Y + 0.9, 0])
        self.say("gift")
        self.play(FadeIn(pt["ov"]), FadeIn(pt["pt"]), FadeIn(pt["bt"]), FadeIn(pt["bb"]), FadeIn(pt["table"]), FadeIn(pt["pk"]),
                  run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in reversed(gl)], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(j, shift=RIGHT * 0.2) for j in reversed(gj)], lag_ratio=0.15), run_time=0.9)
        shipped = []
        SHIP = [np.array([2.8, -1.75, 0]), np.array([4.6, -1.75, 0])]
        for k in range(2):
            if k == 0:
                self.at(2)
            l, j = gl[k], gj[k]
            self.play(l.animate.move_to([TBL_X - 0.35, 1.15, 0]), j.animate.move_to([TBL_X + 0.45, 1.2, 0]),
                      *[x.animate.shift(RIGHT * 1.25) for x in gl[k + 1:]], *[x.animate.shift(RIGHT * 1.25) for x in gj[k + 1:]],
                      run_time=0.75)
            inner = VGroup(l, j)
            gb = gift(inner)
            self.play(FadeIn(gb), run_time=0.3)
            box = VGroup(gb, inner)
            self.play(box.animate.scale(0.8).move_to(SHIP[k]), run_time=0.6)
            tag = M(f"[{k + 1}, {'ab'[k]}]", 22, PACK_C).next_to(box, DOWN, buff=0.12)
            self.play(FadeIn(tag), run_time=0.2)
            shipped.append(VGroup(box, tag))
        self.at(3)
        self.play(FadeIn(jbell, shift=DOWN * 0.1), run_time=0.4)
        self.play(Wiggle(jbell, scale_value=1.25, rotation_angle=0.15 * TAU), run_time=0.9)
        self.at(4)
        nb = T("never boxed", 22, BAD_C).next_to(gl[2], UP, buff=0.15)
        self.play(Circumscribe(gl[2], color=WHITE, buff=0.08), FadeIn(nb), run_time=0.8)
        self.hold()

        zc = VGroup(M('Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b"))', 22, PACK_C),
                    M("[[1,a], [2,b]]", 22)).arrange(RIGHT, buff=0.5).move_to([0, -2.9, 0])
        fit(zc, 12.4)
        self.say("gift_name")
        self.play(FadeIn(zc[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(zc[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= Mono.zip: fan-out =================
        F0, FK = -2.6, 8.2 / 300
        FX = lambda ms: F0 + FK * ms
        YP, YF, YD, YQ = 2.05, 1.05, 0.05, -1.05
        f_axis = VGroup()
        for ms in (0, 100, 200, 300):
            f_axis.add(DashedLine([FX(ms), YP + 0.45, 0], [FX(ms), YQ - 0.45, 0], dash_length=0.06).set_stroke(GREY_D, 1.5))
            f_axis.add(M(str(ms), 20, GREY_B).move_to([FX(ms), 2.85, 0]))
        f_axis.add(T("ms", 20, GREY_B).move_to([FX(300) + 0.6, 2.85, 0]))

        def flane(y, label, color):
            ln = Arrow([FX(0) - 0.2, y, 0], [FX(310), y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.02)
            return VGroup(ln, T(label, 24, color).move_to([FX(0) - 0.45, y, 0], aligned_edge=RIGHT))

        lp, lf, ld, lq = flane(YP, "price", LOAF_C), flane(YF, "delivery fee", JAM_C), flane(YD, "discount", DISC_C), \
            flane(YQ, "Mono.zip", PACK_C)
        cp = chip_n("24.00", LOAF_C).move_to([FX(200), YP, 0])
        cf = chip_n("3.50", JAM_C).move_to([FX(100), YF, 0])
        cd = chip_n("2.00", DISC_C).move_to([FX(0) + 0.45, YD, 0])
        ons = VGroup(*[on_tag(FX(0), y) for y in (YP, YF, YD)])
        self.say("fanout")
        self.play(FadeIn(f_axis), FadeIn(lq), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lp), FadeIn(lf), FadeIn(ld), run_time=0.7)
        self.at_text("a price", lead=0.3)
        self.play(FadeIn(cp, scale=0.7), run_time=0.4)
        self.at_text("a delivery", lead=0.3)
        self.play(FadeIn(cf, scale=0.7), run_time=0.4)
        self.at_text("and a discount", lead=0.3)
        self.play(FadeIn(cd, scale=0.7), run_time=0.4)
        self.hold()

        quote = chip_n("[24.00, 3.50, 2.00]", PACK_C).move_to([FX(200), YQ, 0])
        brace = BraceBetweenPoints([FX(0), YQ - 0.4, 0], [FX(200), YQ - 0.4, 0], direction=DOWN, color=GREY_B)
        b_l = T("about 200 ms: the slowest one", 22, GREY_B).next_to(brace, DOWN, buff=0.1)
        fo = T("fan-out", 28, SLIP_C).move_to([4.7, -2.4, 0])
        self.say("fanout2")
        self.play(FadeIn(ons), run_time=0.6)
        self.at_text("so the quote", lead=0.3)
        self.play(*[Indicate(c, color=WHITE, scale_factor=1.1) for c in (cp, cf, cd)], run_time=0.6)
        self.play(FadeIn(quote, shift=DOWN * 0.15), run_time=0.5)
        self.play(GrowFromCenter(brace), FadeIn(b_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(fo, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # the empty discount
        ebell = bell(0.42).move_to([FX(0) + 0.4, YD + 0.05, 0])
        e_l = T("empty: just the bell", 22, DISC_C).next_to(ebell, RIGHT, buff=0.2)
        self.say("empty_q")
        self.play(FadeOut(VGroup(quote, brace, b_l, fo)), run_time=0.4)
        self.play(FadeOut(cd), FadeIn(ebell), FadeIn(e_l), run_time=0.7)
        self.at(2)
        qz = T("?", 44).move_to([FX(150), YQ, 0]).set_z_index(5)
        self.play(FadeIn(qz), run_time=0.4)
        self.hold(after=0)
        self.predict()

        x_p, x_f = cross_at([FX(200), YP, 0]), cross_at([FX(100), YF, 0])
        canc = VGroup(T("cancelled", 22, BAD_C).next_to(x_p, RIGHT, buff=0.2), T("cancelled", 22, BAD_C).next_to(x_f, RIGHT, buff=0.2))
        zbell = bell(0.42).move_to([FX(0) + 0.4, YQ + 0.05, 0])
        z_l = T("completed empty", 22, PACK_C).next_to(zbell, RIGHT, buff=0.2)
        out = VGroup(M("  price lookup cancelled", 22, GREY_A), M("Mono.zip result: null", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        out.move_to([-2.0, -2.45, 0])
        self.say("empty_a")
        self.play(FadeOut(qz), FadeIn(zbell), FadeIn(z_l), run_time=0.6)
        self.play(FadeIn(x_p), FadeIn(x_f), FadeIn(canc), cp.animate.set_opacity(0.35), cf.animate.set_opacity(0.35), run_time=0.7)
        self.at(1)
        self.play(FadeIn(out[0]), run_time=0.4)
        self.at_text("then:", lead=0.1)
        self.play(FadeIn(out[1]), run_time=0.4)
        self.at(2)
        self.play(Indicate(out[1], color=WHITE, scale_factor=1.06), run_time=0.7)
        self.hold()

        shout = T("a real packer: “we're out of jam!”", 26, PACK_C)
        quiet = T("Mono.zip: lights off, gone home", 26, GREY_B)
        jk = VGroup(shout, quiet).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.6, -2.45, 0])
        self.say("empty_joke")
        self.play(FadeIn(shout, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(quiet, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= say what empty means =================
        fx1 = M('Mono.zip(price, deliveryFee, discount.defaultIfEmpty("0.00"))', 22).move_to([-6.3, 2.3, 0], aligned_edge=LEFT)
        fo1 = M("with defaultIfEmpty: [24.00,3.50,0.00]", 22, LOAF_C).move_to([-5.9, 1.7, 0], aligned_edge=LEFT)
        fx2 = code_block(["Mono.zip(price, deliveryFee,", "        discount.switchIfEmpty(Mono.error(",
                          '                new IllegalStateException("missing discount"))))'], 22)
        fx2.move_to([-6.3, 0.55, 0], aligned_edge=LEFT)
        fo2 = VGroup(M("  price lookup cancelled", 22, GREY_A), M("with switchIfEmpty: missing discount", 22, BAD_C))
        fo2.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([-5.9, -0.85, 0], aligned_edge=LEFT)
        hl1 = SurroundingRectangle(fx1[27:-1], buff=0.07).set_stroke(SLIP_C, 2)
        hl2 = SurroundingRectangle(fx2[1][9:22], buff=0.07).set_stroke(SLIP_C, 2)
        rule2 = VGroup(T("Mono.zip turns one empty source into an empty result.", 28, SLIP_C),
                       T("Say what empty means on every source.", 28, SLIP_C)).arrange(DOWN, buff=0.2).move_to([0, -2.45, 0])
        fit(rule2, 12.4)
        self.say("fix")
        self.play(FadeIn(fx1), run_time=0.6)
        self.play(Create(hl1), run_time=0.5)
        self.at_text("24.00", lead=0.4)
        self.play(FadeIn(fo1, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(fx2), FadeOut(hl1), run_time=0.6)
        self.play(Create(hl2), run_time=0.5)
        self.at_text("missing discount", lead=0.6)
        self.play(FadeIn(fo2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.wait(1.6)
        self.play(FadeOut(VGroup(fx1, fo1, fx2, fo2, rule2, hl2)), run_time=0.6)

        # ================= the price board: combineLatest =================
        B0, BK = -2.7, 8.4 / 450
        BX = lambda ms: B0 + BK * ms
        YW2, YP2, YZ, YL = 2.05, 1.05, -0.15, -1.25
        b_axis = VGroup()
        for ms in (0, 100, 200, 300, 400):
            b_axis.add(DashedLine([BX(ms), YW2 + 0.45, 0], [BX(ms), YL - 0.45, 0], dash_length=0.06).set_stroke(GREY_D, 1.5))
            b_axis.add(M(str(ms), 20, GREY_B).move_to([BX(ms), 2.85, 0]))
        b_axis.add(T("ms", 20, GREY_B).move_to([BX(400) + 0.75, 2.85, 0]))

        def blane(y, label, color):
            ln = Arrow([BX(0) - 0.3, y, 0], [BX(455), y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.02)
            return VGroup(ln, T(label, 24, color).move_to([BX(0) - 0.55, y, 0], aligned_edge=RIGHT))

        bw, bp = blane(YW2, "weight, kg", LOAF_C), blane(YP2, "price per kg", JAM_C)
        bz, bl2 = blane(YZ, "zip", PACK_C), blane(YL, "combineLatest", PACK_C)
        W = [("1.5", 0), ("2.0", 300)]
        P = [("20", 100), ("22", 200), ("21", 400)]
        wch = [chip_n(v, LOAF_C).move_to([BX(t), YW2, 0]) for v, t in W]
        pch = [chip_n(v, JAM_C).move_to([BX(t), YP2, 0]) for v, t in P]
        self.say("board")
        self.play(FadeIn(b_axis), FadeIn(bw), FadeIn(bp), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, scale=0.7) for c in wch], lag_ratio=0.4), run_time=0.9)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, scale=0.7) for c in pch], lag_ratio=0.35), run_time=1.1)
        self.hold()

        self.say("board_q")
        self.play(FadeIn(bz), run_time=0.5)
        self.hold(after=0)
        self.predict()

        def combine(wc, pc, val, t, y, flash=None):
            res = chip_n(val, PACK_C).move_to([BX(t), y, 0])
            a, b = wc.copy(), pc.copy()
            self.add(a, b)
            anims = [a.animate.move_to(res).set_opacity(0), b.animate.move_to(res).set_opacity(0), FadeIn(res, scale=0.7)]
            if flash is not None:
                anims.append(Indicate(flash, color=WHITE, scale_factor=1.15))
            self.play(*anims, run_time=0.6)
            self.remove(a, b)
            return res

        self.say("board_zip")
        z1 = combine(wch[0], pch[0], "30", 100, YZ)
        z2 = combine(wch[1], pch[1], "44", 300, YZ)
        z_end = end_bar(BX(300) + 0.5, YZ, WHITE)
        self.play(FadeIn(z_end), run_time=0.3)
        self.at(2)
        miss = VGroup(cross_at(pch[2].get_center() + DOWN * 0.0, 0.2))
        self.play(Circumscribe(pch[1], color=WHITE, buff=0.06), run_time=0.7)
        self.play(FadeIn(miss), run_time=0.4)
        self.hold()

        self.say("board_cl_q")
        self.play(FadeIn(bl2), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("board_cl")
        c1 = combine(wch[0], pch[0], "30", 100, YL)
        c2 = combine(wch[0], pch[1], "33", 200, YL, flash=wch[0])
        c3 = combine(wch[1], pch[1], "44", 300, YL, flash=pch[1])
        c4 = combine(wch[1], pch[2], "42", 400, YL, flash=wch[1])
        outz = VGroup(M("zip:           [30.000, 44.000]", 22), M("combineLatest: [30.000, 33.000, 44.000, 42.000]", 22))
        outz.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -2.4, 0])
        self.at(1)
        self.play(FadeIn(outz, shift=UP * 0.1), run_time=0.6)
        self.hold()

        polite = T("a zip board waits for the customer and the owner to take turns", 24, GREY_B).move_to([0, -3.15, 0])
        fit(polite, 12.4)
        self.say("board_joke")
        self.play(FadeIn(polite, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(c1, c2, c3, c4), color=WHITE, scale_factor=1.08), run_time=0.8)
        self.at_text("zip shows", lead=0.3)
        self.play(Indicate(VGroup(z1, z2), color=WHITE, scale_factor=1.08), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= two questions, four answers =================
        hdr = VGroup(T("switched on", 26, SLIP_C), T("out comes", 26, SLIP_C))
        rows = [("merge", "all at once", "each item, as it arrives"),
                ("concat", "the next, after the bell", "each item, one belt at a time"),
                ("zip", "all at once", "one from each, paired by position"),
                ("combineLatest", "all at once", "a new value on every change")]
        CX = [-6.2, -2.55, 1.75]
        hdr[0].move_to([CX[1], 2.3, 0], aligned_edge=LEFT)
        hdr[1].move_to([CX[2], 2.3, 0], aligned_edge=LEFT)
        rule_ln = Line([-6.3, 1.9, 0], [6.4, 1.9, 0], stroke_width=1.5, color=GREY_D)
        trows = []
        for i, (a, b, c) in enumerate(rows):
            y = 1.3 - 0.85 * i
            trows.append(VGroup(M(a, 26, PACK_C).move_to([CX[0], y, 0], aligned_edge=LEFT),
                                T(b, 26).move_to([CX[1], y, 0], aligned_edge=LEFT),
                                T(c, 26).move_to([CX[2], y, 0], aligned_edge=LEFT)))
        table = VGroup(hdr, rule_ln, *trows)
        fit(table, 12.8)
        self.say("table")
        self.play(FadeIn(hdr), Create(rule_ln), run_time=0.6)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(trows[i], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(table), run_time=0.6)

        # ================= the code, last =================
        jsrc = ["Mono<BigDecimal> safeDiscount = discount.defaultIfEmpty(BigDecimal.ZERO);",
                "Mono<BigDecimal> safePrice = price.switchIfEmpty(",
                '        Mono.error(() -> new IllegalStateException("missing price")));',
                "Mono<Quote> quote = Mono.zip(safePrice, deliveryFee, safeDiscount)",
                "        .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));"]
        ksrc = ["val safeDiscount = discount.defaultIfEmpty(BigDecimal.ZERO)",
                "val safePrice = price.switchIfEmpty(",
                '    Mono.error { IllegalStateException("missing price") })',
                "val quote = Mono.zip(safePrice, deliveryFee, safeDiscount)",
                "    .map { t -> Quote(t.t1, t.t2, t.t3) }"]
        hl = {"defaultIfEmpty": SLIP_C, "switchIfEmpty": SLIP_C}
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        blk = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                     VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(blk, 12.6).move_to([0, 0.2, 0])
        self.say("code")
        self.play(FadeIn(blk, shift=UP * 0.15), run_time=0.9)
        self.at_text("a missing discount", lead=0.3)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=SLIP_C, scale_factor=1.03), run_time=0.9)
        self.at_text("a missing price", lead=0.3)
        self.play(Indicate(VGroup(jc[1:3], kc[1:3]), color=SLIP_C, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(blk), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Are they all names for “put these together”? No.", 32).move_to(UP * 2.5)
        m1 = T("When is each belt switched on? When does something come out?", 30, SLIP_C).move_to(UP * 1.7)
        m2 = T("And with zip: what if a belt arrives empty?", 30, SLIP_C).move_to(UP * 1.0)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, SLIP_C), M("Mono.zip(orderBook.save(order), prices.forCake(cake))", 24)).arrange(RIGHT, buff=0.25),
                    T("the save is a Mono<Void> done after 20 ms; the price takes 100 ms.", 26),
                    T("What comes out, and when?", 26)).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.45)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict()
        ans = VGroup(T("nothing, at about 20 ms: empty, and the price lookup is cancelled", 28, LOAF_C),
                     M("orderBook.save(order).then(prices.forCake(cake))", 24, PACK_C)).arrange(DOWN, buff=0.25)
        fit(ans, 12.4).move_to(DOWN * 2.2)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
