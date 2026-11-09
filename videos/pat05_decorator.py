from fg import *
import fg

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


def flash(r, color=YELLOW_M):
    return ShowPassingFlash(r.copy().set_fill(opacity=0).set_stroke(color, 7), time_width=0.6)


def fill_of(color, k=0.10):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


class Stack:
    """Nested boxes: box i sits inside box i-1, below its title band. Box 0 is the outside layer."""

    def __init__(self, n, top, bh, w0, ins=0.3, gap=0.16, cx=0.0):
        self.n, self.top, self.bh, self.w0, self.ins, self.gap, self.cx = n, top, bh, w0, ins, gap, cx

    def y(self, i):
        return self.top - i * self.bh - self.bh / 2

    def left(self, i):
        return self.cx - (self.w0 / 2 - i * self.ins)

    def right(self, i):
        return self.cx + (self.w0 / 2 - i * self.ins)

    def boxes(self, colors):
        inner_bottom = self.top - self.n * self.bh
        g = VGroup()
        for i in range(self.n):
            t = self.top - i * self.bh
            b = inner_bottom - (self.n - 1 - i) * self.gap
            r = RoundedRectangle(corner_radius=0.12, width=self.w0 - 2 * i * self.ins, height=t - b,
                                 stroke_color=colors[i], stroke_width=3)
            r.set_fill(fill_of(colors[i]), opacity=1).move_to([self.cx, (t + b) / 2, 0]).set_z_index(i)
            g.add(r)
        return g

    def label(self, i, name, desc, color, size=24, dsize=22, mono=True):
        nm = (M if mono else T)(name, size, color)
        nm.move_to([self.left(i) + 0.3 + nm.width / 2, self.y(i), 0])
        g = VGroup(nm)
        if desc:
            g.add(T(desc, dsize, GREY_B).next_to(nm, RIGHT, buff=0.35))
        return g.set_z_index(20)

    def value(self, i, text, color=GREEN_M, size=24):
        v = M(text, size, color)
        return v.move_to([self.right(i) - 0.3 - v.width / 2, self.y(i), 0]).set_z_index(20)


STREAM = [("DataOutputStream", "typed writes"), ("BufferedOutputStream", "buffering"),
          ("GZIPOutputStream", "compression"), ("out", "the real stream")]
FEE = [("cappedAt(500)", "at most 5.00", PURPLE_M),
       ('crossBorder("DE", 100)', "+1% if not from DE", GOLD_M),
       ("plusFixed(30)", "+0.30", TEAL_M),
       ("percent(290)", "2.9% of the amount", BLUE_M)]
LANE = 2.2


class Pat05Decorator(Beat):
    """pat-05 section 0: a decorator has the same interface, adds one behavior, forwards the call; order matters."""

    def construct(self):
        self.title_card("Decorator", "same interface, one more behavior")

        S = Stack(4, top=2.05, bh=0.8, w0=11.4)
        boxes = S.boxes([GREY_B] * 4)
        names = VGroup(*[S.label(i, n, None, WHITE) for i, (n, _) in enumerate(STREAM)])
        descs = VGroup(*[T(d, 22, GREY_B).next_to(names[i], RIGHT, buff=0.35).set_z_index(20) for i, (_, d) in enumerate(STREAM)])
        scode = one("new DataOutputStream(new BufferedOutputStream(new GZIPOutputStream(out)))", 22, GREY_A).move_to(UP * 3.05)

        def wrap(i):
            return AnimationGroup(FadeIn(boxes[i], scale=1.04), FadeIn(names[i]))

        self.seq("Java's own streams are built in layers. Start with the real stream. "
                 "Wrap it in a GZIPOutputStream, then a BufferedOutputStream, then a DataOutputStream.",
                 [(0, [FadeIn(scode, shift=DOWN * 0.15)], 0.8),
                  (1, [wrap(3), FadeIn(descs[3])], 0.7),
                  (2, [wrap(2)], 0.7), (2, [wrap(1)], 0.7), (2, [wrap(0)], 0.7)],
                 say="Java's own streams are built in layers. Start with the real stream. "
                     "Wrap it in a G zip output stream, then a buffered output stream, then a data output stream.")

        note = T("every layer is an OutputStream", 26, GREY_B).move_to(DOWN * 2.45)
        bytes_dot = Dot(radius=0.09, color=YELLOW_M).move_to([LANE, 2.4, 0]).set_z_index(30)
        self.seq("Each wrapper is an OutputStream too. Each one adds one behavior: typed writes, buffering, compression. "
                 "Then it passes the bytes on to the stream it wraps.",
                 [(0, [FadeIn(note, shift=UP * 0.15)], 0.7),
                  (1, [FadeIn(descs[0])], 0.5), (1, [FadeIn(descs[1])], 0.5), (1, [FadeIn(descs[2])], 0.5),
                  (2, [FadeIn(bytes_dot, run_time=0.2)], 0.2),
                  (2, [Succession(*[AnimationGroup(bytes_dot.animate.move_to([LANE, S.y(i), 0]), flash(boxes[i]))
                                    for i in range(4)])], 2.4),
                  (2, [FadeOut(bytes_dot)], 0.3)])

        self.beat("That is the decorator pattern. A decorator has the same interface as the object it wraps. "
                  "It does one extra thing, and forwards the call. The caller can't tell how many layers there are.",
                  Indicate(note, color=WHITE, scale_factor=1.06), run_time=1.2)

        # ---- the same shape for fees
        fboxes = S.boxes([c for _, _, c in FEE])
        flabels = VGroup(*[S.label(i, n, d, c) for i, (n, d, c) in enumerate(FEE)])
        fcode = one('standard = percent(290).plusFixed(30).crossBorder("DE", 100).cappedAt(500)', 22, WHITE).move_to(UP * 3.05)
        for (n, _, c) in FEE:
            part(fcode, n).set_color(c)
        self.seq("Fees fit the same shape, because a fee is a base rule plus adjustments.",
                 [(0, [FadeOut(note), ReplacementTransform(scode, fcode),
                       *[Transform(boxes[i], fboxes[i]) for i in range(4)],
                       *[FadeOut(VGroup(names[i], descs[i])) for i in range(4)],
                       *[FadeIn(flabels[i]) for i in range(4)]], 1.6)])
        self.seq("The base rule is 2.9 percent of the amount. Then each adjustment wraps it. "
                 "Add 30 cents. Add 1 percent more for a payment from outside Germany. Then cap the fee at 5 euros.",
                 [(0, [flash(boxes[3], BLUE_M), Indicate(flabels[3][0], color=BLUE_M, scale_factor=1.08)], 1.0),
                  (2, [flash(boxes[2], TEAL_M), Indicate(flabels[2][0], color=TEAL_M, scale_factor=1.08)], 1.0),
                  (3, [flash(boxes[1], GOLD_M), Indicate(flabels[1][0], color=GOLD_M, scale_factor=1.06)], 1.0),
                  (4, [flash(boxes[0], PURPLE_M), Indicate(flabels[0][0], color=PURPLE_M, scale_factor=1.08)], 1.0)])
        self.seq("Each call in the chain wraps everything to its left. So the last one, cappedAt, ends up on the outside.",
                 [(0, [mark(part(fcode, "percent(290)"), BLUE_M, 0.1)], 0.8),
                  (0, [mark(part(fcode, "plusFixed(30)"), TEAL_M, 0.1)], 0.8),
                  (0, [mark(part(fcode, 'crossBorder("DE", 100)'), GOLD_M, 0.1)], 0.8),
                  (1, [mark(part(fcode, "cappedAt(500)"), PURPLE_M, 0.4), flash(boxes[0], PURPLE_M)], 1.2)])

        # ---- a call travels in, the result travels back out
        caller = chip("standard.feeMinor(p)", WHITE, size=22, mono=True).move_to([LANE, 2.5, 0])
        pay = T("p: 1,000.00 EUR, from France", 24, GREY_B)
        pay.move_to([caller.get_left()[0] - 0.35 - pay.width / 2, 2.5, 0])
        call = Dot(radius=0.1, color=YELLOW_M).move_to(caller.get_bottom()).set_z_index(30)

        self.seq("Now charge a French payment of 1,000 euros. The call goes to the outside layer first. "
                 "Each layer calls the one it wraps, all the way in to the base rule.",
                 [(0, [FadeIn(caller), FadeIn(pay)], 0.8),
                  (1, [FadeIn(call, run_time=0.2)], 0.2),
                  (1, [call.animate.move_to([LANE, S.y(0), 0]), flash(boxes[0])], 0.7),
                  (2, [Succession(*[AnimationGroup(call.animate.move_to([LANE, S.y(i), 0]), flash(boxes[i]))
                                    for i in (1, 2, 3)])], 2.1)])

        res = Dot(radius=0.1, color=GREEN_M).move_to([LANE, S.y(3), 0]).set_z_index(30)
        vals1 = [S.value(3, "29.00"), S.value(2, "+0.30 = 29.30"), S.value(1, "+10.00 = 39.30"), S.value(0, "cap: 5.00")]
        out1 = M("= 5.00", 26, GREEN_M).next_to(caller, RIGHT, buff=0.3)
        self.seq("The base rule returns 29 euros. On the way back out, each layer does its one thing: 29.30, then 39.30. "
                 "The cap comes last, so the fee is 5 euros.",
                 [(0, [FadeOut(call, run_time=0.2), FadeIn(res, run_time=0.2), FadeIn(vals1[0])], 0.7),
                  (1, [res.animate.move_to([LANE, S.y(2), 0]), FadeIn(vals1[1])], 0.7),
                  (1, [res.animate.move_to([LANE, S.y(1), 0]), FadeIn(vals1[2])], 0.7),
                  (2, [res.animate.move_to([LANE, S.y(0), 0]), FadeIn(vals1[3])], 0.7),
                  (2, [res.animate.move_to(caller.get_bottom()), FadeIn(out1, shift=LEFT * 0.15)], 0.7),
                  (2, [FadeOut(res)], 0.3)],
                 say="The base rule returns twenty-nine euros. On the way back out, each layer does its one thing: "
                     "twenty-nine thirty, then thirty-nine thirty. The cap comes last, so the fee is five euros.")

        # ---- swap two layers
        fcode2 = one('standard = percent(290).plusFixed(30).cappedAt(500).crossBorder("DE", 100)', 22, WHITE).move_to(fcode)
        for (n, _, c) in FEE:
            part(fcode2, n).set_color(c)
        l0_to = flabels[0].copy().shift([S.ins, -S.bh, 0])
        l1_to = flabels[1].copy().shift([-S.ins, S.bh, 0])
        self.seq("Now move cappedAt in front of crossBorder. Same layers, in a different order.",
                 [(0, [FadeOut(VGroup(*vals1)), FadeOut(out1),
                       Transform(fcode, fcode2),
                       flabels[0].animate.move_to(l0_to), flabels[1].animate.move_to(l1_to),
                       boxes[0].animate.set_stroke(GOLD_M).set_fill(fill_of(GOLD_M), opacity=1),
                       boxes[1].animate.set_stroke(PURPLE_M).set_fill(fill_of(PURPLE_M), opacity=1)], 1.8)])

        res2 = Dot(radius=0.1, color=GREEN_M).move_to([LANE, S.y(3), 0]).set_z_index(30)
        vals2 = [S.value(3, "29.00"), S.value(2, "+0.30 = 29.30"), S.value(1, "cap: 5.00"), S.value(0, "+10.00 = 15.00", RED_M)]
        out2 = M("= 15.00", 26, RED_M).next_to(caller, RIGHT, buff=0.3)
        self.seq("Run the same payment. 29, then 29.30. The cap brings it down to 5. "
                 "Then the surcharge lands after the cap, and the fee is 15 euros.",
                 [(0, [FadeIn(res2), FadeIn(vals2[0])], 0.6),
                  (1, [res2.animate.move_to([LANE, S.y(2), 0]), FadeIn(vals2[1])], 0.7),
                  (2, [res2.animate.move_to([LANE, S.y(1), 0]), FadeIn(vals2[2])], 0.7),
                  (3, [res2.animate.move_to([LANE, S.y(0), 0]), FadeIn(vals2[3])], 0.7),
                  (3, [res2.animate.move_to(caller.get_bottom()), FadeIn(out2, shift=LEFT * 0.15)], 0.7),
                  (3, [FadeOut(res2)], 0.3)],
                 say="Run the same payment. Twenty-nine, then twenty-nine thirty. The cap brings it down to five. "
                     "Then the surcharge lands after the cap, and the fee is fifteen euros.")

        cmp_a = VGroup(M("cappedAt last:", 24, PURPLE_M), M("5.00", 26, GREEN_M)).arrange(RIGHT, buff=0.25)
        cmp_b = VGroup(M("cappedAt before crossBorder:", 24, PURPLE_M), M("15.00", 26, RED_M)).arrange(RIGHT, buff=0.25)
        cmp = VGroup(cmp_a, cmp_b).arrange(RIGHT, buff=1.0).move_to(DOWN * 2.45)
        cmp.scale(min(1, 12 / cmp.width))
        self.beat("Both chains compile. Only a test with a large cross-border payment tells them apart.",
                  FadeIn(cmp, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(boxes, flabels, fcode, caller, pay, out2, cmp, *vals2)), run_time=0.7)
        self.remove(call, res, res2)

        # ---- behavior decorators: retry and logging
        A = Stack(3, top=1.75, bh=0.75, w0=5.8, cx=-3.35)
        B = Stack(3, top=1.75, bh=0.75, w0=5.8, cx=3.35)
        ab = A.boxes([WHITE, WHITE, GREY_B])
        bb = B.boxes([WHITE, WHITE, GREY_B])
        al = VGroup(A.label(0, "retry, 3 attempts", None, WHITE, 24, mono=False), A.label(1, "logging", None, WHITE, 24, mono=False),
                    A.label(2, "charge", None, GREY_B, 24, mono=False))
        bl = VGroup(B.label(0, "logging", None, WHITE, 24, mono=False), B.label(1, "retry, 3 attempts", None, WHITE, 24, mono=False),
                    B.label(2, "charge", None, GREY_B, 24, mono=False))
        ha = T("retry outside logging", 26, GREY_B).move_to([A.cx, 2.6, 0])
        hb = T("logging outside retry", 26, GREY_B).move_to([B.cx, 2.6, 0])
        ax, bx = A.right(2) - 0.6, B.right(2) - 0.6

        def logline(stack, k):
            return M("log: charge", 22, YELLOW_M).move_to([stack.cx, -1.35 - 0.42 * k, 0])

        alog = [logline(A, k) for k in range(3)]
        blog = [logline(B, 0)]
        asum = T("3 log lines", 26, YELLOW_M).move_to([A.cx, -2.85, 0])
        bsum = T("1 log line", 26, YELLOW_M).move_to([B.cx, -2.85, 0])

        def attempt_a(k):
            d = Dot(radius=0.09, color=YELLOW_M).move_to([ax, 2.1, 0]).set_z_index(30)
            return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=0.35).move_to([ax, A.y(0), 0]),
                              AnimationGroup(d.animate(run_time=0.35).move_to([ax, A.y(1), 0]), FadeIn(alog[k], run_time=0.35)),
                              d.animate(run_time=0.35).move_to([ax, A.y(2), 0]), FadeOut(d, run_time=0.1))

        bd = Dot(radius=0.09, color=YELLOW_M).move_to([bx, 2.1, 0]).set_z_index(30)

        def hop_b():
            d = Dot(radius=0.09, color=YELLOW_M).move_to([bx, B.y(1), 0]).set_z_index(30)
            return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=0.35).move_to([bx, B.y(2), 0]), FadeOut(d, run_time=0.1))

        self.seq("Behavior decorators have the same issue. Put retry outside logging, and every attempt is logged. "
                 "Swap them, and you log one call, however many attempts it took.",
                 [(0, [FadeIn(VGroup(ab, al, ha)), FadeIn(VGroup(bb, bl, hb))], 1.0),
                  (1, [Succession(*[attempt_a(k) for k in range(3)])], 3.6),
                  (1, [FadeIn(asum, shift=UP * 0.1)], 0.4),
                  (2, [FadeIn(bd, run_time=0.05)], 0.05),
                  (2, [bd.animate.move_to([bx, B.y(0), 0])], 0.35),
                  (2, [bd.animate.move_to([bx, B.y(1), 0]), FadeIn(blog[0])], 0.35),
                  (2, [FadeOut(bd, run_time=0.1), Succession(hop_b(), hop_b(), hop_b())], 1.6),
                  (2, [FadeIn(bsum, shift=UP * 0.1)], 0.4)])
        self.beat("Pick the order you want, and pin it in a test.",
                  Indicate(VGroup(asum, bsum), color=WHITE, scale_factor=1.06), run_time=1.0)
        self.play(FadeOut(VGroup(ab, al, ha, bb, bl, hb, asum, bsum, *alog, *blog)), run_time=0.7)

        # ---- Java and Kotlin
        jv = code(["interface FeeCalculator {",
                   "    long feeMinor(Payment p);",
                   "    default FeeCalculator cappedAt(long cap) {",
                   "        return p -> Math.min(feeMinor(p), cap);",
                   "    }",
                   "}"], 24)
        kt = code(["fun interface FeeCalculator {",
                   "    fun feeMinor(p: Payment): Long",
                   "}",
                   "fun FeeCalculator.cappedAt(cap: Long) =",
                   "    FeeCalculator { p -> minOf(feeMinor(p), cap) }"], 24)
        part(jv[2], "cappedAt").set_color(PURPLE_M)
        part(kt[3], "cappedAt").set_color(PURPLE_M)
        jh = T("Java", 26, GREY_B)
        kh = T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.75).align_to(jv, LEFT)
        block = VGroup(jv, kt)
        jh.next_to(jv[0], LEFT, buff=0.7)
        kh.next_to(kt[0], LEFT, buff=0.7).align_to(jh, LEFT)
        allc = VGroup(block, jh, kh)
        allc.scale(min(1, 12.4 / allc.width)).move_to(ORIGIN)
        self.beat("In Java, each decorator is a default method on the interface. It returns a new lambda, and that lambda is a FeeCalculator too.",
                  FadeIn(VGroup(jv, jh), shift=UP * 0.15), run_time=1.2)
        self.seq("The lambda calls feeMinor on the calculator it wraps. Then it does its one extra thing, here the cap.",
                 [(0, [mark(part(jv[3], "feeMinor(p)"), WHITE, 0.8)], 1.6),
                  (1, [mark(part(jv[3], "Math.min("), PURPLE_M, 0.8)], 1.6)])
        self.seq("In Kotlin, the decorator is an extension function on a fun interface. "
                 "Either way, each call returns a new calculator, and the one it wraps stays as it was.",
                 [(0, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 1.0),
                  (0, [mark(part(kt[4], "feeMinor(p)"), WHITE, 0.5)], 1.3),
                  (1, [mark(part(kt[3], "FeeCalculator.cappedAt"), PURPLE_M, 0.8)], 1.6)])
        self.wait(0.8)
