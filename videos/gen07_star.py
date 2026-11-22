from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"<Any\?>", " of Any nullable"), (r"\bAny\?", "Any nullable"), (r"<\*>", " of star"), (r"<\?>", " of question mark"),
    (r"CapturedType\(\*\)", "captured type star"), (r"CAP#1", "cap one"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"\bMutableList\b", "mutable list"), (r"\bremoveAt\b", "remove at"), (r"\bisEmpty\b", "is empty"),
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



WORN = GREY_B


def worn_box(w=2.6, h=1.7, s=1.0):
    """A crate whose label wore off: crate [0..2], smudged label [3]."""
    c = crate(w, h, None)
    lab = Rectangle(width=1.5, height=0.62).set_stroke(GREY_D, 1.5).set_fill("#8C8676", 1).move_to(c[0].get_center() + DOWN * 0.1)
    smudge = VGroup(*[Line(LEFT * 0.5, RIGHT * 0.5, stroke_width=3, color="#6B6558").shift(UP * dy + RIGHT * dx)
                      for dy, dx in ((0.12, -0.05), (0.0, 0.08), (-0.13, -0.1))]).move_to(lab)
    q = T("?", 30, "#3A362E").move_to(lab)
    c.add(VGroup(lab, smudge, q))
    return c.scale(s)


def drawer(s=1.0):
    """The drawer of odds and ends: front [0], knob [1], label [2]."""
    front = RoundedRectangle(corner_radius=0.08, width=3.0, height=1.2).set_stroke(GREY_A, 3).set_fill("#2a2520", 1)
    knob = Circle(radius=0.1).set_stroke(GREY_A, 2).set_fill(GREY_B, 1).move_to(front.get_center() + DOWN * 0.25)
    lab = paper(["anything"], 20).move_to(front.get_center() + UP * 0.22)
    return VGroup(front, knob, lab).scale(s)


def sticker(text, color=OK, size=22, mono=False):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.36, height=t.height + 0.26).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def pencil(s=1.0):
    body = Rectangle(width=1.0, height=0.14).set_stroke(GREY_B, 1.5).set_fill("#C9A227", 1)
    tip = Polygon(body.get_right() + UP * 0.07, body.get_right() + DOWN * 0.07, body.get_right() + RIGHT * 0.22).set_stroke(GREY_B, 1.5).set_fill("#E8D3A0", 1)
    return VGroup(body, tip).scale(s)


def rain(n=14, x0=-6.0, x1=-1.0, y0=0.5, y1=3.2):
    import random
    rnd = random.Random(7)
    return VGroup(*[Line(UP * 0.18, ORIGIN, stroke_width=2.5, color=BLUE_D).move_to([rnd.uniform(x0, x1), rnd.uniform(y0, y1), 0]) for _ in range(n)])


# every spoken line, in order
N = {
    "open": "Most boxes in the storeroom still have their labels. Box of apples, box of lemons: the clerk at the door "
            "read every one. But one box sat by the back door through a wet week, and its label wore off.",
    "open2": "You can see that everything inside is the same kind of thing. You just can't see which kind.",
    "can": "So what can you safely do with it? Take something out and look at it, as some thing. Count what's inside. "
           "Empty it. What you can't do is put anything in. Whatever you drop might be the wrong kind: the lemon in the "
           "crate of apples, the other way round.",
    "shyq": "Here's a question that's easy to be shy about. If I don't know the element type, why not just write "
            "MutableList<Any?>, the type that covers every value? Isn't that the same as saying, I don't know?",
    "log": "Let's start with a job where the type really doesn't matter. The shop keeps a daily log, and one helper "
           "prints lists into it: a list of variety names, a list of weights, a list of apples. It never needs to know "
           "what the elements are.",
    "code": "Kotlin's way to say that is a star, in place of the type argument: List<*>. Java writes a question mark: "
            "List<?>. Each item comes out as Kotlin's Any?, or Java's Object. And the demo prints all five: Gala, Fuji, "
            "180, 150, 120.",
    "map": "Let's map it. The worn box is the list. The worn-off label is the star. The one kind of thing inside is the "
           "list's real element type, which is still there: you've only lost the label. And taking something out to look "
           "at it is a read, which gives you Any?.",
    "predict_q": "Now the interesting part. Take the list of names, and look at it through a MutableList<*>. Three lines: "
                 "add the string Eureka, add null, clear the list. Which of them compile? Pause and guess.",
    "predict": "Only clear. Adding Eureka fails: the receiver type contains star projection, which prohibits add. The list "
               "might really be the weights, and no string may go into a list of numbers.",
    "nullq": "And null? Refused too: null cannot be a value of a non-null type, CapturedType(*). The unknown type might be "
             "one that never holds null. Null gets in almost everywhere. Not here.",
    "capt": "CapturedType(*) is the compiler's placeholder for the one real element type of this list. It's a name for "
            "the label nobody can read.",
    "java": "Java is more relaxed about one of these. On a List<?>, add null compiles, because every Java reference type "
            "allows null. The Java demo prints a list holding null. Adding the string Eureka fails in Java too: String "
            "cannot be converted to CAP#1.",
    "empty": "Everything that doesn't take an element still works: size, isEmpty, removeAt, clear. So one function can "
             "empty any crate. The demo empties a list of names and a list of weights, and prints: first is Gala, "
             "emptied 2 names and 3 weights.",
    "drawer": "Now back to the shy question. Why not MutableList<Any?>? Let's be fair to it. It's a perfectly real type: "
              "the shop's drawer of odds and ends. A pencil, a number, nothing in particular. You can put anything at "
              "all into it.",
    "break": "So hand a function that takes a MutableList<Any?> our list of names. Kotlin says: argument type mismatch. "
             "Actual type is MutableList<String>, but MutableList<Any?> was expected.",
    "break2": "Think about why. A drawer that takes anything would let that function add a price tag to our list of names. "
              "So the type that looks the most generous is the fussiest: it only takes a list that really is a list of "
              "anything. The worn box is the opposite. Nothing may go in, so every list fits.",
    "name": "Now the name. A star in place of a type argument is called a star projection. And Java calls its question "
            "mark an unbounded wildcard: a wildcard with no extends and no super after it.",
    "breaks": "Here the worn label picture breaks. In the storeroom, you could open the box, look at one apple, and know "
              "what the whole box holds. A program can't. An empty list, or one that starts with an apple, says nothing "
              "about the rest. The star just means: not known.",
    "guard": "So, the guardrail. If a function doesn't care about the element type, say so with a star. It may take items "
             "out, and put nothing in. Write MutableList<Any?> only when the function really stores arbitrary values.",
    "moral": "So, is a list of anything the same as a list of I don't know? No. The drawer says what it holds, anything at "
             "all, so anything may go in. The worn box holds one kind of thing that nobody remembers, so nothing goes in.",
    "check": "Quick check. unlabeled is a MutableList<*>. Does unlabeled dot removeAt of zero compile?",
    "check_a": "Yes. removeAt takes an index, not an element. A star projection locks what goes in, not whether the crate "
               "can change.",
}


class Gen07StarProjection(Narrated):
    """gen-07, section 0 (with the drawer from section 2): the box whose label wore off; what you may do with it; the
    shy question (why not MutableList<Any?>?); the daily log and printAll with List<*> and List<?>, real output; the
    map; predict add("Eureka"), add(null), clear(); the errors and CapturedType(*); Java lets null in; empty() and its
    real output; the drawer of odds and ends, fair to it, then the mismatch; the name, star projection and unbounded
    wildcard; where the picture breaks; the guardrail; moral; a check."""

    def construct(self):
        self.title_card("Star projection", "a box whose label wore off")

        # ================= the worn box =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        b1 = crate(2.0, 1.3, ["apples"], 20).move_to([2.2, FL + 0.65, 0])
        b2 = crate(2.0, 1.3, ["lemons"], 20).move_to([4.7, FL + 0.65, 0])
        dr = door(2.8, 1.4).move_to([-5.2, FL + 1.4, 0])
        dl = T("back door", 22, GREY_B).next_to(dr, UP, buff=0.15)
        wb = worn_box(2.4, 1.6).move_to([-2.2, FL + 0.8, 0])
        fresh = paper(["Box of apples"], 20).move_to(wb[0].get_center() + DOWN * 0.1)
        drops = rain()
        self.say("open")
        self.play(Create(floor), FadeIn(b1), FadeIn(b2), run_time=0.7)
        self.at(1)
        self.play(Indicate(b1[3], color=WHITE, scale_factor=1.1), Indicate(b2[3], color=WHITE, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(Create(dr), FadeIn(dl), FadeIn(wb[:3]), FadeIn(fresh), run_time=0.7)
        self.play(FadeIn(drops, lag_ratio=0.1), run_time=1.0)
        self.play(drops.animate.shift(DOWN * 0.6).set_opacity(0), ReplacementTransform(fresh, wb[3]), run_time=1.4)
        self.hold()

        inside = VGroup(*[Circle(radius=0.17).set_stroke(GREY_A, 2).set_fill(GREY_D, 1) for _ in range(3)]).arrange(RIGHT, buff=0.1)
        inside.move_to(wb[0].get_top() + UP * 0.08)
        same = T("all the same kind", 24, GREY_A).move_to([-2.2, 1.4, 0])
        which = T("but which kind?", 26, YELLOW_M).next_to(same, DOWN, buff=0.15)
        self.say("open2")
        self.play(FadeIn(inside), FadeIn(same), run_time=0.7)
        self.at(1)
        self.play(FadeIn(which), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(b1, b2, same, which)), run_time=0.5)

        rows = VGroup(
            VGroup(tick(True, 0.15), T("take one out, look at it as some thing", 26)),
            VGroup(tick(True, 0.15), T("count what's inside", 26)),
            VGroup(tick(True, 0.15), T("empty it", 26)),
            VGroup(tick(False, 0.15), T("put anything in", 26, BAD)),
        )
        for r in rows:
            r.arrange(RIGHT, buff=0.2)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([3.4, 0.9, 0])
        fit(rows, 6.4)
        rows.move_to([3.2, 0.9, 0])
        some = vchip("some thing", GREY_B, 22).move_to(inside[0])
        self.say("can")
        self.at(1)
        self.play(FadeIn(rows[0]), inside[0].animate.move_to([-2.2, 1.6, 0]), run_time=0.7)
        self.play(FadeIn(some.move_to([-2.2, 2.3, 0])), run_time=0.4)
        self.at(2)
        cnt = T("3", 30, NUM).next_to(wb, RIGHT, buff=0.25)
        self.play(FadeIn(rows[1]), FadeIn(cnt), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[2]), FadeOut(inside[1:]), FadeOut(inside[0]), FadeOut(some), FadeOut(cnt), run_time=0.6)
        self.at(4)
        lm = lemon(0.22).move_to([-0.2, 1.4, 0])
        self.play(FadeIn(rows[3]), FadeIn(lm), run_time=0.5)
        self.play(lm.animate.move_to(wb[0].get_top() + UP * 0.35), run_time=0.6)
        x = tick(False, 0.2).next_to(lm, UP, buff=0.12)
        self.play(FadeIn(x), run_time=0.3)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("If I don't know the element type,", 34, GREY_A)
        q2 = VGroup(T("why not just write", 34), M("MutableList<Any?>", 34, YELLOW_M), T("?", 34)).arrange(RIGHT, buff=0.2)
        q3 = T("Isn't that the same as saying \"I don't know\"?", 34, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.38).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at_text("why not", lead=0.2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= the daily log =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        hp = who(BACK, "helper", 1.1, 22).move_to([-0.6, FL + 0.75, 0])
        book = paper(["daily log", "-----------", "", "", ""], 20).move_to([3.4, 0.0, 0])
        lists = VGroup(vchip('List<String>', APPLE, 22), vchip("List<Int>", NUM, 22), vchip("List<Apple>", APPLE, 22))
        lists.arrange(DOWN, buff=0.3).move_to([-4.6, 0.6, 0])
        dc = T("doesn't care what's inside", 24, GREY_A).next_to(hp, UP, buff=0.35)
        self.say("log")
        self.play(Create(floor), FadeIn(hp), run_time=0.6)
        self.at(1)
        self.play(FadeIn(book), run_time=0.5)
        self.at_text("a list of variety", lead=0.3)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in lists], lag_ratio=0.5), run_time=1.6)
        self.at(2)
        self.play(FadeIn(dc, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        jc = code_block(["static void printAll(List<?> items) {",
                         "    for (Object item : items)",
                         '        System.out.println("  " + item);', "}"], 22)
        kc = code_block(["fun printAll(items: List<*>) {",
                         '    for (item in items) println("  $item")', "}"], 22)
        fit(jc, 6.1)
        fit(kc, 6.1)
        jg = titled(jc, "Java").move_to([-3.3, 2.0, 0])
        kg = titled(kc, "Kotlin").move_to([3.3, 2.0, 0]).align_to(jg, UP)
        tk = VGroup(M("Any?", 26, WORN), T("Kotlin", 20, GREY_B)).arrange(DOWN, buff=0.08).next_to(kg, DOWN, buff=0.35)
        tj = VGroup(M("Object", 26, WORN), T("Java", 20, GREY_B)).arrange(DOWN, buff=0.08).next_to(jg, DOWN, buff=0.35)
        out = term(["  Gala", "  Fuji", "  180", "  150", "  120"], 22, "StarListDemo, real output").move_to([0, -2.0, 0])
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.6)
        self.play(part(kc[0], "List<*>").animate.set_color(YELLOW_M), run_time=0.5)
        self.at(1)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.6)
        self.play(part(jc[0], "List<?>").animate.set_color(YELLOW_M), run_time=0.5)
        self.at(2)
        self.play(FadeIn(tk), FadeIn(tj), run_time=0.6)
        self.at(3)
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in out[1]], lag_ratio=0.35), run_time=1.6)
        self.hold()
        self.wipe()

        # ================= the map =================
        wb = worn_box(2.2, 1.5).move_to([-4.6, 0.4, 0])
        rows = [("the worn box", "the list"), ("the worn-off label", "the star: List<*>"),
                ("one kind of thing inside", "the real element type, still there"), ("take one out and look", "a read: Any?")]
        mp = VGroup(*[VGroup(T(a, 26, GREY_A), M("->", 22, GREY_B), T(b, 26, WHITE)).arrange(RIGHT, buff=0.25) for a, b in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(mp, 8.2).move_to([2.2, 0.4, 0])
        self.say("map")
        self.play(FadeIn(wb), run_time=0.5)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(wb[3], color=WHITE, scale_factor=1.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= predict: add, add null, clear =================
        hd = M("val unlabeled: MutableList<*> = varieties", 26, WHITE).move_to([0, 2.8, 0])
        part(hd, "MutableList<*>").set_color(YELLOW_M)
        lines = VGroup(M('unlabeled.add("Eureka")', 28, WHITE), M("unlabeled.add(null)", 28, WHITE), M("unlabeled.clear()", 28, WHITE))
        lines.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([-2.6, 1.0, 0])
        nums = VGroup(*[T(f"{i}.", 26, GREY_B).next_to(l, LEFT, buff=0.25) for i, l in enumerate(lines, 1)])
        self.say("predict_q")
        self.at(1)
        self.play(FadeIn(hd, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(VGroup(n, l), shift=RIGHT * 0.1) for n, l in zip(nums, lines)], lag_ratio=0.5), run_time=1.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        marks = [cross_by(lines[0]), cross_by(lines[1]), check_by(lines[2])]
        e1 = VGroup(err_line("receiver type 'MutableList<*>' contains star projection which prohibits", 22),
                    M("the use of 'fun add(element: E): Boolean'.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        e1[1].align_to(e1[0][1], LEFT)
        fit(e1, 12.4).move_to([0, -1.3, 0])
        wts = VGroup(T("might really be", 24, GREY_A), vchip("[180, 150, 120]", NUM, 22)).arrange(RIGHT, buff=0.25).move_to([0, -2.6, 0])
        self.say("predict")
        self.play(FadeIn(marks[2]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(marks[0]), FadeIn(e1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(wts, shift=UP * 0.1), run_time=0.5)
        self.hold()

        e2 = err_line("null cannot be a value of a non-null type 'CapturedType(*)'.", 24)
        fit(e2, 12.4).move_to([0, -1.3, 0])
        nn = T("null gets in almost everywhere. Not here.", 26, YELLOW_M).move_to([0, -2.6, 0])
        self.say("nullq")
        self.play(FadeOut(e1), FadeOut(wts), FadeIn(marks[1]), run_time=0.5)
        self.play(FadeIn(e2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(nn, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(nn), run_time=0.4)

        tag = sticker("CapturedType(*)", WORN, 26, mono=True).move_to([0, -2.7, 0])
        tl = T("the one real element type, whose label nobody can read", 24, GREY_A).next_to(tag, DOWN, buff=0.15)
        self.say("capt")
        self.play(Indicate(part(e2[1], "CapturedType(*)"), color=WHITE, scale_factor=1.1), FadeIn(tag, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(tl), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= Java lets null in =================
        jl = VGroup(M("List<?> unlabeled = varieties;", 26, WHITE),
                    VGroup(M("unlabeled.add(null);", 26, WHITE), tick(True, 0.15), T("compiles in Java", 22, OK)).arrange(RIGHT, buff=0.25),
                    VGroup(M('unlabeled.add("Eureka");', 26, WHITE), tick(False, 0.15)).arrange(RIGHT, buff=0.25))
        jl.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        jlg = titled(jl, "Java").move_to([0, 1.6, 0])
        out = term(["after add(null): [null]"], 24, "StarListDemoJava, real output").move_to([-2.6, -1.4, 0])
        ej = err_line("String cannot be converted to CAP#1", 24).move_to([0, -2.9, 0])
        self.say("java")
        self.play(FadeIn(jlg[0]), FadeIn(jl[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(jl[1], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(jl[2], shift=RIGHT * 0.1), FadeIn(ej, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= what still works: empty any crate =================
        ok = VGroup(*[VGroup(M(t, 26, WHITE), tick(True, 0.13)).arrange(RIGHT, buff=0.15) for t in ("size", "isEmpty()", "removeAt(0)", "clear()")])
        ok.arrange(RIGHT, buff=0.6).move_to([0, 2.9, 0])
        fit(ok, 12.4)
        jc = code_block(["static int empty(List<?> crate) {", "    int n = crate.size();", "    crate.clear();", "    return n;", "}"], 22)
        kc = code_block(["fun empty(crate: MutableList<*>): Int {", "    val n = crate.size", "    crate.clear()", "    return n", "}"], 22)
        fit(jc, 6.1)
        fit(kc, 6.1)
        jg = titled(jc, "Java").move_to([-3.3, 0.6, 0])
        kg = titled(kc, "Kotlin").move_to([3.3, 0.6, 0]).align_to(jg, UP)
        out = term(["first = Gala, emptied 2 names and 3 weights"], 24, "StarListDemo, real output").move_to([0, -2.6, 0])
        self.say("empty")
        self.play(LaggedStart(*[FadeIn(o) for o in ok], lag_ratio=0.3), run_time=1.2)
        self.at(1)
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the drawer: fair to Any? =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dw = drawer(1.0).move_to([-3.2, FL + 1.4, 0])
        legs = VGroup(Line(dw[0].get_corner(DL), dw[0].get_corner(DL) + DOWN * 0.8, stroke_width=4, color=GREY_A),
                      Line(dw[0].get_corner(DR), dw[0].get_corner(DR) + DOWN * 0.8, stroke_width=4, color=GREY_A))
        dl = M("MutableList<Any?>", 26, WHITE).next_to(dw, UP, buff=1.0)
        things = VGroup(pencil(0.8), vchip("3", NUM, 22), vchip("null", GREY_B, 22)).arrange(RIGHT, buff=0.35).move_to([2.6, 1.0, 0])
        self.say("drawer")
        self.play(Create(floor), run_time=0.4)
        self.at(2)
        self.play(FadeIn(dw), Create(legs), FadeIn(dl), run_time=0.7)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in things], lag_ratio=0.4), run_time=1.2)
        self.at(4)
        for t in things:
            self.play(t.animate.move_to(dw[0].get_top() + UP * 0.2 + RIGHT * (things.submobjects.index(t) - 1) * 0.7).scale(0.8), run_time=0.45)
        self.hold()
        self.wipe()

        kc = code_block(['fun addPriceTag(list: MutableList<Any?>) { list.add("price tag") }',
                         "addPriceTag(drawer)       // fine",
                         "addPriceTag(varieties)    // a MutableList<String>"], 22)
        jc = code_block(['static void addPriceTag(List<Object> list) { list.add("price tag"); }',
                         "addPriceTag(varieties);   // a List<String>"], 22)
        fit(kc, 12.4)
        fit(jc, 12.4)
        kg = titled(kc, "Kotlin").move_to([0, 2.5, 0])
        jg = titled(jc, "Java").next_to(kg, DOWN, buff=0.45).align_to(kg, LEFT)
        ek = VGroup(err_line("argument type mismatch: actual type is 'MutableList<String>',", 22),
                    M("but 'MutableList<Any?>' was expected.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        ek[1].align_to(ek[0][1], LEFT)
        ej = VGroup(T("Java", 20, GREY_B), err_line("List<String> cannot be converted to List<Object>", 22)).arrange(RIGHT, buff=0.25)
        es = VGroup(ek, ej).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(es, 12.4).move_to([0, -1.5, 0])
        self.say("break")
        self.play(FadeIn(kg, shift=UP * 0.1), FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(part(kc[2], "addPriceTag(varieties)").animate.set_color(BAD), part(jc[1], "addPriceTag(varieties);").animate.set_color(BAD), FadeIn(es, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dw = drawer(0.9).move_to([-3.4, FL + 0.8, 0])
        wb = worn_box(2.4, 1.5).move_to([3.4, FL + 0.75, 0])
        dh = VGroup(T("the drawer", 26, WHITE), M("MutableList<Any?>", 24, GREY_A)).arrange(DOWN, buff=0.1).move_to([-3.4, 2.7, 0])
        wh = VGroup(T("the worn box", 26, WHITE), M("MutableList<*>", 24, YELLOW_M)).arrange(DOWN, buff=0.1).move_to([3.4, 2.7, 0])
        d1 = VGroup(tick(True, 0.13), T("anything may go in", 22, OK)).arrange(RIGHT, buff=0.12)
        d2 = VGroup(tick(False, 0.13), T("takes only a real list of anything", 22, BAD)).arrange(RIGHT, buff=0.12)
        dd = VGroup(d1, d2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(dh, DOWN, buff=0.3)
        w1 = VGroup(tick(False, 0.13), T("nothing may go in", 22, BAD)).arrange(RIGHT, buff=0.12)
        w2 = VGroup(tick(True, 0.13), T("every list fits", 22, OK)).arrange(RIGHT, buff=0.12)
        ww = VGroup(w1, w2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(wh, DOWN, buff=0.3)
        tagc = vchip('"price tag"', GREY_B, 22).move_to([-0.2, 0.9, 0])
        names = vchip('["Gala", "Fuji"]', APPLE, 22).move_to([-0.2, -0.1, 0])
        self.say("break2")
        self.play(Create(floor), FadeIn(dw), FadeIn(dh), run_time=0.6)
        self.at(1)
        self.play(FadeIn(names), FadeIn(tagc), run_time=0.5)
        self.play(tagc.animate.next_to(names, RIGHT, buff=0.1), run_time=0.7)
        xx = tick(False, 0.2).next_to(names, UP, buff=0.15)
        self.play(FadeIn(xx), run_time=0.3)
        self.at(2)
        self.play(FadeOut(VGroup(tagc, names, xx)), FadeIn(dd, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(wb), FadeIn(wh), run_time=0.6)
        self.at(4)
        self.play(FadeIn(ww, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the name =================
        n1 = VGroup(T("star projection", 44, YELLOW_M), T("a * in place of a type argument", 28)).arrange(DOWN, buff=0.2)
        n2 = VGroup(T("unbounded wildcard", 36, GREY_A), T("Java's ? with no extends and no super after it", 26)).arrange(DOWN, buff=0.2)
        pair = VGroup(M("List<*>", 30, WHITE), T("Kotlin", 22, GREY_B), M("List<?>", 30, WHITE), T("Java", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        ng = VGroup(n1, n2, pair).arrange(DOWN, buff=0.5).move_to([0, 0.4, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), FadeIn(pair), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        wb = worn_box(2.4, 1.5).move_to([-3.6, FL + 0.75, 0])
        one = apple(0.26).move_to(wb[0].get_top() + UP * 0.1)
        eye = T("look at one apple, and you know the whole box", 24, GREY_A).move_to([-2.6, 1.7, 0])
        fit(eye, 6.6)
        l1 = vchip("[ ]", GREY_B, 24)
        l2 = vchip("[Gala, ...?]", APPLE, 24)
        ls = VGroup(l1, l2).arrange(DOWN, buff=0.4).move_to([3.4, -0.3, 0])
        cant = T("a program can't tell the rest", 24, BAD).next_to(ls, UP, buff=0.4)
        self.say("breaks")
        self.play(Create(floor), FadeIn(wb), run_time=0.6)
        self.at(1)
        self.play(FadeIn(one), run_time=0.3)
        self.play(one.animate.shift(UP * 1.0), FadeIn(eye), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cant), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ls, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the guardrail =================
        g1 = VGroup(T("doesn't care about the element type?", 28, GREY_A), M("List<*>", 30, YELLOW_M), T("or", 26, GREY_B), M("MutableList<*>", 30, YELLOW_M)).arrange(RIGHT, buff=0.25)
        g2 = VGroup(tick(True, 0.15), T("take items out", 26), tick(False, 0.15), T("put nothing in", 26)).arrange(RIGHT, buff=0.25)
        g3 = VGroup(M("MutableList<Any?>", 30, WHITE), T("only when it really stores arbitrary values", 28, GREY_A)).arrange(RIGHT, buff=0.3)
        gg = VGroup(g1, g2, g3).arrange(DOWN, buff=0.6).move_to([0, 0.6, 0])
        for g in gg:
            fit(g, 12.4)
        self.say("guard")
        self.at(1)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(g3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Is a list of anything the same as a list of I-don't-know?", 32)
        m1 = T("No. The drawer says what it holds, so anything may go in.", 28, GREY_A)
        m2 = T("The worn box holds one kind nobody remembers, so nothing goes in.", 28, YELLOW_M)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("unlabeled.removeAt(0)", 30, WHITE), T("on a", 28), M("MutableList<*>", 30, YELLOW_M), T("?", 28)).arrange(RIGHT, buff=0.2)
        fit(qc, 12.4).move_to(DOWN * 0.4)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(tick(True, 0.16), T("Yes: it takes an index, not an element.", 28, OK)).arrange(RIGHT, buff=0.2).move_to(DOWN * 1.8)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
