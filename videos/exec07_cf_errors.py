from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bthenApply\b", "then apply"), (r"\bwhenComplete\b", "when complete"), (r"\borTimeout\b", "or timeout"),
    (r"\ballOf\b", "all of"), (r"\banyOf\b", "any of"), (r"\bCompletionException\b", "Completion Exception"),
    (r"\bIllegalStateException\b", "Illegal State Exception"), (r"\bTimeoutException\b", "Timeout Exception"),
    (r"\bCompletableFuture\b", "Completable Future"), (r"\bgetCause\b", "get cause"),
    (r"\bcompleteExceptionally\b", "complete exceptionally"), (r"cancel\(true\)", "cancel true"),
    (r"\bErrorPathDemo\b", "Error Path Demo"), (r"\bKeepsRunningDemo\b", "Keeps Running Demo"),
    (r"\bFanOutDemo\b", "Fan Out Demo"), (r"\b21\.50\b", "21 fifty"), (r"\b19\.80\b", "19 eighty"),
    (r"\bHTTP\b", "H T T P"), (r"\bfan-out\b", "fan out"),
]

# every spoken line, in order
N = {
    "shyq": "Here's a question we rarely ask out loud. When the first step of a chain throws, "
            "what happens to the steps after it? Do they run anyway, with nothing in their hands?",
    "ticket": "Back to the kitchen. Last time, the ticket for table 4 carried its own instructions: "
              "grill the steak, pour the sauce, plate it, carry it out. "
              "The ticket was a CompletableFuture, and each instruction a stage.",
    "burn": "Now the steak burns. The sauce cook has no business pouring sauce on charcoal. "
            "So a note goes on the ticket: burned at the grill. "
            "Every later station passes it along, untouched, to the pass, the counter where dishes leave the kitchen. "
            "Someone there reads the note, and decides what table 4 gets.",
    "map": "Let's map it. Each station is a stage, like thenApply. The note is the exception. "
           "The pass is a handler, a stage that also runs after a failure: here, exceptionally.",
    "demo_q": "The lesson's ErrorPathDemo builds this line. The grill always throws: the steak burned. "
              "Each numbered station prints what it does. "
              "Then whenComplete, the manager, glances at every ticket going past, and the pass comes last. "
              "Which numbered lines print?",
    "demo_a": "None. Their code never ran. The manager saw the failure and passed it on. "
              "The pass caught it, and returned: table 4 got an apology and the menu.",
    "joke1": "Not the dinner they ordered. But it beats charcoal with pepper sauce. "
             "So the point is, a failure skips every stage until it reaches a handler.",
    "early": "Where you put the handler decides what you can still save. "
             "Move the pass up, right after the grill, and it can swap in a spare steak. "
             "Then every station after it works as if nothing went wrong.",
    "rule1": "So recover as close to the failure as you can.",
    "env": "Now look at what the pass actually received. Not our IllegalStateException. "
           "A CompletionException, with ours inside. Our note arrived sealed in an envelope.",
    "env_q": "So if the pass asks, is this an IllegalStateException, the answer is no. It's an envelope. "
             "That check is quietly wrong.",
    "env_rule": "The rule: an exception thrown inside a stage travels in an envelope. "
                "A future completed by hand, with completeExceptionally or a timer, holds it bare, "
                "until the next stage seals it again. So open the envelope with getCause, then test the type.",
    "flour": "Now that timer. The restaurant buys flour, and each supplier has a web service, "
             "a program on another computer that answers questions. "
             "Asking for a price is a blocking call: it holds a thread until the answer comes. "
             "So, a cook on the phone.",
    "timer": "The manager sets a kitchen timer. In code, that's orTimeout. "
             "When it rings, the future fails with a TimeoutException, and the manager moves on. "
             "What happens to the cook?",
    "keeps": "The lesson's KeepsRunningDemo gives a 600 millisecond call a deadline of 200. "
             "The future fails right on time, at 236 milliseconds. And the cook? Still on hold. "
             "The supplier answers at 695, and nobody is listening.",
    "music": "He's still listening to the supplier's hold music, the same four notes, over and over. "
             "So the timer freed the manager, not the cook, and the thread stays busy until the call ends.",
    "cancel": "And cancel(true)? It returns true, and the call never notices. Here the picture breaks. "
              "A real manager could walk over and tell the cook to hang up. "
              "A CompletableFuture keeps no line back to the thread doing the work.",
    "two": "So a call to another computer needs two timeouts. The one on the future frees the caller. "
           "The one inside the client, such as a timeout on the HTTP request, makes the call give up, "
           "and frees the thread.",
    "fan": "Now the manager wants three prices at once, from the corner shop, the market and the mill. "
           "Three cooks phone together. Sending several calls at once and collecting the answers is called a fan-out.",
    "fan_q": "In FanOutDemo, the corner shop fails after 50 milliseconds, because it's closed today. "
             "The market answers 21.50 after 100, and the mill answers 19.80 after 300. "
             "allOf waits for all three. What does it hand the manager?",
    "fan_a": "A failure, at 336 milliseconds. Two good prices came back, and the errand failed anyway. "
             "If any future fails, allOf fails, after the slowest is done. "
             "And anyOf, which takes the first to finish? The first news here was the bad news.",
    "fix": "The fix: make each call unable to fail before you combine them. "
           "Each call gets its own deadline, then a handle, which turns a failure into no answer, an empty Optional.",
    "safe": "Run it again. The corner shop becomes no answer, and at 353 milliseconds the next step picks the lowest price: "
            "19.80, from the mill. The cheapest flour came from the slowest supplier. Good thing we waited for it.",
    "code": "Here's one safe call in Java and Kotlin. Keep the deadline on each call. "
            "One deadline on allOf would let a single hung supplier throw away the good answers.",
    "moral": "So, do the steps after a failure run? No. The note rides the ticket to the first handler, "
             "so recover close to the burn. Open the envelope before you read the note. "
             "A kitchen timer frees the manager, not the cook. And make each call unable to fail before you combine.",
    "check": "Quick check. The grill fails. Then come thenApply A, then exceptionally, then thenApply B. "
             "Which of A and B runs?",
    "check_a": "Only B. A is skipped, and exceptionally hands B a value.",
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

    def left(self, until=None):
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video (the same as the last video where they overlap)
MGR, COOK, STEAK, PAPER, STEP, RULE, BAD, PASS, ENV = YELLOW_M, TEAL_M, GOLD_M, GREY_A, BLUE_M, YELLOW_M, RED_M, GREEN_M, PURPLE_M


def person(color, s=1.0, op=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def cook(color=COOK, s=1.0):
    p = person(color)
    band = Rectangle(width=0.26, height=0.08).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1)
    band.next_to(p[1], UP, buff=0.0)
    puff = Circle(radius=0.12).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1).next_to(band, UP, buff=-0.08)
    return VGroup(p[0], p[1], VGroup(puff, band)).scale(s)


def phone(color=STEAK, s=1.0):
    body = RoundedRectangle(corner_radius=0.06, width=0.3, height=0.52).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    scr = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.28).set_stroke(color, 1.5).move_to(body.get_center() + UP * 0.04)
    return VGroup(body, scr).scale(s)


def cook_on_phone(s=1.0):
    c = cook(COOK, s)
    p = phone(STEAK, 0.75 * s).next_to(c[1], RIGHT, buff=0.04)
    return VGroup(c, p)


def tkt(text, w=1.3, h=0.5, size=22, color=PAPER, tcolor=WHITE):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.22), 1)
    return VGroup(r, T(text, size, tcolor).move_to(r))


def chip(text, color, size=20, mono=False):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.3, height=max(0.42, t.height + 0.22))
    r.set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
    return VGroup(r, t.move_to(r))


def station(label, method, color=GREY_B, w=1.75):
    b = box(label, color, w=w, h=0.85, size=24)
    m = M(method, 20, GREY_B).next_to(b, DOWN, buff=0.15)
    return VGroup(b, m)


def envelope(w=3.6, h=2.0, label="CompletionException", size=24):
    r = Rectangle(width=w, height=h).set_stroke(ENV, 3).set_fill(dim(ENV, 0.35), 1)
    flap = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + UP * h * 0.08, r.get_corner(UR)])
    flap.set_stroke(ENV, 2.5)
    t = M(label, size, WHITE).move_to(r.get_center() + DOWN * h * 0.25) if label else VGroup()
    return VGroup(r, flap, t)


def mini_note():
    r = Rectangle(width=1.0, height=0.6).set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.4), 1)
    lines = VGroup(*[Line(LEFT * 0.3, RIGHT * 0.3, stroke_width=2, color=WHITE).shift(UP * dy) for dy in (0.1, -0.08)])
    return VGroup(r, lines.move_to(r))


def house(color=GREY_B, w=1.4, h=0.9):
    r = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    roof = Polygon(r.get_corner(UL) + LEFT * 0.12, r.get_corner(UR) + RIGHT * 0.12, r.get_top() + UP * 0.5)
    roof.set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    door = Rectangle(width=0.26, height=0.42).set_stroke(color, 2).move_to(r.get_bottom() + UP * 0.21)
    return VGroup(r, roof, door)


def kitchen_timer(s=1.0):
    c = Circle(radius=0.3).set_stroke(GREY_A, 3).set_fill(GREY_E, 1)
    knob = Rectangle(width=0.12, height=0.1).set_stroke(GREY_A, 2).set_fill(GREY_D, 1).next_to(c, UP, buff=0)
    hand = Line(c.get_center(), c.get_center() + UP * 0.2 + RIGHT * 0.1, stroke_width=3, color=BAD)
    return VGroup(c, knob, hand).scale(s)


def music_note(color=GREY_A):
    head = Ellipse(width=0.17, height=0.12).set_stroke(color, 2).set_fill(color, 1).rotate(0.4)
    stem = Line(head.get_right() + DOWN * 0.01, head.get_right() + UP * 0.32, stroke_width=2.5, color=color)
    return VGroup(head, stem)


def cross(m, s=0.25, color=BAD):
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(color, 5).move_to(m)


def code_block(src, size=22):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Exec07CfErrors(Narrated):
    """exec-07, section 0 (with sections 1 to 3 as the follow-on): the steak burns at the grill and a note rides the
    ticket past every station to the pass (ErrorPathDemo); a handler right after the grill swaps in a spare steak;
    the note arrives in an envelope (CompletionException); a kitchen timer frees the manager while the cook stays on
    hold (KeepsRunningDemo 236/695); three cooks phone three flour suppliers (FanOutDemo all 84/151/333/336, safe 353)."""

    def construct(self):
        self.title_card("When the steak burns", "errors, timeouts and fan-out with CompletableFuture")

        # ================= the shy question =================
        steps = VGroup(*[box(f"step {i}", GREY_B, w=2.2, h=0.85, size=28) for i in (1, 2, 3)]).arrange(RIGHT, buff=1.1)
        steps.move_to([0, 0.7, 0])
        s_ar = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.1, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.25) for i in (0, 1)])
        boom = T("throws", 26, BAD).next_to(steps[0], DOWN, buff=0.25)
        qs = VGroup(*[T("?", 44, RULE).next_to(steps[i], UP, buff=0.2) for i in (1, 2)])
        ask = T("Do they run anyway, with nothing in their hands?", 32, RULE).move_to([0, -1.5, 0])
        self.say("shyq")
        self.play(FadeIn(steps), FadeIn(s_ar), run_time=0.8)
        self.at(1)
        self.play(steps[0][0].animate.set_stroke(BAD), FadeIn(boom, shift=DOWN * 0.1), run_time=0.6)
        self.at_text("what happens", lead=0.2)
        self.play(FadeIn(qs, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(steps, s_ar, boom, qs, ask)), run_time=0.5)

        # ================= the line of stations =================
        XS = [-5.375, -3.225, -1.075, 1.075, 3.225, 5.375]
        SY, TY = -0.3, 1.25
        specs = [("grill", "supplyAsync", GREY_B), ("1. sauce", "thenApply", GREY_B), ("2. plate", "thenApply", GREY_B),
                 ("3. table 4", "thenApply", GREY_B), ("manager", "whenComplete", MGR), ("the pass", "exceptionally", PASS)]
        st = [station(a, b, c).move_to([x, SY, 0]) for (a, b, c), x in zip(specs, XS)]
        for s_ in st:
            s_[1].next_to(s_[0], DOWN, buff=0.15)
        LBL_Y = st[0][1].get_center()[1] - 0.45

        def links(order):
            return VGroup(*[Arrow(st[order[i]][0].get_right(), st[order[i + 1]][0].get_left(), buff=0.06, stroke_width=3,
                                  color=GREY_D, max_tip_length_to_length_ratio=0.35) for i in range(len(order) - 1)])
        ln4 = links([0, 1, 2, 3])
        ticket = tkt("table 4", 1.3, 0.5, 22).move_to([XS[0], TY, 0]).set_z_index(5)
        top1 = VGroup(T("the ticket:", 26, PAPER), M("CompletableFuture", 26, PAPER)).arrange(RIGHT, buff=0.2)
        top2 = T("each instruction: a stage", 26, STEP)
        tops = VGroup(top1, top2).arrange(RIGHT, buff=0.9).move_to([0, 2.65, 0])
        self.say("ticket")
        self.play(LaggedStart(*[FadeIn(st[i][0]) for i in range(4)], lag_ratio=0.25), FadeIn(ln4), run_time=1.4)
        self.at(1)
        self.play(FadeIn(ticket, shift=DOWN * 0.1), run_time=0.5)
        for i in (1, 2, 3):
            self.play(ticket.animate.set_x(XS[i]), Indicate(st[i][0][1], color=WHITE, scale_factor=1.12), run_time=0.6)
        self.at(2)
        self.play(FadeIn(top1, shift=DOWN * 0.1), Indicate(ticket[1], color=PAPER), run_time=0.7)
        self.at_text("each instruction", lead=0.3)
        self.play(FadeIn(top2, shift=DOWN * 0.1), LaggedStart(*[FadeIn(st[i][1]) for i in range(4)], lag_ratio=0.2), run_time=0.9)
        self.hold()

        # ---- the steak burns ----
        stk = RoundedRectangle(corner_radius=0.12, width=0.7, height=0.32).set_stroke(STEAK, 2.5).set_fill(dim(STEAK, 0.5), 1)
        stk.next_to(st[0][0], UP, buff=0.12).shift(RIGHT * 0.45)
        smoke = VGroup(*[FunctionGraph(lambda t: 0.05 * np.sin(7 * t), x_range=[0, 0.3]).rotate(PI / 2).set_stroke(GREY_B, 2)
                         .move_to(stk.get_top() + UP * 0.22 + RIGHT * dx) for dx in (-0.15, 0.0, 0.15)])
        note = chip("burned at the grill", BAD, 20).set_z_index(5)
        note.next_to(ticket, DOWN, buff=0.06)
        note.set_x(XS[0])
        self.say("burn")
        self.play(FadeOut(tops), ticket.animate.set_x(XS[0]), run_time=0.6)
        self.play(FadeIn(stk, shift=DOWN * 0.1), run_time=0.4)
        self.play(stk.animate.set_fill(GREY_E, 1).set_stroke(BAD), Create(smoke), st[0][0][0].animate.set_stroke(BAD), run_time=0.8)
        self.at(1)
        self.play(Indicate(st[1][0][1], color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(2)
        note.move_to([XS[0], TY - 0.5, 0])
        self.play(FadeIn(note, shift=UP * 0.15), FadeOut(stk), FadeOut(smoke), run_time=0.6)
        tk = VGroup(ticket, note)
        self.at(3)
        self.play(FadeIn(st[5][0]), run_time=0.5)
        hop = ArcBetweenPoints(np.array([XS[0], TY + 0.45, 0]), np.array([XS[5], TY + 0.45, 0]), angle=-PI * 0.35)
        hop = DashedVMobject(hop, num_dashes=40).set_stroke(GREY_B, 2.5)
        hop_l = T("passed along, untouched", 24, GREY_A).move_to([0, 2.5, 0])
        self.play(Create(hop), FadeIn(hop_l), run_time=1.2)
        self.at(4)
        self.play(Indicate(st[5][0][1], color=PASS, scale_factor=1.15), run_time=0.8)
        self.hold()

        # ---- map it ----
        mp = VGroup(VGroup(T("station", 26), T("=", 26, GREY_B), T("a stage", 26, STEP)).arrange(RIGHT, buff=0.15),
                    VGroup(T("note", 26, BAD), T("=", 26, GREY_B), T("the exception", 26)).arrange(RIGHT, buff=0.15),
                    VGroup(T("the pass", 26, PASS), T("=", 26, GREY_B), T("a handler", 26, PASS)).arrange(RIGHT, buff=0.15))
        mp.arrange(RIGHT, buff=0.9)
        fit(mp, 12.4).move_to([0, -2.4, 0])
        self.say("map")
        self.play(FadeOut(hop), FadeOut(hop_l), run_time=0.4)
        self.at(1)
        self.play(FadeIn(mp[0]), *[Indicate(st[i][1], color=STEP, scale_factor=1.1) for i in (1, 2, 3)], run_time=0.8)
        self.at(2)
        self.play(FadeIn(mp[1]), Indicate(note[1], color=WHITE, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(mp[2]), FadeIn(st[5][1]), run_time=0.8)
        self.hold()

        # ---- ErrorPathDemo: predict ----
        ln6 = links([0, 1, 2, 3, 4, 5])
        demo_t = M("ErrorPathDemo", 26, GREY_A).move_to([0, 2.75, 0])
        prints = VGroup(*[T("prints?", 22, GREY_B).move_to([XS[i], LBL_Y, 0]) for i in (1, 2, 3)])
        self.say("demo_q")
        self.play(FadeOut(mp), FadeIn(demo_t), run_time=0.6)
        self.at(2)
        self.play(FadeIn(prints, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(st[4]), FadeOut(ln4), FadeIn(ln6), run_time=0.8)
        self.at(4)
        self.play(Indicate(prints, color=RULE, scale_factor=1.1), run_time=0.8)
        self.hold(after=0)
        self.predict()

        skips = VGroup(*[T("skipped", 22, GREY_B).move_to([XS[i], LBL_Y, 0]) for i in (1, 2, 3)])
        looks = T("looks, passes it on", 22, MGR).move_to([XS[4], LBL_Y, 0])
        apology = chip("apology and the menu", PASS, 20).set_z_index(5).move_to([XS[5], TY - 0.5, 0])
        res = M("result: table 4 got an apology and the menu", 24, PASS).move_to([0, -2.45, 0])
        self.say("demo_a")
        for i in (1, 2, 3):
            self.play(tk.animate.set_x(XS[i]), st[i].animate.set_opacity(0.3), ReplacementTransform(prints[i - 1], skips[i - 1]),
                      run_time=0.55)
        self.at(2)
        self.play(tk.animate.set_x(XS[4]), Indicate(st[4][0][1], color=MGR, scale_factor=1.15), run_time=0.7)
        self.play(FadeIn(looks, shift=UP * 0.1), run_time=0.4)
        self.at(3)
        self.play(tk.animate.set_x(XS[5]), run_time=0.6)
        apology.set_x(XS[5])
        self.play(FadeOut(note, scale=0.6), FadeIn(apology, scale=0.6), Indicate(st[5][0][1], color=PASS, scale_factor=1.15),
                  run_time=0.7)
        self.at_text("table 4 got", lead=0.3)
        self.play(FadeIn(res, shift=UP * 0.1), run_time=0.6)
        self.hold()

        rule0 = T("A failure skips every stage until a handler.", 30, RULE).move_to([0, 2.75, 0])
        self.say("joke1")
        self.at(2)
        self.play(FadeOut(demo_t), FadeIn(rule0, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        # ---- move the pass up ----
        self.say("early")
        self.play(FadeOut(VGroup(skips, looks, res, apology, ticket)), *[st[i].animate.set_opacity(1) for i in (1, 2, 3)],
                  st[0][0][0].animate.set_stroke(GREY_B), FadeOut(rule0), run_time=0.7)
        self.at(1)
        new_x = {1: XS[2], 2: XS[3], 3: XS[4], 4: XS[5]}
        arc = ArcBetweenPoints(st[5].get_center(), np.array([XS[1], st[5].get_center()[1], 0]), angle=PI * 0.6)
        self.play(FadeOut(ln6), run_time=0.3)
        self.play(MoveAlongPath(st[5], arc), *[st[i].animate.set_x(x) for i, x in new_x.items()], run_time=1.2)
        ln_e = links([0, 5, 1, 2, 3, 4])
        ticket2 = tkt("table 4", 1.3, 0.5, 22).move_to([XS[0], TY, 0]).set_z_index(5)
        note2 = chip("burned at the grill", BAD, 20).set_z_index(5).move_to([XS[0], TY - 0.5, 0])
        spare = chip("spare steak", STEAK, 20).set_z_index(5).move_to([XS[1], TY - 0.5, 0])
        tk2 = VGroup(ticket2, note2)
        self.play(FadeIn(ln_e), FadeIn(tk2), st[0][0][0].animate.set_stroke(BAD), run_time=0.5)
        self.play(tk2.animate.set_x(XS[1]), run_time=0.5)
        self.play(FadeOut(note2, scale=0.6), FadeIn(spare, scale=0.6), Indicate(st[5][0][1], color=PASS, scale_factor=1.15),
                  run_time=0.6)
        tk2 = VGroup(ticket2, spare)
        outs = ["1. pour the sauce on the spare steak", "2. plate the spare steak with pepper sauce", "3. carry it to table 4"]
        out_m = VGroup(*[M(o, 22, STEAK) for o in outs]).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([0, -2.45, 0])
        runs = VGroup(*[T("runs", 22, STEAK).move_to([XS[p], LBL_Y, 0]) for p in (2, 3, 4)])
        sees = T("sees success", 22, MGR).move_to([XS[5], LBL_Y, 0])
        self.at(2)
        for k, p in enumerate((2, 3, 4)):
            self.play(tk2.animate.set_x(XS[p]), FadeIn(runs[k]), FadeIn(out_m[k], shift=RIGHT * 0.1), run_time=0.55)
        self.play(tk2.animate.set_x(XS[5]), FadeIn(sees), run_time=0.5)
        self.hold()
        rule1 = T("Recover as close to the failure as you can.", 30, RULE).move_to([0, 2.75, 0])
        self.say("rule1")
        self.play(FadeIn(rule1, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(*st, ln_e, tk2, runs, sees, out_m, rule1)), run_time=0.6)

        # ================= the envelope =================
        big = VGroup(T("IllegalStateException", 26, WHITE), T("the steak burned", 24, WHITE)).arrange(DOWN, buff=0.12)
        big_r = Rectangle(width=big.width + 0.5, height=big.height + 0.4).set_stroke(BAD, 3).set_fill(dim(BAD, 0.45), 1)
        bnote = VGroup(big_r, big.move_to(big_r)).move_to([-3.4, 1.95, 0]).set_z_index(1)
        env = envelope(4.0, 2.1, "CompletionException", 26).move_to([-3.4, 0.0, 0]).set_z_index(2)
        rcv = T("what the pass received", 26, GREY_A).move_to([-3.4, 2.75, 0])
        self.say("env")
        self.play(FadeIn(rcv), FadeIn(bnote, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(bnote[1], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(env, shift=UP * 0.2), run_time=0.6)
        self.play(bnote.animate.move_to([-3.4, 0.82, 0]), run_time=0.8)
        self.at(3)
        self.play(Indicate(env[2], color=ENV, scale_factor=1.1), run_time=0.8)
        self.hold()

        jq = VGroup(T("Java", 22, GREY_B), M("ex instanceof IllegalStateException", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        kq = VGroup(T("Kotlin", 22, GREY_B), M("ex is IllegalStateException", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        qq = VGroup(jq, kq).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([3.0, 1.3, 0])
        fls = M("false", 34, BAD).move_to([3.0, -0.35, 0])
        its = T("it's an envelope", 26, ENV).next_to(fls, DOWN, buff=0.25)
        quiet = T("quietly wrong", 26, BAD).next_to(its, DOWN, buff=0.25)
        self.say("env_q")
        self.play(FadeIn(qq, shift=LEFT * 0.1), run_time=0.7)
        self.at_text("the answer", lead=0.2)
        self.play(FadeIn(fls, scale=0.8), run_time=0.4)
        self.at(1)
        self.play(FadeIn(its), Indicate(env[0], color=ENV, scale_factor=1.03), run_time=0.7)
        self.at(2)
        self.play(FadeIn(quiet, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ---- when the envelope appears ----
        self.play(FadeOut(VGroup(qq, fls, its, quiet, rcv, bnote, env)), run_time=0.6)
        RX = 3.6

        def row(y, words, icon):
            g = VGroup(*words).arrange(RIGHT, buff=0.2)
            g.move_to([-6.2, y, 0], aligned_edge=LEFT)
            icon.move_to([RX, y, 0])
            return VGroup(g, icon)

        def env_icon():
            e = envelope(1.3, 0.75, None)
            n = mini_note().scale(0.55).move_to(e.get_top() + DOWN * 0.08).set_z_index(1)
            e.set_z_index(2)
            return VGroup(n, e)
        r1 = row(1.9, [T("thrown inside a stage", 28)], env_icon())
        r2 = row(0.6, [T("completed by hand:", 28), M("completeExceptionally, orTimeout", 24, GREY_A)], mini_note().scale(0.9))
        r3 = row(-0.7, [T("one stage later", 28)], env_icon())
        lab1 = T("envelope", 22, ENV).next_to(r1[1], RIGHT, buff=0.3)
        lab2 = T("bare", 22, BAD).next_to(r2[1], RIGHT, buff=0.3)
        lab3 = T("envelope again", 22, ENV).next_to(r3[1], RIGHT, buff=0.3)
        rule2 = VGroup(T("Open the envelope with", 30, RULE), M("getCause()", 30, RULE),
                       T("then test the type.", 30, RULE)).arrange(RIGHT, buff=0.2).move_to([0, -2.3, 0])
        fit(rule2, 12.4)
        self.say("env_rule")
        self.play(FadeIn(r1), FadeIn(lab1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2), FadeIn(lab2), run_time=0.7)
        self.at_text("until the next", lead=0.3)
        self.play(FadeIn(r3), FadeIn(lab3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(r1, r2, r3, lab1, lab2, lab3, rule2)), run_time=0.6)

        # ================= the cook on the phone =================
        PY = 1.55
        hs = house().move_to([4.9, PY + 0.05, 0])
        hs_l = T("supplier's web service", 22, GREY_B).next_to(hs, DOWN, buff=0.15)
        ck = cook_on_phone(1.0).move_to([0.6, PY, 0])
        ck_l = T("cook = a thread", 22, COOK).next_to(ck, DOWN, buff=0.15)
        call = DashedLine(ck[1].get_right() + RIGHT * 0.05, hs.get_left() + LEFT * 0.12, dash_length=0.1, stroke_width=2.5,
                          color=STEAK)
        call_l = T("asking for a price", 22, STEAK).next_to(call, DOWN, buff=0.15)
        self.say("flour")
        self.at(1)
        self.play(FadeIn(hs), FadeIn(hs_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(ck), Create(call), FadeIn(call_l), run_time=0.9)
        self.at(3)
        self.play(FadeIn(ck_l), Indicate(ck[1], color=STEAK, scale_factor=1.2), run_time=0.7)
        self.hold()

        mg = person(MGR, 1.0).move_to([-5.6, PY - 0.05, 0])
        mg_l = T("manager", 22, MGR).next_to(mg, DOWN, buff=0.15).set_y(ck_l.get_y())
        tm = kitchen_timer(1.0).move_to([-4.75, PY + 0.1, 0])
        fut = tkt("the future", 1.8, 0.55, 22).move_to([-2.5, PY, 0])
        tm_c = M("orTimeout(200 ms)", 22, GREY_A).move_to([-4.75, PY + 0.75, 0])
        qmark = T("?", 44, RULE).next_to(ck, UP, buff=0.15)
        self.say("timer")
        self.play(FadeIn(mg), FadeIn(mg_l), FadeIn(fut), run_time=0.7)
        self.play(FadeIn(tm, scale=0.7), run_time=0.5)
        self.at(1)
        self.play(FadeIn(tm_c, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(qmark, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()

        # ---- KeepsRunningDemo on a timeline ----
        X0, X1 = -3.0, 5.8
        PX = (X1 - X0) / 800

        def tx(ms):
            return X0 + ms * PX
        FY, CY, AY = -0.55, -1.45, -2.45
        f_lab = T("the future", 24, PAPER).move_to([X0 - 0.25, FY, 0], aligned_edge=RIGHT)
        c_lab = T("io-1, the cook", 24, COOK).move_to([X0 - 0.25, CY, 0], aligned_edge=RIGHT)
        axis = Line([tx(0), AY, 0], [tx(800), AY, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([tx(m), AY + 0.07, 0], [tx(m), AY - 0.07, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([tx(m), AY - 0.32, 0])) for m in (0, 200, 400, 600, 800)])

        def bar(a, b, y, color, label=None):
            r = Rectangle(width=(b - a) * PX, height=0.44, stroke_color=color, stroke_width=2).set_fill(dim(color, 0.35), 1)
            r.move_to([tx((a + b) / 2), y, 0])
            return VGroup(r, T(label, 20).move_to(r)) if label else VGroup(r)
        fb = bar(36, 236, FY, PAPER, "waiting")
        cb1 = bar(36, 236, CY, COOK)
        cb = bar(36, 695, CY, COOK, "on the phone")
        to_chip = chip("TimeoutException at 236 ms", BAD, 20).next_to(fb, RIGHT, buff=0.12)
        ans_l = T("695 ms: the answer arrives, nobody is listening", 22, GREY_A).move_to([X1, CY - 0.5, 0], aligned_edge=RIGHT)
        cur = Line([0, FY + 0.35, 0], [0, CY - 0.35, 0], stroke_width=3, color=WHITE)
        tt = ValueTracker(0.0)
        cur.add_updater(lambda m: m.set_x(tx(tt.get_value())))
        cur.update()
        self.say("keeps")
        self.play(FadeOut(qmark), FadeIn(f_lab), FadeIn(c_lab), FadeIn(axis), FadeIn(ticks), run_time=0.8)
        self.at(1)
        self.add(cur)
        self.play(tt.animate.set_value(236), GrowFromEdge(fb, LEFT), GrowFromEdge(cb1, LEFT), run_time=1.6, rate_func=linear)
        self.play(FadeIn(to_chip, scale=0.8), fut[0].animate.set_stroke(BAD), Wiggle(tm, scale_value=1.15), run_time=0.8)
        self.at(2)
        self.play(Indicate(ck[0], color=COOK, scale_factor=1.12), run_time=0.7)
        self.at(3)
        self.play(tt.animate.set_value(695), UpdateFromAlphaFunc(cb1, lambda m, a: m.become(VGroup(cb[0].copy().stretch_to_fit_width(
            (200 + 459 * a) * PX, about_edge=LEFT).align_to(cb[0], LEFT)))), run_time=2.0, rate_func=linear)
        self.remove(cb1)
        self.add(cb)
        self.play(FadeOut(cur), FadeIn(ans_l, shift=DOWN * 0.1), run_time=0.6)
        cur.clear_updaters()
        self.hold()

        notes = VGroup(*[music_note() for _ in range(4)])
        base = ck[1].get_top() + UP * 0.15
        for k, n_ in enumerate(notes):
            n_.move_to(base + RIGHT * (0.25 + 0.32 * k) + UP * (0.12 * ((k % 2) * 2 - 1)))
        rule3 = T("The timer frees the manager, not the cook.", 30, RULE).move_to([0, 3.15, 0])
        self.say("music")
        self.play(LaggedStart(*[FadeIn(n_, shift=UP * 0.15) for n_ in notes], lag_ratio=0.3), run_time=1.4)
        self.play(notes.animate.shift(UP * 0.12), run_time=0.5, rate_func=there_and_back)
        self.at(1)
        self.play(FadeIn(rule3, shift=DOWN * 0.1), Indicate(cb[0], color=COOK, scale_factor=1.04), run_time=0.8)
        self.hold()

        # ---- cancel(true) ----
        tl = VGroup(f_lab, c_lab, axis, ticks, fb, cb, to_chip, ans_l)
        cc = VGroup(M("cancel(true)", 26, MGR), T("returns true", 26, GREY_A)).arrange(RIGHT, buff=0.25).move_to([-3.4, -0.6, 0])
        never = T("the call never notices", 24, COOK).move_to([0.6, -0.6, 0])
        walk = CurvedArrow(mg.get_top() + UP * 0.15, ck[0].get_top() + UP * 0.45 + LEFT * 0.5, angle=-PI / 3, color=MGR,
                           stroke_width=3)
        walk_l = T("walk over: hang up!", 22, MGR).move_to([-2.4, 2.95, 0])
        line_back = DashedLine(fut.get_right() + RIGHT * 0.08, ck[0].get_left() + LEFT * 0.12, dash_length=0.08, stroke_width=2.5,
                               color=GREY_B)
        lb_x = cross(line_back, 0.2)
        lb_l = T("no line back to the cook", 24, BAD).move_to([-1.0, 0.2, 0])
        self.say("cancel")
        self.play(FadeOut(tl), FadeOut(notes), run_time=0.6)
        self.play(FadeIn(cc, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(never, shift=UP * 0.1), Indicate(ck[1], color=STEAK, scale_factor=1.2), run_time=0.8)
        self.at(3)
        self.play(FadeOut(rule3), run_time=0.3)
        self.play(Create(walk), FadeIn(walk_l), run_time=1.0)
        self.wait(0.6)
        self.play(FadeOut(walk), FadeOut(walk_l), FadeIn(rule3), run_time=0.5)
        self.at(4)
        self.play(Create(line_back), run_time=0.6)
        self.play(Create(lb_x), FadeIn(lb_l), run_time=0.6)
        self.hold()

        # ---- two timeouts ----
        t1 = VGroup(kitchen_timer(0.8), M("orTimeout(300, MILLISECONDS)", 24), T("on the future: frees the caller", 24, MGR))
        t2 = VGroup(kitchen_timer(0.8), M("HttpRequest ... .timeout(Duration.ofMillis(300))", 24),
                    T("in the client: frees the thread", 24, COOK))
        for t_ in (t1, t2):
            t_.arrange(RIGHT, buff=0.3)
        tt2 = VGroup(t1, t2).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(tt2, 12.4).move_to([0, -1.25, 0])
        same = T("the same calls in Java and Kotlin", 22, GREY_B).next_to(tt2, DOWN, buff=0.25)
        tm2 = kitchen_timer(0.6).next_to(ck[1], UP, buff=0.1)
        self.say("two")
        self.play(FadeOut(VGroup(cc, never, line_back, lb_x, lb_l)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(t1, shift=UP * 0.1), Indicate(tm, color=MGR), run_time=0.8)
        self.at(2)
        self.play(FadeIn(t2, shift=UP * 0.1), FadeIn(tm2, scale=0.6), FadeIn(same), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(t1, t2, same, tm2, tm, tm_c, mg, mg_l, fut, ck, ck_l, call, call_l, hs, hs_l, rule3)), run_time=0.7)

        # ================= three cooks, three suppliers =================
        LY = [1.5, 0.3, -0.9]
        F0, F1 = -2.9, 2.5
        FPX = (F1 - F0) / 360

        def fx(ms):
            return F0 + ms * FPX
        names = ["corner shop", "market", "mill"]
        ckf = VGroup(*[cook_on_phone(0.8).move_to([-6.05, y, 0]) for y in LY])
        nm = VGroup(*[T(n, 26).move_to([-5.45, y + 0.12, 0], aligned_edge=LEFT) for n, y in zip(names, LY)])
        subs = ["fails after 50 ms: closed", "21.50 after 100 ms", "19.80 after 300 ms"]
        sb = VGroup(*[T(s_, 20, GREY_B).next_to(nm[k], DOWN, buff=0.08, aligned_edge=LEFT) for k, s_ in enumerate(subs)])
        fan_l = T("fan-out: several calls at once, answers collected", 26, STEP).move_to([-0.6, 2.85, 0])
        AXX = 5.45
        allof = RoundedRectangle(corner_radius=0.15, width=1.6, height=3.5).set_stroke(WHITE, 3).set_fill(BLACK, 1)
        allof.move_to([AXX, LY[1], 0])
        allof_l = M("allOf", 26).next_to(allof, UP, buff=0.15)
        fax = Line([fx(0), -1.65, 0], [fx(360), -1.65, 0], stroke_width=2, color=GREY_B)
        fticks = VGroup(*[VGroup(Line([fx(m), -1.58, 0], [fx(m), -1.72, 0], stroke_width=2, color=GREY_B),
                                 T(f"{m} ms" if m else "0", 22, GREY_B).move_to([fx(m), -1.97, 0])) for m in (0, 100, 200, 300)])
        self.say("fan")
        self.at_text("the corner shop", lead=0.3)
        self.play(FadeIn(nm[0]), run_time=0.4)
        self.at_text("the market", lead=0.3)
        self.play(FadeIn(nm[1]), run_time=0.4)
        self.at_text("the mill", lead=0.3)
        self.play(FadeIn(nm[2]), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c_) for c_ in ckf], lag_ratio=0.2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(fan_l, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        self.say("fan_q")
        self.play(FadeIn(sb[0]), FadeIn(fax), FadeIn(fticks), run_time=0.7)
        self.at(1)
        self.play(FadeIn(sb[1]), run_time=0.4)
        self.at_text("and the mill", lead=0.3)
        self.play(FadeIn(sb[2]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(allof), FadeIn(allof_l), run_time=0.7)
        self.hold(after=0)
        self.predict()

        def race(times, through=None):
            """Bars grow on a clock; each answer flies to allOf (through the handle boxes if given). Returns what is left."""
            bars = [Rectangle(width=t * FPX, height=0.4, stroke_color=COOK, stroke_width=2).set_fill(dim(COOK, 0.35), 1)
                    .move_to([fx(t / 2), y, 0]) for t, y in zip(times, LY)]
            ans = [chip("closed", BAD, 20), chip("21.50", STEAK, 20), chip("19.80", STEAK, 20)]
            stamps = VGroup(*[T(str(t), 20, GREY_A).next_to(b_, DOWN, buff=0.06).align_to(b_, RIGHT) for t, b_ in zip(times, bars)])
            for a_, b_ in zip(ans, bars):
                a_.next_to(b_, RIGHT, buff=0.1)
            cur_ = Line([0, LY[0] + 0.4, 0], [0, LY[2] - 0.4, 0], stroke_width=3, color=WHITE)
            tv = ValueTracker(0.0)
            cur_.add_updater(lambda m: m.set_x(fx(tv.get_value())))
            cur_.update()
            self.add(cur_)
            grow = [b_.copy().stretch_to_fit_width(0.001, about_edge=LEFT) for b_ in bars]
            for g_ in grow:
                self.add(g_)
            prev = 0
            out = []
            for k in range(3):
                t = times[k]
                dt = (t - prev) / 360 * 3.4
                self.play(tv.animate.set_value(t),
                          *[UpdateFromAlphaFunc(grow[j], lambda m, a, j=j, p0=prev, t0=t: m.become(
                              bars[j].copy().stretch_to_fit_width(max(0.001, (min(times[j], p0 + (t0 - p0) * a)) * FPX),
                                                                   about_edge=LEFT).align_to(bars[j], LEFT)))
                            for j in range(k, 3)],
                          run_time=max(0.3, dt), rate_func=linear)
                self.play(FadeIn(ans[k], scale=0.7), FadeIn(stamps[k]), run_time=0.25)
                a_ = ans[k]
                if through is not None:
                    self.play(a_.animate.move_to([through[0], LY[k], 0]), run_time=0.35)
                    if through[1][k] is not None:
                        nb = through[1][k].move_to([through[0], LY[k], 0])
                        self.play(ReplacementTransform(a_, nb), run_time=0.3)
                        a_ = nb
                self.play(a_.animate.move_to([AXX, LY[k], 0]), run_time=0.4)
                out.append(a_)
                prev = t
            cur_.clear_updaters()
            self.play(FadeOut(cur_), run_time=0.3)
            return grow, out, stamps

        g1, o1, s1 = race([84, 151, 333])
        failed = T("allOf failed at 336 ms", 24, BAD).move_to([6.3, -2.35, 0], aligned_edge=RIGHT)
        anyl = T("anyOf: the first to finish was the corner shop's failure, at 161 ms", 22, GREY_A).move_to([0, -3.0, 0])
        fit(anyl, 12.4)
        self.say("fan_a")
        self.play(allof.animate.set_stroke(BAD), FadeIn(failed, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(o1[1][1], color=STEAK, scale_factor=1.3), Indicate(o1[2][1], color=STEAK, scale_factor=1.3), run_time=0.9)
        self.at(2)
        self.play(Indicate(g1[2], color=COOK, scale_factor=1.05), run_time=0.9)
        self.at(3)
        self.play(FadeIn(anyl, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(Indicate(o1[0][1], color=BAD, scale_factor=1.3), run_time=0.8)
        self.hold()

        # ---- the fix: a deadline and a handle on each call ----
        HX = 3.5

        def hbox():
            g = VGroup(T("deadline", 20, GREY_A), M("handle", 22, PASS)).arrange(DOWN, buff=0.06)
            r = RoundedRectangle(corner_radius=0.1, width=1.55, height=0.92).set_stroke(PASS, 2.5).set_fill(dim(PASS, 0.14), 1)
            return VGroup(r, g.move_to(r))
        hb = VGroup(*[hbox().move_to([HX, y, 0]) for y in LY])
        self.say("fix")
        self.play(FadeOut(VGroup(*g1, *o1, s1, failed, anyl)), allof.animate.set_stroke(WHITE), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(h_, shift=LEFT * 0.15) for h_ in hb], lag_ratio=0.25), run_time=1.0)
        self.hold()

        self.say("safe")
        self.wait(0.6)
        empty = chip("no answer", GREY_B, 20)
        g2, o2, s2 = race([91, 170, 340], through=(HX, [empty, None, None]))
        best = T("lowest price: 19.80, at 353 ms", 24, STEAK).move_to([6.3, -2.35, 0], aligned_edge=RIGHT)
        self.at_text("at 353", lead=0.3)
        self.play(allof.animate.set_stroke(PASS), FadeIn(best, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(g2[2], color=COOK, scale_factor=1.05), Indicate(o2[2][1], color=STEAK, scale_factor=1.3), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(*g2, *o2, s2, best, hb, allof, allof_l, fax, fticks, ckf, nm, sb, fan_l)), run_time=0.7)

        # ================= the code =================
        jsrc = ["CompletableFuture<Optional<BigDecimal>> safe = ask(supplier)",
                "        .orTimeout(200, TimeUnit.MILLISECONDS)          // this supplier's deadline",
                "        .handle((price, ex) -> ex == null ? Optional.of(price) : Optional.empty());"]
        ksrc = ["val safe: CompletableFuture<Optional<BigDecimal>> = ask(supplier)",
                "    .orTimeout(200, TimeUnit.MILLISECONDS)              // this supplier's deadline",
                "    .handle { price, ex -> if (ex == null) Optional.of(price) else Optional.empty() }"]
        jc, kc = code_block(jsrc, 22), code_block(ksrc, 22)
        for c_ in (jc, kc):
            c_[1].set_color(RULE)
            c_[2].set_color(PASS)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.4).move_to([0, 0.9, 0])
        bad = M("allOf(corner, market, mill).orTimeout(...)", 24, GREY_B).move_to([0, -2.2, 0])
        bad_x = Line(bad.get_left() + LEFT * 0.1, bad.get_right() + RIGHT * 0.1, stroke_width=4, color=BAD)
        bad_l = T("one hung supplier would throw away the good answers", 24, BAD).next_to(bad, DOWN, buff=0.2)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=RULE, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(FadeIn(bad), run_time=0.5)
        self.play(Create(bad_x), FadeIn(bad_l), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(cols, bad, bad_x, bad_l)), run_time=0.6)

        # ================= moral and check =================
        mo = VGroup(T("The note rides the ticket to the first handler: recover close to the burn.", 30),
                    T("Open the envelope before you read the note.", 30, ENV),
                    T("A kitchen timer frees the manager, not the cook.", 30, MGR),
                    T("Make each call unable to fail before you combine.", 30, PASS)).arrange(DOWN, buff=0.32)
        fit(mo, 12.4).move_to([0, 0.4, 0])
        self.say("moral")
        for i in range(4):
            self.at(i + 2)
            self.play(FadeIn(mo[i], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(mo), run_time=0.5)

        cb_ = VGroup(box("grill fails", BAD, w=2.3, h=0.8, size=26), mbox("thenApply A", GREY_B, w=2.5, h=0.8, size=22),
                     mbox("exceptionally", PASS, w=2.5, h=0.8, size=22), mbox("thenApply B", GREY_B, w=2.5, h=0.8, size=22))
        cb_.arrange(RIGHT, buff=0.5)
        fit(cb_, 12.4).move_to([0, 1.0, 0])
        c_ar = VGroup(*[Arrow(cb_[i].get_right(), cb_[i + 1].get_left(), buff=0.06, stroke_width=3, color=GREY_D,
                              max_tip_length_to_length_ratio=0.35) for i in range(3)])
        cq = T("Which of A and B runs?", 32, RULE).move_to([0, -0.6, 0])
        chk_t = T("Check:", 28, RULE).move_to([0, 2.4, 0])
        self.say("check")
        self.play(FadeIn(chk_t), FadeIn(cb_), FadeIn(c_ar), run_time=0.9)
        self.at(2)
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        sk = T("skipped", 24, GREY_B).next_to(cb_[1], DOWN, buff=0.2)
        rn = T("runs", 24, PASS).next_to(cb_[3], DOWN, buff=0.2)
        ans = T("Only B. A is skipped, and exceptionally hands B a value.", 30, STEAK).move_to([0, -1.8, 0])
        self.say("check_a")
        self.play(cb_[1].animate.set_opacity(0.3), FadeIn(sk), FadeIn(rn), run_time=0.7)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
