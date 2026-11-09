from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"Amount\.box-impl", "Amount dot box impl"), (r"@JvmInline", "J V M inline"), (r"@JvmName", "J V M name"), (r"\bjavap\b", "java P"),
           (r"\bamountMinor\b", "amount minor"), (r"\bconstructor-impl\b", "constructor impl"),
           (r"\bbox-impl\b", "box impl"), (r"\basGeneric\b", "as generic"), (r"\basNullable\b", "as nullable"),
           (r"\basInterface\b", "as interface"), (r"\blistOf\b", "list of"), (r"\bprintln\b", "print line"),
           (r"\bchargeFromJava\b", "charge from Java"), (r"\binit\b", "in-it")]

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


def heap(w, h, label="heap"):
    r = RoundedRectangle(corner_radius=0.18, width=w, height=h, stroke_color=GREY_C, stroke_width=2)
    r.set_fill(fill_of(GREY_D, 0.25), opacity=1)
    t = T(label, 24, GREY_B).move_to(r.get_corner(UL) + np.array([0.5, -0.3, 0]))
    return VGroup(r, t)


def longv(n, size=22, h=0.5):
    """A raw long value: teal, everywhere in this video."""
    t = M(f"long {n}", size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=h, stroke_color=TEAL_M, stroke_width=2.5)
    r.set_fill(TEAL_M, opacity=0.18)
    return VGroup(r, t)


def obj_frame(title, inner, color=GOLD_M, pad=0.18):
    """A real object on the heap: a frame with a class name above its field."""
    t = M(title, 20, color)
    w = max(inner.width, t.width) + 2 * pad
    p = pad * 0.8
    r = RoundedRectangle(corner_radius=0.14, width=w, height=inner.height + t.height + 3 * p,
                         stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color, 0.10), opacity=1)
    r.move_to(inner.get_center() + UP * (t.height + p) / 2)
    t.move_to(r.get_top() + DOWN * (p + t.height / 2))
    return VGroup(r, t)


class Kt02ValueClass(Beat):
    """kt-02 sections 0 and 1 (and section 2 in one closing beat): a value class is a type at compile time and
    its single field at run time, and it is boxed whenever it is used as another type."""

    def construct(self):
        self.title_card("Its own type, then a plain long", "Kotlin value classes, and when they get boxed")

        # ---- the problem: two Longs the compiler can't tell apart
        pa = code(["fun charge(amountMinor: Long): String",
                   "val orderId: Long = 981",
                   "charge(orderId)   // compiles"], 26)
        part(pa[2], "// compiles").set_color(RED_M)
        place(pa, -5.9, 2.6)
        self.seq("A Long parameter named amountMinor will take an order id without complaint. "
                 "Both are Long, so the compiler can't tell them apart.",
                 [(0, [FadeIn(pa, shift=UP * 0.15)], 1.0),
                  (1, [mark(part(pa[0], "Long"), WHITE, 0.4), mark(part(pa[1], "Long"), WHITE, 0.4)], 1.2)])

        pb = code(["class Cents(val value: Long)",
                   "fun charge(amount: Cents): String",
                   "charge(Cents(199))"], 26)
        part(pb[0], "Cents").set_color(BLUE_M)
        part(pb[1], "Cents").set_color(BLUE_M)
        place(pb, -5.9, 2.6)
        hp = heap(5.2, 4.4).move_to([3.6, -0.5, 0])
        o_in = M("value = 199", 22, WHITE)
        o1 = VGroup(obj_frame("Cents object", o_in), o_in).move_to([3.6, 0.35, 0])
        o_in2, o_in3 = M("value = 150", 22, WHITE), M("value = 49", 22, WHITE)
        o2 = VGroup(obj_frame("Cents object", o_in2), o_in2).move_to([2.35, -1.75, 0])
        o3 = VGroup(obj_frame("Cents object", o_in3), o_in3).move_to([4.85, -1.75, 0])
        ref = Arrow(pb[2].get_right() + RIGHT * 0.1, o1.get_left(), buff=0.12, stroke_width=3, color=GOLD_M,
                    max_tip_length_to_length_ratio=0.12)
        self.seq("The classic fix is a small wrapper class. It works, but every amount is now an extra object on the heap.",
                 [(0, [FadeOut(pa), FadeIn(pb, shift=UP * 0.15)], 1.0),
                  (1, [FadeIn(hp)], 0.5),
                  (1, [GrowArrow(ref), FadeIn(o1, scale=0.8)], 0.8),
                  (1, [LaggedStart(FadeIn(o2, scale=0.8), FadeIn(o3, scale=0.8), lag_ratio=0.4)], 0.9)])
        self.play(FadeOut(VGroup(pb, hp, o1, o2, o3, ref)), run_time=0.6)

        # ---- the value class: its own type at compile time
        vc = code(["@JvmInline",
                   "value class Cents(val value: Long) {",
                   "    init {",
                   '        require(value >= 0) { "negative amount: $value" }',
                   "    }",
                   "    operator fun plus(other: Cents): Cents = Cents(value + other.value)",
                   "}",
                   "",
                   'fun charge(amount: Cents): String = "charged $amount"'], 22)
        part(vc[0], "@JvmInline").set_color(BLUE_M)
        part(vc[1], "value class").set_color(BLUE_M)
        place(vc, -6.0, 2.9)
        self.seq("Kotlin's value class keeps the type safety, and wherever it can, it drops the object. "
                 "You write @JvmInline value class, with exactly one property.",
                 [(0, [FadeIn(vc, shift=UP * 0.15)], 1.2),
                  (1, [mark(vc[0], BLUE_M, 0.5), mark(part(vc[1], "value class"), BLUE_M, 0.5)], 1.3),
                  (1, [mark(part(vc[1], "val value: Long"), WHITE, 0.5)], 1.3)])

        bad = one("charge(199L)", 24).next_to(vc, DOWN, buff=0.6).align_to(vc, LEFT)
        err = one("error: argument type mismatch: actual type is 'Long', but 'Cents' was expected.", 20, RED_M)
        err.next_to(bad, DOWN, buff=0.25).align_to(bad, LEFT)
        self.seq("To the compiler, Cents is its own type. Hand charge a plain Long, and the call does not compile.",
                 [(0, [mark(part(vc[8], "amount: Cents"), BLUE_M, 0.6)], 1.3),
                  (1, [FadeIn(bad, shift=UP * 0.1)], 0.6),
                  (1, [FadeIn(err, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(vc, bad, err)), run_time=0.6)

        # ---- the Java view: what javap shows
        kl = [one("fun charge(amount: Cents)", 24),
              one("Cents(150)", 24),
              one("plus(other: Cents)", 24)]
        jl = [one("String charge-X49TzF8(long)", 24),
              one("long constructor-impl(long)", 24),
              one("long plus-dpzqtSM(long, long)", 24)]
        part(jl[0], "-X49TzF8").set_color(PURPLE_M)
        ys = [1.2, 0.0, -1.2]
        for k, j, y in zip(kl, jl, ys):
            k.move_to([0, y, 0]).set_x(-5.65, direction=LEFT)
            j.move_to([0, y, 0]).set_x(0.6, direction=LEFT)
        kh = T("Kotlin", 24, GREY_B).next_to(kl[0], UP, buff=0.6).align_to(kl[0], LEFT)
        jh = T("what javap -p shows", 24, GREY_B).next_to(jl[0], UP, buff=0.6).align_to(jl[0], LEFT)
        arrs = VGroup(*[Arrow([-1.0, y, 0], [0.4, y, 0], buff=0.05, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.18) for y in ys])
        self.seq("At run time, most of it is gone. Here is the Kotlin, next to what javap shows the compiler built.",
                 [(1, [FadeIn(kh), FadeIn(VGroup(*kl), shift=UP * 0.1)], 0.9),
                  (1, [FadeIn(jh), LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.2),
                       LaggedStart(*[FadeIn(j, shift=LEFT * 0.15) for j in jl], lag_ratio=0.2)], 1.3)])

        hl = SurroundingRectangle(VGroup(kl[0], jl[0]), buff=0.14, color=TEAL_M, stroke_width=2.5, corner_radius=0.08)

        def hl_to(i):
            return Transform(hl, SurroundingRectangle(VGroup(kl[i], jl[i]), buff=0.14, color=TEAL_M, stroke_width=2.5,
                                                      corner_radius=0.08))

        self.seq("charge takes a plain long, under a name with a hash on the end.",
                 [(0, [Create(hl)], 0.6), (0, [mark(part(jl[0], "(long)"), TEAL_M, 0.5)], 1.1),
                  (0, [mark(part(jl[0], "-X49TzF8"), PURPLE_M, 0.6)], 1.2)])
        self.seq("Cents(150) calls a static method, constructor-impl. It runs your init block and hands back the same long. "
                 "No object is created. plus became a static method that adds two longs.",
                 [(0, [hl_to(1)], 0.6),
                  (1, [mark(part(jl[1], "long constructor-impl"), TEAL_M, 0.6)], 1.3),
                  (3, [hl_to(2)], 0.6), (3, [mark(part(jl[2], "(long, long)"), TEAL_M, 0.5)], 1.2)])
        self.play(FadeOut(VGroup(kh, jh, *kl, *jl, arrs, hl)), run_time=0.6)

        # ---- one call, all longs, nothing on the heap
        call = one("charge(Cents(150) + Cents(49))", 28).move_to([-2.6, 2.5, 0])
        part(call, "Cents(150)").set_color(BLUE_M)
        part(call, "Cents(49)").set_color(BLUE_M)
        v150 = longv(150, 24, 0.6).next_to(part(call, "Cents(150)"), DOWN, buff=0.75)
        v49 = longv(49, 24, 0.6).next_to(part(call, "Cents(49)"), DOWN, buff=0.75)
        v199 = longv(199, 24, 0.6).move_to([-2.6, -0.1, 0])
        plus_l = M("plus-dpzqtSM", 22, GREY_B).next_to(v199, RIGHT, buff=0.35)
        fn = mbox("charge-X49TzF8(long)", WHITE, h=0.9, size=24).move_to([-2.6, -2.3, 0])
        hp2 = heap(4.3, 4.6).move_to([4.0, -0.3, 0])
        empty = T("no Cents object", 26, GREEN_M).move_to(hp2[0].get_center())
        self.seq("So this whole call runs on plain longs. No Cents object is ever made.",
                 [(0, [FadeIn(call, shift=UP * 0.1), FadeIn(hp2), FadeIn(v150, shift=DOWN * 0.2), FadeIn(v49, shift=DOWN * 0.2)], 0.9),
                  (0, [ReplacementTransform(VGroup(v150, v49), v199), FadeIn(plus_l)], 0.9),
                  (0, [FadeIn(fn), FadeOut(plus_l), v199.animate.next_to(fn, UP, buff=0.12)], 0.8),
                  (1, [FadeIn(empty, scale=0.9), hp2[0].animate.set_stroke(GREEN_M, 3)], 0.9)])
        self.play(FadeOut(VGroup(call, v199, fn, hp2, empty)), run_time=0.6)

        # ---- when it gets boxed
        rule = T("boxed whenever it is used as another type", 32, GOLD_M).move_to(UP * 3.1)
        top = code(["interface Priced { val minor: Long }",
                    "@JvmInline value class Amount(override val minor: Long) : Priced"], 22)
        part(top[1], "Amount").set_color(BLUE_M)
        place(top, -6.4, 2.55)
        decl = [one("class Invoice(val amount: Amount)", 22),
                one("fun <T> asGeneric(x: T): Any? = x", 22),
                one("fun asNullable(a: Amount?): Any? = a", 22),
                one("fun asInterface(p: Priced): Any = p", 22)]
        for d, y in zip(decl, [0.45, -0.55, -1.55, -2.55]):
            d.move_to([0, y, 0]).set_x(-6.4, direction=LEFT)
        decl = VGroup(*decl)
        alab = one("val a = Amount(1_999)", 22, GREY_A).move_to([0, 1.4, 0]).set_x(-6.4, direction=LEFT)
        aval = longv("1999").next_to(alab, RIGHT, buff=0.4)
        hp3 = heap(6.4, 4.9).move_to([3.2, -0.9, 0])
        self.seq("So when is a box needed? A value class is boxed whenever it is used as another type.",
                 [(1, [Write(rule)], 1.4)])
        self.seq("Here is a second value class, Amount. It implements an interface, Priced. Take one amount, a.",
                 [(0, [FadeIn(top, shift=UP * 0.15)], 0.9),
                  (2, [FadeIn(VGroup(alab, aval), shift=DOWN * 0.1), FadeIn(hp3)], 0.9)])

        # Invoice: a long field, no Amount box
        ci = aval.copy().set_z_index(3)
        fl = M("field amount:", 20, GREY_B)
        inv_inner = VGroup(fl, aval.copy()).arrange(RIGHT, buff=0.2).move_to([3.5, 0.6, 0])
        fi = obj_frame("Invoice object", inv_inner, WHITE)
        self.seq("In an Invoice, it is used as an Amount, so the field is a plain long.",
                 [(0, [FadeIn(decl[0], shift=UP * 0.1)], 0.6),
                  (0, [FadeIn(fi), ci.animate.move_to(inv_inner[1]), FadeIn(fl)], 1.0)])

        spots = [[1.65, -0.95, 0], [4.75, -0.95, 0], [1.65, -2.5, 0]]
        boxes = []

        def box_at(i):
            c = aval.copy().set_z_index(3)
            inner = c.copy().move_to(spots[i])
            fr = obj_frame("Amount object", inner, GOLD_M)
            boxes.append(VGroup(fr, c))
            return [c.animate.move_to(inner), FadeIn(fr, scale=1.15)]

        self.seq("Pass it to asGeneric, and it is used as a T. So the compiler calls box-impl first, and a real Amount object appears on the heap.",
                 [(0, [FadeIn(decl[1], shift=UP * 0.1)], 0.6), (1, box_at(0), 1.1)])
        self.seq("A nullable Amount has to be able to hold null, and a long can't. So that boxes too.",
                 [(0, [FadeIn(decl[2], shift=UP * 0.1)], 0.6), (1, box_at(1), 1.0)])
        # interface and Any: two more boxes, the last one inside a list
        lst_in = aval.copy().set_z_index(3)
        lst_inner = lst_in.copy().move_to([4.75, -2.5, 0])
        lst_box = obj_frame("Amount object", lst_inner, GOLD_M)
        lst = SurroundingRectangle(VGroup(lst_box, lst_inner), buff=0.12, corner_radius=0.12, color=GREY_B, stroke_width=2)
        lst_l = M("List", 20, GREY_B).next_to(lst, LEFT, buff=0.12).align_to(lst, UP)
        self.seq("Used as the interface Priced, it boxes. Used as Any, it boxes, and that covers every collection and println.",
                 [(0, [FadeIn(decl[3], shift=UP * 0.1)], 0.6), (0, box_at(2), 1.0),
                  (1, [lst_in.animate.move_to(lst_inner), FadeIn(lst_box, scale=1.15), Create(lst), FadeIn(lst_l)], 1.1)])
        self.play(FadeOut(VGroup(rule, top, decl, alab, aval, hp3, fi, ci, fl, *boxes, lst_in, lst_box, lst, lst_l)), run_time=0.6)

        # ---- the Java view of those call sites
        kc = code(["val a = Amount(1_999)",
                   "asGeneric(a)",
                   "asNullable(a)",
                   "asInterface(a)",
                   "listOf(a)"], 22)
        jc = code(["long a = Amount.constructor-impl(1_999L);",
                   "asGeneric(Amount.box-impl(a));",
                   "asNullable-nrJvU20(Amount.box-impl(a));",
                   "asInterface(Amount.box-impl(a));",
                   "CollectionsKt.listOf(Amount.box-impl(a));"], 22)
        for ln in jc[1:]:
            part(ln, "Amount.box-impl").set_color(GOLD_M)
        part(jc[2], "-nrJvU20").set_color(PURPLE_M)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        jcol = VGroup(T("as Java, read back from the bytecode", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        pair = VGroup(kcol, jcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(UP * 0.6)
        self.seq("Here are the same calls as Java, read back from the bytecode. Each time, Amount.box-impl runs right before the call that needs the object.",
                 [(0, [FadeIn(pair, shift=UP * 0.15)], 1.2),
                  (1, [LaggedStart(*[mark(part(jc[i], "Amount.box-impl"), GOLD_M, 0.3) for i in range(1, 5)], lag_ratio=0.3)], 2.2)])
        same = T("the same rule as long and Long in Java", 26, GREY_A).move_to(DOWN * 2.6)
        self.seq("It is the same rule Java uses for the primitive long and the boxed Long. "
                 "So a List of Amount holds one Amount object per element.",
                 [(0, [FadeIn(same, shift=UP * 0.1)], 0.8),
                  (1, [mark(part(jc[4], "listOf(Amount.box-impl(a))"), GOLD_M, 0.8)], 1.4)])
        self.play(FadeOut(VGroup(pair, same)), run_time=0.6)

        # ---- closing beat: mangled names and @JvmName
        kd = code(["fun charge(amount: Cents): String",
                   "",
                   '@JvmName("chargeFromJava")',
                   "fun chargeJava(amount: Cents): String"], 24)
        part(kd[2], '@JvmName("chargeFromJava")').set_color(PURPLE_M)
        jd = code(["ValueClassDemoKt.charge(199L);          // error: cannot find symbol",
                   "",
                   "ValueClassDemoKt.chargeFromJava(-5L);   // charged -5 cents"], 22)
        part(jd[0], "// error: cannot find symbol").set_color(RED_M)
        part(jd[2], "// charged -5 cents").set_color(RED_M)
        kd_col = VGroup(T("Kotlin", 24, GREY_B), kd).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        jd_col = VGroup(T("Java", 24, GREY_B), jd).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        stack = VGroup(kd_col, jd_col).arrange(DOWN, aligned_edge=LEFT, buff=0.7)
        stack.scale(min(1, 12 / stack.width)).move_to(DOWN * 0.1)
        jvm = one("charge-X49TzF8(long)", 24, PURPLE_M).next_to(kd[0], RIGHT, buff=0.9)
        jvm_a = Arrow(kd[0].get_right() + RIGHT * 0.1, jvm.get_left() + LEFT * 0.05, buff=0.05, stroke_width=3, color=GREY_B,
                      max_tip_length_to_length_ratio=0.15)
        self.seq("Now that name. The compiler adds a hash to every function that takes a value class. "
                 "A dash can't appear in a Java method name, so Java can't call charge.",
                 [(0, [FadeIn(kd_col[0]), FadeIn(kd[0], shift=UP * 0.1)], 0.8),
                  (1, [GrowArrow(jvm_a), FadeIn(jvm, shift=LEFT * 0.15)], 0.9),
                  (2, [FadeIn(jd_col[0]), FadeIn(jd[0], shift=UP * 0.1)], 0.9)])
        self.seq("@JvmName gives it a name Java can call. But Java passes a raw long, so the init block never runs, "
                 "and minus 5 cents gets charged.",
                 [(0, [FadeIn(VGroup(kd[2], kd[3]), shift=UP * 0.1)], 0.9),
                  (1, [FadeIn(jd[2], shift=UP * 0.1)], 0.8),
                  (1, [mark(part(jd[2], "// charged -5 cents"), RED_M, 0.8)], 1.4)])
        self.wait(0.8)
