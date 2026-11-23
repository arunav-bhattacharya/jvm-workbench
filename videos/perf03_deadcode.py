from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bMath\.sqrt\b", "math dot square root"), (r"\bMath\.log\b", "math dot log"), (r"\bnanoTime\b", "nano time"),
    (r"\bNanoLoop\b", "nano loop"), (r"\bOpenJDK\b", "Open J D K"), (r"\b0\.0000\b", "zero point zero zero zero zero"),
    (r"\b0\.07\b", "zero point zero seven"), (r"\b0\.2\b", "zero point two"), (r"\b3\.4\b", "three point four"),
    (r"\b3\.0\b", "three point oh"),
]

# every spoken line, in order
N = {
    "open": "Picture a restaurant that wants to know which of two cooks makes the house soup faster. The manager "
            "hands each cook an order, starts a stopwatch, and stops it when the bowl lands on the counter. "
            "Simple enough.",
    "twist": "But one cook notices something. Nobody ever eats the test bowls. So the cook stops making them. The "
             "stopwatch reads zero. Fastest soup in town.",
    "shyq": "Here's a question we rarely ask out loud. If I time my code with the clock, isn't the number on the "
            "clock simply the answer?",
    "loop": "Let's try it. Here's the benchmark almost everyone writes first. A benchmark is a small program that "
            "measures how long some code takes. Read the clock. Call Math.sqrt, a square root, 100 million times, "
            "and throw each result away. Read the clock again, and divide.",
    "loop2": "The lesson's NanoLoop runs that loop five times. Next to it, a second loop does the same work, but "
             "adds every result to a sum, and prints the sum. So, how long should one square root take? Pause "
             "and guess.",
    "r1": "Round one: the loop that throws the result away says 0.07 nanoseconds a call. The loop that uses it "
          "says 3.4. Round two: 0.2, and 3.0.",
    "r3": "And from round three on: 0.0000. Zero nanoseconds per square root. That's not fast. That's a magic "
          "trick. The used loop stays near 3 nanoseconds, which is believable for a square root and an "
          "addition, on a busy machine.",
    "why": "So where did the work go? Once C2, the JIT's optimizing compiler, had compiled the loop, it proved "
           "that nobody used the result of Math.sqrt. So it deleted the call. Then the loop was empty, so it "
           "deleted the loop. That's called dead-code elimination: work whose result nobody uses can go.",
    "map": "Let's map it. The stopwatch is nanoTime. The test bowl is the result. Nobody eating it is our loop, "
           "throwing it away. And the cook who stops making bowls is C2.",
    "breaks": "But here the picture breaks, in a useful way. A cook who skips the bowl knows they're cutting a "
              "corner. The JIT isn't cheating at all. Removing unused work is exactly its job, and our benchmark "
              "gave it permission.",
    "fold": "And dead code is only one way a hand-made loop lies. If the input is a constant, C2 can work out the "
            "answer before the loop even runs, and you time the loading of one number. That's constant folding: "
            "the cook who gets the same order every day, and makes it before the doors open.",
    "cold": "The first rounds run in the interpreter, and in loop code compiled mid-run, as lesson 1 showed. So "
            "round one measures the cook's first day.",
    "unroll": "And the JIT reshapes loops. JMH's own sample on loops reports an addition that seems to take one "
              "twentieth of a nanosecond, well beyond what hardware can do.",
    "worse": "Now the worse case: a broken benchmark that prints a believable number. Swap the square root for "
             "Math.log. On JDK 21, the throw-away loop was never removed. It said 10 to 13 nanoseconds, round "
             "after round. Looks honest. And on JDK 25?",
    "worse_a": "0.0000 by round three, like the square root. Same source, two JDKs, two stories. The magician got "
               "better, and nothing in your code told you. Whether the JIT can remove a call depends on what it "
               "can prove, and you can't see that from outside.",
    "rule": "So here's the rule. A timing loop you wrote by hand measures whatever the JIT left behind. Don't "
            "trust its number.",
    "wish": "What we really want is a fair taste test. Warm the kitchen up first, and throw away the practice "
            "dishes. Use ingredients the cook can't predict. Have a judge eat every dish. And start each day in "
            "a fresh kitchen.",
    "jmh": "That's what JMH does: the Java Microbenchmark Harness, from the OpenJDK team. You write a method and "
           "mark it as a benchmark. JMH writes the measuring loop around it, and runs it in fresh JVMs. Inputs "
           "live in fields the JIT can't predict. And whatever you return, the judge eats.",
    "code": "Here's an honest benchmark for the report service's reading time, in Java and in Kotlin. words is a "
            "plain field, not a constant. And the result is returned, so JMH consumes it, and C2 has to compute "
            "it. In Kotlin the class must be open, because JMH's generated code extends it.",
    "guard": "One warning about every number in this video. They came from a busy machine. Read the shape, zero "
             "against three, not the digits. And keep JMH's short demo runs for spotting traps, not for "
             "deciding anything.",
    "moral": "The moral of the story: the JIT deletes work nobody uses, and folds work it can predict. A "
             "stopwatch around your loop can't tell you which one happened. So use the result, hide the input, "
             "and let JMH build the loop.",
    "chk": "Quick check. A loop takes the square root of 2.0, a constant, adds every result to a sum, and prints "
           "the sum. Is that an honest measure of a square root?",
    "chka": "No. The result is used, but the input is a constant, so C2 can work out the square root once, "
            "before the loop. Next: two rules that fix most broken benchmarks.",
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


def maprow(left, right, lc=WHITE, rc=WHITE, size=26, mono_right=False):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = (M if mono_right else T)(right, size - 2 if mono_right else size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


def stopwatch(r=0.6, color=GREY_A):
    face = Circle(radius=r).set_stroke(color, 3).set_fill("#141414", 1)
    knob = Rectangle(width=r * 0.35, height=r * 0.22).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1).next_to(face, UP, buff=0.02)
    hand = Line(face.get_center(), face.get_center() + UP * r * 0.75, stroke_width=4, color=YELLOW_M)
    return VGroup(face, knob, hand)


def bowl(color=GOLD_M, s=1.0):
    b = Arc(radius=0.38, start_angle=PI, angle=PI).set_stroke(color, 3)
    rim = Line(LEFT * 0.38, RIGHT * 0.38, stroke_width=3, color=color)
    soup = Arc(radius=0.33, start_angle=PI, angle=PI).set_stroke(width=0).set_fill(dim(color, 0.55), 1)
    steam = VGroup(*[Arc(radius=0.08, start_angle=-PI / 2, angle=PI, stroke_width=2, color=GREY_B).move_to([x, 0.22, 0]) for x in (-0.12, 0.12)])
    return VGroup(soup, b, rim, steam).scale(s)


LOOP_J = ["long t0 = System.nanoTime();",
          "for (int i = 0; i < 100_000_000; i++) {",
          "    Math.sqrt(x);                // result discarded",
          "}",
          "long t1 = System.nanoTime();"]
LOOP_K = ["val t0 = System.nanoTime()",
          "for (i in 0 until 100_000_000) {",
          "    sqrt(x)                      // result discarded",
          "}",
          "val t1 = System.nanoTime()"]
ROUNDS = [("0.0678", "3.3919"), ("0.2053", "3.0171"), ("0.0000", "3.3148"), ("0.0000", "3.2549"), ("0.0000", "3.5381")]
DIS, USED = RED_M, TEAL_M


class Perf03DeadCode(Narrated):
    """perf-03, section 0: the test bowls nobody eats; the shy question (isn't the clock the answer?); the
    nanoTime loop in Java and Kotlin; predict, then NanoLoop's five rounds (0.0000 against about 3 ns); dead-code
    elimination; the map; where the picture breaks (the JIT isn't cheating); constant folding, cold rounds, loop
    reshaping; Math.log on JDK 21 and JDK 25; the rule; the fair taste test that JMH builds; the honest benchmark
    in Java and Kotlin; a warning, the moral and a check."""

    def construct(self):
        self.title_card("The stopwatch that reads zero", "what a hand-made timing loop measures")

        # ================= the soup contest =================
        sw = stopwatch(0.7).move_to([0, 1.9, 0])
        mgr = VGroup(cook(1.3, GREY_B)).next_to(sw, LEFT, buff=0.5)
        mg_t = T("the manager", 22, GREY_B).next_to(mgr, DOWN, buff=0.15)
        ca = cook(1.5).move_to([-3.6, -1.2, 0])
        cb = cook(1.5).move_to([3.6, -1.2, 0])
        ba = bowl().next_to(ca, RIGHT, buff=0.4)
        bb = bowl().next_to(cb, LEFT, buff=0.4)
        ta = T("cook A", 22, GREY_A).next_to(ca, DOWN, buff=0.15)
        tb = T("cook B", 22, GREY_A).next_to(cb, DOWN, buff=0.15)
        self.say("open")
        self.play(FadeIn(ca), FadeIn(cb), FadeIn(ta), FadeIn(tb), run_time=0.7)
        self.at(1)
        self.play(FadeIn(mgr), FadeIn(mg_t), FadeIn(sw), run_time=0.6)
        self.play(Rotate(sw[2], -PI * 1.5, about_point=sw[0].get_center()), run_time=1.4)
        self.play(FadeIn(ba, shift=DOWN * 0.2), FadeIn(bb, shift=DOWN * 0.2), run_time=0.6)
        self.hold()

        nobody = T("nobody eats the test bowls", 24, GREY_A).move_to([0, -0.4, 0])
        zero = T("0.0 s", 30, YELLOW_M).next_to(sw, RIGHT, buff=0.4)
        fast = T("fastest soup in town", 26, C2C).move_to([3.6, 0.6, 0])
        self.say("twist")
        self.at(1)
        self.play(FadeIn(nobody), run_time=0.6)
        self.at(2)
        self.play(FadeOut(bb, scale=0.4), run_time=0.7)
        self.at(3)
        self.play(sw[2].animate.become(Line(sw[0].get_center(), sw[0].get_center() + UP * 0.52, stroke_width=4, color=YELLOW_M)),
                  FadeIn(zero), run_time=0.6)
        self.at(4)
        self.play(FadeIn(fast), run_time=0.5)
        self.hold()

        q1 = T("If I time my code with the clock,", 30)
        q2 = T("isn't the number on the clock simply the answer?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).move_to([0, -3.0, 0])
        self.say("shyq")
        self.play(FadeOut(nobody), FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.0)
        self.wipe()

        # ================= the loop everyone writes =================
        jv = code_block(LOOP_J, 22, hl={"System.nanoTime()": YELLOW_M, "Math.sqrt(x);": DIS})
        kt = code_block(LOOP_K, 22, hl={"System.nanoTime()": YELLOW_M, "sqrt(x)": DIS})
        jc = VGroup(T("Java", 22, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        kc = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(cols, 12.4).move_to([0, 0.5, 0])
        div_t = T("time per call = (t1 - t0) / 100,000,000", 24, GREY_A).next_to(cols, DOWN, buff=0.3)
        self.say("loop")
        self.at(1)
        self.play(FadeIn(jc), FadeIn(kc), run_time=0.8)
        self.at(3)
        self.play(Indicate(VGroup(jv[0], kt[0]), color=YELLOW_M), run_time=0.7)
        self.at(4)
        self.play(Indicate(VGroup(jv[2], kt[2]), color=DIS), run_time=0.8)
        self.at(5)
        self.play(Indicate(VGroup(jv[4], kt[4]), color=YELLOW_M), FadeIn(div_t), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= predict, then the five rounds =================
        hd = VGroup(T("round", 26, GREY_B), T("result thrown away", 26, DIS), T("result used", 26, USED))
        xs = [-4.6, -0.6, 3.8]
        for h, x in zip(hd, xs):
            h.move_to([x, 2.6, 0])
        sub = T("nanoseconds per call, NanoLoop on JDK 25, a busy machine", 20, GREY_B).move_to([0, 3.25, 0])
        rows = VGroup()
        for i, (d, u) in enumerate(ROUNDS):
            y = 1.75 - i * 0.72
            rows.add(VGroup(T(str(i + 1), 28, GREY_A).move_to([xs[0], y, 0]), M(d, 28, DIS).move_to([xs[1], y, 0]),
                            M(u, 28, USED).move_to([xs[2], y, 0])))
        self.say("loop2")
        self.play(FadeIn(hd), FadeIn(sub), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.say("r1")
        self.play(FadeIn(rows[0][0]), FadeIn(rows[0][1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rows[0][2]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rows[1]), run_time=0.5)
        self.hold()
        self.say("r3")
        self.play(LaggedStart(*[FadeIn(rows[i][:2]) for i in (2, 3, 4)], lag_ratio=0.3), run_time=1.0)
        self.at(1)
        self.play(*[Indicate(rows[i][1], color=YELLOW_M) for i in (2, 3, 4)], run_time=0.9)
        trick = T("a magic trick", 28, YELLOW_M).move_to([xs[1], -2.2, 0])
        self.at(3)
        self.play(FadeIn(trick), run_time=0.5)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(rows[i][2]) for i in (2, 3, 4)], lag_ratio=0.3), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= where the work went =================
        lp = RoundedRectangle(corner_radius=0.14, width=5.2, height=2.2).set_stroke(GREY_B, 3).set_fill("#101010", 1).move_to([-2.6, 0.6, 0])
        lp_t = T("the loop, 100 million laps", 22, GREY_B).next_to(lp, UP, buff=0.12)
        call = chip("Math.sqrt(x)", DIS, 26, mono=True).move_to(lp)
        res = T("result", 24, DIS).move_to([2.6, 0.6, 0])
        ra = Arrow(call.get_right(), res.get_left(), buff=0.2, stroke_width=3, color=DIS)
        nob = T("nobody reads it", 24, GREY_A).next_to(res, DOWN, buff=0.2)
        c2 = T("C2", 34, C2C).move_to([-2.6, -1.4, 0])
        x1 = tick(False, 0.35).move_to(call)
        x2 = tick(False, 0.6).move_to(lp)
        dce = VGroup(T("dead-code elimination:", 30, YELLOW_M), T("work whose result nobody uses can go", 30)).arrange(DOWN, buff=0.15)
        dce.move_to([0, -2.7, 0])
        self.say("why")
        self.play(FadeIn(lp), FadeIn(lp_t), FadeIn(call), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c2), GrowArrow(ra), FadeIn(res), run_time=0.7)
        self.play(FadeIn(nob), run_time=0.4)
        self.at(2)
        self.play(Create(x1), call.animate.set_opacity(0.25), run_time=0.6)
        self.at(3)
        self.play(Create(x2), lp.animate.set_stroke(opacity=0.3), run_time=0.6)
        self.at(4)
        self.play(FadeOut(c2), FadeIn(dce, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        maps = [maprow("the stopwatch", "System.nanoTime()", GREY_A, YELLOW_M, mono_right=True),
                maprow("the test bowl", "the result of Math.sqrt", C2C, DIS),
                maprow("nobody eats it", "the loop throws it away", GREY_A, GREY_A),
                maprow("the cook who stops making bowls", "C2", GREY_A, C2C)]
        tbl = maptable(maps, x_arrow=0.2, y0=2.5, dy=0.85)
        fit(tbl, 12.6)
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(maps[i]), run_time=0.5)
        self.hold()
        ck = cook(1.2).move_to([-3.6, -1.6, 0])
        ck_t = T("knows it's cutting a corner", 24, GREY_A).next_to(ck, DOWN, buff=0.2)
        jit = VGroup(T("the JIT", 30, C2C), T("just doing its job", 26), T("we gave it permission", 26, YELLOW_M)).arrange(DOWN, buff=0.15)
        jit.move_to([3.2, -1.9, 0])
        self.say("breaks")
        self.play(FadeIn(ck), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ck_t), run_time=0.5)
        self.at(2)
        self.play(FadeIn(jit[0]), FadeIn(jit[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(jit[2]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= other ways a hand-made loop lies =================
        def lie(title, line1, line2, color, icon):
            r = RoundedRectangle(corner_radius=0.14, width=3.9, height=4.2).set_stroke(color, 3).set_fill(dim(color, 0.1), 1)
            t = T(title, 28, color).move_to(r.get_top() + DOWN * 0.45)
            icon.move_to(r.get_center() + UP * 0.35)
            a = T(line1, 22).move_to(r.get_center() + DOWN * 0.85)
            b = T(line2, 22, GREY_A).next_to(a, DOWN, buff=0.1)
            fit(a, 3.5); fit(b, 3.5)
            return VGroup(r, t, icon, a, b)
        made = VGroup(bowl(C2C, 1.1), T("ready at 8:00", 20, GREY_B)).arrange(DOWN, buff=0.15)
        l1 = lie("constant folding", "the answer is worked out", "before the loop runs", C2C, made)
        l2 = lie("cold rounds", "round one runs in", "the interpreter: day one", CARD, recipe_card(4, 1.4, 1.3))
        l3 = lie("reshaped loops", "an addition in", "1/20 of a nanosecond?", NOTE, M("1/20 ns", 30, NOTE))
        lies = VGroup(l1, l2, l3).arrange(RIGHT, buff=0.35).move_to([0, -0.1, 0])
        fit(lies, 12.6)
        self.say("fold")
        self.at(1)
        self.play(FadeIn(l1), run_time=0.7)
        self.hold()
        self.say("cold")
        self.play(FadeIn(l2), run_time=0.7)
        self.hold()
        self.say("unroll")
        self.play(FadeIn(l3), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the believable number: Math.log =================
        lh = VGroup(T("the same loop, with", 28, GREY_A), M("Math.log(x)", 28, DIS), T("thrown away", 28, GREY_A)).arrange(RIGHT, buff=0.2)
        lh.move_to([0, 2.8, 0])
        j21 = VGroup(T("JDK 21", 32, CARD), T("10 to 13 ns per call", 30), T("round after round", 24, GREY_A),
                     T("looks honest", 26, GREY_B)).arrange(DOWN, buff=0.2).move_to([-3.2, 0.4, 0])
        j25 = VGroup(T("JDK 25", 32, C2C), M("0.0000", 30, DIS), T("by round three", 24, GREY_A)).arrange(DOWN, buff=0.2).move_to([3.2, 0.55, 0])
        dv = DashedLine([0, 1.9, 0], [0, -1.2, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        self.say("worse")
        self.play(FadeIn(lh), run_time=0.6)
        self.at(2)
        self.play(FadeIn(j21[0]), FadeIn(j21[1]), FadeIn(j21[2]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(j21[3]), run_time=0.4)
        self.at(5)
        self.play(Create(dv), FadeIn(j25[0]), run_time=0.5)
        self.hold(after=0)
        self.wait(1.0)
        two = T("same source, two JDKs, two stories", 28, YELLOW_M).move_to([0, -2.0, 0])
        mag = T("the magician got better", 24, GREY_A).next_to(two, DOWN, buff=0.18)
        self.say("worse_a")
        self.play(FadeIn(j25[1:]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(two), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mag), run_time=0.5)
        self.hold()
        self.wipe()

        r1 = T("A timing loop you wrote by hand", 34)
        r1b = T("measures whatever the JIT left behind.", 34)
        r2 = T("Don't trust its number.", 38, YELLOW_M)
        rg = VGroup(r1, r1b, r2).arrange(DOWN, buff=0.3).move_to([0, 0.3, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1), FadeIn(r1b), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the fair taste test, and JMH =================
        test = [("warm the kitchen up, throw the practice dishes away", "warm-up iterations, thrown away"),
                ("ingredients the cook can't predict", "inputs in plain @State fields"),
                ("a judge eats every dish", "JMH consumes the returned value"),
                ("a fresh kitchen each day", "@Fork: a fresh JVM")]
        lt = VGroup(*[T(a, 24, C2C) for a, _ in test]).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        rt = VGroup(*[T(b, 24, C1C) for _, b in test])
        lt.move_to([-6.3, 0.2, 0], aligned_edge=LEFT)
        ax0 = lt.get_right()[0] + 0.3
        for r, l in zip(rt, lt):
            r.move_to([ax0 + 1.0, l.get_center()[1], 0], aligned_edge=LEFT)
        arrs = VGroup(*[Arrow([ax0, l.get_center()[1], 0], [ax0 + 0.85, l.get_center()[1], 0], buff=0, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.3) for l in lt])
        VGroup(lt, rt, arrs).move_to([0, 0.2, 0])
        fit(VGroup(lt, rt, arrs), 12.6)
        th = T("a fair taste test", 30, C2C).move_to([-3.4, 2.9, 0])
        jh = T("JMH", 34, C1C).move_to([3.4, 2.9, 0])
        self.say("wish")
        self.play(FadeIn(th), run_time=0.5)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(lt[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.say("jmh")
        self.play(FadeIn(jh), run_time=0.5)
        self.at(2)
        self.play(GrowArrow(arrs[0]), FadeIn(rt[0]), GrowArrow(arrs[3]), FadeIn(rt[3]), run_time=0.7)
        self.at(3)
        self.play(GrowArrow(arrs[1]), FadeIn(rt[1]), run_time=0.5)
        self.at(4)
        self.play(GrowArrow(arrs[2]), FadeIn(rt[2]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the honest benchmark, Java and Kotlin =================
        jv = code_block(["@State(Scope.Thread)",
                         "public class ReadingBench {",
                         "    long words = 1_234;           // a plain field",
                         "    @Benchmark",
                         "    public long seconds() {",
                         "        return ReadingMath.readingSeconds(words);   // returned",
                         "    }",
                         "}"], 22, hl={"long words = 1_234;": C2C, "return ReadingMath": C1C})
        kt = code_block(["@State(Scope.Thread)",
                         "open class ReadingBench {          // open: JMH extends it",
                         "    var words = 1_234L             // a plain field",
                         "    @Benchmark",
                         "    fun seconds(): Long = ReadingMath.readingSeconds(words)",
                         "}"], 22, hl={"var words = 1_234L": C2C, "open": YELLOW_M})
        jc = VGroup(T("Java", 22, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        kc = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(cols, 12.4).move_to([0, 0, 0])
        self.say("code")
        self.play(FadeIn(jc), FadeIn(kc), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(VGroup(jv[2], kt[2]), color=C2C, buff=0.05), run_time=1.0)
        self.at(2)
        self.play(Circumscribe(jv[5], color=C1C, buff=0.05), Circumscribe(kt[4], color=C1C, buff=0.05), run_time=1.0)
        self.at(3)
        self.play(Indicate(kt[1], color=YELLOW_M), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= a warning, the moral and a check =================
        wn = VGroup(T("Every number here came from a busy machine.", 28, GREY_A),
                    T("Read the shape: zero against three.", 30, YELLOW_M),
                    T("Short demo runs spot traps; they don't decide anything.", 26, GREY_A)).arrange(DOWN, buff=0.25)
        wn.move_to([0, 0.3, 0])
        fit(wn, 12.4)
        self.say("guard")
        self.play(FadeIn(wn[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(wn[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(wn[2]), run_time=0.5)
        self.hold()
        self.wipe()

        m0 = VGroup(T("The JIT deletes work nobody uses,", 30), T("and folds work it can predict.", 30)).arrange(DOWN, buff=0.12)
        m0.move_to([0, 2.7, 0])
        m1 = T("A stopwatch around a loop can't tell you which one happened.", 28, GREY_A).move_to([0, 1.55, 0])
        fit(m1, 12.4)
        m2 = VGroup(T("use the result", 28, C1C), T("hide the input", 28, C2C), T("let JMH build the loop", 28, YELLOW_M)).arrange(RIGHT, buff=0.7)
        m2.move_to([0, 0.6, 0])
        fit(m2, 12.4)
        self.say("moral")
        self.play(FadeIn(m0), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(x) for x in m2], lag_ratio=0.6), run_time=2.0)
        self.hold()
        qa = VGroup(T("Check:", 28, YELLOW_M), T("sum += Math.sqrt(2.0) in the loop, then print the sum.", 28)).arrange(RIGHT, buff=0.25)
        qb = T("An honest measure of a square root?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to([0, -1.4, 0])
        fit(qg2, 12.4)
        self.say("chk")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.5))
        ans = T("No: the input is a constant, so C2 can work out the square root once.", 28, C2C).move_to([0, -2.9, 0])
        fit(ans, 12.4)
        self.say("chka")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
