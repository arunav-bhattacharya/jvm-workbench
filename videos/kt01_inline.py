from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bnanoTime\b", "nano time"), (r"\blmul\b", "L mul"), (r"\bldiv\b", "L div"), (r"\binvokedynamic\b", "invoke dynamic"),
    (r"\binvokestatic\b", "invoke static"), (r"\bcheckcast\b", "check cast"), (r"\blongValue\b", "long value"),
    (r"\bprintln\b", "print line"), (r"\binkNotInline\b", "ink not inline"), (r"\binkInline\b", "ink inline"),
    (r"\btimedNotInline\b", "timed not inline"), (r"\bFunction0\b", "Function zero"), (r"\btoSheets\b", "to sheets"),
    (r"\bforEach\b", "for each"), (r"\b3 ml\b", "3 millilitres"), (r"\b360 ml\b", "360 millilitres"),
    (r"\(pages \+ 1\) / 2", "pages plus 1, divided by 2"),
]

# every spoken line, in order
N = {
    "open": "Picture a small print shop. Behind the counter sits a binder of procedure sheets, like how to time a job. "
            "A clerk takes a job. She can pass it to a colleague who knows the sheet, with a slip for the one step only "
            "she can do. Or she can photocopy the sheet into the job's own folder, and do every step herself.",
    "open2": "The copy is quicker. It costs paper, though. And it never hears about corrections to the master sheet. "
             "Keep those three in mind: quicker, paper, corrections.",
    "shyq": "Now a question that's easy to be shy about. Everybody says: mark small helpers inline, it's faster. "
            "Faster than what? What does it even cost to pass one tiny lambda to a function?",
    "helper": "Let's find out with a helper the shop's app uses everywhere. It runs one step of a job and "
              "prints how long it took. Today's step: how much ink does a job need? The shop's rule of thumb is "
              "3 ml of ink for every 100 pages.",
    "lambda": "The part in braces is a lambda: a small function, written in place and passed as a value. It uses pages, "
              "a variable from outside its braces. A lambda that carries outside values like that is called a closure.",
    "cost_q": "So, besides the multiply and the divide, what extra work does one call do? Pause and guess.",
    "cost": "Three things. One object: the JVM builds a small object that holds a copy of pages. One call through an "
            "interface, a type that only names its methods: the helper calls that object's invoke method. And one "
            "unboxing. The helper works for any result type, so the answer travels back as a plain Object, and has to "
            "be turned back into a primitive long.",
    "map": "In the shop, this is the clerk handing the job to a colleague. The helper, timedNotInline, is the colleague. "
           "The lambda is the slip, with the clerk's own step written on it. And invoke is the colleague calling her "
           "back to do that step.",
    "paste": "You could skip all three by hand: paste the helper's body into the caller, with the lambda's body in the "
             "middle. It works. Now picture doing that in fifty places.",
    "wish": "Wouldn't it be nice if someone did the pasting for us? Well, the compiler is happy to. It never gets bored, "
            "and it never gets paper cuts.",
    "inline": "Write inline in front of fun, and keep the same body. Now, at every call site, each place in the code "
              "that calls the function, the compiler copies in the function's body and the lambda's body. That's the "
              "photocopy: the whole procedure lands in the job's own folder, with the clerk's step written in place.",
    "javap": "Let's see if that's really true. javap, a tool in the JDK, prints the bytecode in a class file: the "
             "instructions the JVM runs. The lesson's demo has two tiny functions, inkNotInline and inkInline.",
    "javap_q": "Which one builds an object with invokedynamic, and which one does the multiply itself? Pause and guess.",
    "bc_not": "inkNotInline is seven instructions. invokedynamic builds a Function0, Kotlin's interface for a function "
              "with no parameters. That's the slip. invokestatic calls the helper. That's handing it over. Then "
              "checkcast and longValue unbox the answer.",
    "bc_in": "inkInline has none of that. No invokedynamic, no call to the helper. The multiply, lmul, and the divide, "
             "ldiv, sit right inside, between two calls to nanoTime. Just like our hand-pasted version.",
    "run": "Run them, and they agree: 12,000 pages need 360 ml of ink.",
    "twice": "So, should we inline everything? Look further down inkInline. The finally block is there twice: once for "
             "the normal exit, and once for the exit by exception. Every caller carries its own copy of the whole body.",
    "goodbad": "The good news: no slip, no call, no box. The bad news: every folder gets thicker. A 40-line helper "
               "called from 200 places becomes 200 copies.",
    "rule": "So here's the rule. inline is for small functions that take lambdas. The standard library is full of them: "
            "forEach, map, filter, let, apply, use, repeat and require are all inline.",
    "frozen": "And remember the corrections? A photocopy never hears about them, and neither does an inlined copy. A "
              "caller gets its copy when it is compiled. In the lesson's test, an app built against version 1 of a "
              "library ran with version 2, and printed this. The plain function ran the new code. The inline one "
              "still ran its old copy.",
    "java": "And here's where the picture breaks. Java can't photocopy anything, because javac can't inline Kotlin "
            "code. To Java, timed is an ordinary static method that takes a Function0, and a Java lambda becomes an "
            "object like any other. Java always hands over the slip.",
    "loop": "One more thing changes once the step sits in the clerk's own folder. If it says stop here, she stops the "
            "whole job, not just her step. So a return inside an inlined lambda leaves more than you'd expect. "
            "That's the next section.",
    "moral": "So, faster than what? Faster than a slip, a call and a box on every use. inline copies the helper and its "
             "lambda into each caller. Keep it for small helpers that take lambdas.",
    "check": "Quick check. The shop also has toSheets, which turns a page count into sheets with (pages + 1) / 2. "
             "No lambda in sight. Should it be inline?",
    "check_a": "No. There's no slip to remove, so there's nothing to gain. The compiler even says so, with this warning.",
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

    def predict(self, secs=2.4, pos=(6.4, -3.62), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


PAPER, INK = "#EDE6D6", "#161616"


def person(color=BLUE_M, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def paper(lines, size=20, pad=0.16, border=GREY_B):
    """A sheet of paper: one Text with line breaks, so every line sits on an even baseline."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(border, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


def open_gap(t, s, d=0.08):
    """Nudge the letters after part s of Text t right by d, so a box around s has room before them."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    t[i + len(k):].shift(RIGHT * d)
    return t


def lam_box(t, s, color):
    """A box around part s of Text t whose right edge sits halfway to the next letter, so it never touches it."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    lam, nxt = t[i:i + len(k)], t[i + len(k)]
    left = lam.get_left()[0] - 0.06
    right = (lam.get_right()[0] + nxt.get_left()[0]) / 2
    r = Rectangle(width=right - left, height=lam.height + 0.1, color=color, stroke_width=2.5)
    return r.move_to([(left + right) / 2, lam.get_y(), 0])


def framed(g, color, buff=0.22, k=0.12):
    r = SurroundingRectangle(g, buff=buff, color=color, stroke_width=2.5, corner_radius=0.1).set_fill(dim(color, k), 1)
    return VGroup(r, g)


def card(lines, color, size=22, title=None, tsize=22):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    g = VGroup(T(title, tsize, color), t).arrange(DOWN, aligned_edge=LEFT, buff=0.14) if title else t
    return framed(g, color, buff=0.22, k=0.14)


def folder(name, color=GOLD_M, w=2.6, h=1.8, size=20):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.16), 1)
    tab = RoundedRectangle(corner_radius=0.05, width=0.9, height=0.24).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    tab.next_to(r, UP, buff=-0.02).align_to(r, LEFT).shift(RIGHT * 0.15)
    t = T(name, size, color).move_to(tab).shift(UP * 0.28)
    return VGroup(tab, r, t)


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


# one colour per thing, for the whole Kotlin track (the print shop)
CLERK, MATE, STEP, OBJ, BAD, OK, CODE = BLUE_M, PURPLE_M, YELLOW_M, GOLD_M, RED_M, GREEN_M, GREY_A


def binder(s=1.0):
    r = Rectangle(width=1.3, height=1.7).set_stroke(GREY_A, 2.5).set_fill("#2a2a2a", 1)
    rings = VGroup(*[Circle(radius=0.07).set_stroke(GREY_B, 2).move_to(r.get_left() + RIGHT * 0.18 + UP * (0.5 - 0.5 * i)) for i in range(3)])
    lab = T("procedures", 20, GREY_A).rotate(PI / 2).move_to(r.get_center() + RIGHT * 0.12)
    return VGroup(r, rings, lab).scale(s)


def slip(s=1.0):
    return paper(["ink:", "pages*3/100"], 20, border=STEP).scale(s)


def floor_line(y=-1.45, x0=-6.3, x1=6.3):
    return Line([x0, y, 0], [x1, y, 0], stroke_width=1.5, color=GREY_D)


class Kt01Inline(Narrated):
    """kt-01, section 0: what inline does. The print shop: a clerk hands a job to a colleague with a slip, or
    photocopies the procedure into the job's folder (quicker, costs paper, never hears corrections). Shy question:
    faster than what? The timed helper (3 ml of ink per 100 pages), lambda and closure, the three costs (object,
    interface call, unboxing), the slip mapped; hand pasting; inline = the photocopy; javap of inkNotInline and
    inkInline (real bytecode), 360 ml; finally copied twice, good news/bad news; the rule and the inline standard
    library; frozen copies (inline=v1 plain=v2); Java always hands over the slip; loop to non-local return; moral; check
    with toSheets and the compiler's warning."""

    def construct(self):
        self.title_card("Inline functions", "a photocopy instead of a slip")

        # ================= the print shop =================
        fl = floor_line()
        bd = binder(1.0).move_to([-5.3, 0.9, 0])
        clerk = person(CLERK, 1.4).move_to([-2.3, -1.45 + 0.42, 0])
        clerk_l = T("clerk", 22, CLERK).next_to(clerk, DOWN, buff=0.15)
        mate = person(MATE, 1.4).move_to([3.4, -1.45 + 0.42, 0])
        mate_l = T("colleague", 22, MATE).next_to(mate, DOWN, buff=0.15)
        sl = slip().move_to([-1.0, 0.15, 0])
        sl_l = T("a slip for her one step", 22, STEP).move_to([1.9, 1.05, 0])
        self.say("open")
        self.play(Create(fl), FadeIn(bd), run_time=0.7)
        self.at(1)
        self.play(FadeIn(clerk), FadeIn(clerk_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mate), FadeIn(mate_l), run_time=0.6)
        self.play(FadeIn(sl, shift=UP * 0.1), run_time=0.4)
        self.play(sl.animate.move_to([1.9, 0.15, 0]), FadeIn(sl_l), run_time=1.4)
        fd = folder("job folder", OBJ, 2.5, 1.9).move_to([-2.3, 1.5, 0])
        sheet = paper(["time a job:", "1. start clock", "2. her step", "3. print time"], 20).move_to(bd.get_center())
        self.at(3)
        self.play(VGroup(mate, mate_l, sl, sl_l).animate.set_opacity(0.3), FadeIn(fd), run_time=0.7)
        self.play(sheet.animate.move_to(fd[1].get_center()), run_time=1.2)
        self.play(part(sheet[1], "2. her step").animate.set_color("#8A6D00"), run_time=0.4)
        self.hold()

        l1 = T("quicker", 26, OK)
        l2 = T("costs paper", 26, OBJ)
        l3 = T("never hears corrections", 26, BAD)
        lg = VGroup(l1, l2, l3).arrange(RIGHT, buff=0.9).move_to([0, -2.75, 0])
        self.say("open2")
        self.play(FadeIn(l1, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(l2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(l3, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(Indicate(lg, color=WHITE, scale_factor=1.06), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("\"Mark small helpers inline, it's faster.\"", 34)
        q2 = T("Faster than what?", 34, STEP)
        q3 = T("What does it cost to pass one tiny lambda?", 34)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)
        self.wipe(0.5)

        # ================= the timed helper =================
        hl = {"pages": WHITE}
        jv = code_block(["static <T> T timed(String label, Supplier<T> block) {",
                         "    long start = System.nanoTime();",
                         "    try { return block.get(); }",
                         "    finally { System.out.println(label + \" took ...\"); }",
                         "}",
                         "long ink = timed(\"ink\", () -> pages * 3 / 100);"], 22, color=CODE)
        kt = code_block(["fun <T> timedNotInline(label: String, block: () -> T): T {",
                         "    val start = System.nanoTime()",
                         "    try { return block() }",
                         "    finally { println(\"$label took ...\") }",
                         "}",
                         "val ink = timedNotInline(\"ink\") { pages * 3 / 100 }"], 22, color=CODE)
        open_gap(jv[5], "() -> pages * 3 / 100")
        jv.move_to([-5.6, 1.55, 0], aligned_edge=LEFT)
        kt.move_to([-5.6, -1.75, 0], aligned_edge=LEFT)
        jl = T("Java", 22, GREY_B).next_to(jv, UP, buff=0.2).align_to(jv, LEFT)
        kl = T("Kotlin", 22, GREY_B).next_to(kt, UP, buff=0.2).align_to(kt, LEFT)
        rule_t = T("3 ml of ink per 100 pages", 24, STEP).move_to([4.2, 3.35, 0])
        self.say("helper")
        self.play(FadeIn(jl), FadeIn(jv, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(kl), FadeIn(kt, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(rule_t), run_time=0.5)
        self.play(jv[5].animate.set_color(WHITE), kt[5].animate.set_color(WHITE), run_time=0.6)
        self.hold()

        lam_k = part(kt[5], "{ pages * 3 / 100 }")
        lam_j = part(jv[5], "() -> pages * 3 / 100")
        bk = SurroundingRectangle(lam_k, buff=0.05, color=STEP, stroke_width=2.5)
        bj = lam_box(jv[5], "() -> pages * 3 / 100", STEP)
        lam_l = T("a lambda", 24, STEP).next_to(bk, DOWN, buff=0.2).align_to(bk, LEFT)
        clo_l = T("uses pages from outside: a closure", 24, STEP).next_to(bk, DOWN, buff=0.2).align_to(bk, LEFT)
        self.say("lambda")
        self.play(Create(bk), Create(bj), FadeIn(lam_l), run_time=0.8)
        self.at(1)
        self.play(Indicate(part(kt[5], "pages"), color=STEP, scale_factor=1.3),
                  Indicate(part(jv[5], "pages"), color=STEP, scale_factor=1.3), run_time=0.9)
        self.at(2)
        self.play(FadeTransform(lam_l, clo_l), run_time=0.6)
        self.hold()

        self.say("cost_q")
        self.hold(after=0)
        self.predict(2.6)
        self.wipe(0.5)

        # ================= three costs, and the slip =================
        def cost_card(title, body, color):
            t = T(title, 26, color)
            b = M(body, 22, WHITE)
            g = VGroup(t, b).arrange(DOWN, buff=0.18)
            r = RoundedRectangle(corner_radius=0.1, width=3.7, height=1.45).set_stroke(color, 2.5).set_fill(dim(color, 0.14), 1)
            return VGroup(r, g.move_to(r))
        c1 = cost_card("one object", "holds a copy of pages", OBJ)
        c2 = cost_card("one interface call", "block.invoke()", MATE)
        c3 = cost_card("one unboxing", "Object -> long", BAD)
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.4).move_to([0, 2.3, 0])
        docs = T("the Kotlin docs name the same three costs", 22, GREY_B).next_to(cards, DOWN, buff=0.25)
        self.say("cost")
        self.play(FadeIn(c1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(c3, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(docs), run_time=0.5)
        self.hold()

        fl = floor_line(-2.6)
        clerk = person(CLERK, 1.3).move_to([-4.0, -2.6 + 0.4, 0])
        clerk_l = T("clerk", 22, CLERK).next_to(clerk, LEFT, buff=0.25)
        mate = person(MATE, 1.3).move_to([3.0, -2.6 + 0.4, 0])
        mate_l = VGroup(T("colleague", 22, MATE), M("timedNotInline", 22, MATE)).arrange(DOWN, buff=0.08).next_to(mate, RIGHT, buff=0.25)
        sl = slip().move_to([-3.0, -1.3, 0])
        sl_l = T("the lambda object", 22, STEP)
        back = CurvedArrow([2.6, -1.25, 0], [-3.6, -1.25, 0], angle=PI / 5, color=MATE, stroke_width=3)
        back_l = M("invoke(): calling her back", 22, MATE).move_to([-0.3, 0.25, 0])
        self.say("map")
        self.play(FadeOut(docs), Create(fl), FadeIn(clerk), FadeIn(clerk_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mate), FadeIn(mate_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sl, shift=UP * 0.1), run_time=0.4)
        self.play(sl.animate.move_to([1.6, -1.3, 0]), run_time=1.1)
        sl_l.next_to(sl, LEFT, buff=0.3)
        self.play(FadeIn(sl_l), Indicate(c1[1][0], color=OBJ, scale_factor=1.1), run_time=0.6)
        self.at(3)
        self.play(Create(back), FadeIn(back_l), Indicate(c2[1][0], color=MATE, scale_factor=1.1), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= paste it by hand =================
        jp = code_block(["long start = System.nanoTime();",
                         "long ink;",
                         "try { ink = pages * 3 / 100; }            // pasted in",
                         "finally { System.out.println(\"ink took ...\"); }"], 22, color=CODE,
                        hl={"// pasted in": STEP})
        kp = code_block(["val start = System.nanoTime()",
                         "val ink = try { pages * 3 / 100 }         // pasted in",
                         "finally { println(\"ink took ...\") }"], 22, color=CODE, hl={"// pasted in": STEP})
        jp.move_to([-5.6, 1.7, 0], aligned_edge=LEFT)
        kp.move_to([-5.6, -0.9, 0], aligned_edge=LEFT)
        jl = T("Java", 22, GREY_B).next_to(jp, UP, buff=0.2).align_to(jp, LEFT)
        kl = T("Kotlin", 22, GREY_B).next_to(kp, UP, buff=0.2).align_to(kp, LEFT)
        stack = VGroup(*[RoundedRectangle(corner_radius=0.06, width=2.0, height=1.2).set_stroke(GREY_B, 1.5).set_fill("#1c1c1c", 1)
                         for _ in range(6)])
        for i, r in enumerate(stack):
            r.move_to([3.2 + 0.14 * i, -2.0 - 0.1 * i, 0])
        fifty = T("x 50", 40, BAD).move_to([5.1, -1.2, 0])
        self.say("paste")
        self.play(FadeIn(jl), FadeIn(jp, shift=UP * 0.1), FadeIn(kl), FadeIn(kp, shift=UP * 0.1), run_time=1.0)
        self.at_text("with the lambda", lead=0.2)
        self.play(Indicate(part(kp[1], "// pasted in"), color=STEP, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.1) for r in stack], lag_ratio=0.2), FadeIn(fifty), run_time=1.4)
        self.hold()

        w1 = T("Wouldn't it be nice if someone did the pasting?", 32).move_to([0, 1.0, 0])
        w2 = T("the compiler: never bored, never gets paper cuts", 28, OBJ).move_to([0, -0.2, 0])
        self.say("wish")
        self.play(FadeOut(VGroup(jp, kp, jl, kl, stack, fifty)), run_time=0.5)
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        sig = M("inline fun <T> timed(label: String, block: () -> T): T", 26, CODE, t2c={"inline": OBJ})
        sig.move_to([0, 3.0, 0])
        fit(sig, 12.4)
        konly = T("Kotlin only: Java has no inline", 20, GREY_B).next_to(sig, DOWN, buff=0.15)
        cs = M("val ink = timed(\"ink\") { pages * 3 / 100 }", 22, CODE).move_to([-3.3, 1.35, 0])
        cs_l = T("a call site", 22, GREY_B).next_to(cs, DOWN, buff=0.12)
        fd = folder("the caller's own code", OBJ, 5.6, 2.6, 20).move_to([2.6, -1.5, 0])
        body = VGroup(M("start = System.nanoTime()", 22, WHITE), M("pages * 3 / 100", 22, STEP),
                      M("println(\"ink took ...\")", 22, WHITE)).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        body.move_to(fd[1].get_center())
        cp = Arrow(cs_l.get_bottom() + DOWN * 0.05, fd[1].get_left() + UP * 0.3, buff=0.1, stroke_width=3, color=OBJ,
                   max_tip_length_to_length_ratio=0.12)
        cp_l = T("the photocopy", 24, OBJ).move_to([-3.6, -1.7, 0])
        self.say("inline")
        self.play(FadeOut(VGroup(w1, w2)), FadeIn(sig, shift=DOWN * 0.1), FadeIn(konly), run_time=0.8)
        self.play(Indicate(part(sig, "inline"), color=OBJ, scale_factor=1.3), run_time=0.8)
        self.at(1)
        self.play(FadeIn(cs), FadeIn(cs_l), run_time=0.6)
        self.at_text("the compiler copies", lead=0.2)
        self.play(GrowArrow(cp), FadeIn(fd), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.15) for b in body], lag_ratio=0.35), run_time=1.2)
        self.at(2)
        self.play(FadeIn(cp_l), Indicate(body[1], color=STEP, scale_factor=1.15), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the bytecode =================
        defs = code_block(["fun inkNotInline(pages: Long): Long =",
                           "    timedNotInline(\"not inline\") { pages * 3 / 100 }",
                           "fun inkInline(pages: Long): Long =",
                           "    timed(\"inline\") { pages * 3 / 100 }"], 22, color=CODE)
        defs.move_to([0, 1.4, 0])
        jd = VGroup(M("javap -c -p InlineDemoKt.class", 24, GREY_B),
                    T("prints the bytecode: the instructions the JVM runs", 22, GREY_B)).arrange(DOWN, buff=0.12).move_to([0, -1.2, 0])
        self.say("javap")
        self.play(FadeIn(jd[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jd[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(defs, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.say("javap_q")
        self.hold(after=0)
        self.predict(2.6)

        nb = code_block(["ldc            \"not inline\"", "lload_0", "invokedynamic  -> Function0",
                         "invokestatic   timedNotInline", "checkcast      java/lang/Number",
                         "invokevirtual  Number.longValue", "lreturn"], 22, color=CODE)
        ib_src = ["invokestatic   System.nanoTime", "lload_0", "iconst_3", "i2l", "lmul", "bipush         100", "i2l",
                  "ldiv", "...", "invokestatic   System.nanoTime", "...", "invokevirtual  PrintStream.println", "...",
                  "invokestatic   System.nanoTime", "...", "invokevirtual  PrintStream.println", "athrow"]
        ib = VGroup(*[M(l, 22, CODE) for l in ib_src])
        for i, l in enumerate(ib):
            l.move_to([0, -0.335 * i, 0], aligned_edge=LEFT)
            if ib_src[i] == "...":
                l.shift(UP * 0.06)
        nh = M("inkNotInline", 26, MATE)
        ih = M("inkInline", 26, OBJ)
        nb.next_to(nh, DOWN, buff=0.3).align_to(nh, LEFT)
        nbg = VGroup(nh, nb).move_to([-6.1, 3.25, 0], aligned_edge=UL)
        ib.next_to(ih, DOWN, buff=0.25).align_to(ih, LEFT)
        ibg = VGroup(ih, ib).move_to([0.9, 3.35, 0], aligned_edge=UL)
        src = T("javap, real output (shortened)", 20, GREY_B).move_to([6.3, -3.55, 0], aligned_edge=RIGHT)
        self.say("bc_not")
        self.play(FadeOut(VGroup(defs, jd)), run_time=0.4)
        self.play(FadeIn(nh), FadeIn(src), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in nb], lag_ratio=0.12), run_time=1.2)
        self.at(1)
        self.play(nb[2].animate.set_color(STEP), run_time=0.5)
        sl = slip(0.8).next_to(nb[2], DOWN, buff=0.0).shift(RIGHT * 4.0 + UP * 0.25)
        self.at(2)
        self.play(FadeIn(sl, shift=LEFT * 0.1), run_time=0.5)
        self.at(3)
        self.play(nb[3].animate.set_color(MATE), run_time=0.5)
        self.at(5)
        self.play(nb[4].animate.set_color(BAD), nb[5].animate.set_color(BAD), run_time=0.6)
        self.hold()

        self.say("bc_in")
        self.play(FadeOut(sl), FadeIn(ih), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in ib], lag_ratio=0.05), run_time=1.4)
        self.at(1)
        self.play(Indicate(nb[2], color=STEP, scale_factor=1.1), Indicate(nb[3], color=MATE, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(ib[4].animate.set_color(OBJ), ib[7].animate.set_color(OBJ), run_time=0.6)
        self.play(ib[0].animate.set_color(WHITE), ib[9].animate.set_color(WHITE), run_time=0.5)
        self.hold()

        out = VGroup(M("ink = 360 ml", 26, OK), M("ink = 360 ml", 26, OK)).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        out_l = T("12,000 pages, both versions: real output", 20, GREY_B)
        outg = VGroup(out_l, out).arrange(DOWN, buff=0.2, aligned_edge=LEFT).move_to([-6.1, -1.9, 0], aligned_edge=LEFT)
        self.say("run")
        self.play(FadeIn(outg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0.6)

        # ================= the price =================
        b1 = Brace(VGroup(ib[9], ib[11]), LEFT, color=OK)
        b2 = Brace(VGroup(ib[13], ib[16]), LEFT, color=BAD)
        b1l = T("finally, normal exit", 24, OK).next_to(b1, LEFT, buff=0.15)
        b2l = T("finally again, exit by exception", 24, BAD).next_to(b2, LEFT, buff=0.15)
        self.say("twice")
        self.play(FadeOut(VGroup(nbg, outg)), run_time=0.5)
        self.at(1)
        self.play(ib[11].animate.set_color(WHITE), ib[15].animate.set_color(WHITE), run_time=0.5)
        self.at(2)
        self.play(GrowFromCenter(b1), FadeIn(b1l), run_time=0.6)
        self.at_text("and once", lead=0.2)
        self.play(GrowFromCenter(b2), FadeIn(b2l), run_time=0.6)
        self.hold()
        self.wipe()

        gn = T("good news", 30, OK)
        gi = VGroup(*[T(x, 26) for x in ("no slip", "no call", "no box")]).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        gg = VGroup(gn, gi).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([-4.0, 1.6, 0])
        bn = T("bad news", 30, BAD)
        bi = T("every folder gets thicker", 26)
        bg = VGroup(bn, bi).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([3.0, 2.0, 0], aligned_edge=LEFT).shift(LEFT * 1.4)
        fds = VGroup(*[folder("", OBJ, 1.0, 0.7 + 0.1 * i) for i in range(8)]).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
        fds.move_to([1.6, -0.75, 0])
        many = T("a 40-line helper, 200 callers: 200 copies", 26, OBJ).move_to([0, -2.0, 0])
        docs = T("the docs: inlining pays off only if you avoid inlining large functions", 22, GREY_B).move_to([0, -2.85, 0])
        self.say("goodbad")
        self.play(FadeIn(gn), LaggedStart(*[FadeIn(x, shift=RIGHT * 0.1) for x in gi], lag_ratio=0.3), run_time=1.2)
        self.at(1)
        self.play(FadeIn(bg, shift=UP * 0.1), LaggedStart(*[FadeIn(f) for f in fds], lag_ratio=0.1), run_time=1.2)
        self.at(2)
        self.play(FadeIn(many), run_time=0.6)
        self.play(FadeIn(docs), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the rule, and two more limits =================
        rl = T("inline is for small functions that take lambdas.", 34, OBJ).move_to([0, 2.6, 0])
        names = ["forEach", "map", "filter", "let", "apply", "use", "repeat", "require"]
        chips = M("   ".join(names), 28, WHITE).move_to([0, 1.1, 0])
        fit(chips, 12.4)
        chips_l = T("all inline, in the standard library", 22, GREY_B).next_to(chips, DOWN, buff=0.2)
        mp = VGroup(M("jobs.map { it.pages }", 26, WHITE), T("costs about what a hand-written loop costs", 24, GREY_A)).arrange(RIGHT, buff=0.4)
        mp.move_to([0, -1.0, 0])
        fit(mp, 12.4)
        self.say("rule")
        self.play(FadeIn(rl, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(part(chips, n), shift=UP * 0.1) for n in names], lag_ratio=0.12), FadeIn(chips_l), run_time=1.6)
        self.hold()
        self.play(FadeOut(VGroup(chips, chips_l)), rl.animate.scale(0.75).move_to([0, 3.3, 0]), run_time=0.6)

        app = framed(VGroup(T("an app", 26, CLERK), T("built against version 1", 22, GREY_A)).arrange(DOWN, buff=0.1), CLERK)
        lib = framed(VGroup(T("the library", 26, MATE), T("now version 2", 22, GREY_A)).arrange(DOWN, buff=0.1), MATE)
        VGroup(app, lib).arrange(RIGHT, buff=2.4).move_to([0, 1.5, 0])
        ar = Arrow(app.get_right(), lib.get_left(), buff=0.15, stroke_width=3, color=GREY_B)
        res = M("inline=v1 plain=v2", 36, WHITE, t2c={"inline=v1": BAD, "plain=v2": OK}).move_to([0, -0.4, 0])
        res_l = T("printed by the lesson's test", 20, GREY_B).next_to(res, DOWN, buff=0.15)
        n1 = T("plain function: the new code", 24, OK)
        n2 = T("inline function: its old copy", 24, BAD)
        ns = VGroup(n1, n2).arrange(RIGHT, buff=1.2).move_to([0, -2.1, 0])
        corr = T("never hears corrections", 24, BAD).move_to([0, -3.0, 0])
        self.say("frozen")
        self.play(FadeIn(corr), run_time=0.5)
        self.at(2)
        self.play(FadeIn(app), run_time=0.5)
        self.at(3)
        self.play(GrowArrow(ar), FadeIn(lib), run_time=0.7)
        self.at_text("and printed this", lead=0.1)
        self.play(FadeIn(res, shift=UP * 0.1), FadeIn(res_l), run_time=0.7)
        self.at(4)
        self.play(FadeIn(n1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(n2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: Java =================
        jc = M("long ink = InlineDemoKt.timed(\"from Java\", () -> 12_000L * 3 / 100);", 22, CODE)
        open_gap(jc, "() -> 12_000L * 3 / 100")
        jc.move_to([0, 1.9, 0])
        fit(jc, 12.4)
        jcl = T("Java", 22, GREY_B).next_to(jc, UP, buff=0.2).align_to(jc, LEFT)
        lam = part(jc, "() -> 12_000L * 3 / 100")
        lb = lam_box(jc, "() -> 12_000L * 3 / 100", STEP)
        j1 = T("javac can't inline Kotlin code", 26, BAD).move_to([0, 0.5, 0])
        j2 = VGroup(T("to Java,", 26), M("timed", 26, WHITE), T("is an ordinary static method that takes a", 26),
                    M("Function0", 26, WHITE)).arrange(RIGHT, buff=0.15).move_to([0, -0.4, 0])
        fit(j2, 12.4)
        clerk = person(CLERK, 1.2).move_to([-2.2, -2.3, 0])
        mate = person(MATE, 1.2).move_to([2.6, -2.3, 0])
        sl = slip(0.85).move_to([-1.2, -2.2, 0])
        j3 = T("Java always hands over the slip.", 26, STEP).move_to([0, -3.35, 0])
        self.say("java")
        self.play(FadeIn(jcl), FadeIn(jc), run_time=0.7)
        self.at_text("because javac", lead=0.3)
        self.play(FadeIn(j1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(j2), Create(lb), run_time=0.7)
        self.at(2)
        self.play(FadeIn(clerk), FadeIn(mate), FadeIn(sl), run_time=0.5)
        self.play(sl.animate.move_to([1.6, -2.2, 0]), FadeIn(j3), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= open loop: "stop here" =================
        fd = folder("job folder", OBJ, 4.4, 2.6).move_to([-3.2, 0.2, 0])
        sheet = paper(["1. start clock", "2. her step:", "   stop here!", "3. print time"], 22).move_to(fd[1].get_center())
        stop = part(sheet[1], "stop here!")
        r1 = T("stops the whole job,", 26, BAD)
        r2 = T("not just her step", 26, BAD)
        r3 = VGroup(M("return", 26, WHITE), T("in an inlined lambda", 26)).arrange(RIGHT, buff=0.15)
        r4 = T("leaves the whole function", 26, BAD)
        rg = VGroup(r1, r2, r3, r4).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([3.0, 0.3, 0])
        nxt = T("next section: non-local returns", 22, GREY_B).move_to([0, -2.6, 0])
        self.say("loop")
        self.play(FadeIn(fd), FadeIn(sheet), run_time=0.7)
        self.at(1)
        self.play(stop.animate.set_color("#B01E12"), run_time=0.4)
        self.play(FadeIn(VGroup(r1, r2), shift=UP * 0.1), fd[1].animate.set_stroke(BAD), run_time=0.7)
        self.at(2)
        self.play(FadeIn(VGroup(r3, r4), shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(nxt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        m0 = T("Faster than what?", 30, GREY_A)
        m1 = T("Than a slip, a call and a box, on every use.", 30, STEP)
        m2 = T("inline copies the helper and its lambda into each caller.", 30, OBJ)
        m3 = T("Keep it for small helpers that take lambdas.", 30, WHITE)
        mg = VGroup(m0, m1, m2, m3).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(m0, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = M("inline fun toSheets(pages: Int): Int = (pages + 1) / 2", 24, CODE, t2c={"inline": OBJ}).move_to([0, -1.0, 0])
        fit(qc, 12.4)
        qq = T("Check: no lambda in sight. Should it be inline?", 26).next_to(qc, UP, buff=0.25)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), FadeIn(qc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        warn = VGroup(M("expected performance impact from inlining is insignificant.", 22, OBJ),
                      M("Inlining works best for functions with parameters of function types.", 22, OBJ)
                      ).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([0, -2.6, 0])
        fit(warn, 12.4)
        wl = T("the compiler's warning", 20, GREY_B).next_to(warn, DOWN, buff=0.12)
        self.say("check_a")
        self.play(FadeIn(cross(qc, 0.22)), run_time=0.5)
        self.at(2)
        self.play(FadeIn(warn, shift=UP * 0.1), FadeIn(wl), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
