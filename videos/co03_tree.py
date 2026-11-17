from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutineScope\b", "co-routine scope"), (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
    (r"\bCancellationException\b", "Cancellation Exception"), (r"\bBurnedException\b", "Burned Exception"),
    (r"\bFailureSpreads\b", "Failure Spreads"), (r"\basync\b", "ay-sink"),
]

# every spoken line, in order
N = {
    "open": "In plain code, an exception has an easy path. A function throws, and the exception climbs back up to "
            "whoever called it, one caller at a time, until someone catches it.",
    "shyq": "So here's a question that's easy to be shy about. A launched coroutine has no caller waiting for it. "
            "The line that started it moved on long ago. So when it throws, where does the exception go?",
    "tree": "The answer is a picture we've been building. A dinner has courses, and a course has dishes. The "
            "dinner is the root coroutine, the main course is a coroutineScope inside it, and the roast, the "
            "potatoes and the gravy are its children.",
    "tree2": "Every coroutine becomes a child of the scope it starts in, so the work forms a tree. You already "
             "know its first rule: a parent can't finish until all of its children have.",
    "burn_q": "Now the roast burns. It happens to the best cooks. At 100 milliseconds it throws BurnedException, an "
              "exception the demo made up. The potatoes would need a whole second. Should they keep cooking? And "
              "when does the caller hear?",
    "s1": "Here's what the tree does, in order. One: the roast fails, and reports the exception to its parent, "
          "the course.",
    "s2": "Two: the course is cancelled with that exception, and a cancelled job cancels all of its children. "
          "The potatoes and the gravy come off the heat, and their finally blocks, the clean up code, run.",
    "s3": "Three: the course waits until they have really stopped.",
    "s4": "Four: coroutineScope throws the BurnedException to its caller, who can catch it like any exception. "
          "The family hears what happened.",
    "sum": "So one failure takes down the whole course, and comes out as one exception, where the work started, "
           "after about 100 milliseconds. Nothing is left cooking.",
    "demo": "The lesson's FailureSpreads runs this with a roast and potatoes. The roast burned at 161 "
            "milliseconds. The potatoes' finally block ran 2 milliseconds later, and the caller caught it 2 after "
            "that. Potatoes: done, never printed.",
    "demo_joke": "Why 161, and not 100? A JVM, the program that runs the code, is slow just after it starts. It was "
                 "still finding its apron. That part is the machine, not the tree.",
    "java": "Many of us carry a picture from Java's executors, the pools that run tasks you hand them: every task "
            "is on its own. On an executor, the roast fails, and the potatoes carry on to potatoes: done, at "
            "about 1,000 milliseconds. close waits for them.",
    "java_joke": "The roast is on fire, and the potatoes are still being lovingly peeled. So the point is: in Java, "
                 "you cancel them by hand. With that one line, their finally ran at 198 milliseconds. coroutineScope "
                 "does that step for you.",
    "cancel": "Now the other direction. The guests phone, and call the dinner off. That's a cancel, and it comes "
              "from the top. It travels down: the dinner is cancelled, then the course, then every dish below it.",
    "up_q": "And the other way? Say only the gravy is cancelled. Does the course stop?",
    "up_a": "No. A cancel never goes up. A child that's cancelled, or that ends by throwing "
            "CancellationException, the exception a cancelled coroutine throws, counts as cancelled, not failed. "
            "Its parent isn't told, and the roast and the potatoes carry on.",
    "name": "This is structured concurrency: work that runs at the same time has the same nested shape as the "
            "code that started it, and failures and cancels follow that shape. A failure goes up the tree and "
            "stops the siblings. A cancel goes down, and stops there.",
    "why": "This is the default because it's almost always what you want. If the roast is ruined, the course is "
           "off: nobody serves potatoes and gravy next to a hole where the roast should be. Sometimes you do "
           "want siblings to survive, like a reminder sent by text, email and phone, where any one is enough. "
           "Lesson 6 brings in a supervisor for that.",
    "breaks": "And here the picture breaks, on timing. A real cook pulls the pans off at once. A coroutine hears "
              "the cancel only at its next suspension point, so a long calculation, or a blocking call, finishes "
              "first. Lesson 5 shows how to cooperate.",
    "code": "Here's the demo's core in Kotlin, shortened, with the Java executor beside it. In Kotlin, the scope "
            "cancels the potatoes for you. In Java, you write that line yourself.",
    "moral": "So, where does a child's exception go? Up the tree, to its parent. The parent stops the siblings, "
             "waits for them, and hands one exception to whoever started the work. A cancel only ever travels "
             "down.",
    "check": "Quick check. Nobody calls off the dinner. Someone cancels just the potatoes. What happens to the "
             "roast, the gravy and the course?",
    "check_a": "Nothing changes for them. The potatoes count as cancelled, not failed, so the course isn't told. The "
               "roast and the gravy keep cooking.",
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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole coroutines track
COOK, COURSE, BAD, CANCEL, OFF, DINNER = BLUE_M, PURPLE_M, RED_M, YELLOW_M, GREY_C, GREY_A
ROAST, POTS, GRAVY = GOLD_M, GREEN_M, TEAL_M
DISHES = [("roast", ROAST), ("potatoes", POTS), ("gravy", GRAVY)]


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def pot(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    return VGroup(body, rim, hl, hr).scale(s)


def steam(m, color=GREY_B):
    c = m.get_top()
    return VGroup(*[VMobject(stroke_width=2, stroke_color=color).set_points_smoothly(
        [c + np.array([dx, 0.06, 0]), c + np.array([dx + 0.05, 0.16, 0]), c + np.array([dx - 0.04, 0.26, 0]),
         c + np.array([dx + 0.03, 0.36, 0])]) for dx in (-0.18, 0.0, 0.18)])


def flame(s=1.0):
    outer = VMobject().set_points_smoothly([[0, 0.45, 0], [0.2, 0.1, 0], [0.22, -0.15, 0], [0, -0.3, 0],
                                            [-0.22, -0.15, 0], [-0.2, 0.1, 0], [0, 0.45, 0]])
    outer.set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.6), 1)
    inner = VMobject().set_points_smoothly([[0, 0.15, 0], [0.09, -0.05, 0], [0, -0.2, 0], [-0.09, -0.05, 0], [0, 0.15, 0]])
    inner.set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.7), 1)
    return VGroup(outer, inner).scale(s)


def phone(s=1.0, color=GREY_A):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(BLUE_M, 0.5), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def node(label, color, w=2.5, mono=False, size=26, icon=None):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=0.85).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    t = (M if mono else T)(label, size, color)
    if icon is not None:
        icon.scale_to_fit_height(0.42)
        g = VGroup(icon, t).arrange(RIGHT, buff=0.2).move_to(r)
        return VGroup(r, t, icon)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def down_arrow(a, b, color, sw=4):
    return Arrow(a.get_bottom(), b.get_top(), buff=0.1, stroke_width=sw, color=color, max_tip_length_to_length_ratio=0.22)


def up_arrow(a, b, color, sw=4):
    return Arrow(a.get_top(), b.get_bottom(), buff=0.1, stroke_width=sw, color=color, max_tip_length_to_length_ratio=0.22)


# the tree, as it sits on screen
DIN_P, CRS_P = np.array([0, 2.45, 0]), np.array([0, 0.75, 0])
DISH_X, DISH_Y = (-3.7, 0.0, 3.7), -1.0
X0, PX = -2.7, 0.0072        # timelines: x(ms)


def tx(ms):
    return X0 + ms * PX


class Co03FailureTree(Narrated):
    """co-03, section 1: failure goes up, cancellation goes down. Where does a child's exception go (no caller on the
    stack)? The dinner tree; the roast burns at 100 ms: four steps up and down the tree; the FailureSpreads log
    (161/163/165 ms); the Java executor has no tree (potatoes done at about 1,000 ms; by hand: 198 ms); the guests call
    the dinner off (down); cancelling only the gravy doesn't go up; structured concurrency named; why it's the default;
    the picture breaks on timing; Kotlin and Java; a check."""

    def construct(self):
        self.title_card("Up the tree, down the tree", "what one burned dish does to the dinner")

        # ================= familiar: the call stack =================
        names = ["main()", "serveDinner()", "cookCourse()", "roast()"]
        stack = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=3.4, height=0.62).set_stroke(GREY_B, 2)
                                .set_fill(BLACK, 1), M(n, 24)) for n in names])
        for s in stack:
            s[1].move_to(s[0])
        stack.arrange(DOWN, buff=0.12).move_to([-3.2, 0.3, 0])
        st_l = T("the call stack", 24, GREY_B).next_to(stack, DOWN, buff=0.25)
        exc = VGroup(RoundedRectangle(corner_radius=0.06, width=1.5, height=0.45).set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.3), 1),
                     T("throw", 22, BAD))
        exc[1].move_to(exc[0])
        exc.next_to(stack[3], RIGHT, buff=0.3)
        caught = T("caught", 24, GREEN_M).next_to(stack[0], RIGHT, buff=0.3)
        self.say("open")
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in stack], lag_ratio=0.2), FadeIn(st_l), run_time=1.2)
        self.at_text("A function throws", lead=0.3)
        self.play(FadeIn(exc, scale=0.8), run_time=0.4)
        self.at_text("climbs back", lead=0.3)
        for k in (2, 1, 0):
            self.play(exc.animate.next_to(stack[k], RIGHT, buff=0.3), run_time=0.5)
        self.play(FadeIn(caught), FadeOut(exc), run_time=0.4)
        self.hold()

        ct = M("launch { roast() }", 22, ROAST)
        child = VGroup(RoundedRectangle(corner_radius=0.08, width=ct.width + 0.5, height=0.62).set_stroke(ROAST, 2.5)
                       .set_fill(dim(ROAST, 0.18), 1), ct)
        child[1].move_to(child[0])
        child.move_to([3.3, 1.2, 0])
        moved = T("its starter has moved on", 22, GREY_A).next_to(child, UP, buff=0.2)
        exc2 = exc.copy().next_to(child, DOWN, buff=0.3)
        q = T("So where does its exception go?", 32, YELLOW_M).move_to([3.0, -1.4, 0])
        self.say("shyq")
        self.play(FadeOut(caught), run_time=0.3)
        self.at(1)
        self.play(FadeIn(child, shift=LEFT * 0.2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(moved), stack[2].animate.set_opacity(0.35), run_time=0.6)
        self.at(3)
        self.play(FadeIn(exc2, scale=0.8), FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(stack, st_l, child, moved, exc2, q)), run_time=0.6)

        # ================= the tree =================
        din = node("dinner", DINNER, w=2.6).move_to(DIN_P)
        crs = node("coroutineScope", COURSE, w=3.3, mono=True, size=24).move_to(CRS_P)
        crs_l = T("the main course", 24, COURSE).next_to(crs, RIGHT, buff=0.3)
        din_l = T("the root coroutine", 22, GREY_B).next_to(din, RIGHT, buff=0.3)
        dish = [node(n, c, w=2.8, icon=pot(c)).move_to([x, DISH_Y, 0]) for (n, c), x in zip(DISHES, DISH_X)]
        e1 = Line(din.get_bottom(), crs.get_top(), stroke_width=2.5, color=GREY_B)
        e2 = [Line(crs.get_bottom(), d.get_top(), stroke_width=2.5, color=GREY_B) for d in dish]
        kids_l = T("children: launch or async", 22, GREY_B).move_to([0, DISH_Y - 0.75, 0])
        self.say("tree")
        self.at(1)
        self.play(FadeIn(din), run_time=0.5)
        self.play(Create(e1), FadeIn(crs), run_time=0.7)
        self.play(*[Create(e) for e in e2], LaggedStart(*[FadeIn(d, shift=DOWN * 0.1) for d in dish], lag_ratio=0.2),
                  run_time=1.0)
        self.at_text("The dinner is", lead=0.3)
        self.play(FadeIn(din_l), run_time=0.5)
        self.at_text("the main course is", lead=0.3)
        self.play(FadeIn(crs_l), run_time=0.5)
        self.at_text("and the roast", lead=0.3)
        self.play(*[Indicate(d[1], color=d[1].get_color(), scale_factor=1.08) for d in dish], FadeIn(kids_l), run_time=1.0)
        self.hold()

        stm = [steam(d[2]) for d in dish]
        wait_l = T("a parent can't finish until all of its children have", 26, COURSE).move_to([0, -2.6, 0])
        self.say("tree2")
        self.play(*[Create(s) for s in stm], run_time=0.8)
        self.at(1)
        self.play(FadeOut(kids_l), FadeIn(wait_l, shift=UP * 0.1), run_time=0.6)
        self.at_text("a parent can't", lead=0.3)
        self.play(Indicate(crs[0], color=COURSE, scale_factor=1.04), run_time=0.8)
        self.hold()

        # ================= the roast burns =================
        fl = flame(1.0).move_to(dish[0][2].get_top() + UP * 0.32)
        burn_l = T("BurnedException at 100 ms", 22, BAD).move_to([DISH_X[0], DISH_Y - 0.75, 0])
        need = T("needs 1,000 ms", 22, POTS).move_to([DISH_X[1], DISH_Y - 0.75, 0])
        qq = T("keep cooking? when does the caller hear?", 26).move_to([0, -2.6, 0])
        self.say("burn_q")
        self.play(FadeOut(wait_l), FadeOut(stm[0]), FadeIn(fl, scale=0.6), dish[0][0].animate.set_stroke(BAD), run_time=0.7)
        self.at(2)
        self.play(FadeIn(burn_l), run_time=0.4)
        self.at(3)
        self.play(FadeIn(need), run_time=0.5)
        self.at(4)
        self.play(FadeIn(qq), run_time=0.5)
        self.hold(after=0)
        self.predict()

        def step_l(text):
            return T(text, 26, WHITE).move_to([0, -2.65, 0])

        a1 = up_arrow(dish[0], crs, BAD).shift(LEFT * 0.0)
        s1 = step_l("1. the roast reports the exception to its parent")
        self.say("s1")
        self.play(FadeOut(qq), FadeOut(need), run_time=0.4)
        self.at(1)
        self.play(GrowArrow(a1), FadeIn(s1), run_time=0.8)
        self.hold()

        a2 = [down_arrow(crs, d, CANCEL) for d in dish[1:]]
        offs = [T("off the heat", 22, OFF).move_to([d.get_x(), DISH_Y - 0.75, 0]) for d in dish[1:]]
        fin = [T("finally runs", 20, CANCEL).next_to(d, UP, buff=0.12).shift(RIGHT * 0.95) for d in dish[1:]]
        s2 = step_l("2. the course is cancelled, so it cancels its children")
        self.say("s2")
        self.play(FadeOut(s1), FadeIn(s2), crs[0].animate.set_stroke(BAD), run_time=0.6)
        self.at_text("a cancelled job", lead=0.3)
        self.play(*[GrowArrow(a) for a in a2], run_time=0.8)
        self.at(1)
        self.play(*[FadeOut(s) for s in stm[1:]], *[d.animate.set_opacity(0.4) for d in dish[1:]],
                  *[FadeIn(o) for o in offs], run_time=0.8)
        self.at_text("finally blocks", lead=0.3)
        self.play(*[FadeIn(f) for f in fin], run_time=0.5)
        self.hold()

        s3 = step_l("3. the course waits until they have stopped")
        stopped = [tick(True, 0.18).next_to(o, RIGHT, buff=0.12) for o in offs]
        self.say("s3")
        self.play(FadeOut(s2), FadeIn(s3), run_time=0.5)
        self.play(*[Create(t) for t in stopped], run_time=0.6)
        self.hold()

        a4 = up_arrow(crs, din, BAD).shift(LEFT * 0.55)
        chipx = VGroup(RoundedRectangle(corner_radius=0.06, width=2.4, height=0.45).set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.3), 1),
                       M("BurnedException", 20, BAD))
        chipx[1].move_to(chipx[0])
        chipx.next_to(a4, LEFT, buff=0.15)
        s4 = step_l("4. coroutineScope throws it to its caller")
        heard = T("caught", 24, GREEN_M).next_to(din, LEFT, buff=0.3)
        self.say("s4")
        self.play(FadeOut(s3), FadeIn(s4), FadeOut(din_l), run_time=0.5)
        self.play(GrowArrow(a4), FadeIn(chipx, shift=UP * 0.3), run_time=0.8)
        self.at(1)
        self.play(FadeIn(heard), run_time=0.5)
        self.hold()

        sm = T("one exception, where the work started: about 100 ms", 26, YELLOW_M).move_to([0, -2.65, 0])
        self.say("sum")
        self.play(FadeOut(s4), FadeIn(sm), run_time=0.6)
        self.at(1)
        self.play(Indicate(sm, color=YELLOW_M, scale_factor=1.04), run_time=0.8)
        self.hold()
        tree_all = VGroup(din, crs, crs_l, *dish, e1, *e2, fl, burn_l, a1, *a2, *offs, *fin, *stopped, a4, chipx, heard, sm, stm[0])
        self.play(FadeOut(tree_all), run_time=0.6)

        # ================= the demo log =================
        logt = T("FailureSpreads, on a busy machine", 26, GREY_B).move_to([0, 2.7, 0])
        log = VGroup(M("[   6 ms] scope body finished; the scope now waits for its children", 22, GREY_A),
                     M("[ 161 ms] roast: burned, throwing BurnedException", 22, ROAST),
                     M("[ 163 ms] potatoes: finally block runs", 22, POTS),
                     M("[ 165 ms] caller caught: the roast burned", 22, GREEN_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(log, 12.4).move_to([0, 1.2, 0])
        never = VGroup(M("potatoes: done", 24, GREY_C), T("never printed", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        never.move_to([0, -0.3, 0])
        nx = Line(never[0].get_left(), never[0].get_right(), stroke_width=3, color=BAD)
        self.say("demo")
        self.play(FadeIn(logt), FadeIn(log[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(log[1], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(log[2], shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(log[3], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(never), Create(nx), run_time=0.6)
        self.hold()

        apron = T("a JVM that just started: still finding its apron", 24, GREY_A).move_to([0, -1.35, 0])
        hl161 = SurroundingRectangle(log[1][1:4], buff=0.06, color=YELLOW_M, stroke_width=2.5)
        self.say("demo_joke")
        self.play(Create(hl161), run_time=0.5)
        self.at_text("still finding", lead=0.4)
        self.play(FadeIn(apron, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(logt, log, never, nx, apron, hl161)), run_time=0.6)

        # ================= break the executor picture =================
        ax = VGroup(Arrow([tx(0) - 0.1, -2.5, 0], [tx(1000) + 0.6, -2.5, 0], buff=0, stroke_width=2.5, color=GREY_B,
                          max_tip_length_to_length_ratio=0.03),
                    *[VGroup(Line([tx(m), -2.57, 0], [tx(m), -2.43, 0], stroke_width=2, color=GREY_B),
                             T(f"{m:,}", 20, GREY_B).move_to([tx(m), -2.8, 0])) for m in (0, 100, 1000)])

        def tbar(ms0, ms1, y, color, op=0.45):
            return Rectangle(width=(ms1 - ms0) * PX, height=0.34).set_stroke(color, 2).set_fill(dim(color, op), 1).move_to(
                [(tx(ms0) + tx(ms1)) / 2, y, 0])

        kt = T("Kotlin: coroutineScope", 24, COURSE).move_to([tx(0) - 0.2, 1.75, 0], aligned_edge=RIGHT)
        k_r = tbar(0, 161, 2.1, ROAST)
        k_p = tbar(0, 163, 1.55, POTS)
        k_rl = T("roast", 20, ROAST).next_to(k_r, RIGHT, buff=0.12)
        k_pl = T("potatoes: stopped at 163 ms", 20, POTS).next_to(k_p, RIGHT, buff=0.12)
        jt = T("Java: an executor", 24, GREY_A).move_to([tx(0) - 0.2, -0.15, 0], aligned_edge=RIGHT)
        j_r = tbar(0, 100, 0.2, ROAST)
        j_p = tbar(0, 1000, -0.35, POTS)
        j_rl = T("roast fails", 20, BAD).next_to(j_r, RIGHT, buff=0.12)
        j_pl = T("potatoes: done, at about 1,000 ms", 20, WHITE).move_to(j_p)
        cls = T("close() waits for them", 22, GREY_A).next_to(j_p, DOWN, buff=0.2).align_to(j_p, RIGHT)
        self.say("java")
        self.play(FadeIn(ax), FadeIn(kt), GrowFromEdge(k_r, LEFT), GrowFromEdge(k_p, LEFT), FadeIn(k_rl), FadeIn(k_pl),
                  run_time=0.9)
        self.at(1)
        self.play(FadeIn(jt), run_time=0.5)
        self.at_text("the roast fails", lead=0.3)
        self.play(GrowFromEdge(j_r, LEFT), FadeIn(j_rl), run_time=0.6)
        self.play(GrowFromEdge(j_p, LEFT), run_time=1.4)
        self.play(FadeIn(j_pl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cls), run_time=0.5)
        self.hold()

        peel = T("on fire, and still being lovingly peeled", 24, BAD).move_to([2.0, -1.35, 0])
        by = tbar(0, 198, -1.75, POTS)
        by_l = T("cancelled by hand: finally at 198 ms", 20, POTS).next_to(by, RIGHT, buff=0.12)
        self.say("java_joke")
        self.play(FadeIn(peel, shift=UP * 0.1), Wiggle(j_p, scale_value=1.03), run_time=1.0)
        self.at(1)
        self.play(FadeOut(peel), cls.animate.set_opacity(0.0), run_time=0.4)
        self.play(GrowFromEdge(by, LEFT), FadeIn(by_l), run_time=0.7)
        self.at(3)
        self.play(Indicate(kt, color=COURSE, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(ax, kt, k_r, k_p, k_rl, k_pl, jt, j_r, j_p, j_rl, j_pl, cls, by, by_l)), run_time=0.6)

        # ================= cancel goes down =================
        din = node("dinner", DINNER, w=2.6).move_to(DIN_P)
        crs = node("coroutineScope", COURSE, w=3.3, mono=True, size=24).move_to(CRS_P)
        crs_l = T("the main course", 24, COURSE).next_to(crs, RIGHT, buff=0.3)
        dish = [node(n, c, w=2.8, icon=pot(c)).move_to([x, DISH_Y, 0]) for (n, c), x in zip(DISHES, DISH_X)]
        e1 = Line(din.get_bottom(), crs.get_top(), stroke_width=2.5, color=GREY_B)
        e2 = [Line(crs.get_bottom(), d.get_top(), stroke_width=2.5, color=GREY_B) for d in dish]
        stm = [steam(d[2]) for d in dish]
        tree = VGroup(din, crs, crs_l, *dish, e1, *e2, *stm)
        gph = phone(1.0).move_to([-4.6, 2.45, 0])
        g_l = T("the guests call it off", 22, GREY_A).next_to(gph, DOWN, buff=0.15)
        self.play(FadeIn(tree), run_time=0.7)
        self.say("cancel")
        self.at(1)
        self.play(FadeIn(gph), FadeIn(g_l), Wiggle(gph, scale_value=1.15), run_time=0.9)
        cg = Arrow(gph.get_right(), din.get_left(), buff=0.15, stroke_width=4, color=CANCEL, max_tip_length_to_length_ratio=0.2)
        self.at(2)
        self.play(GrowArrow(cg), din.animate.set_opacity(0.45), run_time=0.6)
        self.at(3)
        c1 = down_arrow(din, crs, CANCEL).shift(RIGHT * 0.55)
        self.play(GrowArrow(c1), crs.animate.set_opacity(0.45), run_time=0.6)
        cs = [down_arrow(crs, d, CANCEL) for d in dish]
        self.play(*[GrowArrow(c) for c in cs], *[FadeOut(s) for s in stm], *[d.animate.set_opacity(0.4) for d in dish],
                  run_time=0.8)
        down_l = T("a cancel travels down", 26, CANCEL).move_to([0, -2.6, 0])
        self.play(FadeIn(down_l), run_time=0.5)
        self.hold()

        # reset, then cancel only the gravy
        self.play(FadeOut(VGroup(gph, g_l, cg, c1, *cs, down_l)), din.animate.set_opacity(1), crs.animate.set_opacity(1),
                  *[d.animate.set_opacity(1) for d in dish], run_time=0.7)
        stm = [steam(d[2]) for d in dish]
        sc = Arrow(dish[2].get_right() + RIGHT * 0.9 + UP * 0.6, dish[2].get_right() + RIGHT * 0.1 + UP * 0.1, buff=0,
                   stroke_width=4, color=CANCEL, max_tip_length_to_length_ratio=0.25)
        sc_l = M("cancel()", 22, CANCEL).next_to(sc.get_start(), UP, buff=0.08)
        uq = T("only the gravy is cancelled. Does the course stop?", 26).move_to([0, -2.6, 0])
        self.say("up_q")
        self.play(*[Create(s) for s in stm], run_time=0.5)
        self.at(1)
        self.play(GrowArrow(sc), FadeIn(sc_l), FadeOut(stm[2]), dish[2].animate.set_opacity(0.4), run_time=0.8)
        self.at(2)
        self.play(FadeIn(uq), run_time=0.5)
        self.hold(after=0)
        self.predict()
        ua = up_arrow(dish[2], crs, CANCEL)
        ux = tick(False, 0.22).move_to(ua.get_center())
        ce = T("counts as cancelled, not failed", 24, CANCEL).move_to([DISH_X[2], DISH_Y - 0.8, 0])
        go_on = T("carry on", 24, GREEN_M).move_to([(DISH_X[0] + DISH_X[1]) / 2, DISH_Y - 0.8, 0])
        self.say("up_a")
        self.play(FadeOut(uq), GrowArrow(ua), run_time=0.6)
        self.play(Create(ux), run_time=0.4)
        self.at(2)
        self.play(FadeIn(ce), run_time=0.5)
        self.at(3)
        self.play(FadeIn(go_on), Circumscribe(dish[0], color=GREEN_M, buff=0.08), Circumscribe(dish[1], color=GREEN_M, buff=0.08),
                  run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(tree, *stm, sc, sc_l, ua, ux, ce, go_on)), run_time=0.6)

        # ================= name it =================
        nm = T("structured concurrency", 42, COURSE).move_to([0, 2.5, 0])
        gl = T("work that runs at the same time has the same nested shape as the code", 26).next_to(nm, DOWN, buff=0.3)
        fit(gl, 12.4)
        up_r = VGroup(Arrow(DOWN * 0.5, UP * 0.5, buff=0, stroke_width=5, color=BAD, max_tip_length_to_length_ratio=0.3),
                      T("A failure goes up the tree and stops the siblings.", 30, BAD)).arrange(RIGHT, buff=0.35)
        dn_r = VGroup(Arrow(UP * 0.5, DOWN * 0.5, buff=0, stroke_width=5, color=CANCEL, max_tip_length_to_length_ratio=0.3),
                      T("A cancel goes down, and stops there.", 30, CANCEL)).arrange(RIGHT, buff=0.35)
        rules = VGroup(up_r, dn_r).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, -0.4, 0])
        fit(rules, 12.0)
        self.say("name")
        self.play(Write(nm), run_time=1.0)
        self.play(FadeIn(gl, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(up_r, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dn_r, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        # why it's the default, and the supervisor
        self.play(FadeOut(gl), VGroup(nm, rules).animate.scale(0.75).move_to([0, 1.75, 0]), run_time=0.7)
        wasted = T("the roast is ruined, so the course is off: finishing the rest is wasted", 26, GREY_A).move_to([0, -0.45, 0])
        fit(wasted, 12.4)
        rem = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=1.6, height=0.6).set_stroke(GREEN_M, 2.5)
                              .set_fill(dim(GREEN_M, 0.15), 1), T(t, 24, GREEN_M)) for t in ("text", "email", "phone")])
        for r in rem:
            r[1].move_to(r[0])
        rem.arrange(RIGHT, buff=0.4).move_to([-1.8, -1.65, 0])
        any1 = T("any one is enough", 24, GREEN_M).next_to(rem, DOWN, buff=0.2)
        sup = VGroup(T("a supervisor", 28, GREEN_M), T("lesson 6", 22, GREY_B)).arrange(DOWN, buff=0.1).next_to(rem, RIGHT, buff=0.8)
        self.say("why")
        self.at(1)
        self.play(FadeIn(wasted, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rem], lag_ratio=0.2), FadeIn(any1), run_time=0.9)
        self.at(3)
        self.play(FadeIn(sup, shift=LEFT * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(wasted, rem, any1, sup, nm, rules)), run_time=0.5)

        # where the picture breaks: a cancel is heard at the next suspension point
        busy = Rectangle(width=6.0, height=0.45).set_stroke(GRAVY, 2.5).set_fill(dim(GRAVY, 0.4), 1).move_to([0, -0.3, 0])
        busy_l = T("a long calculation, no suspension point", 22, WHITE).move_to(busy)
        sp = Line(busy.get_right() + UP * 0.45, busy.get_right() + DOWN * 0.45, stroke_width=4, color=YELLOW_M)
        sp_l = T("next suspension point", 22, YELLOW_M).next_to(sp, DOWN, buff=0.15)
        ca = Arrow(busy.get_left() + RIGHT * 1.6 + UP * 1.1, busy.get_left() + RIGHT * 1.6 + UP * 0.3, buff=0, stroke_width=4,
                   color=CANCEL, max_tip_length_to_length_ratio=0.3)
        ca_l = M("cancel", 22, CANCEL).next_to(ca, UP, buff=0.08)
        heard = T("heard here", 22, CANCEL).next_to(sp, RIGHT, buff=0.2)
        l5 = T("lesson 5: how to cooperate", 22, GREY_B).move_to([0, -2.5, 0])
        self.say("breaks")
        self.play(FadeIn(busy), FadeIn(busy_l), run_time=0.6)
        self.at_text("hears the cancel", lead=0.3)
        self.play(GrowArrow(ca), FadeIn(ca_l), run_time=0.6)
        self.at_text("next suspension point", lead=0.4)
        self.play(Create(sp), FadeIn(sp_l), run_time=0.6)
        self.play(FadeIn(heard), run_time=0.4)
        self.at(3)
        self.play(FadeIn(l5), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        k2 = code_block(["try {", "    coroutineScope {", "        launch { roast() }      // throws at 100 ms",
                         "        launch { potatoes() }   // needs 1,000 ms", "    }",
                         "} catch (e: BurnedException) { println(\"caught: ${e.message}\") }"], 22,
                        {"coroutineScope": COURSE, "// throws at 100 ms": GREY_B, "// needs 1,000 ms": GREY_B})
        j2 = code_block(["try (var kids = Executors.newVirtualThreadPerTaskExecutor()) {",
                         "    var roast = kids.submit(() -> roast());",
                         "    var potatoes = kids.submit(() -> potatoes());",
                         "    try { roast.get(); }",
                         "    catch (ExecutionException e) { potatoes.cancel(true); }  // by hand",
                         "}"], 22, {"potatoes.cancel(true);": CANCEL, "// by hand": GREY_B})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k2).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java (JDK 21+)", 24, GREY_B), j2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(k2[1], color=COURSE, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(Indicate(j2[4], color=CANCEL, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Where does a child's exception go? Up the tree, to its parent.", 32).move_to(UP * 2.4)
        m1 = T("The parent stops the siblings, waits, and hands one exception on.", 30, BAD).move_to(UP * 1.55)
        m2 = T("A cancel only ever travels down.", 32, CANCEL).move_to(UP * 0.8)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M), T("someone cancels just the potatoes.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("What happens to the roast, the gravy and the course?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("nothing: cancelled isn't failed, so the course isn't told", 30, CANCEL).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
