from fg import *
import fg

# Spoken forms for this file (fg.py is shared and stays untouched). The captions keep the written forms.
fg.SAY[:0] = [
    (r"@DslMarker\b", "D S L marker"), (r"@PaymentDsl\b", "payment D S L"),
    (r"\bthis@paymentRequest\.currency\b", "this at payment request, dot currency"),
    (r"\bEUR\b", "E U R"), (r"\bGBP\b", "G B P"),
]

# ---- helpers for this file ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads another spelling than the caption), captions split only where
    a new sentence starts, seq() to start animations at a given sentence, and ask() for a predict-and-pause."""

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
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def ask(self, text, *anims, pause=2.0, say=None):
        """Ask the viewer to predict, then hold a beat of silence."""
        self.beat(text, *anims, after=0, say=say, run_time=0.8 if anims else None)
        self.wait(pause)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def dimc(color, k=0.10):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip_m(text, color, size=24, h=0.52, fill=0.2):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=fill)
    return VGroup(r, t)


def room(x0, x1, y0, y1, color, k=0.07):
    r = RoundedRectangle(corner_radius=0.15, width=x1 - x0, height=y1 - y0, stroke_color=color, stroke_width=3)
    return r.set_fill(dimc(color, k), opacity=1).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])


OUTER, INNER, OK, LEAK, BAD, MARK, HL = BLUE_M, TEAL_M, GREEN_M, GOLD_M, RED_M, PURPLE_M, YELLOW_M


class Kt04Dsl(Beat):
    """kt-04 section 2 (built on sections 0 and 1): a lambda with receiver runs inside its builder; nested
    builders put two receivers in scope; @DslMarker keeps a bare call from reaching the outer one."""

    def construct(self):
        self.title_card("Lambdas with receivers", "and the call that reaches the wrong builder")

        # ---------- the receiver: write on the form you are holding ----------
        form = room(1.0, 6.3, -2.2, 2.2, OUTER)
        fname = M("EntryBuilder", 28, OUTER).move_to([1.35, 1.75, 0], aligned_edge=LEFT)
        rows_src = [("debit", "merchant:981", "12,000"), ("credit", "bank:clearing", "11,850"), ("credit", "revenue:fees", "150")]
        lines_ = VGroup(*[Line([1.4, y, 0], [5.95, y, 0], stroke_width=1.5, color=GREY_D) for y in (0.5, -0.5, -1.5)])
        rows = VGroup()
        for (k, acct, amt), y in zip(rows_src, (0.75, -0.25, -1.25)):
            r = VGroup(T(k, 26, GREY_B), M(acct, 22), M(amt, 22, OK))
            r[0].move_to([1.4, y, 0], aligned_edge=LEFT)
            r[1].move_to([2.45, y, 0], aligned_edge=LEFT)
            r[2].move_to([5.95, y, 0], aligned_edge=RIGHT)
            rows.add(r)
        self.seq("When you fill in a paper form, you don't write the form's name in every box. You are already holding it.",
                 [(0, [FadeIn(form, scale=1.03), FadeIn(fname), Create(lines_)], 1.0)])

        jl = code(['b -> {',
                   '    b.debit("merchant:981", 12_000);',
                   '    b.credit("bank:clearing", 11_850);',
                   '    b.credit("revenue:fees", 150);',
                   '}'], 22)
        jl.move_to([-3.25, -0.25, 0]).align_to([-6.2, 0, 0], LEFT)
        jtag = T("Java", 26, GREY_B).next_to(jl, UP, buff=0.35).align_to(jl, LEFT)
        bs = [part(jl[i], "b.") for i in (1, 2, 3)]
        part(jl[0], "b").set_color(HL)
        for b in bs:
            b.set_color(HL)
        jarr = [Arrow(jl[i].get_right() + RIGHT * 0.1, [0.95, y, 0], buff=0.05, stroke_width=2.5, color=GREY_B,
                      max_tip_length_to_length_ratio=0.12) for i, y in zip((1, 2, 3), (0.75, -0.25, -1.25))]
        self.seq("A Java builder lambda gets the builder as a parameter, b, and names it on every line.",
                 [(0, [FadeIn(VGroup(jtag, jl), shift=RIGHT * 0.2)], 0.8),
                  (0, [*[Indicate(b, color=HL, scale_factor=1.3) for b in bs]], 0.9),
                  (0, [LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(r, shift=RIGHT * 0.15)) for a, r in zip(jarr, rows)],
                                   lag_ratio=0.4)], 1.6)])

        # Kotlin: the same calls without the prefix, and the builder's box grows around the block
        kl = code(['{',
                   '    debit("merchant:981", 12_000)',
                   '    credit("bank:clearing", 11_850)',
                   '    credit("revenue:fees", 150)',
                   '}'], 22)
        kl.move_to(jl).align_to(jl, LEFT).shift(RIGHT * 0.25)
        ktag = T("Kotlin", 26, GREY_B).move_to(jtag, aligned_edge=LEFT).shift(RIGHT * 0.25)
        rest_j = [VGroup(*[g for g in jl[i] if g not in set(bs[k].submobjects)]) for k, i in enumerate((1, 2, 3))]
        big = room(-6.3, 6.3, -2.2, 2.2, OUTER)
        this_t = M("this", 28, HL).next_to(fname, RIGHT, buff=0.35)
        inside = T("the lambda runs inside the builder", 26, GREY_B).move_to([-3.1, -1.8, 0])
        self.seq("Kotlin can hand the builder to the lambda as its receiver. Inside the braces, the builder is this. "
                 "So the calls need no prefix, as if you were writing a method of the builder itself.",
                 [(0, [FadeOut(VGroup(*jarr))], 0.4),
                  (0, [*[FadeOut(b, shift=UP * 0.3) for b in bs], FadeOut(part(jl[0], "b -> "), shift=UP * 0.3)], 0.6),
                  (0, [Transform(jtag, ktag), *[ReplacementTransform(rest_j[k], kl[i]) for k, i in enumerate((1, 2, 3))],
                       ReplacementTransform(part(jl[0], "{"), kl[0]), ReplacementTransform(jl[4], kl[4])], 1.0),
                  (1, [Transform(form, big), fname.animate.move_to([-5.95, 1.75, 0], aligned_edge=LEFT)], 1.2),
                  (1, [FadeIn(this_t.next_to(fname.copy().move_to([-5.95, 1.75, 0], aligned_edge=LEFT), RIGHT, buff=0.35),
                              shift=DOWN * 0.1)], 0.6),
                  (2, [FadeIn(inside)], 0.6),
                  (2, [*[Indicate(kl[i], color=OUTER, scale_factor=1.04) for i in (1, 2, 3)]], 1.0)])

        # one level down: just a Function1
        self.play(FadeOut(VGroup(form, fname, this_t, inside, kl, lines_, rows, jtag)), run_time=0.6)
        t1 = one("EntryBuilder.() -> Unit", 34)
        part(t1, "EntryBuilder").set_color(OUTER)
        t2 = one("(EntryBuilder) -> Unit", 34)
        part(t2, "EntryBuilder").set_color(OUTER)
        t3 = one("Function1<EntryBuilder, Unit>", 34)
        part(t3, "EntryBuilder").set_color(OUTER)
        VGroup(t1, t2).arrange(RIGHT, buff=1.6).move_to(UP * 1.2)
        eq = T("same thing", 26, GREY_B).move_to((t1.get_right() + t2.get_left()) / 2 + UP * 0.45)
        eqs = M("=", 34, GREY_B).move_to((t1.get_right() + t2.get_left()) / 2)
        t3.move_to(DOWN * 0.9)
        a3 = Arrow(VGroup(t1, t2).get_bottom() + DOWN * 0.1, t3.get_top() + UP * 0.1, buff=0.1, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.15)
        jvm = T("what the JVM runs: the builder is the first argument", 26, GREY_B).next_to(t3, DOWN, buff=0.45)
        self.seq("One level down, nothing magic happens. A lambda with receiver has the same type as a lambda "
                 "that takes the builder as its first argument. Both compile to a Function1. "
                 "Only the compiler treats that first argument as this.",
                 [(0, [FadeIn(t1, shift=UP * 0.15)], 0.7),
                  (1, [FadeIn(eqs), FadeIn(eq), FadeIn(t2, shift=UP * 0.15)], 0.8),
                  (2, [GrowArrow(a3), FadeIn(t3, shift=UP * 0.15), FadeIn(jvm)], 0.9)],
                 say="One level down, nothing magic happens. A lambda with receiver has the same type as a lambda "
                     "that takes the builder as its first argument. Both compile to a Function one. "
                     "Only the compiler treats that first argument as this.")
        self.play(FadeOut(VGroup(t1, t2, t3, eq, eqs, a3, jvm)), run_time=0.6)

        # ---------- nested builders: two receivers in scope ----------
        ob = room(-6.35, 6.35, -2.85, 2.95, OUTER, 0.06)
        oh = M('paymentRequest("PR-1") {', 26, OUTER).move_to([-6.05, 2.55, 0], aligned_edge=LEFT)
        ot = M("this: PaymentRequestBuilder", 22, GREY_B).move_to([6.05, 2.55, 0], aligned_edge=RIGHT)
        ovoc = VGroup(*[chip_m(w, OUTER, 24) for w in ("currency", "payer { }", "payee { }")])
        for c, y in zip(ovoc, (1.15, 0.25, -0.65)):
            c.move_to([5.0, y, 0])
        ib = room(-5.95, 3.4, -2.5, 2.0, INNER, 0.09)
        ih = M("payer {", 26, INNER).move_to([-5.65, 1.62, 0], aligned_edge=LEFT)
        it = M("this: PartyBuilder", 22, GREY_B).move_to([3.15, 1.62, 0], aligned_edge=RIGHT)
        ivoc = VGroup(*[chip_m(w, INNER, 24) for w in ("name", "iban")])
        for c, y in zip(ivoc, (0.75, -0.05)):
            c.move_to([2.45, y, 0])
        self.seq("Builders nest. Inside paymentRequest, the payer block hands you a second builder, a PartyBuilder. "
                 "Now two receivers are in scope, one inside the other.",
                 [(0, [FadeIn(ob), FadeIn(oh), FadeIn(ot)], 0.7),
                  (0, [LaggedStart(*[FadeIn(c, shift=LEFT * 0.1) for c in ovoc], lag_ratio=0.25)], 0.8),
                  (1, [FadeIn(ib, scale=0.97), FadeIn(ih), FadeIn(it)], 0.8),
                  (1, [LaggedStart(*[FadeIn(c, shift=LEFT * 0.1) for c in ivoc], lag_ratio=0.3)], 0.6),
                  (2, [Indicate(ot, color=OUTER, scale_factor=1.05), Indicate(it, color=INNER, scale_factor=1.05)], 1.0)])

        tk1 = one('name = "ACME Ltd"', 26).move_to([-5.55, 0.75, 0], aligned_edge=LEFT)
        a1 = Arrow(tk1.get_right() + RIGHT * 0.1, ivoc[0].get_left(), buff=0.1, stroke_width=3, color=OK,
                   max_tip_length_to_length_ratio=0.08)
        self.seq("A bare call goes to the nearest receiver that has it. Name lands on the party.",
                 [(0, [FadeIn(tk1, shift=RIGHT * 0.15)], 0.6),
                  (1, [GrowArrow(a1), Indicate(ivoc[0], color=OK, scale_factor=1.1)], 0.9)])

        tk2 = one('payee { name = "oops" }', 26).move_to([-5.55, -0.65, 0], aligned_edge=LEFT)
        q = T("PartyBuilder has no payee. What happens?", 30, HL).move_to([-1.25, -1.8, 0])
        self.ask("Now someone types payee inside payer, by mistake. The PartyBuilder has no payee. What does Kotlin do?",
                 FadeIn(tk2, shift=RIGHT * 0.15), FadeIn(q, shift=UP * 0.1), pause=2.0)

        y2 = -0.65
        p2 = [tk2.get_right() + RIGHT * 0.1, [3.75, y2, 0], [ovoc[2].get_left()[0] - 0.05, y2, 0]]
        leak = Arrow(p2[0], p2[2], buff=0, stroke_width=3, color=LEAK, max_tip_length_to_length_ratio=0.05)
        probe = Dot(radius=0.09, color=LEAK).move_to(p2[0])
        miss = T("not here", 22, GREY_B).move_to([2.45, -0.65, 0])
        self.seq("It keeps looking, outward. The outer builder has payee, so the line compiles. "
                 "And it quietly builds a second party.",
                 [(0, [FadeOut(q)], 0.3),
                  (0, [FadeIn(probe), probe.animate.move_to([2.0, y2, 0])], 0.8),
                  (0, [FadeIn(miss), Wiggle(ivoc, scale_value=1.05)], 0.7),
                  (0, [FadeOut(miss), probe.animate.move_to(p2[2]), Create(leak)], 1.0),
                  (1, [FadeOut(probe), Indicate(ovoc[2], color=LEAK, scale_factor=1.15)], 0.8)])

        slot_y = -1.45
        crash = T("at run time: iban required for 'oops'", 26, BAD).move_to([-5.55, slot_y, 0], aligned_edge=LEFT)
        self.seq("In the lesson's demo it fails only when it runs: iban required for oops. "
                 "Without a required field, you would simply send the wrong request.",
                 [(0, [FadeIn(crash, shift=UP * 0.1)], 0.7)])

        # ---------- @DslMarker ----------
        st_o = chip_m("@PaymentDsl", MARK, 22, h=0.46, fill=0.3).next_to(oh, RIGHT, buff=0.3)
        st_i = chip_m("@PaymentDsl", MARK, 22, h=0.46, fill=0.3).next_to(ih, RIGHT, buff=0.3)
        self.seq("The fix is one annotation. Mark an annotation class with @DslMarker, "
                 "and put it on every builder class: the receivers themselves.",
                 [(0, [FadeOut(crash), FadeOut(leak)], 0.5),
                  (1, [FadeIn(st_o, scale=1.4)], 0.6),
                  (1, [FadeIn(st_i, scale=1.4)], 0.6),
                  (1, [ib.animate.set_stroke(MARK, width=7)], 0.8)])

        stopx = 3.4
        probe2 = Dot(radius=0.09, color=LEAK).move_to(p2[0])
        ray = Line(p2[0], [stopx - 0.08, y2, 0], stroke_width=3, color=BAD)
        cross = tick(False, 0.2).move_to([stopx, y2, 0])
        err = T("compile error: payee needs an explicit receiver", 24, BAD).move_to([-5.55, slot_y, 0], aligned_edge=LEFT)
        self.seq("Now only the nearest marked receiver is implicit. The misplaced payee stops at the inner wall. "
                 "It no longer compiles.",
                 [(0, [Indicate(st_i, color=MARK, scale_factor=1.15)], 0.8),
                  (1, [FadeIn(probe2), probe2.animate.move_to([stopx - 0.1, y2, 0]), Create(ray)], 1.2),
                  (1, [FadeOut(probe2), FadeIn(cross, scale=1.5), Flash([stopx, y2, 0], color=BAD, line_length=0.3)], 0.6),
                  (2, [FadeIn(err, shift=UP * 0.1), tk2.animate.set_color(BAD)], 0.7)])

        tk3 = one('this@paymentRequest.currency = "EUR"', 26).move_to([-5.55, -2.05, 0], aligned_edge=LEFT)
        part(tk3, "this@paymentRequest").set_color(OUTER)
        y3 = -2.05
        p3 = [tk3.get_right() + RIGHT * 0.1, [3.75, y3, 0], [3.75, ovoc[0].get_y(), 0], ovoc[0].get_left() + LEFT * 0.05]
        path3 = VMobject(stroke_color=OK, stroke_width=3).set_points_as_corners([np.array(p, dtype=float) for p in p3[:-1]])
        tip3 = Arrow(p3[2], p3[3], buff=0, stroke_width=3, color=OK, max_tip_length_to_length_ratio=0.5)
        self.seq("You can still reach the outer builder on purpose, with a label: this@paymentRequest.currency. "
                 "Nobody types that by accident.",
                 [(0, [FadeIn(tk3, shift=RIGHT * 0.15)], 0.7),
                  (0, [Create(path3)], 1.0),
                  (0, [GrowArrow(tip3), Indicate(ovoc[0], color=OK, scale_factor=1.12)], 0.6)])
        self.play(FadeOut(VGroup(ob, oh, ot, ovoc, ib, ih, it, ivoc, tk1, a1, tk2, ray, cross, err, tk3, path3, tip3,
                                 st_o, st_i)), run_time=0.7)

        # ---------- the code: Kotlin and Java ----------
        kc = code(["@DslMarker annotation class PaymentDsl",
                   "@PaymentDsl class PaymentRequestBuilder(...) { ... }",
                   "@PaymentDsl class PartyBuilder { ... }"], 24)
        for ln in kc:
            part(ln, "@PaymentDsl" if ln.src.startswith("@P") else "@DslMarker").set_color(MARK)
        part(kc[0], "PaymentDsl").set_color(MARK)
        part(kc[1], "PaymentRequestBuilder").set_color(OUTER)
        part(kc[2], "PartyBuilder").set_color(INNER)
        jc = code(['paymentRequest("PR-1", r -> {',
                   "    r.payer(p -> {",
                   '        r.setCurrency("EUR");   // outer builder, by name',
                   "        return Unit.INSTANCE;",
                   "    });",
                   "    return Unit.INSTANCE;",
                   "});"], 24)
        part(jc[2], "r.").set_color(OUTER)
        part(jc[0], "r").set_color(OUTER)
        VGroup(jc[1][jc[1].src.index("(p") + 1]).set_color(INNER)
        kh, jh = T("Kotlin", 26, GREY_B), T("Java", 26, GREY_B)
        jc.next_to(kc, DOWN, buff=0.75).align_to(kc, LEFT)
        kh.next_to(kc[0], LEFT, buff=0.6)
        jh.next_to(jc[0], LEFT, buff=0.6).align_to(kh, LEFT)
        allc = VGroup(kc, jc, kh, jh)
        allc.scale(min(1, 12.4 / allc.width)).move_to(UP * 0.1)
        self.seq("In Kotlin that is the whole fix: one marker annotation, placed on each builder class. "
                 "Java needs none of it. Its lambdas name every builder, so reaching the outer one means typing r on purpose.",
                 [(0, [FadeIn(VGroup(kh, kc), shift=UP * 0.15)], 0.9),
                  (0, [Indicate(part(kc[1], "@PaymentDsl"), color=MARK), Indicate(part(kc[2], "@PaymentDsl"), color=MARK)], 1.0),
                  (1, [FadeIn(VGroup(jh, jc), shift=UP * 0.15)], 0.9),
                  (2, [Indicate(part(jc[2], "r."), color=OUTER, scale_factor=1.5)], 1.0)])
        self.play(FadeOut(allc), run_time=0.6)

        # ---------- the rule and a check ----------
        r1 = T("A bare call goes to the nearest receiver that has it.", 34).move_to(UP * 2.6)
        r2 = T("@DslMarker on the builder classes stops it there.", 34, MARK).next_to(r1, DOWN, buff=0.3)
        rule = VGroup(r1, r2)
        rule.scale(min(1, 12.4 / rule.width))
        self.beat("The rule: a bare call goes to the nearest receiver that has it, "
                  "and @DslMarker on the builder classes stops it there.",
                  FadeIn(r1, shift=UP * 0.15), FadeIn(r2, shift=UP * 0.15), run_time=1.4)
        mo = room(-3.6, 3.6, -2.35, 0.95, OUTER, 0.06)
        mi = room(-3.3, 1.6, -2.1, 0.3, INNER, 0.09).set_stroke(MARK, width=6)
        mol = M("paymentRequest {", 22, OUTER).move_to([-3.35, 0.62, 0], aligned_edge=LEFT)
        mil = M("payer {", 22, INNER).move_to([-3.05, 0.0, 0], aligned_edge=LEFT)
        mtk = one('currency = "GBP"', 26).move_to([-3.05, -0.95, 0], aligned_edge=LEFT)
        mvoc = chip_m("currency", OUTER, 22).move_to([2.6, -0.95, 0])
        cq = T("With the marker on, does it compile?", 30, GREY_A).move_to([0, -3.0, 0])
        self.beat("A quick check. Inside payer, someone writes currency equals GBP, with no label. "
                  "With the marker on, does it compile?",
                  FadeIn(VGroup(mo, mi, mol, mil, mvoc)), FadeIn(mtk, shift=RIGHT * 0.15), FadeIn(cq, shift=UP * 0.1),
                  run_time=1.2)
        self.wait(2.5)
