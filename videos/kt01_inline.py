from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bnoinline\b", "no-inline")]

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


def rest_of(t, sub):
    """The glyphs of line t that are not inside substring sub."""
    i = t.src.index(sub)
    return VGroup(*t[:i], *t[i + len(sub):])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def place(g, left, top):
    """Put a code block so its left edge is at x=left and its first line's top at y=top."""
    g.shift(np.array([left - g.get_left()[0], top - g[0].get_top()[1], 0]))
    return g


LAM = "amountMinor * 3 / 100"


class Kt01Inline(Beat):
    """kt-01 section 0 (and section 2 in one closing beat): inline pastes the body and the lambda into the caller."""

    def construct(self):
        self.title_card("inline pastes the body into the caller", "Kotlin: no Function object, no interface call")

        helper = code(["fun <T> timedNotInline(label: String, block: () -> T): T {",
                       "    val start = System.nanoTime()",
                       "    try {",
                       "        return block()",
                       "    } finally {",
                       '        println("$label took ${(System.nanoTime() - start) / 1_000} us")',
                       "    }",
                       "}"], 22)
        place(helper, -5.9, 2.9)
        call = one('val fee = timedNotInline("fee") { ' + LAM + ' }', 24)
        part(call, "{ " + LAM + " }").set_color(GOLD_M)
        call.next_to(helper, DOWN, buff=0.7).align_to(helper, LEFT)
        self.beat("Here is a helper that every service has. It runs a block of code, and logs how long it took.",
                  FadeIn(helper, shift=UP * 0.15), run_time=1.2)
        self.seq("Here is a call. The lambda uses amountMinor from outside its braces, so it is a closure.",
                 [(0, [FadeIn(call, shift=UP * 0.15)], 0.8),
                  (1, [mark(part(call, "amountMinor"), GOLD_M, 1.0)], 1.8)])

        # ---- what the ordinary call costs, as Java
        top_call = call.copy().move_to(UP * 3.0)
        head = T("the call site, as Java (read back from the bytecode)", 24, GREY_B)
        jb = code([("Function0<Long> block = () -> " + LAM + ";").ljust(55) + "// invokedynamic",
                   'Object r = timedNotInline("fee", block);'.ljust(55) + "// invokestatic",
                   "long fee = ((Number) r).longValue();".ljust(55) + "// checkcast, unbox"], 22)
        part(jb[0], "() -> " + LAM).set_color(GOLD_M)
        for ln, c in zip(jb, ("// invokedynamic", "// invokestatic", "// checkcast, unbox")):
            part(ln, c).set_color(GREY_B)
        jb.move_to(UP * 1.15)
        head.next_to(jb, UP, buff=0.35).align_to(jb, LEFT)
        self.seq("Count what one call costs. Here is the call site, read back from the bytecode and written as Java.",
                 [(0, [FadeOut(helper), Transform(call, top_call)], 0.9),
                  (1, [FadeIn(head), FadeIn(jb, shift=UP * 0.15)], 1.0)])

        obj_r = RoundedRectangle(corner_radius=0.14, width=3.7, height=1.25, stroke_color=GOLD_M, stroke_width=3)
        obj_r.set_fill(fill_of(GOLD_M), opacity=1)
        obj_t = M("Function0 object", 24, GOLD_M)
        obj_f = M("amountMinor = 12000", 22, WHITE)
        VGroup(obj_t, obj_f).arrange(DOWN, buff=0.16).move_to(obj_r)
        obj = VGroup(obj_r, obj_t, obj_f).move_to([-4.3, -1.45, 0])
        tn = mbox("timedNotInline", WHITE, w=3.3, h=0.9, size=24).move_to([0.9, -1.45, 0])
        inv = Arrow(tn.get_left(), obj.get_right(), buff=0.12, stroke_width=4, color=RED_M, max_tip_length_to_length_ratio=0.12)
        inv_l = M("invoke()", 22, RED_M).next_to(inv, UP, buff=0.15)
        boxed = chip("Long 360", PURPLE_M, size=24, mono=True).move_to([5.0, -1.45, 0])
        unboxed = chip("long 360", PURPLE_M, size=24, mono=True).move_to(boxed)
        ret = Arrow(tn.get_right(), boxed.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        ret_l = M("Object", 22, GREY_B).next_to(ret, UP, buff=0.15)
        hl = SurroundingRectangle(jb[0], buff=0.08, color=GOLD_M, stroke_width=2.5, corner_radius=0.06)

        def hl_to(k, color):
            return Transform(hl, SurroundingRectangle(jb[k], buff=0.08, color=color, stroke_width=2.5, corner_radius=0.06))

        self.seq("First, invokedynamic builds a small object, a Function0. It holds a copy of amountMinor.",
                 [(0, [Create(hl)], 0.5), (0, [FadeIn(obj_r), FadeIn(obj_t)], 0.7), (1, [FadeIn(obj_f, shift=UP * 0.1)], 0.6)])
        self.seq("Then the call goes to timedNotInline. Inside it, block() calls that object's invoke method, a call through an interface.",
                 [(0, [hl_to(1, WHITE), FadeIn(tn)], 0.8),
                  (1, [GrowArrow(inv), FadeIn(inv_l)], 0.8)])
        summary = T("one object, one interface call, one unboxing, on every call", 26, GREY_A).move_to(DOWN * 3.0)
        self.seq("The helper is generic, so the result comes back as an Object, a boxed Long. "
                 "It has to be unboxed to a long. That is one object, one interface call and one unboxing, on every call.",
                 [(0, [hl_to(2, PURPLE_M), GrowArrow(ret), FadeIn(ret_l), FadeIn(boxed)], 1.0),
                  (1, [Transform(boxed, unboxed)], 0.7),
                  (2, [FadeIn(summary, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(call, head, jb, hl, obj, tn, inv, inv_l, boxed, ret, ret_l, summary)), run_time=0.7)

        # ---- inline: the compiler pastes the body and the lambda
        kf = code(["inline fun <T> timed(label: String, block: () -> T): T {",
                   "    val start = System.nanoTime()",
                   "    try {",
                   "        return block()",
                   "    } finally {",
                   '        println("$label took ${(System.nanoTime() - start) / 1_000} us")',
                   "    }",
                   "}"], 22)
        part(kf[0], "inline").set_color(BLUE_M)
        place(kf, -5.9, 2.75)
        kcall = one('val fee = timed("fee") { ' + LAM + ' }', 24)
        part(kcall, "{ " + LAM + " }").set_color(GOLD_M)
        kcall.next_to(kf, DOWN, buff=0.75).align_to(kf, LEFT)
        self.seq("Now mark the helper inline. The body stays the same, and so does the call.",
                 [(0, [FadeIn(kf, shift=UP * 0.15)], 1.0), (0, [mark(part(kf[0], "inline"), BLUE_M, 0.6)], 1.3),
                  (1, [FadeIn(kcall, shift=UP * 0.15)], 0.8)])

        jv = code(["long start = System.nanoTime();",
                   "long fee;",
                   "try {",
                   "    fee = " + LAM + ";",
                   "} finally {",
                   "    long us = (System.nanoTime() - start) / 1_000;",
                   '    System.out.println("fee took " + us + " us");',
                   "}"], 22)
        part(jv[3], LAM).set_color(GOLD_M)
        place(jv, -5.9, 2.35)
        jhead = T("the same call site, as Java, with inline", 24, GREY_B).next_to(jv, UP, buff=0.35).align_to(jv, LEFT)
        kp = code(["val start = System.nanoTime()",
                   "val fee = try {",
                   "    " + LAM,
                   "} finally {",
                   '    println("fee took ${(System.nanoTime() - start) / 1_000} us")',
                   "}"], 22)
        part(kp[2], LAM).set_color(GOLD_M)
        place(kp, -5.9, 2.35)
        khead = T("the call site, with the body pasted in", 24, GREY_B).next_to(kp, UP, buff=0.35).align_to(kp, LEFT)
        self.seq("At every call site, the compiler copies the function's body, and the body of the lambda you passed, instead of making a call.",
                 [(0, [FadeOut(kf[0]), FadeOut(kf[7]), FadeOut(rest_of(kcall, LAM))], 0.5),
                  (0, [Transform(VGroup(*kf[1][4:]), kp[0]), FadeTransform(kf[2], kp[1]), FadeOut(kf[3]),
                       Transform(VGroup(*kf[4][4:]), kp[3]), FadeTransform(kf[5], kp[4]), Transform(VGroup(*kf[6][4:]), kp[5])], 1.4),
                  (0, [ReplacementTransform(part(kcall, LAM), part(kp[2], LAM).set_z_index(10)), FadeIn(khead),
                       Succession(kp[4].animate(run_time=0.25).set_opacity(0.15), Wait(0.7), kp[4].animate(run_time=0.25).set_opacity(1))], 1.2)])
        self.remove(*self.mobjects)
        self.add(khead, kp)

        gone = VGroup(T("no Function0 object", 26, GREEN_M), T("no invoke()", 26, GREEN_M), T("no unboxing", 26, GREEN_M))
        gone.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([4.4, 1.3, 0])
        self.seq("Here is that call site read back from the bytecode, as Java. There is no Function0, no invoke, and no unboxing. "
                 "The multiply sits right inside the caller, between two calls to System.nanoTime.",
                 [(0, [FadeTransform(kp, jv), FadeTransform(khead, jhead)], 1.2),
                  (1, [LaggedStart(*[FadeIn(g, shift=LEFT * 0.15) for g in gone], lag_ratio=0.35)], 1.4),
                  (2, [mark(part(jv[3], LAM), GOLD_M, 0.4)], 1.0),
                  (2, [mark(part(jv[0], "System.nanoTime()"), WHITE, 0.3), mark(part(jv[5], "System.nanoTime()"), WHITE, 0.3)], 1.0)])
        self.remove(*self.mobjects)
        self.add(jhead, jv, gone)

        fin = VGroup(*jv[4:8])
        br = Brace(fin, RIGHT, buff=0.25, color=GREY_B)
        br_l = VGroup(T("in the bytecode twice:", 24, GREY_A), T("the normal exit and", 24, GREY_A),
                      T("the exit by exception", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        br_l.next_to(br, RIGHT, buff=0.25)
        self.seq("Read a bit further and you see the price. The finally block is in the bytecode twice: "
                 "once for the normal exit, and once for the exit by exception.",
                 [(0, [FadeOut(gone)], 0.5),
                  (1, [GrowFromCenter(br), FadeIn(br_l, shift=LEFT * 0.15)], 1.0)])

        names = ["forEach", "map", "filter", "let", "apply", "use", "repeat", "synchronized", "require"]
        chips = VGroup(*[chip(n, BLUE_M, size=24, mono=True) for n in names])
        row1 = VGroup(*chips[:5]).arrange(RIGHT, buff=0.3)
        row2 = VGroup(*chips[5:]).arrange(RIGHT, buff=0.3)
        rows = VGroup(row1, row2).arrange(DOWN, buff=0.3).move_to(DOWN * 2.2)
        self.seq("Every caller carries that copy. So inline is for small functions that take lambdas. "
                 "The standard library is full of them.",
                 [(0, [Indicate(fin, color=WHITE, scale_factor=1.02)], 0.9),
                  (2, [LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in chips], lag_ratio=0.12)], 1.4)])
        self.play(FadeOut(VGroup(jhead, jv, br, br_l, rows)), run_time=0.6)

        # ---- Java can't inline Kotlin code
        jc = code(['long fee = InlineDemoKt.timed("fee",',
                   "        () -> " + LAM + ");"], 24)
        kc = code(['val fee = timed("fee") {',
                   "    " + LAM,
                   "}"], 24)
        part(jc[1], "() -> " + LAM).set_color(GOLD_M)
        part(kc[1], LAM).set_color(GOLD_M)
        jn = T("a Function0 object, then invoke()", 24, RED_M)
        kn = T("pasted in: no object", 24, GREEN_M)
        jcol = VGroup(T("Java", 24, GREY_B), jc, jn).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc, kn).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        jn.align_to(kn, UP)
        pair.scale(min(1, 12.4 / pair.width)).move_to(UP * 0.2)
        self.seq("Java gets none of this. javac can't inline Kotlin code. "
                 "To Java, timed is an ordinary static method that takes a Function0, and the Java lambda becomes an object like any other.",
                 [(0, [FadeIn(VGroup(jcol[0], jc, kcol[0], kc), shift=UP * 0.15)], 1.0),
                  (2, [FadeIn(jn, shift=UP * 0.1), FadeIn(kn, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(pair), run_time=0.6)

        # ---- closing beat: noinline and crossinline
        mods = code(["inline fun subscribe(log: (String) -> Unit,",
                     "                     noinline listener: (String) -> Unit) {",
                     '    log("subscribing listener #${listeners.size + 1}")',
                     "    listeners += listener          // kept in a list",
                     "}",
                     "",
                     "inline fun runInBackground(executor: Executor,",
                     "                           crossinline task: () -> Unit) {",
                     "    executor.execute { task() }    // runs later, on a pool thread",
                     "}"], 22)
        part(mods[1], "noinline").set_color(PURPLE_M)
        part(mods[7], "crossinline").set_color(TEAL_M)
        part(mods[3], "// kept in a list").set_color(GREY_B)
        part(mods[8], "// runs later, on a pool thread").set_color(GREY_B)
        mods.scale(min(1, 12.4 / mods.width)).move_to(DOWN * 0.1)
        self.seq("One last rule. Pasting only works when the lambda runs right there, inside the inline function.",
                 [(0, [FadeIn(mods, shift=UP * 0.15)], 1.0)])
        self.seq("Store the lambda in a list, and the compiler asks for noinline. That one lambda stays a real object.",
                 [(0, [mark(part(mods[3], "listeners += listener"), WHITE, 0.5)], 1.2),
                  (0, [mark(part(mods[1], "noinline"), PURPLE_M, 0.8)], 1.4)])
        self.seq("Call it from inside a Runnable, and it asks for crossinline. "
                 "The body is still pasted, into a class generated for that call site, and a bare return is not allowed in it.",
                 [(0, [mark(part(mods[8], "{ task() }"), WHITE, 0.5)], 1.2),
                  (0, [mark(part(mods[7], "crossinline"), TEAL_M, 0.8)], 1.4)])
        self.wait(0.8)
