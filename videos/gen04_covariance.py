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
    "open": "By the shop door stands an apple dispenser. Pull the lever, and an apple drops out. A customer who wants some "
            "fruit can use it happily, because every apple that drops out is a fruit. There's no slot to put anything "
            "in, and that's the whole point.",
    "recall": "Last lesson, a crate of apples couldn't pass as a crate of fruit, because a crate of fruit takes any fruit, "
              "so a lemon could go in. The dispenser has no way in at all.",
    "shyq": "So here's a question that's easy to be shy about. My dispenser has no slot. Why does the compiler still say a "
            "dispenser of apples is not a dispenser of fruit? Can't it see there's no slot?",
    "code": "Here's the dispenser in Kotlin. next hands out the next item, or null when it's empty. totalGrams wants a "
            "Dispenser<Fruit>, and adds up the weights. Our dispenser holds two apples: Gala at 180 grams, and Fuji at "
            "150.",
    "fail": "Hand it the apples, and Kotlin says: argument type mismatch. Actual type is Dispenser<Apple>, but "
            "Dispenser<Fruit> was expected. The compiler can't see the missing slot by itself. Generic types are "
            "invariant unless you say otherwise.",
    "test_q": "So let's run the substitution test from last lesson. Some code expects a dispenser of fruit, and we "
              "secretly hand it a dispenser of apples. What can that code do with it? Can anything go wrong? Pause and "
              "guess.",
    "test": "All it can do is pull the lever. Every call to next returns an apple, and every apple is a fruit. No move "
            "takes a fruit in, so there's nowhere for a lemon to go. Nothing can go wrong.",
    "fix": "So we tell the compiler, once, on the declaration, with one small word: out. Dispenser<out T>. It's a "
           "promise: values of T only come out of this type.",
    "predict": "Same call as before. Nothing else changed. What does it print? Pause and guess.",
    "show": "It compiles, and the lesson's ProducerDemo prints: apple total, 330 grams. That's 180 plus 150, read "
            "through a dispenser of fruit.",
    "map": "Let's map it. The lever is a return type: a T flows out to the caller. A slot would be a parameter: a T "
           "flowing in. And out is a sticker on the machine that says: lever only, no slot.",
    "slot_q": "I know what you're thinking. What stops someone from adding a slot later? Say, a refill function that "
              "takes a T.",
    "slot": "Follow it through. A Dispenser<Apple> passes as a Dispenser<Fruit>. Through that view, refill with a lemon "
            "type checks, because a lemon is a fruit. Now the apple dispenser holds a lemon, and the next pull hands it "
            "to code that expects an apple.",
    "slot2": "An apple dispenser with a slot for any fruit isn't an apple dispenser any more. It's a surprise machine. So "
             "the compiler checks every member that outside code can call, and refuses the slot: T is declared out, but "
             "occurs in an in position.",
    "name": "Now the name. This is covariance. Co means together: the subtype arrow between the element types carries "
            "over to the dispensers, in the same direction. Apple is a subtype of Fruit, so Dispenser<Apple> is a "
            "subtype of Dispenser<Fruit>. And a type that only hands values out is called a producer.",
    "java": "Java has no out on a declaration. Its Dispenser stays invariant, so every method that wants the flexible "
            "behavior says so where it's used, with a wildcard: ? extends Fruit, meaning some subtype of Fruit. Forget "
            "it, and javac says: Dispenser<Apple> cannot be converted to Dispenser<Fruit>.",
    "java2": "That's the difference between the two styles. Kotlin puts the sticker on the machine, once. Java hands "
             "every customer a note to carry in their pocket, and anyone who forgets it is turned away. The names are "
             "declaration-site variance, and use-site variance.",
    "guard": "And the guardrail. You can only make the out promise if it's true: T may appear only where values come "
             "out, like return types. And out doesn't mean read-only, or unchanging. Every pull still takes an apple "
             "out of the machine. The end of this lesson shows that.",
    "moral": "So, why couldn't the compiler see there's no slot? Because it trusts what you declare, not what you meant. "
             "Say out, and an apple dispenser is a fruit dispenser, because only apples come out.",
    "check": "Quick check. Inside Dispenser<out T>, which of these two lines compiles?",
    "check_a": "Only val latest. A val only has a getter, so T only comes out. A var also has a setter, a slot, so T "
               "would go in too: the compiler says it occurs in an invariant position.",
}


def dispenser(label="apples", s=1.0, color=BOX):
    """A tall vending box: body [0], window [1], fruit in the window [2], lever [3], chute [4], paper label [5]."""
    body = RoundedRectangle(corner_radius=0.16, width=2.0, height=3.0).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.5, height=1.5).set_stroke(GREY_B, 2).set_fill("#0c0c0c", 1)
    win.move_to(body.get_top() + DOWN * 1.0)
    fr = VGroup(*[apple(0.16) for _ in range(6)]).arrange_in_grid(rows=2, cols=3, buff=0.12).move_to(win)
    lever_bar = Line(body.get_right() + UP * 0.1, body.get_right() + RIGHT * 0.45 + UP * 0.55, stroke_width=6, color=GREY_A)
    knob = Circle(radius=0.12).set_stroke(GREY_A, 2).set_fill(RED_E, 1).move_to(lever_bar.get_end())
    lever = VGroup(lever_bar, knob)
    chute = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.5).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
    chute.move_to(body.get_bottom() + UP * 0.45)
    lab = paper([label], 20).move_to(body.get_center() + DOWN * 0.45)
    return VGroup(body, win, fr, lever, chute, lab).scale(s)


class Gen04Covariance(Narrated):
    """gen-04, section 0: the apple dispenser by the door (a lever, no slot); the callback to the lemon in the crate;
    the shy question (why can't the compiler see there's no slot?); Dispenser<T> and totalGrams fail without out; the
    substitution test on the dispenser; out on the declaration; ProducerDemo's real output (330 g); the map (lever =
    return type, slot = parameter, out = the sticker); a refill slot would make a surprise machine, so the compiler
    refuses it; the name, covariance and producer; Java's ? extends at every use; the guardrail; moral; a check."""

    def construct(self):
        self.title_card("Covariance with out", "a dispenser only hands things out")

        # ================= the dispenser by the door =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("apples").move_to([-1.2, FL + 1.5, 0])
        cust = who(COUNTER, "customer", 1.1, 22).move_to([3.2, FL + 0.75, 0])
        want = paper(["some fruit,", "please"], 20).next_to(cust, UP, buff=0.3)
        self.say("open")
        self.play(Create(floor), FadeIn(dp), run_time=0.8)
        self.at(1)
        self.play(Rotate(dp[3], angle=-0.6, about_point=dp[3][0].get_start()), run_time=0.4)
        drop = apple(0.18).move_to(dp[4])
        self.play(FadeIn(drop, shift=DOWN * 0.2), Rotate(dp[3], angle=0.6, about_point=dp[3][0].get_start()), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cust), FadeIn(want, shift=UP * 0.1), run_time=0.6)
        self.play(drop.animate.move_to(cust[0][0].get_left() + LEFT * 0.25), run_time=0.8)
        ok1 = VGroup(tick(True, 0.15), T("every apple is a fruit", 22, OK)).arrange(RIGHT, buff=0.15).next_to(want, UP, buff=0.2)
        self.play(FadeIn(ok1), run_time=0.4)
        self.at(3)
        noslot = VGroup(DashedVMobject(Rectangle(width=1.0, height=0.25), num_dashes=14).set_stroke(GREY_B, 2),
                        tick(False, 0.14)).arrange(RIGHT, buff=0.15).next_to(dp, UP, buff=0.2)
        nsl = T("no slot", 22, GREY_B).next_to(noslot, LEFT, buff=0.2)
        self.play(FadeIn(noslot), FadeIn(nsl), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= callback: the lemon in the crate =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        c = crate(2.6, 1.5, ["apples"], 22).move_to([-3.4, FL + 0.75, 0])
        row = VGroup(apple(0.2), apple(0.2), apple(0.2), lemon(0.19)).arrange(RIGHT, buff=0.08).move_to(c[0].get_top() + UP * 0.12)
        cl = T("last lesson: a lemon could go in", 22, BAD).next_to(c, DOWN, buff=0.3)
        dp = dispenser("apples", 0.75).move_to([3.2, FL + 1.15, 0])
        dl = T("no way in at all", 22, OK).next_to(dp, DOWN, buff=0.15)
        self.say("recall")
        self.play(Create(floor), FadeIn(c), FadeIn(row[:3]), run_time=0.7)
        self.at_text("so a lemon", lead=0.3)
        self.play(FadeIn(row[3], shift=DOWN * 0.3), FadeIn(cl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(dp), FadeIn(dl), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("My dispenser has no slot.", 34, GREY_A)
        q2 = T("Why is a dispenser of apples still not a dispenser of fruit?", 32)
        q3 = T("Can't the compiler see there's no slot?", 34, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.38).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= the code, without out =================
        src = ["interface Dispenser<T> {",
               "    fun next(): T?              // null when it is empty",
               "}", "",
               "fun totalGrams(dispenser: Dispenser<Fruit>): Int { ... }", "",
               'val apples: Dispenser<Apple> =',
               '    ListDispenser(listOf(Apple("Gala", 180), Apple("Fuji", 150)))',
               "totalGrams(apples)"]
        kc = code_block(src, 24, hl={"// null when it is empty": GREY_B})
        fit(kc, 12.4)
        kg = titled(kc, "Kotlin").move_to([0, 1.2, 0])
        self.say("code")
        self.play(FadeIn(kg[0]), FadeIn(kc[:3], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(kc[1], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(kc[4], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(kc[6:8], shift=UP * 0.1), run_time=0.7)
        self.hold()

        er = VGroup(err_line("argument type mismatch: actual type is 'Dispenser<Apple>',", 22),
                    M("but 'Dispenser<Fruit>' was expected.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        er[1].align_to(er[0][1], LEFT)
        fit(er, 12.4).move_to([0, -2.4, 0])
        inv = T("generic types are invariant unless you say otherwise", 24, YELLOW_M).move_to([0, -3.25, 0])
        self.say("fail")
        self.play(FadeIn(kc[8], shift=UP * 0.1), run_time=0.5)
        self.play(Create(Underline(kc[8], color=BAD, stroke_width=4, buff=0.06)), FadeIn(er, shift=UP * 0.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(inv), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the substitution test on the dispenser =================
        FL = -2.0
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("Dispenser<Apple>").move_to([-3.0, FL + 1.5, 0])
        dp[5].scale(0.9)
        code_p = who(BACK, "code that expects", 1.1, 20).move_to([3.0, FL + 0.75, 0])
        ex = M("Dispenser<Fruit>", 22, WHITE).next_to(code_p, DOWN, buff=0.06)
        moves = VGroup(T("what it can do:", 24, GREY_B), M("next()", 26, WHITE), T("that's all", 22, GREY_B)).arrange(DOWN, buff=0.15)
        moves.move_to([3.0, 1.6, 0])
        self.say("test_q")
        self.play(Create(floor), FadeIn(dp), run_time=0.7)
        self.at(1)
        self.play(FadeIn(code_p), FadeIn(ex), run_time=0.6)
        self.at(2)
        self.play(FadeIn(moves[0]), run_time=0.4)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, 3.2), edge=LEFT)

        self.say("test")
        self.play(FadeIn(moves[1:], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        for k in range(2):
            self.play(Rotate(dp[3], angle=-0.6, about_point=dp[3][0].get_start()), run_time=0.3)
            a = apple(0.18).move_to(dp[4])
            self.play(FadeIn(a, shift=DOWN * 0.2), Rotate(dp[3], angle=0.6, about_point=dp[3][0].get_start()), run_time=0.35)
            self.play(a.animate.move_to(code_p[0][0].get_left() + LEFT * (0.3 + 0.4 * k) + DOWN * 0.1), run_time=0.6)
        fy = VGroup(T("a Fruit?", 22, GREY_A), tick(True, 0.13)).arrange(RIGHT, buff=0.12).next_to(code_p, LEFT, buff=1.2).shift(UP * 0.6)
        self.play(FadeIn(fy), run_time=0.4)
        self.at(2)
        nl = VGroup(lemon(0.18), T("nowhere to go in", 22, GREY_B)).arrange(RIGHT, buff=0.2).next_to(dp, UP, buff=0.25)
        self.play(FadeIn(nl), run_time=0.5)
        self.at(3)
        safe = T("nothing can go wrong", 28, OK).move_to([0.3, 2.9, 0])
        self.play(FadeIn(safe, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the fix: out =================
        k0 = M("interface Dispenser<T> {", 34, WHITE)
        k1 = M("interface Dispenser<out T> {", 34, WHITE)
        k0.move_to([0, 1.8, 0])
        k1.move_to([0, 1.8, 0])
        part(k1, "out").set_color(OK)
        prom = T("a promise: values of T only come out", 30, OK).move_to([0, 0.6, 0])
        once = T("written once, on the declaration", 24, GREY_B).move_to([0, 2.7, 0])
        self.say("fix")
        self.play(FadeIn(k0), FadeIn(once), run_time=0.6)
        self.at_text("out.", lead=0.4)
        self.play(TransformMatchingShapes(k0, k1), run_time=0.9)
        self.play(Indicate(part(k1, "out"), color=OK, scale_factor=1.4), run_time=0.6)
        self.at(2)
        self.play(FadeIn(prom, shift=UP * 0.1), run_time=0.6)
        self.hold()

        call = M("totalGrams(apples)", 30, WHITE).move_to([0, -0.8, 0])
        self.say("predict")
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)
        out = term(["apple total: 330 g"], 26, "ProducerDemo, real output").move_to([0, -2.3, 0])
        sum_ = T("180 + 150, through a dispenser of fruit", 24, GREY_A).next_to(out, RIGHT, buff=0.4)
        self.say("show")
        self.play(FadeIn(check_by(call, 0.18)), run_time=0.3)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sum_), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the map: lever, slot, sticker =================
        FL = -2.4
        floor = Line([-6.5, FL, 0], [0.6, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("apples").move_to([-3.4, FL + 1.5, 0])
        slot = DashedVMobject(Rectangle(width=1.1, height=0.28), num_dashes=16).set_stroke(GREY_B, 2).next_to(dp, UP, buff=0.12)
        stick = VGroup(RoundedRectangle(corner_radius=0.08, width=0.9, height=0.45).set_stroke(OK, 2.5).set_fill(dim(OK, 0.4), 1),
                       M("out", 24, WHITE))
        stick[1].move_to(stick[0])
        stick.rotate(-8 * DEGREES).move_to(dp[0].get_corner(UL) + RIGHT * 0.35 + DOWN * 0.3).set_z_index(5)
        rows = [("the lever", "a return type: a T flows out", WHITE), ("a slot", "a parameter: a T would flow in", GREY_A),
                ("out", "the sticker: lever only, no slot", OK)]
        mp = VGroup(*[VGroup(T(a, 26, c), M("->", 22, GREY_B), T(b, 26, WHITE)).arrange(RIGHT, buff=0.25) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([2.6, 0.4, 0])
        fit(mp, 7.2)
        mp.move_to([2.7, 0.4, 0])
        ex1 = M("fun next(): T?", 22, GREY_A).next_to(mp[0], DOWN, buff=0.08).align_to(mp[0][2], LEFT)
        self.say("map")
        self.play(Create(floor), FadeIn(dp), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), Indicate(dp[3], color=WHITE, scale_factor=1.3), run_time=0.7)
        self.play(FadeIn(ex1), run_time=0.3)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Create(slot), run_time=0.7)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), FadeIn(stick, scale=1.3), FadeOut(slot), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= what stops a slot? a surprise machine =================
        k = code_block(["interface Dispenser<out T> {", "    fun next(): T?", "    fun refill(item: T)", "}"], 28)
        part(k[0], "out").set_color(OK)
        k.move_to([0, 1.9, 0])
        self.say("slot_q")
        self.play(FadeIn(k[0]), FadeIn(k[1]), FadeIn(k[3]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(k[2], shift=RIGHT * 0.2), part(k[2], "refill(item: T)").animate.set_color(YELLOW_M), run_time=0.7)
        self.hold()

        FL = -2.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("apples", 0.7).move_to([-1.0, FL + 1.05, 0])
        view = paper(["seen as:", "Dispenser<Fruit>"], 18).next_to(dp, LEFT, buff=0.35)
        lm = lemon(0.17).move_to([-5.6, -0.3, 0])
        reader = who(COUNTER, "expects an apple", 1.0, 20).move_to([4.2, FL + 0.7, 0])
        self.say("slot")
        self.play(Create(floor), FadeIn(dp), run_time=0.6)
        self.at(1)
        self.play(FadeIn(view, shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lm), run_time=0.3)
        self.play(lm.animate.move_to(dp[1].get_center()), run_time=0.9)
        self.at(3)
        self.play(FadeIn(reader), run_time=0.4)
        self.play(Rotate(dp[3], angle=-0.6, about_point=dp[3][0].get_start()), run_time=0.3)
        self.play(lm.animate.move_to(reader[0][0].get_left() + LEFT * 0.3), Rotate(dp[3], angle=0.6, about_point=dp[3][0].get_start()), run_time=0.8)
        self.play(Flash(lm, color=BAD, line_length=0.25), run_time=0.5)
        self.hold()

        sm = T("a surprise machine", 30, YELLOW_M).move_to([-1.0, -0.2, 0]).next_to(dp, RIGHT, buff=0.4)
        er = err_line("type parameter 'T' is declared as 'out' but occurs in 'in' position", 22)
        fit(er, 12.4).next_to(k, DOWN, buff=0.3)
        self.say("slot2")
        self.at(1)
        self.play(FadeIn(sm, scale=1.2), run_time=0.6)
        self.at(2)
        self.play(Create(Underline(k[2], color=BAD, stroke_width=4, buff=0.06)), FadeIn(er, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the name: covariance, producer =================
        nm = T("covariance", 44, OK).move_to([0, 2.8, 0])
        co = T("co: together, in the same direction", 24, GREY_B).next_to(nm, DOWN, buff=0.15)
        fr = mbox("Fruit", GREY_A, size=28).move_to([-3.2, 1.0, 0])
        apb = mbox("Apple", APPLE, size=28).move_to([-3.2, -1.5, 0])
        a1 = Arrow(apb.get_top(), fr.get_bottom(), buff=0.12, stroke_width=4, color=OK, max_tip_length_to_length_ratio=0.12)
        df = mbox("Dispenser<Fruit>", GREY_A, size=26).move_to([2.8, 1.0, 0])
        da = mbox("Dispenser<Apple>", APPLE, size=26).move_to([2.8, -1.5, 0])
        a2 = Arrow(da.get_top(), df.get_bottom(), buff=0.12, stroke_width=4, color=OK, max_tip_length_to_length_ratio=0.12)
        isa = T("is a subtype of", 22, OK).next_to(a1, RIGHT, buff=0.15)
        same = T("same direction", 22, OK).next_to(a2, RIGHT, buff=0.15)
        prod = VGroup(T("producer:", 28, YELLOW_M), T("a type that only hands values out", 28)).arrange(RIGHT, buff=0.2).move_to([0, -2.85, 0])
        self.say("name")
        self.play(FadeIn(nm), run_time=0.6)
        self.at(1)
        self.play(FadeIn(co), run_time=0.5)
        self.play(FadeIn(fr), FadeIn(apb), GrowArrow(a1), FadeIn(isa), run_time=0.8)
        self.at(2)
        self.play(FadeIn(df), FadeIn(da), run_time=0.5)
        self.play(GrowArrow(a2), FadeIn(same), run_time=0.7)
        self.at(3)
        self.play(FadeIn(prod, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Java: ? extends at every use =================
        jc = code_block(["interface Dispenser<T> {", "    T next();                // null when it is empty", "}", "",
                         "static int totalGrams(Dispenser<? extends Fruit> dispenser) { ... }", "",
                         "totalGrams(apples);                // fine: the parameter says ? extends",
                         "Dispenser<Fruit> plain = apples;   // error"], 22,
                        hl={"// null when it is empty": GREY_B, "// fine: the parameter says ? extends": GREY_B, "// error": BAD})
        fit(jc, 12.4)
        jg = titled(jc, "Java").move_to([0, 1.2, 0])
        we = err_line("incompatible types: Dispenser<Apple> cannot be converted to Dispenser<Fruit>", 22)
        fit(we, 12.4).move_to([0, -2.55, 0])
        self.say("java")
        self.play(FadeIn(jg[0]), FadeIn(jc[:3], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(jc[4], shift=UP * 0.1), FadeIn(jc[6]), run_time=0.7)
        self.at_text("? extends", lead=0.3)
        self.play(part(jc[4], "? extends Fruit").animate.set_color(OK), Circumscribe(part(jc[4], "Dispenser<? extends Fruit>"), color=OK), run_time=1.0)
        self.at(2)
        self.play(FadeIn(jc[7], shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(we, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        dp = dispenser("apples", 0.7).move_to([-4.0, 0.2, 0])
        stick = VGroup(RoundedRectangle(corner_radius=0.08, width=0.8, height=0.4).set_stroke(OK, 2.5).set_fill(dim(OK, 0.4), 1), M("out", 22, WHITE))
        stick[1].move_to(stick[0])
        stick.rotate(-8 * DEGREES).move_to(dp[0].get_corner(UL) + RIGHT * 0.3 + DOWN * 0.25).set_z_index(5)
        kl = VGroup(T("Kotlin: the sticker on the machine, once", 24, OK), T("declaration-site variance", 24, GREY_A)).arrange(DOWN, buff=0.1)
        kl.next_to(dp, DOWN, buff=0.3)
        ppl = VGroup(*[person(COUNTER, 0.8) for _ in range(3)]).arrange(RIGHT, buff=0.55).move_to([2.8, 0.0, 0])
        notes = VGroup(*[paper(["? extends"], 14).scale(0.9).next_to(p, UP, buff=0.1) for p in ppl[:2]])
        nope = tick(False, 0.16).next_to(ppl[2], UP, buff=0.2)
        jl = VGroup(T("Java: a note in every customer's pocket", 24, GREY_A), T("use-site variance", 24, GREY_A)).arrange(DOWN, buff=0.1)
        jl.move_to([2.8, -1.5, 0])
        self.say("java2")
        self.play(FadeIn(dp), run_time=0.5)
        self.at(1)
        self.play(FadeIn(stick, scale=1.3), FadeIn(kl[0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ppl), FadeIn(notes, shift=UP * 0.1), FadeIn(jl[0]), run_time=0.8)
        self.at_text("anyone who forgets", lead=0.2)
        self.play(FadeIn(nope), run_time=0.4)
        self.at(3)
        self.play(FadeIn(kl[1]), FadeIn(jl[1]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the guardrail =================
        g1 = rule_row("Promise out only if it's true: T appears only where values come out.", 28)
        g2 = rule_row("out doesn't mean read-only, or unchanging.", 28)
        g2n = T("every pull still takes an apple out of the machine (end of this lesson)", 22, GREY_B)
        gg = VGroup(g1, g2, g2n).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.8, 0])
        g2n.shift(RIGHT * 0.5)
        fit(gg, 12.4)
        dp = dispenser("apples", 0.55).move_to([0, -2.2, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(g1, shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g2, shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(g2n), FadeIn(dp), run_time=0.6)
        self.play(FadeOut(dp[2][0], shift=DOWN * 0.3), FadeOut(dp[2][1], shift=DOWN * 0.3), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why couldn't the compiler see there's no slot?", 34)
        m1 = T("It trusts what you declare, not what you meant.", 30, GREY_A)
        m2 = T("Say out, and an apple dispenser is a fruit dispenser.", 30, OK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.1)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qh = VGroup(T("Check: inside", 28, YELLOW_M), M("interface Dispenser<out T>", 26, WHITE)).arrange(RIGHT, buff=0.25)
        qa = M("a)  val latest: T", 28, WHITE)
        qb = M("b)  var current: T", 28, WHITE)
        qg = VGroup(qh, qa, qb).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(DOWN * 0.7)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        self.say("check_a")
        self.play(FadeIn(check_by(qa, 0.18)), FadeIn(cross_by(qb, 0.18)), run_time=0.5)
        self.at(2)
        al = err_line("... declared as 'out' but occurs in 'invariant' position", 22).move_to(DOWN * 2.75)
        fit(al, 12.4)
        self.play(FadeIn(al, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
