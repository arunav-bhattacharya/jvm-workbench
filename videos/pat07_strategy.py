from fg import *
import fg

# ---- helpers for this file (fg.py is shared and stays untouched) ----
fg.SAY += [(r"\bAdyx\b", "Addix"), (r"\bif-else\b", "if else")]
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

FEE, SPEED, MIX, BAD = GOLD_M, BLUE_M, GREEN_M, RED_M


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
            if callable(anims):          # built when it starts, so it sees where things are by then
                anims = anims()
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


# Inside a Succession, manim adds every member to the scene when the Succession starts, so anything that
# should show up later must start invisible and appear through an updater (not FadeIn, an introducer).
def appear(m, run_time=0.3):
    m.set_opacity(0)

    def upd(mob, a):
        mob.set_opacity(a)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b, visible only while it runs."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = Dot(radius=0.1, color=color).move_to(a).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(a + (b - a) * smooth(t))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time + 0.12, rate_func=linear)


def flash(r, color, run_time=1.0, tw=0.6):
    """A passing flash along r's outline, invisible before and after it runs."""
    full = r.copy().set_fill(opacity=0).set_stroke(color, 7, opacity=1)
    m = full.copy().set_stroke(opacity=0).set_z_index(20)

    def upd(mob, a):
        hi = min(1.0, a * (1 + tw))
        lo = max(0.0, hi - tw)
        if a <= 0 or a >= 1 or hi <= lo:
            mob.set_stroke(opacity=0)
            return
        mob.pointwise_become_partial(full, lo, hi)
        mob.set_stroke(color, 7, opacity=1, family=False)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


class Pulse(Transform):
    """Indicate for filled boxes: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.06, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rbox(w, h, color, k=0.12, sw=3):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=sw)
    return r.set_fill(fill_of(color, k), opacity=1)


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


def quote(name, fee, ms):
    r = rbox(3.3, 1.45, WHITE, k=0.1)
    n = T(name, 30)
    f = M(f"fee {fee}", 24, FEE)
    l = M(f"{ms} ms", 24, SPEED)
    row = VGroup(f, l).arrange(RIGHT, buff=0.45)
    VGroup(n, row).arrange(DOWN, buff=0.2).move_to(r)
    g = VGroup(r, n, row)
    g.fee, g.ms = f, l
    return g


def plug(lines, color, w=3.1, h=1.0, size=28):
    r = rbox(w, h, color, k=0.2, sw=4)
    txt = VGroup(*[T(s, size) for s in lines]).arrange(DOWN, buff=0.06).move_to(r)
    nub = Rectangle(width=0.5, height=0.14, stroke_width=0).set_fill(color, 1).next_to(r, UP, buff=0)
    return VGroup(r, txt, nub)


def strip(text, color):
    r = rbox(5.4, 0.5, color, k=0.18, sw=2.5)
    t = M(text, 22).move_to(r)
    return VGroup(r, t)


XS, CY = [-4.3, 0.0, 4.3], -1.65
SOCK = np.array([0, 0.75, 0])
RACK = {"cheap": np.array([-4.75, 1.25, 0]), "fast": np.array([-4.75, 0.05, 0]), "mix": np.array([4.75, 0.75, 0])}


class Pat07Strategy(Beat):
    """pat-07 section 0: sort owns the loop and asks one question; the strategy that answers it plugs in."""

    def construct(self):
        self.title_card("Strategy", "swap the one decision that varies")

        # ---------------- three quotes, one question ----------------
        north, adyx, kest = quote("Northpay", 30, 200), quote("Adyx", 25, 900), quote("Kestrel", 30, 120)
        order = [north, adyx, kest]
        for x, c in zip(XS, order):
            c.move_to([x, CY, 0])
        ranks = VGroup(*[T(s, 24, GREY_B).move_to([x, -2.85, 0]) for s, x in zip(("1st", "2nd", "3rd"), XS)])

        self.seq("Three payment providers quote for one payment. Northpay: 30 cents, 200 milliseconds. "
                 "Adyx: 25 cents, but 900 milliseconds. Kestrel: 30 cents, 120 milliseconds.",
                 [(1, [FadeIn(north, shift=UP * 0.2)], 0.7),
                  (2, [FadeIn(adyx, shift=UP * 0.2)], 0.7),
                  (3, [FadeIn(kest, shift=UP * 0.2)], 0.7)])

        op_cheap = plug(["cheapest"], FEE).move_to([-4.3, 0.6, 0])
        op_fast = plug(["fastest"], SPEED).move_to([0, 0.6, 0])
        op_mix = plug(["a mix"], MIX).move_to([4.3, 0.6, 0])
        owners = VGroup(*[T(s, 22, GREY_B).next_to(o[0], DOWN, buff=0.15)
                          for s, o in zip(("finance", "on-call", "next month"), (op_cheap, op_fast, op_mix))])
        self.seq("Which one does the router try first? Finance says cheapest. The on-call engineer says fastest. "
                 "Next month, someone wants a mix.",
                 [(0, [FadeIn(ranks)], 0.6),
                  (1, [FadeIn(op_cheap, shift=DOWN * 0.15), FadeIn(owners[0])], 0.6),
                  (2, [FadeIn(op_fast, shift=DOWN * 0.15), FadeIn(owners[1])], 0.6),
                  (3, [FadeIn(op_mix, shift=DOWN * 0.15), FadeIn(owners[2])], 0.6)])

        # ---------------- the rule written into the router ----------------
        rbx = RoundedRectangle(corner_radius=0.16, width=11.6, height=1.9, stroke_color=WHITE, stroke_width=3)
        rbx.set_fill(fill_of(WHITE, 0.07), opacity=1).move_to([0, 2.35, 0]).set_z_index(-1)   # stays behind its strips
        r_title = T("router", 32)
        r_sub = T("loops over the quotes, swaps them", 22, GREY_B)
        r_txt = VGroup(r_title, r_sub).arrange(DOWN, buff=0.12).move_to([-3.2, 2.35, 0])
        div = DashedLine([-0.45, 3.1, 0], [-0.45, 1.6, 0], dash_length=0.08, stroke_width=1.5, color=GREY_D)
        s_cheap = strip("if cheapest: compare fees", FEE).move_to([2.75, 2.9, 0])
        s_fast = strip("else if fastest: compare speed", SPEED).move_to([2.75, 2.35, 0])
        s_mix = strip("else if a mix: ...", MIX).move_to([2.75, 1.8, 0])
        self.seq("You could write every opinion into the router, as an if-else chain. "
                 "Then each new one is another branch, in the same code that loops over the quotes and swaps them.",
                 [(0, [FadeIn(rbx), FadeIn(r_txt), Create(div)], 0.8),
                  (0, [FadeOut(owners), ReplacementTransform(op_cheap, s_cheap)], 0.7),
                  (1, [ReplacementTransform(op_fast, s_fast)], 0.6),
                  (1, [ReplacementTransform(op_mix, s_mix)], 0.6),
                  (1, lambda: [rbx.animate.set_stroke(BAD), Indicate(r_sub, color=BAD, scale_factor=1.05)], 0.8)])

        q = T("?", 56).move_to([(XS[0] + XS[1]) / 2, CY + 0.3, 0])
        self.seq("But ordering only ever asks one question, about two quotes at a time: which goes first? "
                 "The answer changes. The looping never does.",
                 [(0, lambda: [rbx.animate.set_stroke(WHITE), north.animate.shift(UP * 0.3), adyx.animate.shift(UP * 0.3)], 0.7),
                  (0, [FadeIn(q, scale=1.4)], 0.5),
                  (1, [Pulse(VGroup(s_cheap, s_fast, s_mix), WHITE, 1.03)], 0.9),
                  (2, [Indicate(r_txt, color=WHITE, scale_factor=1.05)], 0.9),
                  (2, lambda: [FadeOut(q), north.animate.shift(DOWN * 0.3), adyx.animate.shift(DOWN * 0.3)], 0.6)])

        # ---------------- split: sort keeps the loop, the answer plugs in ----------------
        mbx = RoundedRectangle(corner_radius=0.16, width=6.6, height=1.45, stroke_color=WHITE, stroke_width=3)
        mbx.set_fill(fill_of(WHITE, 0.07), opacity=1).move_to([0, 2.5, 0]).set_z_index(-1)
        m_title = T("sort", 34)
        m_sub = T("loops over the quotes, swaps them", 22, GREY_B)
        VGroup(m_title, m_sub).arrange(DOWN, buff=0.1).move_to(mbx)
        con = Line([0, 1.775, 0], [0, 1.35, 0], stroke_width=3, color=GREY_B)
        ask = T("which goes first?", 24, GREY_B).next_to(con, RIGHT, buff=0.25)
        sock = DashedVMobject(RoundedRectangle(corner_radius=0.14, width=3.5, height=1.2), num_dashes=44)
        sock.set_stroke(GREY_B, 2.5).move_to(SOCK)
        p_cheap = plug(["cheapest"], FEE)
        p_fast = plug(["fastest"], SPEED)
        p_mix = plug(["cheapest,", "then fastest"], MIX, size=26)
        for p, k in ((p_cheap, "cheap"), (p_fast, "fast"), (p_mix, "mix")):
            p.shift(RACK[k] - p[0].get_center())

        self.seq("So split them. One general sort does the looping, and the answer plugs in from outside.",
                 [(0, [ReplacementTransform(s_cheap, p_cheap), ReplacementTransform(s_fast, p_fast),
                       ReplacementTransform(s_mix, p_mix), FadeOut(div)], 1.0),
                  (1, [ReplacementTransform(rbx, mbx), ReplacementTransform(r_title, m_title),
                       ReplacementTransform(r_sub, m_sub)], 0.9),
                  (1, [Create(con), Create(sock), FadeIn(ask)], 0.7)])

        def to(p, where):
            return p.animate.shift(where - p[0].get_center())

        def reorder(new):
            anims = []
            for i, c in enumerate(new):
                tgt = np.array([XS[i], CY, 0])
                d = tgt[0] - c.get_center()[0]
                if abs(d) < 1e-3:
                    continue
                c.set_z_index(10 if d < 0 else 5)
                anims.append(c.animate(path_arc=4 * np.arctan(0.3 / (abs(d) / 2))).move_to(tgt))
            order[:] = new
            return anims

        fees = VGroup(north.fee, adyx.fee, kest.fee)
        lat = VGroup(north.ms, adyx.ms, kest.ms)
        self.seq("Plug in cheapest: Adyx moves to the front. Swap in fastest: Kestrel leads. The sort never changed.",
                 [(0, lambda: [to(p_cheap, SOCK)], 0.8),
                  (0, [Indicate(fees, color=FEE, scale_factor=1.2)], 0.6),
                  (0, lambda: reorder([adyx, north, kest]), 1.1),
                  (1, lambda: [to(p_cheap, RACK["cheap"])], 0.6),
                  (1, lambda: [to(p_fast, SOCK)], 0.7),
                  (1, [Indicate(lat, color=SPEED, scale_factor=1.2)], 0.5),
                  (1, lambda: reorder([kest, north, adyx]), 1.2),
                  (2, [Pulse(VGroup(mbx, m_title, m_sub), WHITE, 1.03)], 0.8)])

        t_strat = T("strategy", 28).move_to([0, -0.35, 0])
        t_ctx = T("context", 28).move_to([4.6, 2.5, 0])
        self.seq("That plug is a strategy. The sort that uses it is the context, and the caller picks the strategy, at run time.",
                 [(0, [FadeIn(t_strat, shift=UP * 0.1), Pulse(p_fast, SPEED, 1.05)], 0.8),
                  (1, [FadeIn(t_ctx, shift=LEFT * 0.1)], 0.7)])

        # ---------------- predict ----------------
        self.seq("Now plug in cheapest, then fastest for ties. What order do you get? Pause and work it out.",
                 [(0, lambda: [FadeOut(t_strat), to(p_fast, RACK["fast"])], 0.6),
                  (0, lambda: [to(p_mix, SOCK)], 0.8),
                  (1, [Indicate(ranks, color=WHITE, scale_factor=1.15)], 0.9)], after=2.4)

        self.seq("Adyx first, at 25. Northpay and Kestrel tie at 30, so speed decides: Kestrel, then Northpay.",
                 [(0, [Indicate(adyx.fee, color=FEE, scale_factor=1.3)], 0.6),
                  (0, lambda: reorder([adyx, kest, north]), 1.2),
                  (1, [Indicate(VGroup(kest.fee, north.fee), color=FEE, scale_factor=1.3)], 0.8),
                  (1, [Indicate(VGroup(kest.ms, north.ms), color=SPEED, scale_factor=1.3)], 0.8)])

        # ---------------- the class becomes one expression ----------------
        cls_code = code(["class CheapestFirst implements Comparator<Quote> {",
                         "    public int compare(Quote a, Quote b) {",
                         "        return Long.compare(a.feeMinor(), b.feeMinor());",
                         "    }",
                         "}"], 24)
        part(cls_code[2], "feeMinor").set_color(FEE)
        part(cls_code[2], "feeMinor", 1).set_color(FEE)
        cls_box = rbox(cls_code.width + 0.9, cls_code.height + 0.8, FEE, k=0.12)
        cls_code.move_to(cls_box)
        cls_g = VGroup(cls_box, cls_code).move_to([0, 0.1, 0])
        cls_l = T("1994: a class for each strategy", 26, GREY_B).next_to(cls_g, UP, buff=0.3)
        one = cline("Comparator.comparingLong(Quote::feeMinor)", 30)
        one.remove(one[0])
        part(one, "feeMinor").set_color(FEE)
        one_box = rbox(one.width + 0.8, 1.1, FEE, k=0.12)
        one.move_to(one_box)
        one_g = VGroup(one_box, one).move_to([0, 0.1, 0])
        one_l = T("since Java 8: one method reference", 26, GREY_B).next_to(one_g, UP, buff=0.3)
        rest = VGroup(mbx, m_title, m_sub, con, ask, sock, p_fast, p_mix, t_ctx, ranks, north, adyx, kest)
        self.seq("In the 1994 Design Patterns book, each plug was a class with one method. "
                 "Since Java 8, a lambda or a method reference is the whole class.",
                 [(0, [FadeOut(rest), p_cheap.animate.move_to([0, 0.1, 0])], 0.8),
                  (0, [ReplacementTransform(p_cheap, cls_g), FadeIn(cls_l)], 1.0),
                  (1, [ReplacementTransform(cls_g, one_g), ReplacementTransform(cls_l, one_l)], 1.1)])
        self.play(FadeOut(VGroup(one_g, one_l)), run_time=0.5)

        # ---------------- the code, Java and Kotlin ----------------
        def screen(jlines, klines, size=24):
            jv, kt = code(jlines, size), code(klines, size)
            jh, kh = T("Java", 26, GREY_B), T("Kotlin", 26, GREY_B)
            kt.next_to(jv, DOWN, buff=0.75).align_to(jv, LEFT)
            jh.next_to(jv[0], LEFT, buff=0.6)
            kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
            g = VGroup(jv, kt, jh, kh)
            g.scale(min(1, 12.4 / g.width, 6.4 / g.height)).move_to(ORIGIN)
            return jv, kt, VGroup(jh, kh), g

        jv, kt, heads, scr1 = screen(["Comparator<Quote> cheapest = Comparator.comparingLong(Quote::feeMinor);",
                                      "quotes.sort(cheapest.thenComparingLong(Quote::p95Millis));"],
                                     ["val cheapest = compareBy<Quote> { it.feeMinor }",
                                      "val ordered = quotes.sortedWith(cheapest.thenBy { it.p95Millis })"])
        for c in (jv, kt):
            part(c[0], "feeMinor").set_color(FEE)
            part(c[1], "p95Millis").set_color(SPEED)
        self.seq("In code, each plug is one line, in Java and in Kotlin. The second call chains the tie-breaker behind the first.",
                 [(0, [FadeIn(VGroup(jv, heads[0]), shift=UP * 0.15)], 0.7),
                  (0, [FadeIn(VGroup(kt, heads[1]), shift=UP * 0.15)], 0.7),
                  (1, [Indicate(VGroup(part(jv[1], "thenComparingLong(Quote::p95Millis)"),
                                       part(kt[1], "thenBy { it.p95Millis }")), color=SPEED, scale_factor=1.08)], 1.0)])
        self.play(FadeOut(scr1), run_time=0.5)

        jv2, kt2, heads2, scr2 = screen(["interface FeeStrategy { long fee(Payment p); }",
                                         "FeeStrategy sepa = p -> 25;",
                                         "FeeStrategy card = p -> 30 + p.amountMinor() * 290 / 10_000;"],
                                        ["val sepa: (Payment) -> Long = { 25L }",
                                         "val card: (Payment) -> Long = { 30 + it.amountMinor * 290 / 10_000 }"])
        self.seq("A fee rule has the same shape: one method, from a payment to a fee. "
                 "Java names it with a one-line interface. In Kotlin, a function type is enough.",
                 [(0, [FadeIn(VGroup(jv2, heads2[0]), shift=UP * 0.15)], 0.8),
                  (0, [FadeIn(VGroup(kt2, heads2[1]), shift=UP * 0.15)], 0.8),
                  (1, [Indicate(jv2[0], color=FEE, scale_factor=1.04)], 0.9),
                  (2, [Indicate(VGroup(part(kt2[0], "(Payment) -> Long"), part(kt2[1], "(Payment) -> Long")),
                                color=FEE, scale_factor=1.08)], 0.9)])
        self.play(FadeOut(scr2), run_time=0.5)

        # ---------------- Template Method, one beat ----------------
        tm_t = T("Template Method", 34).move_to([0, 2.7, 0])
        b1 = rbox(3.0, 1.0, WHITE, k=0.1)
        b1.add(T("start timer", 28).move_to(b1))
        hole = DashedVMobject(RoundedRectangle(corner_radius=0.14, width=3.0, height=1.0), num_dashes=36).set_stroke(GREY_B, 2.5)
        hole_t = M("doCall()", 26, GREY_B).move_to(hole)
        b3 = rbox(3.0, 1.0, WHITE, k=0.1)
        b3.add(T("record", 28).move_to(b3))
        row = VGroup(b1, VGroup(hole, hole_t), b3).arrange(RIGHT, buff=1.0).move_to([0, 1.2, 0])
        a1 = Arrow(b1.get_right(), hole.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        a2 = Arrow(hole.get_right(), b3.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        base_l = T("a base class fixes the steps", 24, GREY_B).next_to(row, UP, buff=0.3)
        sub_t = T("a subclass overrides doCall()", 26)
        sub = rbox(sub_t.width + 0.7, 1.0, PURPLE_M, k=0.15)
        sub.add(sub_t.move_to(sub))
        sub.move_to([0, -1.3, 0])
        up = Arrow(sub.get_top(), hole.get_bottom(), buff=0.12, stroke_width=3, color=PURPLE_M, max_tip_length_to_length_ratio=0.15)
        lam_m = M("() -> psp.capture(authId)", 26)
        lam = rbox(lam_m.width + 0.7, 1.0, FEE, k=0.15)
        lam.add(lam_m.move_to(lam))
        lam.move_to([0, -1.3, 0])
        lam_l = T("passed in as a function", 24, GREY_B).next_to(lam, DOWN, buff=0.2)
        up2 = Arrow(lam.get_top(), hole.get_bottom(), buff=0.12, stroke_width=3, color=FEE, max_tip_length_to_length_ratio=0.15)
        self.seq("Template Method, the other half of this lesson, has a hole too. "
                 "A base class fixes the steps, and a subclass fills one in. "
                 "Modern code passes that step in as a function instead.",
                 [(0, [FadeIn(tm_t), FadeIn(row), GrowArrow(a1), GrowArrow(a2)], 1.0),
                  (1, [FadeIn(base_l)], 0.5),
                  (1, [FadeIn(sub, shift=UP * 0.2), GrowArrow(up)], 0.8),
                  (2, [ReplacementTransform(sub, lam), ReplacementTransform(up, up2), FadeIn(lam_l)], 1.0)])
        self.play(FadeOut(VGroup(tm_t, row, a1, a2, base_l, lam, up2, lam_l)), run_time=0.6)

        # ---------------- the rule, then a check ----------------
        rule = VGroup(T("Keep the steps in one place.", 36),
                      T("Pass in the one decision that varies,", 36, FEE),
                      T("usually as a lambda.", 36, FEE)).arrange(DOWN, buff=0.25).move_to([0, 0.3, 0])
        self.seq("The rule: keep the steps in one place, and pass in the one decision that varies, usually as a lambda.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.15)], 0.8), (0, [FadeIn(rule[1:], shift=UP * 0.15)], 0.9)])
        self.play(FadeOut(rule), run_time=0.5)

        blue = quote("Bluefin", 25, 150).move_to([0, 1.4, 0])
        qq = T("With cheapest, then fastest, where does it go?", 32).move_to([0, -0.4, 0])
        ans = T("First: it ties Adyx at 25, and it's faster.", 32, MIX).move_to([0, -1.6, 0])
        self.seq("A quick check. A fourth provider, Bluefin, quotes 25 cents and 150 milliseconds. "
                 "With cheapest, then fastest, where does it go?",
                 [(1, [FadeIn(blue, shift=UP * 0.2)], 0.7), (2, [FadeIn(qq, shift=UP * 0.15)], 0.7)], after=2.0)
        self.seq("First. It ties Adyx on fee, and it's faster.",
                 [(0, [FadeIn(ans, shift=UP * 0.15), Indicate(blue.ms, color=SPEED, scale_factor=1.3)], 0.9)])
        self.wait(0.8)
