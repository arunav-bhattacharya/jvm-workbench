from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"Enum<E extends Enum<E>>", "Enum of E extends Enum of E"),
    (r"\bB : Builder<B>", "B colon Builder of B"), (r"\bT : Comparable<T>", "T colon Comparable of T"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"\bPlainGiftBoxBuilder\b", "plain gift box builder"), (r"\bGiftBoxBuilder\b", "gift box builder"),
    (r"\bPlainBuilder\b", "plain builder"), (r"\bPickupBuilder\b", "pickup builder"),
    (r"\bself\(\)", "self"), (r"\b1200\b", "twelve hundred"), (r"\bkotlinc\b", "kotlin C"),
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



# ---- this video's own pictures ----
BASE_C, GIFT_C, B_C = BLUE_M, GOLD_M, TEAL_M     # the base form, the gift-box form, the blank B


def form(title, lines, w=3.6, size=20, title_color=INK, dim_from=None):
    """A printed order form: a title line, then one line per field. dim_from greys out lines from that index on."""
    rows = [M(title, size + 2, title_color)] + [M(l, size, INK) for l in lines]
    g = VGroup(*rows).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    r = Rectangle(width=w, height=g.height + 0.5).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    g.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.25)
    rule = Line(r.get_left() + RIGHT * 0.15, r.get_right() + LEFT * 0.15, stroke_width=1.5, color=GREY_B)
    rule.next_to(rows[0], DOWN, buff=0.08).set_x(r.get_x())
    return VGroup(r, g, rule)


def chain_step(code, typ, color, size=24):
    c = M(code, size, WHITE)
    t = vchip(typ, color, 20, 0.5).next_to(c, DOWN, buff=0.25)
    return VGroup(c, t)


N = {
    "open": "Orders at the fruit shop come on printed forms. Every form starts with the same lines: the variety, the "
            "weight, a note. A gift-box form adds a line for the ribbon. A delivery form adds a line for the address.",
    "helper": "A helper fills in a form one line at a time, and hands it back after each line. Here's the odd part. The "
              "helper fills in the weight on a gift-box form, and what comes back is: an order form. The ribbon line is "
              "still printed on the paper. But nobody is allowed to look at it any more.",
    "joke": "It's like handing your birthday cake over to be boxed, and getting it back with a label that says: food. "
            "Not wrong, exactly. Just no help at all when you're looking for the candles.",
    "shyq": "Here's a question that's easy to be shy about. The form really is a gift-box form the whole time. So why "
            "does the compiler forget?",
    "builder": "In code, the form is a builder: an object you fill in one setting at a time, and then ask to build the "
               "finished thing. Each setter returns the builder, so the calls can follow each other on one line. That "
               "style is called a fluent chain.",
    "code": "Put the shared setter, grams, in a base class called PlainBuilder. Then add a subclass, PlainGiftBoxBuilder, "
            "with a setter of its own: ribbon.",
    "predict": "Now two chains. Ribbon first, then grams. Or grams first, then ribbon. Which one compiles? Pause and guess.",
    "show": "Ribbon first compiles. Grams first does not. Kotlin says: unresolved reference ribbon, on receiver of type "
            "PlainBuilder. And Java says: cannot find symbol.",
    "why": "Follow the types, the way the compiler does. Each call returns its declared type, and the compiler goes by "
           "that, not by the object. ribbon returns a PlainGiftBoxBuilder, so grams can follow. But grams returns a "
           "PlainBuilder, because that's all the base class knows about itself.",
    "demo": "So is the object still a gift box? The lesson's demo checks. It prints: after grams, static type "
            "PlainBuilder, run-time class PlainGiftBoxBuilder. The object is fine. The form has just forgotten what kind "
            "of form it is.",
    "wish": "What we want is a base class that can say: I return whatever subclass I really am.",
    "blank": "So let's go back to the paper. Print a blank at the top of the base form: this is a, blank, form. Each kind "
             "of form writes its own name in the blank. The gift-box form writes: gift box. Now, when the helper hands "
             "the form back, the blank says what kind of form it is.",
    "map": "Let's map it. The blank is a type parameter, B. The base form is Builder<B>. Writing your own name in the "
           "blank is the subclass declaration: GiftBoxBuilder is a Builder<GiftBoxBuilder>. And the setter that hands "
           "the form back now returns B.",
    "subst": "Now fill in the blank, the same trick as the first lesson. For a GiftBoxBuilder, every B in the base class "
             "reads GiftBoxBuilder. So grams returns a GiftBoxBuilder, and ribbon is in reach again. The demo builds "
             "the finished box: gift box, 1200 grams, red ribbon.",
    "bound": "Now look at the bound itself: B : Builder<B>. The B inside points back at the B it bounds. Read it as: B "
             "is a builder whose own B is B.",
    "joke2": "If that sentence made you a little dizzy, you're in good company. Read it like the form instead. The only "
             "names that fit the blank belong to forms that write their own name there.",
    "self": "One more piece. Inside the base class, this is only known to be a Builder<B>, not a B. So grams returns "
            "self(), and each subclass writes self() as: return this. The compiler checks that it fits.",
    "shortcut": "The tempting shortcut is to write this as B, right in the base class. That's an unchecked cast, and "
                "erasure turns it into no check at all.",
    "break_q": "So far so good. Now let's try to cheat. A class called Liar writes someone else's name in its blank: "
               "Builder<GiftBoxBuilder>. Does it compile? Pause and guess.",
    "break": "It compiles. The bound only asks for the name of some builder. And here the form picture breaks, just as "
             "the code does: anyone can write another form's name in the blank.",
    "break2": "But the abstract self() is where you notice. The liar must hand back a GiftBoxBuilder it doesn't have, so "
              "it makes a fresh one. Fill in the weight on the liar, and what comes back is a GiftBoxBuilder: a new "
              "object, not the liar you filled in.",
    "copy": "And here's the slip that really happens. Someone adds a pickup form by copying the gift-box builder, and "
            "forgets to change the name in the blank. The abstract self() catches it at compile time: return type "
            "mismatch, expected GiftBoxBuilder, actual PickupBuilder. With this as B, the same slip would compile, "
            "and fail later, at the call.",
    "name": "Now the names. A type parameter that stands for my own subclass is called a self type. A bound that "
            "mentions the type parameter itself is called a recursive bound. And you've met the shape before: "
            "T : Comparable<T>, a T that compares with its own kind, and Java's own Enum<E extends Enum<E>>.",
    "guard": "And the guardrail. In plain Kotlin code, the best builder is often the one you never write. A data class "
             "with default arguments and copy covers most cases. Reach for self types when Java callers need a "
             "builder, or when you extend a Java class that already uses one.",
    "moral": "So, why did the compiler forget? Because a base setter could only promise the base class. Give the base "
             "form a blank, and let each subclass write its own name there. A recursive bound lets a base class "
             "return its subclass.",
    "check": "Quick check. Take a new GiftBoxBuilder, and call grams with 1200. What type does the compiler see?",
    "check_a": "GiftBoxBuilder. grams returns B, and the declaration filled B with GiftBoxBuilder. So ribbon is still in "
               "reach.",
}


class Gen10Recursive(Narrated):
    """gen-10, section 0: printed order forms; the helper hands a gift-box form back as 'an order form'; the birthday
    cake labelled food; PlainBuilder and PlainGiftBoxBuilder; predict which chain compiles; the real errors; the static
    type vs the run-time class (SelfTypeDemo); the blank at the top of the base form, mapped to B : Builder<B>;
    substitution; the bound read aloud; self() vs this as B; the Liar and the copied PickupBuilder; self type and
    recursive bound named; Comparable and Enum; guardrail (data class and copy); moral; a check."""

    def construct(self):
        self.title_card("A form that names itself", "recursive bounds keep a builder chain typed")

        # ================= the forms =================
        base = form("ORDER FORM", ["variety: ______", "weight:  ______", "note:    ______"], 3.6)
        gift = form("GIFT-BOX FORM", ["variety: ______", "weight:  ______", "note:    ______", "ribbon:  ______"], 3.6)
        deli = form("DELIVERY FORM", ["variety: ______", "weight:  ______", "note:    ______", "address: ______"], 3.6)
        VGroup(base, gift, deli).arrange(RIGHT, buff=0.6, aligned_edge=UP).move_to([0, 0.6, 0])
        self.say("open")
        self.play(FadeIn(base, shift=UP * 0.2), run_time=0.7)
        self.at(1)
        self.play(Indicate(base[1][1:4], color=BASE_C, scale_factor=1.05), run_time=0.8)
        self.at(2)
        self.play(FadeIn(gift, shift=UP * 0.2), run_time=0.6)
        self.play(gift[1][4].animate.set_color(GIFT_C), run_time=0.4)
        self.at(3)
        self.play(FadeIn(deli, shift=UP * 0.2), run_time=0.6)
        self.hold()

        # the helper fills in the weight on the gift-box form
        FL = -2.6
        helper = who(GREY_A, "helper", 1.1, 22).move_to([-5.2, FL + 0.8, 0])
        self.say("helper")
        self.play(FadeOut(base), FadeOut(deli), gift.animate.move_to([-1.6, 0.5, 0]), FadeIn(helper), run_time=0.9)
        self.at(2)
        wt = Text("1200 g", font=FONT, font_size=22, color=PEN, slant=ITALIC).next_to(part(gift[1][2], "weight:"), RIGHT, buff=0.35)
        self.play(Write(wt), Indicate(helper[0], color=GREY_A, scale_factor=1.15), run_time=0.8)
        back = gift.copy().add(wt.copy())
        self.add(back)
        self.play(back.animate.move_to([3.6, 0.5, 0]), run_time=0.9)
        cover = Rectangle(width=back[0].width - 0.1, height=0.42).set_stroke(width=0).set_fill(PAPER, 1).move_to(back[1][0]).align_to(back[0], LEFT).shift(RIGHT * 0.05)
        cov_t = M("an order form", 22, BAD).move_to(cover).align_to(back[1][0], LEFT)
        self.play(FadeIn(cover), FadeIn(cov_t), run_time=0.6)
        self.at(3)
        self.play(Indicate(back[1][4], color=GIFT_C, scale_factor=1.1), run_time=0.7)
        self.at(4)
        veil = Rectangle(width=back[0].width - 0.1, height=0.4).set_stroke(width=0).set_fill(GREY_D, 0.85).move_to(back[1][4]).set_x(back[0].get_x())
        lk = T("not allowed to look", 22, BAD).next_to(back, DOWN, buff=0.25)
        self.play(FadeIn(veil), FadeIn(lk, shift=UP * 0.1), run_time=0.7)
        self.hold()

        cake = VGroup(Rectangle(width=1.6, height=0.7).set_stroke(GIFT_C, 3).set_fill(dim(GIFT_C, 0.4), 1),
                      Rectangle(width=1.1, height=0.5).set_stroke(GIFT_C, 3).set_fill(dim(GIFT_C, 0.5), 1))
        cake[1].next_to(cake[0], UP, buff=0)
        cand = VGroup(*[Line(UP * 0, UP * 0.3, stroke_width=4, color=RED_M) for _ in range(3)]).arrange(RIGHT, buff=0.25).next_to(cake[1], UP, buff=0)
        cakeg = VGroup(cake, cand).move_to([0, -2.4, 0])
        food = paper(["food"], 24).next_to(cakeg, RIGHT, buff=0.4)
        self.say("joke")
        self.play(FadeOut(helper), FadeIn(cakeg, shift=UP * 0.1), run_time=0.6)
        self.at_text("food", lead=0.3)
        self.play(FadeIn(food, shift=LEFT * 0.2), run_time=0.5)
        self.at(2)
        self.play(Indicate(cand, color=RED_M, scale_factor=1.3), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.2, 0])
        q1 = T("It really is a gift-box form the whole time.", 36)
        q2 = T("So why does the compiler forget?", 36, GIFT_C)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.4).move_to([0, 0.2, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= builder, fluent chain, the plain code =================
        bl = VGroup(T("builder:", 30, YELLOW_M), T("fill in one setting at a time, then build", 30)).arrange(RIGHT, buff=0.25).move_to([0, 2.6, 0])
        fl = M('GiftBoxBuilder().grams(1_200).ribbon("red").build()', 26, WHITE).move_to([0, 1.3, 0])
        fll = T("a fluent chain: each setter returns the builder", 24, GREY_B).next_to(fl, DOWN, buff=0.25)
        self.say("builder")
        self.play(FadeIn(bl, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(fl, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fll), run_time=0.5)
        self.hold()
        self.wipe()

        jv = code_block(["class PlainBuilder {",
                         "    PlainBuilder grams(int grams) { ...; return this; }", "}",
                         "class PlainGiftBoxBuilder extends PlainBuilder {",
                         "    PlainGiftBoxBuilder ribbon(String colour) { ... }", "}"], 22)
        kt = code_block(["open class PlainBuilder {",
                         "    fun grams(grams: Int): PlainBuilder { ...; return this }", "}",
                         "class PlainGiftBoxBuilder : PlainBuilder() {",
                         "    fun ribbon(colour: String): PlainGiftBoxBuilder { ... }", "}"], 22)
        for c in (jv, kt):
            part(c[1], "PlainBuilder").set_color(BASE_C)
            part(c[4], "PlainGiftBoxBuilder").set_color(GIFT_C)
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        cg = VGroup(jg, kg).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        fit(cg, 12.4).move_to([0, 0.2, 0])
        self.say("code")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.8)
        self.play(Indicate(jv[1], color=BASE_C, scale_factor=1.03), Indicate(kt[1], color=BASE_C, scale_factor=1.03), run_time=0.8)
        self.at(1)
        self.play(Indicate(jv[4], color=GIFT_C, scale_factor=1.03), Indicate(kt[4], color=GIFT_C, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= predict: which chain compiles? =================
        c1 = M('PlainGiftBoxBuilder().ribbon("red").grams(1_200)', 26, WHITE)
        c2 = M('PlainGiftBoxBuilder().grams(1_200).ribbon("red")', 26, WHITE)
        ch = VGroup(c1, c2).arrange(DOWN, buff=0.6, aligned_edge=LEFT).move_to([-0.3, 1.6, 0])
        lab1 = T("1", 26, GREY_B).next_to(c1, LEFT, buff=0.35)
        lab2 = T("2", 26, GREY_B).next_to(c2, LEFT, buff=0.35)
        self.say("predict")
        self.at(1)
        self.play(FadeIn(c1, shift=UP * 0.1), FadeIn(lab1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(c2, shift=UP * 0.1), FadeIn(lab2), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        ek = VGroup(T("kotlinc", 22, GREY_B), err_line("Unresolved reference 'ribbon' on receiver of type 'PlainBuilder'.", 22)).arrange(RIGHT, buff=0.25)
        ej = VGroup(T("javac", 22, GREY_B), err_line("cannot find symbol", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(ek, ej).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        fit(eg, 12.4).move_to([0, -0.5, 0])
        self.say("show")
        self.play(FadeIn(check_by(c1)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cross_by(c2)), part(c2, 'ribbon("red")').animate.set_color(BAD), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ek, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(ej, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= follow the types =================
        s1 = chain_step("PlainGiftBoxBuilder()", "PlainGiftBoxBuilder", GIFT_C)
        s2 = chain_step('.ribbon("red")', "PlainGiftBoxBuilder", GIFT_C)
        s3 = chain_step(".grams(1_200)", "PlainBuilder", BASE_C)
        row1 = VGroup(s1, s2, s3).arrange(RIGHT, buff=0.15, aligned_edge=UP)
        fit(row1, 12.4).move_to([0, 2.1, 0])
        ok1 = check_by(row1[2][0], 0.18, 0.15)
        t1 = chain_step("PlainGiftBoxBuilder()", "PlainGiftBoxBuilder", GIFT_C)
        t2 = chain_step(".grams(1_200)", "PlainBuilder", BASE_C)
        t3 = chain_step('.ribbon("red")', "no ribbon here", BAD)
        row2 = VGroup(t1, t2, t3).arrange(RIGHT, buff=0.15, aligned_edge=UP)
        fit(row2, 12.4).move_to([0, -0.1, 0])
        self.say("why")
        self.play(FadeIn(s1[0]), FadeIn(t1[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(s1[1], shift=DOWN * 0.1), FadeIn(t1[1], shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(s2[0]), run_time=0.4)
        self.play(FadeIn(s2[1], shift=DOWN * 0.1), run_time=0.4)
        self.play(FadeIn(s3[0]), FadeIn(s3[1], shift=DOWN * 0.1), FadeIn(ok1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(t2[0]), run_time=0.4)
        self.play(FadeIn(t2[1], shift=DOWN * 0.1), Indicate(t2[1], color=BASE_C, scale_factor=1.1), run_time=0.7)
        self.play(FadeIn(t3[0]), FadeIn(t3[1], shift=DOWN * 0.1), FadeIn(cross_by(t3[0], 0.18, 0.15)), run_time=0.6)
        self.hold()

        out = term(["after grams(): static type PlainBuilder, run-time class PlainGiftBoxBuilder"], 21, "SelfTypeDemo, real output")
        fit(out, 12.4).move_to([0, -2.0, 0])
        self.say("demo")
        self.at(1)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(part(out[1][0], "PlainBuilder").animate.set_color(BASE_C), part(out[1][0], "PlainGiftBoxBuilder").animate.set_color(GIFT_C), run_time=0.6)
        self.at(3)
        self.play(Indicate(part(out[1][0], "PlainGiftBoxBuilder"), color=GIFT_C, scale_factor=1.1), run_time=0.7)
        self.hold()

        wish = T("wanted: a base class that says \"I return whatever subclass I really am\"", 28, OK)
        fit(wish, 12.4).move_to([0, -3.15, 0])
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the blank at the top of the form =================
        bf = form("this is a ________ form", ["variety: ______", "weight:  ______", "note:    ______"], 4.6, 22)
        bf.move_to([-3.4, 0.8, 0])
        blank = part(bf[1][0], "________")
        gf = form("this is a ________ form", ["variety: ______", "weight:  ______", "note:    ______", "ribbon:  ______"], 4.6, 22)
        gf.move_to([3.3, 0.6, 0])
        gblank = part(gf[1][0], "________")
        gname = Text("gift box", font=FONT, font_size=24, color=PEN, slant=ITALIC).move_to(gblank).shift(UP * 0.05)
        self.say("blank")
        self.play(FadeIn(bf, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(blank, color=B_C, scale_factor=1.2), blank.animate.set_color(B_C), run_time=0.8)
        self.at(2)
        self.play(FadeIn(gf, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeOut(gblank), Write(gname), run_time=0.9)
        self.at(4)
        wt = Text("1200 g", font=FONT, font_size=22, color=PEN, slant=ITALIC).next_to(part(gf[1][2], "weight:"), RIGHT, buff=0.35)
        self.play(Write(wt), run_time=0.7)
        self.play(Indicate(gname, color=PEN, scale_factor=1.2), run_time=0.7)
        self.hold()

        rows = [("the blank", "B", B_C), ("the base form", "Builder<B>", BASE_C),
                ("writing your own name in it", "GiftBoxBuilder : Builder<GiftBoxBuilder>()", GIFT_C),
                ("the helper hands back", "fun grams(grams: Int): B", B_C)]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), M(b, 24, c)).arrange(RIGHT, buff=0.25) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        fit(mp, 12.4).move_to([0, -2.45, 0])
        self.say("map")
        self.play(VGroup(bf, gf, gname, wt).animate.shift(UP * 0.5), run_time=0.4)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), Indicate(blank, color=B_C, scale_factor=1.2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), Indicate(gname, color=PEN, scale_factor=1.2), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the code, and substitution =================
        jv = code_block(["abstract class Builder<B extends Builder<B>> {",
                         "    B grams(int grams) { ...; return self(); }",
                         "    protected abstract B self();", "}",
                         "final class GiftBoxBuilder extends Builder<GiftBoxBuilder> {",
                         "    @Override protected GiftBoxBuilder self() { return this; }", "}"], 22)
        kt = code_block(["abstract class Builder<B : Builder<B>> {",
                         "    fun grams(grams: Int): B { ...; return self() }",
                         "    protected abstract fun self(): B", "}",
                         "class GiftBoxBuilder : Builder<GiftBoxBuilder>() {",
                         "    override fun self() = this", "}"], 22)
        for c in (jv, kt):
            part(c[4], "Builder<GiftBoxBuilder>").set_color(GIFT_C)
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        cg = VGroup(jg, kg).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        fit(cg, 12.4).move_to([0, 0.35, 0])
        bs = VGroup(part(kt[1], "B", 0), part(kt[2], "B", 0), part(jv[1], "B", 0), part(jv[2], "B", 0))
        r1 = VGroup(chain_step("GiftBoxBuilder()", "GiftBoxBuilder", GIFT_C), chain_step(".grams(1_200)", "B = GiftBoxBuilder", GIFT_C),
                    chain_step('.ribbon("red")', "GiftBoxBuilder", GIFT_C), chain_step(".build()", "String", WHITE)).arrange(RIGHT, buff=0.15, aligned_edge=UP)
        fit(r1, 12.4).move_to([0, 1.4, 0])
        out = term(["gift box, 1200 g, red ribbon"], 22, "SelfTypeDemo, real output").move_to([0, -1.0, 0])
        self.say("subst")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(part(kt[4], "Builder<GiftBoxBuilder>"), color=GIFT_C, scale_factor=1.05),
                  Indicate(part(jv[4], "Builder<GiftBoxBuilder>"), color=GIFT_C, scale_factor=1.05), run_time=0.8)
        self.play(*[b.animate.set_color(GIFT_C) for b in bs], run_time=0.5)
        self.play(LaggedStart(*[Indicate(b, color=GIFT_C, scale_factor=1.5) for b in bs], lag_ratio=0.15), run_time=1.0)
        self.at(2, lead=0.6)
        self.play(FadeOut(cg), run_time=0.4)
        self.play(FadeIn(r1[0]), run_time=0.3)
        self.play(FadeIn(r1[1]), run_time=0.4)
        self.play(FadeIn(r1[2]), FadeIn(check_by(r1[2][0], 0.18, 0.15)), run_time=0.4)
        self.at(3)
        self.play(FadeIn(r1[3]), run_time=0.3)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the bound read aloud =================
        bd = M("B : Builder<B>", 48, WHITE).move_to([0, 1.8, 0])
        b0, b1 = part(bd, "B", 0), part(bd, "B", 2)
        loop = CurvedArrow(b1.get_top() + UP * 0.1, b0.get_top() + UP * 0.1, angle=PI / 2.2, color=B_C, stroke_width=3)
        rd = T("\"B is a builder whose own B is B\"", 32, GREY_A).move_to([0, 0.2, 0])
        self.say("bound")
        self.play(FadeIn(bd), run_time=0.6)
        self.at(1)
        self.play(b0.animate.set_color(B_C), b1.animate.set_color(B_C), Create(loop), run_time=0.9)
        self.at(2)
        self.play(FadeIn(rd, shift=UP * 0.1), run_time=0.6)
        self.hold()

        jk = T("only forms that write their own name fit the blank", 28, OK).move_to([0, -1.4, 0])
        self.say("joke2")
        self.play(Rotate(loop, angle=2 * PI, about_point=loop.get_center()), run_time=1.2)
        self.at(1)
        self.play(FadeIn(jk, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= self() and the tempting shortcut =================
        sk = code_block(["abstract class Builder<B : Builder<B>> {",
                         "    fun grams(grams: Int): B { this.grams = grams; return self() }",
                         "    protected abstract fun self(): B", "}",
                         "class GiftBoxBuilder : Builder<GiftBoxBuilder>() {",
                         "    override fun self() = this", "}"], 22)
        fit(sk, 12.4).move_to([0, 1.4, 0])
        thisb = VGroup(T("inside the base class,", 24, GREY_B), M("this", 24, WHITE), T("is a", 24, GREY_B),
                       M("Builder<B>", 24, BASE_C), T(", not a", 24, GREY_B), M("B", 24, B_C)).arrange(RIGHT, buff=0.15)
        thisb.move_to([0, -1.0, 0])
        self.say("self")
        self.play(FadeIn(sk, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(thisb, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(part(sk[1], "self()"), color=B_C, scale_factor=1.2), run_time=0.6)
        self.play(Indicate(sk[5], color=GIFT_C, scale_factor=1.05), run_time=0.7)
        self.at(3)
        self.play(FadeIn(check_by(sk[5], 0.18)), run_time=0.4)
        self.hold()

        sc = VGroup(M("return this as B", 26, WHITE), T("unchecked: erasure leaves no check at all", 24, BAD)).arrange(RIGHT, buff=0.4)
        fit(sc, 12.4).move_to([0, -2.4, 0])
        self.say("shortcut")
        self.play(FadeIn(sc[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sc[1], shift=UP * 0.1), FadeIn(cross_by(sc, 0.18)), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= break it: the Liar =================
        lc = M("class Liar : Builder<GiftBoxBuilder>() { override fun self() = GiftBoxBuilder() }", 22, WHITE)
        fit(lc, 12.4).move_to([0, 2.3, 0])
        part(lc, "Builder<GiftBoxBuilder>").set_color(GIFT_C)
        self.say("break_q")
        self.at(2)
        self.play(FadeIn(lc, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(Indicate(part(lc, "Builder<GiftBoxBuilder>"), color=GIFT_C, scale_factor=1.08), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        lf = form("this is a ________ form", ["variety: ______", "weight:  ______", "note:    ______"], 4.6, 22).move_to([-3.2, -0.6, 0])
        lname = Text("gift box", font=FONT, font_size=24, color=PEN, slant=ITALIC).move_to(part(lf[1][0], "________")).shift(UP * 0.05)
        lw = who(BAD, "Liar", 1.0, 22).next_to(lf, LEFT, buff=0.3)
        comp = VGroup(tick(True, 0.2), T("it compiles", 26, GREY_A)).arrange(RIGHT, buff=0.2).move_to([3.0, 1.1, 0])
        self.say("break")
        self.play(FadeIn(comp), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lf), FadeIn(lw), run_time=0.6)
        self.at(2)
        self.play(FadeOut(part(lf[1][0], "________")), Write(lname), run_time=0.9)
        brk = T("the picture breaks: anyone can write another form's name", 22, GREY_A).move_to([0, -2.6, 0])
        self.play(FadeIn(brk), run_time=0.5)
        self.hold()

        fresh = form("this is a ________ form", ["variety: ______", "weight:  5 g", "note:    ______", "ribbon:  ______"], 4.2, 20)
        fresh.move_to([3.4, -0.6, 0])
        fname = Text("gift box", font=FONT, font_size=22, color=PEN, slant=ITALIC).move_to(part(fresh[1][0], "________")).shift(UP * 0.05)
        fl_ = T("Liar().grams(5) gives back a new GiftBoxBuilder", 22, GIFT_C).next_to(fresh, UP, buff=0.2)
        fit(fl_, 6.0)
        self.say("break2")
        self.play(FadeOut(comp), run_time=0.3)
        self.at(1)
        self.play(FadeIn(fresh, shift=LEFT * 0.3), FadeIn(fname), run_time=0.8)
        self.at(2)
        self.play(FadeIn(fl_), run_time=0.6)
        self.play(Indicate(lw[0], color=BAD, scale_factor=1.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the slip that really happens: a copied PickupBuilder =================
        pk = code_block(["class PickupBuilder : OrderBuilder<GiftBoxBuilder>() {   // copied, not changed",
                         "    override fun self(): GiftBoxBuilder = this", "}"], 22)
        fit(pk, 12.4).move_to([0, 2.0, 0])
        part(pk[0], "GiftBoxBuilder").set_color(BAD)
        e1 = VGroup(T("kotlinc", 22, GREY_B), err_line("Return type mismatch: expected 'GiftBoxBuilder', actual 'PickupBuilder'.", 22)).arrange(RIGHT, buff=0.25)
        e2 = VGroup(T("javac", 22, GREY_B), err_line("incompatible types: PickupBuilder cannot be converted to GiftBoxBuilder", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(e1, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        fit(eg, 12.4).move_to([0, 0.2, 0])
        late = T("with  this as B  the same slip compiles, and fails later, at the call", 24, GREY_A).move_to([0, -1.4, 0])
        fit(late, 12.4)
        self.say("copy")
        self.play(FadeIn(pk, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(part(pk[0], "GiftBoxBuilder"), color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(e1, shift=UP * 0.1), FadeIn(e2, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(late, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(M("B", 32, B_C), T("self type: stands for \"my own subclass\"", 28)).arrange(RIGHT, buff=0.35)
        n2 = VGroup(M("B : Builder<B>", 32, WHITE), T("recursive bound: mentions its own type parameter", 28)).arrange(RIGHT, buff=0.35)
        n3 = VGroup(T("met before:", 26, GREY_B), M("T : Comparable<T>", 28, WHITE), M("Enum<E extends Enum<E>>", 28, WHITE)).arrange(RIGHT, buff=0.4)
        ng = VGroup(n1, n2, n3).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.4, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(n3[0]), FadeIn(n3[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("Java's own", lead=0.3)
        self.play(FadeIn(n3[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        gq = T("Do you need a builder at all?", 34).move_to([0, 2.6, 0])
        dc = code_block(['data class GiftBox(val grams: Int = 0, val ribbon: String = "")',
                         'val box = GiftBox(grams = 1_200).copy(ribbon = "red")'], 22)
        fit(dc, 12.4).move_to([0, 1.2, 0])
        dct = T("Kotlin: a data class with default arguments and copy", 22, GREY_B).next_to(dc, UP, buff=0.2)
        g1 = rule_row("Java callers need a builder", 26)
        g2 = rule_row("you extend a Java class that already uses one", 26)
        gg = VGroup(T("Reach for self types when:", 26, GREY_A), g1, g2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -1.6, 0])
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(dc, shift=UP * 0.1), FadeIn(dct), run_time=0.7)
        self.at(3)
        self.play(FadeIn(gg[0]), FadeIn(g1, shift=RIGHT * 0.1), run_time=0.6)
        self.at_text("or when", lead=0.3)
        self.play(FadeIn(g2, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why did the compiler forget?", 32, GREY_A)
        m1 = T("A base setter could only promise the base class.", 30, BAD)
        m2 = T("Give the base form a blank; each subclass writes its own name there.", 30, OK)
        m3 = T("A recursive bound lets a base class return its subclass.", 32, YELLOW_M)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("GiftBoxBuilder().grams(1_200)", 28, WHITE), T("has which static type?", 28)).arrange(RIGHT, buff=0.2)
        fit(qc, 12.4).move_to([0, -1.1, 0])
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("GiftBoxBuilder", 28, GIFT_C), T(": B was filled with it, so ribbon is in reach", 26, GREY_A)).arrange(RIGHT, buff=0.15)
        fit(ans, 12.4).move_to([0, -2.4, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
