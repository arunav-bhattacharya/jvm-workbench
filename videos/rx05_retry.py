from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bonErrorReturn\b", "on error return"), (r"\bonErrorResume\b", "on error resume"), (r"\bonErrorMap\b", "on error map"),
    (r"\bretryWhen\b", "retry when"), (r"\bretry\(2\)", "retry two"), (r"\bRetryExhaustedException\b", "retry exhausted exception"),
    (r"\bRetry\.backoff\(3, 100 milliseconds\)", "Retry dot backoff, 3 and 100 milliseconds,"),
    (r"\bRetry\.backoff\(3, 50 milliseconds\)", "Retry dot backoff, 3 and 50 milliseconds,"),
    (r"\btimeout\(500 milliseconds\)", "timeout, 500 milliseconds,"), (r"\bTimeoutException\b", "timeout exception"),
    (r"\bMono\.defer\b", "Mono dot defer"), (r"\brye-1\b", "rye 1"), (r"3/3", "3 of 3"), (r"\bCONFIRMED\b", "confirmed"),
]

# every spoken line, in order
N = {
    "open": "Ten in the morning, halfway through a tray of rye, the bakery's oven breaks down. "
            "The packer has boxed a few loaves. Then nothing more comes down the belt, only a note: the oven has stopped.",
    "tray": "Let's shrink that. The program shares 8 loaves among some boxes, and the box counts come down the belt: "
            "1, 2, 0 and 4. Eight over 1 is 8. Eight over 2 is 4. Then eight over 0 throws.",
    "predict4": "What happens to the 4?",
    "terminal": "Nothing. The demo printed 8, then 4, then the error. The 4 is never divided. "
                "An error is the oven breaking down: a terminal signal, and after it, nothing else arrives.",
    "shy": "Now the question that's easy to be shy about. If we catch that error, surely the stream carries on, "
           "and the 4 gets its turn?",
    "box": "Well, the packer can't make a broken oven finish the tray. She can only decide what goes in the box instead. "
           "Reactor gives her three choices.",
    "choices": "One loaf from yesterday: onErrorReturn gives 8, 4, minus 1. The backup oven: onErrorResume switches "
               "to another belt, 8, 4, 100, 200. Or a clearer note: onErrorMap turns the error into a better one, "
               "and the stream still fails.",
    "replace": "Look for the 4. It isn't in any of them. Each operator caught the note on its way down, "
               "and replaced the rest of the stream. The oven above it had already stopped. "
               "Error operators replace what's left. They never resume it.",
    "mill": "So what about trying again? Every morning, the bakery orders flour from a mill, a service on another computer. "
            "Usually it says CONFIRMED. Sometimes it's busy, and a minute later the same order works. "
            "And sometimes it refuses: no rye flour this week. Asking again won't change that.",
    "retry": "For the busy mill, we want another try. retry doesn't rewind anything. "
             "When an error reaches it, it subscribes again: it signs a fresh order form, "
             "and the whole order is baked again, from the first loaf.",
    "retry_break": "Here the oven picture breaks. A repaired oven carries on where it stopped. "
                   "A retried Flux starts over, so rye-1 may be boxed twice. For one flour order, starting over is just what we want.",
    "r2_q": "Let's count. retry(2), on a mill that always fails. How many calls does the mill get?",
    "r2_a": "Three. Two retries means three attempts, all within a millisecond or two, and then the original error: mill down.",
    "r2_joke": "Three calls in one millisecond, to a mill that's already struggling. That's not a second try, that's a crowd. "
               "So we want pauses.",
    "backoff": "With its random part switched off, Retry.backoff(3, 100 milliseconds) waits before each retry, "
               "twice as long each time: 100, then 200, then 400. So the calls go out at 0, 100, 300 and 700 milliseconds.",
    "exhaust": "Four attempts, because 3 counts the retries. At 700 milliseconds it gives up with RetryExhaustedException, "
               "Retries exhausted: 3/3, and the mill's last error rides along as its cause.",
    "filter": "Add a filter, and only the busy error is retried. A refusal goes straight through. "
              "And keep the random jitter in production, so a thousand bakeries that failed together "
              "don't all call back in the same millisecond.",
    "eager_q": "Now a trap. Some clients call the mill the moment you call the method, "
               "and hand you a Mono holding the answer they already got. Retry that three times. How many calls reach the mill?",
    "eager_a": "One. The demo printed: mill busy, after 4 subscriptions. Each retry read the same stored answer.",
    "eager_joke": "It's asking the same note, four times, if the mill is still busy. The note isn't going to change its mind. "
                  "So make the call lazy: Mono.defer makes every subscription a fresh call.",
    "silence": "The hardest failure sends nothing at all. The mill takes the order and never answers. "
               "No item, no error. retry needs an error to react to, so nothing ever gives up.",
    "timer": "So we set a kitchen timer. timeout(500 milliseconds) turns silence into a TimeoutException, "
             "and cancels the slow call. In the demo, a 100 millisecond timer on a 300 millisecond call rang, "
             "and the slow call was cancelled.",
    "place": "Where you put the timer matters. Above retryWhen, each attempt gets its own 500 milliseconds, "
             "and a timeout is one more error to retry. Below it, it's one budget for the whole order.",
    "honest": "One last thing. A timer only means you stopped waiting. It doesn't mean the mill said no. "
              "A real kitchen timer lets you open the oven and look. timeout can't see the far side. "
              "So send the same order number every time, and when the retries run out, mark the order pending, not failed.",
    "code": "Here's the whole order in Java and Kotlin: a lazy call, a timer per attempt, a filtered backoff, and pending at the end.",
    "moral": "So, does catching an error carry the stream on? No. An error ends it, and error operators only choose "
             "what goes in the box instead. retry bakes the whole order again, so make the call lazy, pause, and filter. "
             "And a timer turns silence into an error.",
    "check": "Quick check. Retry.backoff(3, 50 milliseconds), no jitter, and a mill that's busy twice, then says CONFIRMED. "
             "When is the mill called, and what comes out?",
    "check_a": "At 0, 50 and 150 milliseconds, and then CONFIRMED. Once an attempt works, the retrying stops.",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.0, pos=(6.4, -3.25), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole reactive track
OVEN_C, PACK_C, SLIP_C, LOAF_C, BELL_C, BAD_C, CAKE_C = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
MILL_C = OVEN_C            # the mill is a source, like the oven
OK_C = GREEN_M


def person(color=PACK_C, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def oven(s=1.0, color=OVEN_C):
    body = RoundedRectangle(corner_radius=0.14, width=1.9, height=1.55).set_stroke(color, 3).set_fill(dim(color, 0.16), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.62).set_stroke(color, 2).set_fill(dim(LOAF_C, 0.5), 1)
    win.move_to(body.get_center() + DOWN * 0.22)
    knobs = VGroup(*[Circle(radius=0.07).set_stroke(color, 2).set_fill(dim(color, 0.5), 1) for _ in range(3)])
    knobs.arrange(RIGHT, buff=0.18).move_to(body.get_top() + DOWN * 0.27)
    return VGroup(body, win, knobs).scale(s)


def loaf(label="", s=1.0, color=LOAF_C):
    body = RoundedRectangle(corner_radius=0.2, width=1.05, height=0.46).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    if label:
        return VGroup(body, M(label, 20, color).move_to(body)).scale(s).set_z_index(4)
    cuts = VGroup(*[Line(LEFT * 0.07 + DOWN * 0.1, RIGHT * 0.07 + UP * 0.1, stroke_width=2.5, color=color)
                    .move_to(body.get_center() + RIGHT * dx) for dx in (-0.26, 0, 0.26)])
    return VGroup(body, cuts).scale(s).set_z_index(4)


def belt(x0, x1, y):
    """A conveyor belt: its top surface at y, rollers underneath."""
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=GREY_B)
    bot = Line([x0, y - 0.24, 0], [x1, y - 0.24, 0], stroke_width=2, color=GREY_D)
    n = int((x1 - x0) / 0.55)
    rollers = VGroup(*[Circle(radius=0.08, stroke_width=1.5, color=GREY_C).move_to([x0 + 0.25 + i * (x1 - x0 - 0.5) / max(1, n - 1), y - 0.12, 0])
                       for i in range(n)])
    return VGroup(top, bot, rollers)


def slip(text, size=22, color=SLIP_C, w=None):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.05, width=w or t.width + 0.36, height=0.5).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.22), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def crate(color=GREY_A):
    """An open box seen from the side."""
    return VGroup(Line([-0.5, 0.3, 0], [-0.5, -0.3, 0]), Line([-0.5, -0.3, 0], [0.5, -0.3, 0]),
                  Line([0.5, -0.3, 0], [0.5, 0.3, 0])).set_stroke(color, 3)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def paper(w, h, color=GREY_A):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.08), 1)
    return r


def scribble(p, w=1.0, color=SLIP_C):
    xs = np.linspace(0, w, 9)
    ys = [0.0, 0.12, -0.06, 0.15, -0.09, 0.1, -0.03, 0.08, 0.0]
    return VMobject().set_points_smoothly([p + np.array([x, y, 0]) for x, y in zip(xs, ys)]).set_stroke(color, 3)


def marble(text, color, r=0.28, size=22):
    c = Circle(radius=r).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    return VGroup(c, M(text, size, WHITE).move_to(c)).set_z_index(5)


def cross_at(p, s=0.26, color=BAD_C):
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(color, 5).scale(s).move_to(p).set_z_index(8)


def end_bar(x, y, color=BELL_C):
    return Line([x, y + 0.32, 0], [x, y - 0.32, 0], stroke_width=5, color=color).set_z_index(4)


def mill(s=1.0, color=MILL_C):
    """A windmill: a tower, a door, and four sails."""
    tower = Polygon([-0.5, -0.75, 0], [0.5, -0.75, 0], [0.32, 0.45, 0], [-0.32, 0.45, 0]).set_stroke(color, 3)
    tower.set_fill(dim(color, 0.18), 1)
    roof = Polygon([-0.42, 0.45, 0], [0.42, 0.45, 0], [0, 0.8, 0]).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    door = RoundedRectangle(corner_radius=0.08, width=0.26, height=0.38).set_stroke(color, 2).move_to([0, -0.56, 0])
    hub = Dot([0, 0.42, 0], radius=0.07, color=color)
    sails = VGroup(*[RoundedRectangle(corner_radius=0.03, width=0.18, height=0.85).set_stroke(GREY_A, 2).set_fill(GREY_E, 1)
                     .move_to([0, 0.42 + 0.48, 0]).rotate(a, about_point=np.array([0, 0.42, 0])) for a in (0.4, 0.4 + PI / 2, 0.4 + PI, 0.4 + 1.5 * PI)])
    return VGroup(sails, tower, roof, door, hub).scale(s)


def timer_icon(color=GREY_A, s=1.0):
    c = Circle(radius=0.3).set_stroke(color, 3).set_fill(BLACK, 1)
    h1 = Line(ORIGIN, UP * 0.2, stroke_width=3, color=color)
    h2 = Line(ORIGIN, RIGHT * 0.15, stroke_width=3, color=color)
    knob = Line(UP * 0.3, UP * 0.42, stroke_width=4, color=color)
    return VGroup(c, h1, h2, knob).scale(s)


def chip_n(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.62, t.width + 0.28), height=0.5).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


class Rx05Retry(Narrated):
    """rx-05, section 2 (with sections 0 and 3): the oven breaks down; 8 / i over 1, 2, 0, 4 ends at the error;
    onErrorReturn, onErrorResume, onErrorMap replace the rest; the mill's three moods; retry subscribes again (rye-1
    twice); retry(2) is three calls in a millisecond; Retry.backoff(3, 100 ms) at 0, 100, 300, 700 and
    RetryExhaustedException; filter and jitter; the eager client (4 subscriptions, 1 call) and Mono.defer; timeout as a
    kitchen timer, per attempt or in total; a timeout is not a no (same order number, PENDING); the code."""

    def construct(self):
        self.title_card("The oven breaks down", "errors, retries and timeouts")

        # ================= the oven breaks down =================
        BY = 0.6
        ov = oven().move_to([-5.2, BY + 0.6, 0])
        bl = belt(-4.1, 4.3, BY)
        pk = person(PACK_C, 1.3).move_to([5.6, BY + 0.5, 0])
        cr = crate().move_to([4.75, BY + 0.05, 0])
        lv = [loaf("rye", s=0.9).move_to([-3.4 + 1.25 * i, BY + 0.24, 0]) for i in range(3)]
        self.say("open")
        self.play(FadeIn(ov), Create(bl), FadeIn(pk), FadeIn(cr), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in lv], lag_ratio=0.2), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[l.animate.scale(0.8).move_to([4.75, BY + 0.1 + 0.08 * k, 0]) for k, l in enumerate(lv)],
                              lag_ratio=0.35), run_time=1.6)
        self.at(2)
        note = slip("the oven has stopped", 22, BAD_C).move_to([-3.2, BY + 0.3, 0])
        smoke = VGroup(*[Circle(radius=0.12 + 0.05 * k).set_stroke(GREY_B, 2).move_to(ov.get_top() + UP * (0.25 + 0.3 * k) + RIGHT * 0.15 * (-1) ** k)
                         for k in range(3)])
        self.play(ov[0].animate.set_stroke(BAD_C), ov[1].animate.set_fill(dim(BAD_C, 0.4)), FadeIn(smoke, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(note), run_time=0.3)
        self.play(note.animate.move_to([3.1, BY + 0.3, 0]), run_time=1.4)
        self.hold()
        self.play(FadeOut(VGroup(ov, bl, pk, cr, *lv, note, smoke)), run_time=0.6)

        # ================= 8 / i over 1, 2, 0, 4 =================
        XS = [-1.5, -0.1, 1.3, 2.7, 4.1]
        Y_SRC, Y_DIV = 2.1, 1.05
        ROWS = [-0.25, -1.25, -2.25]

        def lane(y, label, color=WHITE, mono=True):
            ln = Arrow([-2.2, y, 0], [4.4, y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.02)
            t = (M if mono else T)(label, 22 if mono else 24, color).move_to([-2.45, y, 0], aligned_edge=RIGHT)
            return VGroup(ln, t)

        l_src, l_div = lane(Y_SRC, "box counts", GREY_A, mono=False), lane(Y_DIV, "map(i -> 8 / i)")
        src = [marble(str(v), OVEN_C).move_to([XS[k], Y_SRC, 0]) for k, v in enumerate((1, 2, 0, 4))]
        div = [marble("8", LOAF_C).move_to([XS[0], Y_DIV, 0]), marble("4", LOAF_C).move_to([XS[1], Y_DIV, 0])]
        boom = cross_at([XS[2], Y_DIV, 0])
        boom_l = M("/ by zero", 20, BAD_C).next_to(boom, DOWN, buff=0.12)
        self.say("tray")
        self.play(FadeIn(l_src), FadeIn(l_div), run_time=0.6)
        self.at_text("1, 2, 0 and 4", lead=0.3)
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in src], lag_ratio=0.25), run_time=1.0)
        for k in range(2):
            self.at(2 + k)
            c = src[k].copy()
            self.add(c)
            self.play(c.animate.move_to(div[k]).set_opacity(0), FadeIn(div[k]), run_time=0.6)
            self.remove(c)
        self.at(4)
        c = src[2].copy()
        self.add(c)
        self.play(c.animate.move_to([XS[2], Y_DIV, 0]), run_time=0.5)
        self.remove(c)
        self.play(FadeIn(boom, scale=1.4), FadeIn(boom_l), run_time=0.5)
        self.hold()

        qm = T("?", 44).move_to([XS[3], Y_DIV, 0])
        self.say("predict4")
        self.play(FadeIn(qm), Circumscribe(src[3], color=WHITE, shape=Circle, buff=0.06), run_time=0.8)
        self.hold(after=0)
        self.predict()

        raw = VGroup(M("raw: 8", 22), M("raw: 4", 22), M("raw: error java.lang.ArithmeticException: / by zero", 22, BAD_C))
        raw.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([-6.2, -1.1, 0], aligned_edge=LEFT)
        never = T("never divided", 22, GREY_B).next_to(src[3], UP, buff=0.15)
        term = T("onError: a terminal signal, nothing after it", 26, BAD_C).move_to([0, -2.75, 0])
        self.say("terminal")
        self.play(FadeOut(qm), LaggedStart(*[FadeIn(r) for r in raw], lag_ratio=0.4), run_time=1.2)
        self.at(1)
        self.play(src[3].animate.set_opacity(0.3), FadeIn(never), run_time=0.6)
        self.at(2)
        self.play(FadeIn(term, shift=UP * 0.1), run_time=0.6)
        self.hold()

        shy = T("If we catch the error, does the 4 get its turn?", 32).move_to([0, -1.6, 0])
        self.say("shy")
        self.play(FadeOut(raw), FadeOut(term), run_time=0.4)
        self.at(1)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.7)
        self.hold()

        self.say("box")
        self.play(FadeOut(shy), run_time=0.4)
        self.at(1)
        rl = [lane(y, lab) for y, lab in zip(ROWS, ("onErrorReturn(-1)", "onErrorResume(...)", "onErrorMap(...)"))]
        self.play(LaggedStart(*[FadeIn(r) for r in rl], lag_ratio=0.25), run_time=1.0)
        self.hold()

        def head(y):
            return [marble("8", LOAF_C).move_to([XS[0], y, 0]), marble("4", LOAF_C).move_to([XS[1], y, 0])]

        r1 = head(ROWS[0]) + [marble("-1", GREY_A).move_to([XS[2], ROWS[0], 0])]
        r1_end = end_bar(XS[2] + 0.5, ROWS[0])
        r2 = head(ROWS[1]) + [marble("100", OVEN_C, size=18).move_to([XS[2], ROWS[1], 0]),
                              marble("200", OVEN_C, size=18).move_to([XS[3], ROWS[1], 0])]
        r2_end = end_bar(XS[3] + 0.5, ROWS[1])
        r3 = head(ROWS[2]) + [cross_at([XS[2], ROWS[2], 0])]
        r3_l = M("IllegalStateException: bad box count", 20, BAD_C).move_to([XS[2] - 0.3, ROWS[2] - 0.5, 0], aligned_edge=LEFT)
        ic1 = VGroup(loaf(s=0.55, color=GREY_A), T("yesterday's loaf", 20, GREY_A)).arrange(DOWN, buff=0.08).move_to([5.4, ROWS[0], 0])
        ic2 = VGroup(oven(0.3), T("backup oven", 20, OVEN_C)).arrange(DOWN, buff=0.08).move_to([5.4, ROWS[1], 0])
        ic3 = VGroup(slip("a clearer note", 20, BAD_C)).move_to([5.35, ROWS[2] + 0.1, 0])
        self.say("choices")
        self.play(LaggedStart(*[FadeIn(m) for m in r1], FadeIn(r1_end), lag_ratio=0.3), FadeIn(ic1), run_time=1.2)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(m) for m in r2], FadeIn(r2_end), lag_ratio=0.3), FadeIn(ic2), run_time=1.3)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(m) for m in r3], lag_ratio=0.3), FadeIn(ic3), run_time=1.0)
        self.play(FadeIn(r3_l), run_time=0.4)
        self.hold()

        col = DashedLine([XS[3], Y_SRC + 0.45, 0], [XS[3], ROWS[2] - 0.35, 0], dash_length=0.1).set_stroke(WHITE, 2)
        rule = T("Error operators replace what's left. They never resume it.", 28, SLIP_C).move_to([0, -3.2, 0])
        fit(rule, 12.4)
        self.say("replace")
        self.play(Create(col), Indicate(src[3], color=WHITE, scale_factor=1.2), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(*r1, *r2, *r3[:2]), color=WHITE, scale_factor=1.06), run_time=0.9)
        self.at(4)
        self.play(FadeIn(rule, shift=UP * 0.1), FadeOut(r3_l), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the mill and its three moods =================
        ml = mill(1.2).move_to([-5.4, 0.7, 0])
        ml_l = T("the mill", 26, MILL_C).next_to(ml, DOWN, buff=0.2)
        moods = [(chip_n("CONFIRMED", OK_C), T("usually", 24, GREY_B)),
                 (chip_n("MillBusyException", LOAF_C), T("busy: a minute later, it works", 24, GREY_B)),
                 (chip_n("OrderRefusedException", BAD_C), T("no rye this week: asking again won't help", 24, GREY_B))]
        mrows = VGroup(*[VGroup(c, t).arrange(RIGHT, buff=0.35) for c, t in moods]).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        mrows.move_to([-3.9, 0.7, 0], aligned_edge=LEFT)
        self.say("mill")
        self.play(FadeIn(ml), FadeIn(ml_l), run_time=0.8)
        for i in range(3):
            self.at(i + 2)
            self.play(FadeIn(mrows[i], shift=LEFT * 0.2), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(mrows[0], mrows[2])), mrows[1].animate.move_to([1.5, 2.8, 0]), ml.animate.scale(0.75).move_to([-5.3, 0.9, 0]),
                  FadeOut(ml_l), run_time=0.7)

        # ================= retry subscribes again =================
        CY = 0.9
        b_src = VGroup(M("mill.order(id)", 22, MILL_C)).move_to([-2.9, CY, 0])
        b_src_box = SurroundingRectangle(b_src, buff=0.22, corner_radius=0.1).set_stroke(MILL_C, 2.5)
        b_rt = VGroup(M("retry", 24, SLIP_C)).move_to([0.9, CY, 0])
        b_rt_box = SurroundingRectangle(b_rt, buff=0.22, corner_radius=0.1).set_stroke(SLIP_C, 2.5)
        sub = person(PACK_C, 1.0).move_to([4.3, CY, 0])
        a1 = Arrow(b_src_box.get_right(), b_rt_box.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        a2 = Arrow(b_rt_box.get_right(), sub.get_left() + LEFT * 0.1, buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        chain = VGroup(b_src, b_src_box, b_rt, b_rt_box, sub, a1, a2)
        err = Dot(radius=0.11, color=BAD_C).move_to(b_src_box.get_right()).set_z_index(8)
        form = VGroup(paper(1.0, 0.75), M("order", 18, GREY_A)).set_z_index(7)
        form[1].move_to(form[0].get_center() + UP * 0.12)
        form.move_to(b_rt_box.get_top() + UP * 0.7)
        self.say("retry")
        self.play(FadeIn(chain), run_time=0.8)
        self.at_text("When an error", lead=0.3)
        self.add(err)
        self.play(err.animate.move_to(b_rt_box.get_left()), run_time=0.6)
        self.play(FadeOut(err, scale=1.6), Indicate(b_rt, color=SLIP_C), run_time=0.5)
        self.at_text("signs a fresh", lead=0.4)
        self.play(FadeIn(form, shift=DOWN * 0.1), run_time=0.4)
        sg = scribble(form[0].get_left() + RIGHT * 0.15 + DOWN * 0.18, w=0.7).set_z_index(8)
        self.play(Create(sg), run_time=0.5)
        fs = VGroup(form, sg)
        self.play(fs.animate.scale(0.6).move_to(b_src_box.get_top() + UP * 0.55), run_time=0.8)
        self.play(Flash(b_src_box, color=SLIP_C, flash_radius=1.2), FadeOut(fs), run_time=0.6)
        self.hold()

        # the picture breaks: a retried Flux starts over
        RB = -1.7
        bl2 = belt(-4.6, 3.4, RB)
        cr2 = crate().move_to([4.2, RB + 0.05, 0])
        r1l = loaf("rye-1", s=0.85).move_to([-3.6, RB + 0.24, 0])
        r2l = loaf("rye-2", s=0.85).move_to([-4.7, RB + 0.24, 0])
        again = loaf("rye-1", s=0.85).move_to([-3.6, RB + 0.24, 0])
        twice = T("rye-1, boxed twice", 24, BAD_C).move_to([4.2, RB - 0.75, 0])
        self.say("retry_break")
        self.play(Create(bl2), FadeIn(cr2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r1l), FadeIn(r2l), run_time=0.4)
        self.play(r1l.animate.scale(0.8).move_to([4.2, RB + 0.12, 0]), r2l.animate.move_to([0.6, RB + 0.24, 0]), run_time=1.0)
        self.play(FadeOut(r2l, scale=0.5), Flash(r2l.get_center(), color=BAD_C), run_time=0.5)
        self.at(2)
        self.play(FadeIn(again, shift=RIGHT * 0.2), run_time=0.4)
        self.play(again.animate.scale(0.8).move_to([4.2, RB + 0.24, 0]), run_time=1.0)
        self.play(FadeIn(twice), run_time=0.4)
        self.at(3)
        self.play(Indicate(mrows[1], color=LOAF_C, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(bl2, cr2, r1l, again, twice, chain, mrows[1], ml)), run_time=0.6)

        # ================= count the attempts: retry(2) =================
        TX0, TK = -4.6, 10.2 / 700
        TX = lambda ms: TX0 + TK * ms
        TY = 1.3
        t_axis = VGroup()
        for ms in (0, 100, 300, 700):
            t_axis.add(DashedLine([TX(ms), TY + 0.3, 0], [TX(ms), TY - 0.3, 0], dash_length=0.06).set_stroke(GREY_D, 1.5))
            t_axis.add(M(str(ms), 20, GREY_B).move_to([TX(ms), TY - 0.55, 0]))
        t_axis.add(T("ms", 20, GREY_B).move_to([TX(700) + 0.55, TY - 0.55, 0]))
        t_ln = Arrow([TX(0) - 0.3, TY, 0], [TX(700) + 0.5, TY, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.02)
        t_lab = T("calls", 22, MILL_C).move_to([TX(0) - 0.45, TY, 0], aligned_edge=RIGHT)
        code2 = M("Mono.fromCallable(RetryDemo::alwaysFails).retry(2)", 22, SLIP_C).move_to([0, 3.1, 0])
        self.say("r2_q")
        self.play(FadeIn(code2), FadeIn(t_ln), FadeIn(t_lab), run_time=0.7)
        self.hold(after=0)
        self.predict()

        crowd = [marble(str(i + 1), BAD_C, r=0.24, size=20).move_to([TX(0) + 0.08 * i, TY + 0.0, 0]) for i in range(3)]
        out2 = VGroup(M("  [  5 ms] attempt 1", 22), M("  [  6 ms] attempt 2", 22), M("  [  6 ms] attempt 3", 22),
                      M("  -> java.lang.IllegalStateException: mill down", 22, BAD_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        out2.move_to([-6.2, -1.2, 0], aligned_edge=LEFT)
        self.say("r2_a")
        for i, m in enumerate(crowd):
            self.play(FadeIn(m, scale=0.6), FadeIn(out2[i]), run_time=0.35)
        self.play(VGroup(*crowd).animate.arrange(UP, buff=0.04).move_to([TX(0) + 0.05, TY + 0.0, 0]), run_time=0.5)
        self.at_text("and then", lead=0.3)
        self.play(FadeIn(out2[3]), run_time=0.5)
        self.hold()

        crowd_l = T("a crowd, not a second try", 24, BAD_C).next_to(VGroup(*crowd), RIGHT, buff=0.35).shift(UP * 0.45)
        self.say("r2_joke")
        self.play(FadeIn(crowd_l), Wiggle(VGroup(*crowd), scale_value=1.1), run_time=1.0)
        self.hold()

        # ================= backoff: 0, 100, 300, 700 =================
        code3 = M(".retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0))", 22, SLIP_C).move_to([0, 3.1, 0])
        atts = [marble(str(i + 1), BAD_C, r=0.24, size=20).move_to([TX(ms), TY, 0]) for i, ms in enumerate((0, 100, 300, 700))]
        self.say("backoff")
        self.play(FadeOut(VGroup(*crowd, crowd_l, out2)), FadeOut(code2), FadeIn(code3), FadeIn(t_axis), run_time=0.7)
        waits = VGroup()
        for i, (a, b) in enumerate(((0, 100), (100, 300), (300, 700))):
            br = BraceBetweenPoints([TX(a), TY + 0.35, 0], [TX(b), TY + 0.35, 0], direction=UP, color=GOLD_M)
            waits.add(VGroup(br, T(f"wait {b - a}", 20, GOLD_M).next_to(br, UP, buff=0.06)))
        self.at_text("twice as long", lead=0.3)
        self.play(FadeIn(atts[0]), run_time=0.3)
        for i in range(3):
            self.play(GrowFromCenter(waits[i][0]), FadeIn(waits[i][1]), run_time=0.45)
            self.play(FadeIn(atts[i + 1], scale=0.6), run_time=0.3)
        self.at(1)
        self.play(LaggedStart(*[Indicate(a, color=WHITE, scale_factor=1.25) for a in atts], lag_ratio=0.3), run_time=1.2)
        self.hold()

        ex = VGroup(M("RetryExhaustedException: Retries exhausted: 3/3", 22, BAD_C),
                    M("cause: java.lang.IllegalStateException: mill down", 22, GREY_A)).arrange(DOWN, aligned_edge=RIGHT, buff=0.12)
        ex.move_to([TX(700) + 0.3, TY - 1.15, 0], aligned_edge=RIGHT)
        four = T("3 retries = 4 attempts", 26, SLIP_C).move_to([-4.2, -0.35, 0])
        self.say("exhaust")
        self.play(FadeIn(four, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Flash(atts[3], color=BAD_C, flash_radius=0.5), FadeIn(ex[0], shift=UP * 0.1), run_time=0.7)
        self.at_text("and the mill", lead=0.3)
        self.play(FadeIn(ex[1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        f1 = VGroup(chip_n("MillBusyException", LOAF_C), T("retried", 24, LOAF_C)).arrange(RIGHT, buff=0.3)
        f2 = VGroup(chip_n("OrderRefusedException", BAD_C), T("straight through, never retried", 24, BAD_C)).arrange(RIGHT, buff=0.3)
        fl = VGroup(f1, f2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-6.2, -1.95, 0], aligned_edge=LEFT)
        filt = M(".filter(e -> e instanceof MillBusyException)", 22, SLIP_C).move_to([-6.2, -1.1, 0], aligned_edge=LEFT)
        jit = T("jitter: each wait moves at random, by up to half", 22, GREY_B).move_to([3.2, -3.05, 0])
        self.say("filter")
        self.play(FadeOut(four), FadeIn(filt), run_time=0.5)
        self.play(FadeIn(f1, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(f2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(jit), *[a.animate.shift(RIGHT * d) for a, d in zip(atts[1:], (0.35, -0.5, 0.7))], run_time=0.8)
        self.play(*[a.animate.shift(LEFT * d) for a, d in zip(atts[1:], (0.55, -0.2, 0.9))], run_time=0.7)
        self.play(*[a.animate.move_to([TX(ms), TY, 0]) for a, ms in zip(atts[1:], (100, 300, 700))], run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the eager client =================
        ec = code_block(["static Mono<String> eagerClient() {", "    return Mono.just(callMill());   // the call happens here, once", "}"], 22)
        ec.move_to([-6.2, 2.75, 0], aligned_edge=LEFT)
        ec[1].set_color(BAD_C)
        mono_box = RoundedRectangle(corner_radius=0.12, width=2.6, height=1.7).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1).move_to([-2.6, 0.2, 0])
        mono_l = M("Mono", 22, GREY_A).next_to(mono_box, UP, buff=0.1)
        st_note = slip("mill busy", 22, BAD_C).move_to(mono_box)
        ml2 = mill(0.8).move_to([-5.6, 0.2, 0])
        once = Arrow(ml2.get_right(), mono_box.get_left(), buff=0.15, stroke_width=3, color=MILL_C, max_tip_length_to_length_ratio=0.15)
        once_l = T("1 call", 22, MILL_C).next_to(once, DOWN, buff=0.1)
        rt3 = VGroup(M("retry(3)", 24, SLIP_C), person(PACK_C, 0.9)).arrange(RIGHT, buff=0.4).move_to([3.4, 0.2, 0])
        self.say("eager_q")
        self.play(FadeIn(ec), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ml2), GrowArrow(once), FadeIn(once_l), FadeIn(mono_box), FadeIn(mono_l), run_time=0.8)
        self.play(FadeIn(st_note, scale=0.8), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rt3), run_time=0.5)
        self.hold(after=0)
        self.predict()

        subs = T("subscriptions: 0", 24, SLIP_C)
        subs.move_to([0.6, -1.3, 0])
        out4 = VGroup(M("  [  0 ms] attempt 1", 22), M("  -> java.lang.IllegalStateException: mill busy after 4 subscriptions", 22, BAD_C))
        out4.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([-6.2, -2.35, 0], aligned_edge=LEFT)
        fit(out4, 12.6)
        out4.move_to([-6.2, -2.35, 0], aligned_edge=LEFT)
        self.say("eager_a")
        self.play(FadeIn(subs), run_time=0.3)
        for k in range(4):
            d = Dot(radius=0.1, color=SLIP_C).move_to(rt3[0].get_left() + LEFT * 0.1).set_z_index(9)
            self.add(d)
            new = T(f"subscriptions: {k + 1}", 24, SLIP_C).move_to(subs)
            self.play(d.animate.move_to(st_note.get_right()), run_time=0.4)
            self.remove(d)
            self.play(Indicate(st_note, color=BAD_C, scale_factor=1.12), FadeOut(subs), FadeIn(new), run_time=0.35)
            subs = new
        self.play(FadeIn(out4), run_time=0.5)
        self.hold()

        fixc = M("Mono.defer(() -> mill.order(orderId))", 24, OK_C).move_to([0, -3.15, 0])
        self.say("eager_joke")
        self.play(Wiggle(st_note, scale_value=1.1), run_time=0.9)
        self.at(2)
        self.play(FadeIn(fixc, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= silence, and the kitchen timer =================
        ml3 = mill(1.1).move_to([-4.8, 0.9, 0])
        ask = Arrow([-3.6, 1.0, 0], [-0.2, 1.0, 0], buff=0, stroke_width=3, color=SLIP_C, max_tip_length_to_length_ratio=0.1)
        ask_l = T("the order", 22, SLIP_C).next_to(ask, UP, buff=0.1)
        us = person(PACK_C, 1.1).move_to([0.5, 1.0, 0])
        dots = T("...", 40, GREY_B).move_to([-2.0, 0.2, 0])
        nothing = T("no item, no error", 26, GREY_B).move_to([-2.0, -0.4, 0])
        self.say("silence")
        self.play(FadeIn(ml3), FadeIn(us), run_time=0.6)
        self.play(GrowArrow(ask), FadeIn(ask_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(dots), run_time=0.5)
        self.play(Wiggle(dots, scale_value=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(nothing), run_time=0.5)
        self.hold()

        tmr = timer_icon(GREY_A, 1.6).move_to([3.2, 1.0, 0])
        tmr_l = M("timeout(500 ms)", 24, GREY_A).next_to(tmr, DOWN, buff=0.25)
        te = VGroup(M("  slow call cancelled", 22, GREY_A),
                    M("timeout: java.util.concurrent.TimeoutException:", 22, BAD_C),
                    M("  Did not observe any item or terminal signal within 100ms ...", 22, BAD_C))
        te.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([-6.2, -2.3, 0], aligned_edge=LEFT)
        fit(te, 12.6)
        te.move_to([-6.2, -2.3, 0], aligned_edge=LEFT)
        self.say("timer")
        self.play(FadeIn(tmr), FadeIn(tmr_l), run_time=0.7)
        self.at_text("turns silence", lead=0.3)
        self.play(Rotate(tmr[1], angle=-TAU, about_point=tmr[0].get_center()), run_time=1.2)
        self.play(Wiggle(tmr, scale_value=1.2, rotation_angle=0.12 * TAU), tmr[0].animate.set_stroke(BAD_C), run_time=0.8)
        self.play(FadeOut(dots), FadeOut(nothing), ask.animate.set_opacity(0.3), run_time=0.4)
        self.at(1)
        self.play(FadeIn(te), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(ml3, ask, ask_l, us, tmr, tmr_l, te)), run_time=0.6)

        # where the timer goes
        pl = code_block(["Mono.defer(() -> mill.order(orderId))",
                         "        .timeout(Duration.ofMillis(500))           // each attempt: 500 ms",
                         "        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))",
                         "                .filter(this::worthRetrying))",
                         "        .timeout(Duration.ofSeconds(2));           // the whole order: 2 s"], 22,
                        {"// each attempt: 500 ms": SLIP_C, "// the whole order: 2 s": GOLD_M})
        pl.move_to([-6.2, 1.0, 0], aligned_edge=LEFT)
        self.say("place")
        self.play(FadeIn(pl), run_time=0.8)
        self.at(1)
        self.play(Indicate(pl[1], color=SLIP_C, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(Indicate(pl[4], color=GOLD_M, scale_factor=1.03), run_time=0.9)
        self.hold()

        # a timeout is not a no
        wall = DashedLine([0.4, 2.3, 0], [0.4, -0.4, 0], dash_length=0.12).set_stroke(GREY_B, 2.5)
        us2 = VGroup(timer_icon(BAD_C, 1.3), T("we stopped waiting", 26, BAD_C)).arrange(DOWN, buff=0.15).move_to([-2.6, 1.0, 0])
        far = VGroup(mill(0.9), T("?", 48)).arrange(RIGHT, buff=0.25).move_to([3.0, 1.1, 0])
        far_l = T("did it say yes?", 26, GREY_B).next_to(far, DOWN, buff=0.15)
        same = VGroup(T("same order number every attempt:", 24), M("flour-3", 24, SLIP_C)).arrange(RIGHT, buff=0.2)
        pend = VGroup(T("out of retries:", 24), M('"PENDING:flour-3"', 24, SLIP_C), T("not failed", 24, GREY_B)).arrange(RIGHT, buff=0.2)
        hon = VGroup(same, pend).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.0, 0])
        self.say("honest")
        self.play(FadeOut(pl), run_time=0.6)
        self.play(FadeIn(us2), run_time=0.5)
        self.at(1)
        self.play(Create(wall), FadeIn(far), FadeIn(far_l), run_time=0.8)
        self.at(4)
        self.play(Indicate(wall, color=WHITE), run_time=0.8)
        self.at(5)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.5)
        self.at_text("mark the order", lead=0.4)
        self.play(FadeIn(pend, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        jsrc = ["Mono.defer(() -> mill.order(orderId))",
                "        .timeout(Duration.ofMillis(500))",
                "        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))",
                "                .filter(this::worthRetrying))",
                "        .onErrorResume(Exceptions::isRetryExhausted,",
                '                e -> Mono.just("PENDING:" + orderId));']
        ksrc = ["Mono.defer { mill.order(orderId) }",
                "    .timeout(Duration.ofMillis(500))",
                "    .retryWhen(Retry.backoff(3, Duration.ofMillis(100))",
                "        .filter(this::worthRetrying))",
                "    .onErrorResume(Exceptions::isRetryExhausted) {",
                '        Mono.just("PENDING:$orderId") }']
        hl = {"Mono.defer": OK_C, "timeout": SLIP_C, "Retry.backoff": SLIP_C, "PENDING": SLIP_C}
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        blk = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                     VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(blk, 12.8).move_to([0, 0.0, 0])
        self.say("code")
        self.play(FadeIn(blk, shift=UP * 0.15), run_time=0.9)
        self.at_text("a lazy call", lead=0.3)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=OK_C, scale_factor=1.02), run_time=0.7)
        self.at_text("a timer", lead=0.3)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=SLIP_C, scale_factor=1.02), run_time=0.7)
        self.at_text("a filtered", lead=0.3)
        self.play(Indicate(VGroup(jc[2:4], kc[2:4]), color=SLIP_C, scale_factor=1.02), run_time=0.7)
        self.at_text("and pending", lead=0.3)
        self.play(Indicate(VGroup(jc[4:6], kc[4:6]), color=SLIP_C, scale_factor=1.02), run_time=0.7)
        self.hold()
        self.play(FadeOut(blk), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does catching an error carry the stream on? No.", 32).move_to(UP * 2.55)
        m1 = T("An error ends it. Error operators choose what goes in the box instead.", 28, SLIP_C).move_to(UP * 1.8)
        m2 = T("retry bakes the whole order again: make it lazy, pause, filter.", 28, SLIP_C).move_to(UP * 1.15)
        m3 = T("A timer turns silence into an error.", 28, SLIP_C).move_to(UP * 0.5)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, SLIP_C), M("Retry.backoff(3, Duration.ofMillis(50)).jitter(0)", 24)).arrange(RIGHT, buff=0.25),
                    T("a mill that is busy twice, then says CONFIRMED. When is it called? What comes out?", 26)
                    ).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict()
        ans = T("at 0, 50 and 150 ms, then CONFIRMED: once an attempt works, retrying stops", 28, OK_C).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
