from fg import *

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat3(VoiceScene):
    """VoiceScene with two additions: beat(say=...) lets the voice read a different spelling than the
    caption shows, and captions split only where a new sentence starts."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
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


def cline(text, size=24, color=WHITE):
    """One code line. A hidden '|' in front keeps the indentation and gives every line the same anchor."""
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


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub):
    """The glyphs of substring sub inside a line from code() or one(). With ligatures off, every
    character, spaces included, is one submobject, so string index = glyph index."""
    i = t.src.index(sub)
    return VGroup(*t[i:i + len(sub)])


def slot(w=2.3, h=1.0):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=GREY_B, stroke_width=2.5)
    return r.set_fill(BLACK, opacity=1)


def val(text, color, size=28):
    return chip(text, color, size=size, mono=True)


KIDS = {"Card": BLUE_M, "Transfer": TEAL_M, "Wallet": GOLD_M}


def make_tree(names):
    parent = mbox("sealed interface Method", WHITE, size=26).move_to(UP * 2.2)
    xs = {2: [-1.6, 1.6], 3: [-3.2, 0, 3.2]}[len(names)]
    kids = VGroup(*[mbox(n, KIDS[n], w=2.6, size=26).move_to([x, 0.5, 0]) for n, x in zip(names, xs)])
    lines = VGroup(*[Line(parent.get_bottom(), k.get_top(), stroke_width=2.5, color=GREY_B) for k in kids])
    return VGroup(parent, kids, lines)


class Dop03Exhaustive(Beat3):
    """dop-03 section 0: a pattern switch over a sealed type is checked; an instanceof chain stays silent."""

    def construct(self):
        self.title_card("A pattern switch is checked", "an instanceof chain is not")

        tree = make_tree(["Card", "Transfer"])
        perm = one("sealed interface Method permits Card, Transfer {}", 26, WHITE).move_to(DOWN * 1.2)
        part(perm, "permits Card, Transfer").set_color(GREY_A)
        self.beat("Here is a sealed interface for payment methods. Sealed means it lists every subtype it allows. Right now that is Card and Transfer.",
                  FadeIn(tree[0]), FadeIn(tree[1]), Create(tree[2]), FadeIn(perm, shift=UP * 0.15), run_time=2.0)

        # shrink the tree to the top, bring in the two pieces of code
        S = 0.62
        top = UP * 2.75

        def place(t):
            t.scale(S).move_to(top)
            return t

        small = place(tree.copy())
        lh = T("an instanceof chain", 26, GREY_B)
        lc = code(['if (m instanceof Card c)',
                   '    return "card";',
                   'else if (m instanceof Transfer t)',
                   '    return "transfer";',
                   'else return "unknown";'], 24)
        rh = T("a pattern switch, JDK 21", 26, GREY_B)
        rc = code(['return switch (m) {',
                   '    case Card c -> "card";',
                   '    case Transfer t -> "transfer";',
                   '};'], 24)
        for ln, nm in ((lc[0], "Card"), (lc[2], "Transfer"), (rc[1], "Card"), (rc[2], "Transfer")):
            part(ln, nm).set_color(KIDS[nm])
        lcol = VGroup(lh, lc).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        rcol = VGroup(rh, rc).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        cols = VGroup(lcol, rcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cols.scale(min(1, 12.2 / cols.width)).move_to(DOWN * 0.15)
        self.beat("Two pieces of code turn a method into a receipt label.",
                  Transform(tree, small), FadeOut(perm), FadeIn(cols, shift=UP * 0.2), run_time=1.8)
        okl = tick(True, 0.22).next_to(lh, RIGHT, buff=0.3)
        okr = tick(True, 0.22).next_to(rh, RIGHT, buff=0.3)
        self.beat("Both compile, and both give the same answers today.", FadeIn(okl), FadeIn(okr), run_time=1.0)

        # a new subtype arrives
        big3 = make_tree(["Card", "Transfer", "Wallet"])
        small3 = place(big3.copy())
        self.beat("Now a new payment method ships: Wallet. You add it to the sealed interface.",
                  Transform(tree[0], small3[0]), Transform(tree[1][0], small3[1][0]), Transform(tree[1][1], small3[1][1]),
                  Transform(tree[2][0], small3[2][0]), Transform(tree[2][1], small3[2][1]),
                  FadeIn(small3[1][2], scale=0.6), Create(small3[2][2]), run_time=1.6)
        self.beat("Then you recompile. javac reads the permits list, so it knows every Method there can be. It checks the switch against that list, case by case.",
                  Indicate(small3[1][2], color=GOLD_M, scale_factor=1.15), Indicate(rc[1:3], color=WHITE, scale_factor=1.03), run_time=2.0)
        rerr = VGroup(one("error: the switch expression does not", 20, RED_M),
                      one("cover all possible input values", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        rerr.next_to(rc, DOWN, buff=0.45).align_to(rc, LEFT)
        badr = tick(False, 0.22).move_to(okr)
        self.beat("There is no case for Wallet, so the switch is now a compile error.",
                  FadeOut(okr), FadeIn(badr), FadeIn(rerr, shift=UP * 0.15), run_time=1.2)
        lnote = T("compiles, no warning", 24, GREY_B).next_to(lc, DOWN, buff=0.45).align_to(lc, LEFT)
        self.beat("The chain compiles without a word. To the compiler it is just a few if statements, and nothing says they must cover every Method.",
                  FadeIn(lnote, shift=UP * 0.15), run_time=1.2)

        # a wallet walks through the chain at run time
        w = val("a Wallet", GOLD_M, 24).next_to(okl, RIGHT, buff=0.35)
        hi = SurroundingRectangle(lc[0], buff=0.08, color=GOLD_M, stroke_width=2.5, corner_radius=0.06)
        self.beat("At run time, a Wallet payment walks through it.", FadeIn(w, shift=LEFT * 0.2), Create(hi), run_time=1.2)
        self.beat("Not a Card. Not a Transfer.",
                  Succession(hi.animate(run_time=0.3).set_color(RED_M),
                             Transform(hi, SurroundingRectangle(lc[2], buff=0.08, color=GOLD_M, stroke_width=2.5, corner_radius=0.06), run_time=0.6),
                             hi.animate(run_time=0.3).set_color(RED_M)), run_time=1.6)
        outp = VGroup(T("receipt:", 24, GREY_B), M('"unknown"', 26, RED_M)).arrange(RIGHT, buff=0.25)
        outp.move_to(lnote, aligned_edge=LEFT)
        self.beat("So it lands in the else, and every wallet receipt says unknown.",
                  Transform(hi, SurroundingRectangle(lc[4], buff=0.08, color=RED_M, stroke_width=2.5, corner_radius=0.06)),
                  FadeOut(lnote), FadeIn(outp, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(tree, small3[1][2], small3[2][2], cols, okl, badr, rerr, w, hi, outp)), run_time=0.7)

        # Java and Kotlin side by side
        jv = code(["sealed interface Method",
                   "    permits Card, Transfer, Wallet {}",
                   "",
                   "return switch (m) {",
                   '    case Card c -> "card";',
                   '    case Transfer t -> "transfer";',
                   "};"], 24)
        kt = code(["sealed interface Method",
                   "class Card : Method",
                   "class Transfer : Method",
                   "class Wallet : Method",
                   "",
                   "return when (m) {",
                   '    is Card -> "card"',
                   '    is Transfer -> "transfer"',
                   "}"], 24)
        part(jv[1], "Wallet").set_color(GOLD_M)
        part(kt[3], "Wallet").set_color(GOLD_M)
        je = VGroup(one("error: the switch expression does not", 20, RED_M),
                    one("cover all possible input values", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        ke = VGroup(one("error: 'when' expression must be", 20, RED_M),
                    one("exhaustive. Add the 'is Wallet' branch", 20, RED_M),
                    one("or an 'else' branch.", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        je.next_to(jv, DOWN, buff=0.4).align_to(jv, LEFT).set_y(kt.get_bottom()[1] - 0.4 - je.height / 2)
        ke.next_to(kt, DOWN, buff=0.4).align_to(kt, LEFT)
        allg = VGroup(pair, je, ke)
        allg.scale(min(1, 12.2 / allg.width, 6.6 / allg.height)).move_to(ORIGIN)
        self.beat("Kotlin's when over a sealed interface gets the same check, whether you use it as an expression or as a statement.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.6)
        self.beat("Add Wallet, and both compilers stop. kotlinc even names the branch you forgot.",
                  FadeIn(je, shift=UP * 0.1), FadeIn(ke, shift=UP * 0.1), run_time=1.4)
        self.play(Indicate(part(ke[1], "'is Wallet'"), color=GOLD_M, scale_factor=1.2), run_time=0.9)
        self.beat("Every switch over Method gets this check, so the build stays red until each one handles Wallet.",
                  Indicate(VGroup(jv[3:], kt[5:]), color=WHITE, scale_factor=1.02), run_time=1.4)
        self.play(FadeOut(allg), run_time=0.6)

        dflt = code(['return switch (m) {',
                     '    case Card c -> "card";',
                     '    case Transfer t -> "transfer";',
                     '    default -> "unknown";',
                     '};'], 28).move_to(UP * 0.3)
        part(dflt[1], "Card").set_color(BLUE_M)
        part(dflt[2], "Transfer").set_color(TEAL_M)
        part(dflt[3], "default").set_color(RED_M)
        wv = val("a Wallet", GOLD_M, 26).next_to(dflt[3], RIGHT, buff=0.6)
        dnote = T("compiles, and Wallet lands here", 26, RED_M).next_to(dflt, DOWN, buff=0.6)
        self.beat("One rule follows. Don't put a default on a switch over a sealed type.", FadeIn(dflt, shift=UP * 0.15), run_time=1.2)
        self.beat("A default catches Wallet quietly, the same way the else did, and the compiler has nothing left to check.",
                  FadeIn(wv, shift=LEFT * 0.3), Indicate(part(dflt[3], "default"), color=RED_M, scale_factor=1.2),
                  FadeIn(dnote, shift=UP * 0.1), run_time=1.6)
        self.wait(0.8)
