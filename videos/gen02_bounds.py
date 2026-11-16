from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"T : Comparable<T>", "T colon comparable of T"), (r"T : CharSequence", "T colon char sequence"),
           (r"a\.compareTo\(b\)", "a dot compare to b"), (r"a > b", "a greater than b"), (r"x\.length", "x dot length"),
           (r"\bcompareTo\b", "compare to"), (r"\bhashCode\b", "hash code"), (r"\btoString\b", "to string"),
           (r"\bshortestLabel\b", "shortest label"), (r"\blengthOf\b", "length of"), (r"\bStringBuilder\b", "string builder"),
           (r"\bCharSequence\b", "char sequence"), (r"\bAny\?", "nullable Any"), (r"\bString's\b", "string's")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

INT_C, STR_C, PAY_C, SB_C = GOLD_M, GREEN_M, PURPLE_M, GREY_A     # the types a caller can pick
CMP_C, CS_C, ERR_C, KEY_C = BLUE_M, TEAL_M, RED_M, YELLOW_M       # Comparable bound, CharSequence bound, refusal, keywords


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


# ---- layout: the caller's types on the left, the bound as a gate, the function body as a box on the right
QX, QY = -5.0, [1.2, 0.4, -0.4, -1.2]
G1X, G2X, GH = -2.9, -1.4, 1.65
BOX_C, BOX_W, BOX_H = np.array([3.1, 0.025, 0]), 6.6, 3.95
BL = BOX_C[0] - BOX_W / 2
ROW_Y, LANE_Y, ENTRY_X = 0.8, 1.5, -0.7     # chips travel in a lane above the row, so they never cross a chip already in
TOOL1_Y, TOOL2_Y = -0.62, -1.4
BOT = -2.7


def tchip(text, color):
    c = chip(text, color, size=26, mono=True)
    c.set_z_index(5)
    return c


def tool(text, color):
    return chip(text, color, size=24, mono=True)


def row_slots(chips, y, x0=BL + 0.35, gap=0.3):
    """Left-aligned centres for chips laid out in one row inside the box."""
    out, x = [], x0
    for c in chips:
        out.append(np.array([x + c.width / 2, y, 0])); x += c.width + gap
    return out


class Gen02Bounds(Beat):
    """gen-02 sections 0 to 2: an unbounded T lets every type in and gives the body only what Any? has;
    T : Comparable<T> is a gate at the call site that shuts Payment out and hands the body compareTo;
    a where clause adds a second gate, and T must pass both."""

    def construct(self):
        self.title_card("What a bound buys you", "upper bounds and where clauses")

        # ---------- the problem: bigger(a, b) for any T
        sigA = one("fun <T> bigger(a: T, b: T): T = if (a > b) a else b", 26).move_to([0, 2.95, 0])
        self.seq("You want one function that returns the bigger of two values. Amounts, currency codes, anything. "
                 "So you write it once, for any type T.",
                 [(0, [FadeIn(sigA, shift=DOWN * 0.15)], 0.9), (2, [mark(part(sigA, "<T>"), WHITE, 0.5)], 1.2)])
        self.seq("In Kotlin, a > b means a.compareTo(b). Does this compile?",
                 [(0, [mark(part(sigA, "a > b"), WHITE, 0.8)], 1.5)], after=1.8)

        # the picture: queue of types, an open gate, the function body
        names = [("Int", INT_C), ("String", STR_C), ("Payment", PAY_C), ("StringBuilder", SB_C)]
        chips = [tchip(n, c).move_to([QX, QY[i], 0]) for i, (n, c) in enumerate(names)]
        home = [c.get_center().copy() for c in chips]
        INT, STR, PAY, SB = chips
        q_lbl = T("the caller picks T", 24, GREY_B).move_to([QX, -2.05, 0])

        gate_open = DashedLine([G1X, -GH, 0], [G1X, GH, 0], dash_length=0.12, color=GREY_B, stroke_width=3)
        gate1 = Rectangle(width=0.16, height=2 * GH, stroke_width=0).set_fill(CMP_C, 1).move_to([G1X, 0, 0])
        sign_open = T("no bound", 26, GREY_B).move_to([G1X, 2.0, 0])
        sign1 = M("Comparable<T>", 24, CMP_C).move_to([G1X, 2.0, 0])

        body = RoundedRectangle(corner_radius=0.16, width=BOX_W, height=BOX_H, stroke_color=GREY_B, stroke_width=2.5)
        body.set_fill(BLACK, 1).move_to(BOX_C)
        b_lbl = T("inside the function", 24, GREY_B).move_to([BOX_C[0], 2.3, 0])
        can_be = T("T can be", 24, GREY_B).move_to([BL + BOX_W - 0.3, 1.6, 0], aligned_edge=RIGHT)
        divider = DashedLine([BL + 0.2, 0.3, 0], [BL + BOX_W - 0.2, 0.3, 0], dash_length=0.1, color=GREY_D, stroke_width=1.5)
        may_call = T("the body may call", 24, GREY_B).move_to([BL + 0.3, -0.02, 0], aligned_edge=LEFT)

        basics = [tool("toString()", GREY_B), tool("hashCode()", GREY_B), tool("==", GREY_B)]
        for c, p in zip(basics, row_slots(basics, TOOL1_Y)):
            c.move_to(p)
        cmp_tool = tool("compareTo(T)", CMP_C)
        len_tool = tool("length", CS_C)
        for c, p in zip([cmp_tool, len_tool], row_slots([cmp_tool, len_tool], TOOL2_Y)):
            c.move_to(p)

        def enter(c, slot, rt=0.9):
            path = VMobject().set_points_as_corners([c.get_center(), [ENTRY_X, LANE_Y, 0], [slot[0], LANE_Y, 0], slot])
            return MoveAlongPath(c, path, rate_func=smooth, run_time=rt)

        def go_home(c):
            return c.animate.move_to(home[chips.index(c)])

        crosses = {}

        def stop_at(c, gx):
            return c.animate.move_to([gx - 0.14 - c.width / 2, c.get_center()[1], 0])

        def refuse(c, gx):
            x = tick(False, 0.2).move_to([home[chips.index(c)][0] + c.width / 2 + 0.35, home[chips.index(c)][1], 0])
            crosses[c] = x
            return [Flash(Dot([gx, c.get_center()[1], 0]), color=ERR_C, flash_radius=0.4, line_length=0.15),
                    go_home(c), FadeIn(x, scale=0.5)]

        slotsA = row_slots([INT, STR, PAY], ROW_Y)
        self.seq("No. T has no bound, so the caller may pick any type at all. An Int, a String, a Payment.",
                 [(1, [FadeIn(body), FadeIn(b_lbl), FadeIn(can_be), Create(divider), FadeIn(may_call),
                       Create(gate_open), FadeIn(sign_open)], 0.9),
                  (1, [LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in (INT, STR, PAY)], lag_ratio=0.3), FadeIn(q_lbl)], 0.9),
                  (2, [enter(INT, slotsA[0], 0.7)], 0.7), (2, [enter(STR, slotsA[1], 0.7)], 0.7), (2, [enter(PAY, slotsA[2], 0.7)], 0.7)])

        self.seq("Inside, your code may only use what all of them share. Kotlin's default bound is Any?, and Java's is Object. "
                 "Both give you toString, hashCode and equals.",
                 [(0, [Pulse(VGroup(INT, STR, PAY), WHITE)], 1.0),
                  (2, [LaggedStart(*[FadeIn(b, shift=UP * 0.15) for b in basics], lag_ratio=0.35)], 1.2)])

        self.seq("And a Payment has no order. Should it compare by amount, by time, or by id? "
                 "So the compiler refuses a > b.",
                 [(0, [Pulse(PAY, ERR_C, 1.12)], 0.9), (2, [part(sigA, "a > b").animate.set_color(ERR_C)], 0.5)])

        errs = VGroup(one("Java:   error: cannot find symbol: method compareTo(T)", 22, ERR_C),
                      one("Kotlin: error: candidate 'fun String.compareTo(...)' is inapplicable", 22, ERR_C)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([0, BOT, 0])
        fit(errs, 12.4)
        self.seq("Java says it can't find compareTo. Kotlin finds only String's compareTo, which doesn't fit.",
                 [(0, [FadeOut(q_lbl), FadeIn(errs[0], shift=UP * 0.1)], 0.6), (1, [FadeIn(errs[1], shift=UP * 0.1)], 0.6)])

        # ---------- the fix: T : Comparable<T> is a gate
        sigB = one("fun <T : Comparable<T>> bigger(a: T, b: T): T = if (a > b) a else b", 24).move_to([0, 2.95, 0])
        part(sigB, "Comparable<T>").set_color(CMP_C)
        self.seq("The fix is to promise more about T. Write T : Comparable<T>. "
                 "Read it as: T is something that can be compared with another T.",
                 [(0, [FadeOut(errs), go_home(INT), go_home(STR), go_home(PAY), FadeIn(q_lbl)], 0.8),
                  (1, [FadeTransform(sigA, sigB)], 0.9),
                  (1, [ReplacementTransform(gate_open, gate1), ReplacementTransform(sign_open, sign1)], 0.8),
                  (2, [mark(part(sigB, "T : Comparable<T>"), CMP_C, 0.9)], 1.6)])

        slotsB = row_slots([INT, STR], ROW_Y)
        self.seq("Now the bound is a gate at the call site. Int and String are comparable, so they get in. "
                 "A call with a Payment no longer compiles.",
                 [(0, [Pulse(gate1, WHITE, 1.04)], 0.8),
                  (1, [enter(INT, slotsB[0], 0.8)], 0.8), (1, [enter(STR, slotsB[1], 0.8)], 0.8),
                  (2, [stop_at(PAY, G1X)], 0.6), (2, lambda: refuse(PAY, G1X), 0.6)])

        gt = part(sigB, "a > b")
        self.seq("Inside, the body gains a tool. The bound guarantees a compareTo, so a > b compiles.",
                 [(0, [FadeIn(cmp_tool, shift=UP * 0.15)], 0.7), (1, [Pulse(cmp_tool, CMP_C, 1.1)], 0.8),
                  (1, [gt.animate.set_color(GREEN_M)], 0.5)])

        fewer = T("fewer types get in", 30, KEY_C).move_to([(QX + G1X) / 2, BOT, 0])
        more = T("more the body may call", 30, KEY_C).move_to([BOX_C[0], BOT, 0])
        self.seq("That is the trade. A bound lets fewer types in, and lets your code do more with the one it gets.",
                 [(1, [FadeOut(q_lbl), FadeIn(fewer, shift=UP * 0.1), Pulse(gate1, KEY_C, 1.04)], 0.9),
                  (1, [FadeIn(more, shift=UP * 0.1), Pulse(cmp_tool, KEY_C, 1.1)], 0.9)], after=0.4)

        # ---------- two bounds: a where clause adds a second gate
        sigC = code(["fun <T> shortestLabel(items: List<T>): T",
                     "    where T : CharSequence, T : Comparable<T>"], 24)
        paint(sigC[1], "where", KEY_C); paint(sigC[1], "CharSequence", CS_C); paint(sigC[1], "Comparable<T>", CMP_C)
        sigC.move_to([0, 2.9, 0])
        sigC1 = sigC[0].copy().move_to([0, 2.95, 0])
        sb_x = tick(False, 0.2)
        self.seq("Now a function needs two abilities. shortestLabel finds the shortest label, and breaks ties alphabetically. "
                 "It needs length and compareTo.",
                 [(0, [FadeOut(fewer), FadeOut(more), FadeIn(q_lbl), go_home(INT), go_home(STR), FadeOut(crosses.pop(PAY))], 0.8),
                  (1, [FadeOut(sigB, shift=UP * 0.2), FadeIn(sigC1, shift=DOWN * 0.15)], 0.8),
                  (1, [FadeIn(SB, shift=RIGHT * 0.2)], 0.6),
                  (2, [Pulse(cmp_tool, CMP_C, 1.1)], 0.8)])

        gate2 = Rectangle(width=0.16, height=2 * GH, stroke_width=0).set_fill(CS_C, 1).move_to([G2X, 0, 0])
        sign2 = M("CharSequence", 24, CS_C).move_to([G2X, -2.05, 0])
        slotsC = row_slots([STR, SB], ROW_Y)
        self.seq("Angle brackets hold only one bound. The second goes in a where clause, and T must pass both at once. "
                 "A String does.",
                 [(1, [ReplacementTransform(sigC1, sigC[0]), FadeIn(sigC[1], shift=DOWN * 0.1)], 0.8),
                  (1, [GrowFromEdge(gate2, DOWN), FadeIn(sign2)], 0.7),
                  (1, [Pulse(gate1, WHITE, 1.04), Pulse(gate2, WHITE, 1.04)], 0.8),
                  (2, [enter(STR, slotsC[0], 0.9)], 0.9)])

        self.seq("An Int is comparable, but it has no characters, so it stops at the second gate. Payment stops at the first.",
                 [(0, [stop_at(INT, G2X)], 0.8), (0, lambda: refuse(INT, G2X), 0.6),
                  (1, [stop_at(PAY, G1X)], 0.6), (1, lambda: refuse(PAY, G1X), 0.6)])

        self.seq("What about a StringBuilder?", [(0, [Pulse(SB, WHITE, 1.1)], 0.8)], after=1.3)

        self.seq("It gets in. Since JDK 11, StringBuilder is comparable too. Now the body may call length as well.",
                 [(0, [enter(SB, slotsC[1], 1.0)], 1.0),
                  (2, [FadeIn(len_tool, shift=UP * 0.15)], 0.7), (2, [Pulse(len_tool, CS_C, 1.1)], 0.8)], after=0.3)

        self.play(FadeOut(VGroup(*chips, *crosses.values(), gate1, gate2, sign1, sign2, body, b_lbl, can_be, divider,
                                 may_call, *basics, cmp_tool, len_tool, q_lbl, sigC)), run_time=0.7)

        # ---------- the same bounds in Java and Kotlin
        jl = code(["static <T extends Comparable<T>> T bigger(T a, T b)",
                   "static <T extends CharSequence & Comparable<T>>",
                   "        T shortestLabel(List<T> items)"], 24)
        kl = code(["fun <T : Comparable<T>> bigger(a: T, b: T): T",
                   "fun <T> shortestLabel(items: List<T>): T",
                   "    where T : CharSequence, T : Comparable<T>"], 24)
        for ln in [*jl, *kl]:
            paint(ln, "Comparable<T>", CMP_C); paint(ln, "CharSequence", CS_C)
            paint(ln, "extends", KEY_C); paint(ln, "&", KEY_C); paint(ln, "where", KEY_C)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.6, aligned_edge=LEFT).move_to([0, 0.55, 0])
        fit(both, 12.4)
        self.seq("Java writes a bound with extends, even for an interface, and joins two bounds with an ampersand.",
                 [(0, [FadeIn(jg, shift=UP * 0.15)], 0.7), (0, [mark(part(jl[0], "extends"), KEY_C, 0.4)], 1.0),
                  (0, [mark(part(jl[1], "&"), KEY_C, 0.5)], 1.0), (0, [FadeIn(kg, shift=UP * 0.15)], 0.7)])
        one_cls = T("At most one bound can be a class: a JVM class has one superclass.", 28, GREY_A).move_to([0, BOT, 0])
        fit(one_cls, 12.4)
        self.seq("At most one bound may be a class, because a JVM class has only one superclass.",
                 [(0, [FadeIn(one_cls, shift=UP * 0.1)], 0.8)], after=0.3)
        self.play(FadeOut(VGroup(both, one_cls)), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("A bound shuts some callers out.", 34),
                      T("In return, your code may use what the bound promises.", 34, CMP_C)).arrange(DOWN, buff=0.3).move_to([0, 1.9, 0])
        fit(rule, 12.4)
        self.seq("The rule. A bound shuts some callers out, and in return your code may use what the bound promises.",
                 [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        chk = VGroup(T("Check: lengthOf only reads x.length.", 28),
                     T("Which bound makes it compile? Can you still pass an Int?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.2, 0])
        fit(chk, 12.4)
        self.seq("Quick check. lengthOf only reads x.length. Which bound makes it compile, and can you still pass an Int?",
                 [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)], after=1.8)
        ans = one("fun <T : CharSequence> lengthOf(x: T) = x.length", 26).move_to([0, -1.85, 0])
        paint(ans, "CharSequence", CS_C)
        no42 = VGroup(one("lengthOf(42)", 26), tick(False, 0.2)).arrange(RIGHT, buff=0.3).move_to([0, -2.7, 0])
        self.seq("T : CharSequence. And no: an Int has no characters, so that call won't compile.",
                 [(0, [FadeIn(ans, shift=UP * 0.1)], 0.8), (1, [FadeIn(no42, shift=UP * 0.1)], 0.7)])
        self.wait(0.6)
