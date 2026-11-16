from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form). Applied in order, before fg's own.
fg.SAY[:0] = [
    (r"minor;currency", "minor, semicolon, currency"), (r"\bhashCode\b", "hash code"), (r"\btoString\b", "to string"),
    (r"\bList\.copyOf\b", "List dot copy of"), (r"\bHashSet\b", "hash set"), (r"\bpay_3\b", "pay 3"),
    (r"\beur becomes EUR\b", "lower case E U R becomes upper case E U R"), (r"\bEUR\b", "E U R"),
]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

MIN_C, CUR_C = BLUE_M, TEAL_M      # the two components of Money
REC_C = YELLOW_M                   # the record header and what javac writes from it
DOOR_C = GOLD_M                    # the canonical constructor and its check
LIST_C = PURPLE_M                  # the caller's mutable list
BAD_C, OK_C = RED_M, GREEN_M


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


def one(text, size=26, color=WHITE):
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


def comp(name, color, size=24):
    return chip(name, color, size, mono=True)


def hole(w, color=BAD_C):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=0.62, stroke_color=color, stroke_width=2)
    return DashedVMobject(r, num_dashes=22)


# ---- layout
ROWS = ["fields", "accessors", "constructor", "equals", "hashCode", "toString"]
RY = [1.8, 1.08, 0.36, -0.36, -1.08, -1.8]
PX0, PX1 = -6.3, -0.4
LBL_X, MIN_X, CUR_X = -6.0, -3.0, -1.5

DOOR = np.array([2.0, 0.0, 0])           # the canonical constructor, on the left wall of the record box
BOX_X0, BOX_X1, BOX_Y0, BOX_Y1 = 2.0, 6.2, -2.0, 2.0
ENT_X, ENT_Y = -4.35, [1.95, 0.65, -0.65, -1.95]
FUN_X = 0.2                              # where the paths meet


class Dop01Records(Beat):
    """dop-01 s0: a record is its components and javac writes the rest; the canonical constructor is the one
    way in; equality and immutability go one level deep."""

    def construct(self):
        self.title_card("Records", "the components, and nothing else")

        # ---------------- the problem: a value class by hand drifts
        panel = RoundedRectangle(corner_radius=0.15, width=PX1 - PX0, height=4.6, stroke_color=GREY_B, stroke_width=2.5)
        panel.move_to([(PX0 + PX1) / 2, 0, 0])
        head = T("class Money, written by hand", 28).move_to([(PX0 + PX1) / 2, 2.8, 0])
        labels = [T(r, 26).move_to([LBL_X, y, 0], aligned_edge=LEFT) for r, y in zip(ROWS, RY)]
        mins = [comp("minor", MIN_C).move_to([MIN_X, y, 0]) for y in RY]
        self.seq("Here is a money value written by hand. It lists its fields in six places.",
                 [(0, [Create(panel), FadeIn(head)], 0.8),
                  (1, [LaggedStart(*[AnimationGroup(FadeIn(labels[i]), FadeIn(mins[i], shift=RIGHT * 0.15)) for i in range(6)],
                                   lag_ratio=0.45)], 3.2)])

        curs = [comp("currency", CUR_C).move_to([CUR_X, y, 0]) for y in RY[:3]]
        holes = [hole(curs[0].width).move_to([CUR_X, y, 0]) for y in RY[3:]]
        new_c = comp("currency", CUR_C).move_to([1.4, 2.6, 0])
        self.seq("Someone adds a currency. Three places get it. equals, hashCode and toString don't.",
                 [(0, [FadeIn(new_c, shift=DOWN * 0.2)], 0.7),
                  (1, [LaggedStart(*[TransformFromCopy(new_c, c) for c in curs], lag_ratio=0.3)], 1.3),
                  (2, [LaggedStart(*[Create(h) for h in holes], lag_ratio=0.3)], 1.0)])

        def money(x, cur):
            b = RoundedRectangle(corner_radius=0.12, width=2.5, height=1.25, stroke_color=GREY_A, stroke_width=2.5).move_to([x, 1.2, 0])
            g = VGroup(one("1000", 26, MIN_C), one(f'"{cur}"', 26, CUR_C)).arrange(DOWN, buff=0.15).move_to(b)
            return VGroup(b, g)
        ma, mb = money(1.7, "EUR"), money(4.7, "USD")
        la = one("a", 26, GREY_B).next_to(ma, UP, buff=0.15)
        lb = one("b", 26, GREY_B).next_to(mb, UP, buff=0.15)
        self.seq("So is this euro amount equal to this dollar amount?",
                 [(0, [FadeIn(ma), FadeIn(la), FadeIn(mb), FadeIn(lb)], 0.9)], after=1.6)

        eq = one("a.equals(b)", 28).move_to([2.7, -0.3, 0])
        tru = one("true", 28, BAD_C).next_to(eq, RIGHT, buff=0.4)
        log_l = T("the log line:", 24, GREY_B).move_to([1.15, -1.45, 0])
        log = one("Money[minor=1000]", 26).next_to(log_l, RIGHT, buff=0.3)
        self.seq("True. equals still compares only the amount, and the log doesn't even show the currency.",
                 [(0, [FadeIn(eq), FadeIn(tru, scale=1.3)], 0.7),
                  (1, [Indicate(holes[0], color=BAD_C, scale_factor=1.15), Indicate(VGroup(*[m[1] for m in (ma, mb)]), color=MIN_C)], 1.0),
                  (1, [FadeIn(log_l), FadeIn(log), Indicate(holes[2], color=BAD_C, scale_factor=1.15)], 1.0)])

        # ---------------- the record: one list, javac writes the rest
        self.play(FadeOut(VGroup(ma, mb, la, lb, eq, tru, log_l, log, new_c, head)), run_time=0.6)
        hdr = one("record Money(long minor, String currency) {}", 26).move_to([-0.9, 2.85, 0])
        paint(hdr, "record", REC_C); paint(hdr, "minor", MIN_C); paint(hdr, "currency", CUR_C)
        panel_r = panel.copy().set_stroke(REC_C, 3)
        self.seq("A record says it once. You list its components in the header, and javac writes the rest from that one list.",
                 [(0, [FadeIn(hdr, shift=DOWN * 0.15)], 0.8),
                  (1, [Indicate(part(hdr, "long minor, String currency"), color=WHITE, scale_factor=1.05)], 0.9),
                  (1, [FadeOut(VGroup(*mins, *curs, *holes)), Transform(panel, panel_r)], 0.6)])

        src_m, src_c = part(hdr, "minor"), part(hdr, "currency")
        gm = [comp("minor", MIN_C).move_to([MIN_X, y, 0]) for y in RY]
        gc = [comp("currency", CUR_C).move_to([CUR_X, y, 0]) for y in RY]
        self.seq("A private final field and an accessor for each, a canonical constructor, and equals, hashCode and toString.",
                 [(0, [LaggedStart(*[AnimationGroup(TransformFromCopy(src_m, gm[i]), TransformFromCopy(src_c, gc[i]))
                                     for i in range(6)], lag_ratio=0.35)], 3.4),
                  (0, [Pulse(panel, REC_C, 1.02)], 0.7)])

        # one level down: equals, hashCode and toString are built by the JDK at run time
        brace = Brace(VGroup(*gc[3:]), RIGHT, buff=0.35, color=GREY_B)
        indy = one("invokedynamic", 24, REC_C).next_to(brace, RIGHT, buff=0.2)
        jdk_b = RoundedRectangle(corner_radius=0.12, width=5.0, height=1.3, stroke_color=GREY_A, stroke_width=2.5).move_to([3.6, -2.35, 0])
        jdk_t = VGroup(one('the JDK gets "minor;currency"', 22), T("and builds each method on its first run", 22, GREY_A))
        fit(jdk_t.arrange(DOWN, buff=0.18), 4.6).move_to(jdk_b)
        paint(jdk_t[0], "minor", MIN_C); paint(jdk_t[0], "currency", CUR_C); part(jdk_t[0], "the JDK gets").set_color(GREY_A)
        to_jdk = Arrow(indy.get_bottom(), jdk_b.get_top(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        self.seq("Those last three aren't even written out. javac hands the JDK the names, minor;currency, "
                 "and the JDK builds each method on its first run.",
                 [(0, [GrowFromCenter(brace), FadeIn(indy)], 0.8),
                  (1, [GrowArrow(to_jdk), Create(jdk_b), FadeIn(jdk_t[0])], 0.9), (1, [FadeIn(jdk_t[1], shift=UP * 0.1)], 0.6),
                  (1, [Pulse(jdk_b, REC_C, 1.04)], 0.8)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- one door: the canonical constructor
        box_ = Rectangle(width=BOX_X1 - BOX_X0, height=BOX_Y1 - BOX_Y0, stroke_color=REC_C, stroke_width=3)
        box_.move_to([(BOX_X0 + BOX_X1) / 2, (BOX_Y0 + BOX_Y1) / 2, 0])
        gapc = Rectangle(width=0.2, height=0.9, stroke_width=0).set_fill(BLACK, 1).move_to(DOOR)
        door = Line(DOOR + UP * 0.45, DOOR + DOWN * 0.45, stroke_color=DOOR_C, stroke_width=8)
        box_t = T("Money objects", 26, REC_C).move_to([(BOX_X0 + BOX_X1) / 2, BOX_Y1 + 0.35, 0])
        door_t = T("canonical constructor", 24, DOOR_C).move_to([3.95, -0.6, 0])
        ents = [one("Money.of(1250, \"eur\")", 24), one("new Money(-5, \"eur\")", 24), one("this(minor, \"EUR\")", 24),
                T("deserialization", 26)]
        for e, y in zip(ents, ENT_Y):
            e.move_to([ENT_X, y, 0])
        paths = [VMobject(stroke_color=GREY_B, stroke_width=2.5).set_points_as_corners(
                 [[ENT_X + 2.15, y, 0], [FUN_X, y * 0.12, 0], [DOOR[0] - 0.12, 0, 0]]) for y in ENT_Y]
        # the problem: a check on the factory path only
        gy = ENT_Y[0] - (0.6 / (FUN_X - ENT_X - 2.15)) * (ENT_Y[0] - ENT_Y[0] * 0.12)
        fgate = Line([-1.6, gy - 0.3, 0], [-1.6, gy + 0.3, 0], stroke_color=DOOR_C, stroke_width=7)
        fgate_t = T("check", 22, DOOR_C).next_to(fgate, UP, buff=0.08)
        self.seq("Where do you check that an amount isn't negative? Put the check in a static factory, and new walks straight past it.",
                 [(0, [Create(box_), FadeIn(box_t), FadeIn(gapc)], 0.8),
                  (1, [FadeIn(ents[0]), FadeIn(ents[1]), Create(paths[0]), Create(paths[1]), Create(fgate), FadeIn(fgate_t)], 0.9),
                  (1, lambda: self._walk(ents[1], paths[1], "-5", BAD_C, inside=[3.1, 1.2, 0]), 1.6)])
        bad_in = self._last
        self.seq("A record has one door: the canonical constructor. Other constructors must call it first, "
                 "and so do factories, withers and Java deserialization.",
                 [(0, [Create(door), FadeIn(door_t), FadeOut(bad_in)], 0.8),
                  (1, [FadeIn(ents[2]), Create(paths[2]), FadeIn(ents[3]), Create(paths[3])], 1.0),
                  (1, [*[ShowPassingFlash(p.copy().set_stroke(DOOR_C, 5), time_width=0.5) for p in paths]], 1.2)])

        chk = VGroup(one("minor >= 0", 22, DOOR_C), one("upper-case currency", 22, DOOR_C)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        chk.next_to(door_t, DOWN, buff=0.2)
        stop = tick(False, 0.25).move_to(DOOR + LEFT * 0.45 + UP * 0.45)
        iae = one("IllegalArgumentException: negative amount: -5", 22, BAD_C).move_to([-0.4, -3.15, 0])
        fit(iae, 9.0)
        self.seq("Put the check there, in the compact constructor, and it holds for every instance. "
                 "It can fix values too: eur becomes EUR.",
                 [(0, [FadeOut(fgate), FadeOut(fgate_t), FadeIn(chk, shift=UP * 0.1), Pulse(door, DOOR_C, 1.2)], 0.8),
                  (0, lambda: self._walk(ents[1], paths[1], "-5", BAD_C, stop_at_door=True), 1.3),
                  (0, [Create(stop), FadeIn(iae)], 0.6),
                  (1, lambda: self._walk(ents[0], paths[0], "1250 eur", CUR_C, inside=[4.1, 0.9, 0], fixed="1250 EUR"), 1.8)],
                 after=0.25)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- one level deep: a record holding a mutable list
        bx = RoundedRectangle(corner_radius=0.12, width=3.7, height=1.7, stroke_color=REC_C, stroke_width=3).move_to([-4.15, 1.55, 0])
        bt = T("record Batch", 26, REC_C).next_to(bx, UP, buff=0.12)
        bid = one('id = "b-7"', 24).move_to([-4.6, 1.95, 0], aligned_edge=LEFT).shift(LEFT * 0.9)
        bpl = one("paymentIds", 24).move_to([-4.6, 1.2, 0], aligned_edge=LEFT).shift(LEFT * 0.9)
        dot = Dot(radius=0.07, color=LIST_C).move_to([-2.65, 1.2, 0])
        lst_t = one('["pay_1", "pay_2"]', 24, LIST_C)
        lst_b = RoundedRectangle(corner_radius=0.1, width=5.0, height=0.8, stroke_color=LIST_C, stroke_width=2.5).move_to([2.9, 1.2, 0])
        lst_t.move_to(lst_b)
        lst_cap = T("an ArrayList", 22, GREY_B).next_to(lst_b, DOWN, buff=0.12)
        fld = Arrow(dot.get_center(), lst_b.get_left(), buff=0.05, stroke_width=3, color=LIST_C, max_tip_length_to_length_ratio=0.12)
        fin = T("final: the arrow can't move", 22, GREY_B).move_to([-0.9, 0.5, 0])
        caller = T("caller: ids", 24, GREY_A).move_to([2.9, 2.95, 0])
        c_ar = Arrow(caller.get_bottom(), lst_b.get_top(), buff=0.08, stroke_width=3, color=GREY_A, max_tip_length_to_length_ratio=0.25)
        self.seq("A record is only shallowly immutable. Its fields are final, but what they point to can change.",
                 [(0, [Create(bx), FadeIn(bt), FadeIn(bid), FadeIn(bpl), FadeIn(dot)], 0.9),
                  (1, [GrowArrow(fld), Create(lst_b), FadeIn(lst_t), FadeIn(lst_cap)], 0.9), (1, [FadeIn(fin)], 0.6)])

        bk_x = [-2.7, -0.9, 0.9, 2.7]
        bks = [RoundedRectangle(corner_radius=0.1, width=1.5, height=1.0, stroke_color=GREY_B, stroke_width=2).move_to([x, -1.85, 0]) for x in bk_x]
        bk_i = [T(str(i), 22, GREY_B).next_to(b, DOWN, buff=0.1) for i, b in enumerate(bks)]
        hs = T("HashSet", 26).move_to([-5.0, -1.85, 0])
        token = chip("batch", REC_C, 24).move_to([bk_x[2], -1.85, 0])
        hc = one("hashCode -> 2", 24).move_to([4.95, -1.85, 0])
        self.seq("A Batch holds the caller's list of payment ids. A HashSet files the batch by its hash code.",
                 [(0, [FadeIn(caller), GrowArrow(c_ar)], 0.8),
                  (1, [FadeIn(hs), *[Create(b) for b in bks], *[FadeIn(i) for i in bk_i]], 0.9),
                  (1, [FadeIn(hc), FadeIn(token, shift=DOWN * 0.3)], 0.8)])

        lst_t2 = one('["pay_1", "pay_2", "pay_3"]', 24, LIST_C)
        lst_b2 = lst_b.copy().stretch_to_fit_width(5.6).align_to(lst_b, LEFT)
        lst_t2.move_to(lst_b2)
        self.seq("Now the caller adds pay_3 to its list. Does the set still find the batch?",
                 [(0, [Indicate(caller, color=WHITE), Transform(lst_b, lst_b2), Transform(lst_t, lst_t2)], 1.0)], after=1.8)

        hc2 = one("hashCode -> 0", 24, BAD_C).move_to(hc)
        probe = bks[0].copy().set_stroke(BAD_C, 4)
        fls = one("contains: false", 26, BAD_C).move_to([-0.9, -0.5, 0])
        self.seq("No. The hash code reads the list, so it changed. The set looks in the wrong bucket, and contains says false.",
                 [(1, [Transform(hc, hc2)], 0.7),
                  (2, [Create(probe)], 0.6), (2, [FadeIn(fls), Pulse(token, REC_C, 1.15)], 0.8)])

        cp_b = RoundedRectangle(corner_radius=0.1, width=4.0, height=0.8, stroke_color=REC_C, stroke_width=2.5).move_to([-0.4, -0.35, 0])
        cp_t = one('["pay_1", "pay_2"]', 24, REC_C).move_to(cp_b)
        cp_cap = T("its own unmodifiable copy", 22, GREY_B).next_to(cp_b, RIGHT, buff=0.25)
        fld2 = Arrow(dot.get_center(), cp_b.get_left() + UP * 0.1, buff=0.05, stroke_width=3, color=REC_C, max_tip_length_to_length_ratio=0.12)
        fix = one("paymentIds = List.copyOf(paymentIds);", 24, REC_C).move_to([0.5, -3.1, 0])
        self.seq("The fix is one line in the compact constructor: List.copyOf. Now the record holds its own unmodifiable copy.",
                 [(0, [FadeOut(VGroup(fls, probe)), FadeIn(fix)], 0.7),
                  (1, [FadeOut(fin), FadeOut(fld), Create(cp_b), FadeIn(cp_t), FadeIn(cp_cap)], 0.8), (1, [GrowArrow(fld2)], 0.6),
                  (1, [Transform(hc, one("hashCode -> 2", 24).move_to(hc))], 0.6)], after=0.25)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- the code
        jt = T("Java", 24, GREY_B)
        jc = code([("record Money(long minor, String currency) {", {"record": REC_C, "minor": MIN_C, "currency": CUR_C}),
                   ("    Money {                                  // compact constructor", {"Money {": DOOR_C}),
                   ('        if (minor < 0) throw new IllegalArgumentException("negative");', {"minor": MIN_C}),
                   ("        currency = currency.toUpperCase(Locale.ROOT);", {"currency": CUR_C}),
                   ("    }", {}), ("}", {})], 22)
        kt = T("Kotlin", 24, GREY_B)
        kc = code([("data class Money(val minor: Long, val currency: String) {", {"data class": REC_C, "minor": MIN_C, "currency": CUR_C}),
                   ('    init { require(minor >= 0) { "negative amount: $minor" } }', {"init": DOOR_C, "minor": MIN_C}),
                   ("}", {})], 22)
        jg = VGroup(jt, jc).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        kg = VGroup(kt, kc).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        knote = T("init can reject a value, but it can't rewrite it: normalize in a factory", 22, GREY_B)
        stack = VGroup(jg, kg, knote).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        fit(stack, 12.4).move_to([0, 0.1, 0])
        self.seq("In Kotlin, a data class gets the same methods, but its init block can only reject a value, not rewrite it.",
                 [(0, [FadeIn(jg, shift=UP * 0.1)], 0.9), (0, [FadeIn(kg, shift=UP * 0.1)], 0.9), (0, [FadeIn(knote)], 0.6)],
                 after=0.25)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- rule and check
        rule = VGroup(T("A record is its components, and javac writes the rest.", 32),
                      T("The canonical constructor is the only way in.", 32, DOOR_C),
                      T("Immutability stops one level down.", 32, LIST_C)).arrange(DOWN, buff=0.22).move_to([0, 1.7, 0])
        fit(rule, 12.4)
        self.seq("The rule: a record is its components, and javac writes the rest. The canonical constructor is the only way in. "
                 "And immutability stops one level down.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7),
                  (2, [FadeIn(rule[2], shift=UP * 0.1)], 0.7)])
        chk = VGroup(T("Check: someone edits a serialized Money and sets the amount to -5.", 28),
                     T("What happens when you read it back?", 28)).arrange(DOWN, buff=0.15).move_to([0, -0.85, 0])
        fit(chk, 12.4)
        self.seq("Quick check. Someone edits a serialized Money and sets the amount to minus five. "
                 "What happens when you read it back?",
                 [(1, [FadeIn(chk, shift=UP * 0.1)], 0.8)], after=2.0)
        ans = T("It's rejected: deserialization calls the canonical constructor, so the check throws.", 28, DOOR_C).move_to([0, -2.5, 0])
        fit(ans, 12.4)
        self.seq("It's rejected. Deserialization calls the canonical constructor too, so your check throws.",
                 [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)

    def _walk(self, ent, path, text, color, inside=None, stop_at_door=False, fixed=None):
        """A value chip leaves an entry point and follows its path to the door; it stops there, or goes in."""
        c = chip(text, color, 24, mono=True).set_z_index(5)
        c[0].set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.25), 1)
        c.move_to(path.get_start() + RIGHT * (c.width / 2 + 0.05))
        pts = path.get_anchors() if hasattr(path, "get_anchors") else path.points
        corner = [list(c.get_center()), [FUN_X, path.get_start()[1] * 0.12, 0], [DOOR[0] - 0.12, 0, 0]]
        if stop_at_door:
            route = VMobject().set_points_as_corners([corner[0], corner[1], [DOOR[0] - 0.75, 0, 0]])
            self._last = c
            return [Succession(FadeIn(c, run_time=0.15), MoveAlongPath(c, route, run_time=1.15, rate_func=smooth))]
        route = VMobject().set_points_as_corners([corner[0], corner[1], corner[2], inside])
        self._last = c
        anims = [FadeIn(c, run_time=0.15), MoveAlongPath(c, route, run_time=1.3, rate_func=smooth)]
        if fixed:
            done = chip(fixed, color, 24, mono=True).move_to(inside).set_z_index(5)
            done[0].set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.25), 1)
            anims.append(Transform(c, done, run_time=0.35))
        return [Succession(*anims)]
