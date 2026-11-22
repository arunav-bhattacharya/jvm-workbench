from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bmakeCounter\b", "make counter"), (r"Ref\$IntRef", "ref int ref"), (r"\bincrementAndGet\b", "increment and get"),
    (r"\bAtomicLong\b", "atomic long"), (r"\bAtomicInteger\b", "atomic integer"), (r"\+= 1", "plus equals one"),
    (r"\+\+count", "plus plus count"), (r"\breadyInAnHour\b", "ready in an hour"),
]

# every spoken line, in order
N = {
    "open": "Earlier in this lesson, each check became a value, like a card from a recipe drawer. You can hold it, keep "
            "it in a list, and lend it to a friend. Now pin a note to one card: my oven runs hot, take five minutes "
            "off. The note was written where the card was made, and it goes wherever the card goes.",
    "shyq": "Here's a question that's easy to be shy about. A lambda uses a variable from the function that made it. "
            "But that function has already returned. So where does the variable live now? And if two people hold the "
            "card, does each of them get their own note?",
    "shrink": "Let's shrink it to the smallest closure there is. makeCounter has a local variable, count, starting at "
              "zero. It returns a lambda that adds one to count and hands it back. Call that lambda three times, and "
              "you get 1, 2, 3. So count is still alive, after makeCounter has returned.",
    "java": "Java won't even compile the same idea. It says: local variables referenced from a lambda expression must "
            "be final or effectively final.",
    "why": "The reason is mechanical. A local variable lives in the method's stack frame, the memory one method call "
           "uses for its locals. When makeCounter returns, that frame is gone. But the lambda lives on, and it would "
           "be pointing at nothing.",
    "javafix": "So Java makes you build the box yourself: a one element array, or an AtomicInteger. Either one is an "
               "object on the heap, the memory where objects live for as long as something points at them.",
    "kotlin": "Kotlin builds that box for you, silently. The compiler moves count into a small heap object, a "
              "Ref$IntRef, with one field called element. makeCounter and the lambda both use that one field.",
    "field": "And the field is a plain int: no volatile, no lock. Java refuses the capture. The Kotlin compiler shrugs "
             "and builds the box. So the point really is: the note isn't written on the card. It sits in a box, and "
             "the card points at the box.",
    "map": "Let's map it. The card is the lambda's code. The note is the captured variable. Pinning the note on is "
           "capturing it. And the box on the heap is where the note really lives.",
    "breaks": "Here the card picture breaks, and it breaks in a way that matters. Lend a paper card, and your friend "
              "gets their own copy of the note. Hand out a closure, and everyone holds the same box.",
    "race": "On one thread, that's fine. A thread is one path of work through a program, and several can run at the "
            "same moment. So let's share one closure between four threads. Each one does total += 1, a quarter of a "
            "million times. Four quarters make a million.",
    "race_q": "What does total hold when all four are done?",
    "rmw": "Here's the catch. total += 1 is three steps: read the field, add one, write it back. Two threads read the "
           "same old value, say 41. Both add one. Both write 42. Two additions, and only one counted.",
    "result": "The lesson's demo ran it ten times on a busy four core machine. Run 1 got 250,956. It lost 749,044. "
              "Runs 2 to 10 were all exactly right.",
    "joke": "Well. Three quarters of the count are gone, and nine runs out of ten look perfect. That's the worst kind "
            "of race: it passes most of your tests. Kotlin compiled all of it without a word, because nothing in the "
            "source looks shared. The sharing comes from the box.",
    "name": "Now the name. Code plus the variables it captured is called a closure. And a captured var becomes one "
            "shared box. Everyone holding the closure writes on the same note.",
    "fix": "There are two fixes. One: share a thread safe object instead of a var. Capture a val that holds an "
           "AtomicLong, and call incrementAndGet, one step that can't be split. Two, and better: don't share at all. "
           "Let each task count its own work, and add up the results at the end. Both print exactly a million, "
           "every run.",
    "guard": "So here's the rule. A captured var is one box that everyone holding the closure shares. Never change it "
             "from two threads. In your own code, look for a var declared just before a lambda that runs somewhere "
             "else: inside submit, inside thread, or in a callback.",
    "moral": "So, where does the variable live once the function returns? In a box on the heap. And two people holding "
             "the card don't get two notes. They share one.",
    "check": "Quick check. a and b come from two separate calls to makeCounter. You call a, then a, then b. What does "
             "b return?",
    "check_a": "1. Each call to makeCounter makes its own box. Sharing happens only when one closure is shared.",
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


NOTE, BOXC = GOLD_M, GOLD_M
THR = [BLUE_M, GREEN_M, PURPLE_M, TEAL_M]
fg.SAY[:0] = [(r"Ref\$LongRef", "ref long ref")]


def sticky(lines, color=NOTE, size=20, w=1.9):
    t = VGroup(*[T(l, size, color) for l in lines]).arrange(DOWN, buff=0.08)
    r = Square(side_length=w).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    r.stretch_to_fit_height(max(0.8, t.height + 0.35))
    r.stretch_to_fit_width(max(w, t.width + 0.35))
    return VGroup(r, t.move_to(r)).set_z_index(5)


def heap_box(title, field, w=3.6):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=1.25).set_stroke(BOXC, 3).set_fill(dim(BOXC, 0.12), 1)
    t1 = M(title, 24, BOXC).move_to(r.get_center() + UP * 0.27)
    t2 = M(field, 24).move_to(r.get_center() + DOWN * 0.25)
    return VGroup(r, t1, t2)


class Fp02Closures(Narrated):
    """fp-02, section 3: a closure keeps its variables, and a captured var becomes one shared box. Cards from the
    drawer and a pinned note; makeCounter; Java's compile error and the vanished stack frame; the hand-made box
    and Kotlin's Ref$IntRef; the map; the picture breaks (a paper copy vs one shared box); four threads and a
    read-add-write; the lesson's run (250,956, lost 749,044); the name; two fixes; the rule; a check."""

    def construct(self):
        self.title_card("One note, many hands", "closures and the captured var")

        # ================= cards from the drawer, and a pinned note =================
        names = [("ready in an hour", ["no dish over 60 min"]), ("autumn only", ["pumpkin, leek, apple"]),
                 ("meat free", ["for Sam"])]
        cards = VGroup(*[recipe_card(a, b, w=3.3, size=22) for a, b in names]).arrange(RIGHT, buff=0.6).move_to([0, 0.9, 0])
        lst = T("a list of checks: values you can hold", 28, CARD).move_to([0, -0.8, 0])
        friend = person(COOK, 1.1).move_to([4.6, -2.2, 0])
        note = sticky(["my oven runs hot:", "take 5 min off"]).move_to(cards[0].get_corner(UR) + UP * 0.35 + LEFT * 0.1)
        note.rotate(-0.08)
        self.say("open")
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cards], lag_ratio=0.25), run_time=1.3)
        self.at(1)
        self.play(FadeIn(lst), run_time=0.5)
        self.play(FadeIn(friend), cards[2].animate.scale(0.7).move_to([3.0, -2.1, 0]), run_time=1.0)
        self.at(2)
        self.play(FadeOut(lst), FadeIn(note, shift=DOWN * 0.2, scale=0.8), run_time=0.7)
        self.at(3)
        g0 = VGroup(cards[0], note)
        self.play(g0.animate.shift(DOWN * 1.8 + RIGHT * 0.2), run_time=1.0)
        self.play(g0.animate.shift(UP * 1.8 + LEFT * 0.2), run_time=0.8)
        self.hold()

        q = T("The function has returned. Where does the variable live now?", 32).move_to([0, -2.9, 0])
        fit(q, 11.6)
        self.say("shyq")
        self.play(FadeOut(friend), FadeOut(cards[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.wipe()

        # ================= makeCounter =================
        hl = {"count": NOTE, "makeCounter": CARD}
        kc = code_block(["fun makeCounter(): () -> Int {", "    var count = 0", "    return { ++count }", "}"], 28, hl)
        kl = T("Kotlin", 24, GREY_B)
        kg = VGroup(kl, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-3.0, 1.2, 0])
        calls = VGroup(M("val c = makeCounter()", 26), M("c()   1", 26), M("c()   2", 26), M("c()   3", 26))
        calls.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([3.4, 1.2, 0])
        for x in calls[1:]:
            x[3:].set_color(OUT)
        alive = T("count is still alive after makeCounter returned", 28, NOTE).move_to([0, -1.5, 0])
        self.say("shrink")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(kc[1], color=NOTE, scale_factor=1.05), run_time=0.8)
        self.at(2)
        self.play(Indicate(kc[2], color=CARD, scale_factor=1.05), run_time=0.8)
        self.at(3)
        self.play(FadeIn(calls[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in calls[1:]], lag_ratio=0.5), run_time=1.5)
        self.at(4)
        self.play(FadeIn(alive), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(calls, alive)), kg.animate.move_to([-3.6, 2.2, 0]).scale(0.8), run_time=0.7)

        jc = code_block(["static IntSupplier makeCounter() {", "    int count = 0;", "    return () -> ++count;", "}"], 26,
                        {"count": NOTE})
        jl = T("Java", 24, GREY_B)
        jg = VGroup(jl, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.0, 1.95, 0])
        err = T("local variables referenced from a lambda expression must be final or effectively final", 24, HIDDEN)
        fit(err, 12.4).move_to([0, -0.1, 0])
        xj = cross(jc[2])
        self.say("java")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Create(xj), FadeIn(err), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the stack frame goes away =================
        stack = RoundedRectangle(corner_radius=0.12, width=4.0, height=2.6).set_stroke(GREY_B, 2.5).move_to([-4.0, 0.6, 0])
        stack_l = T("the stack", 24, GREY_B).next_to(stack, UP, buff=0.15)
        fr = VGroup(RoundedRectangle(corner_radius=0.08, width=3.4, height=1.1).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.15), 1),
                    M("makeCounter()", 24, CARD), M("count = 0", 24, NOTE))
        fr[1].move_to(fr[0].get_center() + UP * 0.22)
        fr[2].move_to(fr[0].get_center() + DOWN * 0.24)
        fr.move_to(stack.get_center() + DOWN * 0.5)
        lam = VGroup(RoundedRectangle(corner_radius=0.12, width=3.0, height=1.1).set_stroke(CARD, 3).set_fill(dim(CARD, 0.12), 1),
                     T("the lambda", 24, CARD), M("{ ++count }", 24))
        lam[1].move_to(lam[0].get_center() + UP * 0.22)
        lam[2].move_to(lam[0].get_center() + DOWN * 0.24)
        lam.move_to([3.8, 0.1, 0])
        ptr = Arrow(lam.get_left(), fr[2].get_right(), buff=0.12, stroke_width=3, color=NOTE)
        gone = T("frame gone", 26, HIDDEN).move_to(fr)
        qm = T("?", 44, HIDDEN).move_to(fr.get_right() + RIGHT * 0.5)
        self.say("why")
        self.play(FadeIn(stack), FadeIn(stack_l), run_time=0.5)
        self.at_text("stack frame", lead=0.3)
        self.play(FadeIn(fr, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(lam), GrowArrow(ptr), run_time=0.8)
        self.at(2)
        self.play(FadeOut(fr, shift=UP * 0.3), FadeIn(gone), run_time=0.9)
        self.at(3)
        self.play(ptr.animate.set_color(HIDDEN), FadeIn(qm), Wiggle(lam, scale_value=1.05), run_time=1.0)
        self.hold()

        heap = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=5.4, height=2.1), num_dashes=60).set_stroke(GREY_C, 2)
        heap.move_to([0.4, -1.8, 0])
        heap_l = T("the heap", 22, GREY_C).next_to(heap, LEFT, buff=0.2)
        arr = heap_box("int[] count", "{ 0 }", w=3.0).move_to(heap)
        jfix = M("int[] count = {0};  // build the box yourself", 24, GREY_A).move_to([0.4, 2.9, 0])
        fit(jfix, 12.0)
        ptr2 = Arrow(lam.get_bottom(), arr.get_right() + UP * 0.1, buff=0.12, stroke_width=3, color=NOTE)
        self.say("javafix")
        self.play(FadeOut(qm), FadeOut(ptr), FadeIn(jfix), run_time=0.6)
        self.at(1)
        self.play(FadeIn(heap), FadeIn(heap_l), FadeIn(arr, shift=UP * 0.1), GrowArrow(ptr2), run_time=1.0)
        self.hold()

        ref = heap_box("Ref$IntRef", "int element = 0").move_to(heap)
        fr2 = fr.copy().set_opacity(1)
        kfix = T("Kotlin: the compiler builds the box", 26, GREY_A).move_to(jfix)
        ptr3 = Arrow(fr2.get_bottom(), ref.get_left() + UP * 0.1, buff=0.12, stroke_width=3, color=NOTE)
        self.say("kotlin")
        self.play(FadeOut(jfix), FadeIn(kfix), FadeOut(gone), FadeIn(fr2), run_time=0.7)
        self.at(1)
        self.play(ReplacementTransform(arr, ref), run_time=0.9)
        self.at(2)
        self.play(Indicate(ref[1], color=BOXC), run_time=0.8)
        self.play(GrowArrow(ptr3), ptr2.animate.put_start_and_end_on(lam.get_bottom() + DOWN * 0.12, ref.get_right() + UP * 0.1 + RIGHT * 0.12), run_time=0.8)
        self.hold()

        plain = T("a plain field: no volatile, no lock", 26, HIDDEN).move_to([0.4, -3.2, 0])
        self.say("field")
        self.play(Indicate(ref[2], color=HIDDEN), FadeIn(plain), run_time=1.0)
        self.at(1)
        jr = T("Java: refuses.", 28, GREY_A)
        kr = T("Kotlin: shrugs, and builds the box.", 28, GOLD_M)
        VGroup(jr, kr).arrange(RIGHT, buff=0.5).move_to([0.4, 2.9, 0])
        self.play(FadeOut(kfix), FadeIn(jr), run_time=0.4)
        self.at(2)
        self.play(FadeIn(kr), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= map =================
        hp = T("the kitchen", 28, GREY_B).move_to([-3.3, 2.7, 0])
        hc = T("the code", 28, GREY_B).move_to([3.0, 2.7, 0])
        rows = [("the card", "the lambda's code", CARD), ("the note", "the captured variable", NOTE),
                ("pinning the note on", "capturing it", NOTE), ("where the note lives", "a box on the heap", BOXC)]
        Y = [1.6, 0.6, -0.4, -1.4]
        mrows = VGroup()
        for (a, b, c), y in zip(rows, Y):
            ta = T(a, 28, c).move_to([-3.3, y, 0])
            tb = T(b, 28, c).move_to([3.0, y, 0])
            ln = Arrow([-0.6, y, 0], [1.0, y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.15)
            mrows.add(VGroup(ta, ln, tb))
        self.say("map")
        self.play(FadeIn(hp), FadeIn(hc), run_time=0.5)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mrows[i], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the picture breaks =================
        pl = T("a paper card", 28, GREY_A).move_to([-3.6, 2.6, 0])
        pc1 = recipe_card("card", ["the recipe"], w=2.0, size=20).move_to([-4.9, 0.8, 0])
        pc2 = pc1.copy().move_to([-2.3, 0.8, 0])
        n1 = sticky(["note"], w=1.0, size=20).move_to(pc1.get_corner(UR) + UP * 0.32 + LEFT * 0.1)
        n2 = sticky(["copy"], w=1.0, size=20).move_to(pc2.get_corner(UR) + UP * 0.32 + LEFT * 0.1)
        pf = T("each friend: their own copy", 26, CARD).move_to([-3.6, -0.9, 0])
        cl = T("a closure", 28, GREY_A).move_to([3.4, 2.6, 0])
        h1 = person(THR[0], 0.9).move_to([1.9, 1.0, 0])
        h2 = person(THR[2], 0.9).move_to([4.9, 1.0, 0])
        one = heap_box("one box", "count", w=2.4).move_to([3.4, -1.0, 0])
        a1 = Arrow(h1.get_bottom(), one.get_top() + LEFT * 0.4, buff=0.12, stroke_width=3, color=NOTE)
        a2 = Arrow(h2.get_bottom(), one.get_top() + RIGHT * 0.4, buff=0.12, stroke_width=3, color=NOTE)
        cf = T("everyone: the same box", 26, HIDDEN).move_to([3.4, -2.3, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(pl), FadeIn(pc1), FadeIn(n1), run_time=0.6)
        self.play(TransformFromCopy(VGroup(pc1, n1), VGroup(pc2, n2)), run_time=0.9)
        self.play(FadeIn(pf), run_time=0.4)
        self.at(2)
        self.play(FadeIn(cl), FadeIn(h1), FadeIn(h2), FadeIn(one), run_time=0.6)
        self.play(GrowArrow(a1), GrowArrow(a2), run_time=0.6)
        self.play(FadeIn(cf), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= four threads, one box =================
        tb = heap_box("Ref$LongRef", "total = 0", w=3.4).move_to([0, 0.3, 0])
        ths = VGroup(*[chip(f"thread {c}", THR[i], 26) for i, c in enumerate("ABCD")])
        pos = [[-4.6, 1.9, 0], [4.6, 1.9, 0], [-4.6, -1.3, 0], [4.6, -1.3, 0]]
        for t, p in zip(ths, pos):
            t.move_to(p)
        tarr = VGroup(*[edge_arrow(t, tb, color=THR[i]) for i, t in enumerate(ths)])
        each = M("repeat(250_000) { total += 1 }", 26).move_to([0, 2.8, 0])
        exp = T("expected: 4 x 250,000 = 1,000,000", 28, OUT).move_to([0, -2.6, 0])
        self.say("race")
        self.play(FadeIn(tb), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(t) for t in ths], lag_ratio=0.2), run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in tarr], lag_ratio=0.2), run_time=0.9)
        self.at(3)
        self.play(FadeIn(each), run_time=0.5)
        self.at(4)
        self.play(FadeIn(exp), run_time=0.5)
        self.hold()
        self.say("race_q")
        self.play(Indicate(tb[2], color=BOXC), run_time=0.9)
        self.hold(after=0)
        self.predict()
        self.wipe()

        # ================= read, add, write =================
        box = heap_box("total", "41", w=2.4).move_to([0, 1.6, 0])
        colA = VGroup(T("thread A", 26, THR[0]), T("read 41", 26), T("add 1: 42", 26), T("write 42", 26))
        colB = VGroup(T("thread B", 26, THR[1]), T("read 41", 26), T("add 1: 42", 26), T("write 42", 26))
        for c, x in ((colA, -4.3), (colB, 4.3)):
            c.arrange(DOWN, buff=0.35).move_to([x, 0.2, 0])
        three = T("total += 1 is three steps: read, add, write", 26, GREY_A).move_to([0, 3.0, 0])
        lost = T("two additions, one counted", 30, HIDDEN).move_to([0, -2.6, 0])
        self.say("rmw")
        self.play(FadeIn(three), FadeIn(box), run_time=0.6)
        self.at(1)
        self.play(FadeIn(colA[0]), FadeIn(colB[0]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(colA[1]), FadeIn(colB[1]), Indicate(box[2], color=BOXC), run_time=0.8)
        self.at(3)
        self.play(FadeIn(colA[2]), FadeIn(colB[2]), run_time=0.6)
        self.at(4)
        new = M("42", 24).move_to(box[2])
        self.play(FadeIn(colA[3]), FadeIn(colB[3]), Transform(box[2], new), run_time=0.8)
        self.at(5)
        self.play(FadeIn(lost, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the real run =================
        rl = T("CapturedRace, one try in the lesson (busy 4-core machine)", 24, GREY_B).move_to([0, 2.5, 0])
        out = VGroup(M("run  1: expected 1,000,000, got   250,956 (lost 749,044)", 24),
                     M("run  2: expected 1,000,000, got 1,000,000 (lost 0)", 24),
                     M("run  3: expected 1,000,000, got 1,000,000 (lost 0)", 24),
                     T("runs 4 to 10: all 1,000,000", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(out, 12.2).move_to([0, 1.0, 0])
        out[0].set_color(HIDDEN)
        self.say("result")
        self.play(FadeIn(rl), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[0]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(out[1:]), run_time=0.8)
        self.hold()
        w1 = T("Three quarters gone; nine runs out of ten look perfect.", 30, GOLD_M).move_to([0, -1.2, 0])
        w2 = T("Nothing in the source looks shared. The box is shared.", 28, GREY_A).move_to([0, -2.1, 0])
        fit(w1, 12.4)
        self.say("joke")
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name it =================
        nm = T("a closure", 44, PURE).move_to([0, 1.8, 0])
        d1 = T("code, plus the variables it captured", 30).next_to(nm, DOWN, buff=0.3)
        d2 = T("a captured var: one shared box", 30, NOTE).next_to(d1, DOWN, buff=0.5)
        self.say("name")
        self.play(Write(nm), run_time=0.9)
        self.play(FadeIn(d1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(d2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= two fixes =================
        f1h = T("1. share a thread-safe object", 28, CARD)
        f1k = code_block(["val total = AtomicLong()", "repeat(250_000) { total.incrementAndGet() }"], 24)
        f1j = VGroup(T("Java", 20, GREY_B), M("AtomicLong total = new AtomicLong();", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        f1 = VGroup(f1h, f1k, f1j).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        f2h = T("2. better: don't share", 28, OUT)
        f2k = code_block(["pool.submit(Callable {", "    var mine = 0L", "    repeat(250_000) { mine += 1 }", "    mine", "})",
                          "tasks.sumOf { it.get() }"], 24)
        f2 = VGroup(f2h, f2k).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fx = VGroup(f1, f2).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(fx, 12.4).move_to([-0.2, 0.35, 0])
        both = T("both: exactly 1,000,000, every run", 28, OUT).move_to([0, -3.2, 0])
        self.say("fix")
        self.at(1)
        self.play(FadeIn(f1h), run_time=0.4)
        self.at_text("Capture a val", lead=0.3)
        self.play(FadeIn(f1k), FadeIn(f1j), run_time=0.7)
        self.at(3)
        self.play(FadeIn(f2h), run_time=0.4)
        self.at(4)
        self.play(FadeIn(f2k), run_time=0.8)
        self.at(5)
        self.play(FadeIn(both), run_time=0.5)
        self.hold()
        self.wipe()

        rule = T("A captured var is one box that everyone holding the closure shares.", 30, NOTE).move_to([0, 1.6, 0])
        rule2 = T("Never change it from two threads.", 32, HIDDEN).move_to([0, 0.8, 0])
        fit(rule, 12.4)
        look = VGroup(T("look for:", 26, GREY_B), M("var x ...", 26, NOTE), T("then a lambda inside", 26, GREY_B),
                      M("submit { }", 26), M("thread { }", 26), T("or a callback", 26, GREY_B)).arrange(RIGHT, buff=0.22)
        fit(look, 12.4).move_to([0, -0.8, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(rule), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rule2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(look, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Where does the variable live? In a box on the heap.", 32).move_to(UP * 2.4)
        m1 = T("Two people holding the card don't get two notes. They share one.", 32, NOTE).move_to(UP * 1.5)
        for m in (mq, m1):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(M("val a = makeCounter()", 26), M("val b = makeCounter()", 26), M("a(); a(); b()", 26, CARD))
        qq.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(DOWN * 0.4)
        qh = T("Check: what does b() return?", 28, PURE).next_to(qq, UP, buff=0.3)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("1: each call to makeCounter makes its own box", 28, NOTE).move_to(DOWN * 2.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
