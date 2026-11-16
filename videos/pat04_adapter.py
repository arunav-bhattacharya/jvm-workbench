from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bIOException\b", "I O exception"), (r"\bGatewayUnavailable\b", "gateway unavailable"),
           (r"\bXML\b", "X M L"), (r"\bSDK\b", "S D K"), (r"\bREST\b", "rest")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")



class Beat(VoiceScene):
    """VoiceScene plus captions split only where a new sentence starts, and seq() to start animations
    at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def seq(self, text, plan=(), after=0.25):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), "plan index past the last sentence"
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


class Pulse(Transform):
    """Indicate for filled chips: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.08, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
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
    """Glyphs of substring sub in a line from one()/code() (ligatures off: string index = glyph index)."""
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def paint(t, sub, color):
    """Colour every occurrence of sub in line t."""
    i = t.src.find(sub)
    while i >= 0:
        VGroup(*t[i:i + len(sub)]).set_color(color)
        i = t.src.find(sub, i + 1)
    return t


def mark(m, color=WHITE, hold=0.6):
    """Underline a few glyphs, then fade the line out."""
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))




OUR_C, VEN_C, ADP_C, ERR_C, FAC_C = BLUE_M, GOLD_M, GREEN_M, RED_M, YELLOW_M   # your code, the vendor, the adapter, a failure, the facade
INV_C, PAY_C, NOT_C = TEAL_M, BLUE_M, PURPLE_M                               # three subsystems behind the facade


def tint(m, color, k=0.14):
    return m.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), k), opacity=1).set_stroke(color, 3)


# ---- adapter layout: your code, the adapter's gap, the vendor; requests run above, answers below
BY, BH, SW, AW = 0.35, 1.5, 3.2, 2.4
SX, VX = -(AW / 2 + SW / 2), AW / 2 + SW / 2          # centres of your code and of the vendor when the adapter sits between
PEG_W, PEG_H, SOCK_R = 0.5, 0.56, 0.3
REQ_Y, RES_Y = BY + BH / 2 + 0.55, BY - BH / 2 - 0.55


def service_shape():
    body = Rectangle(width=SW, height=BH).move_to([SX, BY, 0])
    peg = Rectangle(width=PEG_W + 0.02, height=PEG_H).move_to([SX + SW / 2 + PEG_W / 2 - 0.01, BY, 0])
    return tint(Union(body, peg), OUR_C)


def vendor_shape():
    body = Rectangle(width=SW, height=BH).move_to([VX, BY, 0])
    hole = Circle(radius=SOCK_R).move_to([VX - SW / 2, BY, 0])
    return tint(Difference(body, hole), VEN_C)


def adapter_shape():
    body = Rectangle(width=AW, height=BH * 0.86).move_to([0, BY, 0])
    notch = Rectangle(width=PEG_W * 2, height=PEG_H + 0.04).move_to([-AW / 2, BY, 0])
    knob = Circle(radius=SOCK_R - 0.03).move_to([AW / 2, BY, 0])
    return tint(Union(Difference(body, notch), knob), ADP_C)


def token(text, color, size=22):
    return chip(text, color, size=size, mono=True).set_z_index(20)


def sbox(name, color, w=2.8, h=0.9, size=26):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h)
    tint(r, color)
    return VGroup(r, T(name, size, color).move_to(r))


class Pat04Adapter(Beat):
    """pat-04 sections 0 and 2: an adapter has your port's shape on one side and the vendor's on the other,
    and translates calls, answers and errors both ways; a facade is one front door that owns the order of the steps
    and what each failure means."""

    def construct(self):
        self.title_card("Fit their shape, hide the steps", "Adapter and Facade")

        # ---------- two shapes that don't fit
        svc = service_shape()
        svc_t = T("your code", 28, OUR_C).move_to([SX - 0.15, BY, 0])
        port = M("charge(amount, currency, token)", 22, OUR_C).move_to([SX, 2.75, 0])
        port_n = T("your port", 24, OUR_C).next_to(port, UP, buff=0.12)
        self.seq("Your payment code expects one shape. charge, with an amount, a currency and a token, gives back a reference. "
                 "That shape is your port.",
                 [(0, [FadeIn(svc), FadeIn(svc_t)], 0.8), (1, [FadeIn(port, shift=DOWN * 0.1)], 0.7),
                  (2, [FadeIn(port_n), Indicate(svc_t, color=WHITE, scale_factor=1.08)], 0.8)])

        ven = vendor_shape()
        ven_t = M("LegacySoapClient", 22, VEN_C).move_to([VX + 0.15, BY, 0])
        api = M("submitTxn(xml): xml", 22, VEN_C).move_to([VX, 2.75, 0])
        api_n = T("the issuer's SDK", 24, VEN_C).next_to(api, UP, buff=0.12)
        api_e = M("throws IOException", 22, VEN_C).move_to([VX, -1.75, 0])
        self.seq("The issuer's SDK has another shape. It takes an XML string, answers in XML, and throws IOException. "
                 "You can't change it.",
                 [(0, [FadeIn(ven), FadeIn(ven_t), FadeIn(api_n)], 0.8), (1, [FadeIn(api, shift=DOWN * 0.1)], 0.7),
                  (1, [FadeIn(api_e, shift=UP * 0.1)], 0.6)])

        push = AW - PEG_W - 0.02
        ven_g = VGroup(ven, ven_t)
        self.seq("Push them together. They don't fit.",
                 [(0, [ven_g.animate.shift(LEFT * push)], 0.8),
                  (1, [Flash(np.array([SX + SW / 2 + PEG_W, BY, 0]), color=ERR_C, flash_radius=0.5)], 0.6),
                  (1, lambda: [ven_g.animate.shift(RIGHT * push)], 0.6)])   # built late: it must start from the pushed place

        adp = adapter_shape()
        adp_t = T("adapter", 28, ADP_C).move_to([0.2, BY, 0])
        adp_g = VGroup(adp, adp_t).shift(DOWN * 3.2)
        self.seq("So put a piece in between, with your shape on one side and theirs on the other. That piece is an adapter.",
                 [(0, [FadeIn(adp_g)], 0.4), (0, [adp_g.animate.shift(UP * 3.2)], 1.1),
                  (0, [Flash(np.array([SX + SW / 2 + PEG_W / 2, BY, 0]), color=ADP_C, flash_radius=0.45),
                       Flash(np.array([AW / 2, BY, 0]), color=ADP_C, flash_radius=0.45)], 0.6),
                  (1, [Indicate(adp_t, color=WHITE, scale_factor=1.1)], 0.8)])

        # ---------- one call, both ways
        req = token("1250, EUR, tok_1", OUR_C).move_to([SX, REQ_Y, 0])
        xml = token("<txn amt='1250' .../>", VEN_C).move_to([0, REQ_Y, 0])
        resp = token("<ok ref='R-77'/>", VEN_C).move_to([VX, RES_Y, 0])
        ref = token("\"R-77\"", OUR_C).move_to([0, RES_Y, 0])
        self.seq("Follow one call. Your amount, currency and token go in, and the adapter writes the XML the vendor wants. "
                 "The answer comes back as XML, and the adapter hands you only the reference.",
                 [(0, [FadeIn(req, shift=DOWN * 0.1)], 0.5), (1, [req.animate.move_to([0, REQ_Y, 0])], 0.8),
                  (1, [ReplacementTransform(req, xml)], 0.6), (1, [xml.animate.move_to([VX, REQ_Y, 0])], 0.8),
                  (2, [FadeOut(xml), FadeIn(resp, shift=UP * 0.1)], 0.5), (2, [resp.animate.move_to([0, RES_Y, 0])], 0.8),
                  (2, [ReplacementTransform(resp, ref)], 0.6), (2, [ref.animate.move_to([SX, RES_Y, 0])], 0.8)])

        ioe = token("IOException", ERR_C).move_to([VX, RES_Y, 0])
        gu = token("GatewayUnavailable", OUR_C).move_to([0, RES_Y, 0])
        self.seq("Errors get translated too. The vendor throws IOException, and the adapter throws your own GatewayUnavailable.",
                 [(0, [FadeOut(ref)], 0.4), (1, [FadeIn(ioe, scale=0.8)], 0.4), (1, [ioe.animate.move_to([0, RES_Y, 0])], 0.8),
                  (1, [ReplacementTransform(ioe, gu)], 0.6), (1, [gu.animate.move_to([SX, RES_Y, 0])], 0.8)])

        self.seq("What if the adapter let IOException through?", [(0, [FadeOut(gu)], 0.4)], after=1.4)

        leak = token("IOException", ERR_C).move_to([VX, RES_Y, 0])
        self.seq("Then your code depends on the vendor, and a new issuer means changing every caller. "
                 "That's a leaky adapter, the most common adapter bug.",
                 [(0, [FadeIn(leak, scale=0.8)], 0.3), (0, [leak.animate.move_to([SX, RES_Y, 0])], 1.4),
                  (0, [svc.animate.set_stroke(ERR_C), svc_t.animate.set_color(ERR_C)], 0.5),
                  (1, [Indicate(adp_t, color=ERR_C, scale_factor=1.1)], 0.8)], after=0.5)
        self.play(FadeOut(VGroup(svc, svc_t, port, port_n, ven, ven_t, api, api_n, api_e, adp, adp_t, leak)), run_time=0.6)

        # ---------- the adapter in code
        jl = code(["record SoapGatewayAdapter(LegacySoapClient soap)",
                   "        implements PaymentGateway { ...",
                   "    catch (IOException e) { throw new GatewayUnavailable(...); }"], 24)
        kl = code(["class SoapGatewayAdapter(private val soap: LegacySoapClient)",
                   "        : PaymentGateway { ...",
                   "    catch (e: IOException) { throw GatewayUnavailable(...) }"], 24)
        for ln in [*jl, *kl]:
            paint(ln, "PaymentGateway", OUR_C); paint(ln, "GatewayUnavailable", OUR_C)
            paint(ln, "LegacySoapClient", VEN_C); paint(ln, "IOException", ERR_C)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.6, aligned_edge=LEFT).move_to([0, 0.2, 0])
        fit(both, 12.4)
        self.seq("In Java, the port doesn't declare IOException, so javac won't let it escape. "
                 "Kotlin has no checked exceptions, so the same leak compiles without a word.",
                 [(0, [FadeIn(jg, shift=UP * 0.15)], 0.7), (0, [mark(part(jl[2], "IOException"), ERR_C, 0.6)], 1.2),
                  (1, [FadeIn(kg, shift=UP * 0.15)], 0.7), (1, [mark(part(kl[2], "IOException"), ERR_C, 0.6)], 1.2)], after=0.5)
        self.play(FadeOut(both), run_time=0.6)

        # ---------- the facade: one front door
        CX, SBX, ROWS = -4.7, 4.9, [1.7, 0.0, -1.7]
        callers = [sbox(n, WHITE, w=3.0, h=0.85) .move_to([CX, y, 0]) for n, y in zip(["REST resource", "Kafka consumer", "admin tool"], ROWS)]
        subs = [sbox(n, c, w=2.6, h=0.85).move_to([SBX, y, 0]) for n, c, y in zip(["Inventory", "Payments", "Notifier"], [INV_C, PAY_C, NOT_C], ROWS)]
        steps = [M(s, 22, c).next_to(b, DOWN, buff=0.1) for s, c, b in zip(["reserve", "charge", "send"], [INV_C, PAY_C, NOT_C], subs)]
        self.seq("Now a different problem. Checkout is three steps: reserve the stock, charge the card, send a receipt.",
                 [(1, [LaggedStart(*[FadeIn(VGroup(b, s), shift=LEFT * 0.15) for b, s in zip(subs, steps)], lag_ratio=0.5)], 1.6)])

        wires = VGroup(*[Line(c[0].get_right(), s[0].get_left(), stroke_width=2, color=GREY_B) for c in callers for s in subs])
        bad = VGroup(Line(callers[2][0].get_right(), subs[1][0].get_left(), stroke_width=4, color=ERR_C),
                     Line(callers[2][0].get_right(), subs[0][0].get_left(), stroke_width=4, color=ERR_C))
        oops = T("charges first, reserves second", 24, ERR_C).next_to(callers[2], DOWN, buff=0.25)
        self.seq("The REST resource, the Kafka consumer and the admin tool each make those calls themselves, "
                 "and each gets the order a little different. One charges before it reserves, and takes money for stock you don't have.",
                 [(0, [LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in callers], lag_ratio=0.3)], 0.9),
                  (0, [LaggedStart(*[Create(w) for w in wires], lag_ratio=0.08)], 1.4),
                  (1, [Create(bad[0])], 0.6), (1, [Create(bad[1]), FadeIn(oops, shift=UP * 0.1)], 0.6),
                  (1, [Indicate(callers[2][1], color=ERR_C, scale_factor=1.1)], 0.8)])

        fac = sbox("CheckoutFacade", FAC_C, w=3.0, h=1.3, size=28).move_to([0.2, 0, 0])
        fac_m = M("checkout()", 22, FAC_C).next_to(fac[1], DOWN, buff=0.1)
        VGroup(fac[1], fac_m).move_to(fac[0])
        ins = VGroup(*[Arrow(c[0].get_right(), fac[0].get_left(), buff=0.1, stroke_width=3, color=FAC_C,
                             max_tip_length_to_length_ratio=0.12) for c in callers])
        outs = VGroup(*[Arrow(fac[0].get_right(), s[0].get_left(), buff=0.1, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.15) for s in subs])
        self.seq("A facade gives them one front door. Each caller makes one call, checkout, and the steps move behind the door.",
                 [(0, [FadeOut(wires), FadeOut(bad), FadeOut(oops), FadeIn(fac, scale=0.9), FadeIn(fac_m)], 0.9),
                  (1, [LaggedStart(*[GrowArrow(a) for a in ins], lag_ratio=0.25)], 0.9),
                  (1, [LaggedStart(*[GrowArrow(a) for a in outs], lag_ratio=0.25)], 0.9)])

        nums = [T(str(i + 1), 26, FAC_C).move_to(a.point_from_proportion(0.5) + (UP * 0.3 if i < 2 else DOWN * 0.3)) for i, a in enumerate(outs)]
        self.seq("The facade owns the order. Reserve, then charge, then send the receipt.",
                 [(1, [FadeIn(nums[0]), outs[0].animate.set_color(FAC_C), Indicate(steps[0], color=WHITE)], 0.7),
                  (1, [FadeIn(nums[1]), outs[1].animate.set_color(FAC_C), Indicate(steps[1], color=WHITE)], 0.7),
                  (1, [FadeIn(nums[2]), outs[2].animate.set_color(FAC_C), Indicate(steps[2], color=WHITE)], 0.7)])

        rel_l = M("release", 22, FAC_C).next_to(subs[0][0], UP, buff=0.1)
        undo = CurvedArrow(fac[0].get_top() + RIGHT * 0.6, subs[0][0].get_left() + UP * 0.2, angle=-TAU / 8,
                           color=FAC_C, stroke_width=3, tip_length=0.18)
        self.seq("And it owns what each failure means. If the card is declined, it releases the reservation.",
                 [(1, [Flash(subs[1][0].get_left(), color=ERR_C, flash_radius=0.4), subs[1][0].animate.set_stroke(ERR_C)], 0.6),
                  (1, [Create(undo)], 0.9), (1, [FadeIn(rel_l, shift=DOWN * 0.1)], 0.5)], after=0.6)
        self.play(FadeOut(VGroup(*callers, *subs, *steps, fac, fac_m, ins, outs, *nums, undo, rel_l)), run_time=0.7)

        # ---------- the rule and a check
        rule = VGroup(T("An adapter makes a class you can't change fit your port, both ways.", 30, ADP_C),
                      T("A facade gives callers one door, and owns the steps behind it.", 30, FAC_C)).arrange(DOWN, buff=0.3).move_to([0, 1.9, 0])
        fit(rule, 12.4)
        self.seq("The rule. An adapter makes a class you can't change fit your port, both ways. "
                 "A facade gives callers one door, and owns the steps behind it.",
                 [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        q = VGroup(T("Check: the charge fails after the stock is reserved.", 28),
                   T("Which class releases the stock?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.3, 0])
        self.seq("Quick check. The charge fails after the stock is reserved. Which class releases the stock?",
                 [(0, [FadeIn(q, shift=UP * 0.1)], 0.8)], after=2.0)
        ans = T("The facade. The callers never see the steps.", 30, FAC_C).move_to([0, -2.1, 0])
        self.seq("The facade. The callers never see the steps.", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)
