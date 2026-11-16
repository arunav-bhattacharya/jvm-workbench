from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"new AdyenGateway\(\)", "new Adyen gateway"), (r"\bAdyenGateway\b", "Adyen gateway"), (r"\bFakeGateway\b", "fake gateway"),
           (r"\bAdyen\b", "Ad-yen"), (r"\bAMEX\b", "Amex"), (r"\bclientsFor\b", "clients for"),
           (r"\bCardNetworkClients\b", "card network clients"), (r"\bswitch\b", "switch")]

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




CALL_C, FAC_C, ERR_C, OK_C = WHITE, YELLOW_M, RED_M, GREEN_M          # the caller, the factory, refusal, match
ADY_C, STR_C, FAKE_C = GREEN_M, PURPLE_M, GREY_B                      # three gateway classes
VISA_C, MC_C = BLUE_M, GOLD_M                                         # two card network families


def pbox(label, color, w=3.2, h=0.85, size=26, mono=True):
    t = (M if mono else T)(label, size, color)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    return VGroup(r, t.move_to(r))


def prod(family, name, color, w=2.5, h=0.9):
    """A product box: its family on top, small, and what it is below."""
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = VGroup(T(family, 20, color), T(name, 26, color)).arrange(DOWN, buff=0.04).move_to(r)
    return VGroup(r, t)


def slot(w, h):
    r = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=w, height=h), num_dashes=40)
    return r.set_stroke(GREY_B, 2)


def run_dot(a, b, color, run_time=0.8):
    """A dot that runs from point a to point b and is gone before and after."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = Dot(radius=0.11, color=color).move_to(a).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(a + (b - a) * smooth(t))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time, rate_func=linear)


class Pat02Factory(Beat):
    """pat-02 sections 1 and 3: the caller asks for "a gateway" and a factory picks the class
    (Factory Method, now a function); when products must match, one factory makes the whole family (Abstract Factory)."""

    def construct(self):
        self.title_card("Ask for a product, not a class", "Factory Method and Abstract Factory")

        # ---------- the problem: the caller names the class
        chk = pbox("Checkout", CALL_C, w=2.8, h=1.1, size=30).move_to([-4.8, 0.3, 0])
        prods = [pbox("AdyenGateway", ADY_C), pbox("StripeGateway", STR_C), pbox("FakeGateway", FAKE_C)]
        for p, y in zip(prods, [1.6, 0.3, -1.0]):
            p.move_to([4.4, y, 0])
        ADY, STR, FAKE = prods
        fam = DashedVMobject(SurroundingRectangle(VGroup(*prods), buff=0.25, corner_radius=0.16), num_dashes=70).set_stroke(GREY_B, 2)
        fam_l = M("PaymentGateway", 24, GREY_B).next_to(fam, UP, buff=0.15)
        wire = Arrow(chk.get_right(), ADY[0].get_left(), buff=0.1, stroke_width=4, color=WHITE, max_tip_length_to_length_ratio=0.06)
        wire_l = M("new AdyenGateway()", 26, ADY_C).move_to([-0.4, 1.75, 0])
        self.seq("Checkout needs a payment gateway to charge a card. The simple way is to build one right there: new AdyenGateway().",
                 [(0, [FadeIn(chk, shift=RIGHT * 0.15)], 0.7),
                  (0, [Create(fam), FadeIn(fam_l), LaggedStart(*[FadeIn(p) for p in prods], lag_ratio=0.3)], 1.0),
                  (1, [GrowArrow(wire), FadeIn(wire_l)], 0.9)])

        self.seq("Now a test needs a fake gateway, and a new tenant uses Stripe. Which code has to change?",
                 [(0, [Pulse(FAKE[0], FAKE_C, 1.06)], 0.8), (0, [Pulse(STR[0], STR_C, 1.06)], 0.8)], after=1.6)

        self.seq("Checkout itself. It named the class, so the choice is welded into it.",
                 [(0, [Pulse(chk[0], ERR_C, 1.06)], 0.8), (1, [wire.animate.set_color(ERR_C), wire_l.animate.set_color(ERR_C)], 0.6)])

        # ---------- ask for a gateway; a factory picks the class
        fac = pbox("factory", FAC_C, w=2.4, h=1.1, size=30, mono=False).move_to([-0.2, 0.3, 0])
        fac_t = M("() -> PaymentGateway", 24, FAC_C).next_to(fac, DOWN, buff=0.22)
        ask = Arrow(chk.get_right(), fac[0].get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.18)
        ask_l = T("a gateway?", 24, GREY_B).next_to(ask, UP, buff=0.12)

        def pick(p):
            return Line(fac[0].get_right(), p[0].get_left(), stroke_width=3, color=FAC_C)

        pk = pick(ADY)
        self.seq("So take the choice out. Checkout asks for a gateway, and never names a class. Something else decides which one it gets.",
                 [(0, [FadeOut(wire), FadeOut(wire_l)], 0.5),
                  (1, [GrowArrow(ask), FadeIn(ask_l)], 0.7), (2, [FadeIn(fac, scale=0.9), FadeIn(fac_t)], 0.7)])

        def hand_back(p, color):
            c = chip("a PaymentGateway", color, size=22, mono=False).move_to(p[0].get_left()).set_z_index(20)
            path = VMobject().set_points_as_corners([p[0].get_left(), fac[0].get_center(), [-4.8, -0.85, 0]])
            return c, MoveAlongPath(c, path, rate_func=smooth)

        c1, mv1 = hand_back(ADY, ADY_C)
        c2, mv2 = hand_back(FAKE, FAKE_C)
        self.seq("That something is a factory. In production it builds an AdyenGateway. In a test it builds a FakeGateway. "
                 "Checkout doesn't change.",
                 [(0, [Pulse(fac[0], FAC_C, 1.06)], 0.7),
                  (1, [Create(pk)], 0.5), (1, [Pulse(ADY[0], ADY_C, 1.06)], 0.5), (1, [mv1], 1.1),
                  (2, lambda: [FadeOut(c1), Transform(pk, pick(FAKE))], 0.6), (2, [Pulse(FAKE[0], FAKE_C, 1.06)], 0.5),
                  (2, [mv2], 1.1),
                  (3, [Pulse(chk[0], OK_C, 1.06)], 0.8)])

        jl = VGroup(T("Java", 24, GREY_B), M("new Checkout(FakeGateway::new);", 26, WHITE)).arrange(RIGHT, buff=0.35)
        kl = VGroup(T("Kotlin", 24, GREY_B), M("Checkout(::FakeGateway)", 26, WHITE)).arrange(RIGHT, buff=0.35)
        codes = VGroup(jl, kl).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([0, -2.75, 0])
        self.seq("The Design Patterns book calls this Factory Method: a subclass overrides one create method. "
                 "Since Java 8, a plain function does the same job. A Supplier in Java, a function type in Kotlin, often a constructor reference.",
                 [(1, [Indicate(fac_t, color=WHITE, scale_factor=1.1)], 0.9),
                  (2, [FadeIn(jl, shift=UP * 0.1)], 0.6), (2, [FadeIn(kl, shift=UP * 0.1)], 0.6)], after=0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- products that must match: a family
        COLX = [1.2, 4.4]
        fams = []
        for name, col, x in [("Visa", VISA_C, COLX[0]), ("Mastercard", MC_C, COLX[1])]:
            a = prod(name, "authorizer", col).move_to([x, 0.55, 0])
            r = prod(name, "refunder", col).move_to([x, -0.55, 0])
            h = T(name, 28, col).move_to([x, 1.45, 0])
            fams.append(VGroup(h, a, r))
        (vh, va, vr), (mh, ma, mr) = fams
        site = RoundedRectangle(corner_radius=0.16, width=3.5, height=2.6, stroke_color=CALL_C, stroke_width=3).set_fill(BLACK, 1)
        site.move_to([-4.6, 0, 0])
        site_l = T("a call site", 28, CALL_C).next_to(site, UP, buff=0.18)
        sa, sr = slot(2.8, 0.98).move_to([-4.6, 0.55, 0]), slot(2.8, 0.98).move_to([-4.6, -0.55, 0])
        sa_l = T("authorizer", 22, GREY_B).move_to(sa)
        sr_l = T("refunder", 22, GREY_B).move_to(sr)
        self.seq("Now some products must match. A card network gives you an authorizer and a refunder. "
                 "A Visa auth code means nothing to Mastercard's refund endpoint.",
                 [(0, [FadeIn(vh, shift=DOWN * 0.1), FadeIn(mh, shift=DOWN * 0.1)], 0.7),
                  (1, [FadeIn(fams[0][1:], shift=LEFT * 0.15)], 0.7), (1, [FadeIn(fams[1][1:], shift=LEFT * 0.15)], 0.7),
                  (2, [run_dot(va.get_right() + RIGHT * 0.05, mr.get_left() + LEFT * 0.05, VISA_C, 0.9)], 0.9),
                  (2, [Flash(mr.get_left(), color=ERR_C, flash_radius=0.35)], 0.5)])

        ga, gr = va.copy(), mr.copy()
        bad = tick(False, 0.26).move_to([-4.6, -1.65, 0])
        self.seq("If every call site picks its own pair, one day a path that runs once a month takes a Visa authorizer "
                 "and a Mastercard refunder. Its Visa auth code goes to Mastercard, where it means nothing.",
                 [(0, [FadeIn(site), FadeIn(site_l), Create(sa), Create(sr), FadeIn(sa_l), FadeIn(sr_l)], 0.8),
                  (0, [FadeOut(sa_l), ga.animate.move_to(sa)], 1.0), (0, [FadeOut(sr_l), MoveAlongPath(gr, VMobject().set_points_as_corners([gr.get_center(), [COLX[1], -1.75, 0], [-1.6, -1.75, 0], sr.get_center()]), rate_func=smooth)], 1.3),
                  (1, [run_dot(sa.get_bottom(), sr.get_top(), VISA_C, 0.6)], 0.6),
                  (1, [Flash(sr.get_top(), color=ERR_C, flash_radius=0.4), FadeIn(bad, scale=0.5)], 0.6)])

        # the family behind one interface, picked once
        boxes = VGroup(*[SurroundingRectangle(VGroup(f[1], f[2]), buff=0.2, corner_radius=0.16, color=f[0].get_color(), stroke_width=2.5)
                         for f in fams])
        iface = M("CardNetworkClients", 26, FAC_C).move_to([(COLX[0] + COLX[1]) / 2, 2.35, 0])
        menu = VGroup(M("authorizer()", 22, FAC_C), M("refunder()", 22, FAC_C)).arrange(RIGHT, buff=0.5).next_to(iface, DOWN, buff=0.12)
        self.seq("Abstract Factory puts that choice in one place. One interface makes every product of the family, "
                 "with one implementation per family.",
                 [(0, [FadeOut(ga), FadeOut(gr), FadeOut(bad), FadeIn(sa_l), FadeIn(sr_l)], 0.6),
                  (1, [FadeIn(iface, shift=DOWN * 0.1), FadeIn(menu, shift=DOWN * 0.1)], 0.7),
                  (1, [Create(boxes[0]), Create(boxes[1])], 0.9)])

        call = M("clientsFor(card.network)", 24, FAC_C).move_to([-4.6, -2.45, 0])
        ask2 = Arrow(site.get_right(), boxes[0].get_left(), buff=0.12, stroke_width=3, color=FAC_C, max_tip_length_to_length_ratio=0.15)
        ga2, gr2 = va.copy(), vr.copy()
        good = tick(True, 0.26).move_to([-4.6, -1.65, 0])
        self.seq("The call site asks for the family once, and takes both products from it. "
                 "It can't mix families, because it never picks a product itself.",
                 [(0, [FadeIn(call, shift=UP * 0.1), GrowArrow(ask2)], 0.8), (0, [Pulse(boxes[0], VISA_C, 1.04)], 0.7),
                  (0, [FadeOut(sa_l), ga2.animate.move_to(sa)], 0.9), (0, [FadeOut(sr_l), gr2.animate.move_to(sr)], 0.9),
                  (1, [run_dot(sa.get_bottom(), sr.get_top(), VISA_C, 0.6)], 0.6), (1, [FadeIn(good, scale=0.5)], 0.4)])

        # the cost: a new product touches every family
        new_t = [prod(n, "tokenizer", c).move_to([x, -1.65, 0])
                 for n, c, x in [("Visa", VISA_C, COLX[0]), ("Mastercard", MC_C, COLX[1])]]
        tok_m = M("tokenizer()", 22, ERR_C).next_to(menu, RIGHT, buff=0.5)
        note1 = T("new family: one more class", 26, GREY_A).move_to([-3.2, -3.0, 0])
        note2 = T("new product: every family changes", 26, ERR_C).move_to([3.1, -3.0, 0])
        self.seq("The cost runs one way. A new family is one more implementation. "
                 "A new product, say a Tokenizer, changes the interface and every family.",
                 [(0, [FadeOut(call), FadeOut(ask2), FadeOut(good)], 0.5),
                  (1, [FadeIn(note1, shift=UP * 0.1)], 0.6),
                  (2, [VGroup(iface, menu).animate.shift(LEFT * 0.9)], 0.5),
                  (2, lambda: [FadeIn(tok_m.next_to(menu, RIGHT, buff=0.5), shift=LEFT * 0.1),
                               *[b.animate.stretch_to_fit_height(b.height + 1.1).shift(DOWN * 0.55) for b in boxes]], 0.8),
                  (2, [LaggedStart(*[FadeIn(t, shift=UP * 0.15) for t in new_t], lag_ratio=0.4), FadeIn(note2, shift=UP * 0.1)], 0.9)],
                 after=0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- the code
        kl = code(["interface CardNetworkClients {",
                   "    fun authorizer(): Authorizer",
                   "    fun refunder(): Refunder",
                   "}",
                   "val c = clientsFor(card.network)"], 22)
        jl = code(["interface CardNetworkClients {",
                   "    Authorizer authorizer();",
                   "    Refunder refunder();",
                   "}",
                   "var c = clientsFor(card.network());"], 22)
        for ln in [*kl, *jl]:
            paint(ln, "CardNetworkClients", FAC_C); paint(ln, "clientsFor", FAC_C)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(RIGHT, buff=0.9, aligned_edge=UP).move_to([0, 0.4, 0])
        fit(both, 12.4)
        self.seq("In code, the family is one interface with one method per product. A caller gets it from one factory call.",
                 [(0, [FadeIn(jg, shift=UP * 0.15), FadeIn(kg, shift=UP * 0.15)], 0.8),
                  (1, [mark(part(jl[4], "clientsFor(card.network())"), FAC_C, 0.4), mark(part(kl[4], "clientsFor(card.network)"), FAC_C, 0.4)], 1.2)],
                 after=0.6)
        self.play(FadeOut(both), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("The caller asks for what it needs, and never names the class.", 32),
                      T("When products must match, one choice picks the whole family.", 32, FAC_C)).arrange(DOWN, buff=0.3).move_to([0, 1.9, 0])
        fit(rule, 12.4)
        self.seq("The rule. The caller asks for what it needs, and never names the class. "
                 "When products must match, one choice picks the whole family.",
                 [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        q = VGroup(T("Check: card ops adds AMEX to the network enum.", 28),
                   T("Where does the build fail? Which callers change?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.3, 0])
        self.seq("Quick check. Card ops adds AMEX to the network enum. Where does the build fail, and which callers change?",
                 [(0, [FadeIn(q, shift=UP * 0.1)], 0.8)], after=2.4)
        ans = VGroup(T("In the factory's switch: it has no default branch.", 28, OK_C),
                     T("No caller changes: callers only ask for a family.", 28, OK_C)).arrange(DOWN, buff=0.2).move_to([0, -2.3, 0])
        self.seq("It fails in the factory's switch, because it has no default branch, so you add an Amex branch there. "
                 "No caller changes. Callers only ask for a family.",
                 [(0, [FadeIn(ans[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(ans[1], shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
