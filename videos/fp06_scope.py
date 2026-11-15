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


def part(t, src, sub, nth=0):
    """The glyphs of substring sub in a Text built from src (spaces are not glyphs)."""
    i = -1
    for _ in range(nth + 1):
        i = src.index(sub, i + 1)
    a = len(src[:i].replace(" ", ""))
    return t[a:a + len(sub.replace(" ", ""))]


def card(title, rows, color=BLUE_M, w=None, tsize=24, rsize=22, rcolor=WHITE):
    t = M(title, tsize, color)
    rs = VGroup(*[M(x, rsize, rcolor) for x in rows])
    body = VGroup(t, *rs).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.14, width=w or body.width + 0.6, height=body.height + 0.45,
                         stroke_color=color, stroke_width=3).set_fill(fill_of(color), opacity=1)
    body.move_to(r)
    return VGroup(r, body)


def cbox(lines, size=24, color=WHITE, t2c=None, pad=0.45, w=None, pitch=1.45):
    """A block of code drawn as a box."""
    c = code(lines, size, t2c=t2c, pitch=pitch)
    r = RoundedRectangle(corner_radius=0.16, width=w or c.width + pad, height=c.height + pad * 0.9,
                         stroke_color=color, stroke_width=3).set_fill(BLACK, opacity=1)
    c.move_to(r)
    return VGroup(r, c)


def gate(sym, color=GREY_B):
    c = Circle(radius=0.36, stroke_color=color, stroke_width=3).set_fill(BLACK, opacity=1)
    return VGroup(c, M(sym, 28).move_to(c))


def flash(r, color=YELLOW_M):
    return ShowPassingFlash(r.copy().set_fill(opacity=0).set_stroke(color, 7), time_width=0.6)


def dot_run(a, b, color, run_time):
    d = Dot(radius=0.09, color=color).move_to(a).set_z_index(30)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=run_time, rate_func=smooth).move_to(b),
                      FadeOut(d, run_time=0.12))


# grid geometry, the same every time it is on screen
COLX = [0.25, 4.4]
ROWY = [1.55, -0.05]
HEADY = 2.9
CW, CH = 4.0, 1.35
ROWX = -4.45
COLC = [YELLOW_M, BLUE_M]           # result column, object column
ROWC = [TEAL_M, PURPLE_M]           # this row, it row
NAMES = {(0, 0): "run, with", (1, 0): "apply", (0, 1): "let", (1, 1): "also"}
JOBS = {(0, 0): "compute from members", (1, 0): "configure an object",
        (0, 1): "transform, null check", (1, 1): "side effect, keep the value"}
STRIP_Y = -2.3


def row_label(r):
    head = T("object is this" if r == 0 else "object is it", 28, ROWC[r])
    sub = VGroup(T("you write", 22, GREY_B), M("amountMinor" if r == 0 else "it.amountMinor", 22, GREY_B)
                 ).arrange(RIGHT, buff=0.12)
    return VGroup(head, sub).arrange(DOWN, buff=0.14).move_to([ROWX, ROWY[r], 0])


def make_grid():
    heads = VGroup(T("returns the block's result", 24, COLC[0]).move_to([COLX[0], HEADY, 0]),
                   T("returns the object itself", 24, COLC[1]).move_to([COLX[1], HEADY, 0]))
    rows = VGroup(row_label(0), row_label(1))
    cells, names, jobs = {}, {}, {}
    for (c, r), n in NAMES.items():
        rect = RoundedRectangle(corner_radius=0.16, width=CW, height=CH, stroke_color=COLC[c], stroke_width=3)
        rect.set_fill(fill_of(COLC[c], 0.12), opacity=1).move_to([COLX[c], ROWY[r], 0])
        cells[(c, r)] = rect
        names[(c, r)] = M(n, 32).move_to(rect)
        jobs[(c, r)] = T(JOBS[(c, r)], 22, GREY_B).move_to(rect.get_center() + DOWN * 0.33)
    return heads, rows, cells, names, jobs


class Fp06Scope(Beat):
    """fp-06 section 1: two questions pick the scope function (this or it, the object or the block's result),
    each cell's typical job, and the ?.let { } ?: run { } trap from section 2."""

    def construct(self):
        self.title_card("Scope functions", "two questions pick one of five")

        # ---------------- the model: an object, a block, one of two things back ----------------
        charge = card("Charge", ["id = ch_1", "amountMinor = 1999", "currency = EUR"]).move_to([-4.75, 0.5, 0])
        blk = RoundedRectangle(corner_radius=0.18, width=4.0, height=2.5, stroke_color=WHITE, stroke_width=3)
        blk.set_fill(BLACK, opacity=1).move_to([0.0, 0.5, 0])
        blk_lab = T("a block of code", 24, GREY_B).next_to(blk, UP, buff=0.18)
        blk_code = M("amountMinor * 2", 28).move_to(blk.get_center() + DOWN * 0.5)
        inner = chip("charge", BLUE_M, size=26, mono=True).move_to(blk.get_center() + UP * 0.5)

        self.seq("Here is a charge of 1999 cents. You hand it to a small block of code that doubles the amount.",
                 [(0, [FadeIn(charge, shift=RIGHT * 0.2)], 0.8),
                  (1, [FadeIn(VGroup(blk, blk_lab, blk_code))], 0.7),
                  (1, [ReplacementTransform(charge.copy(), inner), charge.animate.set_opacity(0.3)], 1.0)],
                 say="Here is a charge of one thousand nine hundred ninety-nine cents. "
                     "You hand it to a small block of code that doubles the amount.")

        res = chip("3998", YELLOW_M, size=32, mono=True).move_to([4.7, 2.0, 0])
        res_lab = T("the block's result", 26, YELLOW_M).next_to(res, UP, buff=0.2)
        obj = card("Charge", ["id = ch_1", "amountMinor = 1999", "currency = EUR"]).move_to([4.7, -1.0, 0])
        obj_lab = T("the charge you handed in", 26, BLUE_M).next_to(obj, DOWN, buff=0.2)
        a_res = Arrow(blk.get_right() + UP * 0.45, res.get_left(), buff=0.15, stroke_width=3, color=YELLOW_M,
                      max_tip_length_to_length_ratio=0.12)
        a_obj = Arrow(blk.get_right() + DOWN * 0.45, obj.get_left(), buff=0.15, stroke_width=3, color=BLUE_M,
                      max_tip_length_to_length_ratio=0.12)
        res_src = M("3998", 32, YELLOW_M).move_to(blk_code)
        self.seq("When the block is done, the call gives back one of two things. The block's result, 3998. "
                 "Or the charge you handed in.",
                 [(0, [GrowArrow(a_res), GrowArrow(a_obj)], 0.8),
                  (1, [Indicate(blk_code, color=YELLOW_M, scale_factor=1.1)], 0.6),
                  (1, [ReplacementTransform(res_src, res), FadeIn(res_lab)], 0.8),
                  (2, [ReplacementTransform(inner, obj), FadeIn(obj_lab)], 1.0)],
                 say="When the block is done, the call gives back one of two things. "
                     "The block's result, three thousand nine hundred ninety-eight. Or the charge you handed in.")

        # ---- this or it
        L = card("Charge", [], w=6.2)
        L[0].stretch_to_fit_height(2.5)
        L.move_to([-3.35, 0.25, 0])
        L[1].move_to(L[0].get_corner(UL) + np.array([0.75, -0.35, 0]))
        fields = VGroup(*[M(f, 22, TEAL_M if f == "amountMinor" else GREY_B) for f in ("id", "amountMinor", "currency")]
                        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(L[0].get_center() + np.array([-2.05, -0.25, 0]))
        lb = cbox(["amountMinor * 2"], 26, t2c={"amountMinor": TEAL_M}).move_to(L[0].get_center() + np.array([1.25, -0.25, 0]))
        L_head = T("as this", 32, TEAL_M).next_to(L, UP, buff=0.25)
        L_sub = T("the block runs inside the charge", 24, GREY_B).next_to(L, DOWN, buff=0.25)

        rb = cbox(["it.amountMinor * 2"], 26, t2c={"it.": PURPLE_M}).move_to([4.4, 0.25, 0])
        rchip = chip("charge", BLUE_M, size=26, mono=True).move_to([0.75, 0.25, 0])
        rtag = M("it", 28, PURPLE_M).next_to(rchip, UP, buff=0.2)
        rarr = Arrow(rchip.get_right(), rb.get_left(), buff=0.1, stroke_width=3, color=PURPLE_M,
                     max_tip_length_to_length_ratio=0.25)
        R_head = T("as it", 32, PURPLE_M).move_to([3.4, L_head.get_y(), 0])
        R_sub = T("the charge comes in as a parameter", 24, GREY_B).move_to([3.4, L_sub.get_y(), 0])

        self.play(FadeOut(VGroup(a_res, a_obj, res, res_lab, obj, obj_lab, charge, blk_lab)),
                  FadeOut(VGroup(blk, blk_code)), run_time=0.6)
        self.seq("Inside the block, the charge shows up in one of two ways. "
                 "As this, the block runs inside the charge, so you write amountMinor. "
                 "As it, the charge comes in as a parameter, so you write it.amountMinor.",
                 [(1, [FadeIn(L_head), FadeIn(L[0]), FadeIn(L[1])], 0.7),
                  (1, [FadeIn(fields), FadeIn(lb, scale=0.9)], 0.8),
                  (1, [Indicate(fields[1], color=TEAL_M), Indicate(lb[1][0][0:11], color=TEAL_M)], 1.0),
                  (2, [FadeIn(R_head), FadeIn(rchip), FadeIn(rtag), FadeIn(rb, scale=0.9)], 0.8),
                  (2, [GrowArrow(rarr), FadeIn(R_sub), FadeIn(L_sub)], 0.7),
                  (2, [Indicate(rb[1][0][0:2], color=PURPLE_M, scale_factor=1.3), Indicate(rtag, color=PURPLE_M)], 1.0)],
                 say="Inside the block, the charge shows up in one of two ways. "
                     "As this, the block runs inside the charge, so you write amount minor. "
                     "As it, the charge comes in as a parameter, so you write it dot amount minor.")

        # ---- the grid
        heads, rows, cells, names, jobs = make_grid()
        order = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.seq("Two questions, two answers each. That makes four cells, and Kotlin's five scope functions fill them.",
                 [(0, [ReplacementTransform(L_head, rows[0][0]), ReplacementTransform(R_head, rows[1][0]),
                       FadeOut(VGroup(L, fields, lb, L_sub, rb, rchip, rtag, rarr, R_sub))], 1.0),
                  (0, [FadeIn(rows[0][1]), FadeIn(rows[1][1]),
                       FadeIn(heads[0], shift=DOWN * 0.15), FadeIn(heads[1], shift=DOWN * 0.15)], 0.7),
                  (1, [LaggedStart(*[FadeIn(cells[k]) for k in order], lag_ratio=0.2)], 0.9),
                  (1, [LaggedStart(*[Write(names[k]) for k in order], lag_ratio=0.3)], 1.4)])

        # ---------------- predict: the same block, five ways ----------------
        lines = ["charge.let { it.amountMinor * 2 }", "charge.run { amountMinor * 2 }",
                 "with(charge) { amountMinor * 2 }", "charge.also { it.amountMinor * 2 }",
                 "charge.apply { amountMinor * 2 }"]
        cell_of = [(0, 1), (0, 0), (0, 0), (1, 1), (1, 0)]
        five = code(lines, 24, pitch=1.35).move_to([0, -2.32, 0]).align_to([-6.3, 0, 0], LEFT)
        qs = VGroup(*[VGroup(M("->", 24, GREY_B), M("?", 24, GREY_B)).arrange(RIGHT, buff=0.25)
                      .move_to([0.0, ln.get_y(), 0], aligned_edge=LEFT) for ln in five])
        ans = VGroup()
        for ln, k in zip(five, cell_of):
            txt = "3998" if k[0] == 0 else "Charge(id=ch_1, ...)"
            ans.add(M(txt, 24, COLC[k[0]]).move_to([0.6, ln.get_y(), 0], aligned_edge=LEFT))
        note = VGroup(T("Kotlin only:", 22, GREY_B), T("Java has no", 22, GREY_B), T("scope functions", 22, GREY_B)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([5.35, -2.32, 0])
        self.seq("Same block, five functions. What does each one give back?",
                 [(0, [LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in five], lag_ratio=0.15)], 1.2),
                  (1, [FadeIn(qs)], 0.5)])
        self.wait(2.2)

        hl = {k: SurroundingRectangle(cells[k], buff=0.06, color=WHITE, stroke_width=5, corner_radius=0.2) for k in cells}
        self.seq("let, run and with give back 3998. also and apply give back the charge. Java has no scope functions.",
                 [(0, [*[Transform(qs[i][1], ans[i]) for i in (0, 1, 2)], *[flash(cells[cell_of[i]], YELLOW_M) for i in (0, 1)]], 1.0),
                  (1, [*[Transform(qs[i][1], ans[i]) for i in (3, 4)], *[flash(cells[k], BLUE_M) for k in ((1, 1), (1, 0))]], 1.0),
                  (2, [FadeIn(note, shift=LEFT * 0.1)], 0.6)],
                 say="let, run and with give back three thousand nine hundred ninety-eight. "
                     "also and apply give back the charge. Java has no scope functions.")
        self.play(FadeOut(VGroup(five, qs, note)), run_time=0.5)

        # ---------------- each cell's typical job ----------------
        IN_X, OUT_X = -5.15, 4.85

        def req(filled):
            rows_ = ["amount   1999", "merchant m-42"] if filled else ["amount   ?", "merchant ?"]
            return card("PaymentRequest", rows_, w=2.6, tsize=22, rsize=22, rcolor=WHITE if filled else GREY_B)

        def focus(k):
            names[k].generate_target()
            names[k].target.move_to(cells[k].get_center() + UP * 0.22)
            return [MoveToTarget(names[k]), FadeIn(jobs[k], shift=UP * 0.1)]

        hl_now = hl[(1, 0)].copy()
        # apply: configure an object
        blank = req(False).move_to([IN_X, STRIP_Y, 0]).set_z_index(1)
        ab = cbox(["apply {", '    amount = Money(1_999, "EUR")', '    merchantId = "m-42"', "}"], 22,
                  t2c={"apply": BLUE_M}).move_to([-0.3, STRIP_Y, 0]).set_z_index(2)
        filled = req(True).move_to(ab).set_z_index(1)
        self.seq("Each cell has a typical job. apply configures an object, and hands the same object back.",
                 [(0, [Create(hl_now), *focus((1, 0))], 0.8),
                  (1, [FadeIn(blank, shift=RIGHT * 0.2), FadeIn(ab)], 0.7),
                  (1, [blank.animate.move_to(ab)], 0.8),
                  (1, [filled.animate.move_to([OUT_X, STRIP_Y, 0])], 0.9)])
        self.remove(blank)

        # also: a side step, the object flows on
        a_in = req(True).move_to([IN_X, STRIP_Y, 0]).set_z_index(1)
        alb = cbox(['also { log.info("sending {}", it) }'], 22, t2c={"also": BLUE_M}).move_to([-0.3, STRIP_Y + 0.35, 0]).set_z_index(2)
        a_out = a_in.copy()
        logl = VGroup(T("log:", 22, GREY_B), M("sending PaymentRequest", 22, GREY_B)).arrange(RIGHT, buff=0.2)
        logl.move_to([-0.3, STRIP_Y - 0.6, 0])
        self.seq("also does a side step, like a log line, and the object flows on unchanged.",
                 [(0, [hl_now.animate.become(hl[(1, 1)]), *focus((1, 1)), FadeOut(VGroup(filled, ab))], 0.7),
                  (0, [FadeIn(a_in), FadeIn(alb)], 0.6),
                  (0, [a_in.animate.move_to(alb)], 0.7),
                  (0, [a_in.animate.move_to([OUT_X, STRIP_Y, 0]), FadeIn(logl, shift=DOWN * 0.15)], 0.8)])

        # let: only when the value is not null
        tok = chip("tok_4242", BLUE_M, size=24, mono=True).move_to([IN_X, STRIP_Y + 0.4, 0])
        nul = chip("null", RED_M, size=24, mono=True).move_to([IN_X, STRIP_Y - 0.55, 0])
        tok_lab = T("card.token", 22, GREY_B).next_to(tok, UP, buff=0.15)
        g = gate("?.").move_to([-3.45, STRIP_Y + 0.4, 0])
        lb2 = cbox(["let { vault.lookup(it) }"], 22, t2c={"let": YELLOW_M}).move_to([-0.3, STRIP_Y + 0.4, 0]).set_z_index(2)
        lres = chip("lookup result", YELLOW_M, size=22).move_to([OUT_X, STRIP_Y + 0.4, 0])
        nres = chip("null", RED_M, size=24, mono=True).move_to([OUT_X, STRIP_Y - 0.55, 0])
        tok_go = tok.copy().set_z_index(1)
        self.seq("let, after a safe call, runs only when the value is not null. A missing token skips the block.",
                 [(0, [hl_now.animate.become(hl[(0, 1)]), *focus((0, 1)), FadeOut(VGroup(a_in, alb, logl))], 0.7),
                  (0, [FadeIn(tok), FadeIn(tok_lab), FadeIn(g), FadeIn(lb2)], 0.6),
                  (0, [tok_go.animate.move_to(g)], 0.5),
                  (0, [flash(g[0], GREEN_M), tok_go.animate.move_to(lb2)], 0.6),
                  (0, [ReplacementTransform(tok_go, lres)], 0.7),
                  (1, [FadeIn(nul)], 0.4),
                  (1, [nul.animate.move_to([-3.45, STRIP_Y - 0.55, 0])], 0.5),
                  (1, [flash(g[0], RED_M), nul.animate.move_to(nres)], 0.9)])

        # run and with: compute something new
        r_in = chip("request", BLUE_M, size=24, mono=True).move_to([IN_X - 0.2, STRIP_Y, 0]).set_z_index(1)
        rbx = cbox(["run {", "  riskModel.score(amount, merchantId)", "}"], 22, t2c={"run": YELLOW_M}
                   ).move_to([-0.2, STRIP_Y, 0]).set_z_index(2)
        rres = chip("risk score", YELLOW_M, size=24).move_to([OUT_X + 0.1, STRIP_Y, 0])
        self.seq("run and with compute something new from the object's members, like a risk score.",
                 [(0, [hl_now.animate.become(hl[(0, 0)]), *focus((0, 0)), FadeOut(VGroup(tok, tok_lab, g, lb2, lres, nul))], 0.7),
                  (0, [FadeIn(r_in), FadeIn(rbx)], 0.6),
                  (0, [r_in.animate.move_to(rbx)], 0.7),
                  (0, [ReplacementTransform(r_in, rres)], 0.8)])
        grid = VGroup(heads, rows, *cells.values(), *names.values(), *jobs.values())
        self.play(FadeOut(VGroup(rbx, rres, hl_now, grid)), run_time=0.7)

        # ---------------- the trap: ?.let { } ?: run { } ----------------
        TY = 2.2
        p1 = chip("p1", BLUE_M, size=26, mono=True).move_to([-5.75, TY, 0])
        cached_lab = T("cached", 24, GREY_B).next_to(p1, UP, buff=0.22)
        g1 = gate("?.").move_to([-4.55, TY, 0])
        let_box = cbox(["let { ledger.post(it) }"], 24, t2c={"let": YELLOW_M}).move_to([-1.8, TY, 0])
        g2 = gate("?:").move_to([0.95, TY, 0])
        g2_lab = T("Elvis", 22, GREY_B).next_to(g2, UP, buff=0.12)
        res_r = DashedVMobject(RoundedRectangle(corner_radius=0.14, width=2.2, height=0.9, stroke_width=2.5,
                                                stroke_color=GREY_B), num_dashes=40).move_to([5.25, TY, 0])
        res_lab2 = T("result", 24, GREY_B).next_to(res_r, UP, buff=0.12)
        run_box = cbox(["run { ledger.post(fetch()) }"], 24, t2c={"run": YELLOW_M}).move_to([3.4, 0.45, 0])
        a12 = Line(g1.get_right(), let_box.get_left(), stroke_width=3, color=GREY_B)
        a0 = Line(p1.get_right(), g1.get_left(), stroke_width=3, color=GREY_B)
        a23 = Line(let_box.get_right(), g2.get_left(), stroke_width=3, color=GREY_B)
        a_ok = Arrow(g2.get_right(), res_r.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.05)
        ok_lab = T("if not null", 22, GREY_B).next_to(a_ok, UP, buff=0.1)
        a_null = Arrow(g2.get_bottom(), [g2.get_x(), run_box.get_top()[1], 0], buff=0.05, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.15)
        null_lab = T("if null", 22, GREY_B).next_to(a_null, LEFT, buff=0.6)
        a_run = Arrow(run_box.get_top() + RIGHT * 1.85, [res_r.get_x(), res_r.get_bottom()[1], 0], buff=0.05, stroke_width=3,
                      color=GREY_B, max_tip_length_to_length_ratio=0.15)
        ledger = RoundedRectangle(corner_radius=0.16, width=3.8, height=1.45, stroke_color=WHITE, stroke_width=3)
        ledger.set_fill(BLACK, opacity=1).move_to([-1.8, -1.85, 0])
        ledger_t = T("ledger", 24).move_to(ledger.get_top() + DOWN * 0.3)
        db = RoundedRectangle(corner_radius=0.16, width=2.8, height=1.0, stroke_color=GREY_B, stroke_width=3)
        db.set_fill(BLACK, opacity=1).move_to([4.0, -1.85, 0])
        db_t = T("database", 24, GREY_B).move_to(db)
        l_led = DashedLine(let_box.get_bottom(), ledger.get_top(), dash_length=0.08, stroke_width=1.5, color=GREY_D)
        l_db = DashedLine([4.0, run_box.get_bottom()[1], 0], db.get_top(), dash_length=0.08, stroke_width=1.5, color=GREY_D)
        l_rl = DashedLine([1.6, run_box.get_bottom()[1], 0], ledger.get_corner(UR) + LEFT * 0.3, dash_length=0.08,
                          stroke_width=1.5, color=GREY_D)
        console_lab = T("console", 22, GREY_B).move_to([-6.3, -3.2, 0], aligned_edge=LEFT)
        diagram = VGroup(p1, cached_lab, g1, let_box, g2, g2_lab, res_r, res_lab2, run_box, a0, a12, a23, a_ok, ok_lab,
                         a_null, null_lab, a_run, ledger, ledger_t, db, db_t, l_led, l_db, l_rl, console_lab)

        self.seq("Now the trap. It reads like if, else: post the cached payment, or fetch one and post it.",
                 [(0, [FadeIn(VGroup(p1, cached_lab, a0, g1, a12, let_box, a23, g2, g2_lab, a_ok, ok_lab, res_r, res_lab2))], 0.9),
                  (0, [GrowArrow(a_null), FadeIn(null_lab), FadeIn(run_box), GrowArrow(a_run)], 0.7),
                  (1, [FadeIn(VGroup(ledger, ledger_t, db, db_t, l_led, l_db, l_rl, console_lab))], 0.6),
                  (1, [flash(let_box[0], YELLOW_M)], 0.8),
                  (1, [flash(run_box[0], YELLOW_M)], 0.8)])

        def go(m, target, rt=0.5):
            return m.animate(run_time=rt).move_to(target)

        led_p1 = chip("p1", BLUE_M, size=24, mono=True).move_to(ledger.get_center() + DOWN * 0.25)
        le = chip("LE-p1", YELLOW_M, size=24, mono=True).move_to(ledger.get_top() + DOWN * 0.05)
        c1 = p1.copy()
        self.seq("First call: the ledger is empty, post returns an entry id, and run is skipped.",
                 [(0, [go(c1, g1)], 0.5),
                  (0, [flash(g1[0], GREEN_M), go(c1, let_box)], 0.6),
                  (0, [FadeOut(c1, run_time=0.2), dot_run(let_box.get_bottom(), ledger.get_top(), BLUE_M, 0.7)], 0.8),
                  (0, [FadeIn(led_p1, scale=1.3)], 0.4),
                  (0, [FadeIn(le)], 0.3),
                  (0, [go(le, let_box, 0.7)], 0.7),
                  (0, [go(le, g2, 0.5)], 0.5),
                  (0, [flash(g2[0], GREEN_M), go(le, res_r, 0.7)], 0.7)])

        self.play(FadeOut(le), run_time=0.4)
        self.seq("Second call. The payment is still cached, but the ledger has posted it already. Which blocks run?",
                 [(0, [Indicate(p1, color=BLUE_M)], 0.8),
                  (1, [Indicate(led_p1, color=BLUE_M)], 0.8)])
        self.wait(2.2)

        c2 = p1.copy()
        nul1 = chip("null", RED_M, size=24, mono=True).move_to(ledger.get_top() + DOWN * 0.05)
        cons = M("cache miss, fetching from the database", 22).next_to(console_lab, RIGHT, buff=0.3)
        fetched = chip("p1", BLUE_M, size=24, mono=True).move_to(db)
        nul2 = chip("null", RED_M, size=24, mono=True).move_to(ledger.get_corner(UR) + LEFT * 0.3)
        self.play(go(c2, g1, 0.4), run_time=0.4)
        self.play(flash(g1[0], GREEN_M), go(c2, let_box, 0.5), run_time=0.5)
        self.play(FadeOut(c2, run_time=0.2), dot_run(let_box.get_bottom(), ledger.get_top(), BLUE_M, 0.6), run_time=0.7)
        self.seq("post returns null for a duplicate. The Elvis operator tests the value on its left. "
                 "That is the result of the let block, not the cached payment. It is null, so run runs too. "
                 "A cache miss, a fetch from the database, and a second post.",
                 [(0, [Indicate(led_p1, color=RED_M), FadeIn(nul1)], 0.6),
                  (0, [go(nul1, let_box, 0.6)], 0.6),
                  (1, [go(nul1, g2, 0.5)], 0.5),
                  (2, [flash(let_box[0], RED_M), Indicate(p1, color=WHITE, scale_factor=1.1)], 1.0),
                  (3, [flash(g2[0], RED_M), go(nul1, a_null.get_center(), 0.6)], 0.6),
                  (3, [FadeOut(nul1, run_time=0.2), run_box[0].animate.set_stroke(RED_M)], 0.4),
                  (4, [FadeIn(cons, shift=RIGHT * 0.1)], 0.5),
                  (4, [dot_run(l_db.get_start(), db.get_top(), YELLOW_M, 0.5)], 0.5),
                  (4, [FadeIn(fetched), go(fetched, run_box.get_center() + RIGHT * 0.6, 0.6)], 0.6),
                  (4, [FadeOut(fetched, run_time=0.2), dot_run(l_rl.get_start(), l_rl.get_end(), BLUE_M, 0.6)], 0.7),
                  (4, [Indicate(led_p1, color=RED_M), FadeIn(nul2)], 0.6),
                  (4, [go(nul2, res_r, 0.8)], 0.8)])
        both = VGroup(SurroundingRectangle(let_box, buff=0.1, color=RED_M, stroke_width=5, corner_radius=0.2),
                      SurroundingRectangle(run_box, buff=0.1, color=RED_M, stroke_width=5, corner_radius=0.2))
        self.beat("Both blocks ran.", Create(both), run_time=0.8)
        self.play(FadeOut(VGroup(diagram, both, led_p1, nul2, cons)), run_time=0.7)

        # ---- the same trap in Java, and the fix
        def pair(title, color, kt, jv, y):
            hd = T(title, 28, color)
            kc = code(kt, 24, t2c={"?:": color})
            jc = code(jv, 24)
            kh, jh = T("Kotlin", 24, GREY_B), T("Java", 24, GREY_B)
            jc.next_to(kc, DOWN, buff=0.4).align_to(kc, LEFT)
            kh.next_to(kc[0], LEFT, buff=0.5)
            jh.next_to(jc[0], LEFT, buff=0.5).align_to(kh, LEFT)
            body = VGroup(kh, kc, jh, jc)
            hd.next_to(body, UP, buff=0.3).align_to(kh, LEFT)
            g_ = VGroup(hd, body).move_to([0, y, 0])
            return g_.align_to([-6.2, 0, 0], LEFT)

        trap = pair("the trap: both blocks can run", RED_M,
                    ["cached?.let { ledger.post(it) }", "    ?: run { ledger.post(fetch()) }"],
                    ["Optional.ofNullable(cached).map(ledger::post)", "    .orElseGet(() -> ledger.post(fetch.get()))"], 1.65)
        fix = pair("the fix: pick the payment, then post once", GREEN_M,
                   ["val payment = cached ?: fetch()", "ledger.post(payment)"],
                   ["Payment payment = cached != null ? cached : fetch.get();", "ledger.post(payment);"], -1.75)
        self.seq("Java's Optional has the same trap. Write the branch you mean with if or when, "
                 "or pick the payment first and post it once.",
                 [(0, [FadeIn(trap, shift=UP * 0.15)], 1.0),
                  (1, [FadeIn(fix, shift=UP * 0.15)], 1.0)])
        self.wait(1.5)
        self.play(FadeOut(VGroup(trap, fix)), run_time=0.6)

        # ---------------- the rule and a check ----------------
        heads, rows, cells, names, jobs = make_grid()
        for k in cells:
            names[k].move_to(cells[k].get_center() + UP * 0.22)
        grid = VGroup(heads, rows, *cells.values(), *names.values(), *jobs.values())
        rule = T("Ask what the call gives back, and whether the block sees this or it.", 28).move_to([0, -1.55, 0])
        fit(rule, 12.6)
        self.beat("So: what should the call give back, and does the block see the object as this or as it?",
                  FadeIn(grid), FadeIn(rule, shift=UP * 0.1), run_time=1.2)

        chk = M("payment.also { it.copy(status = CAPTURED) }", 26).move_to([0, -2.35, 0])
        part_copy = part(chk, "payment.also { it.copy(status = CAPTURED) }", "it.copy(status = CAPTURED)")
        qm = T("What status comes back?", 26, GREY_B).move_to([0, -3.05, 0])
        self.seq("A quick check. The payment is authorized. What status comes back?",
                 [(0, [FadeIn(chk, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(qm)], 0.4)])
        self.wait(2.2)
        answer = VGroup(M("AUTHORIZED", 26, BLUE_M), T("also gives back the payment itself, and the copy is dropped", 24, GREY_B)
                        ).arrange(RIGHT, buff=0.35).move_to([0, -3.05, 0])
        fit(answer, 12.6)
        hl2 = SurroundingRectangle(cells[(1, 1)], buff=0.06, color=WHITE, stroke_width=5, corner_radius=0.2)
        self.seq("Authorized. also gives back the payment, and the copy is dropped.",
                 [(0, [ReplacementTransform(qm, answer), Create(hl2)], 0.8),
                  (1, [part_copy.animate.set_opacity(0.3)], 0.6)])
        self.wait(1.0)
