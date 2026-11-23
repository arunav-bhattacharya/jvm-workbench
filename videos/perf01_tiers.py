from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bHotSpot\b", "Hot Spot"), (r"\bkotlinc\b", "kotlin C"), (r"\bOpenJDK\b", "Open J D K"),
    (r"\blload\b", "L load"), (r"\blmul\b", "L mul"), (r"\bCompileThreshold\b", "compile threshold"),
    (r"\bWarmupDemo\b", "warm up demo"), (r"\b2,406\b", "two thousand four hundred and six"),
]

# every spoken line, in order
N = {
    "open": "Here's a tiny program. It works out how long a document takes to read, at 238 words a minute. It "
            "does that for 20,000 documents, and times the batch. Then it runs the same batch again, twelve "
            "times in all. Same code, same data.",
    "first": "The first batch takes about a thousand microseconds. Then 713, 682, 482. A little quicker. So what "
             "will batch five take? Make a guess.",
    "five": "78 microseconds. Thirteen times faster than the first batch. And nobody changed a line.",
    "six": "Batch six is an odd one: 2,406. It showed up in most runs, even with the compiler switched off, on a "
           "machine shared by twenty busy programs. Call it a sneeze. One strange number is not a story. The "
           "shape is.",
    "shyq": "So here's the question that feels too basic to ask. Java is already compiled. So how can the same "
            "code get faster, just by running it?",
    "cook1": "Picture a new cook in a busy restaurant. On day one, every dish is cooked from its recipe card, "
             "one line at a time.",
    "cook2": "The cook also keeps tally marks: how often each dish gets ordered. Dishes ordered often earn a quick "
             "cheat sheet. And next to it, the cook takes notes on the orders: who wants extra sauce, who never "
             "wants onions.",
    "cook3": "The house favourites get practised until the cook can make them without looking, with shortcuts "
             "based on what customers usually order. Same recipes. Just a lot faster by the end of the week.",
    "map1": "Now let's map the kitchen onto the JVM, the program that runs your compiled Java and Kotlin. javac "
            "and kotlinc don't make machine code for your processor. They make bytecode: small instructions for "
            "the JVM. lload pushes a long. lmul multiplies two longs. That's the recipe card.",
    "map2": "HotSpot, the JVM in every OpenJDK build, starts every method in the interpreter: a loop that reads "
            "one bytecode at a time, and carries it out. That's the cook on day one.",
    "map3": "Meanwhile, the JVM keeps tally marks: how often each method is called, and how often each loop jumps "
            "back to its start. When the marks pass a threshold, a compiler thread turns the method into machine "
            "code, in the background. The next call runs that instead.",
    "map4": "Compiling while the program runs is called just in time compiling, or the JIT. Because it waits, it "
            "gets to see what your code really does.",
    "c1": "HotSpot has two JIT compilers. C1 compiles quickly, and optimizes a little. That's the cheat sheet. "
          "At tier 3, its code also takes notes, called a profile: which branches ran, and which types turned up "
          "at each call.",
    "c2": "C2 compiles slowly, and optimizes hard, using those notes. That's the practised dish, with shortcuts "
          "that bet on the usual orders.",
    "climb": "So the normal climb is tier 0, the interpreter. Then tier 3, after about 200 calls. Then tier 4, "
             "C2, after about 5,000 more. Loop laps count too. When the compile queue is long, the JVM raises "
             "the bar, so treat these as rough sizes.",
    "myth": "Now, you may have read that a method gets compiled after 10,000 calls. That number is real. It's "
            "called CompileThreshold, and it only applies with tiered compilation switched off. Tiered has been "
            "the default since JDK 8.",
    "myth2": "So those blog posts weren't wrong, just old. The internet remembers everything, even what stopped "
             "being true. Today's numbers are 200 and 5,000, from JDK 21 to JDK 27.",
    "take_q": "Let's test the story by taking cooks out of the kitchen. First, the interpreter only. Then C1 "
              "only: cheat sheets, but no practised dishes. What happens to the late batches? Pause and guess.",
    "take_int": "Interpreter only: every batch stays between 630 and 920 microseconds. This cook never stops "
                "reading the card.",
    "take_c1": "C1 only: 69 microseconds from batch six on. That's a touch faster than the full kitchen, at 78.",
    "take_why": "Wait. C2, the expensive one, didn't help? Not here. That's a master chef, hired to boil an egg. "
                "On a one line method, the cheat sheet is already about as good as it gets. C2 earns its slow "
                "compile on bigger code, and lesson 2 shows how.",
    "breaks": "And here's where the kitchen picture breaks. A real cook remembers yesterday. A JVM forgets "
              "everything when its process ends. So every restart is the cook's first day again.",
    "rule": "So the same code runs at different speeds, depending on how long the JVM has watched it. Never "
            "trust the first lap.",
    "guard": "Three habits follow. Measure after warm-up, or say it's a cold start. On a busy machine, read the "
             "shape, not one batch. And one call right after start is not the speed of your code.",
    "moral": "The moral of the story: your code is compiled twice. Once by javac or kotlinc, into bytecode. And "
             "again while it runs, by the JIT. The interpreter reads the card. C1 writes the cheat sheet and "
             "takes notes. C2 practises, with shortcuts.",
    "check": "Quick check. A test starts the JVM, calls a method once, and times that call. Which tier most "
             "likely ran it, and what did the test measure?",
    "check_a": "The interpreter, tier 0. It measured the cook's first day. Next, we'll ask the JVM which "
               "compiler ran, and when.",
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

    def predict(self, secs=2.4, pos=(6.4, 3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole performance track's kitchen
CARD, C1C, C2C, NOTE, COOK, BAD = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREY_A, RED_M
PAPER = "#EDE6D6"


def cook(s=1.0, color=COOK):
    body = RoundedRectangle(corner_radius=0.16, width=0.5, height=0.46).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.15).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    band = Rectangle(width=0.3, height=0.08).set_stroke(WHITE, 2).set_fill(WHITE, 1).next_to(head, UP, buff=0.01)
    puff = VGroup(*[Circle(radius=0.1).set_stroke(WHITE, 2).set_fill(WHITE, 1) for _ in range(3)]).arrange(RIGHT, buff=-0.08)
    puff.next_to(band, UP, buff=-0.05)
    return VGroup(body, head, band, puff).scale(s)


def recipe_card(lines=4, w=1.5, h=1.1, title="recipe"):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.18), 1)
    t = T(title, 18, CARD).move_to(r.get_top() + DOWN * 0.18)
    ls = VGroup(*[Line(LEFT * w * 0.36, RIGHT * w * 0.36, stroke_width=2, color=GREY_B) for _ in range(lines)])
    ls.arrange(DOWN, buff=(h - 0.45) / max(lines, 1) * 0.6).next_to(t, DOWN, buff=0.12)
    return VGroup(r, t, ls)


def cheat(w=1.1, h=0.8):
    r = Rectangle(width=w, height=h).set_stroke(C1C, 2.5).set_fill(dim(C1C, 0.3), 1).rotate(-6 * DEGREES)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=2.5, color=C1C) for _ in range(2)]).arrange(DOWN, buff=0.2)
    ls.move_to(r).rotate(-6 * DEGREES)
    return VGroup(r, ls)


def notepad(w=0.8, h=0.95):
    r = Rectangle(width=w, height=h).set_stroke(NOTE, 2.5).set_fill(dim(NOTE, 0.3), 1)
    rings = VGroup(*[Circle(radius=0.04).set_stroke(NOTE, 2) for _ in range(3)]).arrange(RIGHT, buff=0.12).move_to(r.get_top() + DOWN * 0.08)
    ls = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.8, color=NOTE) for _ in range(3)]).arrange(DOWN, buff=0.16)
    ls.move_to(r.get_center() + DOWN * 0.06)
    return VGroup(r, rings, ls)


def star(r=0.45):
    return Star(5, outer_radius=r, inner_radius=r * 0.45).set_stroke(C2C, 3).set_fill(dim(C2C, 0.5), 1)


def tally(n=7, color=GREY_A, h=0.42):
    g = VGroup()
    x = 0
    for i in range(n):
        if i % 5 == 4:
            g.add(Line([x - 0.55, -h / 2 + 0.05, 0], [x - 0.05, h / 2 - 0.05, 0], stroke_width=3, color=color))
            x += 0.18
        else:
            g.add(Line([x, -h / 2, 0], [x, h / 2, 0], stroke_width=3, color=color))
            x += 0.13
    return g.center()


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def panel(m, color=GREY_D, buff=0.3):
    return SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


BATCHES = [1002, 713, 682, 482, 78, 2406, 77, 77, 76, 118, 76, 76]


class Perf01Tiers(Narrated):
    """perf-01, section 0: the same batch gets 13 times faster (WarmupDemo); the new cook (recipe card, tally,
    cheat sheet and notes, practised favourite); the map (bytecode, interpreter, counters, JIT, C1 + profile, C2);
    the climb 0 -> 3 -> 4 at about 200 and 5,000 more; the 10,000 myth; taking cooks away (-Xint, C1 only);
    where the picture breaks (restart); the rule, the moral and a check."""

    def construct(self):
        self.title_card("Why the same code gets faster", "the interpreter, C1 and C2")

        # ================= the program and its twelve batches =================
        code = M("readingSeconds(words) = (words * 60 + 237) / 238", 26, CARD).move_to([0, 3.1, 0])
        sub = T("20,000 documents per batch, the same batch twelve times", 24, GREY_B).next_to(code, DOWN, buff=0.2)
        base_y, k, x0, dx = -2.75, 4.0 / 2406, -5.5, 1.0
        axis = Line([x0 - 0.6, base_y, 0], [x0 + 11 * dx + 0.6, base_y, 0], stroke_width=2, color=GREY_C)
        bars, vals, nums = VGroup(), VGroup(), VGroup()
        for i, v in enumerate(BATCHES):
            col = GREY_C if i == 5 else (C1C if i >= 4 else CARD)
            b = Rectangle(width=0.6, height=max(0.04, v * k)).set_stroke(col, 2).set_fill(dim(col, 0.6), 1)
            b.move_to([x0 + i * dx, base_y, 0], aligned_edge=DOWN)
            bars.add(b)
            vals.add(T(f"{v:,}", 20, col).next_to(b, UP, buff=0.08))
            nums.add(T(str(i + 1), 20, GREY_B).next_to([x0 + i * dx, base_y, 0], DOWN, buff=0.12))
        unit = T("microseconds per batch, one run, JDK 25, a busy 4-core machine", 20, GREY_B).move_to([0, -3.55, 0])
        self.say("open")
        self.play(FadeIn(code, shift=DOWN * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(sub), Create(axis), FadeIn(unit), run_time=0.8)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(n) for n in nums], lag_ratio=0.08), run_time=1.2)
        self.hold()

        self.say("first")
        for i in range(4):
            self.at_text(["thousand", "713", "682", "482"][i], lead=0.3)
            self.play(GrowFromEdge(bars[i], DOWN), FadeIn(vals[i]), run_time=0.45)
        qm = T("?", 40, YELLOW_M).next_to([x0 + 4 * dx, base_y, 0], UP, buff=0.3)
        self.play(FadeIn(qm), run_time=0.4)
        self.hold(after=0)
        self.predict()

        x13 = T("13 times faster", 28, YELLOW_M).move_to([x0 + 4 * dx + 0.3, -0.4, 0])
        same = T("nobody changed a line", 24, GREY_B).next_to(x13, DOWN, buff=0.15)
        self.say("five")
        self.play(FadeOut(qm), GrowFromEdge(bars[4], DOWN), FadeIn(vals[4]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(x13), Indicate(vals[0], color=CARD), run_time=0.8)
        self.at(2)
        self.play(FadeIn(same), run_time=0.5)
        self.hold()

        sneeze = T("a sneeze", 24, GREY_B).next_to(vals[5], RIGHT, buff=0.2)
        self.say("six")
        self.play(FadeOut(x13), FadeOut(same), GrowFromEdge(bars[5], DOWN), FadeIn(vals[5]), run_time=0.7)
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(bars[i], DOWN), FadeIn(vals[i])) for i in range(6, 12)],
                              lag_ratio=0.2), run_time=1.6)
        self.at_text("Call it", lead=0.2)
        self.play(FadeIn(sneeze), run_time=0.5)
        self.at_text("The shape", lead=0.2)
        shape = VMobject(stroke_color=YELLOW_M, stroke_width=4).set_points_smoothly(
            [bars[0].get_top() + UP * 0.45, bars[2].get_top() + UP * 0.45, bars[3].get_top() + UP * 0.45,
             bars[4].get_top() + UP * 0.45, bars[8].get_top() + UP * 0.45, bars[11].get_top() + UP * 0.45])
        self.play(Create(shape), run_time=1.2)
        self.hold()

        q1 = T("Java is already compiled.", 30)
        q2 = T("So how can the same code get faster, just by running it?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).move_to([0, 3.0, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeOut(code), FadeOut(sub), FadeOut(sneeze), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.2)
        self.wipe()

        # ================= the new cook =================
        ck = cook(1.7).move_to([-5.2, 0.2, 0])
        day = T("day one", 26, GREY_A).next_to(ck, DOWN, buff=0.25)
        card1 = recipe_card(5, 2.0, 1.9).move_to([-2.4, 0.4, 0])
        cursor = Arrow(LEFT * 0.5, ORIGIN, buff=0, stroke_width=4, color=YELLOW_M, max_tip_length_to_length_ratio=0.4)
        cursor.next_to(card1[2][0], LEFT, buff=0.1)
        self.say("cook1")
        self.play(FadeIn(ck, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(day), FadeIn(card1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(cursor), run_time=0.3)
        for j in range(1, 5):
            self.play(cursor.animate.next_to(card1[2][j], LEFT, buff=0.1), run_time=0.45)
        self.hold()

        tal = tally(9).move_to([0.9, 2.3, 0])
        tal_t = T("tally marks", 22, GREY_A).next_to(tal, UP, buff=0.15)
        sh = cheat().move_to([0.6, 0.4, 0])
        sh_t = T("cheat sheet", 22, C1C).next_to(sh, DOWN, buff=0.2)
        npd = notepad().move_to([2.2, 0.4, 0])
        np_t = T("notes on orders", 22, NOTE).next_to(npd, DOWN, buff=0.2)
        self.say("cook2")
        self.play(FadeOut(cursor), LaggedStart(*[Create(l) for l in tal], lag_ratio=0.15), FadeIn(tal_t), run_time=1.4)
        self.at(1)
        self.play(FadeIn(sh, shift=UP * 0.2), FadeIn(sh_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(npd, shift=UP * 0.2), FadeIn(np_t), run_time=0.7)
        self.hold()

        st = star(0.6).move_to([4.8, 0.45, 0])
        st_t = VGroup(T("by heart,", 22, C2C), T("with shortcuts", 22, C2C)).arrange(DOWN, buff=0.08).next_to(st, DOWN, buff=0.25)
        week = T("end of the week", 26, GREY_A).move_to([4.8, 2.3, 0])
        arr = VGroup(Arrow([-1.2, 0.4, 0], [-0.1, 0.4, 0], buff=0, stroke_width=3, color=GREY_B),
                     Arrow([2.85, 0.4, 0], [3.95, 0.4, 0], buff=0, stroke_width=3, color=GREY_B))
        self.say("cook3")
        self.play(GrowArrow(arr[0]), run_time=0.4)
        self.play(GrowArrow(arr[1]), FadeIn(st, scale=0.6), FadeIn(st_t), run_time=0.8)
        self.at(2)
        self.play(FadeIn(week), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the map, one level down: bytecode is the card =================
        jv = M("static long readingSeconds(long words) {", 22, GREY_A)
        jv2 = M("    return (words * 60 + 237) / 238; }", 22, GREY_A)
        kt = M("fun readingSeconds(words: Long): Long = (words * 60 + 237) / 238", 22, GREY_A)
        src = VGroup(VGroup(T("Java", 20, GREY_B), jv, jv2).arrange(DOWN, aligned_edge=LEFT, buff=0.1),
                     VGroup(T("Kotlin", 20, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.1)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(src, 7.6).move_to([-2.4, 2.2, 0])
        comp = T("javac, kotlinc", 22, GREY_B)
        bc_rows = ["0: lload_0", "1: ldc2_w  60", "4: lmul", "5: ldc2_w  237", "8: ladd", "9: ldc2_w  238",
                   "12: ldiv", "13: lreturn"]
        bc = code_block(bc_rows, 22, hl={"lload_0": YELLOW_M, "lmul": YELLOW_M}, color=WHITE)
        bcard = RoundedRectangle(corner_radius=0.1, width=bc.width + 0.9, height=bc.height + 0.9).set_stroke(CARD, 3)
        bcard.set_fill(dim(CARD, 0.16), 1)
        bct = T("bytecode, from javap", 20, CARD).next_to(bcard, UP, buff=0.12)
        bcg = VGroup(bcard, bc).move_to([4.3, -0.55, 0])
        bc.move_to(bcard).shift(DOWN * 0.05)
        bct.next_to(bcard, UP, buff=0.12)
        carr = Arrow(src.get_right() + DOWN * 0.3, bcard.get_left() + UP * 1.0, buff=0.2, stroke_width=3, color=GREY_B)
        comp.next_to(carr.get_center(), DOWN, buff=0.15).shift(LEFT * 0.4)
        lab_l = VGroup(M("lload", 24, YELLOW_M), T("push a long", 24)).arrange(RIGHT, buff=0.25)
        lab_m = VGroup(M("lmul", 24, YELLOW_M), T("multiply two longs", 24)).arrange(RIGHT, buff=0.25)
        labs = VGroup(lab_l, lab_m).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-3.2, -0.6, 0])
        is_card = VGroup(recipe_card(3, 1.1, 0.85), T("= the recipe card", 26, CARD)).arrange(RIGHT, buff=0.3).move_to([-3.2, -2.3, 0])
        self.say("map1")
        self.play(FadeIn(src), run_time=0.8)
        self.at(1)
        self.play(GrowArrow(carr), FadeIn(comp), FadeIn(bcard), FadeIn(bct), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(r) for r in bc], lag_ratio=0.1), run_time=1.0)
        self.at(3)
        self.play(FadeIn(lab_l), run_time=0.5)
        self.at(4)
        self.play(FadeIn(lab_m), run_time=0.5)
        self.at(5)
        self.play(FadeIn(is_card), run_time=0.6)
        self.hold()

        rd = Arrow(LEFT * 0.5, ORIGIN, buff=0, stroke_width=4, color=YELLOW_M, max_tip_length_to_length_ratio=0.4)
        rd.next_to(bc[0], LEFT, buff=0.12)
        interp = VGroup(T("interpreter", 28, CARD), T("reads one bytecode at a time", 22, GREY_A)).arrange(DOWN, buff=0.1)
        interp.move_to([-3.2, -0.6, 0])
        is_day = VGroup(cook(0.8), T("= the cook on day one", 26, CARD)).arrange(RIGHT, buff=0.3).move_to([-3.2, -2.3, 0])
        self.say("map2")
        self.play(FadeOut(labs), FadeOut(src), FadeOut(carr), FadeOut(comp), FadeIn(interp), FadeIn(rd), run_time=0.7)
        for j in range(1, 8):
            self.play(rd.animate.next_to(bc[j], LEFT, buff=0.12), run_time=0.32)
        self.at(1)
        self.play(FadeOut(is_card), FadeIn(is_day), run_time=0.6)
        self.hold()

        cnt_t = VGroup(T("calls", 24, GREY_A), T("loop jumps back", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        cnt_t.move_to([-4.6, 2.3, 0])
        tl1 = tally(7).next_to(cnt_t[0], RIGHT, buff=0.4)
        tl2 = tally(12).next_to(cnt_t[1], RIGHT, buff=0.4)
        thr = DashedLine([0.4, 2.85, 0], [0.4, 1.4, 0], dash_length=0.08).set_stroke(YELLOW_M, 2.5)
        thr_t = T("threshold", 20, YELLOW_M).next_to(thr, UP, buff=0.08)
        gear = VGroup(T("compiler thread", 22, C1C), T("in the background", 20, GREY_B)).arrange(DOWN, buff=0.08).move_to([-3.2, 0.7, 0])
        mc = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.7).set_stroke(C1C, 3).set_fill(dim(C1C, 0.3), 1)
        mc_t = T("machine code", 24, C1C).move_to(mc)
        mcg = VGroup(mc, mc_t).move_to([-3.2, -0.6, 0])
        self.say("map3")
        self.play(FadeOut(interp), FadeOut(rd), run_time=0.3)
        self.play(FadeIn(cnt_t), LaggedStart(*[Create(l) for l in tl1], lag_ratio=0.1), run_time=1.0)
        self.play(LaggedStart(*[Create(l) for l in tl2], lag_ratio=0.08), run_time=1.0)
        self.at(1)
        self.play(Create(thr), FadeIn(thr_t), run_time=0.6)
        self.play(FadeIn(gear), run_time=0.5)
        self.play(FadeIn(mcg, shift=DOWN * 0.15), run_time=0.6)
        self.at(2)
        self.play(Indicate(mc_t, color=WHITE), run_time=0.8)
        self.hold()

        jit = VGroup(T("JIT", 34, YELLOW_M), T("just in time: compiles while the program runs", 26)).arrange(RIGHT, buff=0.3)
        jit.move_to([0, -3.3, 0])
        fit(jit, 12.4)
        self.say("map4")
        self.play(FadeOut(is_day), FadeIn(jit, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the two compilers, and the climb =================
        def tier_box(num, name, color, w=3.4):
            r = RoundedRectangle(corner_radius=0.14, width=w, height=1.25).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
            a = T(num, 22, GREY_B).move_to(r.get_top() + DOWN * 0.28)
            b = T(name, 28, color).move_to(r.get_center() + DOWN * 0.15)
            return VGroup(r, a, b)
        t0 = tier_box("tier 0", "interpreter", CARD).move_to([-4.6, 1.6, 0])
        t3 = tier_box("tier 3", "C1 + notes", C1C).move_to([0, 1.6, 0])
        t4 = tier_box("tier 4", "C2", C2C).move_to([4.6, 1.6, 0])
        a03 = Arrow(t0.get_right(), t3.get_left(), buff=0.12, stroke_width=3, color=GREY_B)
        a34 = Arrow(t3.get_right(), t4.get_left(), buff=0.12, stroke_width=3, color=GREY_B)
        n03 = T("about 200 calls", 22, GREY_A).next_to(a03, UP, buff=0.5)
        n34 = T("about 5,000 more", 22, GREY_A).next_to(a34, UP, buff=0.5)
        ic0 = recipe_card(3, 1.1, 0.85).next_to(t0, DOWN, buff=0.3)
        ic3 = VGroup(cheat(0.9, 0.65), notepad(0.6, 0.7)).arrange(RIGHT, buff=0.25).next_to(t3, DOWN, buff=0.3)
        ic4 = star(0.42).next_to(t4, DOWN, buff=0.35)
        d3 = VGroup(T("compiles quickly, optimizes a little", 22),
                    T("profile: which branches ran,", 22, NOTE), T("which types at each call", 22, NOTE)).arrange(DOWN, buff=0.1)
        d3.next_to(ic3, DOWN, buff=0.25)
        d4 = VGroup(T("compiles slowly, optimizes hard", 22), T("shortcuts that bet", 22, C2C),
                    T("on the usual orders", 22, C2C)).arrange(DOWN, buff=0.1)
        d4.next_to(ic4, DOWN, buff=0.3)
        self.say("c1")
        self.play(FadeIn(t0), FadeIn(ic0), run_time=0.6)
        self.at(1)
        self.play(FadeIn(t3), FadeIn(ic3[0]), FadeIn(d3[0]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(ic3[1]), FadeIn(d3[1]), FadeIn(d3[2]), run_time=0.7)
        self.hold()
        self.say("c2")
        self.play(FadeIn(t4), FadeIn(ic4, scale=0.6), FadeIn(d4[0]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(d4[1]), FadeIn(d4[2]), run_time=0.6)
        self.hold()

        meth = M("readingSeconds", 22, WHITE)
        mchip = VGroup(RoundedRectangle(corner_radius=0.08, width=meth.width + 0.3, height=0.5).set_stroke(WHITE, 2)
                       .set_fill("#1a1a1a", 1), meth)
        mchip.next_to(t0, UP, buff=0.2)
        side = T("tiers 1 and 2: C1 without notes, for tiny methods, or while C2 is busy", 20, GREY_B).move_to([0, -3.45, 0])
        rough = T("rough sizes: the bar rises when the compile queue is long", 22, YELLOW_M).move_to([0, -2.9, 0])
        self.say("climb")
        self.play(FadeIn(mchip), run_time=0.4)
        self.at(1)
        self.play(GrowArrow(a03), FadeIn(n03), mchip.animate.next_to(t3, UP, buff=0.2), run_time=1.0)
        self.at(2)
        self.play(GrowArrow(a34), FadeIn(n34), mchip.animate.next_to(t4, UP, buff=0.2), run_time=1.0)
        self.at(4)
        self.play(FadeIn(rough), FadeIn(side), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the 10,000 myth =================
        myth = T("compiled after 10,000 calls", 38, GREY_A).move_to([0, 2.4, 0])
        mx = cross(myth, 0.3)
        real = VGroup(M("CompileThreshold", 26, GREY_A), T("only when tiered compilation is switched off", 26)).arrange(RIGHT, buff=0.3)
        real.move_to([0, 1.2, 0])
        fit(real, 12.4)
        dflt = T("tiered has been the default since JDK 8", 28, C1C).move_to([0, 0.35, 0])
        old = T("not wrong, just old", 30, GREY_B).move_to([0, -1.0, 0])
        keep = VGroup(T("keep in mind:", 28, GREY_A), T("about 200", 34, C1C), T("and", 28, GREY_A), T("about 5,000 more", 34, C2C)).arrange(RIGHT, buff=0.3)
        keep.move_to([0, -2.2, 0])
        keep_s = T("the same from JDK 21 to JDK 27", 24, GREY_B).next_to(keep, DOWN, buff=0.2)
        self.say("myth")
        self.play(FadeIn(myth), run_time=0.7)
        self.at(2)
        self.play(FadeIn(real), run_time=0.6)
        self.play(Create(mx), run_time=0.5)
        self.at(3)
        self.play(FadeIn(dflt), run_time=0.6)
        self.hold()
        self.say("myth2")
        self.play(FadeIn(old), run_time=0.6)
        self.at(2)
        self.play(FadeIn(keep), run_time=0.7)
        self.play(FadeIn(keep_s), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= take cooks out of the kitchen =================
        rows_y = [1.6, 0.0, -1.6]
        lab_x = -6.3
        names = [VGroup(T("full kitchen", 26, WHITE), T("the default", 20, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
                 VGroup(T("interpreter only", 26, CARD), M("-Xint", 20, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
                 VGroup(T("C1 only", 26, C1C), M("-XX:TieredStopAtLevel=1", 20, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)]
        for n, y in zip(names, rows_y):
            n.move_to([lab_x, y, 0], aligned_edge=LEFT)
        hd = T("the late batches, microseconds", 24, GREY_B).move_to([1.2, 2.9, 0])
        bx0, kk = -1.9, 7.6 / 920
        def hbar(v0, v1, color, y):
            r = Rectangle(width=max(0.06, (v1 - v0) * kk), height=0.55).set_stroke(color, 2).set_fill(dim(color, 0.6), 1)
            r.move_to([bx0 + v0 * kk, y, 0], aligned_edge=LEFT)
            return r
        b_def = Rectangle(width=78 * kk, height=0.55).set_stroke(WHITE, 2).set_fill(GREY_C, 1).move_to([bx0, rows_y[0], 0], aligned_edge=LEFT)
        v_def = T("78", 24).next_to(b_def, RIGHT, buff=0.2)
        b_int = Rectangle(width=920 * kk, height=0.55).set_stroke(CARD, 2).set_fill(dim(CARD, 0.6), 1).move_to([bx0, rows_y[1], 0], aligned_edge=LEFT)
        v_int = T("630 to 920, every batch", 22, CARD).next_to(b_int, DOWN, buff=0.12).align_to(b_int, RIGHT)
        b_c1 = Rectangle(width=69 * kk, height=0.55).set_stroke(C1C, 2).set_fill(dim(C1C, 0.7), 1).move_to([bx0, rows_y[2], 0], aligned_edge=LEFT)
        v_c1 = T("69, from batch 6 on", 24, C1C).next_to(b_c1, RIGHT, buff=0.2)
        self.say("take_q")
        self.play(FadeIn(names[0]), FadeIn(hd), FadeIn(b_def), FadeIn(v_def), run_time=0.7)
        self.at(1)
        self.play(FadeIn(names[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(names[2]), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.say("take_int")
        self.play(GrowFromEdge(b_int, LEFT), run_time=1.0)
        self.play(FadeIn(v_int), run_time=0.4)
        self.hold()
        self.say("take_c1")
        self.play(GrowFromEdge(b_c1, LEFT), FadeIn(v_c1), run_time=0.7)
        self.at(1)
        self.play(Indicate(v_def, color=YELLOW_M), Indicate(v_c1, color=YELLOW_M), run_time=0.9)
        self.hold()
        egg = T("a master chef, hired to boil an egg", 26, C2C).move_to([0.6, -2.85, 0])
        big = T("C2 pays off on bigger code: lesson 2", 22, GREY_B).next_to(egg, DOWN, buff=0.15)
        self.say("take_why")
        self.at(3)
        self.play(FadeIn(egg), run_time=0.6)
        self.at(5)
        self.play(FadeIn(big), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: every restart is day one =================
        ck2 = cook(1.5).move_to([-4.2, 0.4, 0])
        st2 = star(0.5).next_to(ck2, RIGHT, buff=0.4).shift(UP * 0.3)
        rem = T("a real cook remembers yesterday", 26, GREY_A).next_to(ck2, DOWN, buff=0.35).shift(RIGHT * 0.4)
        div = DashedLine([-0.2, 2.8, 0], [-0.2, -2.4, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        jvm = RoundedRectangle(corner_radius=0.14, width=2.6, height=1.0).set_stroke(C2C, 3).set_fill(dim(C2C, 0.15), 1)
        jvm_t = T("warm JVM", 26, C2C).move_to(jvm)
        jg = VGroup(jvm, jvm_t).move_to([2.0, 1.5, 0])
        jvm2 = RoundedRectangle(corner_radius=0.14, width=2.6, height=1.0).set_stroke(CARD, 3).set_fill(dim(CARD, 0.15), 1)
        jvm2_t = T("new JVM", 26, CARD).move_to(jvm2)
        jg2 = VGroup(jvm2, jvm2_t).move_to([5.0, -0.6, 0])
        rs = CurvedArrow(jg.get_right() + DOWN * 0.1, jg2.get_top() + UP * 0.05, angle=-PI / 2.5, color=GREY_B, stroke_width=3)
        rs_t = T("restart", 22, GREY_B).next_to(rs, RIGHT, buff=0.1).shift(UP * 0.4)
        c3 = recipe_card(3, 1.1, 0.85).next_to(jg2, DOWN, buff=0.3)
        forget = T("forgets everything: day one again", 26, CARD).move_to([2.9, -2.9, 0])
        self.say("breaks")
        self.play(FadeIn(ck2), FadeIn(st2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rem), run_time=0.5)
        self.at(2)
        self.play(Create(div), FadeIn(jg), run_time=0.7)
        self.play(Create(rs), FadeIn(rs_t), FadeIn(jg2), run_time=0.9)
        self.at(3)
        self.play(FadeIn(c3), FadeIn(forget), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the rule and its guardrails =================
        r1 = T("The same code runs at different speeds,", 32)
        r1b = T("depending on how long the JVM has watched it.", 32)
        r2 = T("Never trust the first lap.", 38, YELLOW_M)
        rg = VGroup(r1, r1b, r2).arrange(DOWN, buff=0.3).move_to([0, 2.2, 0])
        fit(rg, 12.4)
        self.say("rule")
        self.play(FadeIn(r1), FadeIn(r1b), run_time=0.8)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        gs = VGroup(T("1.  Measure after warm-up, or say it's a cold start.", 28),
                    T("2.  On a busy machine, read the shape, not one batch.", 28),
                    T("3.  One call right after start is not the speed of your code.", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(gs, 12.2).move_to([0, -1.3, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gs[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(gs[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(gs[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the moral: compiled twice, and a check =================
        m0 = T("Your code is compiled twice.", 36, YELLOW_M).move_to([0, 3.0, 0])
        once = VGroup(T("javac or kotlinc", 26, GREY_A), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B),
                      T("bytecode", 26, CARD)).arrange(RIGHT, buff=0.2).move_to([0, 2.1, 0])
        cols = VGroup(
            VGroup(recipe_card(3, 1.3, 1.0), T("interpreter", 26, CARD), T("reads the card", 22, GREY_A)).arrange(DOWN, buff=0.15),
            VGroup(VGroup(cheat(0.95, 0.7), notepad(0.6, 0.7)).arrange(RIGHT, buff=0.2), T("C1", 26, C1C),
                   T("cheat sheet and notes", 22, GREY_A)).arrange(DOWN, buff=0.15),
            VGroup(star(0.5), T("C2", 26, C2C), T("practised, with shortcuts", 22, GREY_A)).arrange(DOWN, buff=0.15)).arrange(RIGHT, buff=1.3)
        cols.move_to([0, 0.0, 0])
        jl = T("then again while it runs, by the JIT", 24, GREY_B).next_to(cols, UP, buff=0.3)
        self.say("moral")
        self.play(FadeIn(m0), run_time=0.6)
        self.at(1)
        self.play(FadeIn(once), run_time=0.6)
        self.at(2)
        self.play(FadeIn(jl), run_time=0.5)
        self.at(3)
        self.play(FadeIn(cols[0]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(cols[1]), run_time=0.5)
        self.at(5)
        self.play(FadeIn(cols[2]), run_time=0.5)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("a test calls a method once, right after start, and times it.", 28)).arrange(RIGHT, buff=0.25)
        qb = T("Which tier ran it? What did it measure?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to([0, -2.2, 0])
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.5))
        ans = T("The interpreter, tier 0: the cook's first day.", 28, CARD).move_to([0, -3.35, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
