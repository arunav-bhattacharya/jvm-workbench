from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"withContext\(NonCancellable\)", "with context of non cancellable"), (r"withContext\(IO\)", "with context of I O"),
    (r"\bjob\.cancel\(\)", "job dot cancel"), (r"\bFuture\.cancel\(true\)", "Future dot cancel true"),
    (r"\bCancellationException\b", "Cancellation Exception"), (r"\bNonCancellable\b", "non cancellable"),
    (r"\bensureActive\b", "ensure active"), (r"\bisActive\b", "is active"), (r"\bcountStones\b", "count stones"),
    (r"\bgiveBack\b", "give back"), (r"\bwithTimeout\b", "with timeout"), (r"\bwithContext\b", "with context"),
    (r"\brunInterruptible\b", "run interruptible"), (r"\bcancelAndJoin\b", "cancel and join"),
    (r"\bThread\.sleep\b", "Thread dot sleep"), (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
]

# every spoken line, in order
N = {
    "open": "Halfway through the afternoon, the phone rings. The guests can't come: dinner is off. The cook turns the "
            "heat down, puts a lid on the soup, and takes the sauce off the stove. She heard the news between two steps "
            "of a recipe, when she glanced at her phone.",
    "helper": "Her helper in the corner is picking small stones out of a big sack of lentils. He never looks up between "
              "lentils. So he hears nothing, and he sorts the whole sack.",
    "shyq": "So here's a question that's easy to be shy about. When you cancel a coroutine, doesn't it just stop? "
            "How could it keep going?",
    "asks": "It's natural to think cancel stops the code. It doesn't. It only asks, and the code has to look up.",
    "job": "Every coroutine has a job, the handle to its life. job.cancel() marks that job as cancelling, and that's all. "
           "It doesn't stop the thread, the worker running the code.",
    "point": "The coroutine finds out at its next suspension point, a call where it may pause, such as delay, await or "
             "withContext. That's the cook glancing at her phone between steps.",
    "throw": "Those calls look at the job first. If it's cancelled, they throw CancellationException, the exception that "
             "carries a cancel. Every finally block runs on the way out, and the job ends as cancelled.",
    "loop": "Now the helper, in code. countStones goes through the lentils and counts the stones. It's pure calculation, "
            "with no waiting, so there's no suspension point anywhere in the loop.",
    "pred": "The lesson's demo gives four loops 60 million lentils each, on Default, and cancels each one 100 milliseconds "
            "after it starts. The first loop has no check. How long after the cancel does it stop?",
    "show": "2,851 milliseconds. It didn't stop when it was asked. It stopped when the sack was empty.",
    "joke": "Very thorough. Not a great listener. So the point is: a cancel only asks, and code that never looks up never "
            "hears it.",
    "fix": "The other three loops look up now and then. ensureActive throws CancellationException once the job is "
           "cancelled. isActive is a plain true or false, for a loop that stops quietly. And yield checks too, and lets "
           "others have a turn. They stopped 10, 4 and 1 millisecond after the cancel.",
    "cheap": "A check only reads the job's state, so it costs almost nothing. Once every thousand lentils is plenty.",
    "code": "Here's the loop with the check, in Kotlin, and its Java match. Java's Future.cancel(true) works the same way: "
            "it sets the thread's interrupt flag, and the loop has to read it.",
    "name": "This is cooperative cancellation. Cancelling asks, and the code stops the next time it checks.",
    "pan": "Now the cleanup. The cook is making jam in a big pan borrowed from the community kitchen, and the pan must go "
           "back, whatever happens. Giving it back means phoning the lending desk, so giveBack is a suspend function. "
           "It goes in a finally block.",
    "pan_q": "The jam is called off while it sets. Does the pan go back?",
    "pan_a": "No. The finally block runs, but inside a coroutine that is still cancelled, and there, every suspension point "
             "throws at once. giveBack fails before the phone even rings. The community kitchen would like a word.",
    "nc": "The fix is one wrapper: withContext(NonCancellable). NonCancellable is a job that is always active, so inside "
          "it, suspension points don't throw. The pan went back about 50 milliseconds after the cancel, and then the "
          "cancel carried on up, as before.",
    "timer": "Last, the timer. The cook sets a kitchen timer on the bread order: if the bakery hasn't answered in time, "
             "she bakes her own. withTimeout is that timer: when it runs out, it cancels the block. "
             "A timeout is a cancel with a timer.",
    "t1": "The bakery takes one and a half seconds, and we wait 300 milliseconds. With delay standing in for the call, "
          "the timer works: 307 milliseconds.",
    "t2": "But the bakery's old phone line blocks the thread until somebody picks up. Wrapped in withContext(IO), the timer "
          "fired at 300, and the caller still waited 1,519 milliseconds. The thread stayed on the line, listening to it "
          "ring, long after the timer gave up.",
    "t3": "runInterruptible fixes that. On a cancel, it interrupts the blocked thread, and the same call came back in "
          "301 milliseconds.",
    "breaks": "Here the kitchen picture breaks. A cook can hang up whenever she likes. runInterruptible can only interrupt, "
              "and that helps only if the call listens. Thread.sleep does; some old network clients don't.",
    "moral": "So, does cancel just stop a coroutine? No. It asks. The coroutine hears it at its next suspension point or "
             "check, carries it out as an exception, and needs NonCancellable to clean up. And a timeout is the same "
             "request, with a timer.",
    "check": "Quick check. A loop on Default weighs jars forever, with plain function calls and no checks. "
             "You call cancelAndJoin. What happens?",
    "check_a": "It never returns. Nothing in the loop ever looks up. Add ensureActive, and it stops at the next check.",
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


# one colour per thing, for the whole coroutines track (cook blue, cancel yellow, failure red, as in co-03)
COOK, HELPER, CANCEL, SUSP, BAD, PAN, SAFE, TIMER, OFF = (BLUE_M, TEAL_M, YELLOW_M, PURPLE_M, RED_M, GOLD_M, TEAL_M,
                                                          GREEN_M, GREY_C)


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


def lid(p, color):
    arc = Arc(radius=0.42, start_angle=0.2, angle=PI - 0.4).set_stroke(color, 3)
    arc.stretch(0.45, 1).move_to(p.get_top() + UP * 0.1)
    knob = Dot(arc.get_top() + UP * 0.04, radius=0.05, color=color)
    return VGroup(arc, knob)


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


def sack(s=1.0):
    body = VMobject().set_points_smoothly([[-0.4, -0.45, 0], [-0.48, 0.0, 0], [-0.3, 0.35, 0], [0.3, 0.35, 0],
                                           [0.48, 0.0, 0], [0.4, -0.45, 0], [-0.4, -0.45, 0]])
    body.set_stroke(GREY_B, 2.5).set_fill(dim(GOLD_M, 0.25), 1)
    tie = Line([-0.18, 0.42, 0], [0.18, 0.42, 0], stroke_width=3, color=GREY_B)
    dots = VGroup(*[Dot([x, y, 0], radius=0.035, color=GOLD_M) for x, y in ((-0.15, 0.0), (0.05, -0.12), (0.2, 0.08),
                                                                           (-0.05, 0.15), (0.12, -0.28), (-0.22, -0.22))])
    return VGroup(body, tie, dots).scale(s)


def bowl(color=GREY_A, s=1.0):
    arc = Arc(radius=0.45, start_angle=PI, angle=PI).set_stroke(color, 3)
    top = Line(LEFT * 0.45, RIGHT * 0.45, stroke_width=3, color=color)
    return VGroup(arc, top).scale(s)


def timer(color=TIMER, s=1.0):
    face = Circle(radius=0.36).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    knob = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.13).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    knob.next_to(face, UP, buff=0)
    hand = Line(ORIGIN, UP * 0.25, stroke_width=3, color=color)
    ticks = VGroup(*[Line(UP * 0.28, UP * 0.34, stroke_width=2, color=color).rotate(a, about_point=ORIGIN)
                     for a in np.arange(0, TAU, TAU / 8)])
    return VGroup(face, knob, ticks, hand).scale(s)


def jam_pan(s=1.0):
    body = RoundedRectangle(corner_radius=0.14, width=1.2, height=0.5).set_stroke(PAN, 3).set_fill(dim(PAN, 0.2), 1)
    jam = RoundedRectangle(corner_radius=0.1, width=1.0, height=0.22).set_stroke(width=0).set_fill(dim(BAD, 0.7), 1)
    jam.move_to(body.get_top() + DOWN * 0.15)
    handle = Line(body.get_right() + UP * 0.12, body.get_right() + RIGHT * 0.65 + UP * 0.22, stroke_width=6, color=PAN)
    return VGroup(body, jam, handle).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def block(x0, x1, y, label, color, h=0.55, size=22):
    r = RoundedRectangle(corner_radius=0.08, width=x1 - x0, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    r.move_to([(x0 + x1) / 2, y, 0])
    return VGroup(r, T(label, size, color).move_to(r))


def ghost(x0, x1, y, label, h=0.55, size=22):
    r = DashedVMobject(RoundedRectangle(corner_radius=0.08, width=x1 - x0, height=h).set_stroke(OFF, 2)
                       .move_to([(x0 + x1) / 2, y, 0]), num_dashes=30)
    return VGroup(r, T(label, size, OFF).move_to([(x0 + x1) / 2, y, 0]))


def glance(x, y):
    """A suspension point: the cook glances at her phone between steps."""
    return Square(side_length=0.2).rotate(PI / 4).set_stroke(SUSP, 2.5).set_fill(dim(SUSP, 0.6), 1).move_to([x, y, 0])


def bar(x0, x1, y, color, h=0.4):
    return Rectangle(width=max(0.02, x1 - x0), height=h).set_stroke(color, 2).set_fill(dim(color, 0.4), 1).move_to(
        [(x0 + x1) / 2, y, 0])


# the two lanes, as they sit on screen
COOK_Y, HELP_Y = -0.15, -1.8
STEPS = [(-4.2, -2.2, "chop"), (-1.85, 0.15, "brown"), (0.5, 2.5, "simmer"), (2.85, 4.85, "season")]
GAPS = (-2.025, 0.325, 2.675)
RING_X = -0.9


class Co05Cancel(Narrated):
    """co-05, section 0: a cancel is a request. Dinner is called off: the cook hears it between steps, her helper
    sorting lentils never looks up (two lanes, one cancel line); the shy question (doesn't cancel just stop it?); job,
    suspension point, CancellationException mapped onto the lanes; countStones with no check stops 2,851 ms after the
    cancel, the three checks stop in 10, 4 and 1 ms; the code; cooperative cancellation named; the borrowed jam pan
    (finally fails at once, NonCancellable gives it back); the timer on the bread order (307, 1,519 and 301 ms);
    where the picture breaks; the moral and a check."""

    def construct(self):
        self.title_card("The phone call between steps", "how a coroutine hears a cancel")

        # ================= the cook hears the news between steps =================
        cook = person(COOK, 1.2).move_to([-5.4, 2.0, 0])
        soup = pot(GOLD_M, 0.8).move_to([-4.1, 1.85, 0])
        sauce = pot(TEAL_M, 0.8).move_to([-2.8, 1.85, 0])
        f1 = flame(0.55).move_to(soup.get_bottom() + DOWN * 0.22)
        f2 = flame(0.55).move_to(sauce.get_bottom() + DOWN * 0.22)
        ph = phone(0.9).move_to([-6.1, 2.85, 0])
        lane_c = T("the cook", 24, COOK).move_to([-6.3, COOK_Y, 0], aligned_edge=LEFT)
        blocks = [block(a, b, COOK_Y, lbl, COOK) for a, b, lbl in STEPS]
        marks = [glance(x, COOK_Y) for x in GAPS]
        self.say("open")
        self.play(FadeIn(cook), FadeIn(soup), FadeIn(sauce), FadeIn(f1), FadeIn(f2), FadeIn(ph), FadeIn(lane_c), run_time=0.7)
        self.play(GrowFromEdge(blocks[0], LEFT), run_time=0.8)
        self.play(FadeIn(marks[0], scale=0.5), run_time=0.25)
        part = block(-1.85, RING_X, COOK_Y, "", COOK)
        self.play(GrowFromEdge(part, LEFT), run_time=0.5)
        self.at_text("the phone rings", lead=0.3)
        ring = Line([RING_X, COOK_Y + 0.75, 0], [RING_X, HELP_Y - 0.4, 0], stroke_width=4, color=CANCEL)
        ring_l = T("the phone rings", 24, CANCEL).move_to([RING_X, COOK_Y + 0.95, 0])
        bub = VGroup(RoundedRectangle(corner_radius=0.18, width=2.6, height=0.55).set_stroke(CANCEL, 2).set_fill(BLACK, 1),
                     T("dinner is off", 24, CANCEL))
        bub[1].move_to(bub[0])
        bub.move_to([-4.3, 3.0, 0])
        self.play(Wiggle(ph, scale_value=1.3, rotation_angle=0.08 * TAU), Create(ring), FadeIn(ring_l), run_time=0.9)
        self.at(1)
        self.play(FadeIn(bub, scale=0.8), run_time=0.5)
        self.at(2)
        part2 = block(RING_X, 0.15, COOK_Y, "", COOK)
        self.play(GrowFromEdge(part2, LEFT), run_time=0.5)
        self.remove(part, part2)
        self.add(blocks[1])
        heard = Circle(radius=0.26).set_stroke(CANCEL, 3).move_to(marks[1])
        self.play(FadeIn(marks[1], scale=0.5), run_time=0.3)
        self.play(Create(heard), run_time=0.4)
        lid_s = lid(soup, GOLD_M)
        self.play(FadeOut(f1), FadeIn(lid_s, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeOut(f2), sauce.animate.shift(RIGHT * 0.5 + UP * 0.1), run_time=0.6)
        ghosts = [ghost(a, b, COOK_Y, lbl) for a, b, lbl in STEPS[2:]]
        self.play(*[FadeIn(g) for g in ghosts], run_time=0.6)
        self.at(3)
        self.play(Indicate(marks[1], color=SUSP, scale_factor=1.6), run_time=0.9)
        self.hold()

        helper = person(HELPER, 1.2).move_to([2.6, 2.0, 0])
        sk = sack(1.0).move_to([3.75, 1.9, 0])
        bw = bowl(GREY_A, 0.9).move_to([5.0, 1.75, 0])
        lane_h = T("her helper", 24, HELPER).move_to([-6.3, HELP_Y, 0], aligned_edge=LEFT)
        hbar = block(-4.2, 6.0, HELP_Y, "", HELPER)
        hbar[1].become(T("sorting lentils, never looking up", 22, HELPER).move_to([2.6, HELP_Y, 0]))
        whole = T("the whole sack", 24, HELPER).move_to([4.9, HELP_Y - 0.65, 0])
        self.say("helper")
        self.play(FadeIn(helper), FadeIn(sk), FadeIn(bw), FadeIn(lane_h), run_time=0.7)
        self.at(1)
        beans = VGroup(*[Dot(sk.get_center() + UP * 0.1, radius=0.04, color=GOLD_M) for _ in range(6)])
        self.add(beans)
        self.play(GrowFromEdge(hbar, LEFT),
                  LaggedStart(*[b.animate.move_to(bw.get_center() + UP * 0.05 + RIGHT * (0.12 * k - 0.3))
                                for k, b in enumerate(beans)], lag_ratio=0.3), run_time=3.2)
        self.at_text("he sorts the whole", lead=0.3)
        self.play(FadeIn(whole), Indicate(hbar[1], color=HELPER, scale_factor=1.05), run_time=0.8)
        self.hold()

        # ================= the shy question =================
        icons = VGroup(cook, soup, sauce, lid_s, ph, bub, helper, sk, bw, beans)
        q = T("When you cancel a coroutine, doesn't it just stop?", 32).move_to([0, 2.55, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.play(FadeOut(icons), run_time=0.6)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        asks = T("It only asks. The code has to look up.", 34, CANCEL).move_to([0, 2.55, 0])
        self.say("asks")
        self.at(1)
        self.play(FadeOut(q), run_time=0.4)
        self.at(2)
        self.play(FadeIn(asks, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the map: job, suspension point, CancellationException =================
        jl = M("job.cancel()", 24, CANCEL).move_to(ring_l)
        jl2 = T("marks the job: cancelling", 22, GREY_A).next_to(jl, UP, buff=0.12)
        nostop = T("the thread keeps running", 22, GREY_A).move_to([3.2, COOK_Y + 0.95, 0])
        self.say("job")
        self.play(FadeOut(asks), run_time=0.4)
        self.at(1)
        self.play(FadeOut(ring_l), FadeIn(jl), run_time=0.6)
        self.play(FadeIn(jl2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(nostop), run_time=0.5)
        self.hold()

        sp_l = T("suspension points: delay, await, withContext", 22, SUSP).move_to([2.7, COOK_Y - 0.6, 0])
        self.say("point")
        self.play(FadeOut(nostop), run_time=0.3)
        self.play(LaggedStart(*[Indicate(m, color=SUSP, scale_factor=1.7) for m in marks], lag_ratio=0.3),
                  FadeIn(sp_l), run_time=1.2)
        self.at(1)
        self.play(Indicate(heard, color=CANCEL, scale_factor=1.3), run_time=0.8)
        self.hold()

        ce = VGroup(M("CancellationException", 22, CANCEL), T("finally blocks run, the job ends cancelled", 22, GREY_A))
        ce.arrange(DOWN, buff=0.12).move_to([3.1, COOK_Y + 1.0, 0])
        ce_ar = Arrow(ce.get_bottom() + LEFT * 1.6, heard.get_top() + RIGHT * 0.1, buff=0.08, stroke_width=3, color=CANCEL,
                      max_tip_length_to_length_ratio=0.2)
        cpu_l = T("a CPU loop: no suspension point, so it never hears", 22, HELPER).move_to([0.9, HELP_Y - 0.7, 0])
        self.say("throw")
        self.at(1)
        self.play(FadeIn(ce[0], shift=UP * 0.1), GrowArrow(ce_ar), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ce[1]), run_time=0.5)
        self.play(FadeOut(whole), FadeIn(cpu_l), run_time=0.6)
        self.hold()
        lanes = VGroup(lane_c, *blocks[:2], *marks, heard, *ghosts, ring, jl, jl2, sp_l, ce, ce_ar, lane_h, hbar, cpu_l)
        self.play(FadeOut(lanes), run_time=0.7)

        # ================= the helper in code, and the demo =================
        hl0 = {"for": SUSP, "stones++": HELPER}
        naive = code_block(["for (lentil in lentils) if (isStone(lentil)) stones++"], 26, hl0)
        naive_l = T("countStones, Kotlin: pure calculation, no suspension point", 24, GREY_B)
        ng = VGroup(naive_l, naive).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 2.45, 0])
        self.say("loop")
        self.play(FadeIn(ng, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(naive[0], color=HELPER, scale_factor=1.04), run_time=0.9)
        self.hold()

        X0, PX = -1.3, 7.3 / 3000           # x for 0 ms, units per ms
        rows_y = (0.75, -0.05, -0.85, -1.65)
        names = ["no check", "while (isActive)", "ensureActive() every 1,000", "yield() every 1,000"]
        stops = [2851, 4, 10, 1]
        labels = [M(n, 22, GREY_A).move_to([-6.3, y, 0], aligned_edge=LEFT) for n, y in zip(names, rows_y)]
        base = [bar(X0, X0 + 100 * PX, y, HELPER) for y in rows_y]
        cline = Line([X0 + 100 * PX, 1.25, 0], [X0 + 100 * PX, -2.15, 0], stroke_width=4, color=CANCEL)
        cl_l = M("cancel()", 22, CANCEL).next_to(cline, UP, buff=0.12)
        axis = VGroup(Line([X0, -2.55, 0], [X0 + 3000 * PX, -2.55, 0], stroke_width=2, color=GREY_C),
                      *[VGroup(Line([X0 + t * PX, -2.6, 0], [X0 + t * PX, -2.5, 0], stroke_width=2, color=GREY_C),
                               T(f"{t:,} ms", 20, GREY_B).move_to([X0 + t * PX, -2.85, 0])) for t in (0, 1000, 2000, 3000)])
        self.say("pred")
        self.play(FadeIn(labels[0]), FadeIn(base[0]), FadeIn(axis), run_time=0.7)
        self.at(1)
        self.play(Create(cline), FadeIn(cl_l), run_time=0.6)
        self.at(2)
        self.play(Indicate(labels[0], color=WHITE, scale_factor=1.08), run_time=0.8)
        self.hold(after=0)
        self.predict()

        tail0 = bar(X0 + 100 * PX, X0 + (100 + stops[0]) * PX, rows_y[0], BAD)
        r0 = T("stopped 2,851 ms after cancel()", 24, BAD).move_to([2.2, rows_y[0] + 0.48, 0])
        self.say("show")
        self.play(GrowFromEdge(tail0, LEFT), run_time=1.8)
        self.play(FadeIn(r0, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("joke")
        self.play(Wiggle(tail0, scale_value=1.04), run_time=0.9)
        self.hold()

        tails = [bar(X0 + 100 * PX, X0 + (100 + s) * PX + 0.03, y, GREEN_M) for s, y in zip(stops[1:], rows_y[1:])]
        res = [T(f"{s} ms", 24, GREEN_M).next_to(t, RIGHT, buff=0.2) for s, t in zip(stops[1:], tails)]
        self.say("fix")
        self.at(1)
        self.play(FadeIn(labels[2]), FadeIn(base[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(labels[1]), FadeIn(base[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(labels[3]), FadeIn(base[3]), run_time=0.5)
        self.at(4)
        self.play(*[GrowFromEdge(t, LEFT) for t in tails], run_time=0.5)
        self.play(LaggedStart(*[FadeIn(r) for r in (res[1], res[0], res[2])], lag_ratio=0.3), run_time=0.9)
        self.hold()
        cheap = T("a check only reads the job's state: once every 1,000 lentils is plenty", 24, GREY_A).move_to([0, -3.3, 0])
        fit(cheap, 12.4)
        self.say("cheap")
        self.play(FadeIn(cheap), run_time=0.6)
        self.hold()
        demo = VGroup(*labels, *base, cline, cl_l, axis, tail0, r0, *tails, *res, cheap, ng)
        self.play(FadeOut(demo), run_time=0.6)

        # ================= the code, and the name =================
        k_hl = {"ensureActive()": GREEN_M, "// throws once cancelled": GREY_B}
        ksrc = ["for ((i, lentil) in lentils.withIndex()) {",
                "    if (i % 1_000 == 0) context.ensureActive()   // throws once cancelled",
                "    if (isStone(lentil)) stones++",
                "}"]
        j_hl = {"isInterrupted()": GREEN_M}
        jsrc = ["for (int i = 0; i < lentils.length; i++) {",
                "    if (i % 1_000 == 0 && Thread.currentThread().isInterrupted())",
                "        throw new CancellationException();",
                "    if (isStone.test(lentils[i])) stones++;",
                "}"]
        kc, jc = code_block(ksrc, 22, k_hl), code_block(jsrc, 22, j_hl)
        cols = VGroup(VGroup(T("Kotlin (context = currentCoroutineContext())", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.75, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(kc[1], color=GREEN_M, scale_factor=1.03), run_time=0.8)
        self.play(Indicate(jc[1], color=GREEN_M, scale_factor=1.03), run_time=0.8)
        self.hold()
        nm = VGroup(T("cooperative cancellation", 32, CANCEL), T("cancelling asks; the code stops the next time it checks", 26, GREY_A))
        nm.arrange(DOWN, buff=0.18).move_to([0, -2.6, 0])
        self.say("name")
        self.play(FadeIn(nm[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(nm[1]), run_time=0.6)
        self.hold()
        self.play(FadeOut(cols), FadeOut(nm), run_time=0.6)

        # ================= the borrowed jam pan =================
        jp = jam_pan(1.1).move_to([-4.5, 2.3, 0])
        tk = VGroup(RoundedRectangle(corner_radius=0.05, width=1.3, height=0.42).set_stroke(PAN, 2).set_fill(dim(PAN, 0.25), 1),
                    M("ticket-7", 20, PAN))
        tk[1].move_to(tk[0])
        tk.next_to(jp, DOWN, buff=0.2)
        desk = VGroup(RoundedRectangle(corner_radius=0.1, width=2.9, height=1.0).set_stroke(GREY_A, 2.5).set_fill(GREY_E, 1),
                      T("the lending desk", 24, GREY_A))
        desk[1].move_to(desk[0])
        desk.move_to([4.6, 2.3, 0])
        dph = phone(0.7).next_to(desk, LEFT, buff=0.25)
        p_hl = {"finally": SUSP, "desk.giveBack(ticket)": PAN, "// cancelled here": GREY_B, "// suspends": GREY_B}
        psrc = ["val ticket = desk.lend(\"jam-pan\")", "try {", "    waitForTheJamToSet()      // cancelled here",
                "} finally {", "    desk.giveBack(ticket)     // suspends", "}"]
        pc = code_block(psrc, 24, p_hl).move_to([-1.3, -0.65, 0])
        self.say("pan")
        self.play(FadeIn(jp, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(desk), FadeIn(dph), FadeIn(tk), run_time=0.6)
        self.at(2)
        self.play(FadeIn(pc[0]), FadeIn(pc[1]), FadeIn(pc[2]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(pc[3:]), run_time=0.6)
        self.hold()

        cx = T("cancel", 24, CANCEL).next_to(pc[2], RIGHT, buff=0.6)
        cxa = Arrow(cx.get_left(), pc[2].get_right() + RIGHT * 0.05, buff=0.08, stroke_width=3, color=CANCEL,
                    max_tip_length_to_length_ratio=0.25)
        self.say("pan_q")
        self.play(FadeIn(cx), GrowArrow(cxa), run_time=0.6)
        self.hold(after=0)
        self.predict()

        fail = T("giving back failed at once: JobCancellationException", 24, BAD).next_to(pc, DOWN, buff=0.35)
        fit(fail, 12.4)
        stays = T("the pan is still in our kitchen", 24, BAD).next_to(tk, DOWN, buff=0.2)
        self.say("pan_a")
        self.play(Indicate(pc[3], color=SUSP, scale_factor=1.05), run_time=0.7)
        self.at(1)
        self.play(Indicate(pc[4], color=BAD, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fail, shift=UP * 0.1), Wiggle(dph, scale_value=1.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(stays), Wiggle(jp, scale_value=1.08), run_time=0.9)
        self.hold()

        fixed = code_block(["    withContext(NonCancellable) { desk.giveBack(ticket) }"], 24,
                           {"withContext(NonCancellable)": SAFE, "desk.giveBack(ticket)": PAN})[0]
        fixed.move_to(pc[4], aligned_edge=LEFT)
        ok = T("gave back the pan on ticket-7, about 50 ms after the cancel", 24, SAFE).move_to(fail)
        fit(ok, 12.4)
        up = Arrow([5.6, -1.3, 0], [5.6, 0.7, 0], buff=0, stroke_width=4, color=CANCEL, max_tip_length_to_length_ratio=0.15)
        up_l = T("then the cancel\ncarries on up", 22, CANCEL).next_to(up, LEFT, buff=0.2)
        self.say("nc")
        self.play(FadeOut(pc[4]), FadeIn(fixed), FadeOut(fail), FadeOut(stays), FadeOut(cx), FadeOut(cxa), run_time=0.8)
        self.at(1)
        self.play(Indicate(fixed, color=SAFE, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(VGroup(jp, tk).animate.move_to([4.6, 0.95, 0]), run_time=1.2)
        self.play(FadeIn(ok, shift=UP * 0.1), run_time=0.5)
        self.at_text("and then the cancel", lead=0.3)
        self.play(GrowArrow(up), FadeIn(up_l), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(jp, tk, desk, dph, pc[:4], pc[5], fixed, ok, up, up_l)), run_time=0.6)

        # ================= the timer on the bread order =================
        tm = timer(TIMER, 1.1).move_to([-5.4, 2.4, 0])
        bph = phone(1.0).move_to([5.6, 2.4, 0])
        bph_l = T("the bakery", 24, GREY_A).next_to(bph, LEFT, buff=0.25)
        tline = T("withTimeout: when the timer runs out, it cancels the block", 30, TIMER).move_to([0, 0.9, 0])
        fit(tline, 12.4)
        self.say("timer")
        self.play(FadeIn(tm), run_time=0.5)
        self.at_text("she bakes", lead=0.3)
        self.play(FadeIn(bph), FadeIn(bph_l), run_time=0.5)
        self.at(1)
        self.play(FadeIn(tline, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Wiggle(tm, scale_value=1.2, rotation_angle=0.08 * TAU), run_time=0.9)
        self.hold()

        TX0, TPX = -0.9, 7.0 / 1600
        trows = (1.15, 0.05, -1.05)
        tnames = [T("delay stands in for the call", 22, GREY_A), T("blocking call in withContext(IO)", 22, GREY_A),
                  T("blocking call in runInterruptible", 22, GREY_A)]
        for t, y in zip(tnames, trows):
            t.move_to([-6.3, y, 0], aligned_edge=LEFT)
        tl = Line([TX0 + 300 * TPX, 1.65, 0], [TX0 + 300 * TPX, -1.55, 0], stroke_width=4, color=TIMER)
        tl_l = T("timer: 300 ms", 22, TIMER).next_to(tl, DOWN, buff=0.12)
        tax = VGroup(Line([TX0, -2.25, 0], [TX0 + 1600 * TPX, -2.25, 0], stroke_width=2, color=GREY_C),
                     *[VGroup(Line([TX0 + t * TPX, -2.3, 0], [TX0 + t * TPX, -2.2, 0], stroke_width=2, color=GREY_C),
                              T(f"{t:,} ms", 20, GREY_B).move_to([TX0 + t * TPX, -2.55, 0])) for t in (0, 500, 1000, 1500)])
        b1 = bar(TX0, TX0 + 307 * TPX, trows[0], COOK)
        b1_r = T("307 ms", 24, GREEN_M).next_to(b1, RIGHT, buff=0.25)
        want = DashedVMobject(Rectangle(width=1500 * TPX, height=0.4).set_stroke(GREY_D, 1.5)
                              .move_to([TX0 + 750 * TPX, trows[0], 0]), num_dashes=50)
        self.say("t1")
        self.play(FadeOut(tline), FadeIn(tax), FadeIn(tnames[0]), FadeIn(want), run_time=0.7)
        self.at_text("we wait", lead=0.3)
        self.play(Create(tl), FadeIn(tl_l), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(b1, LEFT), run_time=0.8)
        self.play(FadeIn(b1_r), run_time=0.4)
        self.hold()

        b2 = bar(TX0, TX0 + 1519 * TPX, trows[1], BAD)
        b2_r = T("1,519 ms", 24, BAD).next_to(b2, UP, buff=0.12).align_to(b2, RIGHT)
        ring2 = T("still on the line", 22, WHITE).move_to([TX0 + 900 * TPX, trows[1], 0])
        self.say("t2")
        self.play(FadeIn(tnames[1]), run_time=0.5)
        self.at(1)
        self.play(GrowFromEdge(b2, LEFT), run_time=2.2)
        self.play(FadeIn(b2_r), run_time=0.4)
        self.at(2)
        self.play(FadeIn(ring2), Wiggle(bph, scale_value=1.2), run_time=0.9)
        self.hold()

        b3 = bar(TX0, TX0 + 301 * TPX, trows[2], COOK)
        zap = VMobject(stroke_color=CANCEL, stroke_width=4).set_points_as_corners(
            [[0.1, 0.25, 0], [-0.08, 0.02, 0], [0.08, -0.02, 0], [-0.1, -0.25, 0]]).move_to(b3.get_right() + RIGHT * 0.25)
        b3_r = T("301 ms: interrupted, returned null", 22, GREEN_M).next_to(zap, RIGHT, buff=0.2)
        self.say("t3")
        self.play(FadeIn(tnames[2]), run_time=0.5)
        self.at_text("On a cancel", lead=0.3)
        self.play(GrowFromEdge(b3, LEFT), run_time=0.7)
        self.play(Create(zap), run_time=0.4)
        self.at_text("came back", lead=0.3)
        self.play(FadeIn(b3_r), run_time=0.5)
        self.hold()

        br = VGroup(T("A cook can hang up whenever she likes.", 26, GREY_A),
                    T("runInterruptible can only interrupt: Thread.sleep listens, some old network clients don't.", 24,
                      CANCEL)).arrange(DOWN, buff=0.15).move_to([0, -2.9, 0])
        fit(br, 12.4)
        self.say("breaks")
        self.play(FadeOut(tax), run_time=0.4)
        self.play(FadeIn(br[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(br[1]), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(tm, bph, bph_l, tl, tl_l, b1, b1_r, want, b2, b2_r, ring2, b3, zap, b3_r, br, *tnames)),
                  run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does cancel just stop a coroutine? No. It asks.", 32).move_to(UP * 2.4)
        m1 = T("It's heard at the next suspension point or check, and carried out as an exception.", 28, CANCEL).move_to(UP * 1.55)
        m2 = T("Suspending cleanup needs NonCancellable. A timeout is a cancel with a timer.", 28,
               t2c={"NonCancellable": SAFE, "a timer.": TIMER}).move_to(UP * 0.8)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a loop on Default weighs jars forever, with plain calls and no checks.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = VGroup(T("You call", 28), M("cancelAndJoin()", 26), T(". What happens?", 28)).arrange(RIGHT, buff=0.15)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("it never returns: nothing looks up. Add ensureActive().", 30, GREEN_M).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
