from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bisA<(\w+)>", r"is A of \1"), (r"\bisA\b", "is A"), (r"\bnameOf<(\w+)>", r"name of \1"), (r"\bnameOf\b", "name of"),
    (r"\bfilterIsInstance\b", "filter is instance"), (r"\bisInstance\b", "is instance"), (r"\binstanceof\b", "instance of"),
    (r"T::class", "T colon colon class"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
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



NOTE = YELLOW_M


def plain_box(w=2.0, h=1.3):
    """A storeroom box after the clerk tore its label off."""
    return crate(w, h, None)


def note(lines, size=20):
    """A small yellow note pinned to a job."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 0.3, height=t.height + 0.26).set_stroke(GREY_B, 1.5).set_fill("#F2E394", 1)
    pin = Dot(radius=0.06, color=RED_M).move_to(r.get_top())
    return VGroup(r, t.move_to(r), pin)


def body_box(text, color=GREY_A, size=22):
    return mbox(text, color, size=size, h=0.7)


# every spoken line, in order
N = {
    "open": "Every box that comes into the storeroom passes the clerk at the door. The clerk reads its label, box of "
            "apples, checks that only apples go in, and nods it through. Then, as you've heard before, the clerk tears "
            "the label off.",
    "open2": "On the shelves, a box of apples and a box of lemons look alike. That's fine, until someone asks a box: are "
             "you a box of apples? There's no label left to read.",
    "code0": "In code, that tearing off is called type erasure. The compiler checks every type argument, then leaves it "
             "out of the compiled program. At run time, a list of names and a list of weights are the same class. The "
             "demo prints: same class at run time, true.",
    "fail0": "So a type check can only test the class. Ask whether something is a List<String>, and Kotlin says: cannot "
             "check for instance of erased type. Ask whether it is T, inside an ordinary generic function, and it fails "
             "the same way.",
    "shyq": "Here's a question that's easy to be shy about. When I call isA<Apple>, I typed Apple right there, in plain "
            "sight. The compiler saw it. So where did it go? Why can't my function just ask T what it is?",
    "clerk2": "Picture a second clerk at the door. This one knows the labels are about to come off. So before a label "
              "goes, the clerk copies it onto a note, and pins the note to the job: this job, apples. When the job "
              "reaches the shop floor, whoever does it can read the note.",
    "inline": "Kotlin's version of that clerk has two parts. The first is inline. Normally a function has one shared body, "
              "compiled once, and every caller jumps to it. Mark it inline, and the compiler copies the body into each "
              "place that calls it.",
    "inline2": "And at each of those places, the type argument is known. A call like isA<Apple> is being compiled right "
               "there, with Apple in plain sight.",
    "reified": "The second part is reified. It sounds like something a doctor would say, but it just means made real. "
               "Mark T reified, and the compiler writes the caller's real class into the copied body. That's the note.",
    "code": "Here it is. isA is an inline function with a reified T, and its body is one line: this is T. Java has no "
            "such clerk, so it passes the class by hand: a Class object, and isInstance.",
    "figure": "Now watch what happens to the call. gala dot isA<Apple> isn't a call any more. The body is copied into the "
              "caller, with Apple written in. In the caller's own bytecode, it has become: gala instanceof Apple. A real "
              "check, on a real class.",
    "predict_q": "So let's sort a mixed delivery: two apples, a lemon, a paper bag, and a null. Is Gala an apple? Is the "
                 "bag? And filterIsInstance, from the standard library, is reified too. What does it keep? Pause and "
                 "guess.",
    "show": "The demo prints: Gala isA<Apple>, true. The bag, false. Apples: Gala and Fuji. Lemons: Eureka. The bag and "
            "the null are simply left out.",
    "map": "Let's map it. The torn-off label is erasure. The note is the real class, written into the copy. Pinning the "
           "note to the job is inline: one copy for each call. And reified is the clerk's habit of copying the label "
           "first.",
    "break_q": "Now let's be skeptical. If inline already copies the body into the caller, isn't that enough? Why the extra "
               "word? Remove reified, keep inline, and compile it. Pause and guess.",
    "break": "It doesn't compile: cannot check for instance of erased type T. Copying the body isn't the same as copying "
             "the label. Without reified, the copy still says T, and T is still erased. So you need both: a copy for "
             "each call, and a note on each copy.",
    "rule1": "The other rules follow from the picture. Reified without inline? Only type parameters of inline functions "
             "can be reified. That's a clerk with no job to pin the note to.",
    "rule2": "And this one matters most. A generic function with an ordinary T tries to pass it along: x dot isA<T>. "
             "Kotlin says: cannot use T as reified type parameter. Use a class instead. That caller's own label is "
             "already gone, so there's nothing to copy onto the note.",
    "rule3": "So the requirement spreads upward. The caller must be inline with a reified T too, or it must pass a real "
             "class, the way Java does.",
    "name": "Now the names, in one breath each. inline copies a function's body into each place that calls it. reified "
            "writes the caller's real class into that copy. Inside, you get back what erasure took away: is T, as T, "
            "and T::class.",
    "guard": "And the guardrail: the note has room for one word. filterIsInstance of List<String> keeps every list, even a "
             "list of weights, because after inlining the check is only instanceof List. The demo prints both lists. So "
             "use reified for the outer class: checks, casts and class tokens.",
    "moral": "So, where did Apple go? The compiler saw it, checked it, and erased it. Make the function inline and T "
             "reified, and the compiler copies the label onto a note at every call. Ask T what it is, and it can finally "
             "answer.",
    "check": "Quick check. nameOf is inline, with a reified T, and returns the simple name of T's class. What does "
             "nameOf<Lemon> print?",
    "check_a": "Lemon. The note at that call says Lemon, and the demo prints exactly that.",
}


class Gen08Reified(Narrated):
    """gen-08, section 1 (with the erasure set-up of section 0): the clerk who checks the label and tears it off; boxes
    on the shelf look alike; erasure in code and ErasureDemo's output; is List<String> is refused; the shy question
    (where did Apple go?); a second clerk copies the label onto a note; inline copies the body into each caller;
    reified writes the real class in; isA in Kotlin and Class.isInstance in Java; the call becomes instanceof;
    ReifiedDemo's real output; the map; inline alone is not enough (broken on purpose); the two rules and the
    requirement spreading upward; the names; the guardrail (the note has room for one word); moral; a check."""

    def construct(self):
        self.title_card("Reified type parameters", "a clerk who copies the label onto a note")

        # ================= the clerk tears the label off =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-2.6, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-1.1, FL + 0.75, 0])
        bx = crate(2.0, 1.3, ["Box of apples"], 20).move_to([-5.4, FL + 0.65, 0])
        chk = tick(True, 0.2).next_to(clerk, UP, buff=0.2)
        shelf = Line([2.0, FL + 1.6, 0], [6.4, FL + 1.6, 0], stroke_width=4, color=GREY_B)
        self.say("open")
        self.play(Create(floor), Create(dr), FadeIn(clerk), FadeIn(bx), run_time=0.8)
        self.at(1)
        self.play(bx.animate.move_to([-4.4, FL + 0.65, 0]), run_time=0.8)
        self.play(Indicate(bx[3], color=WHITE, scale_factor=1.1), FadeIn(chk), run_time=0.7)
        self.at(2)
        lab = bx[3]
        self.play(lab.animate.shift(UP * 1.0 + LEFT * 0.4).rotate(0.4), run_time=0.5)
        self.play(lab.animate.shift(DOWN * 2.2 + LEFT * 0.6).set_opacity(0), FadeOut(chk), run_time=0.7)
        self.play(VGroup(bx[0], bx[1], bx[2]).animate.move_to([3.2, FL + 0.65, 0]), Create(shelf), run_time=0.8)
        self.hold()

        b2 = plain_box().move_to([5.4, FL + 0.65, 0])
        bq = paper(["are you a box", "of apples?"], 20).move_to([4.3, 1.6, 0])
        nol = T("no label left to read", 24, BAD).move_to([4.3, 2.8, 0])
        self.say("open2")
        self.play(FadeIn(b2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nol), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= erasure in code =================
        jc = code_block(["List<String> varieties = new ArrayList<>();",
                         "List<Integer> weights = new ArrayList<>();",
                         "varieties.getClass() == weights.getClass()"], 22)
        kc = code_block(["val varieties = ArrayList<String>()",
                         "val weights = ArrayList<Int>()",
                         "varieties.javaClass == weights.javaClass"], 22)
        fit(jc, 6.1)
        fit(kc, 6.1)
        jg = titled(jc, "Java").move_to([-3.3, 2.3, 0])
        kg = titled(kc, "Kotlin").move_to([3.3, 2.3, 0]).align_to(jg, UP)
        nm = VGroup(T("type erasure", 36, BAD), T("check every type argument, then leave it out", 26, GREY_A)).arrange(DOWN, buff=0.12).move_to([0, 0.2, 0])
        out = term(["same class at run time: true (java.util.ArrayList)"], 22, "ErasureDemo, real output").move_to([0, -1.6, 0])
        self.say("code0")
        self.play(FadeIn(nm[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nm[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()

        e1 = VGroup(M("x is List<String>", 24, WHITE), err_line("cannot check for instance of erased type 'List<String>'.", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        e2 = VGroup(M("x is T", 24, WHITE), T("fails the same way", 22, BAD)).arrange(RIGHT, buff=0.4)
        eg = VGroup(e1, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(eg, 12.4).move_to([0, -2.85, 0])
        self.say("fail0")
        self.play(FadeOut(out), run_time=0.3)
        self.at(1)
        self.play(FadeIn(e1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(e2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = VGroup(T("I typed", 34, GREY_A), M("Apple", 34, APPLE), T("right there, in", 34, GREY_A), M("isA<Apple>()", 34, WHITE)).arrange(RIGHT, buff=0.22)
        q2 = T("The compiler saw it. So where did it go?", 34)
        q3 = T("Why can't my function just ask T what it is?", 34, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.38).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= a second clerk: the note =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-3.4, FL + 1.4, 0])
        clerk = who(CLERK, "second clerk", 1.1, 22).move_to([-1.9, FL + 0.75, 0])
        bx = crate(1.9, 1.2, ["Box of apples"], 20).move_to([-5.3, FL + 0.6, 0])
        nt = note(["this job:", "apples"], 20).next_to(clerk, UP, buff=0.35)
        worker = who(BACK, "shop floor", 1.1, 22).move_to([4.8, FL + 0.75, 0])
        knows = T("knows the labels are about to come off", 24, GREY_A).move_to([0.6, 2.9, 0])
        self.say("clerk2")
        self.play(Create(floor), Create(dr), FadeIn(clerk), FadeIn(bx), run_time=0.8)
        self.at(1)
        self.play(FadeIn(knows), run_time=0.5)
        self.at(2)
        self.play(TransformFromCopy(bx[3], nt), run_time=1.0)
        self.play(bx[3].animate.shift(DOWN * 0.6).set_opacity(0), run_time=0.5)
        self.play(nt.animate.scale(0.85).next_to(bx[0], UP, buff=0.12), run_time=0.6)
        self.at(3)
        self.play(VGroup(bx[0], bx[1], bx[2], nt).animate.shift(RIGHT * 5.0), FadeIn(worker), run_time=1.2)
        rd = T("reads the note", 22, OK).next_to(worker, UP, buff=0.3)
        self.play(FadeIn(rd), Indicate(nt, color=NOTE, scale_factor=1.15), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= inline: a copy for each caller =================
        shared = body_box("isA body:  this is T", GREY_A, 24).move_to([2.8, 1.5, 0])
        callers = VGroup(M("gala.isA<Apple>()", 24, WHITE), M("bag.isA<Apple>()", 24, WHITE), M("x.isA<Lemon>()", 24, WHITE))
        callers.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([-3.6, 1.5, 0])
        arrows = VGroup(*[Arrow(c.get_right(), shared.get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08) for c in callers])
        one = T("normally: one shared body, compiled once", 24, GREY_B).move_to([0, 3.2, 0])
        self.say("inline")
        self.play(FadeIn(callers), run_time=0.6)
        self.at(1)
        self.play(FadeIn(one), run_time=0.4)
        self.at(2)
        self.play(FadeIn(shared), LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.3), run_time=1.0)
        self.at(3)
        copies = VGroup(*[body_box("this is T", GREY_A, 22).next_to(c, RIGHT, buff=0.6) for c in callers])
        inl = T("inline: the body is copied into each caller", 24, OK).move_to([0, 3.2, 0])
        self.play(FadeOut(arrows), FadeOut(one), FadeIn(inl), run_time=0.5)
        self.play(*[TransformFromCopy(shared, cp) for cp in copies], run_time=1.0)
        self.play(FadeOut(shared), run_time=0.4)
        self.hold()

        knownA = VGroup(*[part(c, n).copy() for c, n in zip(callers, ("Apple", "Apple", "Lemon"))])
        self.say("inline2")
        self.play(*[Indicate(part(c, n), color=YELLOW_M, scale_factor=1.25) for c, n in zip(callers, ("Apple", "Apple", "Lemon"))], run_time=1.0)
        self.at(1)
        kn = T("the type argument is known here", 24, YELLOW_M).move_to([-3.6, -0.6, 0])
        self.play(FadeIn(kn), run_time=0.5)
        self.hold()

        real = VGroup(body_box("this is Apple", APPLE, 22), body_box("this is Apple", APPLE, 22), body_box("this is Lemon", LEMON, 22))
        for r_, cp in zip(real, copies):
            r_.move_to(cp).align_to(cp, LEFT)
        rf = T("reified: the real class is written into each copy", 24, NOTE).move_to([0, -1.6, 0])
        notes = VGroup(*[note([n], 18).scale(0.8).next_to(r_, RIGHT, buff=0.2) for r_, n in zip(real, ("Apple", "Apple", "Lemon"))])
        self.say("reified")
        self.play(FadeOut(kn), run_time=0.3)
        self.at(2)
        self.play(*[ReplacementTransform(cp, r_) for cp, r_ in zip(copies, real)], FadeIn(rf), run_time=1.0)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(n, shift=DOWN * 0.1) for n in notes], lag_ratio=0.3), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the code =================
        jc = code_block(["static boolean isA(Object x, Class<?> type) {",
                         "    return type.isInstance(x);", "}", "",
                         "isA(gala, Apple.class);   // true"], 22)
        kc = code_block(["inline fun <reified T> Any?.isA(): Boolean =",
                         "    this is T", "",
                         "gala.isA<Apple>()         // true"], 22)
        fit(jc, 12.4)
        fit(kc, 12.4)
        kg = titled(kc, "Kotlin").move_to([0, 1.9, 0])
        jg = titled(jc, "Java").next_to(kg, DOWN, buff=0.45).align_to(kg, LEFT)
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(part(kc[0], "inline").animate.set_color(OK), part(kc[0], "reifiedT").animate.set_color(NOTE), run_time=0.6)
        self.play(part(kc[1], "thisisT").animate.set_color(YELLOW_M), run_time=0.4)
        self.at(2)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.7)
        self.play(part(jc[0], "Class<?>type").animate.set_color(NOTE), part(jc[1], "type.isInstance(x)").animate.set_color(YELLOW_M), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the call becomes instanceof =================
        c0 = M("gala.isA<Apple>()", 34, WHITE).move_to([0, 2.0, 0])
        c1 = M("gala instanceof Apple", 34, APPLE).move_to([0, 0.0, 0])
        ar = Arrow(c0.get_bottom(), c1.get_top(), buff=0.2, stroke_width=4, color=GREY_B)
        al = T("copied into the caller, Apple written in", 24, GREY_A).next_to(ar, RIGHT, buff=0.3)
        bl = T("in the caller's own bytecode", 24, GREY_B).next_to(c1, DOWN, buff=0.3)
        rc = T("a real check, on a real class", 28, OK).move_to([0, -2.2, 0])
        self.say("figure")
        self.play(FadeIn(c0), run_time=0.5)
        self.at(1)
        self.play(Indicate(c0, color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(ar), FadeIn(al), run_time=0.6)
        self.at(3)
        self.play(TransformFromCopy(c0, c1), FadeIn(bl), run_time=0.9)
        self.at(4)
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= predict, then show =================
        dl = VGroup(vchip("Gala", APPLE, 24), vchip('"a paper bag"', GREY_B, 24), vchip("null", GREY_B, 24),
                    vchip("Eureka", LEMON, 24), vchip("Fuji", APPLE, 24)).arrange(RIGHT, buff=0.3)
        fit(dl, 12.4).move_to([0, 2.6, 0])
        dlh = T("the delivery", 22, GREY_B).next_to(dl, UP, buff=0.15)
        qs = VGroup(M("delivery[0].isA<Apple>()", 24, WHITE), M("delivery[1].isA<Apple>()", 24, WHITE),
                    M("delivery.filterIsInstance<Apple>()", 24, WHITE), M("delivery.filterIsInstance<Lemon>()", 24, WHITE))
        qs.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-1.6, 0.4, 0])
        self.say("predict_q")
        self.play(FadeIn(dlh), LaggedStart(*[FadeIn(d, shift=DOWN * 0.1) for d in dl], lag_ratio=0.25), run_time=1.4)
        self.at(1)
        self.play(FadeIn(qs[0]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(qs[1]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(qs[2]), FadeIn(qs[3]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        out = term(["Gala isA<Apple>() = true, the bag isA<Apple>() = false", "apples: [Gala, Fuji]", "lemons: [Eureka]"], 22,
                   "ReifiedDemo, real output")
        fit(out, 12.4).move_to([0, -2.3, 0])
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out[1][1], shift=RIGHT * 0.1), Indicate(dl[0], color=APPLE), Indicate(dl[4], color=APPLE), run_time=0.7)
        self.at(3)
        self.play(FadeIn(out[1][2], shift=RIGHT * 0.1), Indicate(dl[3], color=LEMON), run_time=0.6)
        self.at(4)
        self.play(dl[1].animate.set_opacity(0.3), dl[2].animate.set_opacity(0.3), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the map =================
        rows = [("the torn-off label", "erasure"), ("the note", "the real class, written into the copy"),
                ("pinning the note to the job", "inline: one copy for each call"), ("copying the label first", "reified")]
        mp = VGroup(*[VGroup(T(a, 28, GREY_A), M("->", 24, GREY_B), T(b, 28, WHITE)).arrange(RIGHT, buff=0.3) for a, b in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        mp[1][2].set_color(NOTE)
        mp[2][2].set_color(OK)
        mp[3][2].set_color(NOTE)
        fit(mp, 12.4).move_to([0, 0.4, 0])
        mph = T("Let's map it", 28, GREY_B).next_to(mp, UP, buff=0.5)
        self.say("map")
        self.play(FadeIn(mph), run_time=0.4)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= break it: inline alone =================
        k = code_block(["inline fun <T> Any?.isA(): Boolean = this is T"], 28)
        fit(k, 12.4).move_to([0, 2.4, 0])
        gone = VGroup(M("reified", 26, NOTE), T("removed", 24, GREY_B)).arrange(RIGHT, buff=0.2).next_to(k, DOWN, buff=0.3)
        self.say("break_q")
        self.at(3)
        self.play(FadeIn(k), FadeIn(gone), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        er = err_line("cannot check for instance of erased type 'T (of fun <T> Any?.isA)'.", 24)
        fit(er, 12.4).move_to([0, 0.6, 0])
        cpy = VGroup(body_box("this is T", GREY_A, 22), T("a copy, but it still says T", 24, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -0.8, 0])
        both = VGroup(VGroup(M("inline", 28, OK), T("a copy for each call", 26)).arrange(RIGHT, buff=0.25),
                      VGroup(M("reified", 28, NOTE), T("a note on each copy", 26)).arrange(RIGHT, buff=0.25)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        both.move_to([0, -2.6, 0])
        self.say("break")
        self.play(FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cpy), run_time=0.6)
        self.at(3)
        self.play(FadeIn(both, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the rules =================
        r1 = VGroup(M("fun <reified T> notInline(x: Any) = x is T", 24, WHITE),
                    err_line("only type parameters of inline functions can be reified.", 22),
                    T("a clerk with no job to pin the note to", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        r2 = VGroup(M("fun <T> forward(x: Any) = x.isA<T>()", 24, WHITE),
                    err_line("cannot use 'T' as reified type parameter. Use a class instead.", 22),
                    T("the caller's own label is already gone", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        rr = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(rr, 12.4).move_to([0, 1.2, 0])
        self.say("rule1")
        self.at(1)
        self.play(FadeIn(r1[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r1[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r1[2]), run_time=0.4)
        self.hold()
        self.say("rule2")
        self.at(1)
        self.play(FadeIn(r2[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r2[1], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(r2[2]), run_time=0.4)
        self.hold()

        up = VGroup(T("so the caller must be", 24, GREY_A), M("inline <reified T>", 24, OK), T("too, or pass a real class", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        fit(up, 12.4).move_to([0, -2.6, 0])
        upar = Arrow([0, -2.2, 0], [0, -1.4, 0], stroke_width=4, color=YELLOW_M, buff=0)
        upar.next_to(up, UP, buff=0.1)
        self.say("rule3")
        self.play(GrowArrow(upar), FadeIn(up, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(M("inline", 40, OK), T("copies a function's body into each place that calls it", 26)).arrange(RIGHT, buff=0.4)
        n2 = VGroup(M("reified", 40, NOTE), T("writes the caller's real class into that copy", 26)).arrange(RIGHT, buff=0.4)
        n3 = VGroup(T("inside, back again:", 26, GREY_A), M("is T", 28, WHITE), M("as T", 28, WHITE), M("T::class", 28, WHITE)).arrange(RIGHT, buff=0.4)
        ng = VGroup(n1, n2, n3).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.5, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(n3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the guardrail: one word =================
        nt = note(["List"], 26).move_to([-4.6, 1.0, 0])
        nl = T("room for one word", 24, NOTE).next_to(nt, DOWN, buff=0.2)
        code = VGroup(M('val boxes: List<Any> = listOf(listOf(180, 150), listOf("Gala"), "Fuji")', 22, WHITE),
                      M("boxes.filterIsInstance<List<String>>()", 22, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(code, 12.4).move_to([0, 2.8, 0])
        out = term(["lists of names? [[180, 150], [Gala]]"], 24, "LimitsDemo, real output").move_to([1.8, 0.9, 0])
        only = VGroup(T("after inlining, the check is only", 24, GREY_A), M("instanceof List", 26, BAD)).arrange(RIGHT, buff=0.2).move_to([0, -1.4, 0])
        use = T("use reified for the outer class: checks, casts, class tokens", 28, YELLOW_M).move_to([0, -2.7, 0])
        fit(use, 12.4)
        self.say("guard")
        self.play(FadeIn(nt, shift=DOWN * 0.1), FadeIn(nl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.6)
        self.at_text("because after", lead=0.3)
        self.play(FadeIn(only, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(out[1][0], "[180,150]"), color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(use, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("So, where did Apple go?", 34)
        m1 = T("The compiler saw it, checked it, and erased it.", 30, GREY_A)
        m2 = T("inline + reified: the label is copied onto a note at every call.", 30, OK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("inline fun <reified T : Any> nameOf(): String =", 26, WHITE)).arrange(RIGHT, buff=0.25)
        qc2 = M("T::class.java.simpleName", 26, WHITE).next_to(qc[1], DOWN, buff=0.12).align_to(qc[1], LEFT).shift(RIGHT * 0.6)
        qc3 = VGroup(M("nameOf<Lemon>()", 28, LEMON), T("prints?", 28)).arrange(RIGHT, buff=0.25)
        qg = VGroup(VGroup(qc, qc2), qc3).arrange(DOWN, buff=0.3)
        fit(qg, 12.4).move_to(DOWN * 0.3)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(term(["nameOf<Lemon>() = Lemon"], 24, "ReifiedDemo, real output"), note(["Lemon"], 22)).arrange(RIGHT, buff=0.5).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
