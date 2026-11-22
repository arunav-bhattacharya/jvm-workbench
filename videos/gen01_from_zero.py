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
    "open": "Picture the storeroom behind a small fruit shop. Boxes sit on the shelves, each with a label: Gala apples, "
            "lemons, paper bags. Someone in the back room fills them before the shop opens. The person at the counter "
            "trusts the labels.",
    "shyq": "Here's a question that's easy to be shy about. Why label a box at all? A box that takes anything sounds more flexible. In Kotlin, that box holds Any. In Java, Object. So what's wrong with it?",
    "morning": "Let's find out. One morning, the counter opens the box for today's apple, to write the sign. Inside, "
               "where a name should be, is the number 12. The back room wrote how many apples there were, not which kind.",
    "morning2": "Notice where things happened. The mistake was made in the back. It shows up at the counter.",
    "code": "Here it is in code. AnyBox holds a value of type Any. restock is the back room: it puts 12 in. signFor is the counter: it takes the value out, and casts it to a String. A cast tells the compiler: trust me. The real check waits until the program runs.",
    "predict": "So where does this program fail? On the line that puts 12 in, or at the counter? Pause and guess.",
    "show": "Here's what the lesson's AnyBoxDemo printed. restock returned, and nothing has failed yet. Then a "
            "ClassCastException, thrown in signFor, at line 13. That's the cast at the counter.",
    "show2": "The counter did nothing wrong, and the function with the bug isn't even in the trace. In a bigger program, that read could come hours later.",
    "joke": "If Any had an honest name, it would be called whatever. It says yes to everything, and leaves the bad news "
            "for whoever opens the box.",
    "joke2": "So the point is this. Any doesn't remove the check. It moves the check to the read, far from the bug. What "
             "we really want is a check at the storeroom door, on the line that puts the wrong thing in.",
    "label": "So let's print a label with a gap in it. Box of, and then a blank. The person who makes the box has no "
             "idea what will go in it. Whoever takes the box writes in the gap: apple names, say.",
    "clerk": "And at the storeroom door stands a clerk who reads every label. A name like Fuji fits, so it goes in. The "
             "number 12 doesn't match, so it's turned away, at the door.",
    "map": "Let's map it. The printed label is class Box, with T in angle brackets. The gap is the T. What you write in "
           "the gap is a real type, like String in Box<String>. And the clerk at the door is the compiler.",
    "fix": "Now give restock a Box<String>, and try the same move. The compiler stops it right there, on the line with "
           "the bug, before the program ever runs.",
    "fix2": "kotlinc, the Kotlin compiler, says: assignment type mismatch. Actual type is Int, but String was expected. "
            "And javac, the Java compiler, says: int cannot be converted to String.",
    "fix3": "The counter needs no cast any more. The value in a Box<String> is already a String, so signFor can't throw "
            "a ClassCastException.",
    "fill_q": "Here's a trick that predicts any call. The box gets a method, replace: put a new value in, get the old one back. We make two boxes: variety, holding Gala, and count, holding 12. Will count dot replace, with Fuji, compile? Pause and guess.",
    "fill": "Fill in the blank. count is a Box<Int>, so read every T in Box as Int. For this call, replace takes an Int, "
            "and gives back an Int. Fuji is a String, so it doesn't fit.",
    "fill2": "The compiler agrees: argument type mismatch. Actual type is String, but Int was expected. The same call on "
             "variety is fine, and the demo prints: variety was Gala, now Fuji.",
    "many": "So one class gives you many types: Box<String>, Box<Int>, Box<Apple>. To the compiler, they're as different as String and Int.",
    "fun": "Functions can have a blank too. In Kotlin, the T goes right after fun. In Java, before the return type. A list of apples goes in, and an apple or null comes out. No cast anywhere.",
    "name": "Now the names. T is called a type parameter: the blank on the label. The real type you write in, like String, is a type argument. A class or function with a blank is generic, and that's where this track's name comes from: generics.",
    "breaks": "The picture breaks in one place, and it matters later. A real label stays on the box. The compiler checks "
              "the label, and then tears it off. When the program runs, on the JVM, there is only one Box class, and "
              "the String part is gone.",
    "breaks2": "So our clerk is strict at the door, with one odd habit: every label goes in the bin before the shop opens. That's fine, because by then every box has been checked.",
    "guard": "Three rules. One: a cast like as String, on a value from Any, marks a box with no label. Two: don't widen a type to Any to feel flexible. Here, flexible means unchecked. Three: a plain T promises nothing, and the next lesson fixes that.",
    "moral": "So, why put a label on the box? Because a cast checks at the read, far from the bug. A type parameter puts "
             "the check at the write, on the very line that made the mistake.",
    "check": "Quick check. Someone writes the line on the screen: a Box<String>, filled with 42. Where do you hear about it?",
    "check_a": "Right on that line, before the program runs: initializer type mismatch, expected Box<String>, actual "
               "Box<Int>. The clerk read the label.",
}


class Gen01FromZero(Narrated):
    """gen-01, section 1 (with the problem of section 0): the storeroom box of Any; the 12 the back room put in where a
    name belongs; AnyBoxDemo's real output (the cast at the counter throws, signFor line 13); Any renamed 'whatever';
    the label with a gap, the clerk at the door, mapped; Box<String> stops the 12 at the write; fill in the blank to
    predict count.replace("Fuji"); one class, many types; firstOrNull; the names; the label torn off at run time;
    rules; moral; a check."""

    def construct(self):
        self.title_card("Generics from zero", "a label with a blank, filled in by each caller")

        # ================= the storeroom =================
        FL = -1.7
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        shelf = Line([-3.3, 0.55, 0], [3.3, 0.55, 0], stroke_width=4, color=GREY_B)
        bx = VGroup(crate(2.0, 1.4, ["Gala", "apples"], 20), crate(2.0, 1.4, ["lemons"], 20),
                    crate(2.0, 1.4, ["paper", "bags"], 20)).arrange(RIGHT, buff=0.3)
        bx.next_to(shelf, UP, buff=0)
        legs = VGroup(*[Line([x, 0.55, 0], [x, FL, 0], stroke_width=4, color=GREY_B) for x in (-3.1, 3.1)])
        back = who(BACK, "back room").move_to([-5.4, FL + 0.75, 0])
        counter = who(COUNTER, "counter").move_to([5.4, FL + 0.75, 0])
        self.say("open")
        self.play(Create(floor), Create(shelf), Create(legs), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in bx], lag_ratio=0.3), run_time=1.4)
        self.at(2)
        self.play(FadeIn(back, shift=RIGHT * 0.2), run_time=0.6)
        self.at(3)
        self.play(FadeIn(counter, shift=LEFT * 0.2), run_time=0.6)
        self.play(LaggedStart(*[Indicate(b[3], color=WHITE, scale_factor=1.1) for b in bx], lag_ratio=0.25), run_time=1.2)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("Why put a label on a box at all?", 38)
        q2 = T("A box that takes anything sounds more flexible.", 32, GREY_A)
        q3 = VGroup(T("Kotlin:", 30, GREY_B), M("Any", 32, BOX), T("   Java:", 30, GREY_B), M("Object", 32, BOX)).arrange(RIGHT, buff=0.2)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= one morning: a 12 where a name should be =================
        FL = -1.4
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        box = crate(2.6, 1.7, ["today's", "apple"], 22).move_to([0, FL + 0.85, 0])
        back = who(BACK, "back room").move_to([-4.6, FL + 0.75, 0])
        counter = who(COUNTER, "counter").move_to([4.6, FL + 0.75, 0])
        twelve = vchip("12", NUM, 30).move_to([-4.6, 1.6, 0])
        self.say("morning")
        self.play(Create(floor), FadeIn(box), FadeIn(back), FadeIn(counter), run_time=0.8)
        self.at(1)
        sign = paper(["Today's apple:", "  ?"], 22).move_to([4.6, 1.9, 0])
        self.play(FadeIn(sign, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        up = twelve.copy().move_to(box.get_top() + UP * 0.55)
        self.play(FadeIn(up, shift=UP * 0.5), Indicate(box[3], color=WHITE, scale_factor=1.05), run_time=0.8)
        self.at(3)
        self.play(Indicate(up, color=NUM, scale_factor=1.3), run_time=0.8)
        self.hold()

        made = T("the mistake is made here", 24, BAD).next_to(back, DOWN, buff=0.35)
        seen = T("it shows up here", 24, BAD).next_to(counter, DOWN, buff=0.35)
        trip = ArcBetweenPoints([-4.6, 1.15, 0], box.get_top() + UP * 0.2 + LEFT * 0.3, angle=-PI / 3, color=NUM, stroke_width=3)
        self.say("morning2")
        self.play(Create(trip), run_time=0.7)
        self.at(1)
        self.play(FadeIn(made, shift=UP * 0.1), Indicate(back[0], color=BACK, scale_factor=1.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(seen, shift=UP * 0.1), Indicate(counter[0], color=COUNTER, scale_factor=1.2), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the code: AnyBox, restock, signFor =================
        java = code_block(["class AnyBox { Object value; }", "",
                           "static void restock(AnyBox box) {", "    box.value = 12;", "}", "",
                           "static String signFor(AnyBox box) {", "    String variety = (String) box.value;",
                           "    return \"Today's apple: \" + variety;", "}"], 22)
        kt = code_block(["class AnyBox(var value: Any)", "",
                         "fun restock(box: AnyBox) {", "    box.value = 12", "}", "",
                         "fun signFor(box: AnyBox): String {", "    val variety = box.value as String",
                         "    return \"Today's apple: $variety\"", "}"], 22)
        fit(java, 6.0)
        fit(kt, 6.0)
        jg = titled(java, "Java").move_to([-3.3, 0.35, 0])
        kg = titled(kt, "Kotlin").move_to([3.3, 0.35, 0])
        kg.align_to(jg, UP)
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Indicate(java[0], color=BOX, scale_factor=1.04), Indicate(kt[0], color=BOX, scale_factor=1.04), run_time=0.8)
        self.at(2)
        rb_j = SurroundingRectangle(java[2:5], buff=0.1, color=BACK, stroke_width=2.5, corner_radius=0.06)
        rb_k = SurroundingRectangle(kt[2:5], buff=0.1, color=BACK, stroke_width=2.5, corner_radius=0.06)
        self.play(Create(rb_j), Create(rb_k), run_time=0.7)
        self.play(part(java[3], "12").animate.set_color(NUM), part(kt[3], "12").animate.set_color(NUM), run_time=0.4)
        self.at(3)
        rc_j = SurroundingRectangle(java[6:10], buff=0.1, color=COUNTER, stroke_width=2.5, corner_radius=0.06)
        rc_k = SurroundingRectangle(kt[6:10], buff=0.1, color=COUNTER, stroke_width=2.5, corner_radius=0.06)
        self.play(Create(rc_j), Create(rc_k), run_time=0.7)
        self.at(4)
        self.play(part(java[7], "(String)").animate.set_color(COUNTER), part(kt[7], "as String").animate.set_color(COUNTER),
                  run_time=0.5)
        self.at(5)
        self.play(Indicate(part(kt[7], "as String"), color=COUNTER, scale_factor=1.2),
                  Indicate(part(java[7], "(String)"), color=COUNTER, scale_factor=1.2), run_time=0.9)
        self.hold()

        self.say("predict")
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)
        self.wipe()

        # ================= the real output =================
        out = term(["restock() returned. Nothing has failed yet.",
                    "ClassCastException: class java.lang.Integer cannot be cast",
                    "    to class java.lang.String (...)",
                    "thrown in: ...AnyBoxDemoKt.signFor(AnyBoxDemo.kt:13)"], 22, "AnyBoxDemo, real output")
        fit(out, 12.4).move_to([0, 1.3, 0])
        lines = out[1]
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lines[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lines[1], shift=RIGHT * 0.1), FadeIn(lines[2], shift=RIGHT * 0.1),
                  part(lines[1], "ClassCastException").animate.set_color(BAD), run_time=0.7)
        self.at_text("thrown in", lead=0.3)
        self.play(FadeIn(lines[3], shift=RIGHT * 0.1), run_time=0.5)
        self.play(part(lines[3], "signFor(AnyBoxDemo.kt:13)").animate.set_color(COUNTER), run_time=0.5)
        self.hold()

        bug = VGroup(T("the bug:", 26, GREY_B), M("restock", 26, BACK), T("(not in the trace)", 26, GREY_B)).arrange(RIGHT, buff=0.2)
        blamed = VGroup(T("blamed:", 26, GREY_B), M("signFor", 26, COUNTER), T("(did nothing wrong)", 26, GREY_B)).arrange(RIGHT, buff=0.2)
        bg = VGroup(blamed, bug).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, -1.7, 0])
        self.say("show2")
        self.play(FadeIn(blamed, shift=UP * 0.1), run_time=0.6)
        self.at_text("the function with", lead=0.3)
        self.play(FadeIn(bug, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        later = T("hours later, another team's code", 24, GREY_A).move_to([0, -3.05, 0])
        self.play(FadeIn(later), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= light moment: Any, renamed =================
        anyw = M("Any", 64, BOX).move_to([-2.2, 1.2, 0])
        strike = Line(anyw.get_left() + LEFT * 0.1, anyw.get_right() + RIGHT * 0.1, stroke_width=5, color=BAD)
        wv = T("whatever", 60, GREY_A).move_to([2.4, 1.2, 0])
        yes = T("says yes to everything", 26, GREY_B).next_to(wv, DOWN, buff=0.3)
        self.say("joke")
        self.play(FadeIn(anyw), run_time=0.5)
        self.at_text("called whatever", lead=0.2)
        self.play(Create(strike), Write(wv), run_time=0.9)
        self.at(1)
        self.play(FadeIn(yes, shift=UP * 0.1), run_time=0.5)
        self.hold()

        pt1 = VGroup(T("Any doesn't remove the check.", 32), T("It moves it to the read, far from the bug.", 32, BAD)).arrange(DOWN, buff=0.25)
        pt1.move_to([0, -1.3, 0])
        wish = T("wanted: a check at the door, on the line that puts it in", 28, OK).move_to([0, -2.9, 0])
        fit(wish, 12.4)
        self.say("joke2")
        self.at(1)
        self.play(FadeIn(pt1[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(pt1[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the label with a gap, and the clerk =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        big = crate(4.0, 2.2, None).move_to([2.6, FL + 1.1, 0])
        lab = paper(["Box of ___________"], 26).move_to(big[0].get_center() + DOWN * 0.1)
        gap = part(lab[1], "___________")
        filled = Text("apple names", font=FONT, font_size=24, color=PEN, slant=ITALIC)
        filled.next_to(part(lab[1], "Boxof"), RIGHT, buff=0.2).align_to(gap, DOWN)
        maker = who(GREY_A, "box maker", 1.0, 20).move_to([-0.2, FL + 0.7, 0])
        taker = who(BACK, "whoever takes it", 1.0, 20).move_to([5.7, FL + 0.7, 0])
        qmark = T("?", 40, GREY_A).next_to(maker[0], UP, buff=0.15)
        self.say("label")
        self.play(Create(floor), FadeIn(big), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lab, scale=1.1), run_time=0.7)
        self.play(Indicate(gap, color=GREY_D, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(maker), FadeIn(qmark, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(taker), run_time=0.5)
        self.at_text("apple names", lead=0.4)
        self.play(FadeOut(gap), Write(filled), run_time=0.9)
        self.hold()

        dr = door(2.8, 1.4).move_to([-3.2, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-1.75, FL + 0.7, 0])
        fuji = vchip('"Fuji"', APPLE, 26).move_to([-6.0, 0.4, 0])
        tw = vchip("12", NUM, 26).move_to([-6.0, 0.4, 0])
        self.say("clerk")
        self.play(FadeOut(maker), FadeOut(qmark), Create(dr), FadeIn(clerk), run_time=0.8)
        self.at(1)
        self.play(fuji.animate.move_to([-3.2, 0.4, 0]), run_time=0.7)
        ok1 = tick(True, 0.2).next_to(fuji, UP, buff=0.15)
        self.play(FadeIn(ok1), run_time=0.3)
        self.play(FadeOut(ok1), fuji.animate.move_to(big[0].get_center() + DOWN * 0.75 + LEFT * 0.8).scale(0.8), run_time=0.8)
        self.at(2)
        self.play(FadeIn(tw), run_time=0.3)
        self.play(tw.animate.move_to([-3.6, 0.4, 0]), run_time=0.6)
        no1 = tick(False, 0.22).next_to(tw, UP, buff=0.15)
        self.play(FadeIn(no1), tw[0].animate.set_stroke(BAD), Indicate(clerk[0], color=CLERK, scale_factor=1.2), run_time=0.5)
        self.play(tw.animate.move_to([-5.6, 0.4, 0]), FadeOut(no1), run_time=0.6)
        self.hold()

        rows = [("the printed label", "class Box<T>"), ("the gap", "T"), ("what you write in it", "String, in Box<String>"),
                ("the clerk at the door", "the compiler")]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), M(b, 24, WHITE)).arrange(RIGHT, buff=0.25)
                      for a, b in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        mp_bg = SurroundingRectangle(mp, buff=0.25, color=GREY_D, stroke_width=1.5, corner_radius=0.1).set_fill(BLACK, 0.92)
        mpg = VGroup(mp_bg, mp).move_to([0, 2.25, 0])
        fit(mpg, 12.4)
        mp[3][2].set_color(CLERK)
        self.say("map")
        self.play(FadeOut(tw), FadeIn(mp_bg), run_time=0.4)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), Indicate(lab[0], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(filled, color=PEN, scale_factor=1.15), run_time=0.7)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), Indicate(clerk[0], color=CLERK, scale_factor=1.2), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the fix: Box<String> stops the 12 at the write =================
        java = code_block(["class Box<T> { T value; }", "",
                           "static void restock(Box<String> box) {", "    box.value = 12;", "}"], 22)
        kt = code_block(["class Box<T>(var value: T)", "",
                         "fun restock(box: Box<String>) {", "    box.value = 12", "}"], 22)
        fit(java, 6.0)
        fit(kt, 6.0)
        jg = titled(java, "Java").move_to([-3.3, 1.5, 0])
        kg = titled(kt, "Kotlin").move_to([3.3, 1.5, 0]).align_to(jg, UP)
        for c in (java, kt):
            part(c[0], "<T>").set_color(CLERK)
            part(c[2], "Box<String>").set_color(APPLE)
        self.say("fix")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        sq = VGroup(*[Underline(c[3], color=BAD, stroke_width=4, buff=0.06) for c in (java, kt)])
        self.play(part(java[3], "12").animate.set_color(NUM), part(kt[3], "12").animate.set_color(NUM), run_time=0.4)
        self.play(Create(sq), run_time=0.6)
        nb = VGroup(tick(False, 0.18), T("stopped at the write, before it runs", 26, BAD)).arrange(RIGHT, buff=0.2).move_to([0, -0.35, 0])
        self.play(FadeIn(nb, shift=UP * 0.1), run_time=0.5)
        self.hold()

        e1 = VGroup(T("kotlinc", 22, GREY_B), err_line("assignment type mismatch: actual type is 'Int',", 22)).arrange(RIGHT, buff=0.25)
        e1b = M("but 'String' was expected.", 22, GREY_A)
        e2 = VGroup(T("javac", 22, GREY_B), err_line("incompatible types: int cannot be converted to String", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(e1, e1b, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        e1b.align_to(e1[1][1], LEFT)
        fit(eg, 12.4).move_to([0, -1.75, 0])
        self.say("fix2")
        self.play(FadeIn(e1, shift=UP * 0.1), FadeIn(e1b, shift=UP * 0.1), run_time=0.7)
        self.at_text("And javac", lead=0.3)
        self.play(FadeIn(e2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        nc = VGroup(tick(True, 0.18), T("the counter reads a String: no cast, no ClassCastException", 26, OK)).arrange(RIGHT, buff=0.2)
        fit(nc, 12.4).move_to([0, -3.1, 0])
        self.say("fix3")
        self.play(FadeIn(nc, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= fill in the blank =================
        kt = code_block(["class Box<T>(var value: T) {", "    fun replace(newValue: T): T {", "        val old = value",
                         "        value = newValue", "        return old", "    }", "}"], 22)
        kg = titled(kt, "Kotlin").move_to([-3.4, 1.4, 0])
        vb = crate(2.2, 1.3, None).move_to([2.0, 1.75, 0])
        cb = crate(2.2, 1.3, None).move_to([5.0, 1.75, 0])
        vbl = paper(["Box<String>"], 20).move_to(vb[0].get_center() + DOWN * 0.1)
        cbl = paper(["Box<Int>"], 20).move_to(cb[0].get_center() + DOWN * 0.1)
        vbn = M("variety", 22, GREY_A).next_to(vb, DOWN, buff=0.12)
        cbn = M("count", 22, GREY_A).next_to(cb, DOWN, buff=0.12)
        vval = vchip('"Gala"', APPLE, 22).next_to(vb, UP, buff=0.08)
        cval = vchip("12", NUM, 22).next_to(cb, UP, buff=0.08)
        call = M('count.replace("Fuji")', 28, WHITE).move_to([3.5, -0.3, 0])
        self.say("fill_q")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(VGroup(kt[1], kt[4]), color=WHITE, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(FadeIn(VGroup(vb, vbl, vbn)), FadeIn(vval, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(VGroup(cb, cbl, cbn)), FadeIn(cval, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        sig = M("fun replace(newValue: Int): Int", 28, WHITE).move_to([3.3, -1.3, 0])
        for k in range(2):
            part(sig, "Int", k).set_color(NUM)
        sig_l = T("count's replace, with the blank filled in", 22, GREY_B).next_to(sig, DOWN, buff=0.15)
        tts = VGroup(part(kt[0], "T", 0), part(kt[0], "T", 1), part(kt[1], "T", 0), part(kt[1], "T", 1))
        self.say("fill")
        self.play(Indicate(cbl, color=NUM, scale_factor=1.15), run_time=0.7)
        self.at(1)
        self.play(*[t.animate.set_color(NUM) for t in tts], run_time=0.6)
        self.play(LaggedStart(*[Indicate(t, color=NUM, scale_factor=1.5) for t in tts], lag_ratio=0.2), run_time=1.0)
        self.at(2)
        self.play(FadeIn(sig, shift=UP * 0.1), FadeIn(sig_l), run_time=0.7)
        self.at(3)
        self.play(part(call, '"Fuji"').animate.set_color(APPLE), run_time=0.3)
        cx = cross_by(call, 0.2)
        self.play(FadeIn(cx), Indicate(part(call, '"Fuji"'), color=BAD, scale_factor=1.2), run_time=0.7)
        self.hold()

        ee = err_line("argument type mismatch: actual type is 'String', but 'Int' was expected.", 22)
        fit(ee, 12.4).move_to([0, -2.45, 0])
        ok_out = term(["variety was Gala, now Fuji"], 22, "BoxDemo, real output")
        ok_out.move_to([0, -2.85, 0])
        self.say("fill2")
        self.play(FadeIn(ee, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeOut(sig_l), sig.animate.shift(UP * 0.3), ee.animate.shift(UP * 0.55), run_time=0.4)
        self.play(FadeIn(ok_out, shift=UP * 0.1), Indicate(vbl, color=APPLE, scale_factor=1.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= one class, many types =================
        gen = mbox("class Box<T>", CLERK, size=26).move_to([-4.3, 0.3, 0])
        gl = T("one class, one blank", 22, GREY_B).next_to(gen, DOWN, buff=0.15)
        ts = VGroup(mbox("Box<String>", APPLE, size=26), mbox("Box<Int>", NUM, size=26), mbox("Box<Apple>", APPLE, size=26))
        ts.arrange(DOWN, buff=0.45).move_to([0.2, 0.3, 0])
        for b in ts:
            b[0].stretch_to_fit_width(2.9)
        arrs = VGroup(*[Arrow(gen.get_right(), b.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
                        for b in ts])
        tl = T("the compiler checks three types", 22, GREY_B).next_to(ts, DOWN, buff=0.25)
        self.say("many")
        self.play(FadeIn(gen), FadeIn(gl), run_time=0.6)
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(b, shift=RIGHT * 0.1)) for a, b in zip(arrs, ts)],
                              lag_ratio=0.35), run_time=1.6)
        self.at(1)
        self.play(FadeIn(tl), Indicate(ts[0], color=WHITE, scale_factor=1.05), Indicate(ts[1], color=WHITE, scale_factor=1.05), run_time=0.9)
        self.hold()

        jf = code_block(["static <T> T firstOrNull(List<T> items)"], 24)
        kf = code_block(["fun <T> firstOrNull(items: List<T>): T?"], 24)
        for c in (jf, kf):
            part(c[0], "<T>").set_color(CLERK)
        fg_ = VGroup(titled(jf, "Java: before the return type"), titled(kf, "Kotlin: right after fun")).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        fit(fg_, 12.4).move_to([0, 0.6, 0])
        flow = VGroup(M("List<Apple>", 26, APPLE), Arrow(LEFT, RIGHT, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2),
                      M("firstOrNull", 26, WHITE), Arrow(LEFT, RIGHT, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2),
                      M("Apple?", 26, APPLE)).arrange(RIGHT, buff=0.25).move_to([0, -2.1, 0])
        nocast = T("no cast anywhere", 22, OK).next_to(flow, DOWN, buff=0.2)
        self.say("fun")
        self.play(FadeOut(VGroup(gen, gl, ts, arrs, tl)), run_time=0.5)
        self.play(FadeIn(fg_[1], shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(kf[0], "<T>"), color=CLERK, scale_factor=1.3), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fg_[0], shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part(jf[0], "<T>"), color=CLERK, scale_factor=1.3), run_time=0.6)
        self.at(3)
        self.play(FadeIn(flow, shift=RIGHT * 0.1), run_time=0.9)
        self.at(4)
        self.play(FadeIn(nocast), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(M("T", 34, CLERK), T("type parameter: the blank on the label", 30)).arrange(RIGHT, buff=0.35)
        n2 = VGroup(M("String", 34, APPLE), T("type argument: the real type you write in", 30)).arrange(RIGHT, buff=0.35)
        n3 = VGroup(M("Box<T>", 34, WHITE), T("generic: a class or function with a blank", 30)).arrange(RIGHT, buff=0.35)
        ng = VGroup(n1, n2, n3).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.4, 0])
        fit(ng, 12.4)
        self.say("name")
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(n3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: the label is torn off =================
        h1 = T("you write", 22, GREY_B).move_to([-4.6, 2.6, 0])
        h2 = T("the compiler checks", 22, GREY_B).move_to([-0.6, 2.6, 0])
        h3 = T("the JVM runs", 22, GREY_B).move_to([4.2, 2.6, 0])
        gen = mbox("class Box<T>", CLERK, size=26).move_to([-4.6, 0.4, 0])
        ts = VGroup(mbox("Box<String>", APPLE, size=26), mbox("Box<Int>", NUM, size=26), mbox("Box<Apple>", APPLE, size=26))
        ts.arrange(DOWN, buff=0.45).move_to([-0.6, 0.4, 0])
        for b in ts:
            b[0].stretch_to_fit_width(2.9)
        arrs = VGroup(*[Arrow(gen.get_right(), b.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
                        for b in ts])
        one_b = mbox("Box", GREY_A, size=28).move_to([4.2, 0.4, 0])
        arrs2 = VGroup(*[Arrow(b.get_right(), one_b.get_left(), buff=0.12, stroke_width=2.5, color=GREY_D, max_tip_length_to_length_ratio=0.12)
                         for b in ts])
        torn = T("one class, label torn off", 22, GREY_A).next_to(one_b, DOWN, buff=0.2)
        self.say("breaks")
        self.play(FadeIn(VGroup(h1, h2, gen, ts, arrs)), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[Indicate(b, color=WHITE, scale_factor=1.05) for b in ts], lag_ratio=0.2), run_time=0.9)
        self.at_text("tears it off", lead=0.6)
        self.play(FadeIn(h3), LaggedStart(*[GrowArrow(a) for a in arrs2], lag_ratio=0.2), FadeIn(one_b), run_time=1.0)
        self.at(3)
        self.play(FadeIn(torn), run_time=0.5)
        self.hold()

        bin_ = VGroup(Polygon([-0.4, 0.45, 0], [0.4, 0.45, 0], [0.3, -0.45, 0], [-0.3, -0.45, 0]).set_stroke(GREY_B, 2.5).set_fill("#1a1a1a", 1),
                      Line([-0.48, 0.5, 0], [0.48, 0.5, 0], stroke_width=3, color=GREY_B)).move_to([1.8, -2.4, 0])
        clerk = person(CLERK, 1.0).move_to([0.6, -2.45, 0])
        scraps = VGroup(*[paper([w], 16).scale(0.8) for w in ("<String>", "<Int>", "<Apple>")])
        for i, s in enumerate(scraps):
            s.move_to([-0.3 + i * 0.1, -1.9 + i * 0.05, 0])
        note2 = T("checked first, then binned", 22, GREY_A).move_to([4.4, -2.4, 0])
        self.say("breaks2")
        self.play(FadeIn(clerk), FadeIn(bin_), FadeIn(scraps), run_time=0.6)
        self.at_text("in the bin", lead=0.5)
        self.play(LaggedStart(*[s.animate.move_to(bin_.get_center() + UP * 0.1).scale(0.5).set_opacity(0) for s in scraps], lag_ratio=0.25),
                  run_time=1.2)
        self.at(1)
        self.play(FadeIn(note2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the rules =================
        gq = T("Three rules", 34).move_to([0, 2.7, 0])
        rules = VGroup(rule_row("A cast like  as String  on a value from Any marks a box with no label."),
                       rule_row("Don't widen to Any to feel flexible. Here, flexible means unchecked."),
                       rule_row("A plain T promises nothing about what's inside. Next lesson: bounds."))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, 0.5, 0])
        fit(rules, 12.6)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rules[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(rules[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why put a label on the box?", 34)
        m1 = T("A cast checks at the read, far from the bug.", 30, BAD)
        m2 = T("A type parameter checks at the write, on the line with the mistake.", 30, OK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("val wrong: Box<String> = Box(42)", 28, WHITE)).arrange(RIGHT, buff=0.25)
        qc2 = T("Where do you hear about it?", 28)
        qg2 = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to(DOWN * 0.55)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = err_line("initializer type mismatch: expected 'Box<String>', actual 'Box<Int>'.", 22)
        fit(ans, 12.4)
        ansl = T("on that line, before the program runs", 24, OK)
        ag = VGroup(ans, ansl).arrange(DOWN, buff=0.2).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ansl, shift=UP * 0.1), run_time=0.5)
        self.at_text("initializer", lead=0.3)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
