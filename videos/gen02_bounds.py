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
    "open": "Back in the storeroom. Last lesson, every box got a label with a blank: Box of, and then whatever the caller "
            "writes in. Any caller, any type. That freedom has a price, and it surprises people.",
    "shyq": "Here's a question that's easy to be shy about. I only ever pass fruit to my function. So why can't my "
            "generic code ask a T for its weight? Can't the compiler see my callers?",
    "plain": "Start with a plain T, with no sign on it. describe takes any T, and prints its value and its hash code. "
             "Gala, 180, even null: all fine.",
    "plain2": "That works because toString, hashCode and equals exist on every type. In Kotlin, the type that covers "
              "every value, null included, is Any?. A plain T can do what Any? can do, and nothing more.",
    "length_q": "Now ask for something more specific. lengthOf returns x dot length. Every caller you have in mind passes "
                "a String. Does it compile? Pause and guess.",
    "length": "No: unresolved reference, length. The compiler isn't being fussy. Someone could call lengthOf with 42, and "
              "an Int has no length. A generic function must work for every type a caller may pick, so it can only use "
              "what all of them share.",
    "bigger": "Comparing fails too, with a stranger message. Write a greater than b on two T's, and Kotlin talks about "
              "compareTo on String. You never mentioned String.",
    "bigger2": "It's like asking the clerk for a ripe apple, and hearing that the paper bags are the wrong shape. A "
               "roundabout no. So when an error names some other type's method, read it as: this isn't defined for T.",
    "sign": "Back to the storeroom. One box carries a sign: fruit only. The sign shuts out the hammer and the till roll. "
            "In return, whoever unpacks the box knows something about every item in it: each one has a weight, so it "
            "can go straight on the scales.",
    "map": "Let's map it. The sign is a bound on T, written T : Fruit in Kotlin, and T extends Fruit in Java. The hammer "
           "at the door is a caller the bound shuts out. And the scales are the function's body, which may now use the "
           "weight.",
    "code": "Here's the shop's fruit in code. Fruit is an interface with a name and a weight in grams. Apple is a small "
            "data class that implements it. heavier takes two T's, where T must be a Fruit, and returns the heavier one. "
            "Inside, a dot grams compiles, because every T is now some kind of Fruit.",
    "run": "Two apples: Gala at 180 grams, and Fuji at 150. The demo prints Gala, 180 grams. And two strings? Argument "
           "type mismatch: actual type is String, but Fruit was expected. The sign did its job, at the door.",
    "whyT_q": "You might be thinking: why a T at all? Just take two Fruit parameters, and return a Fruit. Fewer angle "
              "brackets, same thing, right?",
    "whyT": "Let's be fair, and try it. Two apples go in, and a Fruit comes out. To get your Apple back, you'd need a cast: "
            "the very thing the last lesson took away. With T, two apples in give an Apple out.",
    "cmp": "The most common bound isn't a class you wrote. It's Comparable. Read T : Comparable<T> aloud as: T is "
           "something that can be compared with another T. Now a greater than b compiles, because the bound promises "
           "a compareTo.",
    "cmp2": "So 180 and 150 give 180. And Gala and Fuji give Gala, the one that comes later in the alphabet.",
    "apples_q": "Now hand maxOf2 two apples. What happens? Pause and guess.",
    "apples": "It fails: actual type is Apple, but a Comparable was expected. Apple has no natural order. Should two "
              "apples compare by weight? By name? By price? The compiler refuses to pick favorites, and it's right.",
    "apples2": "So you choose. Make Apple a Comparable of Apple, by weight, say. Or, usually better, keep Apple plain, and "
               "pass a Comparator, a small object that compares two values, where you need an order.",
    "breaks": "The sign picture breaks in one place. A real fruit only sign is checked by a person, who looks at the "
              "item. The compiler only trusts what the types declare. A class with a grams property that doesn't say "
              "it's a Fruit is still turned away.",
    "name": "Now the name. A sign like this is called an upper bound: T must be this type, or a subtype of it. For now, "
            "read subtype as a class that inherits from it, the way Apple inherits from Fruit. The next lesson makes "
            "that word exact.",
    "guard": "And the guardrail. A bound shuts some callers out, and lets the body do more. So ask for exactly what the "
             "body uses. Every extra demand turns callers away for nothing. Later in this lesson, a where clause asks "
             "for two things at once, and T : Any keeps null out of the box.",
    "moral": "So, why can't a plain T tell you its weight? Because the compiler doesn't know your callers. It only knows "
             "the label. Put a sign on the label, and the body may use what the sign promises.",
    "check": "Quick check. maxOf2 of 1, and the string a. Both are comparable. Does it compile?",
    "check_a": "No. One T can't be an Int and a String at once: actual type is String, but Int was expected.",
}


def hammer(s=1.0):
    handle = Rectangle(width=0.14, height=0.9).set_stroke(GREY_B, 2).set_fill("#6B4A2B", 1)
    head = Rectangle(width=0.6, height=0.22).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).next_to(handle, UP, buff=0)
    return VGroup(handle, head).scale(s)


def till_roll(s=1.0):
    roll = Circle(radius=0.28).set_stroke(GREY_A, 2).set_fill("#DDDDDD", 1)
    core = Circle(radius=0.08).set_stroke(GREY_B, 2).set_fill(GREY_D, 1)
    tail = Rectangle(width=0.5, height=0.12).set_stroke(GREY_A, 1.5).set_fill("#DDDDDD", 1).next_to(roll, RIGHT, buff=-0.1).shift(DOWN * 0.2)
    return VGroup(tail, roll, core).scale(s)


def scales(s=1.0):
    base = RoundedRectangle(corner_radius=0.08, width=1.6, height=0.5).set_stroke(GREY_A, 2.5).set_fill("#1c1c1c", 1)
    post = Rectangle(width=0.14, height=0.35).set_stroke(GREY_A, 2).set_fill("#1c1c1c", 1).next_to(base, UP, buff=0)
    plate = RoundedRectangle(corner_radius=0.05, width=1.5, height=0.12).set_stroke(GREY_A, 2.5).set_fill("#2a2a2a", 1).next_to(post, UP, buff=0)
    disp = RoundedRectangle(corner_radius=0.04, width=0.9, height=0.3).set_stroke(OK, 1.5).set_fill(BLACK, 1).move_to(base)
    return VGroup(base, post, plate, disp).scale(s)


def sign_board(text, color=OK, size=24):
    t = T(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.4, height=t.height + 0.3).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


class Gen02Bounds(Narrated):
    """gen-02, section 1 (with the edge of section 0): the label with a blank from lesson 1; the shy question (why
    can't T tell me its weight?); a plain T can do only what Any? does (UnboundedDemo's output); lengthOf and bigger
    fail, the roundabout String.compareTo message; the 'fruit only' sign, mapped; heavier with T : Fruit and MaxDemo's
    output; why not two Fruit parameters (a cast comes back); T : Comparable<T>, maxOf2; two apples have no order;
    where the sign breaks; the name; the guardrail; moral; a check."""

    def construct(self):
        self.title_card("Bounds", "a sign on the box: fruit only")

        # ================= callback: the label with a blank =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        big = crate(3.4, 2.2, ["Box of ________"], 26).move_to([1.6, FL + 1.1, 0])
        dr = door(2.8, 1.4).move_to([-2.4, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-0.95, FL + 0.7, 0])
        callers = VGroup(vchip('"Gala"', APPLE, 24), vchip("180", NUM, 24), vchip("null", GREY_B, 24))
        callers.arrange(DOWN, buff=0.25).move_to([-5.3, 0.1, 0])
        anyc = T("any caller, any type", 24, GREY_A).next_to(callers, UP, buff=0.3)
        self.say("open")
        self.play(Create(floor), FadeIn(big), Create(dr), FadeIn(clerk), run_time=0.9)
        self.at(1)
        self.play(Indicate(big[3], color=WHITE, scale_factor=1.08), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in callers], lag_ratio=0.3), FadeIn(anyc), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("I only ever pass fruit to my function.", 34, GREY_A)
        q2 = T("So why can't my generic code ask a T for its weight?", 34)
        q3 = T("Can't the compiler see my callers?", 34, YELLOW_M)
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

        # ================= a plain T: only what Any? can do =================
        jd = code_block(["static <T> String describe(T x) {",
                         "    return \"value=\" + x + \", hash=\"",
                         "        + Objects.hashCode(x);", "}"], 22)
        kd = code_block(["fun <T> describe(x: T): String =",
                         "    \"value=$x, hash=${x.hashCode()}\""], 22)
        fit(jd, 6.0)
        fit(kd, 6.0)
        jg = titled(jd, "Java").move_to([-3.3, 2.0, 0])
        kg = titled(kd, "Kotlin").move_to([3.3, 2.0, 0]).align_to(jg, UP)
        out = term(["value=Gala, hash=2211823", "value=180, hash=180", "value=null, hash=0"], 22, "UnboundedDemo, real output")
        out.move_to([-3.0, -1.2, 0])
        self.say("plain")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(part(kd[1], "${x.hashCode()}"), color=WHITE, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in out[1]], lag_ratio=0.35), run_time=1.2)
        self.hold()

        fence = RoundedRectangle(corner_radius=0.2, width=5.4, height=2.6).set_stroke(GREY_A, 2.5).set_fill(dim(GREY_A, 0.06), 1)
        fence.move_to([3.4, -1.25, 0])
        fl = M("Any?", 28, WHITE).move_to(fence.get_top() + DOWN * 0.35)
        fl2 = T("every value, null included", 20, GREY_B).next_to(fl, DOWN, buff=0.08)
        inside = VGroup(vchip('"Gala"', APPLE, 22), vchip("180", NUM, 22), vchip("null", GREY_B, 22)).arrange(RIGHT, buff=0.3)
        inside.move_to(fence.get_center() + DOWN * 0.45)
        can = VGroup(M("toString", 20, GREY_A), M("hashCode", 20, GREY_A), M("==", 20, GREY_A)).arrange(RIGHT, buff=0.4)
        can.next_to(inside, DOWN, buff=0.25)
        self.say("plain2")
        self.play(Create(fence), run_time=0.6)
        self.play(FadeIn(can, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(fl), FadeIn(fl2), LaggedStart(*[FadeIn(c) for c in inside], lag_ratio=0.2), run_time=0.9)
        self.at(2)
        self.play(Indicate(fl, color=WHITE, scale_factor=1.2), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= lengthOf and bigger fail =================
        kl = M("fun <T> lengthOf(x: T) = x.length", 28, WHITE).move_to([0, 2.3, 0])
        jl = M("static <T> int lengthOf(T x) { return x.length(); }", 22, GREY_A).next_to(kl, DOWN, buff=0.3)
        jl_t = T("Java", 20, GREY_B).next_to(jl, LEFT, buff=0.25)
        kl_t = T("Kotlin", 20, GREY_B).next_to(kl, LEFT, buff=0.25)
        callers = T("every caller in mind passes a String", 24, GREY_B).move_to([0, 0.6, 0])
        self.say("length_q")
        self.play(FadeIn(kl, shift=UP * 0.1), FadeIn(kl_t), run_time=0.7)
        self.play(FadeIn(jl, shift=UP * 0.1), FadeIn(jl_t), run_time=0.5)
        self.at(2)
        self.play(FadeIn(callers), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        e1 = VGroup(T("Kotlin", 20, GREY_B), err_line("unresolved reference 'length'.", 22)).arrange(RIGHT, buff=0.25)
        e2 = VGroup(T("Java", 20, GREY_B), err_line("cannot find symbol: method length()", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(e1, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -0.4, 0])
        c42 = M("lengthOf(42)", 26, NUM)
        noLen = T("an Int has no length", 24, BAD)
        cg = VGroup(c42, noLen).arrange(RIGHT, buff=0.4).move_to([0, -1.7, 0])
        rule = T("a generic function may only use what every allowed T shares", 26, WHITE).move_to([0, -2.8, 0])
        fit(rule, 12.4)
        self.say("length")
        self.play(FadeOut(callers), FadeIn(eg, shift=UP * 0.1), Indicate(part(kl, "x.length"), color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        kb = M("fun <T> bigger(a: T, b: T): T = if (a > b) a else b", 24, WHITE).move_to([0, 2.2, 0])
        fit(kb, 12.4)
        eb = VGroup(err_line("candidate 'fun String.compareTo(other: String,", 22),
                    M("ignoreCase: Boolean = ...): Int' is inapplicable", 22, GREY_A),
                    M("because of a receiver type mismatch.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        eb[1].align_to(eb[0][1], LEFT)
        eb[2].align_to(eb[0][1], LEFT)
        fit(eb, 12.4).move_to([0, 0.6, 0])
        self.say("bigger")
        self.play(FadeIn(kb, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(part(kb, "a > b"), color=WHITE, scale_factor=1.2), FadeIn(eb, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(part(eb[0][1], "String.compareTo").animate.set_color(YELLOW_M), Circumscribe(part(eb[0][1], "String.compareTo"), color=YELLOW_M), run_time=1.0)
        self.hold()

        clerk = person(CLERK, 1.1).move_to([-4.2, -2.2, 0])
        you = person(BACK, 1.1).move_to([-5.6, -2.2, 0])
        b1 = paper(["a ripe apple, please"], 20).next_to(you, UP, buff=0.25)
        b1.align_to(you, LEFT).shift(LEFT * 0.3)
        b2 = paper(["the paper bags are", "the wrong shape"], 20).next_to(clerk, RIGHT, buff=0.3).shift(UP * 0.4)
        read = VGroup(T("read it as:", 24, GREY_B), T("this isn't defined for T", 26, YELLOW_M)).arrange(RIGHT, buff=0.2)
        read.move_to([2.6, -2.9, 0])
        self.say("bigger2")
        self.play(FadeIn(you), FadeIn(clerk), FadeIn(b1, shift=UP * 0.1), run_time=0.7)
        self.at_text("and hearing", lead=0.2)
        self.play(FadeIn(b2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(read, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the sign: fruit only =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-2.4, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-0.95, FL + 0.7, 0])
        big = crate(3.0, 1.8, None).move_to([1.6, FL + 0.9, 0])
        sb = sign_board("fruit only", OK, 28).next_to(big, UP, buff=0.25)
        sc = scales(1.1).move_to([5.0, FL + 0.48, 0])
        ham = hammer(0.9).move_to([-5.6, 0.2, 0])
        till = till_roll(1.0).move_to([-5.6, 0.2, 0])
        ap = apple(0.24).move_to([-5.6, 0.2, 0])
        lm = lemon(0.22).move_to([-5.6, 0.2, 0])
        self.say("sign")
        self.play(Create(floor), FadeIn(big), Create(dr), FadeIn(clerk), run_time=0.8)
        self.at(1)
        self.play(FadeIn(sb, shift=DOWN * 0.2), run_time=0.6)
        self.at(2)
        for item, dx in ((ham, -6.1), (till, -4.9)):
            self.play(FadeIn(item), run_time=0.25)
            self.play(item.animate.move_to([-3.0, 0.2, 0]), run_time=0.45)
            x = tick(False, 0.2).next_to(item, UP, buff=0.12)
            self.play(FadeIn(x), Indicate(clerk[0], color=CLERK, scale_factor=1.15), run_time=0.35)
            self.play(item.animate.move_to([dx, -1.1, 0]).scale(0.7), FadeOut(x), run_time=0.45)
        self.at(3)
        for item in (ap, lm):
            self.play(FadeIn(item), run_time=0.2)
            self.play(item.animate.move_to(big[0].get_center() + (LEFT if item is ap else RIGHT) * 0.5), run_time=0.8)
        self.at_text("straight on", lead=0.5)
        g = T("180 g", 18, OK).move_to(sc[3])
        self.play(ap.animate.move_to(sc[2].get_top() + UP * 0.26), run_time=0.8)
        self.play(FadeIn(g), run_time=0.3)
        self.hold()

        rows = [("the sign", "T : Fruit  (Java: T extends Fruit)"), ("the hammer at the door", "a caller the bound shuts out"),
                ("the scales", "the body, which may use .grams")]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), T(b, 24, WHITE)).arrange(RIGHT, buff=0.25) for a, b in rows])
        mp[0][2] = M("T : Fruit   (Java: T extends Fruit)", 22, OK)
        mp[0].arrange(RIGHT, buff=0.25)
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        bg = SurroundingRectangle(mp, buff=0.25, color=GREY_D, stroke_width=1.5, corner_radius=0.1).set_fill(BLACK, 0.92)
        mpg = VGroup(bg, mp).move_to([0, 2.45, 0])
        fit(mpg, 12.4)
        self.say("map")
        self.play(FadeOut(sb), FadeIn(bg), run_time=0.5)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(ham, color=BAD, scale_factor=1.3), run_time=0.7)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), Indicate(sc, color=OK, scale_factor=1.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= heavier with T : Fruit =================
        jc = code_block(["interface Fruit {", "    String name(); int grams();", "}",
                         "record Apple(String name, int grams)", "    implements Fruit {}",
                         "static <T extends Fruit>", "T heavier(T a, T b) {",
                         "    return a.grams() >= b.grams()", "        ? a : b;", "}"], 22)
        kc = code_block(["interface Fruit {", "    val name: String; val grams: Int", "}",
                         "data class Apple(", "    override val name: String,", "    override val grams: Int) : Fruit",
                         "fun <T : Fruit> heavier(a: T, b: T): T =",
                         "    if (a.grams >= b.grams) a else b"], 22)
        fit(jc, 6.1)
        fit(kc, 6.1)
        jg = titled(jc, "Java").move_to([-3.3, 1.0, 0])
        jg.align_to(UP * 3.3, UP)
        kg = titled(kc, "Kotlin").move_to([3.3, 1.0, 0]).align_to(jg, UP)
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Indicate(jc[0:3], color=WHITE, scale_factor=1.03), Indicate(kc[0:3], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(Indicate(jc[3:5], color=APPLE, scale_factor=1.03), Indicate(kc[3:6], color=APPLE, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(part(jc[5], "<T extends Fruit>").animate.set_color(OK), part(kc[6], "<T : Fruit>").animate.set_color(OK), run_time=0.6)
        self.at(4)
        self.play(part(jc[7], "a.grams()").animate.set_color(YELLOW_M), part(kc[7], "a.grams").animate.set_color(YELLOW_M), run_time=0.6)
        self.hold()

        out = term(["Apple(name=Gala, grams=180)"], 22, "MaxDemo, real output")
        call = M('heavier(Apple("Gala", 180), Apple("Fuji", 150))', 22, WHITE)
        call2 = M('heavier("Gala", "Fuji")', 22, WHITE)
        er = err_line("argument type mismatch: actual type is 'String', but 'Fruit' was expected.", 20)
        row1 = VGroup(call, out).arrange(RIGHT, buff=0.5)
        row2 = VGroup(call2, er).arrange(RIGHT, buff=0.4)
        rr = VGroup(row1, row2).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(rr, 12.6).move_to([0, -2.65, 0])
        self.say("run")
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out, shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(call2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(er, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= why a T at all? =================
        self.say("whyT_q")
        alt = M("fun heavier(a: Fruit, b: Fruit): Fruit", 28, GREY_A).move_to([0, 2.4, 0])
        self.play(FadeIn(alt, shift=UP * 0.1), run_time=0.7)
        self.hold()

        def flow(sig, out_mob, y):
            a1, a2 = apple(0.2), apple(0.2)
            ins = VGroup(a1, a2).arrange(RIGHT, buff=0.15)
            fn = mbox(sig, GREY_A, size=22)
            arr1 = Arrow(LEFT * 0.5, RIGHT * 0.5, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
            arr2 = arr1.copy()
            g = VGroup(ins, arr1, fn, arr2, out_mob).arrange(RIGHT, buff=0.25).move_to([0, y, 0])
            return g

        f1 = flow("heavier(Fruit, Fruit)", mbox("Fruit", GREY_A, size=24), 0.9)
        f2 = flow("heavier<T : Fruit>", mbox("Apple", APPLE, size=24), -1.3)
        fit(f1, 11.5)
        fit(f2, 11.5)
        f2.align_to(f1, LEFT)
        need = VGroup(M("as Apple", 24, BAD), T("a cast comes back", 22, BAD)).arrange(DOWN, buff=0.08).next_to(f1, DOWN, buff=0.15).align_to(f1[4], LEFT)
        good = VGroup(tick(True, 0.15), T("two apples in, an Apple out", 22, OK)).arrange(RIGHT, buff=0.15).next_to(f2, DOWN, buff=0.2).align_to(f2[4], RIGHT)
        self.say("whyT")
        self.play(FadeIn(f1[:3]), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(f1[3]), FadeIn(f1[4], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(need, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(f2), run_time=0.8)
        self.play(FadeIn(good), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= T : Comparable<T> =================
        jm = code_block(["static <T extends Comparable<T>>", "T maxOf2(T a, T b) {",
                         "    return a.compareTo(b) >= 0 ? a : b;", "}"], 22)
        km = code_block(["fun <T : Comparable<T>>", "maxOf2(a: T, b: T): T =",
                         "    if (a > b) a else b"], 22)
        fit(jm, 6.1)
        fit(km, 6.1)
        jg = titled(jm, "Java").move_to([-3.3, 2.2, 0])
        kg = titled(km, "Kotlin").move_to([3.3, 2.2, 0]).align_to(jg, UP)
        aloud = T("T is something that can be compared with another T", 28, OK).move_to([0, 0.35, 0])
        fit(aloud, 12.4)
        self.say("cmp")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(part(jm[0], "<T extends Comparable<T>>").animate.set_color(OK), part(km[0], "<T : Comparable<T>>").animate.set_color(OK), run_time=0.6)
        self.at(2)
        self.play(FadeIn(aloud, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(part(km[2], "a > b"), color=YELLOW_M, scale_factor=1.3), Indicate(part(jm[2], "a.compareTo(b)"), color=YELLOW_M, scale_factor=1.1), run_time=0.9)
        self.hold()

        r1 = VGroup(M("maxOf2(180, 150)", 24, WHITE), M("180", 24, NUM)).arrange(RIGHT, buff=0.5)
        r2 = VGroup(M('maxOf2("Gala", "Fuji")', 24, WHITE), M("Gala", 24, APPLE)).arrange(RIGHT, buff=0.5)
        rs = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-2.2, -1.2, 0])
        r1[1].next_to(r2[0], RIGHT, buff=0.5).match_y(r1[0])
        r2[1].next_to(r2[0], RIGHT, buff=0.5)
        rl = T("MaxDemo, real output", 20, GREY_B).next_to(rs, RIGHT, buff=0.6)
        self.say("cmp2")
        self.play(FadeIn(r1, shift=UP * 0.1), FadeIn(rl), run_time=0.6)
        self.at_text("And Gala", lead=0.3)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ca = M('maxOf2(Apple("Gala", 180), Apple("Fuji", 150))', 24, WHITE).move_to([0, -2.6, 0])
        fit(ca, 12.4)
        self.say("apples_q")
        self.play(FadeIn(ca, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.35), edge=RIGHT)
        self.play(FadeOut(VGroup(rs, rl, aloud)), ca.animate.move_to([0, 0.55, 0]), run_time=0.6)

        ea = VGroup(err_line("argument type mismatch: actual type is 'Apple',", 22),
                    M("but 'Comparable<uninferred T (of fun <T : Comparable<T>> maxOf2)>' was expected.", 22, GREY_A))
        ea.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        ea[1].align_to(ea[0][1], LEFT)
        fit(ea, 12.6).move_to([0, -0.4, 0])
        qs = VGroup(T("by weight?", 28, YELLOW_M), T("by name?", 28, YELLOW_M), T("by price?", 28, YELLOW_M)).arrange(RIGHT, buff=0.9)
        qs.move_to([0, -1.8, 0])
        aa = VGroup(apple(0.3), apple(0.3)).arrange(RIGHT, buff=0.5).move_to([0, -2.85, 0])
        self.say("apples")
        self.play(FadeIn(ea, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(aa), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qs[0], shift=UP * 0.1), run_time=0.4)
        self.at(3)
        self.play(FadeIn(qs[1], shift=UP * 0.1), run_time=0.4)
        self.at(4)
        self.play(FadeIn(qs[2], shift=UP * 0.1), run_time=0.4)
        self.at(5)
        self.play(Wiggle(aa), run_time=0.9)
        self.hold()
        self.wipe()

        o1 = VGroup(T("1.", 28, YELLOW_M), M("data class Apple(...) : Fruit, Comparable<Apple>", 24, WHITE)).arrange(RIGHT, buff=0.2)
        o1n = T("compare by weight: compareTo(other) = grams.compareTo(other.grams)", 22, GREY_A)
        o2 = VGroup(T("2.", 28, YELLOW_M), T("keep Apple plain, and pass a Comparator where you need an order", 28, WHITE)).arrange(RIGHT, buff=0.2)
        o2n = T("usually better", 22, OK)
        og = VGroup(o1, o1n, o2, o2n).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, 0.4, 0])
        o1n.shift(RIGHT * 0.45)
        o2n.shift(RIGHT * 0.45)
        fit(og, 12.4)
        self.say("apples2")
        self.at(1)
        self.play(FadeIn(o1, shift=UP * 0.1), FadeIn(o1n), run_time=0.7)
        self.at(2)
        self.play(FadeIn(o2, shift=UP * 0.1), FadeIn(o2n), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the sign picture breaks =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-1.0, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([0.45, FL + 0.7, 0])
        big = crate(3.0, 1.8, None).move_to([3.6, FL + 0.9, 0])
        sb = sign_board("fruit only", OK, 26).next_to(big, UP, buff=0.25)
        eyes = VGroup(T("a person looks at the item", 24, GREY_A)).move_to([-3.8, 2.3, 0])
        decl = VGroup(T("the compiler reads", 24, GREY_A), T("only what the type declares", 24, CLERK)).arrange(DOWN, buff=0.08).move_to([0.6, 2.4, 0])
        imp = paper(["has grams,", "but never says", "it's a Fruit"], 20).move_to([-4.2, 0.1, 0])
        self.say("breaks")
        self.play(Create(floor), Create(dr), FadeIn(clerk), FadeIn(big), FadeIn(sb), run_time=0.8)
        self.at(1)
        self.play(FadeIn(eyes), run_time=0.5)
        self.at(2)
        self.play(FadeIn(decl), run_time=0.5)
        self.at(3)
        self.play(FadeIn(imp, shift=RIGHT * 0.2), run_time=0.5)
        self.play(imp.animate.move_to([-2.7, 0.1, 0]), run_time=0.6)
        x = tick(False, 0.22).next_to(imp, UP, buff=0.12)
        self.play(FadeIn(x), Indicate(clerk[0], color=CLERK, scale_factor=1.2), run_time=0.5)
        self.play(imp.animate.move_to([-4.6, 0.1, 0]), FadeOut(x), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the name and the guardrail =================
        nm = VGroup(T("upper bound", 40, OK), T("T must be this type, or a subtype of it", 30)).arrange(DOWN, buff=0.25)
        nm2 = VGroup(M("T : Fruit", 30, WHITE), T("Kotlin", 22, GREY_B), M("T extends Fruit", 30, WHITE), T("Java", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        sub = T("subtype, for now: a class that inherits from it, like Apple from Fruit", 24, GREY_A)
        ng = VGroup(nm, nm2, sub).arrange(DOWN, buff=0.4).move_to([0, 0.6, 0])
        fit(ng, 12.4)
        self.say("name")
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(nm2, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        gq = T("A bound shuts some callers out, and lets the body do more.", 32).move_to([0, 2.2, 0])
        fit(gq, 12.4)
        gr = T("Ask for exactly what the body uses.", 34, YELLOW_M).move_to([0, 1.1, 0])
        more = VGroup(VGroup(M("where T : CharSequence, T : Comparable<T>", 24, WHITE), T("two at once", 24, GREY_A)).arrange(RIGHT, buff=0.4),
                      VGroup(M("T : Any", 24, WHITE), T("keeps null out of the box", 24, GREY_A)).arrange(RIGHT, buff=0.4))
        more.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -1.2, 0])
        later = T("later in this lesson", 22, GREY_B).next_to(more, UP, buff=0.3)
        self.say("guard")
        self.play(FadeIn(gq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(gr, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(later), FadeIn(more, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why can't a plain T tell you its weight?", 34)
        m1 = T("The compiler doesn't know your callers. It only knows the label.", 30, GREY_A)
        m2 = T("Put a sign on the label, and the body may use what it promises.", 30, OK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M('maxOf2(1, "a")', 30, WHITE), T("Does it compile?", 28)).arrange(RIGHT, buff=0.3)
        qc.move_to(DOWN * 0.5)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = err_line("... actual type is 'String', but 'Int' was expected.", 24)
        ansl = T("one T can't be an Int and a String at once", 26, BAD)
        ag = VGroup(ansl, ans).arrange(DOWN, buff=0.2).move_to(DOWN * 2.2)
        self.say("check_a")
        self.play(FadeIn(ansl, shift=UP * 0.1), run_time=0.5)
        self.at_text("actual type", lead=0.3)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
