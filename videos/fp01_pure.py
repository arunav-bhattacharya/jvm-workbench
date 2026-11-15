from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [
    (r"\b200\.00\b", "200 euros"), (r"\b3\.00\b", "3 euros"), (r"\b4\.00\b", "4 euros"),
    (r"\b15:59\b", "fifteen fifty-nine"), (r"\b16:00\b", "sixteen hundred"),
    (r"\bisExpired\b", "is expired"), (r"\bYearMonth\.now\(\)", "year month dot now"),
]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads a different spelling than the caption shows), captions split
    only where a new sentence starts, seq() to start animations at a given sentence, and ask() for a
    question followed by a silent pause so the viewer can predict."""

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

    def ask(self, text, *anims, pause=1.5, say=None, run_time=None):
        """A question, then silence so the viewer can predict before the answer appears."""
        self.beat(text, *anims, after=pause, say=say, run_time=run_time)


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


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def chain(m, *steps):
    """Several changes of one mobject in a row, inside one Succession. Each target is built from the one
    before it (several m.animate builders on one mobject would all share the last target)."""
    cur, anims = m, []
    for fn, rt in steps:
        cur = cur.copy()
        fn(cur)
        anims.append(Transform(m, cur, run_time=rt))
    return Succession(*anims)


def moved(m, where):
    """Move m to an absolute place (safe to build next to other moves of m)."""
    return Transform(m, m.copy().move_to(where))


def xfade(old, new, rt=None):
    """Swap one label or token for another by cross-fading (a Transform between different glyphs smears)."""
    kw = {"run_time": rt} if rt else {}
    return AnimationGroup(FadeOut(old), FadeIn(new), **kw)


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def tok(text, color, size=28):
    """A value token: a small filled chip with monospace text."""
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=max(0.66, t.height + 0.34), stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color, 0.35), opacity=1)
    return VGroup(r, t.move_to(r))


def machine(label, w, h, size=28, color=WHITE):
    b = mbox(label, color, w=w, h=h, size=size)
    b.set_z_index(5)
    return b


def wire(a, b, color, tip=True, dash=0.12):
    ln = DashedLine(a, b, dash_length=dash, stroke_width=3, color=color)
    if tip:
        ln.add_tip(tip_length=0.2, tip_width=0.2)
    return ln


class WallClock(VGroup):
    """A clock face whose hands follow the tracker self.t (hours). The hands are a separate mobject:
    add clk.hands to the scene after the face."""

    def __init__(self, hours, r=0.55, color=GOLD_M):
        super().__init__()
        self.t = ValueTracker(hours)
        self.face = Circle(radius=r, stroke_color=color, stroke_width=3).set_fill(fill_of(color, 0.15), 1)
        ticks = VGroup(*[Line(on_circle(ORIGIN, r * 0.78, a), on_circle(ORIGIN, r * 0.93, a), stroke_width=2, color=color)
                         for a in range(0, 360, 30)])
        self.add(self.face, ticks)

        def hands():
            c = self.face.get_center(); rr = self.face.width / 2
            h = self.t.get_value()
            ah = np.radians(90 - 30 * (h % 12)); am = np.radians(90 - 360 * (h % 1))
            return VGroup(Line(c, c + 0.5 * rr * np.array([np.cos(ah), np.sin(ah), 0]), stroke_width=5, color=WHITE),
                          Line(c, c + 0.8 * rr * np.array([np.cos(am), np.sin(am), 0]), stroke_width=3, color=WHITE),
                          Dot(c, radius=0.04 * rr / 0.55, color=WHITE))
        self.hands = always_redraw(hands)

    def placed(self, where):
        """Move the clock and redraw its hands there at once (they would show at the old spot during a FadeIn)."""
        self.move_to(where)
        self.hands.update()
        return self


def feed(scene_tokens, box, out, out_pos, rt_in=0.7, rt_out=0.6):
    """Tokens slide into the box (under it, so they vanish inside); the result slides out to out_pos."""
    out.move_to(box.get_center()).set_z_index(1)
    for t in scene_tokens:
        t.set_z_index(1)
    return Succession(
        AnimationGroup(*[t.animate.move_to(box.get_center()) for t in scene_tokens], run_time=rt_in),
        AnimationGroup(*[FadeOut(t) for t in scene_tokens], FadeIn(out), run_time=0.05),
        out.animate(run_time=rt_out).move_to(out_pos))


class Fp01Pure(Beat):
    """fp-01 section 1 (with section 0's problem and section 2's swap): a pure function's result depends only
    on its arguments and it changes nothing; that is what lets you replace a call with its value."""

    def construct(self):
        self.title_card("A pure function", "same input, same output, nothing else touched")

        # ---------- the problem: a fee function with hidden wires ----------
        Y = -0.9
        fn = machine("quotePayoutFee(amount)", w=5.0, h=1.3, size=28).move_to([0, Y, 0])
        a_in = Arrow([-4.75, Y, 0], fn.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a_out = Arrow(fn.get_right(), [4.15, Y, 0], buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        IN = np.array([-5.65, Y, 0]); OUT = np.array([4.95, Y, 0])
        amt = tok("200.00", BLUE_M).move_to(IN)
        r1 = tok("3.00", GREEN_M)
        self.beat("Here is a fee function. You hand it an amount, and it hands back the fee.",
                  FadeIn(fn), GrowArrow(a_in), GrowArrow(a_out), FadeIn(amt, shift=RIGHT * 0.2), run_time=1.4)
        ctx = T("on your laptop, at 10:00", 26, GREY_B).move_to([0, -2.75, 0])
        expect = T("the test expects 3.00", 24, GREY_B).move_to([4.7, Y - 0.95, 0])
        ok1 = tick(True, 0.3).next_to(OUT, RIGHT, buff=0.75)
        self.seq("A test passes in 200.00 and expects 3.00. At ten in the morning, it passes.",
                 [(0, [FadeIn(expect), FadeIn(ctx)], 0.6),
                  (1, [feed([amt], fn, r1, OUT)], 1.4), (1, [Create(ok1)], 0.4)])

        amt2 = tok("200.00", BLUE_M).move_to(IN)
        r2 = tok("4.00", RED_M)
        bad = tick(False, 0.3).move_to(ok1)
        ctx2 = T("in the nightly build, at 17:00", 26, GREY_B).move_to(ctx)
        self.seq("At five in the afternoon, the nightly build gets 4.00.",
                 [(0, [FadeOut(r1), FadeOut(ok1), FadeIn(amt2), Transform(ctx, ctx2)], 0.6),
                  (0, [feed([amt2], fn, r2, OUT)], 1.3), (0, [Create(bad)], 0.4)])
        self.ask("Same amount, same code. Where did the extra euro come from?")

        # reveal the hidden wires
        clk = WallClock(10).placed([0, 2.0, 0])
        clk_t = M("17:00", 26, GOLD_M).next_to(clk, RIGHT, buff=0.3)
        w_clk = wire(clk.get_bottom() + DOWN * 0.08, fn.get_top() + UP * 0.08, GOLD_M)
        self.seq("It reads the wall clock. After the 16:00 cut-off, it adds a late surcharge.",
                 [(0, [FadeIn(clk), FadeIn(clk.hands), Create(w_clk)], 0.9),
                  (0, [clk.t.animate.set_value(17), FadeIn(clk_t)], 1.6),
                  (1, [Indicate(r2, color=RED_M, scale_factor=1.15)], 0.8)])
        rates = mbox("FeeConfig.rates", TEAL_M, w=3.5, h=1.05, size=24).move_to([-4.45, 2.0, 0])
        w_rates = wire(rates.get_bottom() + DOWN * 0.08 + RIGHT * 0.9, fn.get_top() + LEFT * 1.6 + UP * 0.08, TEAL_M)
        self.beat("It also reads a global rate table that can change at any time.",
                  FadeIn(rates), Create(w_rates), run_time=1.2)

        log_r = RoundedRectangle(corner_radius=0.1, width=3.8, height=1.55, stroke_color=RED_M, stroke_width=3)
        log_r.set_fill(fill_of(RED_M, 0.1), opacity=1)
        log_h = T("audit log", 22, RED_M).move_to(log_r.get_top() + DOWN * 0.27)
        log = VGroup(log_r, log_h).move_to([4.5, 2.0, 0])
        w_log = wire(fn.get_top() + RIGHT * 1.6 + UP * 0.08, log_r.get_bottom() + DOWN * 0.08 + LEFT * 0.9, RED_M)
        line1 = M("fee 4.00 at 17:00", 20, WHITE).move_to(log_r.get_center() + DOWN * 0.15)
        amt3 = tok("200.00", BLUE_M).move_to(IN)
        r3 = tok("4.00", RED_M)
        self.seq("And every call writes a line to the audit log.",
                 [(0, [FadeIn(log), Create(w_log), FadeOut(r2), FadeIn(amt3)], 0.8),
                  (0, [feed([amt3], fn, r3, OUT), Succession(Wait(0.6), FadeIn(line1, shift=UP * 0.1, run_time=0.4))], 1.4)])

        hid1 = T("hidden input", 24, TEAL_M).next_to(rates, UP, buff=0.2)
        hid2 = T("hidden input", 24, GOLD_M).next_to(clk, UP, buff=0.2)
        eff = T("side effect", 24, RED_M).next_to(log, UP, buff=0.2)
        self.seq("The signature shows one input. The clock and the rates are hidden inputs. "
                 "The log line is a side effect: something the call does besides return its value.",
                 [(0, [mark(VGroup(*fn[1][14:]), WHITE, 0.6)], 1.4),
                  (1, [FadeIn(hid1, shift=DOWN * 0.1), FadeIn(hid2, shift=DOWN * 0.1)], 0.7),
                  (2, [FadeIn(eff, shift=DOWN * 0.1)], 0.6)])

        # ---------- the fix: every input is a parameter ----------
        PY = -0.55
        pf = machine("payoutFee", w=3.2, h=2.7, size=30).move_to([0.9, PY, 0])
        rows = [PY + 0.85, PY, PY - 0.85]
        arrs = VGroup(*[Arrow([-2.95, y, 0], [pf.get_left()[0], y, 0], buff=0.12, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.12) for y in rows])
        labs = VGroup(*[M(s, 20, GREY_B).next_to(a, UP, buff=0.06) for s, a in zip(["amount", "rates", "requestedAt"], arrs)])
        SLOT = [np.array([-4.55, y, 0]) for y in rows]
        v_amt = tok("200.00", BLUE_M).move_to(SLOT[0])
        v_rates = tok("STANDARD", TEAL_M).move_to(SLOT[1])
        v_time = tok("15:59", GOLD_M).move_to(SLOT[2])
        p_out = Arrow(pf.get_right(), [4.0, PY, 0], buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        POUT = np.array([4.9, PY, 0])
        corner = np.array([5.75, 2.75, 0])
        self.seq("Now take them out. The time and the rates come in as values, and the caller writes the log. "
                 "Every input is now a parameter.",
                 [(0, [FadeOut(VGroup(ctx, expect, bad, r3, hid1, hid2, eff, w_clk, w_rates, w_log, clk_t)),
                       FadeOut(VGroup(log, line1), shift=RIGHT * 0.8)], 0.8),
                  (1, [ReplacementTransform(fn, pf), FadeOut(a_in), FadeOut(a_out),
                       clk.animate.scale(0.75).move_to(corner),
                       ReplacementTransform(rates, v_rates), FadeIn(v_time), FadeIn(v_amt)], 1.4),
                  (2, [LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.2), FadeIn(labs), GrowArrow(p_out)], 1.0)])

        def copies():
            return [v.copy() for v in (v_amt, v_rates, v_time)]

        o1 = tok("3.00", GREEN_M)
        o2 = tok("4.00", GREEN_M)
        self.seq("At 15:59 it gives 3.00. At 16:00, 4.00.",
                 [(0, [feed(copies(), pf, o1, POUT)], 1.4),
                  (1, [FadeOut(o1), Transform(v_time, tok("16:00", GOLD_M).move_to(SLOT[2]))], 0.5),
                  (1, [feed(copies(), pf, o2, POUT)], 1.4)], after=0.6)

        q = M("?", 40, GREY_B).move_to(POUT)
        self.ask("Run it again tonight, or on eight threads. What comes out?",
                 FadeOut(o2), FadeIn(q), clk.t.animate(rate_func=linear).set_value(23.5), run_time=2.2)
        outs = [tok("4.00", GREEN_M) for _ in range(3)]
        stack = [POUT + UP * 0.85, POUT, POUT + DOWN * 0.85]
        self.seq("4.00, every time. The real clock can spin all it likes.",
                 [(0, [FadeOut(q), LaggedStart(*[feed(copies(), pf, o, p, rt_in=0.5, rt_out=0.4) for o, p in zip(outs, stack)], lag_ratio=0.35),
                       clk.t.animate(rate_func=linear).set_value(33)], 2.4)])

        pure = T("pure", 32, GREEN_M).next_to(pf, UP, buff=0.3)
        rule1 = T("its result depends only on its arguments", 28, WHITE)
        rule2 = T("calling it changes nothing outside it", 28, WHITE)
        rules = VGroup(rule1, rule2).arrange(DOWN, buff=0.25).move_to([0, -2.85, 0])
        self.seq("That is a pure function. Its result depends only on its arguments. And calling it changes nothing outside it.",
                 [(0, [FadeIn(pure, shift=DOWN * 0.1)], 0.6), (1, [FadeIn(rule1, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(rule2, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(pf, arrs, labs, v_amt, v_rates, v_time, p_out, *outs, pure, rules, clk)), FadeOut(clk.hands), run_time=0.7)

        # ---------- replace a call with its value ----------
        fee = machine("fee", w=1.9, h=0.95, size=30).move_to([0, 2.3, 0])
        f_in = tok("20_000", BLUE_M).move_to([-3.2, 2.3, 0])
        f_ar = Arrow([-2.2, 2.3, 0], fee.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        f_ar2 = Arrow(fee.get_right(), [2.2, 2.3, 0], buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        f_out = tok("300", GREEN_M)
        self.seq("Here is a smaller fee function. 20,000 cents in, 300 out.",
                 [(0, [FadeIn(fee), GrowArrow(f_ar), GrowArrow(f_ar2), FadeIn(f_in)], 0.8),
                  (1, [feed([f_in], fee, f_out, [3.1, 2.3, 0])], 1.3)])

        c1 = mbox("fee(20_000)", WHITE, size=28, h=0.9)
        c2 = mbox("fee(20_000)", WHITE, size=28, h=0.9)
        plus = M("+", 34); eq = M("=", 34); res = M("?", 36, GREY_B)
        expr = VGroup(c1, plus, c2, eq, res).arrange(RIGHT, buff=0.4).move_to([0, 0.0, 0])
        self.ask("This line calls it twice and adds the answers. Could you call it once, and use the answer twice?",
                 FadeIn(expr, shift=UP * 0.15), run_time=1.0)
        v1 = tok("300", GREEN_M).move_to(c1); v2 = tok("300", GREEN_M).move_to(c2)
        r600 = tok("600", GREEN_M).next_to(eq, RIGHT, buff=0.4)
        self.seq("Yes. Swap each call for its value: 300 plus 300 is 600.",
                 [(1, [TransformFromCopy(f_out, v1), TransformFromCopy(f_out, v2), FadeOut(c1), FadeOut(c2)], 1.0),
                  (1, [Transform(res, r600)], 0.6)])
        swap_ok = tick(True, 0.24).next_to(r600, RIGHT, buff=0.35)
        self.play(Create(swap_ok), run_time=0.4)
        self.play(FadeOut(VGroup(fee, f_ar, f_ar2, f_out, plus, eq, res, v1, v2, swap_ok)), run_time=0.6)

        # the same swap on a call that charges a card
        card = mbox("card", BLUE_M, w=1.9, h=0.9, size=28).move_to([-5.0, 2.0, 0])
        prov = mbox("provider", WHITE, w=2.4, h=0.9, size=28).move_to([4.8, 2.0, 0])
        cnt = T("charges: 0", 26, RED_M).next_to(prov, DOWN, buff=0.25)
        head = T("store the receipt in c, use it twice", 26, GREY_B).move_to([0, 3.2, 0])
        ch = mbox("charge(card, 20_000)", RED_M, size=26, h=0.9).move_to([0, 0.6, 0])
        ch.set_z_index(5)
        cvar_r = RoundedRectangle(corner_radius=0.1, width=1.9, height=0.85, stroke_color=GREY_B, stroke_width=2.5).set_fill(BLACK, 1)
        cvar_l = M("c", 26, GREY_B).next_to(cvar_r, LEFT, buff=0.2)
        cvar = VGroup(cvar_r, cvar_l).move_to([0, -0.85, 0])
        SL = [np.array([-1.7, -2.6, 0]), np.array([1.7, -2.6, 0])]
        slots = VGroup(*[RoundedRectangle(corner_radius=0.1, width=1.9, height=0.85, stroke_color=GREY_B, stroke_width=2.5).move_to(p) for p in SL])
        list_l = T("the list", 24, GREY_B).next_to(slots, LEFT, buff=0.4)

        def coin(box):
            c = tok("20_000", BLUE_M, size=22).move_to(card).set_z_index(1).set_opacity(0)
            return c, chain(c, (lambda x: x.set_opacity(1), 0.1), (lambda x: x.move_to(box), 0.5),
                            (lambda x: x.move_to(prov), 0.6), (lambda x: x.set_opacity(0), 0.1))

        coinA, flyA = coin(ch)
        rec1 = tok("ch_1", GOLD_M, size=26).move_to(ch).set_z_index(1)
        cpy = [tok("ch_1", GOLD_M, size=26).move_to(cvar_r) for _ in range(2)]
        arr_c = VGroup(*[Arrow(cvar_r.get_bottom(), s.get_top(), buff=0.1, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.15) for s in slots])
        self.seq("Now a call that charges a card. Store the receipt in c, and put c in a list twice: one charge.",
                 [(0, [FadeIn(card), FadeIn(prov), FadeIn(cnt), FadeIn(ch)], 0.9),
                  (1, [FadeIn(head), FadeIn(cvar), FadeIn(slots), FadeIn(list_l)], 0.7),
                  (1, [AnimationGroup(flyA, Succession(Wait(1.2), Transform(cnt, T("charges: 1", 26, RED_M).move_to(cnt), run_time=0.3)),
                                      Succession(Wait(0.5), rec1.animate(run_time=0.6).move_to(cvar_r)))], 1.5),
                  (1, [GrowArrow(arr_c[0]), GrowArrow(arr_c[1]), cpy[0].animate.move_to(SL[0]), cpy[1].animate.move_to(SL[1])], 0.9)])

        head2 = T("now inline c", 26, GREY_B).move_to(head)
        chs = VGroup(*[mbox("charge(...)", RED_M, size=26, h=0.9).move_to([p[0], -0.85, 0]) for p in SL])
        for b in chs:
            b.set_z_index(5)
        arr_b = VGroup(*[Arrow(b.get_bottom(), s.get_top(), buff=0.1, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.15) for b, s in zip(chs, slots)])
        cnt0 = T("charges: ?", 26, RED_M).move_to(cnt)
        self.ask("Now inline c. How many charges?",
                 FadeOut(VGroup(ch, cvar, arr_c, rec1, *cpy)), Transform(head, head2), Transform(cnt, cnt0),
                 FadeIn(chs), FadeIn(arr_b), run_time=1.2)
        cA, fA = coin(chs[0]); cB, fB = coin(chs[1])
        ra = tok("ch_1", GOLD_M, size=26).move_to(chs[0]).set_z_index(1)
        rb = tok("ch_2", GOLD_M, size=26).move_to(chs[1]).set_z_index(1)
        self.seq("Two. The customer paid twice, and nothing in the code warned you.",
                 [(0, [AnimationGroup(
                     Succession(fA, ra.animate(run_time=0.5).move_to(SL[0])),
                     Succession(Wait(0.7), fB, rb.animate(run_time=0.5).move_to(SL[1])),
                     Succession(Wait(1.05), Transform(cnt, T("charges: 1", 26, RED_M).move_to(cnt), run_time=0.2), Wait(0.5),
                                Transform(cnt, T("charges: 2", 26, RED_M).move_to(cnt), run_time=0.2)))], 2.6)])
        self.play(FadeOut(VGroup(card, prov, cnt, head, chs, arr_b, ra, rb, slots, list_l)), run_time=0.6)

        # name it
        name = T("referential transparency", 46, WHITE).move_to([0, 1.4, 0])
        defn = T("you can replace a call with its value, and nothing changes", 28, GREY_A).next_to(name, DOWN, buff=0.4)
        ok_row = VGroup(M("fee(20_000)", 26), M("->", 26, GREY_B), tok("300", GREEN_M, 26), tick(True, 0.2)).arrange(RIGHT, buff=0.3)
        no_row = VGroup(M("charge(card, 20_000)", 26), M("->", 26, GREY_B), tok("ch_1", GOLD_M, 26), tick(False, 0.2)).arrange(RIGHT, buff=0.3)
        rows2 = VGroup(ok_row, no_row).arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to([0, -1.45, 0])
        self.seq("This swap has a name: referential transparency. Only pure calls allow it.",
                 [(0, [Write(name, run_time=1.2), FadeIn(defn, shift=UP * 0.1)], 1.4),
                  (1, [FadeIn(ok_row, shift=UP * 0.1), FadeIn(no_row, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(VGroup(name, defn, rows2)), run_time=0.6)

        # ---------- code last: Java and Kotlin ----------
        jv = code(["static long fee(long amountCents) {",
                   "    return amountCents * 15 / 1000;",
                   "}",
                   "",
                   "long t = fee(20_000) + fee(20_000);",
                   "long f = fee(20_000);",
                   "long same = f + f;       // == t"], 22)
        kt = code(["fun fee(amountCents: Long): Long =",
                   "    amountCents * 15 / 1000",
                   "",
                   "",
                   "val t = fee(20_000) + fee(20_000)",
                   "val f = fee(20_000)",
                   "val same = f + f         // == t"], 22)
        part(jv[6], "// == t").set_color(GREEN_M)
        part(kt[6], "// == t").set_color(GREEN_M)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        pair.scale(min(1, 12.6 / pair.width)).move_to(UP * 0.3)
        self.seq("In Java and Kotlin, these two totals always agree, because fee is pure.",
                 [(0, [FadeIn(pair, shift=UP * 0.15)], 1.0),
                  (0, [mark(VGroup(*jv[4][9:]), BLUE_M, 0.3), mark(VGroup(*kt[4][8:]), BLUE_M, 0.3)], 1.1),
                  (0, [mark(part(jv[6], "f + f"), BLUE_M, 0.3), mark(part(kt[6], "f + f"), BLUE_M, 0.3)], 1.1)])
        self.play(FadeOut(pair), run_time=0.6)

        # ---------- the rule, then a check ----------
        rule = VGroup(T("A pure function takes everything as parameters,", 32),
                      T("and gives everything back as its return value.", 32)).arrange(DOWN, buff=0.22).move_to([0, 2.5, 0])
        self.beat("The rule: a pure function takes everything as parameters, and gives everything back as its return value.",
                  FadeIn(rule, shift=UP * 0.1), run_time=1.2)
        ex = machine("isExpired(card)", w=4.0, h=1.0, size=28).move_to([0, -1.0, 0])
        e_in = tok("card", BLUE_M).move_to([-4.0, -1.0, 0])
        e_ar = Arrow([-3.25, -1.0, 0], ex.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        e_q = M("?", 40, GREY_B).move_to([4.45, -1.0, 0])
        e_ar2 = Arrow(ex.get_right(), [3.25, -1.0, 0], buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        q2 = T("it compares the card's expiry with YearMonth.now()", 26, GREY_A).move_to([0, 0.55, 0])
        self.ask("Quick check: isExpired compares a card's expiry with YearMonth.now(). Pure?",
                 FadeIn(ex), FadeIn(e_in), GrowArrow(e_ar), GrowArrow(e_ar2), FadeIn(e_q), FadeIn(q2), run_time=1.2)
        clk2 = WallClock(9.25, r=0.45).placed([0, -2.85, 0])
        w2 = wire(clk2.get_top() + UP * 0.06, ex.get_bottom() + DOWN * 0.08, GOLD_M)
        h2 = T("hidden input", 24, GOLD_M).next_to(clk2, RIGHT, buff=0.35)
        nope = T("not pure", 30, RED_M).move_to(e_q)
        self.seq("Not pure. The clock is a hidden input again.",
                 [(0, [Transform(e_q, nope)], 0.6),
                  (1, [FadeIn(clk2), FadeIn(clk2.hands), Create(w2), FadeIn(h2)], 0.9),
                  (1, [clk2.t.animate(rate_func=linear).set_value(11)], 1.0)])
        self.wait(0.8)
