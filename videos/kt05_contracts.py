from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form). Applied in order, before fg's own.
fg.SAY[:0] = [
    (r"\bString\?", "nullable String"), (r"\brequireCurrency\b", "require currency"), (r"\brequireNotNull\b", "require not null"),
    (r"\bClassCastException\b", "class cast exception"), (r"\bjavap\b", "java P"), (r"\bKotlin 2\.4\b", "Kotlin two point four"),
]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

NUL_C, OK_C, BAD_C = GOLD_M, GREEN_M, RED_M   # String? (may be null), a narrowed type, an error
CON_C = YELLOW_M                               # the contract
EYE_C = BLUE_M                                 # what the compiler reads
JVM_C = TEAL_M                                 # the JVM at run time
KT_C = PURPLE_M                                # the Kotlin compiler


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
        """plan: (sentence index, [animations] or a function returning them, run_time)."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), f"plan index past the last sentence: {text[:40]}"
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            if callable(anims):
                anims = anims()
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


class Pulse(Transform):
    """Indicate for outlined shapes: grows and recolours outlines only, so fills and text stay readable."""

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


def one(text, size=24, color=WHITE):
    """One mono line; glyph i is character i (spaces kept, ligatures off)."""
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.remove(t[0])
    t.src = text
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def paint(t, sub, color):
    i = t.src.find(sub)
    while i >= 0:
        VGroup(*t[i:i + len(sub)]).set_color(color)
        i = t.src.find(sub, i + 1)
    return t


def code(lines, size=24):
    """Mono lines, left aligned, leading spaces kept. lines: str or (str, {substring: colour})."""
    pitch = M("|", size).height * 1.6
    g = VGroup()
    for i, ln in enumerate(lines):
        txt, cols = ln if isinstance(ln, tuple) else (ln, {})
        t = Text("|" + txt, font=MONO, font_size=size, disable_ligatures=True)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        t.src = "|" + txt
        for sub, c in cols.items():
            paint(t, sub, c)
        g.add(t)
    for t in g:
        t.remove(t[0])
        t.src = t.src[1:]
    return g


def tag(text, x0, y, maxw):
    """The contract drawn as a yellow tag on the function: a small 'contract' label over a framed line."""
    t = one(text, 22, CON_C)
    fit(t, maxw - 0.3)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.5, stroke_color=CON_C, stroke_width=2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(CON_C), 0.10), 1)
    g = VGroup(r, t)
    g.move_to([x0 + g.width / 2, y, 0])
    t.move_to(r)
    lbl = T("contract", 22, CON_C).next_to(r, UP, buff=0.06).align_to(r, LEFT).shift(RIGHT * 0.05)
    return VGroup(r, t, lbl)


def at_left(m, x, y):
    return m.move_to([x + m.width / 2, y, 0])


# ---- layout: the caller on the left, the function it calls on the right
CA_X0, CA_X1 = -6.4, -1.0
CE_X0, CE_X1 = -0.4, 6.4
BOX_Y0, BOX_Y1 = -0.45, 2.15
L1, L2 = 1.4, 0.35             # line rows inside the boxes
KNOW_Y = -1.2                  # "the compiler knows" row under the caller
ERR_Y = -2.45


def panel(x0, x1, color):
    r = RoundedRectangle(corner_radius=0.14, width=x1 - x0, height=BOX_Y1 - BOX_Y0, stroke_color=color, stroke_width=2.5)
    return r.move_to([(x0 + x1) / 2, (BOX_Y0 + BOX_Y1) / 2, 0])


class Kt05Contracts(Beat):
    """kt-05 s0-1: the compiler smart-casts only from checks it can see, and never opens a function it calls;
    a contract puts the guarantee on the outside, and the compiler trusts it without checking."""

    def construct(self):
        self.title_card("Contracts", "what the compiler can see")

        # ---------------- the problem: your own check function
        ca = panel(CA_X0, CA_X1, GREY_B)
        ce = panel(CE_X0, CE_X1, GREY_B)
        ca_t = T("the caller", 26).next_to(ca, UP, buff=0.25)
        ce_t = one("fun requireCurrency(currency: String?)", 22).next_to(ce, UP, buff=0.15)
        paint(ce_t, "String?", NUL_C)
        c1 = at_left(one("requireCurrency(currency)", 24), CA_X0 + 0.35, L1)
        c2 = at_left(one("currency.uppercase()", 24), CA_X0 + 0.35, L2)
        b2 = at_left(one("if (currency == null) throw ...", 22), CE_X0 + 0.35, L2)
        call = Arrow([CA_X1 - 0.15, L1, 0], [CE_X0 + 0.05, L1, 0], buff=0.05, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.3)
        self.seq("A payment request carries a currency that may be null. You write a small function that throws if it is.",
                 [(0, [Create(ca), FadeIn(ca_t)], 0.8),
                  (1, [Create(ce), FadeIn(ce_t), FadeIn(b2, shift=UP * 0.1)], 1.0)])
        self.seq("Call it, then use the currency on the next line. Does this compile?",
                 [(0, [FadeIn(c1), GrowArrow(call)], 0.8), (0, [FadeIn(c2)], 0.6)], after=1.8)

        know = VGroup(T("the compiler knows:", 24, GREY_B), one("currency: String?", 26)).arrange(RIGHT, buff=0.3)
        paint(know[1], "String?", NUL_C)
        at_left(know, CA_X0 + 0.1, KNOW_Y)
        err = VGroup(one("error: only safe (?.) or non-null asserted (!!.) calls are allowed", 22, BAD_C),
                     one("on a nullable receiver of type 'String?'.", 22, BAD_C)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        fit(err, 12.0).move_to([0, ERR_Y, 0])
        ul = Line(c2.get_corner(DL) + DOWN * 0.08, c2.get_corner(DR) + DOWN * 0.08, stroke_color=BAD_C, stroke_width=4)
        self.seq("No. The compiler still sees a String?, and refuses the call.",
                 [(1, [FadeIn(know, shift=UP * 0.1)], 0.7), (1, [Create(ul), FadeIn(err)], 0.8)])

        # ---------------- why: the compiler reads only the function it compiles
        eye = DashedVMobject(SurroundingRectangle(ca, buff=0.1, corner_radius=0.18, stroke_color=EYE_C, stroke_width=3),
                             num_dashes=60)
        eye_t = T("the compiler reads this function", 26, EYE_C).move_to(ca_t)
        lid = Rectangle(width=CE_X1 - CE_X0 - 0.3, height=0.85, stroke_width=0).set_fill("#2A2A2A", 1).move_to([(CE_X0 + CE_X1) / 2, L2, 0])
        lid_t = T("the compiler doesn't look in here", 24, GREY_A).move_to(lid)
        self.seq("Here's why. The compiler narrows a type, a smart cast, only from checks it can see in the function it is compiling.",
                 [(1, [FadeOut(err), FadeOut(ul), Create(eye), Transform(ca_t, eye_t)], 1.0), (1, [Pulse(know[1], EYE_C, 1.1)], 0.7)])
        self.seq("It never opens the body of a function you call. That body could change, or live in another module.",
                 [(0, [FadeIn(lid, shift=DOWN * 0.3), FadeIn(lid_t)], 0.9)])

        # ---------------- the contract: the guarantee, written on the outside
        con = tag("returns() implies (currency != null)", CE_X0 + 0.2, L1, CE_X1 - CE_X0 - 0.4)
        know2 = one("currency: String", 26)
        paint(know2, "String", OK_C)
        know2.move_to(know[1], aligned_edge=LEFT)
        eye2 = DashedVMobject(SurroundingRectangle(VGroup(con[0], con[2]), buff=0.1, corner_radius=0.12, stroke_color=EYE_C,
                                                   stroke_width=3), num_dashes=40)
        okt = tick(True, 0.25).next_to(c2, RIGHT, buff=0.3)
        self.seq("A contract puts that fact on the outside. It's the first statement of the function: "
                 "returns implies currency is not null.",
                 [(0, [FadeIn(con, shift=DOWN * 0.15), Pulse(ce, CON_C, 1.03)], 1.0),
                  (1, [Indicate(con[1], color=WHITE, scale_factor=1.04)], 1.0)])
        self.seq("The compiler reads the contract, never the body. After the call, currency is a String, and the line compiles. "
                 "That's how require and requireNotNull work.",
                 [(0, [Create(eye2)], 0.9),
                  (1, [Transform(know[1], know2), Create(okt)], 0.8)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- trusted, never checked: a contract that lies
        cb_x1, cb_x0 = -1.25, -0.75           # this part needs a wider function box
        ca_b = panel(CA_X0, cb_x1, GREY_B)
        ce_b = panel(cb_x0, CE_X1, GREY_B)
        ca_t2 = T("the caller", 26).next_to(ca_b, UP, buff=0.25)
        ce_t2 = one("fun PaymentEvent.lyingIsCaptured()", 22).next_to(ce_b, UP, buff=0.15)
        con2 = tag("returns(true) implies (this is Captured)", cb_x0 + 0.2, L1, CE_X1 - cb_x0 - 0.4)
        lie = at_left(one("return true", 24, BAD_C), cb_x0 + 0.35, L2)
        lie_t = T("the lie", 24, BAD_C).next_to(lie, RIGHT, buff=0.4)
        d1 = at_left(one("if (failed.lyingIsCaptured())", 22), CA_X0 + 0.25, L1)
        d2 = at_left(one("  println(failed.amountMinor)", 22), CA_X0 + 0.25, L2)
        self.seq("But nothing checks the contract against the body. The compiler trusts a contract unconditionally.",
                 [(0, [Create(ca_b), Create(ce_b), FadeIn(ca_t2), FadeIn(ce_t2), FadeIn(con2)], 1.0)])
        self.seq("So write one that says: if I return true, this event is Captured. Then make the body always return true.",
                 [(0, [Indicate(con2[1], color=WHITE, scale_factor=1.04)], 1.0), (1, [FadeIn(lie), FadeIn(lie_t)], 0.7)])

        k3 = VGroup(T("the compiler knows:", 24, GREY_B), one("failed: Captured", 26)).arrange(RIGHT, buff=0.3)
        paint(k3[1], "Captured", OK_C)
        at_left(k3, CA_X0 + 0.1, KNOW_Y)
        ok2 = T("compiles, no warning", 26, OK_C).move_to([(cb_x0 + CE_X1) / 2, KNOW_Y, 0])
        jvm = VGroup(T("at run time the JVM checks the cast:", 24, JVM_C),
                     one("class ...Failed cannot be cast to class ...Captured", 22, BAD_C)).arrange(DOWN, buff=0.15)
        jvm.move_to([0, -2.3, 0])
        cce = T("ClassCastException", 26, BAD_C).next_to(jvm, DOWN, buff=0.15)
        self.seq("Call it on a Failed event. It compiles without a warning. Then the JVM checks the cast it was given, "
                 "and throws ClassCastException.",
                 [(0, [FadeIn(d1), FadeIn(d2)], 0.8), (1, [FadeIn(k3, shift=UP * 0.1), FadeIn(ok2)], 0.8),
                  (2, [FadeIn(jvm[0])], 0.6), (2, [FadeIn(jvm[1]), Pulse(part(d2, "failed.amountMinor"), BAD_C, 1.1)], 0.8),
                  (2, [FadeIn(cce, scale=1.2)], 0.6)], after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- one level down: where a contract lives
        cf = RoundedRectangle(corner_radius=0.14, width=6.6, height=4.0, stroke_color=GREY_A, stroke_width=2.5).move_to([2.6, 0.25, 0])
        cf_t = T("the class file", 26, GREY_A).next_to(cf, UP, buff=0.15)
        bc_b = RoundedRectangle(corner_radius=0.1, width=6.0, height=1.6, stroke_color=JVM_C, stroke_width=2).move_to([2.6, 1.15, 0])
        bc = VGroup(T("an honest isCaptured, in javap -c", 22, JVM_C), one("instanceof Captured   ireturn", 22),
                    T("no trace of the contract", 22, GREY_B)).arrange(DOWN, buff=0.12).move_to(bc_b)
        md_b = RoundedRectangle(corner_radius=0.1, width=6.0, height=1.4, stroke_color=KT_C, stroke_width=2).move_to([2.6, -0.8, 0])
        md = VGroup(T("Kotlin metadata", 22, KT_C), one("returns(true) implies ...", 22, CON_C)).arrange(DOWN, buff=0.15).move_to(md_b)
        no_c = bc[2]
        r_x = -4.4
        rk = T("the Kotlin compiler", 24, KT_C).move_to([r_x, -0.8, 0])
        rj = T("javac", 24, GREY_B).move_to([r_x, -2.5, 0])
        rv = T("the JVM at run time", 24, JVM_C).move_to([r_x, 1.15, 0])
        ak = Arrow(rk.get_right(), md_b.get_left(), buff=0.15, stroke_width=3, color=KT_C, max_tip_length_to_length_ratio=0.15)
        av = Arrow(rv.get_right(), bc_b.get_left(), buff=0.15, stroke_width=3, color=JVM_C, max_tip_length_to_length_ratio=0.15)
        aj = DashedLine(rj.get_right() + RIGHT * 0.15, md_b.get_corner(DL) + RIGHT * 0.5 + UP * 0.05, dash_length=0.1,
                        stroke_width=2.5, color=GREY_B)
        xj = tick(False, 0.22).move_to(aj.get_center())
        self.seq("One level down, javap shows no trace of the contract in the bytecode. "
                 "It lives in Kotlin metadata, which only the Kotlin compiler reads. Java callers never see it.",
                 [(0, [Create(cf), FadeIn(cf_t), Create(bc_b), FadeIn(bc[:2])], 0.9), (0, [FadeIn(no_c)], 0.5),
                  (1, [Create(md_b), FadeIn(md)], 0.8), (1, [FadeIn(rk), GrowArrow(ak), FadeIn(rv), GrowArrow(av)], 0.9),
                  (2, [FadeIn(rj), Create(aj), Create(xj)], 0.8)], after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- the code (Kotlin only)
        head = T("Kotlin only", 26, GREY_B)
        kc = code([("@OptIn(ExperimentalContracts::class)", {"@OptIn(ExperimentalContracts::class)": GREY_B}),
                   ("fun requireCurrency(currency: String?) {", {"String?": NUL_C}),
                   ("    contract { returns() implies (currency != null) }", {"contract { returns() implies (currency != null) }": CON_C}),
                   ('    if (currency == null) throw IllegalArgumentException("currency missing")', {}),
                   ("}", {}), ("", {}),
                   ("requireCurrency(currency)", {}),
                   ("println(currency.uppercase())     // compiles: currency is a String", {"// compiles: currency is a String": OK_C})], 22)
        notes = VGroup(T("Java's types don't track null, so Java has no smart cast to give and no contracts.", 22, GREY_B),
                       T("Contracts are still Experimental in Kotlin 2.4: opt in with @OptIn.", 22, GREY_B)).arrange(DOWN, buff=0.12)
        blk = VGroup(head, kc).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        allg = VGroup(blk, notes).arrange(DOWN, buff=0.5)
        fit(allg, 12.4).move_to([0, 0.1, 0])
        self.seq("Contracts are Kotlin only, and still Experimental in Kotlin 2.4, so you opt in. "
                 "Java doesn't track null in its types, so the question never comes up there.",
                 [(0, [FadeIn(blk, shift=UP * 0.1)], 1.0), (0, [FadeIn(notes[1])], 0.6), (1, [FadeIn(notes[0])], 0.6)], after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- rule and check
        rule = VGroup(T("The compiler learns only from what it can see.", 32),
                      T("A contract tells it what a function guarantees,", 32, CON_C),
                      T("and it believes you without checking.", 32, CON_C)).arrange(DOWN, buff=0.22).move_to([0, 1.8, 0])
        fit(rule, 12.4)
        self.seq("The rule: the compiler learns only from what it can see. A contract tells it what a function guarantees, "
                 "and it believes you without checking. So keep the body as small as the promise.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7),
                  (1, [FadeIn(rule[2], shift=UP * 0.1)], 0.7)])
        chk = VGroup(T("Check: requireCurrency now logs a warning instead of throwing,", 28),
                     T("and keeps its contract. Does the caller still compile?", 28)).arrange(DOWN, buff=0.12).move_to([0, -0.75, 0])
        fit(chk, 12.4)
        self.seq("Quick check. You change requireCurrency to log a warning instead of throwing, and keep the contract. "
                 "Does the caller still compile?",
                 [(1, [FadeIn(chk, shift=UP * 0.1)], 0.8)], after=2.0)
        ans = VGroup(T("Yes. The compiler reads the contract, never the body.", 28, CON_C),
                     T("The promise is now a lie, and a null reaches the next line at run time.", 28, CON_C)).arrange(DOWN, buff=0.12)
        ans.move_to([0, -2.55, 0])
        fit(ans, 12.4)
        self.seq("Yes. The compiler reads the contract, never the body. The promise is now a lie, "
                 "and a null reaches the next line at run time.",
                 [(0, [FadeIn(ans[0], shift=UP * 0.1)], 0.6), (2, [FadeIn(ans[1], shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
