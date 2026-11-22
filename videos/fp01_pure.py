from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bflourToBuy\b", "flour to buy"), (r"\bgramsToBuy\b", "grams to buy"), (r"\bgramsFor\b", "grams for"),
    (r"\bisFresh\b", "is fresh"), (r"\btotalGrams\b", "total grams"), (r"LocalDate\.now\(\)", "local date dot now"),
    (r"\bLocalDate\b", "local date"), (r"\bShoppingList\b", "shopping list"), (r"\bmillilitres\b", "milliliters"),
]

# every spoken line, in order
N = {
    "open": "Picture a recipe card for pancakes. 200 grams of flour, two eggs, 300 millilitres of milk, makes eight. "
            "Follow it with the same ingredients, and you get the same eight pancakes, every time. And the kitchen "
            "ends up the way you found it, apart from a pan to wash.",
    "cook2": "Now picture a second cook with the same card. She glances at the clock, and makes half a batch, because "
             "it's late. She weighs the flour on a scale someone left set to ounces. And she eats a spoonful of batter "
             "on the way. Same card, same ingredients, different pancakes.",
    "shyq": "So here's a question that's easy to be shy about. My function has one parameter. How can it have more "
            "inputs than that? And why would a test even care?",
    "helper": "Here's a small piece of a recipe app. Before you cook, it looks in the cupboard and tells you how much "
              "flour to buy. The shop only sells whole bags of one kilo, so it rounds up.",
    "hidden": "Now look inside. It takes the bag from Cupboard, a global object that any part of the program can "
              "change. It asks LocalDate.now() for today's date, and a bag past its best-before date counts as empty. "
              "And it writes a line on the shopping list. Two inputs and one output that the signature never "
              "mentions.",
    "test": "Now a test. The bag in the cupboard has 700 grams left, and it's good until the 31st of March. We need "
            "1500 grams, so 800 are missing, and we buy one bag: 1000. The test expects 1000, and it passes all "
            "through March.",
    "test_q": "Nobody touches the code. What does the same test say on the first of April?",
    "test_a": "It fails. It got 2000. On the first of April the bag is past its date, so it counts as empty, and we "
              "need two bags. The test didn't break. Its flour went off.",
    "order": "Order matters too. In the lesson's demo, a second test puts a new bag in the cupboard and never takes "
             "it out. Run the two tests in the other order, and the first one fails: expected 800, got 0. And the "
             "line that broke it isn't even in the test that failed.",
    "wish": "The usual fixes add machinery. A fake clock that always says the same day. A reset of the cupboard "
            "before every test. Clearing the list after it. That's a lot of babysitting for one small function. "
            "Wouldn't it be nice to just hand it everything it needs?",
    "map": "Let's go back to the two cooks and map it. The card is the function. The ingredients on it are its "
           "arguments. The pancakes are the return value. The clock, and the scale left on ounces, are inputs nobody "
           "passed in. And eating the batter, like writing the shopping list, changes the kitchen.",
    "name": "Now we can give it a name. A pure function follows two rules. One: its result depends only on its "
            "arguments, so the same values always give the same answer. Two: calling it changes nothing outside it. "
            "Break either rule, and the function is impure.",
    "terms": "Anything a call does besides handing back its value is a side effect: writing a file, printing, "
             "changing a field. And anything it reads that can change, like the clock, a random number or a global, "
             "is a hidden input.",
    "quiz_q": "Let's try three. gramsFor turns cups into grams with a constant. isFresh compares a bag's date with "
              "LocalDate.now(). And totalGrams sorts the list you gave it, then adds up the grams. Which of them are "
              "pure?",
    "quiz_a": "Only the first. isFresh reads the calendar, a hidden input. And totalGrams returns the right total, "
              "but it reorders the caller's list. The answer is right, and it's still not pure. That one bites in "
              "practice.",
    "fix": "So here's the fix. Move every input into the parameter list. gramsToBuy takes the grams you need, the "
           "bag, and today's date. Nothing is read from outside, and nothing is written. The grams come back as the "
           "return value, and that's all.",
    "test2": "Now the test is plain values. The 31st of March gives 1000, the first of April gives 2000, two lines "
             "side by side. No fake clock, no reset, no clean up. Run them in any order, even on eight threads at "
             "once, because nothing is shared.",
    "joke": "The calendar can turn all it likes. This test brought its own date. So the point really is: a function "
            "that reads only its arguments is tested with plain values.",
    "breaks": "The card picture breaks in one place. A real recipe never gives exactly the same pancakes twice, "
              "because eggs and pans differ. A pure function gives the same value every time, to the last digit. "
              "That's stronger than any kitchen.",
    "guard": "One honest limit. Kotlin has no pure keyword, and neither compiler checks it. The clues are in the "
             "signature: plain values in, a real return type instead of Unit or void, and no clock, file or logger "
             "inside. And a real app still has to read the cupboard and write the list. The end of the lesson "
             "pushes that work out to the edge.",
    "moral": "So, how can a function have more inputs than parameters? By peeking, at the clock and at a global. A "
             "pure function doesn't peek, and it doesn't touch. Pass everything in.",
    "check": "Quick check. portion divides the grams by four, and also adds one to a shared counter. Pure or not?",
    "check_a": "Not pure. The portion is right, but bumping a shared counter is a side effect.",
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

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole fp track (a recipe book and a kitchen scale)
CARD, ARG, OUT, HIDDEN, EFFECT, COOK, PURE = TEAL_M, BLUE_M, GREEN_M, RED_M, PURPLE_M, BLUE_M, YELLOW_M
PAPER = "#EDE6D6"


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def recipe_card(title, lines, w=3.4, size=24):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.75 + 0.48 * len(lines)).set_stroke(CARD, 3)
    r.set_fill(dim(CARD, 0.12), 1)
    head = T(title, 30, CARD).move_to(r.get_top() + DOWN * 0.38)
    rule = Line(LEFT * (w / 2 - 0.25), RIGHT * (w / 2 - 0.25), stroke_width=1.5, color=CARD).next_to(head, DOWN, buff=0.12)
    rows = VGroup(*[T(l, size, GREY_A) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    rows.next_to(rule, DOWN, buff=0.2).align_to(r.get_left() + RIGHT * 0.35, LEFT)
    return VGroup(r, head, rule, rows)


def pancakes(n, color=GOLD_M, s=1.0):
    g = VGroup(*[Ellipse(width=1.3, height=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1) for _ in range(n)])
    g.arrange(UP, buff=-0.1)
    return g.scale(s)


def clock(color=HIDDEN, s=1.0):
    face = Circle(radius=0.38).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    h1 = Line(ORIGIN, UP * 0.24, stroke_width=3, color=color)
    h2 = Line(ORIGIN, RIGHT * 0.17 + DOWN * 0.1, stroke_width=3, color=color)
    return VGroup(face, h1, h2).scale(s)


def kitchen_scale(text, color=HIDDEN, s=1.0):
    plate = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.14).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    base = RoundedRectangle(corner_radius=0.1, width=1.1, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
    base.next_to(plate, DOWN, buff=0.06)
    disp = RoundedRectangle(corner_radius=0.04, width=0.7, height=0.3).set_stroke(color, 2).set_fill(BLACK, 1).move_to(base)
    t = M(text, 18, color).move_to(disp)
    return VGroup(plate, base, disp, t).scale(s)


def spoon(color=HIDDEN, s=1.0):
    bowl_ = Ellipse(width=0.36, height=0.24).set_stroke(color, 2.5).set_fill(dim(GOLD_M, 0.6), 1)
    handle = Line(ORIGIN, RIGHT * 0.7, stroke_width=4, color=color).next_to(bowl_, RIGHT, buff=0)
    return VGroup(bowl_, handle).rotate(0.4).scale(s)


def bag(left, until, s=1.0):
    r = RoundedRectangle(corner_radius=0.14, width=1.9, height=1.5).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.15), 1)
    top = Polygon([-0.95, 0.75, 0], [-0.75, 0.98, 0], [0.75, 0.98, 0], [0.95, 0.75, 0]).set_stroke(GOLD_M, 3)
    top.set_fill(dim(GOLD_M, 0.25), 1)
    t1 = T("flour, 1 kg bag", 20, GOLD_M)
    t2 = T(left, 22, WHITE)
    t3 = T(until, 20, GREY_A)
    tx = VGroup(t1, t2, t3).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, top, tx).scale(s)


def fn_box(label, w=4.2, h=1.1, color=CARD, size=28):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    return VGroup(r, M(label, size, color).move_to(r))


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


class Fp01Pure(Narrated):
    """fp-01, section 1: what makes a function pure. The recipe card and the second cook (clock, a scale on ounces,
    eating batter); flourToBuy with two hidden inputs and a hidden output; the test that passes in March and fails on
    1 April (1000 vs 2000), and the order-dependent pair (expected 800, got 0); the machinery; the map; the two rules
    named; three functions to judge; gramsToBuy with every input a parameter; where the picture breaks; the limit;
    a check."""

    def construct(self):
        self.title_card("Same card, same pancakes", "what makes a function pure")

        # ================= the recipe card =================
        card = recipe_card("Pancakes", ["200 g flour", "2 eggs", "300 ml milk", "makes 8"]).move_to([-3.8, 0.4, 0])
        stack = pancakes(8).move_to([2.6, 0.2, 0])
        st_l = T("8 pancakes", 26, GOLD_M).next_to(stack, DOWN, buff=0.3)
        again = T("same ingredients, same pancakes", 28, CARD).move_to([0, -2.5, 0])
        kit = T("kitchen: as you found it", 26, GREY_A).next_to(again, DOWN, buff=0.2)
        ar = Arrow(card.get_right(), stack.get_left() + LEFT * 0.2, buff=0.25, stroke_width=3, color=GREY_B)
        self.say("open")
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(GrowArrow(ar), LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in stack], lag_ratio=0.12), run_time=1.4)
        self.play(FadeIn(st_l), run_time=0.4)
        self.at(2)
        self.play(FadeIn(again, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(kit), run_time=0.5)
        self.hold()

        # ================= the second cook =================
        cook = person(COOK, 1.2).move_to([-0.3, 0.6, 0])
        ck = clock(HIDDEN, 0.9).move_to([-0.9, 2.5, 0])
        sc = kitchen_scale("oz", HIDDEN, 0.9).move_to([0.9, 2.4, 0])
        sp = spoon(HIDDEN, 1.0).next_to(cook, DOWN, buff=0.2)
        half = pancakes(4).move_to([2.6, 0.2, 0]).align_to(stack, DOWN)
        diff = T("same card, different pancakes", 28, HIDDEN).move_to([0, -2.5, 0])
        qm = T("?", 40, HIDDEN).next_to(half, UP, buff=0.2)
        self.say("cook2")
        self.play(FadeOut(again), FadeOut(kit), FadeIn(cook), ar.animate.set_opacity(0.3), run_time=0.7)
        self.at_text("glances", lead=0.3)
        self.play(FadeIn(ck, scale=0.8), run_time=0.5)
        self.play(Rotate(ck[1], angle=-TAU / 3, about_point=ck[0].get_center()), run_time=0.8)
        self.at_text("makes half", lead=0.3)
        self.play(FadeOut(stack[4:]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sc, scale=0.8), run_time=0.6)
        self.at(3)
        self.play(FadeIn(sp, shift=UP * 0.15), run_time=0.6)
        self.at(4)
        self.play(FadeIn(diff, shift=UP * 0.1), FadeIn(qm), run_time=0.6)
        self.hold()

        q = T("My function has one parameter. How can it have more inputs?", 32).move_to([0, -2.5, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeOut(diff), FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the helper and its hidden wires =================
        fb = fn_box("flourToBuy(neededGrams)", w=5.2).move_to([0, 0.1, 0])
        inp = T("1500 g needed", 26, ARG).move_to([-5.0, 0.1, 0])
        a_in = Arrow(inp.get_right(), fb.get_left(), buff=0.15, stroke_width=3, color=ARG)
        outp = T("grams to buy", 26, OUT).move_to([5.0, 0.1, 0])
        a_out = Arrow(fb.get_right(), outp.get_left(), buff=0.15, stroke_width=3, color=OUT)
        self.say("helper")
        self.play(FadeIn(fb), run_time=0.7)
        self.at(1)
        self.play(FadeIn(inp), GrowArrow(a_in), run_time=0.7)
        self.play(GrowArrow(a_out), FadeIn(outp), run_time=0.7)
        self.hold()

        h1 = M("Cupboard.flour", 24, HIDDEN).move_to([-2.6, 2.6, 0])
        h2 = M("LocalDate.now()", 24, HIDDEN).move_to([2.6, 2.6, 0])
        h3 = M("ShoppingList.lines.add(...)", 24, EFFECT).move_to([0, -2.3, 0])
        w1 = DashedLine(h1.get_bottom() + DOWN * 0.1, fb.get_top() + LEFT * 1.3, dash_length=0.1).set_stroke(HIDDEN, 3)
        w2 = DashedLine(h2.get_bottom() + DOWN * 0.1, fb.get_top() + RIGHT * 1.3, dash_length=0.1).set_stroke(HIDDEN, 3)
        w3 = DashedLine(fb.get_bottom(), h3.get_top() + UP * 0.1, dash_length=0.1).set_stroke(EFFECT, 3)
        hl1 = T("hidden input", 22, HIDDEN).next_to(h1, UP, buff=0.12)
        hl2 = T("hidden input", 22, HIDDEN).next_to(h2, UP, buff=0.12)
        hl3 = T("hidden output", 22, EFFECT).next_to(h3, DOWN, buff=0.12)
        self.say("hidden")
        self.at(1)
        self.play(FadeIn(h1), Create(w1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(h2), Create(w2), run_time=0.8)
        self.at(3)
        self.play(Create(w3), FadeIn(h3), run_time=0.8)
        self.at(4)
        self.play(FadeIn(hl1), FadeIn(hl2), FadeIn(hl3), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the test that passes in March =================
        bg = bag("700 g left", "best before 31 Mar").move_to([-4.6, 1.0, 0])
        tl = M("assertEquals(1000, flourToBuy(1500))", 26).move_to([1.3, 1.0, 0])
        fit(tl, 7.6)
        arith = VGroup(T("need 1500, have 700: 800 missing", 26, GREY_A),
                       T("whole bags only: buy 1000", 26, OUT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        arith.move_to([1.3, -0.35, 0]).align_to(tl, LEFT)
        cal = chip("March", ARG, 26).move_to([-4.6, -1.6, 0])
        ok1 = check(tl)
        self.say("test")
        self.play(FadeIn(bg, shift=UP * 0.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(arith[0]), run_time=0.6)
        self.at_text("and we buy", lead=0.3)
        self.play(FadeIn(arith[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(tl), FadeIn(cal), run_time=0.7)
        self.play(Create(ok1), run_time=0.4)
        self.hold()

        cal2 = chip("1 April", HIDDEN, 26).move_to(cal)
        self.say("test_q")
        self.play(Transform(cal, cal2), run_time=0.8)
        self.hold(after=0)
        self.predict()
        got = T("got 2000", 28, HIDDEN).next_to(tl, DOWN, buff=1.4).align_to(tl, LEFT)
        x1 = cross(tl)
        why = T("past its date: counts as empty, so two bags", 26, GREY_A).next_to(got, DOWN, buff=0.2).align_to(got, LEFT)
        off = T("The test didn't break. Its flour went off.", 30, GOLD_M).move_to([0, -3.0, 0])
        self.say("test_a")
        self.play(FadeOut(ok1), Create(x1), FadeOut(arith), run_time=0.6)
        self.play(FadeIn(got), run_time=0.5)
        self.at(2)
        self.play(FadeIn(why), bg[2][2].animate.set_color(HIDDEN), run_time=0.7)
        self.at(3)
        self.play(FadeIn(off, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= order matters =================
        ttl = T("the lesson's demo, two tests sharing Cupboard", 26, GREY_B).move_to([0, 2.4, 0])
        o1 = VGroup(T("written order", 26, GREY_A), M("halfBag: pass", 26, OUT), M("newBag: pass", 26, OUT))
        o2 = VGroup(T("reversed", 26, GREY_A), M("newBag: pass", 26, OUT), M("halfBag: FAIL (expected 800, got 0)", 26, HIDDEN))
        for g in (o1, o2):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fit(o2, 6.6)
        o1.move_to([-6.0, 0.6, 0], aligned_edge=UP + LEFT)
        o2.move_to([-0.3, 0.6, 0], aligned_edge=UP + LEFT)
        note = VGroup(M("Cupboard.flourLeft = 1_700", 24, HIDDEN), T("set by newBag, never put back", 24, GREY_A))
        note.arrange(DOWN, buff=0.15).move_to([0.4, -1.9, 0])
        self.say("order")
        self.play(FadeIn(ttl), run_time=0.5)
        self.at(1)
        self.play(FadeIn(o1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(o2[0]), FadeIn(o2[1]), run_time=0.5)
        self.play(FadeIn(o2[2]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the machinery, and the wish =================
        fb2 = fn_box("flourToBuy(neededGrams)", w=5.2).move_to([0, 1.8, 0])
        mach = VGroup(chip("a fake clock: Clock.fixed(...)", GREY_B, 26), chip("reset Cupboard before each test", GREY_B, 26),
                      chip("clear the list after each test", GREY_B, 26)).arrange(DOWN, buff=0.25).move_to([0, -0.6, 0])
        wish = T("just hand it everything it needs", 30, PURE).move_to([0, -2.85, 0])
        self.say("wish")
        self.play(FadeIn(fb2), run_time=0.5)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(mach[i], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(Wiggle(mach, scale_value=1.04, rotation_angle=0.015 * TAU), run_time=0.9)
        self.at(5)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= map the picture =================
        hp = T("the kitchen", 28, GREY_B).move_to([-3.3, 2.7, 0])
        hc = T("the code", 28, GREY_B).move_to([3.0, 2.7, 0])
        rows = [("the recipe card", "the function", CARD), ("the ingredients", "its arguments", ARG),
                ("the pancakes", "the return value", OUT), ("the clock, the scale on ounces", "hidden inputs", HIDDEN),
                ("eating the batter", "a side effect", EFFECT)]
        Y = [1.75, 0.85, -0.05, -0.95, -1.85]
        mrows = VGroup()
        for (a, b, c), y in zip(rows, Y):
            ta = T(a, 28, c).move_to([-3.3, y, 0])
            tb = T(b, 28, c).move_to([3.0, y, 0])
            ln = Arrow([-0.6, y, 0], [1.0, y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.15)
            mrows.add(VGroup(ta, ln, tb))
        self.say("map")
        self.play(FadeIn(hp), FadeIn(hc), run_time=0.5)
        for i in range(5):
            self.at(i + 1)
            self.play(FadeIn(mrows[i], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name it =================
        nm = T("a pure function", 44, PURE).move_to([0, 2.4, 0])
        r1 = VGroup(T("1", 30, PURE), T("its result depends only on its arguments", 30)).arrange(RIGHT, buff=0.35)
        r2 = VGroup(T("2", 30, PURE), T("calling it changes nothing outside it", 30)).arrange(RIGHT, buff=0.35)
        rr = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.9, 0])
        imp = T("break either rule: impure", 28, HIDDEN).move_to([0, -0.4, 0])
        self.say("name")
        self.play(Write(nm), run_time=1.0)
        self.at(2)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(imp), run_time=0.5)
        self.hold()

        se = VGroup(T("side effect:", 28, EFFECT), T("anything besides handing back the value", 28, GREY_A)).arrange(RIGHT, buff=0.25)
        hi = VGroup(T("hidden input:", 28, HIDDEN), T("anything it reads that can change", 28, GREY_A)).arrange(RIGHT, buff=0.25)
        defs = VGroup(se, hi).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -1.9, 0])
        fit(defs, 12.4)
        self.say("terms")
        self.play(FadeIn(se, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(hi, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= three to judge =================
        qs = VGroup(M("fun gramsFor(cups: Int) = cups * FLOUR_PER_CUP", 24),
                    M("fun isFresh(bag: Bag) = !LocalDate.now().isAfter(bag.bestBefore)", 24),
                    M("fun totalGrams(items: MutableList<Item>): Int {", 24),
                    M("    items.sortBy { it.name }; return items.sumOf { it.grams } }", 24))
        qs.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        qs[3].shift(RIGHT * 0.5)
        fit(qs, 11.6).move_to([-0.3, 0.9, 0])
        cnote = T("FLOUR_PER_CUP is a const val", 22, GREY_B).next_to(qs, UP, buff=0.35).align_to(qs, LEFT)
        nums = VGroup(*[T(s, 26, GREY_B).next_to(qs[i], LEFT, buff=0.25) for i, s in ((0, "1"), (1, "2"), (2, "3"))])
        self.say("quiz_q")
        self.at(1)
        self.play(FadeIn(qs[0]), FadeIn(nums[0]), FadeIn(cnote), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qs[1]), FadeIn(nums[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(qs[2:]), FadeIn(nums[2]), run_time=0.6)
        self.hold(after=0)
        self.predict()
        a1 = tick(True, 0.22).move_to([5.9, qs[0].get_y(), 0])
        a2 = tick(False, 0.22).move_to([5.9, qs[1].get_y(), 0])
        a3 = tick(False, 0.22).move_to([5.9, (qs[2].get_y() + qs[3].get_y()) / 2, 0])
        e2 = T("reads the calendar: a hidden input", 26, HIDDEN).move_to([0, -1.2, 0])
        e3 = T("right total, but it reorders the caller's list: a side effect", 26, EFFECT).move_to([0, -1.85, 0])
        fit(e3, 12.4)
        self.say("quiz_a")
        self.play(Create(a1), run_time=0.5)
        self.at(1)
        self.play(Create(a2), FadeIn(e2), run_time=0.6)
        self.at(2)
        self.play(Create(a3), FadeIn(e3), run_time=0.6)
        self.play(Indicate(part_of(qs[3], "items.sortBy"), color=EFFECT), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the fix =================
        pb = fn_box("gramsToBuy", w=3.4).move_to([0, 1.3, 0])
        ins = VGroup(T("neededGrams", 26, ARG), T("bag", 26, ARG), T("today", 26, ARG)).arrange(DOWN, buff=0.4)
        ins.move_to([-4.4, 1.3, 0])
        ain = VGroup(*[Arrow(i.get_right(), pb.get_left() + UP * (0.3 - 0.3 * k), buff=0.15, stroke_width=3, color=ARG)
                       for k, i in enumerate(ins)])
        po = T("grams", 26, OUT).move_to([4.2, 1.3, 0])
        aout = Arrow(pb.get_right(), po.get_left(), buff=0.15, stroke_width=3, color=OUT)
        nothing = T("nothing read from outside, nothing written", 26, PURE).move_to([0, -0.2, 0])
        self.say("fix")
        self.play(FadeIn(pb), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(i), GrowArrow(a)) for i, a in zip(ins, ain)], lag_ratio=0.4), run_time=1.6)
        self.at(3)
        self.play(FadeIn(nothing), run_time=0.6)
        self.at(4)
        self.play(GrowArrow(aout), FadeIn(po), run_time=0.7)
        self.hold()

        jv = VGroup(T("Java", 22, GREY_B), M("static int gramsToBuy(int neededGrams, Bag bag, LocalDate today)", 22))
        kt = VGroup(T("Kotlin", 22, GREY_B), M("fun gramsToBuy(neededGrams: Int, bag: Bag, today: LocalDate): Int", 22))
        tst = VGroup(T("the test, both languages alike", 22, GREY_B),
                     M("assertEquals(1000, gramsToBuy(1500, bag, LocalDate.of(2026, 3, 31)))", 22),
                     M("assertEquals(2000, gramsToBuy(1500, bag, LocalDate.of(2026, 4, 1)))", 22))
        for g in (jv, kt):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        tst.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        code = VGroup(jv, kt, tst).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(code, 12.4).move_to([0, -1.9, 0])
        self.say("test2")
        self.play(FadeOut(nothing), VGroup(pb, ins, ain, po, aout).animate.scale(0.75).move_to([0, 2.55, 0]), run_time=0.8)
        self.play(FadeIn(jv), FadeIn(kt), run_time=0.7)
        self.at(1)
        self.play(FadeIn(tst), run_time=0.7)
        self.at(2)
        self.play(Create(check(tst[1], 0.18)), Create(check(tst[2], 0.18)), run_time=0.6)
        self.hold()

        jk = T("This test brought its own date.", 32, GOLD_M).move_to([0, 1.1, 0])
        self.say("joke")
        self.play(FadeIn(jk, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(tst[2], color=ARG, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= where the picture breaks; the limit =================
        c2 = recipe_card("Pancakes", ["200 g flour", "2 eggs", "300 ml milk", "makes 8"], w=3.0, size=22).move_to([-4.3, 0.9, 0])
        pa = pancakes(8, s=0.8).move_to([-1.1, 1.6, 0])
        pb2 = pancakes(8, s=0.8).move_to([-1.1, 0.2, 0])
        pb2[3].stretch(1.25, 0)
        pb2[6].stretch(0.8, 0)
        rl = T("a kitchen: nearly the same", 26, GREY_A).next_to(pb2, DOWN, buff=0.3)
        fv = VGroup(M("gramsToBuy(1500, bag, 1 Apr)", 24, CARD), M("2000", 30, OUT), M("2000", 30, OUT), M("2000", 30, OUT))
        fv.arrange(DOWN, buff=0.25).move_to([3.7, 1.0, 0])
        fl = T("a pure function: exactly the same", 26, PURE).next_to(fv, DOWN, buff=0.3)
        self.say("breaks")
        self.play(FadeIn(c2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pa), FadeIn(pb2), FadeIn(rl), run_time=0.8)
        self.at(2)
        self.play(FadeIn(fv[0]), LaggedStart(*[FadeIn(x) for x in fv[1:]], lag_ratio=0.4), run_time=1.2)
        self.play(FadeIn(fl), run_time=0.5)
        self.hold()
        self.wipe()

        gl = T("no pure keyword; no compiler checks it", 30, HIDDEN).move_to([0, 2.4, 0])
        clues = VGroup(T("clues in the signature:", 28, GREY_B), T("plain values in", 28, ARG),
                       T("a real return type, not Unit or void", 28, OUT), T("no clock, file or logger inside", 28, HIDDEN))
        clues.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, 0.3, 0])
        edge = T("the cupboard and the list: pushed out to the edge", 28, GREY_A).move_to([0, -2.2, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gl), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in clues], lag_ratio=0.4), run_time=2.0)
        self.at(3)
        self.play(FadeIn(edge), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("More inputs than parameters? It peeks: the clock, a global.", 32).move_to(UP * 2.4)
        m1 = T("A pure function doesn't peek, and doesn't touch.", 34, PURE).move_to(UP * 1.5)
        m2 = T("Pass everything in.", 34, CARD).move_to(UP * 0.7)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = M("fun portion(grams: Int): Int { stats.portions++; return grams / 4 }", 24)
        fit(qq, 12.4).move_to(DOWN * 0.6)
        qh = T("Check: pure or not?", 28, PURE).next_to(qq, UP, buff=0.3)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("not pure: the portion is right, but bumping a shared counter is a side effect", 28, EFFECT)
        fit(ans, 12.4).move_to(DOWN * 2.0)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)


def part_of(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]
