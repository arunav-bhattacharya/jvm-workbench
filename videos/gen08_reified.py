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


def listobj(values, colors, w=1.9, h=0.9):
    cells = VGroup(*[slot(w, h) for _ in values]).arrange(RIGHT, buff=0.1)
    frame = SurroundingRectangle(cells, buff=0.14, corner_radius=0.14, color=GREY_D, stroke_width=2)
    vals = VGroup(*[val(v, c, 26).move_to(s) for v, c, s in zip(values, colors, cells)])
    return VGroup(frame, cells, vals)


class Gen08Reified(Beat3):
    """gen-08 section 1: erasure removes T from objects; inline + reified copies the real class into each call site."""

    def construct(self):
        self.title_card("inline and reified bring T back", "type erasure, and Kotlin's way around it")

        cap = T("what the compiler checks", 26, GREY_B).move_to(UP * 2.95)
        l_ids = listobj(['"pay_1"', '"pay_2"'], [BLUE_M, BLUE_M]).move_to(LEFT * 3.5 + UP * 0.45)
        l_cts = listobj(["1200", "350"], [GOLD_M, GOLD_M]).move_to(RIGHT * 3.5 + UP * 0.45)
        n_ids = one("ArrayList<String>", 30, BLUE_M).next_to(l_ids, UP, buff=0.35)
        n_cts = one("ArrayList<Int>", 30, GOLD_M).next_to(l_cts, UP, buff=0.35)
        self.beat("Here are two lists. One holds payment ids. The other holds amounts in cents.",
                  FadeIn(l_ids), FadeIn(l_cts), FadeIn(n_ids), FadeIn(n_cts), run_time=1.4)
        self.beat("The compiler checks them as two different types.", FadeIn(cap),
                  Indicate(part(n_ids, "<String>"), color=BLUE_M, scale_factor=1.2),
                  Indicate(part(n_cts, "<Int>"), color=GOLD_M, scale_factor=1.2), run_time=1.4)

        cap2 = T("what exists at run time", 26, GREY_B).move_to(cap)
        r_ids = one("java.util.ArrayList", 30, GREY_A).move_to(n_ids)
        r_cts = one("java.util.ArrayList", 30, GREY_A).move_to(n_cts)
        self.play(part(n_ids, "<String>").animate.set_color(RED_M), part(n_cts, "<Int>").animate.set_color(RED_M), run_time=0.4)
        self.beat("Then it erases the type arguments. At run time both objects are the same class, java.util.ArrayList.",
                  Transform(cap, cap2), Transform(n_ids, r_ids), Transform(n_cts, r_cts), run_time=1.6)
        same = one("ids.javaClass == cents.javaClass   // true", 26, WHITE).move_to(DOWN * 2.0)
        part(same, "// true").set_color(GREY_B)
        self.beat("Nothing in the object says String. Ask each one for its class, and you get the same answer.",
                  FadeIn(same, shift=UP * 0.15), run_time=1.2)
        self.play(FadeOut(VGroup(cap, l_ids, l_cts, n_ids, n_cts, same)), run_time=0.6)

        bad = one("fun <T> isA(x: Any?) = x is T", 28, WHITE).move_to(UP * 0.5)
        bad_e = one("error: cannot check for instance of erased type 'T (of fun <T> isA)'.", 20, RED_M).next_to(bad, DOWN, buff=0.45)
        self.beat("So a check like x is T can't compile. At run time, there is no T to check against.",
                  FadeIn(bad), FadeIn(bad_e, shift=UP * 0.1), run_time=1.4)
        self.play(FadeOut(VGroup(bad, bad_e)), run_time=0.5)

        # inline copies the body; reified fills in the class
        dfn = one("inline fun <reified T> Any?.isA(): Boolean = this is T", 26, WHITE).move_to(UP * 2.75)
        part(dfn, "inline").set_color(GREEN_M)
        self.beat("Kotlin has one way around this. Mark the function inline.", Succession(FadeIn(dfn, shift=DOWN * 0.15, run_time=0.8),
                             Indicate(part(dfn, "inline"), color=GREEN_M, scale_factor=1.25, run_time=0.8)), run_time=1.6)

        you = code(["fun check(x: Any?) {",
                    "    println(x.isA<String>())",
                    "    println(x.isA<Long>())",
                    "}"], 26)
        you_h = T("you write", 24, GREY_B)
        youc = VGroup(you_h, you).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(LEFT * 3.4 + UP * 0.25)
        part(you[1], "String").set_color(BLUE_M)
        part(you[2], "Long").set_color(GOLD_M)
        self.beat("Now the compiler does not call it. It copies its body into every call site.",
                  FadeIn(youc, shift=UP * 0.15), run_time=1.2)
        self.beat("At each call site, the type argument is right there in the code. Here it is String. Here it is Long.",
                  Succession(Indicate(part(you[1], "String"), color=BLUE_M, scale_factor=1.3),
                             Indicate(part(you[2], "Long"), color=GOLD_M, scale_factor=1.3)), run_time=2.6)

        out = code(["fun check(x: Any?) {",
                    "    println(x is String)",
                    "    println(x is Long)",
                    "}"], 26)
        out_h = T("what the compiler emits", 24, GREY_B)
        outc = VGroup(out_h, out).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(RIGHT * 3.4 + UP * 0.25)
        outc.align_to(youc, UP)
        part(out[1], "x is String").set_color(BLUE_M)
        part(out[2], "x is Long").set_color(GOLD_M)
        body = part(dfn, "this is T")
        cp1, cp2 = body.copy(), body.copy()
        rest = VGroup(out_h, out[0], part(out[1], "println("), part(out[1], ")"), part(out[2], "println("), part(out[2], ")"), out[3])
        self.play(part(dfn, "reified").animate.set_color(GREEN_M), run_time=0.4)
        self.beat("Mark T reified, and the compiler writes that real class into each copy.",
                  FadeIn(rest),
                  Transform(cp1, part(out[1], "x is String")), Transform(cp2, part(out[2], "x is Long")), run_time=2.0)
        self.remove(cp1, cp2, rest)
        self.add(outc)

        bc_h = T("javap -c on the compiled check function", 22, GREY_B)
        bc = code(["public static final void check(java.lang.Object);",
                   "   5: instanceof  #24  // class java/lang/String",
                   "  21: instanceof  #38  // class java/lang/Long"], 22)
        part(bc[1], "class java/lang/String").set_color(BLUE_M)
        part(bc[2], "class java/lang/Long").set_color(GOLD_M)
        bcg = VGroup(bc_h, bc).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(DOWN * 2.35)
        self.beat("Here is javap on the compiled check function. There is no call to isA. There is an instanceof String, and an instanceof Long, right in the caller's own bytecode.",
                  FadeIn(bcg, shift=UP * 0.15), run_time=1.6)
        self.play(FadeOut(VGroup(dfn, youc, outc, bcg)), run_time=0.6)

        # the standard library: filterIsInstance
        items = [('"pay_1"', BLUE_M), ("1200L", GOLD_M), ("null", GREY_B), ('"pay_2"', BLUE_M), ("2.5", PURPLE_M)]
        chips = VGroup(*[val(t, c, 28) for t, c in items]).arrange(RIGHT, buff=0.35).move_to(UP * 1.6)
        p_lab = one("payload: List<Any?>", 26, GREY_A).next_to(chips, UP, buff=0.35)
        call = one("payload.filterIsInstance<String>()", 28, WHITE).move_to(DOWN * 0.1)
        part(call, "String").set_color(BLUE_M)
        self.beat("The standard library uses the same trick. Here is a list of mixed values.", FadeIn(chips), FadeIn(p_lab), run_time=1.2)
        keep = VGroup(chips[0], chips[3])
        drop = VGroup(chips[1], chips[2], chips[4])
        res = VGroup(chips[0].copy(), chips[3].copy()).arrange(RIGHT, buff=0.35).move_to(DOWN * 1.7)
        brk = VGroup(M("[", 34, GREY_A).next_to(res, LEFT, buff=0.15), M("]", 34, GREY_A).next_to(res, RIGHT, buff=0.15))
        self.beat("filterIsInstance of String keeps only the strings, with a real instanceof check on each one.",
                  FadeIn(call, shift=UP * 0.1), drop.animate.set_opacity(0.25),
                  Transform(keep.copy(), res), FadeIn(brk), run_time=2.0)
        self.play(*[FadeOut(m) for m in self.mobjects if isinstance(m, VMobject)], run_time=0.6)

        # the rules
        r1 = one("fun <reified T> notInline(x: Any) = x is T", 26, WHITE)
        r1e = one("error: only type parameters of inline functions can be reified.", 20, RED_M)
        r2 = one("fun <T> forward(x: Any) = x.isA<T>()", 26, WHITE)
        r2e = one("error: cannot use 'T' as reified type parameter. Use a class instead.", 20, RED_M)
        rg = VGroup(VGroup(r1, r1e).arrange(DOWN, aligned_edge=LEFT, buff=0.25),
                    VGroup(r2, r2e).arrange(DOWN, aligned_edge=LEFT, buff=0.25)).arrange(DOWN, aligned_edge=LEFT, buff=0.9)
        rg.move_to(ORIGIN)
        self.beat("It needs both words. Without inline, there is one compiled body for every caller, so there is nowhere to write the real class.",
                  FadeIn(rg[0], shift=UP * 0.1), run_time=1.4)
        self.beat("And the caller must know the type. A generic caller with a plain T has no class to copy in.",
                  FadeIn(rg[1], shift=UP * 0.1), run_time=1.4)
        self.play(FadeOut(rg), run_time=0.5)

        # Java passes the class by hand
        jv = code(["static boolean isA(Object x,",
                   "        Class<?> type) {",
                   "    return type.isInstance(x);",
                   "}",
                   "",
                   'isA("pay_1", String.class);'], 24)
        kt = code(["inline fun <reified T>",
                   "    Any?.isA() = this is T",
                   "",
                   "",
                   "",
                   '"pay_1".isA<String>()'], 24)
        part(jv[5], "String.class").set_color(BLUE_M)
        part(kt[5], "String").set_color(BLUE_M)
        part(kt[0], "reified").set_color(GREEN_M)
        part(kt[0], "inline").set_color(GREEN_M)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(UP * 0.2)
        self.beat("Java has no reified type parameters. The closest Java gets is to pass the Class object yourself.",
                  FadeIn(jcol, shift=UP * 0.2), run_time=1.4)
        self.beat("In Kotlin you name the type at the call, and the compiler fills in the class. Both calls return true.",
                  FadeIn(kcol, shift=UP * 0.2), run_time=1.4)
        self.play(Indicate(part(jv[5], "String.class"), color=BLUE_M, scale_factor=1.2),
                  Indicate(part(kt[5], "String"), color=BLUE_M, scale_factor=1.3), run_time=1.0)
        self.wait(0.8)
