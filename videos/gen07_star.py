from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"MutableList<\*>", "mutable list of star"), (r"(\w+)<\*>", r"\1 of star"), (r"(\w+)<\?>", r"\1 of question mark"),
           (r"(\w+)<in Nothing>", r"\1 of in Nothing"), (r"(\w+)<out (\w+)\?>", r"\1 of out nullable \2"),
           (r"(\w+)<out (\w+)>", r"\1 of out \2"), (r"(\w+)<(\w+)>", r"\1 of \2"),
           (r"\bAny\?", "nullable Any"), (r"\bMutableList\b", "mutable list"), (r"\bCardAuthorized\b", "Card Authorized"),
           (r"\bBigDecimal\b", "Big Decimal"), (r"\bCAP#1\b", "cap one"), (r"\bisEmpty\b", "is empty"),
           (r"\bremoveAt\b", "remove at"), (r"\blogAll\b", "log all"), (r"\badd\(null\)", "add null")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads a different spelling than the caption shows), captions split
    only where a new sentence starts, and seq() to start animations at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        dur = self._speak(text, say)
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

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


def cline(text, size=24, color=WHITE):
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


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def place(g, left, top):
    """Put a code block so its left edge is at x=left and its first line's top at y=top."""
    g.shift(np.array([left - g.get_left()[0], top - g[0].get_top()[1], 0]))
    return g




def slot(w=1.8, h=0.85):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=GREY_B, stroke_width=2.5)
    return r.set_fill(BLACK, opacity=1)


def val(text, color, size=26):
    return chip(text, color, size=size, mono=True)


def mlist(vals, color, sw=1.8):
    """A list object: a frame of slots, each holding a value chip."""
    slots = VGroup(*[slot(sw) for _ in vals]).arrange(RIGHT, buff=0.12)
    chips = VGroup(*[val(v, color).move_to(s) for v, s in zip(vals, slots)])
    frame = SurroundingRectangle(slots, buff=0.16, corner_radius=0.16, color=GREY_D, stroke_width=2)
    return VGroup(frame, slots, chips)


def dline(a, b, color=PURPLE_M, tip=True):
    d = DashedLine(a, b, dash_length=0.12, stroke_width=3, color=color)
    if tip:
        d.add_tip(tip_length=0.18, tip_width=0.18)
    return d


class Gen07StarProjection(Beat):
    """gen-07 sections 0 and 1: List<*> is a list of one type you don't know, and what * stands for depends on
    the declared variance (out: the bound, in: Nothing, invariant: both)."""

    def construct(self):
        self.title_card("A list of some type you don't know", "star projection: Kotlin's * and Java's ?")

        # ---- the problem: one helper for every list
        ids = mlist(['"pay_1"', '"pay_2"'], BLUE_M)
        cents = mlist(["1200", "350", "99"], GOLD_M)
        VGroup(ids, cents).arrange(RIGHT, buff=1.2).move_to(UP * 0.3)
        ids_n = M("ids: MutableList<String>", 24, BLUE_M).next_to(ids, DOWN, buff=0.3)
        cents_n = M("cents: MutableList<Int>", 24, GOLD_M).next_to(cents, DOWN, buff=0.3)
        self.seq("A logging helper has to take every list. A list of payment ids. A list of amounts in cents. "
                 "It never needs to know the element type.",
                 [(1, [FadeIn(ids), FadeIn(ids_n)], 0.8), (2, [FadeIn(cents), FadeIn(cents_n)], 0.8)])
        la = one("fun logAll(items: List<*>)", 28).move_to(UP * 2.6)
        part(la, "*").set_color(PURPLE_M)
        a1 = Arrow(la.get_bottom() + LEFT * 1.0, ids[0].get_top() + RIGHT * 0.6, buff=0.12, stroke_width=3, color=GREEN_M,
                   max_tip_length_to_length_ratio=0.12)
        a2 = Arrow(la.get_bottom() + RIGHT * 1.0, cents[0].get_top() + LEFT * 0.8, buff=0.12, stroke_width=3, color=GREEN_M,
                   max_tip_length_to_length_ratio=0.12)
        self.seq("Kotlin says that with a star projection: logAll takes a List<*>, and both lists fit.",
                 [(0, [FadeIn(la, shift=DOWN * 0.15)], 0.8), (0, [mark(part(la, "List<*>"), PURPLE_M, 0.5)], 1.1),
                  (0, [GrowArrow(a1), GrowArrow(a2)], 0.8)])

        # ---- one name, one list, an unknown element type
        sv = one("val star: MutableList<*> = ids", 26).move_to(UP * 2.55)
        part(sv, "*").set_color(PURPLE_M)
        part(sv, "star").set_color(PURPLE_M)
        to_ids = Arrow(sv.get_bottom() + LEFT * 1.6, ids[0].get_top() + RIGHT * 0.4, buff=0.1, stroke_width=4, color=PURPLE_M,
                       max_tip_length_to_length_ratio=0.12)
        to_cents = dline(sv.get_bottom() + RIGHT * 1.6 + DOWN * 0.1, cents[0].get_top() + LEFT * 0.6 + UP * 0.1)
        maybe = T("or this one?", 24, PURPLE_M).next_to(to_cents.get_center(), RIGHT, buff=0.25)
        self.seq("Read List<*> as a list of one specific type, and you don't know which. "
                 "Here star points at the list of ids, but the compiler only knows it is a list of something. "
                 "It could be the list of ints.",
                 [(1, [FadeOut(VGroup(la, a1, a2)), FadeIn(sv, shift=DOWN * 0.15)], 0.8),
                  (1, [GrowArrow(to_ids)], 0.7),
                  (2, [Create(to_cents), FadeIn(maybe)], 1.0)])

        # read: safe, comes out as Any?
        BOT = -1.85
        rd = one("val first: Any? = star[0]", 26).move_to([0, BOT, 0]).set_x(-6.2, direction=LEFT)
        out = ids[2][0].copy()
        ok = tick(True, 0.25)
        self.seq("Reading is safe. Whatever the list holds, each element comes out typed as Any?, which fits anything.",
                 [(0, [FadeIn(rd, shift=UP * 0.1)], 0.7),
                  (1, [out.animate.next_to(rd, RIGHT, buff=0.5).set_color(GREY_A)], 1.0),
                  (1, [FadeIn(ok.next_to(rd, RIGHT, buff=0.5 + out.width + 0.3))], 0.4)])
        self.play(FadeOut(VGroup(rd, out, ok)), run_time=0.5)

        # write: a String could land in a list of Int
        wr = one('star.add("pay_3")', 26).move_to([0, BOT, 0]).set_x(-6.2, direction=LEFT)
        werr = VGroup(one("Receiver type 'MutableList<*>' contains star projection", 20, RED_M),
                      one("which prohibits the use of 'fun add(element: E): Boolean'.", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        werr.next_to(wr, DOWN, buff=0.25).align_to(wr, LEFT)
        p3 = val('"pay_3"', BLUE_M).move_to([-0.3, 1.75, 0])
        stop = tick(False, 0.3).move_to([-0.75, 1.2, 0])
        self.seq("Writing is not safe. star might be the list of ints, so no String may go in.",
                 [(0, [FadeIn(wr, shift=UP * 0.1), FadeIn(p3, scale=0.7)], 0.7),
                  (1, [Indicate(VGroup(to_cents, maybe), color=PURPLE_M, scale_factor=1.05)], 0.9),
                  (1, [p3.animate.move_to([-0.75, 1.2, 0])], 0.6),
                  (1, [FadeIn(stop, scale=0.5), p3.animate.set_opacity(0.35), FadeIn(werr, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(wr, werr, p3, stop)), run_time=0.5)

        # null: the unknown type might be non-nullable
        nl = one("star.add(null)", 26).move_to([0, BOT, 0]).set_x(-6.2, direction=LEFT)
        nerr = one("Null cannot be a value of a non-null type 'CapturedType(*)'.", 20, RED_M)
        nerr.next_to(nl, DOWN, buff=0.25).align_to(nl, LEFT)
        pn = val("null", GREY_B).move_to([-0.3, 1.75, 0])
        stop2 = tick(False, 0.3).move_to([-0.75, 1.2, 0])
        self.seq("Kotlin doesn't even let null in, because the unknown type might be non-nullable.",
                 [(0, [FadeIn(nl, shift=UP * 0.1), FadeIn(pn, scale=0.7)], 0.7),
                  (0, [pn.animate.move_to([-0.75, 1.2, 0])], 0.6),
                  (0, [FadeIn(stop2, scale=0.5), pn.animate.set_opacity(0.35), FadeIn(nerr, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(VGroup(nl, nerr, pn, stop2)), run_time=0.5)

        # clear: takes no element, still allowed
        cl = one("star.clear()   // fine: takes no element", 26).move_to([0, BOT, 0]).set_x(-6.2, direction=LEFT)
        part(cl, "// fine: takes no element").set_color(GREEN_M)
        sizes = M("size   isEmpty()   removeAt(0)   clear()", 24, GREEN_M).next_to(cl, DOWN, buff=0.35).align_to(cl, LEFT)
        self.seq("Everything that doesn't take an element still works: size, isEmpty, removeAt and clear. "
                 "So a function that empties any buffer can take a MutableList<*>.",
                 [(0, [FadeIn(cl, shift=UP * 0.1)], 0.7),
                  (0, [FadeIn(sizes, shift=UP * 0.1)], 0.8),
                  (1, [FadeOut(ids[2], scale=0.6)], 0.9)])
        self.play(FadeOut(VGroup(sv, to_ids, to_cents, maybe, ids[0], ids[1], ids_n, cents, cents_n, cl, sizes)), run_time=0.6)

        # ---- Java's ? next to Kotlin's *
        jv = code(["static void logAll(List<?> items) {",
                   "    for (Object item : items) ...",
                   "}",
                   'star.add("pay_3");    // error',
                   "star.add(null);       // compiles"], 22)
        kt = code(["fun logAll(items: List<*>) {",
                   "    for (item in items) ...  // Any?",
                   "}",
                   'star.add("pay_3")     // error',
                   "star.add(null)        // error"], 22)
        part(jv[0], "?").set_color(PURPLE_M)
        part(kt[0], "*").set_color(PURPLE_M)
        part(jv[3], "// error").set_color(RED_M)
        part(kt[3], "// error").set_color(RED_M)
        part(kt[4], "// error").set_color(RED_M)
        part(jv[4], "// compiles").set_color(GREEN_M)
        part(kt[1], "// Any?").set_color(GREY_B)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(UP * 0.2)
        self.seq("Java writes the same idea as List<?>, the unbounded wildcard. Each element comes out as an Object.",
                 [(0, [FadeIn(VGroup(jcol[0], kcol[0], *jv[:3], *kt[:3]), shift=UP * 0.15)], 1.0),
                  (0, [mark(part(jv[0], "List<?>"), PURPLE_M, 0.5), mark(part(kt[0], "List<*>"), PURPLE_M, 0.5)], 1.2),
                  (1, [mark(part(jv[1], "Object"), WHITE, 0.6)], 1.2)],
                 say="Java writes the same idea as List of question mark, the unbounded wildcard. Each element comes out as an Object.")
        self.seq("A String can't go in on either side. Java is more relaxed about null: add(null) compiles on a List<?>, "
                 "because every Java reference type allows null.",
                 [(0, [FadeIn(jv[3], shift=UP * 0.1), FadeIn(kt[3], shift=UP * 0.1)], 0.8),
                  (1, [FadeIn(jv[4], shift=UP * 0.1), FadeIn(kt[4], shift=UP * 0.1)], 0.8),
                  (1, [mark(part(jv[4], "// compiles"), GREEN_M, 0.8)], 1.3)])
        self.play(FadeOut(pair), run_time=0.6)

        # ---- section 1: what * stands for depends on the declaration
        src = one("interface Source<out T : Number> { fun next(): T }", 26).move_to(UP * 2.9)
        part(src, "out T : Number").set_color(GREEN_M)
        st = mbox("Source<*>", PURPLE_M, h=0.9, size=24).move_to([-5.2, 0.3, 0])
        c1 = mbox("Source<Int>", WHITE, w=3.8, h=0.9, size=24).move_to([-1.3, 1.25, 0])
        c2 = mbox("Source<BigDecimal>", WHITE, w=3.8, h=0.9, size=24).move_to([-1.3, -0.65, 0])
        l1 = dline(st.get_right() + UP * 0.15, c1.get_left() + DOWN * 0.1)
        l2 = dline(st.get_right() + DOWN * 0.15, c2.get_left() + UP * 0.1)
        res = RoundedRectangle(corner_radius=0.14, width=2.6, height=2.2, stroke_color=GREEN_M, stroke_width=3)
        res.set_fill(fill_of(GREEN_M, 0.1), opacity=1).move_to([4.5, 0.3, 0])
        res_l = M("a Number", 24, GREEN_M).next_to(res, UP, buff=0.2)
        o1 = Arrow(c1.get_right(), res.get_left() + UP * 0.45, buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        o2 = Arrow(c2.get_right(), res.get_left() + DOWN * 0.45, buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        v1 = val("1200", GOLD_M).move_to(c1.get_right() + RIGHT * 0.6)
        v2 = val("19.99", YELLOW_M).move_to(c2.get_right() + RIGHT * 0.65)
        rule1 = one("Source<*>  means  Source<out Number>", 28).move_to(DOWN * 2.45)
        part(rule1, "*").set_color(PURPLE_M)
        part(rule1, "out Number").set_color(GREEN_M)
        self.seq("What the star stands for depends on the declaration. Take Source, declared out T, with the bound Number.",
                 [(0, [FadeIn(src, shift=DOWN * 0.15)], 0.9), (1, [mark(part(src, "out T : Number"), GREEN_M, 0.7)], 1.3)])
        self.seq("A Source<*> might be a Source<Int>, or a Source<BigDecimal>.",
                 [(0, [FadeIn(st), Create(l1), Create(l2), FadeIn(c1), FadeIn(c2)], 1.4)])
        self.seq("Whichever it is, next returns some Number. So reads keep the bound: Source<*> means Source<out Number>.",
                 [(0, [FadeIn(res), FadeIn(res_l), GrowArrow(o1), GrowArrow(o2), ], 0.8),
                  (0, [FadeIn(v1), FadeIn(v2)], 0.3),
                  (0, [v1.animate.move_to(res.get_center() + UP * 0.45), v2.animate.move_to(res.get_center() + DOWN * 0.45)], 1.0),
                  (1, [FadeIn(rule1, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(VGroup(src, st, c1, c2, l1, l2, res, res_l, o1, o2, v1, v2, rule1)), run_time=0.6)

        # Sink: in T, no value fits every candidate
        snk = one("interface Sink<in T> { fun accept(item: T) }", 26).move_to(UP * 2.9)
        part(snk, "in T").set_color(TEAL_M)
        st2 = mbox("Sink<*>", PURPLE_M, h=0.9, size=24).move_to([5.3, 0.3, 0])
        k1 = mbox("Sink<String>", WHITE, w=4.1, h=0.9, size=24).move_to([1.3, 1.25, 0])
        k2 = mbox("Sink<CardAuthorized>", WHITE, w=4.1, h=0.9, size=24).move_to([1.3, -0.65, 0])
        m1 = dline(st2.get_left() + UP * 0.15, k1.get_right() + DOWN * 0.1)
        m2 = dline(st2.get_left() + DOWN * 0.15, k2.get_right() + UP * 0.1)
        s_v = val('"pay_1"', BLUE_M).move_to([-5.0, 1.25, 0])
        a_v = val("auth pay_1", TEAL_M).move_to([-5.0, -0.65, 0])

        def go(a, b, good):
            ar = Arrow(a.get_right(), b.get_left(), buff=0.12, stroke_width=3, color=GREEN_M if good else RED_M,
                       max_tip_length_to_length_ratio=0.08)
            mk = tick(good, 0.2).move_to(ar.point_from_proportion(0.5 if good else 0.72))
            if good:
                mk.shift(UP * 0.25)
            return ar, mk

        g1, t1 = go(s_v, k1, True)
        b1, x1 = go(s_v, k2, False)
        g2, t2 = go(a_v, k2, True)
        b2, x2 = go(a_v, k1, False)
        rule2 = one("Sink<*>  means  Sink<in Nothing>", 28).move_to(DOWN * 2.45)
        part(rule2, "*").set_color(PURPLE_M)
        part(rule2, "in Nothing").set_color(RED_M)
        self.seq("Now take Sink, declared in T. A Sink<*> might be a Sink<String>, or a Sink<CardAuthorized>.",
                 [(0, [FadeIn(snk, shift=DOWN * 0.15)], 0.8),
                  (1, [FadeIn(st2), Create(m1), Create(m2), FadeIn(k1), FadeIn(k2)], 1.3)])
        self.seq("A String fits only the first. A card authorization fits only the second.",
                 [(0, [FadeIn(s_v), GrowArrow(g1), FadeIn(t1)], 0.8), (0, [GrowArrow(b1), FadeIn(x1)], 0.8),
                  (1, [FadeIn(a_v), GrowArrow(g2), FadeIn(t2)], 0.8), (1, [GrowArrow(b2), FadeIn(x2)], 0.8)])
        self.seq("No value is accepted by every one of them, so the compiler allows none. "
                 "Nothing is Kotlin's name for a type with no values. Sink<*> means Sink<in Nothing>.",
                 [(0, [Indicate(VGroup(x1, x2), color=RED_M, scale_factor=1.3)], 1.0),
                  (2, [FadeIn(rule2, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(VGroup(snk, st2, k1, k2, m1, m2, s_v, a_v, g1, t1, b1, x1, g2, t2, b2, x2, rule2)), run_time=0.6)

        # ---- the three rules side by side, and the invariant Box
        heads = [T("declared as", 22, GREY_B), T("the * stands for", 22, GREY_B), T("what you can do", 22, GREY_B)]
        X = [-6.0, -1.2, 2.7]
        r1 = [one("Source<out T : Number>", 22), one("Source<out Number>", 22), one("read: Number", 22, GREEN_M)]
        r2 = [one("Sink<in T>", 22), one("Sink<in Nothing>", 22), one("write: nothing fits", 22, RED_M)]
        r3 = [VGroup(one("class Box<T>", 22), T("(invariant)", 20, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.12),
              VGroup(one("Box<out Any?>", 22), one("Box<in Nothing>", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
              VGroup(one("read: Any?", 22, GREEN_M), one("write: nothing fits", 22, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)]
        rows = []
        for cells, y in ((heads, 2.55), (r1, 1.6), (r2, 0.65), (r3, -0.6)):
            for c, x in zip(cells, X):
                c.move_to([0, y, 0]).set_x(x, direction=LEFT)
            rows.append(VGroup(*cells))
        arrs = VGroup()
        for y in (1.6, 0.65, -0.6):
            arrs.add(Arrow([-2.3, y, 0], [-1.4, y, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.3),
                     Arrow([1.85, y, 0], [2.55, y, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.3))
        self.seq("So a star is shorthand for the safest projection the declaration allows.",
                 [(0, [FadeIn(rows[0])], 0.6),
                  (0, [FadeIn(rows[1]), FadeIn(arrs[0]), FadeIn(arrs[1])], 0.8),
                  (0, [FadeIn(rows[2]), FadeIn(arrs[2]), FadeIn(arrs[3])], 0.8)])
        bx = one('anyBox.item = "USD"', 24).move_to([0, -2.1, 0]).set_x(-6.0, direction=LEFT)
        berr = one("Assignment type mismatch: actual type is 'String', but 'Nothing' was expected.", 20, RED_M)
        berr.next_to(bx, DOWN, buff=0.22).align_to(bx, LEFT)
        self.seq("An invariant Box gets both rules. A Box<*> reads as Box<out Any?>, and writes as Box<in Nothing>. "
                 "Assign to its item, and the compiler names the type it wanted: Nothing.",
                 [(0, [FadeIn(r3[0]), FadeIn(arrs[4]), FadeIn(arrs[5])], 0.7),
                  (1, [FadeIn(r3[1][0]), FadeIn(r3[2][0])], 0.7),
                  (1, [FadeIn(r3[1][1]), FadeIn(r3[2][1])], 0.7),
                  (2, [FadeIn(bx, shift=UP * 0.1)], 0.6), (2, [FadeIn(berr, shift=UP * 0.1)], 0.6),
                  (2, [mark(part(berr, "'Nothing'"), RED_M, 0.8)], 1.2)],
                 say="An invariant Box gets both rules. A Box of star reads as Box of out nullable Any, and writes as Box of in Nothing. "
                     "Assign to its item, and the compiler names the type it wanted: Nothing.")
        self.play(FadeOut(VGroup(*rows, arrs, bx, berr)), run_time=0.6)

        # ---- Java's ? follows the same rules, except for null
        jj = code(["static Number peek(Source<?> s) {",
                   "    return s.next();  // a Number",
                   "}",
                   'anySink.accept("pay_1"); // error',
                   "anySink.accept(null);    // compiles"], 22)
        kk = code(["fun peek(s: Source<*>): Number =",
                   "    s.next()          // a Number",
                   "",
                   'anySink.accept("pay_1")  // error',
                   "anySink.accept(null)     // error"], 22)
        part(jj[0], "?").set_color(PURPLE_M)
        part(kk[0], "*").set_color(PURPLE_M)
        for ln in (jj[1], kk[1]):
            part(ln, "// a Number").set_color(GREEN_M)
        for ln in (jj[3], kk[3], kk[4]):
            part(ln, "// error").set_color(RED_M)
        part(jj[4], "// compiles").set_color(GREEN_M)
        jc = VGroup(T("Java", 24, GREY_B), jj).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kc = VGroup(T("Kotlin", 24, GREY_B), kk).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pr = VGroup(jc, kc).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pr.scale(min(1, 12 / pr.width)).move_to(UP * 0.2)
        self.seq("Java's question mark follows the same rules: the bound survives it, and a String can't go into a Sink<?>. "
                 "Only null gets through, and only in Java.",
                 [(0, [FadeIn(VGroup(jc[0], kc[0], *jj[:3], *kk[:3]), shift=UP * 0.15)], 1.0),
                  (0, [mark(part(jj[1], "// a Number"), GREEN_M, 0.4), mark(part(kk[1], "// a Number"), GREEN_M, 0.4)], 1.1),
                  (0, [FadeIn(jj[3], shift=UP * 0.1), FadeIn(kk[3], shift=UP * 0.1)], 0.8),
                  (1, [FadeIn(jj[4], shift=UP * 0.1), FadeIn(kk[4], shift=UP * 0.1)], 0.8),
                  (1, [mark(part(jj[4], "// compiles"), GREEN_M, 0.6)], 1.0)])
        self.wait(0.8)
