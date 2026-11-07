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


def panel(title, sub, color, w=4.6, h=2.8):
    r = RoundedRectangle(corner_radius=0.16, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.1), opacity=1)
    t = M(title, 26, color).move_to(r.get_top() + DOWN * 0.42)
    s = T(sub, 22, GREY_B).next_to(t, DOWN, buff=0.12)
    return VGroup(r, t, s)


class Gen04Covariance(Beat3):
    """gen-04 section 0: a producer only hands values out, so Source<CardPayment> can stand in for Source<Payment>."""

    def construct(self):
        self.title_card("A producer only hands values out", "covariance, with out")

        iface = one("interface Source<T> { fun next(): T? }", 28, WHITE).move_to(UP * 2.9)
        pbox = mbox("Source<T>", WHITE, w=3.2, h=1.1, size=30).move_to(LEFT * 2.0 + DOWN * 0.1)
        pout = Arrow(pbox.get_right(), pbox.get_right() + RIGHT * 3.6, buff=0.15, stroke_width=4, color=GREEN_M,
                     max_tip_length_to_length_ratio=0.1)
        plab = M("next(): T", 26, GREEN_M).next_to(pout, UP, buff=0.15)
        pt = val("T", GREEN_M, 26).move_to(pout.get_start() + RIGHT * 0.35)
        self.beat("A producer is a type that only hands values of T out. A feed of payments, an iterator, a Supplier. You call it, and it gives you a T.",
                  FadeIn(iface, shift=DOWN * 0.2), FadeIn(pbox), GrowArrow(pout), FadeIn(plab),
                  Succession(Wait(1.2), FadeIn(pt, run_time=0.3), pt.animate(run_time=1.2).move_to(pout.get_end() + RIGHT * 0.5)),
                  run_time=3.2)
        self.play(FadeOut(VGroup(pbox, pout, plab, pt)), run_time=0.5)

        src = panel("Source<CardPayment>", "a source of card payments", BLUE_M).move_to(LEFT * 3.85 + DOWN * 0.15)
        c1 = val("card pay_1  1200", BLUE_M, 26)
        c2 = val("card pay_2   350", BLUE_M, 26)
        VGroup(c1, c2).arrange(DOWN, buff=0.2).move_to(src[0].get_center() + DOWN * 0.45)
        self.beat("Here is a source of card payments. It holds two of them.", FadeIn(src), FadeIn(c1), FadeIn(c2), run_time=1.2)

        tot = panel("totalCents", "wants a Source<Payment>", WHITE).move_to(RIGHT * 3.85 + DOWN * 0.15)
        sumv = M("sum = 0", 30, WHITE).move_to(tot[0].get_center() + DOWN * 0.45)
        flow = Arrow(src[0].get_right() + UP * 0.2, tot[0].get_left() + UP * 0.2, buff=0.12, stroke_width=4, color=GREY_B,
                     max_tip_length_to_length_ratio=0.1)
        flow_l = M("next()", 26, GREY_B).next_to(flow, UP, buff=0.15)
        self.beat("And here is totalCents. It wants a source of any Payment. It calls next until it gets null, and adds up the cents.",
                  FadeIn(tot), FadeIn(sumv), GrowArrow(flow), FadeIn(flow_l), run_time=1.6)
        self.beat("Can you hand it your source of card payments? Run the substitution test from lesson 3 of this track.",
                  Indicate(src[1], color=BLUE_M, scale_factor=1.06), run_time=1.0)

        def deliver(c, new_sum):
            return Succession(c.animate(run_time=1.0).move_to(tot[0].get_center() + DOWN * 0.45 + UP * 0.0).scale(0.8).set_opacity(0),
                              Transform(sumv, M(new_sum, 30, WHITE).move_to(sumv), run_time=0.4))

        self.beat("The only thing totalCents ever does with the source is call next. Each call hands back a CardPayment.",
                  deliver(c1, "sum = 1200"), run_time=1.6)
        ok = tick(True, 0.3).next_to(sumv, RIGHT, buff=0.3)
        self.beat("Every CardPayment is a Payment, so the sum works.", deliver(c2, "sum = 1550"), FadeIn(ok), run_time=1.6)

        back = DashedLine(tot[0].get_left() + DOWN * 0.75 + LEFT * 0.15, src[0].get_right() + DOWN * 0.75 + RIGHT * 0.15,
                          dash_length=0.12, stroke_width=3, color=GREY_B)
        back.add_tip(tip_length=0.2, tip_width=0.2)
        bx = tick(False, 0.26).move_to(back)
        nb = T("no member takes a T in", 26, RED_M).move_to(DOWN * 2.35)
        self.beat("Nothing can go wrong, because nothing ever goes into a source.",
                  Create(back), FadeIn(bx), FadeIn(nb, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(src, tot, sumv, flow, flow_l, ok, back, bx, nb, c1, c2)), run_time=0.6)

        # the compiler does not know
        prog = code(["fun totalCents(source: Source<Payment>): Long",
                     "val cards: Source<CardPayment> = ...",
                     "totalCents(cards)"], 26).move_to(UP * 0.7)
        err = VGroup(one("error: argument type mismatch: actual type is 'Source<CardPayment>',", 20, RED_M),
                     one("but 'Source<Payment>' was expected.", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        err.next_to(prog, DOWN, buff=0.5).align_to(prog, LEFT)
        self.beat("But the compiler can't see that by itself. Generic types are invariant unless you say otherwise.",
                  FadeIn(prog), run_time=1.2)
        self.beat("So this call fails, with an argument type mismatch.", FadeIn(err, shift=UP * 0.15),
                  Indicate(prog[2], color=RED_M, scale_factor=1.05), run_time=1.2)

        iface2 = one("interface Source<out T> { fun next(): T? }", 28, WHITE).move_to(iface)
        part(iface2, "out").set_color(GREEN_M)
        fine = one("// fine", 26, GREEN_M).next_to(prog[2], RIGHT, buff=0.5)
        self.beat("In Kotlin you say otherwise once, on the declaration, with out. Now the same call compiles.",
                  Transform(iface, iface2), FadeOut(err), FadeIn(fine), run_time=1.6)
        self.play(FadeOut(VGroup(prog, fine, iface)), run_time=0.6)

        # the arrow keeps its direction
        e_top = mbox("Payment", WHITE, w=3.4, size=28).move_to(LEFT * 3.4 + UP * 1.5)
        e_bot = mbox("CardPayment", BLUE_M, w=3.4, size=28).move_to(LEFT * 3.4 + DOWN * 1.5)
        e_ar = edge_arrow(e_bot, e_top, GREEN_M)
        e_lb = T("is a", 26, GREEN_M).next_to(e_ar, RIGHT, buff=0.15)
        s_top = mbox("Source<Payment>", WHITE, w=4.6, size=28).move_to(RIGHT * 2.9 + UP * 1.5)
        s_bot = mbox("Source<CardPayment>", BLUE_M, w=4.6, size=28).move_to(RIGHT * 2.9 + DOWN * 1.5)
        s_ar = edge_arrow(s_bot, s_top, GREEN_M)
        s_lb = T("is a", 26, GREEN_M).next_to(s_ar, RIGHT, buff=0.15)
        h1 = T("element types", 24, GREY_B).next_to(e_top, UP, buff=0.35)
        h2 = T("Source<out T>", 24, GREY_B).next_to(s_top, UP, buff=0.35)
        same = T("same direction", 26, GREEN_M).next_to(VGroup(e_bot, s_bot), DOWN, buff=0.55)
        self.beat("This is covariance. CardPayment is a subtype of Payment.",
                  FadeIn(VGroup(e_top, e_bot, h1)), GrowArrow(e_ar), FadeIn(e_lb), run_time=1.6)
        self.beat("Because Source is declared out, a Source of CardPayment is a subtype of a Source of Payment.",
                  FadeIn(VGroup(s_top, s_bot, h2)), GrowArrow(s_ar), FadeIn(s_lb), run_time=1.8)
        self.beat("The arrow between the elements carries over to the sources, in the same direction.",
                  FadeIn(same, shift=UP * 0.15), Indicate(VGroup(e_ar, s_ar), color=GREEN_M, scale_factor=1.1), run_time=1.4)
        self.play(FadeOut(VGroup(e_top, e_bot, e_ar, e_lb, s_top, s_bot, s_ar, s_lb, h1, h2, same)), run_time=0.6)

        # Java and Kotlin side by side
        jv = code(["interface Source<T> {",
                   "    T next();",
                   "}",
                   "",
                   "long totalCents(",
                   "    Source<? extends Payment> s)",
                   "",
                   "totalCents(cards);   // fine"], 24)
        kt = code(["interface Source<out T> {",
                   "    fun next(): T?",
                   "}",
                   "",
                   "fun totalCents(",
                   "    source: Source<Payment>): Long",
                   "",
                   "totalCents(cards)    // fine"], 24)
        part(jv[5], "? extends").set_color(GREEN_M)
        part(kt[0], "out").set_color(GREEN_M)
        part(jv[7], "// fine").set_color(GREY_B)
        part(kt[7], "// fine").set_color(GREY_B)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(DOWN * 0.1)
        self.beat("Java has no out keyword. Each Java method that takes a source says it at the use site, with ? extends.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.8,
                  say="Java has no out keyword. Each Java method that takes a source says it at the use site, with question mark extends.")
        self.beat("Kotlin's out is declaration-site variance. You write it once, on Source, and every caller gets it for free.",
                  Indicate(part(kt[0], "out"), color=GREEN_M, scale_factor=1.4), run_time=1.4)
        self.beat("Java's ? extends is use-site variance. A method that forgets it is stricter than it needs to be.",
                  Indicate(part(jv[5], "? extends"), color=GREEN_M, scale_factor=1.3), run_time=1.4,
                  say="Java's question mark extends is use-site variance. A method that forgets it is stricter than it needs to be.")
        self.play(FadeOut(pair), run_time=0.6)

        # the promise behind out
        pr = code(["interface Source<out T> {",
                   "    fun next(): T?        // T comes out: fine",
                   "    fun push(item: T)     // T goes in",
                   "}"], 26).move_to(UP * 0.9)
        part(pr[0], "out").set_color(GREEN_M)
        part(pr[1], "// T comes out: fine").set_color(GREEN_M)
        part(pr[2], "// T goes in").set_color(RED_M)
        perr = VGroup(one("error: type parameter 'T' is declared as 'out' but occurs in 'in' position", 20, RED_M),
                      one("in type 'T (of interface Source<out T>)'.", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        perr.next_to(pr, DOWN, buff=0.55).align_to(pr, LEFT)
        grp = VGroup(pr, perr)
        grp.scale(min(1, 12 / grp.width)).move_to(DOWN * 0.1)
        self.beat("That is the promise out makes: T only comes out.", FadeIn(pr[0]), FadeIn(pr[1]), FadeIn(pr[3]), run_time=1.2)
        self.beat("Add a method that takes a T in, and the compiler rejects the out, and tells you which position broke it.",
                  FadeIn(pr[2], shift=UP * 0.1), FadeIn(perr, shift=UP * 0.15), run_time=1.6)
        self.wait(0.8)
