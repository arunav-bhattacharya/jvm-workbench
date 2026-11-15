from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bfeeFor\b", "fee for"), (r"\bandThen\b", "and then")]

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

    def ask(self, text, *anims, pause=1.6, say=None, run_time=None):
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




def machine(label, color=WHITE, w=None, h=0.9, size=26):
    b = mbox(label, color, w=w, h=h, size=size)
    b.set_z_index(5)
    return b


def loop_icon(r=0.28, color=GREY_B):
    a = Arc(radius=r, start_angle=PI * 0.6, angle=-PI * 1.7, stroke_width=3, color=color)
    a.add_tip(tip_length=0.14, tip_width=0.14)
    return a


def feed(tokens, box, out, out_pos, rt_in=0.6, rt_out=0.5):
    """Tokens slide under the box and vanish; the result slides out to out_pos."""
    out.move_to(box.get_center()).set_z_index(1)
    for t in tokens:
        t.set_z_index(1)
    return Succession(
        AnimationGroup(*[t.animate.move_to(box.get_center()) for t in tokens], run_time=rt_in),
        AnimationGroup(*[FadeOut(t) for t in tokens], FadeIn(out), run_time=0.05),
        out.animate(run_time=rt_out).move_to(out_pos))


class Fp03Hof(Beat):
    """fp-03 section 0 (with sections 1 and 2): a function that takes a function (retry), one that returns a
    function (feeFor), and two small functions composed into one pipeline."""

    def construct(self):
        self.title_card("Functions in, functions out", "higher-order functions")

        # ---------- the problem: the same loop three times ----------
        calls = ["issuer.authorize(payment)", "ledger.post(entry)", 'fx.rate("EURUSD")']
        rows = VGroup()
        for i, c in enumerate(calls):
            fr = RoundedRectangle(corner_radius=0.14, width=9.4, height=1.2, stroke_color=GREY_B, stroke_width=2.5)
            ic = loop_icon().move_to(fr.get_left() + RIGHT * 0.55)
            lb = T("try up to 3 times", 26, GREY_A).next_to(ic, RIGHT, buff=0.3)
            ch = tok(c, GOLD_M, 24).move_to(fr.get_right() + LEFT * 2.35).set_z_index(3)
            rows.add(VGroup(fr, ic, lb, ch))
        rows.arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        self.seq("Three places in a payment service call something flaky: the card issuer, the ledger, and the FX rate service.",
                 [(0, [LaggedStart(*[FadeIn(VGroup(r[0], r[1], r[2])) for r in rows], lag_ratio=0.2)], 1.2),
                  (0, [LaggedStart(*[FadeIn(r[3], shift=LEFT * 0.2) for r in rows], lag_ratio=0.5)], 2.0)],
                 say="Three places in a payment service call something flaky: the card issuer, the ledger, and the F X rate service.")
        self.seq("Each call sits inside the same loop: try up to three times, then give up. Only the call in the middle changes.",
                 [(0, [*[Indicate(VGroup(r[1], r[2]), color=WHITE, scale_factor=1.04) for r in rows]], 1.0),
                  (1, [*[Indicate(r[3], color=GOLD_M, scale_factor=1.08) for r in rows]], 1.0)])
        self.ask("How do you write that loop once, when the part that changes is a call?")

        # ---------- functions in: retry ----------
        rm = RoundedRectangle(corner_radius=0.16, width=8.0, height=2.3, stroke_color=WHITE, stroke_width=3).set_fill(fill_of(WHITE, 0.1), 1)
        rm_t = M("retry(3, block)", 28, WHITE).move_to(rm.get_top() + DOWN * 0.42)
        sock = DashedVMobject(RoundedRectangle(corner_radius=0.1, width=5.0, height=0.85, stroke_color=GOLD_M, stroke_width=2.5), num_dashes=40)
        sock.move_to(rm.get_center() + DOWN * 0.3 + RIGHT * 0.9)
        sock_l = M("block", 24, GOLD_M).next_to(sock, LEFT, buff=0.3)
        ric = loop_icon(0.24, WHITE).next_to(rm_t, LEFT, buff=0.3)
        retry = VGroup(rm, rm_t, sock, sock_l, ric).move_to([-1.0, 1.1, 0])
        issuer = rows[0][3]
        spare = VGroup(rows[1][3], rows[2][3])
        self.seq("Pass the call in, as a function. retry owns the loop. The call arrives as block, and retry decides when to run it.",
                 [(0, [FadeOut(VGroup(*[VGroup(r[0], r[1], r[2]) for r in rows])), FadeIn(retry),
                       spare.animate.arrange(RIGHT, buff=0.6).move_to([-1.0, -2.9, 0]).set_opacity(0.45)], 1.0),
                  (0, [issuer.animate.move_to(sock)], 0.8),
                  (2, [Indicate(sock_l, color=GOLD_M, scale_factor=1.15)], 0.8)])

        att = VGroup(*[tok(t, c, 22) for t, c in (("1: timeout", RED_M), ("2: timeout", RED_M), ("3: auth_pay_42", GREEN_M))])
        att.arrange(RIGHT, buff=0.35).move_to([-1.0, -0.75, 0])
        for a in att:
            a.set_opacity(0)
        out_ar = Arrow(rm.get_right(), [4.0, 1.1, 0], buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        res = tok("auth_pay_42", GREEN_M, 24)

        def attempt(k):
            return Succession(Indicate(issuer, color=GOLD_M, scale_factor=1.06, run_time=0.45), att[k].animate(run_time=0.3).set_opacity(1))

        self.seq("Here the issuer times out twice. retry runs block again, and the third try returns an authorization.",
                 [(0, [attempt(0)], 0.75), (0, [attempt(1)], 0.75),
                  (1, [attempt(2)], 0.75), (1, [GrowArrow(out_ar), FadeIn(res.move_to([5.25, 1.1, 0]), shift=RIGHT * 0.2)], 0.6)])
        hof = T("a function that takes a function: a higher-order function", 28, WHITE).move_to([0, -1.9, 0])
        new_row = VGroup(issuer.copy(), spare[1].copy()).arrange(RIGHT, buff=0.6).move_to([-1.0, -2.9, 0])
        self.seq("The ledger call plugs into the same socket. A function that takes a function is a higher-order function.",
                 [(0, [FadeOut(VGroup(att, res, out_ar)),
                       Transform(issuer, issuer.copy().move_to(new_row[0]).set_opacity(0.45)),
                       Transform(spare[1], spare[1].copy().move_to(new_row[1])),
                       Transform(spare[0], spare[0].copy().move_to(sock).set_opacity(1))], 1.0),
                  (1, [FadeIn(hof, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(retry, issuer, spare, hof)), run_time=0.6)

        # ---------- functions out: feeFor ----------
        fac = machine("feeFor(country)", WHITE, w=4.0, h=1.1, size=28).move_to([-2.0, 1.9, 0])
        nl = tok("NL", TEAL_M, 28).move_to([-5.6, 1.9, 0])
        f_ar = Arrow(nl.get_right(), fac.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        dutch = machine("dutch", BLUE_M, w=2.6, h=1.0, size=28)
        pocket = RoundedRectangle(corner_radius=0.08, width=2.6, height=0.6, stroke_color=TEAL_M, stroke_width=2.5).set_fill(fill_of(TEAL_M, 0.15), 1)
        pk = M("bps = 140", 22, WHITE)
        prod = VGroup(dutch, pocket, pk)
        pocket.next_to(dutch, DOWN, buff=0); pk.move_to(pocket)
        prod.move_to(fac.get_center()).set_z_index(1)
        pocket.set_z_index(1); pk.set_z_index(1); dutch.set_z_index(1)
        PROD = np.array([0.3, -0.85, 0])
        self.seq("It works the other way too. feeFor takes a country, and hands back a fee function.",
                 [(1, [FadeIn(fac), FadeIn(nl), GrowArrow(f_ar)], 0.7),
                  (1, [nl.animate.move_to(fac.get_center()).set_opacity(0)], 0.6),
                  (1, [prod.animate.move_to(PROD + DOWN * 0.3)], 1.0)])
        self.remove(nl)
        for m in (dutch, pocket, pk):
            m.set_z_index(5)
        a_in = tok("100,000", BLUE_M, 26).move_to([-3.6, -0.85, 0])
        in_ar = Arrow([-2.6, -0.85, 0], dutch.get_left() + DOWN * 0.0, buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        out_ar2 = Arrow(dutch.get_right(), [3.4, -0.85, 0], buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        fee1 = tok("1,400", GREEN_M, 26)
        self.seq("It looks up the Dutch rate once. The function it returns keeps that number, and prices every payment after that.",
                 [(0, [Circumscribe(VGroup(pocket, pk), color=TEAL_M, buff=0.08)], 0.9),
                  (1, [FadeIn(a_in), GrowArrow(in_ar), GrowArrow(out_ar2)], 0.6),
                  (1, [feed([a_in], dutch, fee1, [4.3, -0.85, 0])], 1.2)])
        self.play(FadeOut(VGroup(fac, f_ar, prod, in_ar, out_ar2, fee1)), run_time=0.6)

        # ---------- functions combined: a pipeline ----------
        XS = [-3.2, 0.2, 3.6]
        specs = [("+25", "addSchemeFee"), ("-10%", "loyaltyDiscount"), ("cap 1,000", "capAtTenEuros")]
        ms = VGroup()
        for (lab, nm), x in zip(specs, XS):
            m = machine(lab, GOLD_M, w=2.0, h=1.0, size=26).move_to([x, 0.6, 0])
            n = M(nm, 20, GREY_B).next_to(m, DOWN, buff=0.22)
            ms.add(VGroup(m, n))
        self.seq("Small functions also snap together. Add a 25-cent scheme fee, take 10 percent off, cap at 10 euros.",
                 [(1, [FadeIn(ms[0])], 0.5), (1, [FadeIn(ms[1])], 0.5), (1, [FadeIn(ms[2])], 0.5)])

        def run_pipe(order, values, y=0.6):
            v = tok(values[0], BLUE_M, 24).move_to([-5.45, y, 0])
            anims = [FadeIn(v, run_time=0.3)]
            cur = v
            for k, mi in enumerate(order):
                m = ms[mi][0]
                nxt = tok(values[k + 1], BLUE_M if k < 2 else GREEN_M, 24)
                anims.append(feed([cur], m, nxt, [XS[k] + 1.7 if k < 2 else 5.85, y, 0], rt_in=0.45, rt_out=0.4))
                cur = nxt
            return cur, Succession(*anims)

        last, pipe = run_pipe([0, 1, 2], ["1,200", "1,225", "1,102", "1,000"])
        brace = SurroundingRectangle(ms, buff=0.25, corner_radius=0.15, color=WHITE, stroke_width=2)
        price_l = M("price", 30, WHITE).next_to(brace, UP, buff=0.2)
        self.seq("Feed each result into the next. That's composition: three functions become one pipeline, price. 1,200 cents comes out as 1,000.",
                 [(0, [pipe], 3.2), (1, [Create(brace), FadeIn(price_l)], 0.8)])
        self.ask("Move the cap to the front. Same price?",
                 FadeOut(last), FadeOut(brace), FadeOut(price_l),
                 ms[2].animate.move_to([XS[0], ms[2].get_center()[1], 0]),
                 ms[0].animate.move_to([XS[1], ms[0].get_center()[1], 0]),
                 ms[1].animate.move_to([XS[2], ms[1].get_center()[1], 0]), run_time=1.2)
        ms2 = VGroup(ms[2], ms[0], ms[1])
        ms = ms2
        last2, pipe2 = run_pipe([0, 1, 2], ["1,200", "1,000", "1,025", "922"])
        order_l = T("the order is part of the result", 28, GOLD_M).move_to([0, -2.2, 0])
        self.seq("No. 922. The order is part of the result.",
                 [(0, [pipe2], 3.0), (2, [FadeIn(order_l, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(ms, last2, order_l)), run_time=0.6)

        # ---------- code: Java and Kotlin ----------
        jv = code(["String auth = retry(3, () -> issuer.authorize(payment));",
                   "Function<Long, Long> price = addSchemeFee",
                   "        .andThen(loyaltyDiscount).andThen(capAtTenEuros);"], 22)
        kt = code(["val auth = retry(3) { issuer.authorize(payment) }",
                   "infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C =",
                   "    { a -> next(this(a)) }",
                   "val price = addSchemeFee andThen loyaltyDiscount andThen capAtTenEuros"], 22)
        part(jv[0], "() -> issuer.authorize(payment)").set_color(GOLD_M)
        part(kt[0], "{ issuer.authorize(payment) }").set_color(GOLD_M)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        pair = VGroup(jcol, kcol).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        pair.scale(min(1, 12.4 / pair.width, 6.6 / pair.height)).move_to(ORIGIN)
        self.seq("In code, the call goes in as a lambda. Java's Function has andThen built in. "
                 "Kotlin's function types don't, so you write it in one line.",
                 [(0, [FadeIn(pair, shift=UP * 0.15)], 1.0),
                  (0, [mark(part(jv[0], "() -> issuer.authorize(payment)"), GOLD_M, 0.3), mark(part(kt[0], "{ issuer.authorize(payment) }"), GOLD_M, 0.3)], 1.1),
                  (1, [mark(part(jv[2], ".andThen(loyaltyDiscount)"), WHITE, 0.5)], 1.3),
                  (2, [mark(kt[1], WHITE, 0.8)], 1.6)])
        self.play(FadeOut(pair), run_time=0.6)

        # ---------- the rule, then a check ----------
        rule = VGroup(T("Write the shape of the work once,", 32),
                      T("and pass in the part that changes as a function.", 32)).arrange(DOWN, buff=0.22).move_to([0, 2.55, 0])
        self.beat("The rule: write the shape of the work once, and pass in the part that changes as a function.",
                  FadeIn(rule, shift=UP * 0.1), run_time=1.2)
        tm = RoundedRectangle(corner_radius=0.16, width=6.8, height=2.0, stroke_color=WHITE, stroke_width=3).set_fill(fill_of(WHITE, 0.1), 1)
        tm_t = M('timed("auth", block)', 26, WHITE).move_to(tm.get_top() + DOWN * 0.4)
        tsock = DashedVMobject(RoundedRectangle(corner_radius=0.1, width=5.3, height=0.8, stroke_color=GOLD_M, stroke_width=2.5), num_dashes=34)
        tsock.move_to(tm.get_center() + DOWN * 0.3)
        tq = M("?", 36, GREY_B).move_to(tsock)
        tim = VGroup(tm, tm_t, tsock).move_to([0, -0.6, 0])
        tq.move_to(tsock)
        self.ask("Quick check. timed runs a block and logs how long it took. Is it higher-order?",
                 FadeIn(tim), FadeIn(tq), run_time=0.9)
        blk = tok("issuer.authorize(payment)", GOLD_M, 24).move_to([0, -2.9, 0]).set_z_index(3)
        self.seq("Yes. It takes the block as a function.",
                 [(1, [FadeOut(tq), FadeIn(blk)], 0.4), (1, [blk.animate.move_to(tsock)], 0.8)])
        self.wait(0.8)
