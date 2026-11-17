from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bwithTimeout\b", "with timeout"), (r"\bretryWhen\b", "retry when"),
    (r"\bonEach\b", "on each"), (r"\bIOException\b", "I O exception"),
    (r"\bJobCancellationException\b", "job cancellation exception"),
    (r"\bCancellationException\b", "cancellation exception"), (r"\bIllegalStateException\b", "illegal state exception"),
    (r"\bRetryExhaustedException\b", "retry exhausted exception"), (r"\bidempotent\b", "eye-dem-potent"),
]

# every spoken line, in order
N = {
    "open": "Bread for dinner comes from the bakery round the corner, ordered by phone. It's a lovely bakery with a "
            "terrible phone. Sometimes the call drops halfway, and sometimes nobody picks up at all.",
    "routine": "So the cook has a routine. No bread? Crackers instead. Or ring again, after a short pause, then a "
               "longer one. And meanwhile, plates can drop anywhere.",
    "code": "Here's the bread course as a flow, a recipe card for values. The cook sends out yesterday's loaf, "
            "then rings the bakery inside withTimeout of 50 milliseconds, which gives up if the call takes "
            "longer. Below her, catch sends out crackers if anything goes wrong. Today the bakery takes 100 "
            "milliseconds.",
    "shyq": "So here's a question that's easy to be shy about. A timeout is a cancellation, a "
            "CancellationException: a coroutine's way of saying, stop, you've been called off. And catch doesn't "
            "handle cancellation. So doesn't the timeout fly straight past?",
    "reveal": "It doesn't. The diner gets yesterday's loaf, then crackers, and the caller sees nothing. The catch "
              "heard the timeout.",
    "tidy": "So the rule we all learned, catch ignores cancellation, is a little too tidy. Let's end the bread "
            "course five ways.",
    "cases1": "The bakery call throws an IOException, Java's usual exception for a failed call, like a dropped line. "
              "Crackers. The bakery throws a CancellationException. Crackers again. The timeout fires. Crackers.",
    "cases2": "Now the diner drops a plate. The catch does nothing, and the caller sees an IllegalStateException: "
              "the diner dropped the plate.",
    "cases3": "And last, the caller's own job is cancelled while it waits. The catch does nothing again, and the "
              "caller sees a JobCancellationException.",
    "net": "Here's the picture. A net is strung under the cook's side of the line. Everything above catch is called "
           "the upstream: the cook and her bakery call. Everything below it is the downstream: the diner, the "
           "collector, and whoever called collect.",
    "net2": "Anything that falls from above lands in the net, even a cancellation, while the job is still "
            "running. A plate the diner drops falls below the net, to the caller. And when the caller calls off "
            "the whole dinner, the net steps aside, on purpose.",
    "how": "But an exception doesn't carry a label saying who threw it. So how does catch know? Let's build it by "
           "hand, in Kotlin.",
    "byhand": "First it wraps the downstream emit and remembers anything that comes out: the diner's dropped plate. "
              "Then, when the whole collect fails, it asks two questions. Did the diner throw this? Throw it on. Is "
              "it our own job's cancellation? Throw that on too. Everything else goes to your action.",
    "name": "Remember the inspector from lesson 2, who refuses any emit after the diner has thrown? That rule is "
            "called exception transparency: an exception from downstream belongs to downstream. So catch must "
            "never swallow it.",
    "cover": "The net is generous, but it only covers what hangs above it. Serving inside collect is below the net. "
             "To protect it, move the serving into onEach, above catch, and call collect with nothing inside.",
    "ends": "And a caught error still ends the upstream. map fails on 2, catch emits minus 1, and the diner gets 1, "
            "then minus 1. The 3 is never made.",
    "rule": "So here's the rule. catch hears only what falls from above it. Put the work it should cover above it.",
    "retry_intro": "The net can send out crackers. Sometimes you'd rather ring the bakery again. That's retry.",
    "retry_q": "The grocer's van brings a delivery note: flour, eggs and butter, read line by line. On the first try, "
               "the line drops after eggs, with an IOException. The pantry reads the note through retry of 3. "
               "What does the pantry receive?",
    "retry_a": "Flour, eggs, flour, eggs, butter. Two lines went in twice.",
    "retry_why": "A retry collects the upstream again, and a cold flow is a recipe card: collecting it again cooks it "
                 "again, from the top. So retry of 3 means up to four collections, and whatever went out goes out "
                 "again.",
    "pantry": "The flour doesn't mind. The pantry book does: it now says we bought twice the flour we did. So "
              "whatever comes after a retry must be idempotent: safe to see an item twice. Skip any line whose id "
              "you've already seen.",
    "prank": "Now the cook's pauses. Ringing a bakery that won't answer a thousand times a second isn't a routine. "
             "It's a prank call. So the waits grow.",
    "backoff": "That growing wait is a backoff. In code, it's a delay inside retryWhen, the operator under retry. It "
               "gets the cause, and an attempt number that starts at 0, so the waits are 100 milliseconds, then "
               "200, then 400.",
    "backoff2": "Against a bakery that never answers, she rings at 0, 100, 300 and 700 milliseconds. Then she gives "
                "up, and the original IOException comes out.",
    "reactor": "Reactor's backoff rings at the same times, but wraps the last error in a RetryExhaustedException, "
               "and outside tests adds jitter, a small random spread. In Flow, you write the policy yourself.",
    "timeout": "Position matters for the egg timer too. A timeout above the retry limits each try. Below it, a "
               "timeout limits them all, waits included.",
    "moral": "So, does a timeout fly past catch? No. catch doesn't sort exceptions by type. It asks who threw. "
             "What falls from the cook's side lands in the net, timeouts included; the diner's plate and the "
             "caller's own cancel go past. And a retry cooks the recipe again, from the top.",
    "check": "Quick check. catch sits above map, and map throws. Who handles it?",
    "check_a": "Not that catch. map is below the net, so its exception falls past it, to the caller.",
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

    def hold(self, after=0.12):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.0, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing (cook blue as in the coroutines track; failure red, cancellation yellow)
COOK, DINER, BREAD, NETC, BAD, CANCEL, CALLER, NOTE = BLUE_M, TEAL_M, GOLD_M, GREEN_M, RED_M, YELLOW_M, GREY_A, GREY_B


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def phone(s=1.0, color=GREY_A):
    hand = RoundedRectangle(corner_radius=0.1, width=0.85, height=0.22).set_stroke(color, 3).set_fill("#1a1a1a", 1)
    ear = RoundedRectangle(corner_radius=0.06, width=0.24, height=0.2).set_stroke(color, 3).set_fill("#1a1a1a", 1)
    ear.next_to(hand, DOWN, buff=-0.04).align_to(hand, LEFT)
    mouth = ear.copy().align_to(hand, RIGHT)
    return VGroup(hand, ear, mouth).scale(s)


def bakery(s=1.0):
    wall = Rectangle(width=2.2, height=1.4).set_stroke(BREAD, 3).set_fill(dim(BREAD, 0.12), 1)
    awning = VGroup(*[Polygon([x, 0, 0], [x + 0.44, 0, 0], [x + 0.44, -0.3, 0], [x, -0.3, 0])
                      .set_stroke(BREAD, 2).set_fill(dim(BREAD, 0.55) if k % 2 == 0 else "#151515", 1)
                      for k, x in enumerate(np.arange(-1.1, 1.0, 0.44))])
    awning.next_to(wall, UP, buff=0)
    door = Rectangle(width=0.45, height=0.8).set_stroke(BREAD, 2.5).move_to(wall.get_bottom() + UP * 0.4 + RIGHT * 0.55)
    win = Rectangle(width=0.9, height=0.55).set_stroke(BREAD, 2.5).move_to(wall.get_center() + LEFT * 0.45 + UP * 0.1)
    loaf = loaf_icon(0.7).move_to(win)
    return VGroup(wall, awning, door, win, loaf).scale(s)


def loaf_icon(s=1.0, color=BREAD):
    body = RoundedRectangle(corner_radius=0.2, width=0.9, height=0.45).set_stroke(color, 3).set_fill(dim(color, 0.45), 1)
    cuts = VGroup(*[Line([x - 0.06, -0.1, 0], [x + 0.06, 0.12, 0], stroke_width=2.5, color=color) for x in (-0.22, 0, 0.22)])
    return VGroup(body, cuts.move_to(body)).scale(s)


def crackers(s=1.0):
    sq = VGroup(*[RoundedRectangle(corner_radius=0.03, width=0.32, height=0.32).set_stroke(GREY_A, 2.2)
                  .set_fill("#2a2418", 1) for _ in range(2)]).arrange(RIGHT, buff=0.06)
    dots = VGroup(*[Dot(sq[k].get_center() + d, radius=0.025, color=GREY_A) for k in range(2)
                    for d in (UL * 0.07, DR * 0.07, UR * 0.07, DL * 0.07)])
    return VGroup(sq, dots).scale(s)


def plate(s=1.0, color=DINER):
    return VGroup(Ellipse(width=0.62, height=0.18).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1),
                  Ellipse(width=0.32, height=0.08).set_stroke(color, 1.5)).scale(s)


def net(x0=-6.3, x1=-3.7, y=1.25, sag=0.45):
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=NETC)
    xs = np.linspace(x0, x1, 9)
    bot_y = [y - sag * (1 - ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 2) - 0.08 for x in xs]
    bottom = VMobject().set_points_smoothly([[x, b, 0] for x, b in zip(xs, bot_y)]).set_stroke(NETC, 3)
    mesh = VGroup()
    for i in range(len(xs) - 1):
        mesh.add(Line([xs[i], y, 0], [xs[i + 1], bot_y[i + 1], 0], stroke_width=1.6, color=NETC))
        mesh.add(Line([xs[i + 1], y, 0], [xs[i], bot_y[i], 0], stroke_width=1.6, color=NETC))
    return VGroup(top, bottom, mesh)


def ball(color, s=1.0):
    return Circle(radius=0.17).set_stroke(color, 3).set_fill(dim(color, 0.6), 1).scale(s).set_z_index(8)


def code_block(src, size=22, hl=None, buff=0.15):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def node(label, color, w=2.4, size=24):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=0.75).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    return VGroup(r, T(label, size, color).move_to(r))


def note_paper(lines, w=1.9, color=GREY_A):
    t = VGroup(*[T(l, 24, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    r = RoundedRectangle(corner_radius=0.05, width=w, height=t.height + 0.55).set_stroke(color, 2.5).set_fill("#151515", 1)
    t.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.3)
    return VGroup(r, t)


def book(w=2.6, h=2.6, color=GREY_A):
    left = Rectangle(width=w / 2, height=h).set_stroke(color, 2.5).set_fill("#141414", 1)
    right = left.copy().next_to(left, RIGHT, buff=0)
    spine = Line(left.get_corner(UR), left.get_corner(DR), stroke_width=3, color=color)
    return VGroup(left, right, spine)


COOK_P = np.array([-5.0, 2.35, 0])
DINER_P = np.array([-5.0, -0.45, 0])
CALLER_P = np.array([-5.0, -2.6, 0])


class Flow06Upstream(Narrated):
    """flow-06, section 0 (and the retry of section 1), told with the bakery round the corner and its terrible phone.
    The shy question (doesn't a timeout fly past catch?); the bread course: yesterday's loaf, then crackers; five
    endings from the lesson's table; the net under the upstream, mapped; myCatch by hand and exception transparency;
    what the net covers ([1, -1], 3 never made); retry(3) replays the grocer's note from the top
    ([flour, eggs, flour, eggs, butter]); backoff rings at 0, 100, 300, 700; Reactor's differences; where a timeout
    goes; the moral and a check."""

    def construct(self):
        self.title_card("A net under the cook", "catch, retry and backoff in Kotlin Flow")

        # ================= the bakery and its terrible phone =================
        ck = person(COOK, 1.2).move_to([-4.3, 0.2, 0])
        ck_l = T("the cook", 24, COOK).next_to(ck, DOWN, buff=0.2)
        ph = phone(0.7).next_to(ck, RIGHT, buff=0.15).shift(UP * 0.25)
        bk = bakery(1.0).move_to([3.6, 0.35, 0])
        bk_l = T("the bakery round the corner", 24, BREAD).next_to(bk, DOWN, buff=0.25)
        wire = DashedLine(ph.get_right() + RIGHT * 0.1, bk.get_left() + LEFT * 0.15, dash_length=0.12).set_stroke(GREY_B, 2.5)
        self.say("open")
        self.play(FadeIn(ck), FadeIn(ck_l), run_time=0.6)
        self.play(FadeIn(bk), FadeIn(bk_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ph), Create(wire), run_time=0.8)
        self.at(2)
        brk = tick(False, 0.2).move_to(wire.get_center())
        self.play(Create(brk), wire.animate.set_stroke(BAD), run_time=0.6)
        self.at_text("nobody picks up", lead=0.3)
        rings = VGroup(*[Arc(radius=r, start_angle=-0.7, angle=1.4).set_stroke(GREY_B, 2.5).move_arc_center_to(bk.get_left() + LEFT * 0.05)
                         .rotate(PI, about_point=bk.get_left() + LEFT * 0.05) for r in (0.25, 0.45, 0.65)])
        self.play(LaggedStart(*[Create(r) for r in rings], lag_ratio=0.3), run_time=0.9)
        self.play(FadeOut(rings), run_time=0.4)
        self.hold()

        steps = VGroup(
            VGroup(crackers(0.8), T("no bread? crackers instead", 24)),
            VGroup(phone(0.45), T("ring again: a short pause, then a longer one", 24)),
            VGroup(plate(0.8, BAD), T("plates drop: in the kitchen, or at the table", 24)))
        for r in steps:
            r.arrange(RIGHT, buff=0.3)
        steps.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -2.4, 0])
        self.say("routine")
        self.play(FadeOut(VGroup(ck_l, bk_l)), VGroup(ck, ph).animate.shift(UP * 0.6), bk.animate.shift(UP * 0.6),
                  wire.animate.shift(UP * 0.6), brk.animate.shift(UP * 0.6), run_time=0.6)
        self.at_text("No bread", lead=0.3)
        self.play(FadeIn(steps[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("Or ring", lead=0.3)
        self.play(FadeIn(steps[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("And meanwhile", lead=0.3)
        self.play(FadeIn(steps[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(ck, ph, bk, wire, brk, steps)), run_time=0.6)

        # ================= the bread course: the chain, with the code beside it =================
        cook = person(COOK, 1.0).move_to(COOK_P)
        cph = phone(0.42).next_to(cook, LEFT, buff=0.12).shift(UP * 0.1)
        up_l = T("upstream", 22, NOTE).move_to(COOK_P + UP * 0.85)
        nt = net()
        dn_l = T("downstream", 22, NOTE).move_to([-5.0, 0.42, 0])
        diner = person(DINER, 1.0).move_to(DINER_P)
        table = VGroup(Rectangle(width=1.6, height=0.12).set_stroke(DINER, 2.5).set_fill(dim(DINER, 0.3), 1)
                       .move_to(DINER_P + DOWN * 0.47),
                       Line(DINER_P + DOWN * 0.53 + LEFT * 0.6, DINER_P + DOWN * 0.95 + LEFT * 0.6, stroke_width=3, color=DINER),
                       Line(DINER_P + DOWN * 0.53 + RIGHT * 0.6, DINER_P + DOWN * 0.95 + RIGHT * 0.6, stroke_width=3, color=DINER))
        caller = node("the caller", CALLER, w=2.3).move_to(CALLER_P)
        hl = {"emit(oldLoaf)": BREAD, "withTimeout(50)": CANCEL, "bakery.fresh()": BREAD, ".catch": NETC,
              "emit(crackers)": NETC, ".collect": DINER, "diner.eat(it)": DINER, "// 100 ms": GREY_B}
        X0 = -3.1
        c_flow = code_block(["flow {", "    emit(oldLoaf)", "    emit(withTimeout(50) { bakery.fresh() })  // 100 ms", "}"],
                            22, hl, buff=0.12).move_to([X0, 2.35, 0], aligned_edge=LEFT)
        c_catch = code_block(["    .catch { e -> emit(crackers) }"], 22, hl).move_to([X0, 1.05, 0], aligned_edge=LEFT)
        c_coll = code_block(["    .collect { diner.eat(it) }"], 22, hl).move_to([X0, -0.45, 0], aligned_edge=LEFT)
        self.say("code")
        self.play(FadeIn(cook), FadeIn(c_flow[0]), FadeIn(c_flow[3]), run_time=0.6)
        self.at_text("The cook sends", lead=0.3)
        self.play(FadeIn(c_flow[1]), run_time=0.5)
        self.at_text("then rings", lead=0.3)
        self.play(FadeIn(c_flow[2]), FadeIn(cph), run_time=0.6)
        self.at_text("Below her", lead=0.3)
        self.play(Create(nt), FadeIn(c_catch), run_time=0.8)
        self.play(FadeIn(diner), FadeIn(table), FadeIn(c_coll), FadeIn(caller), run_time=0.7)
        self.at_text("Today the bakery", lead=0.3)
        self.play(Indicate(c_flow[2][-6:], color=GREY_A), run_time=0.8)
        self.hold()

        q = T("A timeout is a cancellation. Doesn't it fly straight past catch?", 28).move_to([1.6, -2.15, 0])
        fit(q, 9.0)
        self.say("shyq")
        self.at_text("A timeout is", lead=0.3)
        self.play(Indicate(c_flow[2][5:20], color=CANCEL), run_time=0.8)
        self.at_text("And catch", lead=0.3)
        self.play(Indicate(c_catch, color=NETC, scale_factor=1.04), run_time=0.8)
        self.at_text("So doesn't", lead=0.3)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.1), edge=RIGHT)

        # the reveal: old loaf, then crackers; the timeout lands in the net
        served = VGroup(loaf_icon(0.5), crackers(0.6)).arrange(RIGHT, buff=0.25).next_to(diner, RIGHT, buff=0.25)
        served.shift(UP * 0.05)
        tb = ball(CANCEL).move_to(COOK_P + DOWN * 0.5)
        self.say("reveal")
        self.play(FadeOut(q), FadeIn(served[0], shift=DOWN * 0.3), run_time=0.6)
        self.play(FadeIn(tb, scale=0.5), run_time=0.3)
        self.play(tb.animate.move_to([-5.0, 0.95, 0]), run_time=0.7, rate_func=rate_functions.ease_in_quad)
        self.play(Indicate(nt, color=NETC, scale_factor=1.04), FadeIn(served[1], shift=DOWN * 0.3), run_time=0.7)
        self.at(2)
        self.play(Indicate(c_catch, color=NETC, scale_factor=1.04), run_time=0.8)
        self.hold()

        self.say("tidy")
        tidy = T("\"catch ignores cancellation\"", 28, GREY_B).move_to([1.6, -2.15, 0])
        strike = Line(tidy.get_left(), tidy.get_right(), stroke_width=3, color=BAD).set_z_index(3)
        self.play(FadeIn(tidy), run_time=0.5)
        self.play(Create(strike), run_time=0.6)
        self.hold()
        self.play(FadeOut(tidy), FadeOut(strike), FadeOut(served), FadeOut(tb), run_time=0.4)

        # ================= five endings =================
        LX, LY = -2.55, -1.3

        def row(k, ok, text):
            r = VGroup(tick(ok, 0.17), T(text, 22, WHITE if ok else BAD)).arrange(RIGHT, buff=0.25)
            return r.move_to([LX, LY - 0.42 * k, 0], aligned_edge=LEFT)

        rows = [row(0, True, "the bakery throws IOException: crackers"),
                row(1, True, "the bakery throws CancellationException: crackers"),
                row(2, True, "withTimeout fires: crackers"),
                row(3, False, "the diner drops a plate: the caller sees IllegalStateException"),
                row(4, False, "the caller's job is cancelled: the caller sees JobCancellationException")]
        for r in rows:
            fit(r, 8.95)

        def drop_into_net(color):
            b = ball(color).move_to(COOK_P + DOWN * 0.5)
            return b

        self.say("cases1")
        b1 = drop_into_net(BAD)
        self.play(FadeIn(b1, scale=0.5), run_time=0.3)
        self.play(b1.animate.move_to([-5.3, 0.95, 0]), run_time=0.6, rate_func=rate_functions.ease_in_quad)
        self.play(FadeIn(rows[0]), Indicate(nt[0], color=NETC), run_time=0.5)
        self.at_text("The bakery throws a", lead=0.3)
        b2 = drop_into_net(CANCEL)
        self.play(FadeIn(b2, scale=0.5), run_time=0.3)
        self.play(b2.animate.move_to([-4.95, 0.9, 0]), run_time=0.6, rate_func=rate_functions.ease_in_quad)
        self.play(FadeIn(rows[1]), run_time=0.4)
        self.at_text("The timeout fires", lead=0.3)
        b3 = drop_into_net(CANCEL)
        clock = Circle(radius=0.07).set_stroke(BLACK, 2).move_to(b3)
        b3.add(clock)
        self.play(FadeIn(b3, scale=0.5), run_time=0.3)
        self.play(b3.animate.move_to([-4.6, 0.95, 0]), run_time=0.6, rate_func=rate_functions.ease_in_quad)
        self.play(FadeIn(rows[2]), run_time=0.4)
        self.hold()

        pl = plate(0.8, BAD).move_to(DINER_P + RIGHT * 0.55 + DOWN * 0.25)
        self.say("cases2")
        self.play(FadeIn(pl), run_time=0.3)
        self.play(pl.animate.move_to(CALLER_P + UP * 0.55 + RIGHT * 0.55), run_time=0.8, rate_func=rate_functions.ease_in_quad)
        self.play(caller[0].animate.set_stroke(BAD), FadeIn(rows[3]), run_time=0.6)
        self.hold()

        jb = ball(CANCEL).move_to(COOK_P + DOWN * 0.5)
        self.say("cases3")
        self.play(FadeOut(pl), caller[0].animate.set_stroke(CALLER), run_time=0.4)
        self.play(FadeIn(jb, scale=0.5), run_time=0.3)
        self.play(nt.animate.set_stroke(opacity=0.25), run_time=0.3)
        self.play(jb.animate.move_to(CALLER_P + UP * 0.55 + LEFT * 0.6), run_time=1.0, rate_func=rate_functions.ease_in_quad)
        self.play(nt.animate.set_stroke(opacity=1), caller[0].animate.set_stroke(CANCEL), FadeIn(rows[4]), run_time=0.6)
        self.hold()

        # ================= the net, mapped =================
        up_box = SurroundingRectangle(VGroup(cook, cph, c_flow), buff=0.15, color=COOK, corner_radius=0.12).set_stroke(width=2)
        dn_box = SurroundingRectangle(VGroup(diner, table, c_coll, caller), buff=0.15, color=DINER, corner_radius=0.12).set_stroke(width=2)
        self.say("net")
        self.play(Indicate(nt, color=NETC, scale_factor=1.03), run_time=0.8)
        self.at_text("Everything above", lead=0.3)
        self.play(FadeOut(VGroup(*rows)), Create(up_box), FadeIn(up_l), run_time=0.7)
        self.at_text("Everything below", lead=0.3)
        self.play(Create(dn_box), FadeIn(dn_l), caller[0].animate.set_stroke(CALLER), FadeOut(jb), run_time=0.7)
        self.hold()
        self.say("net2")
        self.play(FadeOut(up_box), FadeOut(dn_box), run_time=0.4)
        self.play(Indicate(VGroup(b1, b2, b3), color=WHITE, scale_factor=1.2), run_time=0.8)
        self.at(1)
        pl2 = plate(0.8, BAD).move_to(DINER_P + RIGHT * 0.55 + DOWN * 0.25)
        self.play(FadeIn(pl2), run_time=0.3)
        self.play(pl2.animate.move_to(CALLER_P + UP * 0.55 + RIGHT * 0.55), run_time=0.7)
        self.at(2)
        jb2 = ball(CANCEL).move_to(COOK_P + DOWN * 0.5)
        self.play(FadeIn(jb2, scale=0.5), nt.animate.set_stroke(opacity=0.25), run_time=0.4)
        self.play(jb2.animate.move_to(CALLER_P + UP * 0.55 + LEFT * 0.6), run_time=0.9)
        self.play(nt.animate.set_stroke(opacity=1), run_time=0.3)
        self.hold()
        chain = VGroup(cook, cph, up_l, nt, dn_l, diner, table, caller, c_flow, c_catch, c_coll, b1, b2, b3, pl2, jb2)

        # ================= catch, built by hand =================
        q2 = T("An exception carries no label saying who threw it.", 28, GREY_A).move_to([1.6, -2.1, 0])
        fit(q2, 9.0)
        self.say("how")
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(chain), FadeOut(q2), run_time=0.6)

        m_hl = {"fromDownstream": BAD, "emit(v)": DINER, "action(e)": NETC, "ours": CANCEL,
                "// 1. the diner threw": GREY_B, "// 2. our own job": GREY_B, "// 3. from above": GREY_B}
        msrc = ["fun <T> Flow<T>.myCatch(",
                "    action: suspend FlowCollector<T>.(Throwable) -> Unit",
                "): Flow<T> = flow {",
                "    var fromDownstream: Throwable? = null",
                "    try {",
                "        collect { v ->",
                "            try { emit(v) }",
                "            catch (e: Throwable) { fromDownstream = e; throw e }",
                "        }",
                "    } catch (e: Throwable) {",
                "        if (e === fromDownstream) throw e                // 1. the diner threw",
                "        val ours = !currentCoroutineContext().isActive",
                "        if (e is CancellationException && ours) throw e  // 2. our own job",
                "        action(e)                                        // 3. from above",
                "    }",
                "}"]
        mc = code_block(msrc, 22, m_hl, buff=0.11)
        fit(mc, 12.6).move_to([0, -0.15, 0])
        m_t = T("catch, built by hand (Kotlin)", 26, GREY_B).next_to(mc, UP, buff=0.25).align_to(mc, LEFT)
        box1 = SurroundingRectangle(VGroup(mc[6], mc[7]), buff=0.06, color=BAD, corner_radius=0.05)
        box2 = SurroundingRectangle(mc[10], buff=0.05, color=BAD, corner_radius=0.05)
        box3 = SurroundingRectangle(VGroup(mc[11], mc[12]), buff=0.05, color=CANCEL, corner_radius=0.05)
        box4 = SurroundingRectangle(mc[13], buff=0.05, color=NETC, corner_radius=0.05)
        self.say("byhand")
        self.play(FadeIn(m_t), FadeIn(mc), run_time=0.8)
        self.play(Create(box1), run_time=0.6)
        self.at_text("Then, when", lead=0.3)
        self.play(Indicate(mc[9], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at_text("Did the diner", lead=0.3)
        self.play(Create(box2), run_time=0.6)
        self.at_text("Is it our own", lead=0.3)
        self.play(Create(box3), run_time=0.6)
        self.at_text("Everything else", lead=0.3)
        self.play(Create(box4), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(mc, m_t, box1, box2, box3, box4)), run_time=0.5)

        nm = VGroup(T("exception transparency", 36, NETC),
                    T("an exception from downstream belongs to downstream", 28, GREY_A)).arrange(DOWN, buff=0.3)
        nm.move_to([0, 0.9, 0])
        insp = VGroup(person(GREY_A, 1.0), T("the inspector from lesson 2:", 24, GREY_B),
                      T("no emit after the diner has thrown", 24, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -1.4, 0])
        fit(insp, 12.4)
        self.say("name")
        self.play(FadeIn(insp, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(nm[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("an exception from", lead=0.3)
        self.play(FadeIn(nm[1]), run_time=0.6)
        self.hold()
        self.play(FadeOut(nm), FadeOut(insp), run_time=0.5)

        # ================= what the net covers =================
        c_hl = {".catch": NETC, "emit(crackers)": NETC, ".onEach": DINER, "serve(it)": DINER, ".collect": DINER,
                "// below": BAD, "// above": GREEN_M}
        left = code_block(["bread", "    .catch { emit(crackers) }", "    .collect { serve(it) }  // below"], 22, c_hl)
        right = code_block(["bread", "    .onEach { serve(it) }  // above", "    .catch { emit(crackers) }",
                            "    .collect()"], 22, c_hl)
        cols = VGroup(VGroup(T("not covered", 24, BAD), left).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("covered", 24, GREEN_M), right).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(RIGHT, buff=0.8,
                                                                                                                  aligned_edge=UP)
        fit(cols, 12.6).move_to([0, 1.7, 0])
        self.say("cover")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(left[2], color=BAD, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.7)
        self.hold()

        e_hl = {"check(it != 2)": BAD, ".catch": NETC, "emit(-1)": NETC}
        ends = M("flowOf(1, 2, 3).map { check(it != 2); it }.catch { emit(-1) }", 24, t2c=e_hl).move_to([0, -0.6, 0])
        fit(ends, 12.4)
        out = VGroup(T("the diner gets", 26, GREY_A), M("1, -1", 28, DINER), T("and 3 is never made", 26, BAD)).arrange(RIGHT, buff=0.3)
        out.move_to([0, -1.45, 0])
        self.say("ends")
        self.play(FadeIn(ends, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(out[0]), FadeIn(out[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out[2]), run_time=0.5)
        self.hold()
        rule = T("catch hears only what falls from above it. Put the work it should cover above it.", 28, NETC)
        fit(rule, 12.4).move_to([0, -2.7, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(cols, ends, out, rule)), run_time=0.5)

        # ================= ring again: retry replays the recipe from the top =================
        intro_ph = phone(0.9).move_to([0, 0.5, 0])
        self.say("retry_intro")
        self.play(FadeIn(intro_ph), run_time=0.5)
        self.at(2)
        self.play(Wiggle(intro_ph, scale_value=1.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(intro_ph), run_time=0.4)

        nte = note_paper(["flour", "eggs", "butter"]).move_to([-4.6, 0.9, 0])
        nte_l = T("the grocer's note", 24, GREY_A).next_to(nte, UP, buff=0.2)
        bk2 = book(2.8, 2.5).move_to([3.9, 0.7, 0])
        bk2_l = T("the pantry book", 24, GREY_A).next_to(bk2, UP, buff=0.2)
        arr = Arrow(nte.get_right() + RIGHT * 0.2, bk2.get_left() + LEFT * 0.2, buff=0.1, stroke_width=4, color=GREY_B,
                    max_tip_length_to_length_ratio=0.08)
        r_hl = {"retry(3)": NETC}
        rk = M("val received = note.retry(3).toList()", 24, t2c=r_hl)
        rj = M("Flux.defer(grocer::note).retry(3).collectList().block()", 24, t2c=r_hl)
        rcode = VGroup(VGroup(T("Kotlin", 22, GREY_B), rk).arrange(RIGHT, buff=0.3),
                       VGroup(T("Java", 22, GREY_B), rj).arrange(RIGHT, buff=0.3)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(rcode, 12.4).move_to([0, -2.55, 0])
        self.say("retry_q")
        self.play(FadeIn(nte), FadeIn(nte_l), run_time=0.6)
        self.at(1)
        drop = tick(False, 0.2).next_to(nte[1][1], RIGHT, buff=0.35)
        self.play(Create(drop), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bk2), FadeIn(bk2_l), GrowArrow(arr), FadeIn(rcode), run_time=0.8)
        self.hold(after=0)
        self.predict()

        entries = ["flour", "eggs", "flour", "eggs", "butter"]
        ents = VGroup(*[T(e, 24, BAD if k in (2, 3) else GREY_A) for k, e in enumerate(entries)])
        ents.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(bk2[1].get_center()).align_to(bk2[1], LEFT).shift(RIGHT * 0.25)
        try1 = T("try 1", 22, NOTE).move_to([bk2[0].get_center()[0], ents[0].get_center()[1], 0])
        try2 = T("try 2", 22, NETC).move_to([bk2[0].get_center()[0], ents[2].get_center()[1], 0])
        self.say("retry_a")
        self.play(FadeIn(try1), FadeIn(ents[0]), FadeIn(ents[1]), run_time=0.7)
        self.play(FadeIn(try2), FadeIn(ents[2]), FadeIn(ents[3]), FadeIn(ents[4]), run_time=0.8)
        self.at(1)
        self.play(Indicate(VGroup(ents[2], ents[3]), color=BAD), run_time=0.8)
        self.hold()
        self.say("retry_why")
        self.play(Indicate(nte, color=GREY_A, scale_factor=1.05), run_time=0.8)
        self.at(1)
        cnt = T("retry(3): up to 4 collections", 24, NETC).next_to(arr, DOWN, buff=0.2)
        self.play(FadeIn(cnt), run_time=0.5)
        self.hold()
        idem = T("idempotent: seeing an item twice leaves the same result as once", 24, GREEN_M).next_to(arr, DOWN, buff=0.2)
        idem.move_to([0, -1.25, 0])
        self.say("pantry")
        self.play(Wiggle(ents[2], scale_value=1.15), run_time=0.9)
        self.at(2)
        self.play(FadeOut(cnt), FadeIn(idem), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(nte, nte_l, drop, bk2, bk2_l, arr, rcode, ents, try1, try2, idem)), run_time=0.5)

        # ================= backoff =================
        TX0, TK = -4.6, 9.6 / 800

        def tx(ms):
            return TX0 + TK * ms

        TY = -0.9
        rings_t = [0, 100, 300, 700]
        tax = VGroup(Line([tx(0), TY, 0], [tx(800), TY, 0], stroke_width=1.5, color=GREY_C))
        for ms in range(0, 801, 100):
            tax.add(Line([tx(ms), TY - 0.07, 0], [tx(ms), TY + 0.07, 0], stroke_width=1.5, color=GREY_C))
            tax.add(T(f"{ms} ms" if ms == 0 else str(ms), 20, NOTE).move_to([tx(ms), TY - 0.32, 0]))
        p_icons = VGroup(*[phone(0.4).move_to([tx(ms), TY + 0.55, 0]) for ms in rings_t])
        waits = VGroup()
        for a, b in ((0, 100), (100, 300), (300, 700)):
            bar = Rectangle(width=TK * (b - a) - 0.5, height=0.16).set_stroke(width=0).set_fill(NETC, 0.6)
            bar.move_to([(tx(a) + tx(b)) / 2, TY + 0.55, 0])
            waits.add(VGroup(bar, T(f"wait {b - a}", 20, NETC).next_to(bar, UP, buff=0.12)))
        gone = VGroup(tick(False, 0.18), M("IOException", 22, BAD)).arrange(RIGHT, buff=0.15).move_to([tx(700) + 1.3, TY + 1.3, 0])
        b_hl = {"retryWhen": NETC, "delay(100L shl attempt.toInt())": NETC, "// 100, 200, 400 ms": GREY_B}
        bsrc = ['bakery.order("sourdough").retryWhen { cause, attempt ->',
                "    val retry = cause is IOException && attempt < 3",
                "    if (retry) delay(100L shl attempt.toInt())   // 100, 200, 400 ms",
                "    retry",
                "}"]
        bk_c = code_block(bsrc, 22, b_hl).move_to([0, 2.35, 0])
        self.say("prank")
        many = VGroup(*[phone(0.55).move_to([-4.8 + 1.2 * (k % 9), 1.2 - 1.0 * (k // 9), 0]).rotate(0.35 * ((k % 3) - 1))
                        for k in range(27)])
        self.play(LaggedStart(*[FadeIn(p, scale=0.6) for p in many], lag_ratio=0.08), run_time=1.3)
        self.at(2)
        self.play(FadeOut(many), run_time=0.5)
        self.hold()
        self.say("backoff")
        self.play(FadeIn(bk_c, shift=UP * 0.1), run_time=0.8)
        self.at_text("It gets the cause", lead=0.3)
        self.play(Indicate(bk_c[0][-16:], color=NETC), run_time=0.8)
        self.at_text("so the waits", lead=0.3)
        self.play(Indicate(bk_c[2], color=NETC, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.say("backoff2")
        self.play(FadeIn(tax), FadeIn(p_icons[0]), run_time=0.6)
        for k in range(3):
            self.play(GrowFromEdge(waits[k][0], LEFT), FadeIn(waits[k][1]), run_time=0.4 + 0.15 * k)
            self.play(FadeIn(p_icons[k + 1], scale=0.6), run_time=0.3)
        self.at(1)
        self.play(FadeIn(gone, shift=RIGHT * 0.2), run_time=0.6)
        self.hold()

        rx = VGroup(T("Java, with Reactor:", 22, GREY_B),
                    M("retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0))", 22, t2c={"Retry.backoff": NETC}))
        rx.arrange(RIGHT, buff=0.25)
        fit(rx, 12.6).move_to([0, -2.35, 0])
        rx2 = VGroup(T("same times; then", 22, GREY_A), M("RetryExhaustedException", 22, BAD),
                     T("and jitter, outside tests", 22, GREY_A)).arrange(RIGHT, buff=0.2)
        fit(rx2, 12.6).move_to([0, -2.95, 0])
        self.say("reactor")
        self.play(FadeIn(rx), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rx2), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(tax, p_icons, waits, gone, bk_c, rx, rx2)), run_time=0.5)

        t_hl = {".timeout(300.milliseconds)": CANCEL, ".timeout(1.seconds)": CANCEL, ".retryWithBackoff()": NETC}
        ta = code_block(["bakery.order(kind)", "    .timeout(300.milliseconds)", "    .retryWithBackoff()"], 24, t_hl)
        tb_ = code_block(["bakery.order(kind)", "    .retryWithBackoff()", "    .timeout(1.seconds)"], 24, t_hl)
        tcols = VGroup(VGroup(ta, T("above the retry: each try", 24, CANCEL)).arrange(DOWN, aligned_edge=LEFT, buff=0.3),
                       VGroup(tb_, T("below it: all of them, waits included", 24, CANCEL)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
                       ).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(tcols, 12.6).move_to([0, 0.4, 0])
        self.say("timeout")
        self.play(FadeIn(tcols[0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(tcols[1], shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(tcols), run_time=0.5)

        # ================= the moral and a check =================
        mq = T("Does a timeout fly past catch? No: catch asks who threw.", 32).move_to(UP * 2.55)
        m1 = T("From the cook's side: into the net, timeouts included.", 28, NETC).move_to(UP * 1.8)
        m2 = T("The diner's dropped plate and the caller's own cancel: past it.", 28, BAD).move_to(UP * 1.15)
        m3 = T("A retry cooks the recipe again, from the top.", 28, GREY_A).move_to(UP * 0.5)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("the diner's plate", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(5)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, YELLOW_M), T("catch sits above map, and map throws.", 28)).arrange(RIGHT, buff=0.25),
                    T("Who handles it?", 28)).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.0, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("not that catch: map is below the net, so it falls past, to the caller", 28, BAD)
        fit(ans, 12.4).move_to(DOWN * 2.45)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(1.5)
