from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bmaxByOrNull\b", "max by or null"), (r"\breduceOrNull\b", "reduce or null"), (r"\bfirstOrNull\b", "first or null"),
    (r"\bOrNull\b", "or null"), (r"\bsumOf\b", "sum of"), (r"\bc([1-5])\b", r"C \1"),
]

# every spoken line, in order
N = {
    "open": "Picture the end of a baking day. Two trays of cookies come out of the oven, five cookies in all: two oat, "
            "two chocolate and one ginger. Most are golden. One chocolate cookie is still raw in the middle, the "
            "ginger one is burnt, and someone has already taken a 10 gram bite out of an oat one.",
    "jar": "There's a cookie jar on the kitchen scale, and it already holds 200 grams. At the end of the day, each "
           "golden cookie goes in, minus any bite. The raw and burnt ones stay out.",
    "shyq": "Here's a question that's easy to be shy about. map and filter make sense. But whenever I need one total, "
            "I'm back to a for loop with a var. Is that wrong? And what is this fold everyone talks about?",
    "loop": "Let's start with the loop we'd all write. jar starts at 200. For each cookie, if it's golden, add its "
            "grams, minus the bite. At the end, jar is the answer.",
    "parts": "Look at its shape. Every loop that builds one result has two parts. A starting value, here 200. And a "
             "step, which takes the result so far and the next cookie, and gives the next result.",
    "walk_q": "Let's walk it cookie by cookie, with the scale. Before we do: where will the scale end up?",
    "walk1": "Start at 200. c1 is a golden oat cookie, 45 grams: 245. c2 is raw, so it stays out: still 245.",
    "walk2": "c3 is golden, 50 grams, but with a 10 gram bite, so 40 more: 285. c4 is burnt: still 285. c5 is golden "
             "chocolate, 30 grams: 315.",
    "map": "Now let's map it. The reading on the scale is the one value you carry from cookie to cookie. The 200 "
           "already in the jar is the starting value. Your rule at each cookie, in or out, is the step. And the last "
           "reading is the answer.",
    "name": "Now the names. The value you carry along is called the accumulator. And fold is that loop, with both "
            "parts passed in: the starting value in parentheses, and the step as a lambda that gets the accumulator "
            "and the next element.",
    "code": "Here's the jar. cookies.fold, starting at 200, with jar and c. A golden cookie gives jar plus its grams, "
            "minus the bite. Raw or burnt gives jar, unchanged. Java's stream reduce takes the same two parts, plus "
            "a third argument that only matters for parallel streams.",
    "inside": "So where did the var go? The standard library's fold is the loop you'd write by hand: a var set to the "
              "start, a for loop, one step per element. And it's inline, so your lambda is pasted right into that "
              "loop. The var didn't disappear. It moved inside fold, where nobody else can touch it, and your own code "
              "has only vals.",
    "special": "You've been using folds already. sumOf, count and maxByOrNull are special cases of fold, already "
               "written and named. The sum of all five weights is 295, and three cookies are golden. Prefer them when "
               "they fit: sumOf says more than a fold that adds. Reach for fold when the step needs a when, like the "
               "jar does.",
    "reduce": "And then there's reduce. It looks like fold without the starting value: it uses the first element as "
              "the start instead. It's shorter, and on a normal day it gives the same answer, 295. So why ever type "
              "a starting value?",
    "reduce_q": "Here's a day when nothing was baked: an empty list of weights. fold starting at 0, sum, and reduce. "
                "What does each one give?",
    "reduce_a": "fold gives 0. sum gives 0. And reduce throws: Empty collection can't be reduced. first fails the same "
                "way: List is empty.",
    "why": "Think of the jar. On an empty day, fold still has a jar on the scale, and the scale shows the starting "
           "value. reduce has nothing to put on the scale at all, so all it can do is complain. A quiet day in the "
           "kitchen isn't an emergency. reduce treats it like one.",
    "ornull": "Kotlin gives you two names. reduce throws, and reduceOrNull gives null. first throws, and firstOrNull "
              "gives null. Java chose differently. Its reduce without a starting value returns an Optional, a box "
              "that may be empty, so the type makes you handle the empty day.",
    "breaks": "The jar picture has one limit. A scale shows one number, but an accumulator can be anything: a list, a "
              "map, even a function. The last lesson folded a list of recipe adjustments into one function, starting "
              "from a function that changes nothing.",
    "guard": "So here's the rule. An empty list is a normal day. Use fold, sumOf, or an OrNull function whenever the "
             "input can be empty. Keep reduce and first for places where an empty list is a bug you want to hear "
             "about, loudly.",
    "moral": "So, is the for loop with a var wrong? No. It's a fold, written out by hand. fold is that loop, with the "
             "start and the step passed in, and the var tucked away inside.",
    "check": "Quick check. A day with no cookies at all. cookies.fold, starting at 200, with the jar rule. What does the "
             "scale show?",
    "check_a": "200. With nothing to add, fold hands back the starting value. That's exactly why it never throws.",
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
    r = RoundedRectangle(corner_radius=0.14, width=2.8, height=1.6).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.15), 1)
    top = Polygon([-1.4, 0.8, 0], [-1.2, 1.03, 0], [1.2, 1.03, 0], [1.4, 0.8, 0]).set_stroke(GOLD_M, 3)
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


def part_of(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


GOLDEN, RAWC, BURNT, ACC = GOLD_M, GREY_A, "#B5653A", YELLOW_M

# the lesson's sample day: id, flavor, grams, status, bite
DAY = [("c1", "oat", 45, "golden", 0), ("c2", "chocolate", 90, "raw", 0), ("c3", "oat", 50, "golden", 10),
       ("c4", "ginger", 80, "burnt", 0), ("c5", "chocolate", 30, "golden", 0)]


def cookie(status, bite=0, r=0.42):
    if status == "golden":
        c = Circle(radius=r).set_stroke(GOLDEN, 3).set_fill(dim(GOLDEN, 0.45), 1)
    elif status == "raw":
        c = DashedVMobject(Circle(radius=r), num_dashes=18).set_stroke(RAWC, 3)
        c = VGroup(Circle(radius=r).set_stroke(width=0).set_fill(dim(RAWC, 0.25), 1), c)
    else:
        c = Circle(radius=r).set_stroke(BURNT, 3).set_fill(dim(BURNT, 0.55), 1)
    chips = VGroup(*[Dot(radius=0.045, color=GREY_E if status != "raw" else GREY_C).move_to([dx, dy, 0])
                     for dx, dy in ((-0.15, 0.1), (0.12, 0.16), (0.02, -0.15), (0.2, -0.05))]).scale(r / 0.42)
    g = VGroup(c, chips)
    if bite:
        nib = Circle(radius=r * 0.38).set_stroke(width=0).set_fill(BLACK, 1).move_to(g.get_center() + np.array([r * 0.8, r * 0.6, 0]))
        g.add(nib)
    return g


def cookie_tag(i, r=0.42):
    cid, fl, gr, st, bt = DAY[i]
    ck = cookie(st, bt, r)
    col = {"golden": GOLDEN, "raw": RAWC, "burnt": BURNT}[st]
    l1 = M(cid, 22, col)
    l2 = T(f"{fl}, {gr} g", 20, GREY_A)
    lbl = VGroup(l1, l2).arrange(DOWN, buff=0.06).next_to(ck, DOWN, buff=0.12)
    return VGroup(ck, lbl)


def jar_on_scale(reading="200 g", s=1.0):
    body = RoundedRectangle(corner_radius=0.25, width=1.5, height=1.5).set_stroke(GREY_A, 3).set_fill(dim(GREY_A, 0.08), 1)
    lid = RoundedRectangle(corner_radius=0.08, width=1.2, height=0.22).set_stroke(GREY_A, 3).set_fill(dim(GREY_A, 0.2), 1)
    lid.next_to(body, UP, buff=0.04)
    plate = RoundedRectangle(corner_radius=0.05, width=2.3, height=0.14).set_stroke(ACC, 2.5).set_fill(dim(ACC, 0.3), 1)
    plate.next_to(body, DOWN, buff=0.02)
    base = RoundedRectangle(corner_radius=0.12, width=2.1, height=0.8).set_stroke(ACC, 3).set_fill(dim(ACC, 0.12), 1)
    base.next_to(plate, DOWN, buff=0.04)
    disp = RoundedRectangle(corner_radius=0.06, width=1.5, height=0.5).set_stroke(ACC, 2).set_fill(BLACK, 1).move_to(base)
    txt = M(reading, 28, ACC).move_to(disp)
    return VGroup(body, lid, plate, base, disp, txt).scale(s)


class Fp04Fold(Narrated):
    """fp-04, section 2: the loop you were writing is a fold. The baking day (five cookies); the jar on the scale at
    200 g; the hand-written loop and its two parts; the walk 200, 245, 245, 285, 285, 315; the map; accumulator and
    fold named; Kotlin fold and Java reduce; the stdlib fold with the var inside; sumOf/count/maxByOrNull as named
    folds (295, 3); reduce steelmanned and broken on an empty day (EmptyTraps output); the jar explains why; the
    OrNull pair and Java's Optional; where the picture stops; the rule; a check."""

    def construct(self):
        self.title_card("The jar on the scale", "the loop you were writing is a fold")

        # ================= the baking day =================
        tray1 = RoundedRectangle(corner_radius=0.15, width=5.6, height=2.4).set_stroke(GREY_B, 2.5).move_to([-3.2, 0.5, 0])
        tray2 = RoundedRectangle(corner_radius=0.15, width=4.0, height=2.4).set_stroke(GREY_B, 2.5).move_to([3.6, 0.5, 0])
        tags = VGroup(*[cookie_tag(i) for i in range(5)])
        for t, x in zip(tags, (-4.9, -3.2, -1.5, 2.6, 4.6)):
            t.move_to([x, 0.5, 0])
        tl1 = T("tray 1", 22, GREY_B).next_to(tray1, UP, buff=0.12)
        tl2 = T("tray 2", 22, GREY_B).next_to(tray2, UP, buff=0.12)
        self.say("open")
        self.play(Create(tray1), Create(tray2), FadeIn(tl1), FadeIn(tl2), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in tags], lag_ratio=0.2), run_time=1.4)
        self.at(2)
        self.play(*[Indicate(tags[i][0], color=GOLDEN, scale_factor=1.12) for i in (0, 2, 4)], run_time=0.9)
        self.at(3)
        self.play(Indicate(tags[1][0], color=RAWC, scale_factor=1.12), run_time=0.7)
        self.at_text("the ginger", lead=0.3)
        self.play(Indicate(tags[3][0], color=BURNT, scale_factor=1.12), run_time=0.7)
        self.at_text("and someone", lead=0.3)
        bite = T("10 g bite", 20, HIDDEN).next_to(tags[2][0], UP, buff=0.1)
        self.play(FadeIn(bite), Indicate(tags[2][0][2], color=HIDDEN, scale_factor=1.4), run_time=0.9)
        self.hold()

        day = VGroup(tray1, tray2, tl1, tl2, tags, bite)
        jar = jar_on_scale().move_to([0, -2.0, 0])
        rule = VGroup(T("golden: in, minus any bite", 24, GOLDEN), T("raw or burnt: stays out", 24, GREY_A))
        rule.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.9, -2.2, 0])
        self.say("jar")
        self.play(day.animate.scale(0.9).move_to([0, 1.95, 0]), run_time=0.9)
        self.play(FadeIn(jar, shift=UP * 0.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rule[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rule[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(day, jar, rule)), run_time=0.6)

        q = T("I need one total, and I'm back to a for loop with a var. Is that wrong?", 30).move_to([0, 0.4, 0])
        fit(q, 12.4)
        q2 = T("And what is fold?", 30, ACC).next_to(q, DOWN, buff=0.3)
        self.say("shyq")
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(q2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the loop and its two parts =================
        kl = code_block(["var jar = 200", "for (c in cookies) {",
                         "    if (c.status == GOLDEN) jar += c.grams - (c.nibbledGrams ?: 0)", "}"], 24)
        jl = code_block(["int jar = 200;", "for (Cookie c : cookies)",
                         "    if (c.status() == GOLDEN) jar += c.grams() - biteOf(c);"], 24)
        kg = VGroup(T("Kotlin", 22, GREY_B), kl).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        jg = VGroup(T("Java", 22, GREY_B), jl).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cg = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cg, 12.2).move_to([0, 0.6, 0])
        self.say("loop")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.9)
        self.hold()
        s1 = VGroup(SurroundingRectangle(part_of(kl[0], "200"), color=ACC, buff=0.07),
                    SurroundingRectangle(part_of(jl[0], "200"), color=ACC, buff=0.07))
        s2 = VGroup(SurroundingRectangle(part_of(kl[2], "jar += c.grams - (c.nibbledGrams ?: 0)"), color=CARD, buff=0.07),
                    SurroundingRectangle(part_of(jl[2], "jar += c.grams() - biteOf(c);"), color=CARD, buff=0.07))
        p1 = T("a starting value", 28, ACC).move_to([-3.3, -2.7, 0])
        p2 = T("a step: result so far + next cookie", 28, CARD).move_to([2.6, -2.7, 0])
        self.say("parts")
        self.at(2)
        self.play(Create(s1), FadeIn(p1), run_time=0.7)
        self.at(3)
        self.play(Create(s2), FadeIn(p2), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the walk =================
        row = VGroup(*[cookie_tag(i, 0.38) for i in range(5)]).arrange(RIGHT, buff=0.9).move_to([0, 2.2, 0])
        jar = jar_on_scale().move_to([0, -1.6, 0])
        self.say("walk_q")
        self.play(FadeIn(row), FadeIn(jar), run_time=0.8)
        self.hold(after=0)
        self.predict()
        readings = ["245 g", "245 g", "285 g", "285 g", "315 g"]
        notes = ["+45", "stays out", "+50 - 10", "stays out", "+30"]

        def step(i):
            ck = row[i][0]
            nt = T(notes[i], 24, GOLDEN if DAY[i][3] == "golden" else GREY_A).next_to(row[i], DOWN, buff=0.2)
            new = M(readings[i], 28, ACC).move_to(jar[5])
            if DAY[i][3] == "golden":
                mover = ck.copy()
                self.play(FadeIn(nt), mover.animate.move_to(jar[0].get_center()).scale(0.6), run_time=0.9)
                self.play(FadeOut(mover), Transform(jar[5], new), ck.animate.set_opacity(0.25), run_time=0.5)
            else:
                x = tick(False, 0.2).move_to(ck)
                self.play(FadeIn(nt), Create(x), run_time=0.6)
                self.play(Indicate(jar[5], color=ACC), run_time=0.5)

        self.say("walk1")
        self.at(1)
        step(0)
        self.at(2)
        step(1)
        self.hold()
        self.say("walk2")
        step(2)
        self.at(1)
        step(3)
        self.at(2)
        step(4)
        self.hold()
        fin = T("315 g", 34, ACC).next_to(jar, RIGHT, buff=0.6)
        self.play(Circumscribe(jar[4], color=ACC), FadeIn(fin), run_time=0.9)
        self.wipe()

        # ================= map =================
        hp = T("the kitchen", 28, GREY_B).move_to([-3.3, 2.7, 0])
        hc = T("the code", 28, GREY_B).move_to([3.0, 2.7, 0])
        rows = [("the reading you carry along", "one value, carried", ACC), ("200 g already in the jar", "the starting value", ACC),
                ("in or out, at each cookie", "the step", CARD), ("the last reading", "the result", OUT)]
        Y = [1.6, 0.6, -0.4, -1.4]
        mrows = VGroup()
        for (a, b, c), y in zip(rows, Y):
            ta = T(a, 28, c).move_to([-3.3, y, 0])
            tb = T(b, 28, c).move_to([3.4, y, 0])
            ln = Arrow([-0.2, y, 0], [1.4, y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.15)
            mrows.add(VGroup(ta, ln, tb))
        self.say("map")
        self.play(FadeIn(hp), FadeIn(hc), run_time=0.5)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mrows[i], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name it =================
        nm = T("the accumulator", 42, ACC).move_to([0, 2.4, 0])
        nd = T("the value carried from one step to the next", 26, GREY_A).next_to(nm, DOWN, buff=0.2)
        sig = M("fold(initial) { acc, element -> next acc }", 30)
        sig.move_to([0, -0.2, 0])
        fit(sig, 12.2)
        b1 = Brace(part_of(sig, "(initial)"), DOWN, color=ACC)
        b1l = T("starting value", 24, ACC).next_to(b1, DOWN, buff=0.1)
        b2 = Brace(part_of(sig, "{ acc, element -> next acc }"), DOWN, color=CARD)
        b2l = T("the step", 24, CARD).next_to(b2, DOWN, buff=0.1)
        self.say("name")
        self.play(Write(nm), run_time=0.9)
        self.play(FadeIn(nd), run_time=0.4)
        self.at(2)
        self.play(FadeIn(sig, shift=UP * 0.1), run_time=0.7)
        self.at_text("the starting value", lead=0.3)
        self.play(GrowFromCenter(b1), FadeIn(b1l), run_time=0.6)
        self.at_text("and the step", lead=0.3)
        self.play(GrowFromCenter(b2), FadeIn(b2l), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the code =================
        kf = code_block(["val jar = cookies.fold(200) { jar, c ->", "    when (c.status) {",
                         "        Status.GOLDEN -> jar + c.grams - (c.nibbledGrams ?: 0)",
                         "        Status.RAW, Status.BURNT -> jar", "    }", "}"], 24, {"200": ACC})
        jf = code_block(["int jar = cookies.stream().reduce(200,",
                         "        (acc, c) -> c.status() == GOLDEN ? acc + c.grams() - biteOf(c) : acc,",
                         "        Integer::sum);   // only matters for parallel streams"], 24, {"200": ACC})
        kfg = VGroup(T("Kotlin", 22, GREY_B), kf).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        jfg = VGroup(T("Java", 22, GREY_B), jf).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fg_ = VGroup(kfg, jfg).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(fg_, 12.4).move_to([0, 0.2, 0])
        self.say("code")
        self.play(FadeIn(kfg, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(kf[2], color=GOLDEN, scale_factor=1.03), run_time=0.9)
        self.at(3)
        self.play(Indicate(kf[3], color=GREY_A, scale_factor=1.03), run_time=0.8)
        self.at(4)
        self.play(FadeIn(jfg, shift=UP * 0.1), run_time=0.8)
        self.at_text("plus a third", lead=0.3)
        self.play(Indicate(jf[2], color=GREY_A, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= inside fold =================
        src = code_block(["inline fun <T, R> Iterable<T>.fold(",
                          "        initial: R, operation: (acc: R, T) -> R): R {",
                          "    var accumulator = initial",
                          "    for (element in this)",
                          "        accumulator = operation(accumulator, element)",
                          "    return accumulator", "}"], 24)
        sl = T("Kotlin's standard library", 22, GREY_B)
        sg = VGroup(sl, src).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(sg, 12.4).move_to([0, 0.9, 0])
        house = SurroundingRectangle(src[2:6], color=ACC, buff=0.12)
        hl = T("the var lives in here", 26, ACC).next_to(house, DOWN, buff=0.25)
        yours = VGroup(T("your code:", 26, GREY_B), M("val jar = cookies.fold(200) { ... }", 26, CARD)).arrange(RIGHT, buff=0.3)
        yours.move_to([0, -2.4, 0])
        self.say("inside")
        self.at(1)
        self.play(FadeIn(sg, shift=UP * 0.1), run_time=0.9)
        self.play(Indicate(src[2], color=ACC, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(Indicate(part_of(src[0], "inline"), color=CARD), run_time=0.8)
        self.at(3)
        self.play(Create(house), FadeIn(hl), run_time=0.8)
        self.at_text("and your own", lead=0.3)
        self.play(FadeIn(yours), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= named folds =================
        nf = VGroup(VGroup(M("sumOf { it.grams }", 28, CARD), M("295", 28, OUT)),
                    VGroup(M("count { it.status == GOLDEN }", 28, CARD), M("3", 28, OUT)),
                    VGroup(M("maxByOrNull { it.grams }", 28, CARD), T("the heaviest, or null", 26, GREY_A)))
        for r in nf:
            r.arrange(RIGHT, buff=0.6)
        nf.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.9, 0])
        nl = T("folds, already written and named", 28, GREY_B).move_to([0, 2.8, 0])
        say1 = VGroup(M("sumOf { it.grams }", 24, CARD), T("says more than", 24, GREY_A),
                      M("fold(0) { acc, c -> acc + c.grams }", 24, GREY_A)).arrange(RIGHT, buff=0.25)
        fit(say1, 12.4).move_to([0, -1.4, 0])
        wh = T("fold: when the step needs a when, like the jar", 26, ACC).move_to([0, -2.4, 0])
        self.say("special")
        self.at(1)
        self.play(FadeIn(nl), LaggedStart(*[FadeIn(r[0]) for r in nf], lag_ratio=0.3), run_time=1.2)
        self.at(2)
        self.play(FadeIn(nf[0][1]), FadeIn(nf[1][1]), FadeIn(nf[2][1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(say1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(wh), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= reduce, steelmanned =================
        r1 = VGroup(M("weights.fold(0) { a, b -> a + b }", 28), M("295", 28, OUT)).arrange(RIGHT, buff=0.5)
        r2 = VGroup(M("weights.reduce { a, b -> a + b }", 28), M("295", 28, OUT)).arrange(RIGHT, buff=0.5)
        rr = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 1.2, 0])
        wl = T("weights = [45, 90, 50, 80, 30]", 24, GREY_B).move_to([0, 2.8, 0])
        nostart = T("no starting value: it starts from the first element", 26, CARD).move_to([0, -0.4, 0])
        self.say("reduce")
        self.play(FadeIn(wl), FadeIn(r1[0]), run_time=0.6)
        self.play(FadeIn(r2[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(nostart), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r1[1]), FadeIn(r2[1]), run_time=0.6)
        self.hold()
        self.wipe()

        el = M("val none = emptyList<Int>()", 26, GREY_B).move_to([0, 2.7, 0])
        tab = [("fold(0) { a, b -> a + b }", "0", OUT), ("sum()", "0", OUT),
               ("reduce { a, b -> a + b }", "throws UnsupportedOperationException:", HIDDEN),
               ("", "Empty collection can't be reduced.", HIDDEN),
               ("first()", "throws NoSuchElementException: List is empty.", HIDDEN)]
        lines = VGroup()
        for a, b, c in tab:
            lines.add(VGroup(M(a or ".", 24).set_opacity(1 if a else 0), M(b, 24, c)))
        Ys = [1.6, 0.95, 0.3, -0.25, -0.9]
        for (ln, y) in zip(lines, Ys):
            ln[0].move_to([-6.0, y, 0], aligned_edge=LEFT)
            ln[1].move_to([-1.3, y, 0], aligned_edge=LEFT)
        tg = VGroup(lines)
        fit(tg, 12.4).move_to([0, 0.35, 0])
        self.say("reduce_q")
        self.play(FadeIn(el), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lines[0][0]), FadeIn(lines[1][0]), FadeIn(lines[2][0]), run_time=0.8)
        self.hold(after=0)
        self.predict()
        self.say("reduce_a")
        self.play(FadeIn(lines[0][1]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(lines[1][1]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(lines[2][1]), FadeIn(lines[3][1]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(lines[4]), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(el, lines)), run_time=0.5)

        # ================= why: the jar =================
        jf2 = jar_on_scale("0 g", 0.9).move_to([-3.4, 0.1, 0])
        jl2 = VGroup(T("fold: a jar on the scale", 26, OUT), T("shows the starting value", 24, GREY_A)).arrange(DOWN, buff=0.1)
        jl2.next_to(jf2, DOWN, buff=0.3)
        sc = jar_on_scale("?", 0.9)
        empty_sc = VGroup(*sc[2:]).move_to([3.4, -0.4, 0])
        rl2 = VGroup(T("reduce: nothing to put on it", 26, HIDDEN), T("so it complains", 24, GREY_A)).arrange(DOWN, buff=0.1)
        rl2.next_to(empty_sc, DOWN, buff=0.3).align_to(jl2, UP)
        quiet = T("A quiet day isn't an emergency. reduce treats it like one.", 30, GOLD_M).move_to([0, 2.7, 0])
        fit(quiet, 12.4)
        self.say("why")
        self.play(FadeIn(jf2), FadeIn(jl2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(empty_sc), FadeIn(rl2), run_time=0.8)
        self.play(Wiggle(empty_sc, scale_value=1.08), run_time=0.8)
        self.at(3)
        self.play(FadeIn(quiet, shift=DOWN * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= OrNull, and Java's Optional =================
        prs = VGroup(VGroup(M("reduce { }", 26), T("throws", 26, HIDDEN), M("reduceOrNull { }", 26), T("null", 26, OUT)),
                     VGroup(M("first()", 26), T("throws", 26, HIDDEN), M("firstOrNull()", 26), T("null", 26, OUT)))
        for p in prs:
            p[0].move_to([-4.6, 0, 0], aligned_edge=LEFT)
            p[1].move_to([-1.4, 0, 0], aligned_edge=LEFT)
            p[2].move_to([0.6, 0, 0], aligned_edge=LEFT)
            p[3].move_to([4.4, 0, 0], aligned_edge=LEFT)
        prs[0].move_to([0, 2.0, 0])
        prs[1].move_to([0, 1.2, 0]).align_to(prs[0], LEFT)
        jo = VGroup(T("Java", 22, GREY_B), M("stream.reduce((a, b) -> a + b)", 26), T("returns Optional.empty", 26, CARD)).arrange(RIGHT, buff=0.3)
        fit(jo, 12.4).move_to([0, -0.6, 0])
        jo2 = T("Optional: a box that may be empty, so the type makes you handle it", 26, GREY_A).move_to([0, -1.5, 0])
        fit(jo2, 12.4)
        self.say("ornull")
        self.at(1)
        self.play(FadeIn(prs[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(prs[1]), run_time=0.6)
        self.at(4)
        self.play(FadeIn(jo), run_time=0.6)
        self.at_text("a box", lead=0.3)
        self.play(FadeIn(jo2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture stops =================
        kinds = VGroup(chip("a number: 315", ACC, 26), chip("a list", ACC, 26), chip("a map", ACC, 26), chip("a function", ACC, 26))
        kinds.arrange(RIGHT, buff=0.4).move_to([0, 1.7, 0])
        al = T("an accumulator can be anything", 28, GREY_B).move_to([0, 2.8, 0])
        prev = M("steps.fold({ x: Int -> x }) { acc, step -> acc andThen step }", 24, CARD)
        fit(prev, 12.2).move_to([0, 0.0, 0])
        pl = T("the last lesson: adjustments folded into one function", 24, GREY_A).next_to(prev, DOWN, buff=0.25)
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(al), LaggedStart(*[FadeIn(k) for k in kinds], lag_ratio=0.3), run_time=1.3)
        self.at(2)
        self.play(FadeIn(prev), FadeIn(pl), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the rule =================
        rule = T("An empty list is a normal day.", 34, ACC).move_to([0, 2.2, 0])
        use = VGroup(T("can be empty:", 26, GREY_B), M("fold", 26, OUT), M("sumOf", 26, OUT), M("...OrNull", 26, OUT)).arrange(RIGHT, buff=0.35)
        use.move_to([0, 1.0, 0])
        loud = VGroup(T("empty is a bug:", 26, GREY_B), M("reduce", 26, HIDDEN), M("first()", 26, HIDDEN), T("loudly", 26, HIDDEN)).arrange(RIGHT, buff=0.35)
        loud.move_to([0, 0.0, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(rule), run_time=0.6)
        self.at(2)
        self.play(FadeIn(use), run_time=0.6)
        self.at(3)
        self.play(FadeIn(loud), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Is the for loop with a var wrong? No: it's a fold, by hand.", 32).move_to(UP * 2.4)
        m1 = T("fold: the start and the step passed in, the var tucked inside.", 32, ACC).move_to(UP * 1.5)
        for m in (mq, m1):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = M("emptyList<Cookie>().fold(200) { jar, c -> ... }", 26)
        fit(qq, 12.2).move_to(DOWN * 0.4)
        qh = T("Check: no cookies at all. What does the scale show?", 28, PURE).next_to(qq, UP, buff=0.3)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("200 g: with nothing to add, fold hands back the starting value", 28, ACC).move_to(DOWN * 2.2)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
