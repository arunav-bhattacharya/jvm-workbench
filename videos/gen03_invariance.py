from fg import *

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


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


class Gen03Invariance(Beat3):
    """gen-03 section 1: MutableList<String> is not a MutableList<Any>, or the String reader would crash."""

    def construct(self):
        self.title_card("A list of String is not a list of Any", "the substitution test, with one real list")

        # one list object with two slots
        s0, s1 = slot(), slot()
        cells = VGroup(s0, s1).arrange(RIGHT, buff=0.12).move_to(UP * 0.55)
        frame = SurroundingRectangle(cells, buff=0.16, corner_radius=0.16, color=GREY_D, stroke_width=2)
        idx = VGroup(M("[0]", 22, GREY_B).next_to(s0, DOWN, buff=0.32), M("[1]", 22, GREY_B).next_to(s1, DOWN, buff=0.32))
        what = T("one list object in memory", 22, GREY_B).next_to(idx, DOWN, buff=0.12)
        p1 = val('"pay_1"', BLUE_M).move_to(s0)
        lst = VGroup(frame, cells, idx, what)

        ids = M("ids: MutableList<String>", 28, BLUE_M).move_to(LEFT * 3.7 + UP * 2.75)
        anyl = M("anything: MutableList<Any>", 28, GOLD_M).move_to(RIGHT * 3.7 + UP * 2.75)
        a_ids = arrow(ids.get_bottom() + DOWN * 0.05, frame.get_corner(UL) + RIGHT * 1.0, BLUE_M)
        a_any = arrow(anyl.get_bottom() + DOWN * 0.05, frame.get_corner(UR) + LEFT * 1.0, GOLD_M)

        self.beat("Here is a mutable list of strings, called ids. It holds one payment id, pay_1.",
                  FadeIn(lst), FadeIn(p1), FadeIn(ids), GrowArrow(a_ids), run_time=1.6)

        sub = VGroup(M("String", 30, BLUE_M), M("Any", 30, GOLD_M)).arrange(RIGHT, buff=1.9).move_to(DOWN * 2.2)
        sub_a = edge_arrow(sub[0], sub[1], GREEN_M, buff=0.2)
        sub_l = T("is a", 24, GREEN_M).next_to(sub_a, UP, buff=0.08)
        subg = VGroup(sub, sub_a, sub_l)
        self.beat("String is a subtype of Any. Every String is an Any.", FadeIn(subg, shift=UP * 0.2), run_time=1.2)
        self.beat("So it looks harmless to use this list as a mutable list of Any. Suppose the compiler allowed it.",
                  FadeIn(anyl), GrowArrow(a_any), run_time=1.4)

        log = code(["val anything: MutableList<Any> = ids  // suppose",
                    "anything.add(42)",
                    "val second: String = ids[1]"], 24)
        log.move_to(DOWN * 2.25, aligned_edge=LEFT).set_x(-4.9, direction=LEFT)
        log[0].set_color(GOLD_M); log[1].set_color(GOLD_M); log[2].set_color(BLUE_M)
        part(log[0], "// suppose").set_color(GREY_B)
        self.beat("Now two names point at the same list. Nothing was copied.",
                  FadeOut(subg), FadeIn(log[0], shift=UP * 0.15), Indicate(frame, color=WHITE, scale_factor=1.03), run_time=1.6)

        n42 = val("42", GOLD_M).next_to(anyl, DOWN, buff=0.25).shift(RIGHT * 1.2)
        self.play(FadeIn(n42, scale=0.6), run_time=0.4)
        self.beat("Through the Any name, adding 42 is legal. 42 is an Int, and an Int is an Any.",
                  n42.animate.move_to(s1), FadeIn(log[1], shift=UP * 0.15), run_time=1.6)

        self.beat("Now code on the String side reads slot one. It was promised a String.",
                  FadeIn(log[2], shift=UP * 0.15), Indicate(ids, color=BLUE_M, scale_factor=1.05), run_time=1.2)
        ghost = n42.copy()
        self.play(ghost.animate.next_to(ids, DOWN, buff=0.25).shift(LEFT * 1.2), run_time=0.9)
        boom = one("// ClassCastException", 24, RED_M).next_to(log[2], RIGHT, buff=0.45)
        self.beat("The compiler put a hidden cast to String on that read. 42 is not a String, so the cast throws a ClassCastException.",
                  Flash(ghost, color=RED_M, flash_radius=0.7), ghost.animate.set_color(RED_M), FadeIn(boom, shift=LEFT * 0.2), run_time=1.4)
        self.beat("The bad value went in through one name. The crash comes out of the other, later, on a line with no cast in it.",
                  Indicate(log[1], color=GOLD_M, scale_factor=1.05), run_time=1.4)
        self.play(Indicate(VGroup(log[2], boom), color=RED_M, scale_factor=1.05), run_time=0.9)

        # Java: the same picture with Java names
        ids_j = M("ids: List<String>", 28, BLUE_M).move_to(ids)
        any_j = M("anything: List<Object>", 28, GOLD_M).move_to(anyl)
        log_j = code(["List<Object> anything = ids;  // suppose",
                      "anything.add(42);",
                      "String second = ids.get(1);"], 24)
        log_j.move_to(log, aligned_edge=UL)
        log_j[0].set_color(GOLD_M); log_j[1].set_color(GOLD_M); log_j[2].set_color(BLUE_M)
        part(log_j[0], "// suppose").set_color(GREY_B)
        boom_j = one("// ClassCastException", 24, RED_M).next_to(log_j[2], RIGHT, buff=0.45)
        self.beat("Java has the same problem, with a List of String and a List of Object.",
                  Transform(ids, ids_j), Transform(anyl, any_j), Transform(log, log_j), boom.animate.move_to(boom_j), run_time=1.8)
        self.beat("Same list, same 42, same crash on the read.",
                  Indicate(n42, color=GOLD_M), Indicate(ghost, color=RED_M), run_time=1.2)
        self.play(FadeOut(VGroup(lst, p1, n42, ghost, ids, anyl, a_ids, a_any, log, boom)), run_time=0.7)

        # both compilers refuse the assignment
        jl = T("Java", 24, GREY_B)
        jc = one("List<Object> anything = ids;", 26, GOLD_M)
        je = one("error: incompatible types: List<String> cannot be converted to List<Object>", 20, RED_M)
        kl = T("Kotlin", 24, GREY_B)
        kc = one("val anything: MutableList<Any> = ids", 26, GOLD_M)
        ke = VGroup(one("error: initializer type mismatch:", 20, RED_M),
                    one("expected 'MutableList<Any>', actual 'MutableList<String>'.", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        jb = VGroup(jl, jc, je).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        kb = VGroup(kl, kc, ke).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        both = VGroup(jb, kb).arrange(DOWN, aligned_edge=LEFT, buff=0.7)
        both.scale(min(1, 12 / both.width)).move_to(ORIGIN)
        self.beat("So both compilers refuse the line that makes the second name.",
                  FadeIn(jb[:2]), FadeIn(kb[:2]), run_time=1.2)
        self.beat("javac says the types are incompatible. kotlinc says the initializer type does not match.",
                  FadeIn(je, shift=UP * 0.1), FadeIn(ke, shift=UP * 0.1), run_time=1.4)
        self.play(FadeOut(both), run_time=0.6)

        # the rule: invariance
        head = T("Invariance", 40).to_edge(UP, buff=0.7)
        e_any = mbox("Any", GOLD_M, w=2.4, size=28).move_to(LEFT * 3.6 + UP * 1.2)
        e_str = mbox("String", BLUE_M, w=2.4, size=28).move_to(LEFT * 3.6 + DOWN * 1.6)
        e_ar = edge_arrow(e_str, e_any, GREEN_M)
        e_lb = T("is a", 24, GREEN_M).next_to(e_ar, RIGHT, buff=0.15)
        l_any = mbox("MutableList<Any>", GOLD_M, w=4.4, size=28).move_to(RIGHT * 2.9 + UP * 1.2)
        l_str = mbox("MutableList<String>", BLUE_M, w=4.4, size=28).move_to(RIGHT * 2.9 + DOWN * 1.6)
        l_ln = DashedLine(l_str.get_top(), l_any.get_bottom(), dash_length=0.1, stroke_width=2.5, color=GREY_D)
        l_x = tick(False, 0.3).move_to(l_ln)
        l_lb = T("no arrow", 24, RED_M).next_to(l_x, RIGHT, buff=0.25)
        self.beat("This rule is called invariance.", Write(head), run_time=1.0)
        self.beat("A mutable list of A is a subtype of a mutable list of B only when A and B are the same type.",
                  FadeIn(VGroup(l_any, l_str)), Create(l_ln), FadeIn(l_x), FadeIn(l_lb), run_time=2.0)
        self.beat("It does not matter that String is an Any. The arrow between the elements does not carry over to the lists.",
                  FadeIn(VGroup(e_any, e_str)), GrowArrow(e_ar), FadeIn(e_lb), run_time=1.8)
        self.play(Indicate(l_x, color=RED_M, scale_factor=1.3), run_time=0.8)
        self.play(FadeOut(VGroup(head, e_any, e_str, e_ar, e_lb, l_any, l_str, l_ln, l_x, l_lb)), run_time=0.6)

        # in real code
        sig = one("fun settle(batch: MutableList<Payment>)", 26, WHITE).move_to(UP * 2.4)
        sig.set_x(-5.0, direction=LEFT)
        call = one("settle(cards)   // does not compile", 26, WHITE).next_to(sig, DOWN, buff=0.3).align_to(sig, LEFT)
        part(call, "// does not compile").set_color(RED_M)
        c0 = val("card pay_1", BLUE_M)
        c1 = val("card pay_2", BLUE_M)
        cards = VGroup(c0, c1).arrange(RIGHT, buff=0.3)
        cframe = SurroundingRectangle(cards, buff=0.22, corner_radius=0.14, color=BLUE_M, stroke_width=2.5)
        clab = M("cards: MutableList<CardPayment>", 26, BLUE_M).next_to(cframe, DOWN, buff=0.25)
        cg = VGroup(cards, cframe, clab).move_to(LEFT * 1.6 + DOWN * 0.9)
        self.beat("You meet this in real code. You have a mutable list of CardPayment, and a function that takes a mutable list of Payment.",
                  FadeIn(sig), FadeIn(cg), run_time=1.6)
        self.beat("The call does not compile. Don't reach for a cast. Ask what the function does with the list.",
                  FadeIn(call, shift=UP * 0.1), run_time=1.0)

        sig2 = one("fun settle(batch: List<Payment>)", 26, WHITE).move_to(sig, aligned_edge=LEFT)
        part(sig2, "List<Payment>").set_color(GREEN_M)
        call2 = one("settle(cards)   // compiles", 26, WHITE).move_to(call, aligned_edge=LEFT)
        part(call2, "// compiles").set_color(GREEN_M)
        self.beat("If it only reads, make it take a read-only List of Payment. That call compiles. The last section of this lesson shows why.",
                  Transform(sig, sig2), Transform(call, call2), run_time=1.6)

        bt = val("transfer pay_7", PURPLE_M).move_to(RIGHT * 4.3).set_y(cframe.get_y())
        self.play(FadeIn(bt, shift=LEFT * 0.3), run_time=0.5)
        stop = tick(False, 0.3).next_to(cframe, RIGHT, buff=0.4)
        self.beat("If it adds, the compiler just caught a bug. It could have put a BankTransfer into your list of card payments.",
                  Succession(bt.animate(run_time=0.9).next_to(cframe, RIGHT, buff=0.15),
                             AnimationGroup(FadeIn(stop, scale=0.5), bt.animate.next_to(cframe, RIGHT, buff=1.1), run_time=0.6)),
                  run_time=1.5)
        self.wait(1.0)
