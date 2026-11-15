from fg import *
import fg

# ---- helpers for this file (fg.py is shared and stays untouched) ----
# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\blload_0\b", "L load zero"), (r"\biload_2\b", "I load two"), (r"\bi2l\b", "I to L"),
           (r"\blmul\b", "L mul"), (r"\bldc2_w\b", "L D C two W"), (r"\bldiv\b", "L div"),
           (r"\blreturn\b", "L return"), (r"\bsipush\b", "S I push"), (r"\bladd\b", "L add"),
           (r" -v\b", " dash V"), (r"\bstack=4\b", "stack equals four"), (r"\blocals=3\b", "locals equals three"),
           (r"\bStackDemoKt\b", "Stack Demo K T"), (r"\bkotlinc\b", "kotlin C"), (r"\bamountMinor\b", "amount minor"),
           (r"\bbps\b", "B P S"), (r"\bthe l is\b", "the L is"), (r"\bthe i is\b", "the I is")]
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

LONG, INT, PROD, CONST, RES = BLUE_M, GOLD_M, PURPLE_M, TEAL_M, GREEN_M


class Beat(VoiceScene):
    """VoiceScene plus captions split only where a new sentence starts, and seq() to start animations at a
    given sentence of the line. A plan step may be a function, built when it starts."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def seq(self, text, plan=(), after=0.25):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            if callable(anims):
                anims = anims()
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


# Inside a Succession, manim adds every member to the scene when the Succession starts, so anything that
# should show up later must start invisible and appear through an updater (not FadeIn, an introducer).
def appear(m, run_time=0.3):
    m.set_opacity(0)

    def upd(mob, a):
        mob.set_opacity(a)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b, visible only while it runs."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = Dot(radius=0.1, color=color).move_to(a).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(a + (b - a) * smooth(t))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time + 0.12, rate_func=linear)


def flash(r, color, run_time=1.0, tw=0.6):
    """A passing flash along r's outline, invisible before and after it runs."""
    full = r.copy().set_fill(opacity=0).set_stroke(color, 7, opacity=1)
    m = full.copy().set_stroke(opacity=0).set_z_index(20)

    def upd(mob, a):
        hi = min(1.0, a * (1 + tw))
        lo = max(0.0, hi - tw)
        if a <= 0 or a >= 1 or hi <= lo:
            mob.set_stroke(opacity=0)
            return
        mob.pointwise_become_partial(full, lo, hi)
        mob.set_stroke(color, 7, opacity=1, family=False)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


class Pulse(Transform):
    """Indicate for filled boxes: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.06, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rbox(w, h, color, k=0.14, sw=3):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=sw)
    return r.set_fill(fill_of(color, k), opacity=1)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE, pitch=None):
    pitch = pitch or M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def block(value, color, w, h, name=None, vsize=26):
    r = rbox(w, h, color, k=0.2)
    v = M(value, vsize, color)
    if name:
        g = VGroup(T(name, 22, GREY_B), v).arrange(DOWN, buff=0.1).move_to(r)
    else:
        g = VGroup(v).move_to(r)
    return VGroup(r, g)


# frame geometry
CELL_W, CELL_H, CELL_Y = 1.9, 1.2, 2.35
CELL_X = [1.6, 3.5, 5.4]
WELL_X, WELL_B, WELL_T, WELL_W = 3.5, -3.2, 0.25, 3.0
U = 0.6                                    # one stack slot


def stack_y(depth_slots, h_slots):
    """centre y of a block h_slots tall whose bottom sits depth_slots above the well's floor"""
    return WELL_B + depth_slots * U + h_slots * U / 2


class Cls02Stack(Beat):
    """cls-02 section 1: feeMinor's seven instructions, run on the operand stack and the local slots."""

    def construct(self):
        self.title_card("The operand stack", "how the JVM runs one line of arithmetic")

        # ---------------- one line of source, then javap's listing ----------------
        js = code(["static long feeMinor(long amountMinor, int bps) {",
                   "    return amountMinor * bps / 10_000;",
                   "}"], 26)
        ks = code(["fun feeMinor(amountMinor: Long, bps: Int): Long =",
                   "    amountMinor * bps / 10_000"], 26)
        jh, kh = T("Java", 26, GREY_B), T("Kotlin", 26, GREY_B)
        ks.next_to(js, DOWN, buff=0.7).align_to(js, LEFT)
        jh.next_to(js[0], LEFT, buff=0.6)
        kh.next_to(ks[0], LEFT, buff=0.6).align_to(jh, LEFT)
        src = VGroup(js, ks, jh, kh)
        src.scale(min(1, 12.4 / src.width)).move_to([0, 0.3, 0])
        self.seq("Here is a card fee in Java and Kotlin: the amount times the rate in basis points, over ten thousand.",
                 [(0, [FadeIn(VGroup(js, jh), shift=UP * 0.15)], 0.8), (0, [FadeIn(VGroup(ks, kh), shift=UP * 0.15)], 0.8),
                  (0, [Indicate(VGroup(js[1][11:], ks[1][4:]), color=WHITE, scale_factor=1.05)], 1.0)])

        lst_src = ["0: lload_0", "1: iload_2", "2: i2l", "3: lmul", "4: ldc2_w #7   // long 10000", "7: ldiv", "8: lreturn"]
        lst = code(lst_src, 28, pitch=0.62)
        lst.move_to([-6.3, 2.0, 0], aligned_edge=UL)
        part(lst[4], "// long 10000").set_color(GREY_B)
        head = M("static long feeMinor(long, int);", 24, GREY_B).move_to([-6.3, 2.85, 0], aligned_edge=LEFT)
        self.seq("javap shows what javac made of the Java one. Seven instructions, and not one variable name. "
                 "It reads like noise, until you see the machine it runs on.",
                 [(0, [FadeOut(src, shift=UP * 0.2)], 0.6),
                  (0, [FadeIn(head), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in lst], lag_ratio=0.15)], 1.6),
                  (2, [Indicate(lst, color=WHITE, scale_factor=1.03)], 0.9)])

        # ---------------- the frame: local slots and the operand stack ----------------
        cells = VGroup(*[Rectangle(width=CELL_W, height=CELL_H, stroke_color=GREY_D, stroke_width=2).move_to([x, CELL_Y, 0])
                         for x in CELL_X])
        idx = VGroup(*[M(str(i), 24, GREY_B).next_to(c, DOWN, buff=0.15) for i, c in enumerate(cells)])
        slots_t = T("local variable slots", 24, GREY_B).next_to(cells, UP, buff=0.2)
        wl, wr = WELL_X - WELL_W / 2, WELL_X + WELL_W / 2
        well = VMobject(stroke_color=GREY_B, stroke_width=4).set_points_as_corners(
            [[wl, WELL_T, 0], [wl, WELL_B, 0], [wr, WELL_B, 0], [wr, WELL_T, 0]])
        well_t = T("operand stack", 24, GREY_B).move_to([WELL_X, WELL_T + 0.35, 0])
        self.seq("Each call gets a frame. Numbered slots hold the local variables. "
                 "The operand stack is a pile: instructions pop their inputs off the top, and push their results back.",
                 [(1, [Create(cells), FadeIn(idx), FadeIn(slots_t)], 1.0),
                  (2, [Create(well), FadeIn(well_t)], 1.0)])

        amt = block("125000L", LONG, 2 * CELL_W - 0.16, CELL_H - 0.16, "amountMinor")
        amt.move_to([(CELL_X[0] + CELL_X[1]) / 2, CELL_Y, 0])
        bps = block("290", INT, CELL_W - 0.16, CELL_H - 0.16, "bps").move_to([CELL_X[2], CELL_Y, 0])
        span = VGroup(idx[0], idx[1])
        self.seq("Call it with 125,000 cents and 290 basis points. amountMinor is a long, and a long fills two slots.",
                 [(0, [FadeIn(amt, shift=DOWN * 0.4)], 0.8),
                  (1, [Indicate(span, color=LONG, scale_factor=1.4), Pulse(amt, LONG, 1.04)], 1.0)])
        self.seq("So which slot does bps get? Pause on it.", [], after=2.0)
        self.seq("Slot 2. That's why the listing says iload_2.",
                 [(0, [FadeIn(bps, shift=DOWN * 0.4), Indicate(idx[2], color=INT, scale_factor=1.5)], 0.8),
                  (1, [Indicate(part(lst[1], "iload_2"), color=INT, scale_factor=1.15)], 0.9)])

        # ---------------- run it ----------------
        bar = RoundedRectangle(corner_radius=0.08, width=6.0, height=0.5, stroke_width=0)
        bar.set_fill(GREY_D, opacity=0.55).set_z_index(-1)

        def at(i):
            return bar.copy().move_to([-6.45 + 3.0, lst[i].get_center()[1], 0])

        bar.become(at(0))
        stack = []                                  # (block, height in slots)

        def depth():
            return sum(h for _, h in stack)

        def push_from(src_mob, value, color, h, vsize=26):
            b = block(value, color, WELL_W - 0.24, h * U - 0.08, vsize=vsize).move_to([WELL_X, stack_y(depth(), h), 0])
            c = src_mob.copy()
            stack.append((b, h))
            return [ReplacementTransform(c, b)]

        self.seq("Now run it. lload_0 copies the long from slot 0 onto the stack: the l is for long. "
                 "iload_2 copies the int from slot 2: the i is for int.",
                 [(0, [FadeIn(bar)], 0.4),
                  (1, lambda: push_from(amt, "125000L", LONG, 2, 28), 1.0),
                  (1, [Indicate(lst[0][2], color=LONG, scale_factor=1.6)], 0.6),
                  (2, lambda: [bar.animate.move_to(at(1))], 0.4),
                  (2, lambda: push_from(bps, "290", INT, 1, 26), 0.9),
                  (2, [Indicate(lst[1][2], color=INT, scale_factor=1.6)], 0.6)])

        self.seq("Next is a multiply, and lmul only takes two longs. The top of the stack is an int. What has to happen first?",
                 [(0, [Indicate(part(lst[3], "lmul"), color=WHITE, scale_factor=1.15)], 0.8),
                  (1, lambda: [Pulse(stack[-1][0], INT, 1.08)], 0.8)], after=2.0)

        def widen():
            b, _ = stack.pop()
            nb = block("290L", INT, WELL_W - 0.24, 2 * U - 0.08, vsize=28).move_to([WELL_X, stack_y(depth(), 2), 0])
            stack.append((nb, 2))
            return [ReplacementTransform(b, nb)]

        self.seq("i2l, int to long. It pops the 290 and pushes it back as a long, two slots tall.",
                 [(0, lambda: [bar.animate.move_to(at(2))], 0.4),
                  (1, widen, 1.0)])

        def combine(value, color):
            (b2, _), (b1, _) = stack.pop(), stack.pop()
            nb = block(value, color, WELL_W - 0.24, 2 * U - 0.08, vsize=28).move_to([WELL_X, stack_y(depth(), 2), 0])
            stack.append((nb, 2))
            return [ReplacementTransform(b1, nb), FadeOut(b2, target_position=nb.get_center())]

        self.seq("lmul pops both longs and pushes the product.",
                 [(0, lambda: [bar.animate.move_to(at(3))], 0.4),
                  (0, lambda: [Pulse(VGroup(stack[-1][0], stack[-2][0]), WHITE, 1.05)], 0.6),
                  (0, lambda: combine("36250000L", PROD), 0.9)])

        pool = VGroup(T("pool #7", 22, GREY_B), M("10000L", 24, CONST)).arrange(DOWN, buff=0.08)
        pool_b = rbox(1.35, 1.05, CONST, k=0.12).move_to([5.8, -1.0, 0])
        pool.move_to(pool_b)
        pool_g = VGroup(pool_b, pool)
        ghost = []

        def ghost_now():
            for b, _ in stack:
                ghost.append(DashedVMobject(b[0].copy().set_fill(opacity=0), num_dashes=30).set_stroke(b[0].get_stroke_color(), 2))
            return [Wait(0.01)]

        self.seq("ldc2_w pushes the long 10,000 from the constant pool. ldiv pops two longs and pushes 3,625.",
                 [(0, lambda: [bar.animate.move_to(at(4)), FadeIn(pool_g, shift=LEFT * 0.2)], 0.6),
                  (0, lambda: push_from(pool[1], "10000L", CONST, 2, 28), 0.9),
                  (0, ghost_now, 0.05),
                  (1, lambda: [bar.animate.move_to(at(5))], 0.4),
                  (1, lambda: combine("3625L", RES), 0.9)])

        caller = rbox(1.35, 0.75, WHITE, k=0.1).move_to([5.8, -2.75, 0])
        caller_t = T("caller", 24).move_to(caller)
        ret = M("3625L", 26, RES).move_to(caller).set_z_index(5)   # above the caller box

        def give_back():
            b, _ = stack.pop()
            return [ReplacementTransform(b, ret), FadeOut(caller_t)]

        self.seq("lreturn pops it and returns it: 36 euros and 25 cents.",
                 [(0, lambda: [bar.animate.move_to(at(6)), FadeIn(VGroup(caller, caller_t))], 0.5),
                  (0, give_back, 0.9)])

        g = VGroup(*ghost)
        br_s = Brace(VGroup(*[gg for gg in ghost]), LEFT, buff=0.35, color=GREY_B)
        br_s_t = M("stack=4", 26).next_to(br_s, LEFT, buff=0.15)
        slots_t2 = VGroup(T("local variable slots", 24, GREY_B), M("locals=3", 26)).arrange(RIGHT, buff=0.3).move_to(slots_t)
        self.seq("At its fullest, the stack held two longs, four slots. javap -v prints that as stack=4, and the slots as locals=3.",
                 [(0, [Create(g)], 0.9),
                  (1, [GrowFromCenter(br_s), FadeIn(br_s_t)], 0.7),
                  (1, [Transform(slots_t, slots_t2), Indicate(cells, color=WHITE, scale_factor=1.03)], 0.8)])
        self.play(FadeOut(VGroup(head, lst, bar, cells, idx, slots_t, well, well_t, amt, bps, pool_g, caller, ret,
                                 g, br_s, br_s_t)), run_time=0.6)

        # ---------------- Kotlin's listing ----------------
        jl = code(["0: lload_0", "1: iload_2", "2: i2l", "3: lmul", "4: ldc2_w #7 // long 10000", "7: ldiv", "8: lreturn"], 26, pitch=0.56)
        kl = code(["0: lload_0", "1: iload_2", "2: i2l", "3: lmul", "4: sipush 10000", "7: i2l", "8: ldiv", "9: lreturn"], 26, pitch=0.56)
        jt = VGroup(T("javac", 30), T("static, in class StackDemo", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        kt = VGroup(T("kotlinc", 30), T("public static final, in class StackDemoKt", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        jt.move_to([-6.1, 2.75, 0], aligned_edge=UL)
        kt.move_to([0.6, 2.75, 0], aligned_edge=UL)
        jl.move_to([-6.1, 1.55, 0], aligned_edge=UL)
        kl.move_to([0.6, 1.55, 0], aligned_edge=UL)
        self.seq("kotlinc's version is almost the same: a public static final method, on a class named StackDemoKt.",
                 [(0, [FadeIn(VGroup(jt, jl), shift=UP * 0.15)], 0.8), (0, [FadeIn(VGroup(kt, kl), shift=UP * 0.15)], 0.8),
                  (0, [Indicate(kt[1], color=WHITE, scale_factor=1.05)], 0.9)])
        diff_j = jl[4]
        diff_k = VGroup(kl[4], kl[5])
        same = VGroup(*[jl[i] for i in (0, 1, 2, 3, 5, 6)], *[kl[i] for i in (0, 1, 2, 3, 6, 7)])
        self.seq("Only the constant differs. javac loads a ready-made long from the constant pool. "
                 "kotlinc writes 10,000 into the instruction with sipush, then widens it with i2l. Same long on the stack.",
                 [(0, [same.animate.set_opacity(0.35), diff_j.animate.set_color(CONST), diff_k.animate.set_color(CONST)], 0.8),
                  (1, [Indicate(diff_j, color=CONST, scale_factor=1.06)], 0.9),
                  (2, [Indicate(kl[4], color=CONST, scale_factor=1.1)], 0.8),
                  (2, [Indicate(kl[5], color=CONST, scale_factor=1.15)], 0.8)])
        self.play(FadeOut(VGroup(jt, jl, kt, kl)), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Every instruction pops typed inputs off the stack", 36),
                      T("and pushes its result.", 36),
                      T("Its first letter names the type.", 36, LONG)).arrange(DOWN, buff=0.25).move_to([0, 0.2, 0])
        self.seq("The rule: every instruction pops typed inputs off the stack and pushes its result, "
                 "and its first letter names the type.",
                 [(0, [FadeIn(rule[:2], shift=UP * 0.15)], 0.9), (0, [FadeIn(rule[2], shift=UP * 0.15)], 0.7)])
        self.play(FadeOut(rule), run_time=0.5)

        qsrc = cline("return amountMinor * bps / 10_000 + 30;", 28)
        qsrc.remove(qsrc[0])
        part(qsrc, "+ 30").set_color(YELLOW_M)
        qsrc.move_to([0, 2.4, 0])
        tail = code(["7: ldiv", "   ?", "   lreturn"], 28, pitch=0.62).move_to([0, 0.2, 0])
        ans = code(["7: ldiv", "8: ldc2_w #9  // long 30", "11: ladd", "12: lreturn"], 28, pitch=0.62)
        part(ans[1], "// long 30").set_color(GREY_B)
        ans.move_to([0, 0.0, 0])
        for i in (1, 2):
            ans[i].set_color(YELLOW_M)
        part(ans[1], "// long 30").set_color(GREY_B)
        self.seq("A quick check. Add plus 30 at the end of the Java version. What appears between ldiv and lreturn?",
                 [(1, [FadeIn(qsrc, shift=UP * 0.15)], 0.7), (2, [FadeIn(tail, shift=UP * 0.15)], 0.7)], after=2.0)
        self.seq("ldc2_w pushes the long 30, then ladd adds the two longs.",
                 [(0, [ReplacementTransform(tail, ans)], 1.0)])
        self.wait(0.6)
