from fg import *

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Za-z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads a different spelling than the caption shows), captions split
    only where a new sentence starts, and seq() to start animations at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        dur = self._speak(text, say)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if idx >= len(starts):
                print(f"SEQ WARNING: sentence {idx} of {len(starts)} in: {text[:60]}")
                idx = len(starts) - 1
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


def fill_of(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=24, color=WHITE, pitch=1.6, t2c=None):
    """Code lines, left aligned, indentation kept (a hidden '|' anchors each line)."""
    step = M("|", size).height * pitch
    g = VGroup()
    for i, ln in enumerate(lines):
        t = Text("|" + ln, font=MONO, font_size=size, color=color, t2c=t2c or {}, disable_ligatures=True)
        t.shift(np.array([0, -i * step, 0]) - t[0].get_center())
        t.remove(t[0])
        g.add(t)
    return g


def station(name, w=2.3, color=WHITE, size=26):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=0.85, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    return VGroup(r, M(name, size).move_to(r)).set_z_index(4)


def flash(r, color=YELLOW_M):
    return ShowPassingFlash(r.copy().set_fill(opacity=0).set_stroke(color, 7), time_width=0.6)


def train(text, color=BLUE_M, size=22):
    """A request token: opaque, and drawn under the stations so it passes through them like a tunnel."""
    c = chip(text, color, size=size, mono=True)
    c[0].set_fill(fill_of(color, 0.25), opacity=1)
    return c.set_z_index(2)


def solid_chip(text, color, size=22):
    c = chip(text, color, size=size, mono=True)
    c[0].set_fill(fill_of(color, 0.25), opacity=1)
    return c


# one colour per meaning for the whole video
OK_C, ERR_C, REQ_C, CANCEL_C = GREEN_M, RED_M, BLUE_M, GOLD_M
TOP_Y, BOT_Y = 0.95, -0.85
SX = [-3.3, -0.3, 2.7]
END_X = 5.55


class Fp07Errors(Beat):
    """fp-07 section 3 (with the railway of section 1 and runCatching from section 2): errors as values,
    fail fast versus collecting every error, and runCatching catching the cancel."""

    def construct(self):
        self.title_card("Errors as values", "fail fast, or collect every error")

        # ---------------- the problem: a thrown decline nobody expects ----------------
        http = station("HTTP layer", 3.6, GREY_B, 26).move_to([-2.6, 2.0, 0])
        endp = station("new endpoint", 3.6, WHITE, 26).move_to([-2.6, 0.4, 0])
        auth = station("authorize(p): AuthCode", 5.0, WHITE, 24).move_to([-2.6, -1.2, 0])
        links = VGroup(Line(http.get_bottom(), endp.get_top(), stroke_width=2, color=GREY_D),
                       Line(endp.get_bottom(), auth.get_top(), stroke_width=2, color=GREY_D))
        note = T("no try", 24, GREY_B).next_to(endp, LEFT, buff=0.3)
        sig = T("nothing here says it can fail", 24, GREY_B).next_to(auth, DOWN, buff=0.3)
        pay = train("payment").move_to(endp.get_center() + LEFT * 2.6)
        EX = 0.3          # the exception climbs beside the layers, never over their labels
        exc = solid_chip("CardDeclinedException", ERR_C).set_z_index(7)
        exc.move_to([EX + exc.width / 2, auth.get_y(), 0])
        e500 = VGroup(chip("500", ERR_C, size=30, mono=True), T("for a card that was out of money", 24, ERR_C)
                      ).arrange(RIGHT, buff=0.25)
        e500.move_to([EX + e500.width / 2, http.get_y(), 0])
        pay.move_to([-2.6, -0.4, 0]).set_z_index(6)
        self.seq("A card is declined, and authorize throws. Nothing in its Kotlin signature says so. "
                 "A new endpoint forgets the try, and the customer gets a 500.",
                 [(0, [FadeIn(VGroup(http, endp, auth, links))], 0.7),
                  (0, [FadeIn(pay)], 0.3),
                  (0, [pay.animate.move_to([-2.6, -0.95, 0]).set_opacity(0)], 0.7),
                  (0, [FadeOut(pay), flash(auth[0], ERR_C), FadeIn(exc, shift=RIGHT * 0.3)], 0.5),
                  (1, [FadeIn(sig, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(note)], 0.4),
                  (2, [exc.animate.move_to([exc.get_x(), endp.get_y(), 0])], 0.6),
                  (2, [exc.animate.move_to([exc.get_x(), http.get_y(), 0])], 0.6),
                  (2, [ReplacementTransform(exc, e500), flash(http[0], ERR_C)], 0.7)],
                 say="A card is declined, and authorize throws. Nothing in its Kotlin signature says so. "
                     "A new endpoint forgets the try, and the customer gets a five hundred.")

        ok_box = chip("Ok(value)", OK_C, size=28, mono=True)
        err_box = chip("Err(error)", ERR_C, size=28, mono=True)
        boxes = VGroup(ok_box, T("or", 28, GREY_B), err_box).arrange(RIGHT, buff=0.4).move_to([0, -0.6, 0])
        ret = T("a result that is one of two things", 28).next_to(boxes, UP, buff=0.5)
        self.seq("A decline happens every day. Return it as a value: a result that holds either the value, or the error.",
                 [(0, [FadeOut(VGroup(http, endp, auth, links, note, sig, e500))], 0.6),
                  (1, [FadeIn(ret)], 0.5),
                  (1, [FadeIn(ok_box, shift=UP * 0.1)], 0.5),
                  (1, [FadeIn(boxes[1]), FadeIn(err_box, shift=UP * 0.1)], 0.5)])

        # ---------------- the railway ----------------
        top = Line([-6.1, TOP_Y, 0], [END_X - 0.5, TOP_Y, 0], stroke_width=4, color=OK_C)
        bot = Line([SX[0] + 0.9, BOT_Y, 0], [END_X - 0.5, BOT_Y, 0], stroke_width=4, color=ERR_C)
        st = [station(n) .move_to([x, TOP_Y, 0]) for n, x in zip(("validate", "authorise", "capture"), SX)]
        sw = [Line([x + 0.75, TOP_Y - 0.42, 0], [x + 1.35, BOT_Y, 0], stroke_width=4, color=ERR_C) for x in SX]
        ok_end = solid_chip("Ok", OK_C, 26).move_to([END_X, TOP_Y, 0]).set_z_index(5)
        err_end = solid_chip("Err", ERR_C, 26).move_to([END_X, BOT_Y, 0]).set_z_index(5)
        lab_ok = T("success", 22, OK_C).move_to([-6.1, TOP_Y + 0.55, 0], aligned_edge=LEFT)
        lab_err = T("failure", 22, ERR_C).next_to(bot, DOWN, buff=0.2).align_to(bot, LEFT)
        rail = VGroup(top, bot, *sw, *st, ok_end, err_end, lab_ok, lab_err)
        self.seq("Chain the steps of a payment: validate, authorise, capture. "
                 "Each step keeps the payment on the success track, or switches it to the failure track.",
                 [(0, [ReplacementTransform(ok_box, ok_end), ReplacementTransform(err_box, err_end),
                       FadeOut(VGroup(ret, boxes[1]))], 0.8),
                  (0, [Create(top), FadeIn(lab_ok)], 0.6),
                  (0, [LaggedStart(*[FadeIn(s, shift=DOWN * 0.1) for s in st], lag_ratio=0.3)], 1.0),
                  (1, [Create(bot), FadeIn(lab_err), *[Create(x) for x in sw]], 0.9)])

        def printed(names):
            return VGroup(T("printed", 22, GREY_B), M("  ".join(names), 22)).arrange(RIGHT, buff=0.3
                                                                                   ).move_to([-6.1, -2.35, 0], aligned_edge=LEFT)

        def result(text, color):
            return VGroup(T("result", 22, GREY_B), M(text, 22, color)).arrange(RIGHT, buff=0.3
                                                                              ).move_to([-6.1, -2.95, 0], aligned_edge=LEFT)

        t1 = train("Req(500)").move_to([-5.3, TOP_Y, 0])
        p1, r1 = printed(["validate", "authorise", "capture"]), result("Ok(value=CAP-OF-AUTH-1)", OK_C)
        plan = [(0, [FadeIn(t1, shift=RIGHT * 0.2)], 0.4)]
        for k in range(3):
            plan.append((0, [t1.animate.move_to([SX[k], TOP_Y, 0])], 0.55))
            plan.append((0, [flash(st[k][0], OK_C), Indicate(st[k][1], color=OK_C, scale_factor=1.08)], 0.35))
        plan += [(0, [t1.animate.move_to(ok_end).scale(0.3).set_opacity(0)], 0.6),
                 (0, [FadeOut(t1, run_time=0.2), flash(ok_end[0], OK_C), FadeIn(p1), FadeIn(r1)], 0.6)]
        self.seq("A request for 500 cents passes all three steps, and comes out as Ok.", plan,
                 say="A request for five hundred cents passes all three steps, and comes out as Ok.")

        t2 = train("Req(50000)").move_to([-5.4, TOP_Y, 0])
        self.seq("Now a request for 50,000 cents. The issuer declines it at authorise. Does capture run?",
                 [(0, [FadeOut(VGroup(p1, r1)), FadeIn(t2, shift=RIGHT * 0.2)], 0.6),
                  (1, [Indicate(st[1], color=ERR_C, scale_factor=1.05)], 0.8)],
                 say="Now a request for fifty thousand cents. The issuer declines it at authorise. Does capture run?")
        self.wait(2.2)

        p2, r2 = printed(["validate", "authorise"]), result("Err(error=Declined)", ERR_C)
        never = T("never runs", 24, GREY_B).next_to(st[2], UP, buff=0.2)
        self.seq("No. The train switches to the failure track, and rides past capture to the end. "
                 "The first failure wins, and nothing after it runs. That is called fail fast.",
                 [(0, [t2.animate.move_to([SX[0], TOP_Y, 0])], 0.5),
                  (0, [flash(st[0][0], OK_C)], 0.3),
                  (0, [t2.animate.move_to([SX[1], TOP_Y, 0])], 0.5),
                  (0, [flash(st[1][0], ERR_C), t2[0].animate.set_stroke(ERR_C).set_fill(fill_of(ERR_C, 0.25), 1)], 0.4),
                  (0, [MoveAlongPath(t2, Line([SX[1], TOP_Y, 0], sw[1].get_end()))], 0.5),
                  (0, [t2.animate.move_to(err_end).scale(0.3).set_opacity(0), st[2].animate.set_opacity(0.35),
                       FadeIn(never)], 1.3),
                  (0, [FadeOut(t2, run_time=0.2), flash(err_end[0], ERR_C)], 0.5),
                  (1, [FadeIn(p2), FadeIn(r2)], 0.5),
                  (2, [Indicate(VGroup(st[2], never), color=GREY_B, scale_factor=1.05)], 0.8)])
        self.play(FadeOut(VGroup(rail, t2, p2, r2, never)), run_time=0.7)

        # ---------------- a form: fail fast versus collect every error ----------------
        def form(y):
            g = VGroup(M("amount   -5", 22), M("currency XYZ", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            r = RoundedRectangle(corner_radius=0.14, width=g.width + 0.5, height=g.height + 0.4, stroke_color=REQ_C,
                                 stroke_width=3).set_fill(fill_of(REQ_C), 1)
            g.move_to(r)
            return VGroup(r, g).move_to([-5.2, y, 0]).set_z_index(4)

        AY, BY = 2.2, -1.3
        hA = T("fail fast", 28).move_to([-6.2, AY + 0.85, 0], aligned_edge=LEFT)
        fA = form(AY)
        vaA = station("validAmount", 2.6, WHITE, 24).move_to([-2.2, AY, 0])
        vcA = station("validCurrency", 2.9, WHITE, 24).move_to([1.0, AY, 0])
        trkA = Line(fA.get_right(), [3.4, AY, 0], stroke_width=3, color=GREY_B)
        swA = Line(vaA.get_bottom() + RIGHT * 0.6, [-1.0, AY - 0.8, 0], stroke_width=4, color=ERR_C)
        failA = Line([-1.0, AY - 0.8, 0], [3.4, AY - 0.8, 0], stroke_width=4, color=ERR_C)
        eA = solid_chip("InvalidAmount(-5)", ERR_C).set_z_index(6)
        eA.move_to([swA.get_end()[0] + eA.width / 2, AY - 0.8, 0])
        resA = M("Either.Left(InvalidAmount(amountMinor=-5))", 22, ERR_C).move_to([-6.2, AY - 1.45, 0], aligned_edge=LEFT)
        sep = DashedLine([-6.2, 0.3, 0], [6.2, 0.3, 0], dash_length=0.08, stroke_width=1.2, color=GREY_D)

        hB = T("collect every error", 28).move_to([-6.2, -0.1, 0], aligned_edge=LEFT)
        fB = form(BY)
        vaB = station("validAmount", 2.6, WHITE, 24).move_to([-1.9, BY + 0.55, 0])
        vcB = station("validCurrency", 2.9, WHITE, 24).move_to([-1.9, BY - 0.55, 0])
        fan = VGroup(Line(fB.get_right(), vaB.get_left(), stroke_width=3, color=GREY_B),
                     Line(fB.get_right(), vcB.get_left(), stroke_width=3, color=GREY_B))
        tray = RoundedRectangle(corner_radius=0.16, width=4.5, height=1.75, stroke_color=ERR_C, stroke_width=3)
        tray.set_fill(fill_of(ERR_C, 0.08), 1).move_to([3.75, BY, 0])
        tray_t = M("NonEmptyList", 22, ERR_C).next_to(tray, UP, buff=0.1).align_to(tray, LEFT)
        eB1 = solid_chip("InvalidAmount(-5)", ERR_C).set_z_index(6).move_to(tray.get_center() + UP * 0.38)
        eB2 = solid_chip("UnsupportedCurrency(XYZ)", ERR_C).set_z_index(6).move_to(tray.get_center() + DOWN * 0.38)
        resB = M("Either.Left([InvalidAmount(amountMinor=-5), UnsupportedCurrency(code=XYZ)])", 22, ERR_C)
        resB.move_to([-6.2, BY - 1.6, 0], aligned_edge=LEFT)
        fit(resB, 12.5)

        self.seq("Fail fast suits a pipeline, where each step needs the one before. Not a form. "
                 "A client sends an amount of minus 5 and an unknown currency.",
                 [(1, [FadeIn(hA), FadeIn(fA), FadeIn(trkA), FadeIn(vaA), FadeIn(vcA)], 0.8),
                  (2, [Indicate(fA, color=REQ_C, scale_factor=1.05)], 0.8)])
        self.seq("Fail fast stops at the amount. The currency check never runs, "
                 "so the client fixes one field, sends again, and only then hears about the other.",
                 [(0, [flash(vaA[0], ERR_C)], 0.5),
                  (0, [Create(swA), Create(failA)], 0.5),
                  (0, [FadeIn(eA, shift=RIGHT * 0.3)], 0.4),
                  (0, [eA.animate.move_to([failA.get_end()[0] + 0.5, AY - 0.8, 0])], 0.8),
                  (0, [vcA.animate.set_opacity(0.35), FadeIn(resA)], 0.6),
                  (1, [Indicate(fA, color=REQ_C, scale_factor=1.05)], 0.8)])
        self.wait(0.3)
        self.seq("To collect every error, run the independent checks side by side. "
                 "Both fail, and both errors land in one list.",
                 [(0, [FadeIn(sep), FadeIn(hB), FadeIn(fB), Create(fan), FadeIn(vaB), FadeIn(vcB)], 0.9),
                  (1, [flash(vaB[0], ERR_C), flash(vcB[0], ERR_C), FadeIn(tray), FadeIn(tray_t)], 0.6),
                  (1, [FadeIn(eB1, target_position=vaB.get_right()), FadeIn(eB2, target_position=vcB.get_right())], 1.0),
                  (1, [FadeIn(resB)], 0.5)])
        self.beat("In Arrow, zipOrAccumulate does this: every check runs, and the Amount is built only if all of them pass.",
                  Indicate(tray_t, color=ERR_C), run_time=1.0,
                  say="In Arrow, zip-or-accumulate does this: every check runs, and the Amount is built only if all of them pass.")
        self.play(FadeOut(VGroup(sep, hA, fA, trkA, vaA, vcA, swA, failA, eA, resA, hB, fB, fan, vaB, vcB, tray, tray_t, eB1, eB2, resB)),
                  run_time=0.7)

        # ---------------- runCatching catches the cancel ----------------
        b1 = code(["runCatching { delay(1_000) }"], 24)[0]
        b1r = RoundedRectangle(corner_radius=0.14, width=b1.width + 0.5, height=0.85, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
        b1g = VGroup(b1r, b1.move_to(b1r)).move_to([-5.8, 1.0, 0], aligned_edge=LEFT)
        b2 = code(['ledger += "charged card"'], 24)[0]
        b2r = RoundedRectangle(corner_radius=0.14, width=b2.width + 0.5, height=0.85, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
        b2g = VGroup(b2r, b2.move_to(b2r)).move_to([-5.8, -0.7, 0], aligned_edge=LEFT)
        job = T("a Kotlin coroutine", 24, GREY_B).next_to(b1g, UP, buff=0.3).align_to(b1g, LEFT)
        led = RoundedRectangle(corner_radius=0.16, width=3.4, height=1.4, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
        led.move_to([4.4, -1.15, 0])
        led_t = T("ledger", 24).move_to(led.get_top() + DOWN * 0.3)
        cancel = chip("cancel", CANCEL_C, size=24, mono=True).set_z_index(7).move_to([4.4, 2.6, 0])
        caught = VGroup(T("a failed Result:", 22, CANCEL_C), M("JobCancellationException", 22, CANCEL_C)).arrange(RIGHT, buff=0.2)
        caught.next_to(b1g, RIGHT, buff=0.3)
        charged = chip("charged card", ERR_C, size=22, mono=True).set_z_index(7).move_to(b2g)
        cur = Triangle(color=WHITE).set_fill(WHITE, 1).scale(0.12).rotate(-PI / 2).next_to(b1g, LEFT, buff=0.12)
        self.seq("One trap sits at the edge. runCatching catches every Throwable, "
                 "and in a coroutine that includes the cancel. "
                 "Cancel this job while it waits. The cancel becomes a failed Result, the job runs on, "
                 "and the card is charged anyway.",
                 [(0, [FadeIn(VGroup(job, b1g, b2g, led, led_t))], 0.8),
                  (1, [FadeIn(cur)], 0.3),
                  (2, [FadeIn(cancel, shift=DOWN * 0.2)], 0.5),
                  (2, [cancel.animate.move_to(b1g.get_right() + LEFT * 0.7)], 0.8),
                  (3, [ReplacementTransform(cancel, caught), flash(b1r, CANCEL_C)], 0.7),
                  (3, [cur.animate.next_to(b2g, LEFT, buff=0.12)], 0.5),
                  (3, [flash(b2r, ERR_C), charged.animate.move_to(led.get_center() + DOWN * 0.2)], 0.9)],
                 say="One trap sits at the edge. run-catching catches every Throwable, "
                     "and in a coroutine that includes the cancel. "
                     "Cancel this job while it waits. The cancel becomes a failed Result, the job runs on, "
                     "and the card is charged anyway.")

        fixl = code([".onFailure { if (it is CancellationException) throw it }"], 22, t2c={"throw it": CANCEL_C})[0]
        fixl.next_to(b1g, DOWN, buff=0.18).align_to(b1g, LEFT)
        cancel2 = chip("cancel", CANCEL_C, size=24, mono=True).set_z_index(7).move_to([4.4, 2.6, 0])
        gone = T("job cancelled, ledger stays empty", 24, CANCEL_C).move_to([0, -2.8, 0])
        self.seq("Rethrow CancellationException in onFailure, and the cancel keeps going. Nothing is charged.",
                 [(0, [FadeOut(charged), FadeOut(caught), cur.animate.next_to(b1g, LEFT, buff=0.12)], 0.5),
                  (0, [FadeIn(fixl, shift=UP * 0.1)], 0.6),
                  (0, [FadeIn(cancel2, shift=DOWN * 0.2)], 0.4),
                  (0, [cancel2.animate.move_to(b1g.get_right() + LEFT * 0.7)], 0.7),
                  (0, [cancel2.animate.move_to(fixl.get_right() + LEFT * 0.9)], 0.5),
                  (0, [cancel2.animate.move_to(job.get_right() + RIGHT * 1.2).set_opacity(0), FadeOut(cur),
                       b2g.animate.set_opacity(0.3)], 0.8),
                  (1, [FadeIn(gone, shift=UP * 0.1)], 0.5)])
        self.play(FadeOut(VGroup(job, b1g, b2g, led, led_t, fixl, gone)), run_time=0.6)

        # ---------------- code, Kotlin and Java ----------------
        kt = code(["either { Amount(validAmount(a), validCurrency(c)) }   // fail fast",
                   "either {   // collect every error",
                   "    zipOrAccumulate({ validAmount(a) }, { validCurrency(c) }) {",
                   "        amount, currency -> Amount(amount, currency) }",
                   "}"], 22, t2c={"// fail fast": GREY_B, "// collect every error": GREY_B})
        jv = code(["List<FormError> errors = new ArrayList<>();",
                   "if (a <= 0) errors.add(new InvalidAmount(a));",
                   "if (!CURRENCIES.contains(c)) errors.add(new UnsupportedCurrency(c));"], 22)
        kh, jh = T("Kotlin, with Arrow", 24, GREY_B), T("Java: collect by hand", 24, GREY_B)
        kh.next_to(kt, UP, buff=0.25).align_to(kt, LEFT)
        jv.next_to(kt, DOWN, buff=0.9).align_to(kt, LEFT)
        jh.next_to(jv, UP, buff=0.25).align_to(jv, LEFT)
        cg = VGroup(kh, kt, jh, jv)
        cg.scale(min(1, 12.6 / cg.width)).move_to([0, 0.35, 0])
        self.seq("In code, Arrow's either block fails fast, and zipOrAccumulate collects. "
                 "Java has no Arrow: you collect the errors in a list yourself.",
                 [(0, [FadeIn(VGroup(kh, kt), shift=UP * 0.15)], 0.9),
                  (1, [FadeIn(VGroup(jh, jv), shift=UP * 0.15)], 0.9)],
                 say="In code, Arrow's either block fails fast, and zip-or-accumulate collects. "
                     "Java has no Arrow: you collect the errors in a list yourself.")
        self.wait(1.0)
        self.play(FadeOut(cg), run_time=0.6)

        # ---------------- the rule and a check ----------------
        rule = VGroup(T("Fail fast when each step needs the one before.", 32),
                      T("Collect every error when the checks are independent.", 32)).arrange(DOWN, buff=0.25).move_to([0, 2.4, 0])
        self.beat("So: fail fast when each step needs the one before. Collect every error when the checks are independent, "
                  "like the fields of a form.",
                  LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in rule], lag_ratio=0.5), run_time=2.0)

        mini = VGroup(*[station(n, 2.1, WHITE, 24).move_to([x, 0.4, 0]) for n, x in zip(("validate", "authorise", "capture"), (-3.0, 0, 3.0))])
        rails = Line([-5.0, 0.4, 0], [5.0, 0.4, 0], stroke_width=4, color=OK_C).set_z_index(0)
        t3 = train("Req(-1)").move_to([-5.0, 0.4, 0])
        q = T("Which steps run, and what comes out?", 26, GREY_B).move_to([0, -0.7, 0])
        self.seq("A quick check. A request for minus 1 cents rides the railway. Which steps run, and what comes out?",
                 [(0, [FadeIn(rails), FadeIn(mini)], 0.6),
                  (1, [FadeIn(t3, shift=RIGHT * 0.2)], 0.5),
                  (2, [FadeIn(q)], 0.4)])
        self.wait(2.2)
        ans = VGroup(VGroup(T("only", 26, GREY_B), M("validate", 26)).arrange(RIGHT, buff=0.2),
                     M("Err(error=Invalid(why=amount<=0))", 26, ERR_C)).arrange(DOWN, buff=0.3).move_to([0, -1.9, 0])
        self.seq("Only validate. It fails, and the result is an Err with the reason.",
                 [(0, [t3.animate.move_to([-3.0, 0.4, 0])], 0.6),
                  (0, [flash(mini[0][0], ERR_C), mini[1].animate.set_opacity(0.35), mini[2].animate.set_opacity(0.35),
                       FadeIn(ans[0])], 0.6),
                  (1, [FadeIn(ans[1], shift=UP * 0.1)], 0.6)])
        self.wait(1.0)
