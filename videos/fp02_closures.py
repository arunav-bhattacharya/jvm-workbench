from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bmakeCounter\b", "make counter"), (r"\bpay_(\d)", r"pay \1")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads a different spelling than the caption shows), captions split
    only where a new sentence starts, seq() to start animations at a given sentence, and ask() for a
    question followed by a silent pause so the viewer can predict."""

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

    def ask(self, text, *anims, pause=1.6, say=None, run_time=None):
        """A question, then silence so the viewer can predict before the answer appears."""
        self.beat(text, *anims, after=pause, say=say, run_time=run_time)


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


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def chain(m, *steps):
    """Several changes of one mobject in a row, inside one Succession. Each target is built from the one
    before it (several m.animate builders on one mobject would all share the last target)."""
    cur, anims = m, []
    for fn, rt in steps:
        cur = cur.copy()
        fn(cur)
        anims.append(Transform(m, cur, run_time=rt))
    return Succession(*anims)


def moved(m, where):
    """Move m to an absolute place (safe to build next to other moves of m)."""
    return Transform(m, m.copy().move_to(where))


def xfade(old, new, rt=None):
    """Swap one label or token for another by cross-fading (a Transform between different glyphs smears)."""
    kw = {"run_time": rt} if rt else {}
    return AnimationGroup(FadeOut(old), FadeIn(new), **kw)


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def tok(text, color, size=28):
    """A value token: a small filled chip with monospace text."""
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=max(0.66, t.height + 0.34), stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color, 0.35), opacity=1)
    return VGroup(r, t.move_to(r))




def machine(label, color=GOLD_M, w=None, h=0.9, size=24):
    b = mbox(label, color, w=w, h=h, size=size)
    b.set_z_index(5)
    return b


def slot(label, w=2.4, h=0.9, color=GREY_B, size=24):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5).set_fill(BLACK, 1)
    l = M(label, size, color).next_to(r, UP, buff=0.12)
    return VGroup(r, l)


def pay(pid, amt, color=WHITE):
    r = RoundedRectangle(corner_radius=0.12, width=2.1, height=1.25, stroke_color=color, stroke_width=3).set_fill(fill_of(color, 0.1), 1)
    a = M(pid, 22, GREY_A); b = M(amt, 26, WHITE)
    VGroup(a, b).arrange(DOWN, buff=0.15).move_to(r)
    return VGroup(r, a, b)


def ref_box(value, w=3.7):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=1.5, stroke_color=PURPLE_M, stroke_width=3.5).set_fill(fill_of(PURPLE_M, 0.18), 1)
    h = M("Ref box", 24, PURPLE_M).move_to(r.get_top() + DOWN * 0.34)
    v = M("element = " + value, 30, WHITE).move_to(r.get_center() + DOWN * 0.22)
    return VGroup(r, h, v)


def set_ref(b, value):
    return Transform(b[2], M("element = " + value, 30, WHITE).move_to(b[2]).align_to(b[2], LEFT), run_time=0.3)


class Fp02Closures(Beat):
    """fp-02 section 3 (with section 0's rule-as-value opening): a lambda is a value, a closure keeps the
    variables it uses, and a captured var becomes one shared Ref box that threads update without a lock."""

    def construct(self):
        self.title_card("A lambda keeps what it uses", "functions as values, closures, and the hidden box")

        # ---------- a rule is a value ----------
        p = pay("pay_2", "900,000").move_to([-5.15, 0.4, 0])
        names = ["maxAmount", "servedCountry", "euroOnly"]
        rules = VGroup(*[machine(n, GOLD_M, size=24) for n in names]).arrange(RIGHT, buff=0.45).move_to([1.45, 0.4, 0])
        lst = SurroundingRectangle(rules, buff=0.3, corner_radius=0.15, color=GREY_B, stroke_width=2)
        lst_l = M("rules", 24, GREY_B).next_to(lst, UP, buff=0.15).align_to(lst, LEFT)
        rej = T("rejected: amount-limit", 26, RED_M).next_to(rules[0], DOWN, buff=0.75)
        self.seq("Fraud screening runs each payment through a list of rules. Here, 900,000 cents trips the amount limit.",
                 [(0, [FadeIn(p), LaggedStart(*[FadeIn(r) for r in rules], lag_ratio=0.2), Create(lst), FadeIn(lst_l)], 1.2),
                  (1, [p.animate.move_to(rules[0].get_left() + LEFT * 1.45)], 0.7),
                  (1, [Indicate(rules[0], color=RED_M, scale_factor=1.08), FadeIn(rej, shift=UP * 0.1)], 0.8)])

        var = slot("val maxAmount", w=rules[0].width + 0.5, h=1.25, color=GOLD_M).move_to([-1.0, 2.55, 0])
        var[1].next_to(var[0], LEFT, buff=0.3)
        r0_home = rules[0].get_center()
        runner = machine("firstRejection(p, rules)", WHITE, size=24).move_to([1.45, -1.75, 0])
        pass_ar = Arrow(lst.get_bottom(), runner.get_top(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        lam = T("a lambda: a function written as a value", 28, GOLD_M).move_to([0.0, -3.0, 0])
        self.seq("A rule here is a value, like a number. It sits in a variable, it goes into a list, and it gets passed around. "
                 "A function written as a value is called a lambda.",
                 [(0, [FadeOut(rej), moved(p, [-5.15, 0.4, 0])], 0.6),
                  (1, [FadeIn(var), moved(rules[0], var[0].get_center())], 0.8),
                  (1, [moved(rules[0], r0_home), FadeOut(var), Indicate(lst, color=WHITE, scale_factor=1.03)], 0.8),
                  (1, [GrowArrow(pass_ar), FadeIn(runner)], 0.7),
                  (2, [FadeIn(lam, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(p, rules[1], rules[2], lst, lst_l, pass_ar, runner, lam)), rules[0].animate.move_to([1.4, 0.1, 0]).scale(1.25), run_time=0.7)

        # ---------- a closure keeps what it uses ----------
        rule = rules[0]
        lim = slot("limit", w=2.4, h=0.9, color=BLUE_M)
        lim_v = M("500_000", 26, WHITE).move_to(lim[0])
        limg = VGroup(lim, lim_v).move_to([-3.6, 0.1, 0])
        lim[1].next_to(lim[0], UP, buff=0.12)
        w = DashedLine(lim[0].get_right(), rule.get_left(), dash_length=0.1, stroke_width=2.5, color=BLUE_M)
        reads = M("cents > limit", 24, WHITE).next_to(rule, UP, buff=0.3)
        self.seq("A lambda can also use a variable from outside its braces. This rule reads limit.",
                 [(0, [FadeIn(limg)], 0.6), (1, [FadeIn(reads), Create(w)], 0.8)])
        pocket = RoundedRectangle(corner_radius=0.08, width=2.7, height=0.75, stroke_color=BLUE_M, stroke_width=2.5).set_fill(fill_of(BLUE_M, 0.15), 1)
        pocket.next_to(rule, DOWN, buff=0.0)
        pk_v = M("limit = 500_000", 22, WHITE).move_to(pocket)
        clo = VGroup(rule, pocket, pk_v, reads)
        clo_l = T("closure", 30, GOLD_M).move_to(pocket.get_bottom() + RIGHT * 2.6 + DOWN * 0.45)
        self.seq("It carries that value along, wherever the rule goes. Code plus the variables it captured is called a closure.",
                 [(0, [FadeIn(pocket), TransformFromCopy(lim_v, pk_v)], 0.8),
                  (0, [FadeOut(w), clo.animate.shift(RIGHT * 2.6)], 0.9),
                  (1, [FadeIn(clo_l, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(clo, clo_l, limg)), run_time=0.6)

        # ---------- a captured var becomes a box ----------
        frame = RoundedRectangle(corner_radius=0.15, width=4.2, height=2.6, stroke_color=GREY_B, stroke_width=2.5).move_to([-3.9, 1.3, 0])
        frame_l = M("makeCounter()", 24, GREY_B).next_to(frame, UP, buff=0.15)
        cnt = VGroup(RoundedRectangle(corner_radius=0.1, width=2.6, height=0.85, stroke_color=PURPLE_M, stroke_width=2.5).set_fill(BLACK, 1),
                     M("count = 0", 26, WHITE))
        cnt[1].move_to(cnt[0]); cnt.move_to(frame.get_center() + DOWN * 0.15)
        cnt_l = M("var", 22, GREY_B).next_to(cnt, UP, buff=0.12)
        lamb = machine("{ ++count }", GOLD_M, w=2.8, h=1.0, size=26).move_to([3.4, 1.3, 0])
        lamb_l = T("the lambda it returns", 24, GOLD_M).next_to(lamb, UP, buff=0.2)
        lw = DashedLine(lamb.get_left(), cnt.get_right(), dash_length=0.1, stroke_width=2.5, color=GOLD_M)
        self.seq("Now capture a var, one that changes. makeCounter makes count, and returns a lambda that adds one to it.",
                 [(1, [Create(frame), FadeIn(frame_l), FadeIn(cnt), FadeIn(cnt_l)], 0.8),
                  (1, [FadeIn(lamb), FadeIn(lamb_l), Create(lw)], 0.8)])
        self.ask("When makeCounter returns, its local variables are gone. But the lambda still needs count. Where does count live?",
                 frame.animate.set_stroke(opacity=0.25), frame_l.animate.set_opacity(0.25), cnt_l.animate.set_opacity(0.25), run_time=1.0)
        box = ref_box("0").move_to([0, -1.7, 0])
        heap = T("on the heap", 24, PURPLE_M).next_to(box, DOWN, buff=0.2)
        a1 = Arrow(lamb.get_bottom(), box.get_right() + UP * 0.2, buff=0.12, stroke_width=3, color=GOLD_M, max_tip_length_to_length_ratio=0.12)
        self.seq("The compiler moves count into a small object on the heap, a Ref box with one plain field. The lambda points at the box.",
                 [(0, [FadeOut(lw), ReplacementTransform(cnt, box), FadeIn(heap), FadeOut(VGroup(frame, frame_l, cnt_l))], 1.4),
                  (1, [GrowArrow(a1)], 0.6)])
        self.seq("Call the lambda three times, and the box counts one, two, three.",
                 [(0, [Succession(*[Succession(Indicate(lamb, color=GOLD_M, scale_factor=1.08, run_time=0.4), set_ref(box, str(k)))
                                    for k in (1, 2, 3)])], 2.4)])
        self.play(FadeOut(VGroup(lamb, lamb_l, a1, heap)), Transform(box, ref_box("41").move_to([0, 1.6, 0])), run_time=0.8)

        # ---------- two threads, one box ----------
        tA = T("thread A", 28, BLUE_M).move_to([-4.6, 0.2, 0])
        tB = T("thread B", 28, TEAL_M).move_to([4.6, 0.2, 0])
        rA = mbox("reg = ?", BLUE_M, w=2.6, h=0.85, size=26).next_to(tA, DOWN, buff=0.3)
        rB = mbox("reg = ?", TEAL_M, w=2.6, h=0.85, size=26).next_to(tB, DOWN, buff=0.3)
        steps = T("++count is three steps: read the field, add one, write it back", 26, GREY_A).move_to([0, -2.9, 0])
        self.seq("Now hand that lambda to two threads at once. Each ++count is three steps: read the field, add one, write it back.",
                 [(0, [FadeIn(tA), FadeIn(tB), FadeIn(rA), FadeIn(rB)], 0.8), (1, [FadeIn(steps, shift=UP * 0.1)], 0.6)],
                 say="Now hand that lambda to two threads at once. Each plus plus count is three steps: read the field, add one, write it back.")

        def setr(r, text, color):
            return Transform(r, mbox(text, color, w=2.6, h=0.85, size=26).move_to(r), run_time=0.3)

        dA = M("41", 30, BLUE_M).move_to(box); dB = M("41", 30, TEAL_M).move_to(box)
        self.ask("Both threads read 41. What ends up in the box?",
                 Succession(AnimationGroup(dA.animate.move_to(rA), dB.animate.move_to(rB), run_time=0.8),
                            AnimationGroup(FadeOut(dA), FadeOut(dB), setr(rA, "reg = 41", BLUE_M), setr(rB, "reg = 41", TEAL_M), run_time=0.3)),
                 run_time=1.1)
        wA = M("42", 30, BLUE_M).move_to(rA).set_opacity(0); wB = M("42", 30, TEAL_M).move_to(rB).set_opacity(0)
        lost = T("two increments, one lost", 30, RED_M).move_to([0, 0.0, 0])
        self.seq("42. Both add one, and both write 42. Two increments, and one is lost.",
                 [(1, [setr(rA, "reg = 42", BLUE_M), setr(rB, "reg = 42", TEAL_M)], 0.5),
                  (1, [Succession(chain(wA, (lambda x: x.set_opacity(1), 0.1), (lambda x: x.move_to(box), 0.6), (lambda x: x.set_opacity(0), 0.1)),
                                  set_ref(box, "42"),
                                  chain(wB, (lambda x: x.set_opacity(1), 0.1), (lambda x: x.move_to(box), 0.6), (lambda x: x.set_opacity(0), 0.1)),
                                  Indicate(box[2], color=TEAL_M, scale_factor=1.1, run_time=0.4))], 2.4),
                  (2, [FadeIn(lost, shift=UP * 0.1), Flash(box, color=RED_M, flash_radius=1.9)], 0.7)])
        res = VGroup(T("four threads, 250,000 each", 26, GREY_A), M("expected 1,000,000", 28, WHITE), M("got        669,421", 28, RED_M))
        res.arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([0, -0.4, 0])
        self.seq("In the lesson's run, four threads each added 250,000, and the total came out 669,421, not a million.",
                 [(0, [FadeOut(VGroup(lost, steps, tA, tB, rA, rB)), FadeIn(res[0])], 0.6),
                  (0, [FadeIn(res[1]), FadeIn(res[2])], 0.7)])

        # the fix: don't share
        mines = VGroup(*[mbox("mine = 250,000", c, w=3.0, h=0.8, size=22) for c in (BLUE_M, TEAL_M, GOLD_M, GREEN_M)])
        mines.arrange(DOWN, buff=0.25).move_to([-2.2, -0.5, 0])
        tot = mbox("sum = 1,000,000", GREEN_M, w=3.6, h=0.9, size=26).move_to([3.6, -0.5, 0])
        arrs = VGroup(*[Arrow(m.get_right(), tot.get_left(), buff=0.1, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.1) for m in mines])
        ok = tick(True, 0.24).next_to(tot, DOWN, buff=0.3)
        self.seq("Nothing in the source looks shared. The compiler made the box. "
                 "The fix: let each task count its own, and add the results at the end.",
                 [(1, [Indicate(box, color=PURPLE_M, scale_factor=1.06)], 0.8),
                  (2, [FadeOut(res), FadeOut(box), LaggedStart(*[FadeIn(m) for m in mines], lag_ratio=0.15)], 1.0),
                  (2, [LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.1), FadeIn(tot), Create(ok)], 1.0)])
        self.play(FadeOut(VGroup(mines, tot, arrs, ok)), run_time=0.6)

        # ---------- code: Java and Kotlin ----------
        jv = code(["long[] total = {0};  // the box",
                   "pool.submit(() -> {",
                   "    for (int i = 0; i < 250_000; i++)",
                   "        total[0] += 1;",
                   "});"], 22)
        kt = code(["var total = 0L       // a Ref box",
                   "pool.submit {",
                   "    repeat(250_000) {",
                   "        total += 1",
                   "    }",
                   "}"], 22)
        part(jv[0], "// the box").set_color(GREY_B)
        part(kt[0], "// a Ref box").set_color(GREY_B)
        part(jv[0], "long[] total = {0};").set_color(PURPLE_M)
        part(kt[0], "var total = 0L").set_color(PURPLE_M)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pair.scale(min(1, 12.4 / pair.width)).move_to(UP * 0.2)
        self.seq("Java refuses to capture a local that changes, so you build the box yourself, a one-element array. "
                 "Kotlin builds the same box for you, without a word.",
                 [(0, [FadeIn(pair, shift=UP * 0.15)], 1.0), (0, [mark(part(jv[0], "long[] total = {0};"), PURPLE_M, 0.6)], 1.4),
                  (1, [mark(part(kt[0], "var total = 0L"), PURPLE_M, 0.6)], 1.4)])
        self.play(FadeOut(pair), run_time=0.6)

        # ---------- the rule, then a check ----------
        rule = VGroup(T("A lambda keeps the variables it uses.", 32),
                      T("A captured var is one shared box: keep other threads off it.", 28)).arrange(DOWN, buff=0.25).move_to([0, 2.55, 0])
        self.beat("The rule: a lambda keeps the variables it uses. A captured var is one shared box, so keep other threads off it.",
                  FadeIn(rule, shift=UP * 0.1), run_time=1.2)
        c1 = machine("counter 1", GOLD_M, w=2.6, h=0.9, size=24).move_to([-2.6, 0.5, 0])
        c2 = machine("counter 2", GOLD_M, w=2.6, h=0.9, size=24).move_to([2.6, 0.5, 0])
        self.ask("Quick check. Call makeCounter twice. Do the two counters share a box?", FadeIn(c1), FadeIn(c2), run_time=0.8)
        b1 = ref_box("0", w=3.2).move_to([-2.6, -1.7, 0]); b2 = ref_box("0", w=3.2).move_to([2.6, -1.7, 0])
        ar1 = Arrow(c1.get_bottom(), b1.get_top(), buff=0.1, stroke_width=3, color=GOLD_M, max_tip_length_to_length_ratio=0.15)
        ar2 = Arrow(c2.get_bottom(), b2.get_top(), buff=0.1, stroke_width=3, color=GOLD_M, max_tip_length_to_length_ratio=0.15)
        self.seq("No. Each call makes its own count, so each counter gets its own box.",
                 [(1, [FadeIn(b1), FadeIn(b2), GrowArrow(ar1), GrowArrow(ar2)], 1.0)])
        self.wait(1.0)
