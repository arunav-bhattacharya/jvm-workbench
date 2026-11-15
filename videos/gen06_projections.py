from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"MutableList<out (\w+)>", r"mutable list of out \1"), (r"MutableList<in (\w+)>", r"mutable list of in \1"),
           (r"MutableList<(\w+)>", r"mutable list of \1"), (r"\bMutableList\b", "mutable list"),
           (r"\? extends", "question mark extends"), (r"\? super", "question mark super"), (r"\bAny\?", "nullable Any"),
           (r"CAP#1", "cap one"), (r"amounts\.add\(0\)", "amounts dot add zero"), (r"\badd\(0\)", "add zero"),
           (r"\bremoveAt\b", "remove at"), (r"\bpadWithZeros\b", "pad with zeros"), (r"\bcopyInto\b", "copy into"),
           (r'"EUR"', "the string E U R"), (r"total\(cents\)", "total, called with cents,")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

INT_C, DBL_C, ANY_C = GOLD_M, PURPLE_M, GREY_A      # what is in the list
OUT_C, IN_C, ERR_C = BLUE_M, TEAL_M, RED_M          # the read view, the write view, a refusal

N = {
    "s1": "Here is a function that adds up amounts. It takes a MutableList of Number, and it only reads from it.",
    "s2": "You have cents, a MutableList<Int>. An Int is a Number. So does total(cents) compile?",
    "s3": "No. A MutableList<Int> is not a MutableList<Number>.",
    "s4": "A mutable list has two doors. get hands an element out. add takes one in.",
    "s5": "If cents could pass as a list of Number, total could push 2.5 through the add door, into a list of ints.",
    "s6": "The element type sits at both doors, so MutableList stays invariant.",
    "s7": "But total never uses the add door. So it asks for a view of the list with that door shut: MutableList<out Number>.",
    "s9": "Read it as: a list of some subtype of Number, and I don't know which. "
          "Now cents fits, and so does rates, a list of Doubles. Every read comes out as a Number.",
    "q1": "Now total calls amounts.add(0). Zero is an Int, and cents holds ints. Does it compile?",
    "s10": "No. Through the view, the compiler can't tell which list it has. It could be rates, and zero is not a Double.",
    "s11": "javac calls that unknown element type CAP#1. Nothing you can write is known to fit it, so nothing goes in.",
    "s12": "Calls that take no element, like clear, still work. The view limits types, not changes.",
    "s13": "Now flip it. padWithZeros only adds zeros. So it asks for the other view: MutableList<in Int>.",
    "s14": "A list of Int, of Number or of Any. Each one takes an Int, so add(0) is safe.",
    "s15": "Reading is the side that gets weaker. The first element might be \"EUR\", so a read comes back typed only as Any?, which fits anything.",
    "s16": "Writing out or in on one use of a type is called use-site variance. The view itself is a type projection.",
    "s17": "Java has only this kind of variance. Its ? extends is the read view, and ? super is the write view. "
           "Kotlin's out and in compile to exactly these wildcards.",
    "r": "The rule. A type that reads and writes T stays invariant. Only reads it: out, or ? extends. Only writes it: in, or ? super.",
    "c": "Quick check. copyInto reads from one mutable list, and adds each item to another. Which parameter gets out, and which gets in?",
    "a": "The from list gets out. The to list gets in.",
}
PAUSE = {"s2": 1.6, "q1": 2.2, "c": 2.4}


def cline(text, size=24, color=WHITE):
    """One code line. A hidden '|' in front keeps leading spaces and gives every line the same anchor."""
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


def mark(m, color=WHITE, hold=0.6):
    """Underline a few glyphs, then fade the line out. Never grows text into its neighbours like Indicate."""
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def slot(w=1.4, h=0.95):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=GREY_B, stroke_width=2.5)
    return r.set_fill(BLACK, opacity=1)


def val(text, color, size=28):
    return chip(text, color, size=size, mono=True)


class Gen06Projections(VoiceScene):
    """gen-06 section 0: an invariant MutableList has a read door and a write door; a use-site projection shuts one
    of them for one parameter. out (Java ? extends) is the read view and refuses add; in (Java ? super) is the write view."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def say(self, key, plan=(), after=0.25):
        """Speak N[key]; plan is a list of (sentence index, [animations], run_time), each started no earlier than its sentence."""
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))


    def construct(self):
        self.title_card("A view that only reads, or only writes", "use-site variance: out and in, ? extends and ? super")

        # ---------- the list: four slots, a read door on the left, a write door on the right
        LY = 0.35
        slots = VGroup(*[slot() for _ in range(4)]).arrange(RIGHT, buff=0.12).move_to([0, LY, 0])
        frame = SurroundingRectangle(slots, buff=0.16, corner_radius=0.16, color=GREY_B, stroke_width=2.5)
        FL, FR = frame.get_left()[0], frame.get_right()[0]

        def contents(vals):
            return VGroup(*[val(v, c).move_to(slots[i]) for i, (v, c) in enumerate(vals)])

        cents = contents([("1200", INT_C), ("350", INT_C), ("99", INT_C)])
        rates = contents([("2.5", DBL_C), ("1.5", DBL_C), ("4.75", DBL_C)])
        NAME_Y = LY - 1.35
        cents_n = M("cents: MutableList<Int>", 26, INT_C).move_to([0, NAME_Y, 0])
        rates_n = M("rates: MutableList<Double>", 26, DBL_C).move_to([0, NAME_Y, 0])
        TICK_P = [FR + 0.7, NAME_Y + 0.05, 0]
        BOT = -2.45

        sig = one("fun total(amounts: MutableList<Number>): Double", 28).move_to([0, 2.85, 0])
        self.say("s1", [(0, [FadeIn(sig, shift=DOWN * 0.15)], 0.8), (1, [mark(part(sig, "MutableList<Number>"), WHITE, 0.6)], 1.4)])
        self.say("s2", [(0, [Create(frame), FadeIn(slots)], 0.7), (0, [FadeIn(cents), FadeIn(cents_n)], 0.7)])

        no = tick(False, 0.3).move_to(TICK_P)
        err0 = T("compile error: a MutableList<Int> is not a MutableList<Number>", 28, ERR_C).move_to([0, BOT, 0])
        fit(err0, 12.4)
        self.say("s3", [(0, [FadeIn(no, scale=0.5)], 0.4), (1, [FadeIn(err0, shift=UP * 0.1)], 0.7)])

        # the two doors
        out_ar = Arrow([FL - 0.08, LY, 0], [FL - 1.5, LY, 0], buff=0, stroke_width=4, color=GREY_B, max_tip_length_to_length_ratio=0.18)
        in_ar = Arrow([FR + 1.5, LY, 0], [FR + 0.08, LY, 0], buff=0, stroke_width=4, color=GREY_B, max_tip_length_to_length_ratio=0.18)
        out_l = M("get(i)", 26, GREY_B).next_to(out_ar, UP, buff=0.3).shift(LEFT * 0.2)
        in_l = M("add(e)", 26, GREY_B).next_to(in_ar, UP, buff=0.3).shift(RIGHT * 0.2)
        OUT_X, IN_X = FL - 2.3, FR + 2.3
        rd = cents[0].copy()
        self.say("s4", [(0, [FadeOut(err0), FadeOut(no)], 0.4),
                        (1, [GrowArrow(out_ar), FadeIn(out_l)], 0.6),
                        (1, [rd.animate.move_to([OUT_X, LY, 0])], 0.8),
                        (2, [GrowArrow(in_ar), FadeIn(in_l)], 0.6)])

        bad = val("2.5", DBL_C).move_to([IN_X, LY, 0])
        self.say("s5", [(0, [FadeOut(rd), FadeIn(bad, scale=0.6)], 0.5),
                        (0, [bad.animate.move_to(slots[3])], 1.0),
                        (0, [frame.animate.set_stroke(ERR_C, 4), Flash(slots[3], color=ERR_C, flash_radius=1.0)], 0.7)])
        inv = T("invariant: it can't be declared out or in", 30, GREY_B).move_to([0, BOT, 0])
        self.say("s6", [(0, [FadeOut(bad), frame.animate.set_stroke(GREY_B, 2.5)], 0.5),
                        (0, [mark(out_l, WHITE, 0.4), mark(in_l, WHITE, 0.4)], 1.2),
                        (0, [FadeIn(inv, shift=UP * 0.1)], 0.6)])

        # ---------- the read view: out
        def dashed_view(color):
            return DashedVMobject(RoundedRectangle(corner_radius=0.22, width=frame.width + 0.44, height=frame.height + 0.44),
                                  num_dashes=70).set_stroke(color, 3).move_to(frame)

        view = dashed_view(OUT_C)
        VR = view.get_right()[0]
        gate = Rectangle(width=0.2, height=1.2, stroke_width=0).set_fill(OUT_C, 1).move_to([VR, LY, 0]).set_z_index(3)
        sig2 = one("fun total(amounts: MutableList<out Number>): Double", 28).move_to([0, 2.85, 0])
        part(sig2, "out Number").set_color(OUT_C)
        self.say("s7", [(0, [FadeOut(inv), in_l.animate.set_opacity(0.4)], 0.5),
                        (1, [Create(view)], 1.0), (1, [GrowFromEdge(gate, UP)], 0.5),
                        (1, [FadeTransform(sig, sig2)], 0.9), (1, [mark(part(sig2, "out"), OUT_C, 0.4)], 1.0)])

        gloss = T("a list of some subtype of Number", 30, OUT_C).move_to([0, 2.1, 0])
        ok = tick(True, 0.28).move_to(TICK_P)
        got = val("Number", OUT_C).move_to([OUT_X, LY, 0])
        rd2 = rates[0].copy()
        self.say("s9", [(0, [FadeIn(gloss, shift=DOWN * 0.1)], 0.7),
                        (1, [FadeIn(ok, scale=0.5)], 0.4),
                        (1, [FadeOut(cents), FadeIn(rates), FadeOut(cents_n), FadeIn(rates_n)], 0.7),
                        (2, [rd2.animate.move_to([OUT_X, LY, 0])], 0.8),
                        (2, [ReplacementTransform(rd2, got)], 0.6)])

        # the question: add(0) through the read view
        cents2 = contents([("1200", INT_C), ("350", INT_C), ("99", INT_C)])
        call = one("amounts.add(0)", 30).move_to([0, BOT, 0])
        zero = val("0", INT_C).move_to([IN_X, LY, 0])
        self.say("q1", [(0, [FadeOut(got), FadeOut(ok), FadeIn(call, shift=UP * 0.1), FadeIn(zero, scale=0.6)], 0.7),
                        (1, [FadeOut(rates), FadeIn(cents2), FadeOut(rates_n), FadeIn(cents_n)], 0.7)])

        rates2 = contents([("2.5", DBL_C), ("1.5", DBL_C), ("4.75", DBL_C)])
        stop = tick(False, 0.26).move_to([VR + 0.65, LY - 0.7, 0])
        self.say("s10", [(1, [FadeOut(cents2), FadeIn(rates2), FadeOut(cents_n), FadeIn(rates_n)], 0.8),
                         (2, [zero.animate.move_to([VR + 0.6, LY, 0])], 0.6),
                         (2, [FadeIn(stop, scale=0.5), zero.animate.move_to([IN_X, LY, 0])], 0.6)])

        cap = M("CAP#1", 24, GREY_B).move_to(slots[3])
        e1 = VGroup(one("Kotlin: Receiver type 'MutableList<out Number>' contains out projection", 22, ERR_C),
                    one("        which prohibits the use of 'fun add(element: E): Boolean'.", 22, ERR_C),
                    one("Java:   incompatible types: int cannot be converted to CAP#1", 22, ERR_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        fit(e1, 12.4).move_to([0, -2.55, 0])
        self.play(FadeOut(rates2), FadeOut(rates_n), FadeIn(cents), FadeIn(cents_n), FadeOut(call), run_time=0.5)
        self.say("s11", [(0, [FadeIn(cap, scale=0.8)], 0.6), (1, [FadeIn(e1, shift=UP * 0.1)], 0.8)])

        clr = VGroup(M("amounts.clear()", 30), tick(True, 0.24)).arrange(RIGHT, buff=0.3).move_to([0, BOT, 0])
        self.say("s12", [(0, [FadeOut(e1), FadeOut(cap)], 0.4), (0, [FadeIn(clr, shift=UP * 0.1)], 0.6),
                         (0, [LaggedStart(*[FadeOut(c, scale=0.6) for c in cents], lag_ratio=0.2)], 0.9)])

        # ---------- the write view: in
        ints = contents([("1200", INT_C), ("350", INT_C), ("99", INT_C)])
        nums = contents([("2.5", DBL_C), ("1200", INT_C), ("350", INT_C)])
        anys = contents([('"EUR"', ANY_C), ("2.5", DBL_C), ("99", INT_C)])
        ints_n = M("ints: MutableList<Int>", 26, INT_C).move_to([0, NAME_Y, 0])
        nums_n = M("numbers: MutableList<Number>", 26, WHITE).move_to([0, NAME_Y, 0])
        anys_n = M("anything: MutableList<Any>", 26, ANY_C).move_to([0, NAME_Y, 0])
        view2 = dashed_view(IN_C)
        sig3 = one("fun padWithZeros(target: MutableList<in Int>, count: Int)", 28).move_to([0, 2.85, 0])
        part(sig3, "in Int").set_color(IN_C)
        fit(sig3, 12.4)
        gloss2 = T("a list of Int, or of some supertype of Int", 30, IN_C).move_to([0, 2.1, 0])
        self.say("s13", [(0, [FadeOut(VGroup(clr, gloss, cents_n, zero, stop)), FadeOut(gate), in_l.animate.set_opacity(1),
                              ReplacementTransform(view, view2), FadeOut(sig2, shift=UP * 0.2)], 0.8),
                         (1, [FadeIn(sig3, shift=DOWN * 0.15)], 0.8),
                         (2, [mark(part(sig3, "in Int"), IN_C, 0.4)], 1.0), (2, [FadeIn(gloss2, shift=DOWN * 0.1)], 0.6)])

        z = [val("0", INT_C).move_to([IN_X, LY, 0]) for _ in range(3)]
        oks = [tick(True, 0.24).move_to(TICK_P) for _ in range(3)]

        def pad(k, lst, nm, prev=()):
            return [FadeIn(lst), FadeIn(nm), FadeIn(z[k], scale=0.6), *[FadeOut(p) for p in prev]]

        self.say("s14", [(0, pad(0, ints, ints_n), 0.45), (0, [z[0].animate.move_to(slots[3]), FadeIn(oks[0])], 0.55),
                         (0, pad(1, nums, nums_n, [ints, ints_n, z[0], oks[0]]), 0.45), (0, [z[1].animate.move_to(slots[3]), FadeIn(oks[1])], 0.55),
                         (0, pad(2, anys, anys_n, [nums, nums_n, z[1], oks[1]]), 0.45), (1, [z[2].animate.move_to(slots[3]), FadeIn(oks[2])], 0.55),
                         (1, [Indicate(in_l, color=IN_C, scale_factor=1.15)], 0.8)])

        rd3 = anys[0].copy()
        weak = val("Any?", ANY_C).move_to([OUT_X, LY, 0])
        self.say("s15", [(0, [mark(out_l, IN_C, 0.5)], 1.2),
                         (1, [Indicate(anys[0][1], color=WHITE, scale_factor=1.15)], 0.7),
                         (1, [rd3.animate.move_to([OUT_X, LY, 0])], 0.8), (1, [ReplacementTransform(rd3, weak)], 0.6)])

        n1 = T("use-site variance", 36, YELLOW_M).move_to([0, -2.2, 0])
        n2 = T("the view: a type projection", 30, WHITE).move_to([0, -2.95, 0])
        self.say("s16", [(0, [FadeOut(oks[2]), FadeOut(anys_n), Write(n1)], 1.0), (1, [FadeIn(n2, shift=UP * 0.1)], 0.7),
                         (1, [Indicate(view2, color=IN_C, scale_factor=1.02)], 0.8)])
        self.play(FadeOut(VGroup(frame, slots, anys, z[2], view2, out_ar, in_ar, out_l, in_l, weak, gloss2, sig3, n1, n2)),
                  run_time=0.7)

        # ---------- Java's wildcards are the same two views
        jl = code(["static double total(List<? extends Number> amounts)",
                   "static void padWithZeros(List<? super Integer> target, int count)"], 24)
        kl = code(["fun total(amounts: MutableList<out Number>): Double",
                   "fun padWithZeros(target: MutableList<in Int>, count: Int)"], 24)
        part(jl[0], "? extends Number").set_color(OUT_C)
        part(jl[1], "? super Integer").set_color(IN_C)
        part(kl[0], "out Number").set_color(OUT_C)
        part(kl[1], "in Int").set_color(IN_C)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.7, aligned_edge=LEFT).move_to([0, 0.1, 0])
        fit(both, 12.4)
        self.say("s17", [(0, [FadeIn(jg, shift=UP * 0.15)], 0.7),
                         (1, [mark(part(jl[0], "? extends"), OUT_C, 0.5)], 1.0), (1, [mark(part(jl[1], "? super"), IN_C, 0.5)], 1.0),
                         (2, [FadeIn(kg, shift=UP * 0.15)], 0.7),
                         (2, [mark(part(kl[0], "out"), OUT_C, 0.3), mark(part(kl[1], "in"), IN_C, 0.3)], 1.1)])
        self.play(FadeOut(both), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("A type that reads and writes T stays invariant.", 32),
                      T("Only reads it: out, or ? extends.", 32, OUT_C),
                      T("Only writes it: in, or ? super.", 32, IN_C)).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.8), (2, [FadeIn(rule[1], shift=UP * 0.1)], 0.7),
                       (3, [FadeIn(rule[2], shift=UP * 0.1)], 0.7)])
        chk = VGroup(T("Check: copyInto reads one mutable list and adds to another.", 28),
                     T("Which parameter gets out, and which gets in?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.85, 0])
        fit(chk, 12.4)
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = one("fun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>)", 24).move_to([0, -2.6, 0])
        part(ans, "out T").set_color(OUT_C)
        part(ans, "in T").set_color(IN_C)
        fit(ans, 12.4)
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.8)])
        self.wait(1.0)
