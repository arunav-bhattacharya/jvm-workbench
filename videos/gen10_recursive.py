from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"Enum<E extends Enum<E>>", "enum of E, extends enum of E"), (r"T : Comparable<T>", "T colon comparable of T"),
           (r"B : Builder<B>", "B colon builder of B"), (r"Liar : Builder<CardBuilder>\(\)", "liar colon builder of card builder"),
           (r"Builder<CardBuilder>", "builder of card builder"), (r"Builder<B>", "builder of B"),
           (r"\bPlainCardBuilder\(\)", "plain card builder"), (r"\bCardBuilder\(\)", "card builder"),
           (r"\bPlainCardBuilder\b", "plain card builder"), (r"\bPlainBuilder\b", "plain builder"),
           (r"\bCardBuilder\b", "card builder"), (r"\bcardToken\b", "card token"), (r"\bself\(\)", "self")]

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




def letters(t, pat):
    """Glyphs of every regex match in a line from one()/code()."""
    return VGroup(*[VGroup(*t[m.start():m.end()]) for m in re.finditer(pat, t.src)])


SUB_C, BASE_C, BLANK_C, ERR_C, OK_C = GOLD_M, BLUE_M, YELLOW_M, RED_M, GREEN_M   # subclass, base class, the blank B

# ---- layout: the chain on top, what the compiler sees per call, the one object underneath
COLS = [-4.3, 0.0, 4.3]
CODE_Y, TAG_Y, TAG_W, TAG_H = 2.85, 0.85, 3.5, 1.7
OBJ_Y, BOT = -1.3, -2.65


def tagbox(name, color, items):
    r = RoundedRectangle(corner_radius=0.14, width=TAG_W, height=TAG_H, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.12), opacity=1)
    title = M(name, 26, color).move_to(r.get_top() + DOWN * 0.38)
    rule = Line(r.get_left() + RIGHT * 0.25, r.get_right() + LEFT * 0.25, stroke_width=1.5, color=GREY_D).move_to(r.get_top() + DOWN * 0.72)
    menu = VGroup(*[M(x, 24, WHITE) for x in items]).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
    menu.next_to(rule, DOWN, buff=0.18)
    return VGroup(r, title, rule, menu)


def chain_parts(segs, size=28):
    """The chain as one line, and the same segments as separate texts (to spread into columns)."""
    line = one("".join(segs), size)
    pieces, i = [], 0
    for s in segs:
        pieces.append(VGroup(*line[i:i + len(s)])); i += len(s)
    return line, pieces


def loop_arrow(a, b, color=BLANK_C, angle=-TAU / 3):
    """Arc over the text from glyph a back to glyph b."""
    return CurvedArrow(a.get_top() + UP * 0.1, b.get_top() + UP * 0.1, angle=angle, color=color, stroke_width=3, tip_length=0.18)


class Gen10Recursive(Beat):
    """gen-10 section 0: a base-class setter returns the base type, so the chain loses the subclass;
    a self type B : Builder<B> lets the subclass write its own name into the blank, and amount returns it."""

    def construct(self):
        self.title_card("A type that names itself", "recursive bounds and self types")

        # ---------- the problem: the chain forgets the subclass
        segs = ["PlainCardBuilder()", ".amount(1_200)", ".cardToken(\"tok_1\")"]
        line, pieces = chain_parts(segs)
        line.move_to([0, CODE_Y, 0])
        self.seq("You build a card payment with a chain of calls. amount, then cardToken. "
                 "amount lives in a base class, so every builder shares it.",
                 [(0, [FadeIn(line, shift=DOWN * 0.15)], 0.9),
                  (1, [mark(pieces[1][1:7], WHITE, 0.3)], 0.9), (1, [mark(pieces[2][1:10], WHITE, 0.3)], 0.9)])

        sees = T("what the compiler knows", 24, GREY_B).move_to([COLS[0] - TAG_W / 2, 2.05, 0], aligned_edge=LEFT)
        self.seq("Each call hands back an object, and the compiler only knows the type the call declares. "
                 "Watch that type as the chain runs.",
                 [(0, [*[p.animate.move_to([COLS[i], CODE_Y, 0]) for i, p in enumerate(pieces)]], 1.0),
                  (1, [FadeIn(sees)], 0.6)])

        t1 = tagbox("PlainCardBuilder", SUB_C, ["amount()", "cardToken()"]).move_to([COLS[0], TAG_Y, 0])
        self.seq("PlainCardBuilder() gives you a PlainCardBuilder. It has both setters.",
                 [(0, [mark(pieces[0], SUB_C, 0.3)], 0.9), (0, [FadeIn(t1, shift=DOWN * 0.15)], 0.8)])

        t2 = tagbox("PlainBuilder", BASE_C, ["amount()"]).move_to([COLS[1], TAG_Y, 0])
        a1 = Arrow([COLS[0] + TAG_W / 2 + 0.05, TAG_Y, 0], [COLS[1] - TAG_W / 2 - 0.05, TAG_Y, 0], buff=0, stroke_width=3,
                   color=GREY_B, max_tip_length_to_length_ratio=0.3)
        a2 = Arrow([COLS[1] + TAG_W / 2 + 0.05, TAG_Y, 0], [COLS[2] - TAG_W / 2 - 0.05, TAG_Y, 0], buff=0, stroke_width=3,
                   color=GREY_B, max_tip_length_to_length_ratio=0.3)
        self.seq("But amount is declared in the base class, and it returns a PlainBuilder. "
                 "That's all the base class knows about itself.",
                 [(0, [mark(pieces[1], BASE_C, 0.3)], 0.9), (0, [GrowArrow(a1), FadeIn(t2, shift=RIGHT * 0.15)], 0.8),
                  (1, [Pulse(t2[0], BASE_C, 1.04)], 0.8)])

        self.seq("Can you call cardToken now?", [(0, [mark(pieces[2], WHITE, 0.6)], 1.2)], after=1.6)

        no = tick(False, 0.38).move_to([COLS[2], TAG_Y + 0.35, 0])
        no_t = VGroup(T("PlainBuilder has", 24, ERR_C), T("no cardToken", 24, ERR_C)).arrange(DOWN, buff=0.1).move_to([COLS[2], TAG_Y - 0.55, 0])
        err = one("error: Unresolved reference 'cardToken' on receiver of type 'PlainBuilder'.", 22, ERR_C).move_to([0, BOT, 0])
        fit(err, 12.4)
        obj_lbl = T("the object really is", 24, GREY_B).move_to([COLS[0] - TAG_W / 2, -0.38, 0], aligned_edge=LEFT)
        strip = RoundedRectangle(corner_radius=0.14, width=COLS[2] - COLS[0] + TAG_W, height=0.75, stroke_color=SUB_C, stroke_width=3)
        strip.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(SUB_C), 0.12), opacity=1).move_to([0, OBJ_Y, 0])
        strip_t = T("one PlainCardBuilder object, the whole way", 28, SUB_C).move_to(strip)
        self.seq("No. A PlainBuilder has no cardToken. The object is still a PlainCardBuilder, but the compiler has lost that.",
                 [(0, [GrowArrow(a2), FadeIn(no, scale=0.5), FadeIn(no_t)], 0.7), (0, [FadeIn(err, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(obj_lbl), Create(strip), FadeIn(strip_t)], 1.0),
                  (2, [Pulse(t2[0], ERR_C, 1.04)], 0.8)], after=0.6)
        self.play(FadeOut(VGroup(line, sees, t1, t2, a1, a2, no, no_t, err, obj_lbl, strip, strip_t)), run_time=0.6)

        # ---------- the self type: a blank B that the subclass fills with its own name
        base = code(["abstract class Builder<B : Builder<B>> {",
                     "    fun amount(cents: Long): B { ...; return self() }",
                     "    protected abstract fun self(): B",
                     "}"], 26)
        sub = code(["class CardBuilder : Builder<CardBuilder>() {",
                    "    fun cardToken(t: String): CardBuilder { ...; return this }",
                    "    override fun self() = this",
                    "}"], 26)
        for ln in base:
            paint(ln, "Builder", BASE_C)
        for ln in sub:
            paint(ln, "Builder", BASE_C); paint(ln, "CardBuilder", SUB_C)
        kt = T("Kotlin", 24, GREY_B)
        blk = VGroup(kt, base, sub).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        blk.move_to([0, 0.15, 0])
        base_lbl = T("the base class, written once", 24, BASE_C).next_to(base, RIGHT, buff=0.4).align_to(base, UP)
        bs = VGroup(*letters(base[0], r"\bB\b"), *letters(base[1], r"\bB\b"), *letters(base[2], r"\bB\b"))
        ret_bs = VGroup(letters(base[1], r"\bB\b")[0], letters(base[2], r"\bB\b")[0])
        self.seq("The base class needs to say: I return whatever subclass I really am. "
                 "So give it a type parameter, B, and make amount return B.",
                 [(0, [FadeIn(kt), FadeIn(base, shift=DOWN * 0.15)], 0.9),
                  (1, [bs.animate.set_color(BLANK_C)], 0.6), (1, [mark(ret_bs[0], BLANK_C, 0.5)], 1.0)])

        boxes = VGroup(*[SurroundingRectangle(b, buff=0.07, color=BLANK_C, stroke_width=2) for b in ret_bs])
        name_in = part(sub[0], "CardBuilder", 1)
        self.seq("B is a blank. Each subclass fills it with its own name: CardBuilder is a Builder<CardBuilder>.",
                 [(0, [Create(boxes)], 0.7), (1, [FadeIn(sub[0], shift=UP * 0.15)], 0.8),
                  (1, [mark(name_in, SUB_C, 0.6)], 1.2)])

        flies = [name_in.copy() for _ in bs]
        every = T("for a CardBuilder, every B reads CardBuilder", 28, SUB_C).move_to([0, -3.0, 0])
        self.seq("Now substitute. For a CardBuilder, every B in the base class reads CardBuilder. So amount returns a CardBuilder.",
                 [(1, [*[f.animate.move_to(b).scale(0.35).set_opacity(0) for f, b in zip(flies, bs)],
                       bs.animate.set_color(SUB_C), boxes.animate.set_stroke(SUB_C)], 1.2),
                  (1, [FadeIn(every, shift=UP * 0.1)], 0.6), (2, [mark(ret_bs[0], SUB_C, 0.6)], 1.2)])
        self.remove(*flies)

        self.seq("One more piece. Inside the base class, this is a Builder<B>, not a B. "
                 "So amount returns self(), and each subclass writes self() as this. The compiler checks that it fits.",
                 [(0, [FadeOut(every), FadeIn(sub[1:], shift=UP * 0.1)], 0.7),
                  (1, [mark(part(base[1], "return self()"), WHITE, 0.4)], 1.0),
                  (1, [mark(part(sub[2], "override fun self() = this"), SUB_C, 0.5)], 1.2)], after=0.5)
        self.play(FadeOut(VGroup(kt, base, sub, boxes)), run_time=0.6)

        # ---------- the same chain, now with the self type
        segs2 = ["CardBuilder()", ".amount(1_200)", ".cardToken(\"tok_1\")"]
        line2, pieces2 = chain_parts(segs2)
        for i, p in enumerate(pieces2):
            p.move_to([COLS[i], CODE_Y, 0])
        c1 = tagbox("CardBuilder", SUB_C, ["amount()", "cardToken()"]).move_to([COLS[0], TAG_Y, 0])
        c2 = tagbox("CardBuilder", SUB_C, ["amount()", "cardToken()"]).move_to([COLS[1], TAG_Y, 0])
        c3 = tagbox("CardBuilder", SUB_C, ["amount()", "cardToken()"]).move_to([COLS[2], TAG_Y, 0])
        b_note = M("B = CardBuilder", 24, SUB_C).move_to([COLS[1], -0.35, 0])
        ok = tick(True, 0.3).move_to([COLS[2], -0.35, 0])
        strip2 = strip.copy()
        strip2_t = T("one CardBuilder object, the whole way", 28, SUB_C).move_to(strip2)
        self.seq("Run the chain again. CardBuilder() gives a CardBuilder. amount returns B, and B is CardBuilder. "
                 "So cardToken is in reach.",
                 [(0, [FadeIn(line2), FadeIn(sees)], 0.6), (1, [FadeIn(c1, shift=DOWN * 0.15)], 0.7),
                  (2, [GrowArrow(a1), FadeIn(c2, shift=RIGHT * 0.15)], 0.8), (2, [FadeIn(b_note, shift=UP * 0.1)], 0.6),
                  (3, [GrowArrow(a2), FadeIn(c3, shift=RIGHT * 0.15)], 0.8), (3, [FadeIn(ok, scale=0.5)], 0.4),
                  (3, [FadeIn(obj_lbl), FadeIn(strip2), FadeIn(strip2_t)], 0.7)], after=0.8)
        self.play(FadeOut(VGroup(line2, sees, c1, c2, c3, a1, a2, b_note, ok, obj_lbl, strip2, strip2_t)), run_time=0.6)

        # ---------- draw the type that refers to itself
        big = one("B : Builder<B>", 48).move_to([0, 1.55, 0])
        paint(big, "Builder", BASE_C)
        bB = letters(big, r"\bB\b")
        bB.set_color(BLANK_C)
        loop = loop_arrow(bB[1], bB[0], angle=TAU / 5)
        self_l = T("refers to itself", 26, BLANK_C).next_to(loop, UP, buff=0.12)
        self.seq("Look at the bound itself. B : Builder<B>. The B inside points back to the B it bounds.",
                 [(1, [FadeIn(big, shift=UP * 0.1)], 0.8), (2, [Create(loop)], 1.0), (2, [FadeIn(self_l)], 0.5)])

        fitl = one("CardBuilder : Builder<CardBuilder>", 32).move_to([0, 0.05, 0])
        paint(fitl, "Builder", BASE_C); paint(fitl, "CardBuilder", SUB_C)
        fit_ok = tick(True, 0.26).next_to(fitl, RIGHT, buff=0.35)
        self.seq("Read it as: B is a builder whose own B is B. CardBuilder fits, because it is a Builder<CardBuilder>.",
                 [(0, [Pulse(VGroup(bB[0], bB[1]), BLANK_C, 1.15)], 0.9),
                  (1, [FadeIn(fitl, shift=UP * 0.1)], 0.8), (1, [FadeIn(fit_ok, scale=0.5)], 0.4)])

        cmp = one("T : Comparable<T>", 32).move_to([-3.4, -2.2, 0])
        enm = one("Enum<E extends Enum<E>>", 32).move_to([3.0, -2.2, 0])
        paint(cmp, "Comparable", BASE_C); paint(enm, "Enum", BASE_C)
        cT, eE = letters(cmp, r"\bT\b"), letters(enm, r"\bE\b")
        cT.set_color(BLANK_C); eE.set_color(BLANK_C)
        l2 = loop_arrow(cT[1], cT[0], angle=TAU / 5)
        l3 = loop_arrow(eE[1], eE[0], angle=TAU / 5)
        self.seq("You've met this shape before. T : Comparable<T> is a recursive bound too, and so is Java's Enum<E extends Enum<E>>.",
                 [(1, [FadeIn(cmp, shift=UP * 0.1)], 0.6), (1, [Create(l2)], 0.8),
                  (1, [FadeIn(enm, shift=UP * 0.1)], 0.6), (1, [Create(l3)], 0.8)], after=0.6)
        self.play(FadeOut(VGroup(big, loop, self_l, fitl, fit_ok, cmp, enm, l2, l3)), run_time=0.6)

        # ---------- Java and Kotlin
        jl = code(["abstract class Builder<B extends Builder<B>>",
                   "final class CardBuilder extends Builder<CardBuilder>",
                   "new CardBuilder().amount(1_200).cardToken(\"tok_1\");"], 26)
        kl = code(["abstract class Builder<B : Builder<B>>",
                   "class CardBuilder : Builder<CardBuilder>()",
                   "CardBuilder().amount(1_200).cardToken(\"tok_1\")"], 26)
        for ln in [*jl, *kl]:
            paint(ln, "Builder", BASE_C); paint(ln, "CardBuilder", SUB_C)
            for g in letters(ln, r"\bB\b"):
                g.set_color(BLANK_C)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.6, aligned_edge=LEFT).move_to([0, 0.3, 0])
        fit(both, 12.4)
        self.seq("In code, Java writes extends where Kotlin writes a colon. In both, the subclass names itself, and the chain compiles.",
                 [(0, [FadeIn(jg, shift=UP * 0.15)], 0.7), (0, [FadeIn(kg, shift=UP * 0.15)], 0.7),
                  (1, [mark(part(jl[1], "Builder<CardBuilder>"), SUB_C, 0.3), mark(part(kl[1], "Builder<CardBuilder>"), SUB_C, 0.3)], 1.1)],
                 after=0.6)
        self.play(FadeOut(both), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("A recursive bound lets a base class return its own subclass,", 32),
                      T("so a chain keeps the subclass's methods in reach.", 32, SUB_C)).arrange(DOWN, buff=0.3).move_to([0, 1.9, 0])
        fit(rule, 12.4)
        self.seq("The rule. A recursive bound lets a base class return its own subclass, so a chain keeps the subclass's methods in reach.",
                 [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        liar = one("class Liar : Builder<CardBuilder>()", 30).move_to([0, -0.2, 0])
        paint(liar, "Builder", BASE_C); paint(liar, "CardBuilder", SUB_C)
        chk = T("Check: does this compile?", 30).next_to(liar, UP, buff=0.4)
        self.seq("Quick check. Someone writes class Liar : Builder<CardBuilder>(). Does it compile?",
                 [(0, [FadeIn(chk, shift=UP * 0.1)], 0.6), (1, [FadeIn(liar, shift=UP * 0.1)], 0.7)], after=2.2)
        yes = T("Yes. The bound only asks for some builder in the blank.", 28, OK_C).move_to([0, -1.6, 0])
        nofo = T("It can't force a subclass to write its own name.", 28, GREY_A).move_to([0, -2.3, 0])
        self.seq("Yes. The bound only asks for some builder in the blank. It can't force a subclass to write its own name.",
                 [(0, [FadeIn(yes, shift=UP * 0.1)], 0.7), (1, [FadeIn(nofo, shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
