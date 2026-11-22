from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"<out (\w+)>", r" of out \1"), (r"\? extends", "question mark extends"), (r"\bT : (\w+)", r"T colon \1"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)\?>", r"\1 of nullable \2"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)<([A-Za-z]+)>>", r"\1 of \2 of \3"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"\bAny\?", "Any nullable"), (r"\bT\?", "T nullable"),
    (r"\bMutableList\b", "mutable list"), (r"\bClassCastException\b", "class cast exception"),
    (r"\bArrayStoreException\b", "array store exception"), (r"\bkotlinc\b", "kotlin C"),
    (r"\bAnyBoxDemo\b", "any box demo"), (r"\bAnyBox\b", "any box"), (r"\bsignFor\b", "sign for"),
    (r"\bfirstOrNull\b", "first or null"), (r"\bmaxOf2\b", "max of two"), (r"\bhashCode\b", "hash code"),
    (r"\blengthOf\b", "length of"), (r"\bcompareTo\b", "compare to"), (r"\bInvarianceDemo\b", "invariance demo"),
    (r"\bProducerDemo\b", "producer demo"), (r"\bListDispenser\b", "list dispenser"), (r"\btotalGrams\b", "total grams"),
    (r"\bMaxDemo\b", "max demo"), (r"\bUnboundedDemo\b", "unbounded demo"),
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole generics track (the fruit shop storeroom)
BOX, BACK, COUNTER, CLERK, APPLE, LEMON, NUM, BAD, OK = GOLD_M, BLUE_M, TEAL_M, PURPLE_M, GREEN_M, YELLOW_M, BLUE_M, RED_M, GREEN_M
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"   # box labels: paper, printed ink, handwriting


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def crate(w=2.2, h=1.5, label=None, size=20, color=BOX):
    """A cardboard storeroom box: body [0], lid [1], tape [2], optional paper label [3]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.36).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.18)
    g = VGroup(body, lid, tape)
    if label:
        g.add(paper(label, size).move_to(body.get_center() + DOWN * 0.1))
    return g


def apple(r=0.2):
    a = Circle(radius=r).set_stroke(APPLE, 2.5).set_fill(dim(APPLE, 0.55), 1)
    stem = Line(a.get_top(), a.get_top() + UP * r * 0.45 + RIGHT * r * 0.12, stroke_width=3, color="#8B5A2B")
    leaf = Ellipse(width=r * 0.6, height=r * 0.3).set_stroke(APPLE, 1.5).set_fill(APPLE, 1)
    leaf.rotate(25 * DEGREES).move_to(a.get_top() + UP * r * 0.3 + RIGHT * r * 0.38)
    return VGroup(a, stem, leaf)


def lemon(r=0.2):
    l = Ellipse(width=r * 2.5, height=r * 1.8).set_stroke(LEMON, 2.5).set_fill(dim(LEMON, 0.55), 1)
    tip = Dot(radius=r * 0.12, color=LEMON).move_to(l.get_right())
    return VGroup(l, tip)


def vchip(text, color, size=26, h=0.56):
    """A value travelling into or out of a box: a small rounded chip with monospace text."""
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
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


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def err_line(text, size=22):
    """A compiler message: red 'error:' then the message in light grey."""
    return VGroup(M("error:", size, BAD), M(text, size, GREY_A)).arrange(RIGHT, buff=0.15)


def door(h=2.6, w=1.5, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def cross_by(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check_by(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


# every spoken line, in order
N = {
    "open": "The shop's apples arrive in a crate labeled apples. A helper needs a crate of fruit to carry to the front, "
            "and the apple crate seems fine: every apple is a fruit. But the helper was told the crate holds fruit, so "
            "they top it up with a lemon.",
    "open2": "The next customer who reaches in for an apple bites into a lemon. Hold on to that face. It's the whole lesson.",
    "shyq": "So here's a question that's easy to be shy about. An apple is a fruit. So why isn't a list of apples a list "
            "of fruit? Kotlin won't pass a MutableList<Apple> as a MutableList<Fruit>. Isn't the compiler just being "
            "fussy?",
    "test": "To answer that, we need the test the compiler runs on every assignment. A type A is a subtype of B when an "
            "A can be used anywhere a B is expected, and nothing can go wrong. So ask: if I secretly hand over an A "
            "where a B is expected, can any allowed move go wrong?",
    "test2": "Try it on one apple. What can you do with a Fruit? Read its name. An apple has a name, so nothing goes "
             "wrong. Apple is a subtype of Fruit.",
    "crate_q": "Now run the same test on the crates. Someone expects a MutableList<Fruit>, and we secretly hand over a "
               "MutableList<Apple>. What moves are allowed on a list of fruit? Read an item: fine, every apple is a "
               "fruit. And add an item: any fruit at all. Can anything go wrong? Pause and guess.",
    "crate": "It can. Here it is in code, in both languages. Suppose the second line compiled. Then anyFruit and apples "
             "are two names for one list object.",
    "crate2": "One crate, with two labels. Through the fruit label, adding a lemon is perfectly legal. Through the apples "
              "label, someone reads the second item as an apple. And that's the lemon.",
    "refuse": "So both compilers refuse the hand over itself. kotlinc says: initializer type mismatch, expected "
              "MutableList<Fruit>, actual MutableList<Apple>. javac says: List<Apple> cannot be converted to List<Fruit>.",
    "fussy": "So the compiler isn't fussy. It's just the only one in the shop who thought about the lemon.",
    "force": "Let's break it on purpose, to see what the rule saves us from. An unchecked cast forces the hand over, and "
             "the compiler only warns. Think of the warning as a shrug: fine, it's your lemon.",
    "force2": "The lesson's InvarianceDemo does exactly that, then adds a lemon. It prints: the apple crate holds 2 items, "
              "and nothing failed yet. Then a ClassCastException: Lemon cannot be cast to Apple.",
    "force3": "Notice where it failed. The lemon went in without a sound. The failure came later, on a read, on a line "
              "with no cast in it. It's the 12 in the box from lesson 1, with the compiler switched off on purpose.",
    "breaks": "The crate picture breaks in one place, and it's the important one. A real crate holds its apples in plain "
              "sight, and you'd spot the lemon when you opened it. At run time, the JVM spots nothing. The list doesn't "
              "know it was meant for apples, so nothing checks the lemon until someone reads it as an apple.",
    "title": "The lesson's title is the same story, with the widest types there are. Swap Apple for String, and Fruit "
             "for Object. Now the lemon is the number 42, dropped into a list of strings. That's why Java won't let a "
             "List<String> pass as a List<Object>.",
    "name": "Now the name. This rule is called invariance. MutableList<A> is a subtype of MutableList<B> only when A and "
            "B are the same type. The arrow from Apple to Fruit is real, but it doesn't carry over to the lists. Every "
            "Java generic type works the same way.",
    "guard": "In practice, invariance annoys people. You have a MutableList<Apple>, a function takes a MutableList<Fruit>, "
             "and the call won't compile. The fix is never the cast. Ask what the function does with the list.",
    "guard2": "If it only reads, it should take a read-only List<Fruit>: a display case, with no way to put anything in. "
              "The end of this lesson shows why that one is allowed. And if it adds, the compiler just caught a bug: "
              "that function could have dropped a lemon into your apples.",
    "moral": "So, why isn't a crate of apples a crate of fruit? Because a crate of fruit lets you add any fruit. A list "
             "you can write to must match its element type exactly. Don't cast your way past it.",
    "check": "Quick check. crate is a MutableList<Apple>. Which of these two lines compiles?",
    "check_a": "Only b. A read-only List has no add, so reading apples as fruit can never lie. Kotlin declares it "
               "List<out E>, and the next lesson is about writing that out yourself.",
}


def crate_with(items, label, w=2.6, h=1.6, size=22):
    """A crate with fruit sitting in its open top, and a paper label on its front."""
    c = crate(w, h, [label], size)
    row = VGroup(*items).arrange(RIGHT, buff=0.08)
    row.move_to(c[0].get_top() + UP * 0.12)
    return c, row


def sour(p):
    """Little squiggle lines next to a person's head: a sour face."""
    h = p[1]
    ls = VGroup(*[Line(ORIGIN, RIGHT * 0.22, stroke_width=3, color=LEMON).rotate(a * DEGREES) for a in (25, 0, -25)])
    ls.arrange(DOWN, buff=0.06).next_to(h, RIGHT, buff=0.1)
    return ls


class Gen03Invariance(Narrated):
    """gen-03, section 1: the apple crate topped up with a lemon; the shy question; the substitution test, on one apple
    and on the crates (read is fine, add takes any fruit); the code with two names for one list; both compilers refuse;
    the unchecked cast and InvarianceDemo's real output (late failure on a read); where the crate picture breaks; the
    title's String/Object version; the name, invariance, with the arrow that doesn't carry over; the guardrail (reads
    only: List<Fruit>; adds: a caught bug); moral; a check."""

    def construct(self):
        self.title_card("A crate of apples is not a crate of fruit", "the substitution test, and invariance")

        # ================= the crate and the lemon =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        c, row = crate_with([apple(0.2) for _ in range(4)], "apples")
        c.move_to([0, FL + 0.8, 0])
        row.move_to(c[0].get_top() + UP * 0.12)
        helper = who(BACK, "helper").move_to([-3.2, FL + 0.75, 0])
        told = paper(["bring a crate", "of fruit"], 20).next_to(helper, UP, buff=0.3)
        ok_ = VGroup(tick(True, 0.15), T("every apple is a fruit", 22, OK)).arrange(RIGHT, buff=0.15).move_to([0, 2.3, 0])
        lm = lemon(0.2).move_to([-3.2, 1.0, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(c), FadeIn(row, shift=DOWN * 0.2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(helper), FadeIn(told, shift=UP * 0.1), run_time=0.7)
        self.at_text("seems fine", lead=0.3)
        self.play(FadeIn(ok_), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lm), run_time=0.3)
        self.play(lm.animate.move_to(row.get_right() + RIGHT * 0.28), run_time=0.9)
        self.hold()

        cust = who(COUNTER, "customer").move_to([3.4, FL + 0.75, 0])
        self.say("open2")
        self.play(FadeIn(cust), FadeOut(ok_), FadeOut(told), run_time=0.6)
        self.play(lm.animate.move_to(cust[0][1].get_center() + LEFT * 0.3 + UP * 0.05), run_time=0.9)
        sq = sour(cust[0])
        self.play(FadeIn(sq), Wiggle(cust[0]), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("An apple is a fruit. So why isn't a list of apples a list of fruit?", 32)
        q2 = VGroup(M("MutableList<Apple>", 30, APPLE), T("as a", 30, GREY_A), M("MutableList<Fruit>", 30, WHITE), tick(False, 0.2)).arrange(RIGHT, buff=0.25)
        q3 = T("Isn't the compiler just being fussy?", 32, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= the substitution test =================
        d1 = VGroup(T("A is a subtype of B when an A can be used", 30), T("anywhere a B is expected, and nothing can go wrong.", 30)).arrange(DOWN, buff=0.12)
        d1.move_to([0, 2.3, 0])
        tb = VGroup(T("the substitution test", 24, YELLOW_M),
                    T("Secretly hand over an A where a B is expected.", 28),
                    T("Can any allowed move go wrong?", 28)).arrange(DOWN, buff=0.15)
        tbr = SurroundingRectangle(tb, buff=0.3, color=YELLOW_M, stroke_width=2, corner_radius=0.12)
        tg = VGroup(tbr, tb).move_to([0, 0.1, 0])
        fit(d1, 12.4)
        self.say("test")
        self.at(1)
        self.play(FadeIn(d1, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Create(tbr), FadeIn(tb), run_time=0.9)
        self.hold()

        fb = mbox("Fruit", GREY_A, size=28).move_to([-3.2, -1.9, 0])
        ap = apple(0.3).move_to([-5.0, -2.25, 0])
        moves = VGroup(T("allowed on a Fruit:", 24, GREY_B), M(".name", 26, WHITE), tick(True, 0.17)).arrange(RIGHT, buff=0.25)
        moves.move_to([1.2, -1.9, 0])
        verdict = VGroup(M("Apple", 28, APPLE), T("is a subtype of", 26, GREY_A), M("Fruit", 28, WHITE)).arrange(RIGHT, buff=0.2).move_to([1.2, -2.9, 0])
        self.say("test2")
        self.play(FadeIn(ap), FadeIn(fb), run_time=0.6)
        self.play(ap.animate.move_to(fb.get_left() + LEFT * 0.4), run_time=0.6)
        self.at(1)
        self.play(FadeIn(moves[:2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(moves[2]), run_time=0.3)
        self.at(3)
        self.play(FadeIn(verdict, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the test on the crates =================
        FL = -1.4
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        c, row = crate_with([apple(0.2) for _ in range(4)], "MutableList<Apple>", w=3.2, size=20)
        c.move_to([-3.6, FL + 0.8, 0])
        row.move_to(c[0].get_top() + UP * 0.12)
        expects = paper(["expects:", "MutableList<Fruit>"], 20).move_to([3.4, 2.4, 0])
        hand = who(BACK, "someone", 1.1, 22).move_to([3.4, FL + 0.75, 0])
        mv = VGroup(T("allowed on a list of fruit:", 24, GREY_B),
                    VGroup(T("read an item", 26), tick(True, 0.15)).arrange(RIGHT, buff=0.2),
                    VGroup(T("add any fruit", 26), M("?", 30, YELLOW_M)).arrange(RIGHT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        mv.move_to([3.4, 0.4, 0])
        self.say("crate_q")
        self.play(Create(floor), FadeIn(c), FadeIn(row), run_time=0.7)
        self.at(1)
        self.play(FadeIn(hand), FadeIn(expects, shift=DOWN * 0.1), run_time=0.6)
        self.play(VGroup(c, row).animate.shift(RIGHT * 2.2), run_time=0.9)
        self.at(2)
        self.play(FadeIn(mv[0]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(mv[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(mv[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, 3.2), edge=LEFT)
        self.wipe()

        # ================= the code: two names for one list =================
        jc = code_block(['List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala")));',
                         "List<Fruit> anyFruit = apples;           // suppose this compiled",
                         'anyFruit.add(new Lemon("Eureka"));       // legal on a List<Fruit>',
                         "Apple second = apples.get(1);            // ClassCastException"], 22,
                        hl={"// suppose this compiled": GREY_B, "// legal on a List<Fruit>": GREY_B, "// ClassCastException": BAD})
        kc = code_block(['val apples: MutableList<Apple> = mutableListOf(Apple("Gala"))',
                         "val anyFruit: MutableList<Fruit> = apples   // suppose this compiled",
                         'anyFruit.add(Lemon("Eureka"))                // legal on a MutableList<Fruit>',
                         "val second: Apple = apples[1]                // ClassCastException"], 22,
                        hl={"// suppose this compiled": GREY_B, "// legal on a MutableList<Fruit>": GREY_B, "// ClassCastException": BAD})
        fit(jc, 12.4)
        fit(kc, 12.4)
        jg = titled(jc, "Java")
        kg = titled(kc, "Kotlin")
        cg = VGroup(jg, kg).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, 0.9, 0])
        self.say("crate")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.9)
        self.at(2)
        self.play(Indicate(jc[1], color=WHITE, scale_factor=1.03), Indicate(kc[1], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(part(jc[1], "anyFruit").animate.set_color(YELLOW_M), part(kc[1], "anyFruit").animate.set_color(YELLOW_M),
                  part(jc[0], "apples").animate.set_color(APPLE), part(kc[0], "apples").animate.set_color(APPLE), run_time=0.6)
        self.hold()

        # one crate, two labels
        self.play(cg.animate.scale(0.75).move_to([0, 2.35, 0]), run_time=0.7)
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        c2 = crate(3.4, 1.7, None).move_to([0, FL + 0.85, 0])
        l_ap = paper(["apples"], 22).move_to(c2[0].get_center() + LEFT * 0.75 + DOWN * 0.1)
        l_fr = paper(["anyFruit"], 22).move_to(c2[0].get_center() + RIGHT * 0.75 + DOWN * 0.1)
        l_fr[0].set_stroke(YELLOW_M, 2)
        l_ap[0].set_stroke(APPLE, 2)
        g1 = apple(0.22).move_to(c2[0].get_top() + UP * 0.14 + LEFT * 0.4)
        one = T("one list object", 22, GREY_A).next_to(c2, RIGHT, buff=0.4)
        self.say("crate2")
        self.play(Create(floor), FadeIn(c2), FadeIn(g1), FadeIn(l_ap), run_time=0.6)
        self.play(FadeIn(l_fr, shift=DOWN * 0.1), FadeIn(one), run_time=0.5)
        self.at(1)
        lm = lemon(0.2).move_to([5.5, 0.0, 0])
        self.play(Indicate(l_fr, color=YELLOW_M, scale_factor=1.15), Indicate(VGroup(jc[2], kc[2]), color=WHITE, scale_factor=1.02), run_time=0.7)
        self.play(FadeIn(lm), run_time=0.2)
        self.play(lm.animate.move_to(c2[0].get_top() + UP * 0.14 + RIGHT * 0.35), run_time=0.8)
        self.at(2)
        reader = who(COUNTER, "reads item 1 as Apple", 1.0, 20).move_to([-4.6, FL + 0.7, 0])
        self.play(FadeIn(reader), Indicate(l_ap, color=APPLE, scale_factor=1.15), Indicate(VGroup(jc[3], kc[3]), color=WHITE, scale_factor=1.02), run_time=0.8)
        self.at(3)
        self.play(lm.animate.move_to(reader[0][1].get_center() + RIGHT * 0.35 + UP * 0.05), run_time=0.8)
        self.play(FadeIn(sour(reader[0])), Flash(reader[0][1], color=BAD, line_length=0.25), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= both compilers refuse =================
        kl = M("val anyFruit: MutableList<Fruit> = apples", 28, WHITE).move_to([0, 2.3, 0])
        und = Underline(kl, color=BAD, stroke_width=4, buff=0.08)
        e1 = VGroup(T("kotlinc", 22, GREY_B), err_line("initializer type mismatch: expected 'MutableList<Fruit>',", 22)).arrange(RIGHT, buff=0.25)
        e1b = M("actual 'MutableList<Apple>'.", 22, GREY_A)
        e2 = VGroup(T("javac", 22, GREY_B), err_line("incompatible types: List<Apple> cannot be converted to List<Fruit>", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(e1, e1b, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        e1b.align_to(e1[1][1], LEFT)
        fit(eg, 12.4).move_to([0, 0.6, 0])
        self.say("refuse")
        self.play(FadeIn(kl), run_time=0.5)
        self.play(Create(und), run_time=0.5)
        self.at(1)
        self.play(FadeIn(e1, shift=UP * 0.1), FadeIn(e1b, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(e2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        clerk = person(CLERK, 1.2).move_to([-2.6, -2.2, 0])
        thought = VGroup(lemon(0.2), T("?", 30, YELLOW_M)).arrange(RIGHT, buff=0.1).next_to(clerk, UR, buff=0.1)
        fz = T("not fussy: the only one who thought about the lemon", 26, GREY_A).next_to(clerk, RIGHT, buff=1.2)
        fit(fz, 8.0)
        self.say("fussy")
        self.play(FadeIn(clerk), FadeIn(thought, scale=0.7), run_time=0.6)
        self.at_text("It's just", lead=0.2)
        self.play(FadeIn(fz, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= break it on purpose: the unchecked cast =================
        fc = code_block(['val apples: MutableList<Apple> = mutableListOf(Apple("Gala"))',
                         "@Suppress(\"UNCHECKED_CAST\")",
                         "val anyFruit = apples as MutableList<Fruit>",
                         'anyFruit.add(Lemon("Eureka"))',
                         "val second: Apple = apples[1]"], 22, hl={"@Suppress(\"UNCHECKED_CAST\")": GREY_B})
        fit(fc, 12.4)
        fg_ = titled(fc, "Kotlin, from InvarianceDemo").move_to([0, 1.9, 0])
        wn = VGroup(M("warning:", 22, YELLOW_M), M("unchecked cast of 'MutableList<Apple>' to 'MutableList<Fruit>'", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        fit(wn, 12.4).move_to([0, -0.15, 0])
        shrug = VGroup(person(CLERK, 1.0), T("fine, it's your lemon", 24, YELLOW_M)).arrange(RIGHT, buff=0.3).move_to([0, -1.2, 0])
        self.say("force")
        self.play(FadeIn(fg_, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(part(fc[2], "as MutableList<Fruit>").animate.set_color(YELLOW_M), run_time=0.5)
        self.play(FadeIn(wn, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(shrug, shift=UP * 0.1), run_time=0.6)
        self.hold()

        out = term(["the apple crate holds 2 items, and nothing failed yet",
                    "ClassCastException: class workbench.generics.l03.demo.Lemon",
                    "    cannot be cast to class workbench.generics.l03.demo.Apple (...)"], 22, "InvarianceDemo, real output")
        fit(out, 12.4).move_to([0, -2.35, 0])
        self.say("force2")
        self.play(FadeOut(shrug), FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[1][0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out[1][1:], shift=RIGHT * 0.1), part(out[1][1], "ClassCastException").animate.set_color(BAD), run_time=0.7)
        self.hold()

        quiet = VGroup(T("went in without a sound", 22, GREY_A)).next_to(fc[3], RIGHT, buff=0.5)
        loud = VGroup(T("fails here, on a read, with no cast", 22, BAD)).next_to(fc[4], RIGHT, buff=0.5)
        self.say("force3")
        self.play(FadeOut(wn), run_time=0.3)
        self.at(1)
        self.play(FadeIn(quiet, shift=LEFT * 0.1), Indicate(fc[3], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at(2)
        self.play(FadeIn(loud, shift=LEFT * 0.1), Indicate(fc[4], color=BAD, scale_factor=1.03), run_time=0.7)
        self.at(3)
        cb = VGroup(mbox("Box", BOX, size=22), T("the 12 in the box, lesson 1", 22, GREY_B)).arrange(RIGHT, buff=0.2)
        cb.move_to([4.0, -0.15, 0])
        self.play(FadeIn(cb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the crate picture breaks =================
        FL = -1.2
        floor = Line([-6.5, FL, 0], [-0.8, FL, 0], stroke_width=1.5, color=GREY_D)
        c3 = crate(2.8, 1.5, ["apples"], 22).move_to([-3.6, FL + 0.75, 0])
        fruit = VGroup(apple(0.22), apple(0.22), lemon(0.2)).arrange(RIGHT, buff=0.1).move_to(c3[0].get_top() + UP * 0.15)
        eye = VGroup(Ellipse(width=0.6, height=0.32).set_stroke(WHITE, 2.5), Dot(radius=0.08, color=WHITE)).move_to([-3.6, 2.2, 0])
        spot = T("in plain sight: you'd spot the lemon", 24, GREY_A).move_to([-3.6, -2.2, 0])
        jl = VGroup(RoundedRectangle(corner_radius=0.1, width=4.6, height=1.3).set_stroke(GREY_A, 2.5).set_fill("#111111", 1))
        jlt = VGroup(M("java.util.ArrayList", 22, GREY_A), M("[ Apple(Gala), Lemon(Eureka) ]", 22, WHITE)).arrange(DOWN, buff=0.15)
        jl.add(jlt.move_to(jl[0]))
        jl.move_to([3.4, 0.0, 0])
        jlh = T("at run time", 24, GREY_B).next_to(jl, UP, buff=0.25)
        nolab = T("no label: nothing checks the lemon", 24, BAD).next_to(jl, DOWN, buff=0.3)
        self.say("breaks")
        self.play(Create(floor), FadeIn(c3), FadeIn(fruit), run_time=0.7)
        self.at(1)
        self.play(FadeIn(eye), FadeIn(spot), Indicate(fruit[2], color=LEMON, scale_factor=1.4), run_time=0.8)
        self.at(2)
        self.play(FadeIn(jlh), FadeIn(jl), run_time=0.7)
        self.at(3)
        self.play(FadeIn(nolab, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the title: String and Object =================
        a = VGroup(M("Apple", 34, APPLE), M("->", 30, GREY_B), M("String", 34, WHITE)).arrange(RIGHT, buff=0.3)
        b = VGroup(M("Fruit", 34, GREY_A), M("->", 30, GREY_B), M("Object", 34, WHITE)).arrange(RIGHT, buff=0.3)
        ab = VGroup(a, b).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, 1.9, 0])
        lst = VGroup(M('[ "Gala", "Fuji",', 30, WHITE), M("42", 30, NUM), M("]", 30, WHITE)).arrange(RIGHT, buff=0.2).move_to([0, -0.2, 0])
        lstl = T("a list of strings, through a List<Object> view", 24, GREY_B).next_to(lst, DOWN, buff=0.25)
        why = VGroup(M("List<String>", 30, WHITE), T("is not a", 28, GREY_A), M("List<Object>", 30, WHITE)).arrange(RIGHT, buff=0.25).move_to([0, -2.4, 0])
        self.say("title")
        self.at(1)
        self.play(FadeIn(a, shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(b, shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lst), FadeIn(lstl), run_time=0.7)
        self.play(Indicate(lst[1], color=NUM, scale_factor=1.4), run_time=0.7)
        self.at(3)
        self.play(FadeIn(why, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the name: invariance =================
        nm = T("invariance", 44, YELLOW_M).move_to([0, 2.8, 0])
        fr = mbox("Fruit", GREY_A, size=28).move_to([-3.6, 1.2, 0])
        apb = mbox("Apple", APPLE, size=28).move_to([-3.6, -1.4, 0])
        a1 = Arrow(apb.get_top(), fr.get_bottom(), buff=0.12, stroke_width=4, color=OK, max_tip_length_to_length_ratio=0.12)
        a1l = T("is a subtype of", 22, OK).next_to(a1, LEFT, buff=0.15)
        mf = mbox("MutableList<Fruit>", GREY_A, size=26).move_to([2.8, 1.2, 0])
        ma = mbox("MutableList<Apple>", APPLE, size=26).move_to([2.8, -1.4, 0])
        brk = DashedLine(ma.get_top(), mf.get_bottom(), dash_length=0.12, stroke_width=3, color=BAD)
        nob = VGroup(tick(False, 0.18), T("no arrow", 24, BAD)).arrange(RIGHT, buff=0.15).next_to(brk, RIGHT, buff=0.25)
        rule = T("MutableList<A> is a subtype of MutableList<B> only when A and B are the same type", 24, WHITE).move_to([0, -2.7, 0])
        fit(rule, 12.4)
        self.say("name")
        self.play(FadeIn(nm), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fr), FadeIn(apb), GrowArrow(a1), FadeIn(a1l), run_time=0.8)
        self.play(FadeIn(mf), FadeIn(ma), run_time=0.5)
        self.play(Create(brk), FadeIn(nob), run_time=0.7)
        self.at(3)
        jv = T("every Java generic type: the same", 22, GREY_B).next_to(mf, UP, buff=0.3)
        self.play(FadeIn(jv), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the guardrail =================
        prob = VGroup(T("a function takes", 26, GREY_A), M("MutableList<Fruit>", 26, WHITE), T("; you pass", 26, GREY_A),
                      M("MutableList<Apple>", 26, APPLE), tick(False, 0.18)).arrange(RIGHT, buff=0.2)
        fit(prob, 12.4).move_to([0, 2.6, 0])
        never = VGroup(T("the fix is never the cast", 28, BAD)).move_to([0, 1.6, 0])
        ask = T("Ask: what does the function do with the list?", 30, YELLOW_M).move_to([0, 0.7, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(prob, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(never), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.5)
        self.hold()

        r1 = VGroup(T("only reads", 28, OK), M("->", 26, GREY_B), M("take a read-only List<Fruit>", 26, WHITE)).arrange(RIGHT, buff=0.3)
        r1n = T("a display case: nothing can go in (end of this lesson)", 22, GREY_B)
        r2 = VGroup(T("adds", 28, BAD), M("->", 26, GREY_B), T("the compiler just caught a bug", 28, WHITE)).arrange(RIGHT, buff=0.3)
        r2n = T("it could have dropped a lemon into your apples", 22, GREY_B)
        rg = VGroup(r1, r1n, r2, r2n).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0, -1.5, 0])
        r1n.shift(RIGHT * 0.3)
        r2n.shift(RIGHT * 0.3)
        r2.shift(DOWN * 0.15)
        r2n.shift(DOWN * 0.15)
        fit(rg, 12.4)
        self.say("guard2")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(r1n), run_time=0.4)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(r2n), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why isn't a crate of apples a crate of fruit?", 34)
        m1 = T("Because a crate of fruit lets you add any fruit.", 30, GREY_A)
        m2 = T("A list you can write to must match its element type exactly.", 30, YELLOW_M)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.1)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qh = VGroup(T("Check:", 28, YELLOW_M), M("val crate: MutableList<Apple> = ...", 26, WHITE)).arrange(RIGHT, buff=0.25)
        qa = M("a)  val a: MutableList<Fruit> = crate", 26, WHITE)
        qb = M("b)  val b: List<Fruit> = crate", 26, WHITE)
        qg = VGroup(qh, qa, qb).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(DOWN * 0.7)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        xa = cross_by(qa, 0.18)
        cb_ = check_by(qb, 0.18)
        al = T("a read-only List has no add, so it can never lie", 24, OK).move_to(DOWN * 2.75)
        self.say("check_a")
        self.play(FadeIn(xa), FadeIn(cb_), run_time=0.5)
        self.at(1)
        self.play(FadeIn(al, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
