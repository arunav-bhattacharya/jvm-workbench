from fg import *
import fg

# ---- helpers for this file ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads another spelling than the caption), captions split only where
    a new sentence starts, seq() to start animations at a given sentence, and ask() for a predict-and-pause."""

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

    def ask(self, text, *anims, pause=2.0, say=None):
        """Ask the viewer to predict, then hold a beat of silence."""
        self.beat(text, *anims, after=0, say=say, run_time=0.8 if anims else None)
        self.wait(pause)


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


def dimc(color, k=0.10):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip_m(text, color, size=24, h=0.52, fill=0.2):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=fill)
    return VGroup(r, t)


def room(x0, x1, y0, y1, color, k=0.07):
    r = RoundedRectangle(corner_radius=0.15, width=x1 - x0, height=y1 - y0, stroke_color=color, stroke_width=3)
    return r.set_fill(dimc(color, k), opacity=1).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])


def node(label, color, w=2.5, h=0.85, size=28):
    t = M(label, size, color)
    r = RoundedRectangle(corner_radius=0.12, width=max(w, t.width + 0.5), height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dimc(color, 0.12), opacity=1)
    return VGroup(r, t.move_to(r))


def edge(a, b, color=GREY_B):
    return Line(a.get_bottom(), b.get_top(), stroke_width=2.5, color=color, buff=0.06)


GROUP, FLAT, PCT, ASK, ANS = GOLD_M, TEAL_M, BLUE_M, YELLOW_M, GREEN_M


class Pat06Composite(Beat):
    """pat-06 section 0: Composite. A group and a single rule answer the same question; a group asks its
    children and adds up, so one recursive function prices the whole fee plan."""

    def construct(self):
        self.title_card("Composite", "a group answers like a single rule")

        # ---------- the problem: a fee that is several rules, some of them groups ----------
        c30 = chip_m("30 cents", FLAT, 28, h=0.62).move_to([-4.6, 0.3, 0])
        c29 = chip_m("2.9%", PCT, 28, h=0.62).move_to([-1.4, 0.3, 0])
        bun = room(1.2, 5.6, -0.75, 1.35, GROUP, 0.08)
        bunl = T("a bundle of add-ons", 26, GROUP).move_to([3.4, 0.95, 0])
        c5 = chip_m("5 cents", FLAT, 28, h=0.62).move_to([3.4, 0.05, 0])
        plus = VGroup(T("+", 36, GREY_B).move_to([-3.0, 0.3, 0]), T("+", 36, GREY_B).move_to([0.05, 0.3, 0]))
        self.seq("A merchant's fee is rarely one number. This plan is 30 cents, plus 2.9 percent, plus a bundle of add-ons. "
                 "And the bundle has rules of its own: here, 5 cents more.",
                 [(1, [FadeIn(c30, shift=UP * 0.15)], 0.5), (1, [FadeIn(plus[0]), FadeIn(c29, shift=UP * 0.15)], 0.5),
                  (1, [FadeIn(plus[1]), FadeIn(bun), FadeIn(bunl)], 0.7),
                  (2, [FadeIn(c5, shift=DOWN * 0.15)], 0.6)])
        note = T("some parts are single rules, some are groups", 28, GREY_B).move_to([0, -2.0, 0])
        self.seq("So some parts are single rules, and some are groups of rules. A group can even hold another group. "
                 "The code that prices a payment should not have to care which is which.",
                 [(0, [FadeIn(note, shift=UP * 0.1)], 0.6),
                  (0, [Indicate(c30, color=FLAT, scale_factor=1.1), Indicate(c29, color=PCT, scale_factor=1.1)], 0.8),
                  (0, [Indicate(bun, color=GROUP, scale_factor=1.04)], 0.8)])

        # ---------- the tree ----------
        root = node("AllOf", GROUP).move_to([0, 2.45, 0])
        n30 = node("Flat(30)", FLAT).move_to([-4.5, 0.45, 0])
        n29 = node("Percent(290)", PCT).move_to([0, 0.45, 0])
        nin = node("AllOf", GROUP).move_to([4.5, 0.45, 0])
        n5 = node("Flat(5)", FLAT).move_to([4.5, -1.55, 0])
        edges = VGroup(edge(root, n30), edge(root, n29), edge(root, nin), edge(nin, n5))
        self.seq("Draw the plan as a tree. The leaves are single rules: Flat for a fixed amount, and Percent in basis points. "
                 "Each group is an AllOf, and the whole plan is one AllOf at the root.",
                 [(0, [FadeOut(note), FadeOut(plus), ReplacementTransform(c30, n30), ReplacementTransform(c29, n29),
                       ReplacementTransform(VGroup(bun, bunl), nin), ReplacementTransform(c5, n5)], 1.3),
                  (0, [Create(edges[3])], 0.4),
                  (1, [Indicate(VGroup(n30, n5), color=FLAT, scale_factor=1.06), Indicate(n29, color=PCT, scale_factor=1.06)], 1.0),
                  (2, [Indicate(nin, color=GROUP, scale_factor=1.08)], 0.8),
                  (2, [FadeIn(root, shift=DOWN * 0.2), Create(edges[0]), Create(edges[1]), Create(edges[2])], 1.0)])

        # ---------- one question, asked of every node ----------
        q = chip_m("fee on 10,000?", ASK, 26, h=0.58).move_to([-4.2, 2.45, 0])
        self.seq("Now ask the root one question: what is your fee on this payment? Say the payment is 100.00, which is 10,000 cents.",
                 [(0, [FadeIn(q, shift=RIGHT * 0.2)], 0.6),
                  (1, [q.animate.next_to(root, LEFT, buff=0.25)], 0.8)],
                 say="Now ask the root one question: what is your fee on this payment? "
                     "Say the payment is one hundred, which is ten thousand cents.")

        def token():
            return chip_m("10,000", ASK, 22, h=0.46)
        tk = [token().move_to(root.get_bottom()) for _ in range(3)]
        tk5 = token().move_to(nin.get_bottom())

        def mid(e, f=0.5):
            return e.get_start() + f * (e.get_end() - e.get_start())
        self.seq("A group does not know the answer by itself. It passes the same question on to each child, "
                 "and the inner group passes it on again.",
                 [(0, [Indicate(root, color=GROUP, scale_factor=1.08)], 0.7),
                  (1, [*[FadeIn(t) for t in tk]], 0.2),
                  (1, [*[t.animate.move_to(mid(edges[i], 0.55)) for i, t in enumerate(tk)]], 1.0),
                  (1, [*[FadeOut(t) for t in tk], Indicate(n30, color=FLAT), Indicate(n29, color=PCT), Indicate(nin, color=GROUP)], 0.6),
                  (1, [FadeIn(tk5)], 0.2),
                  (1, [tk5.animate.move_to(mid(edges[3], 0.55))], 0.7),
                  (1, [FadeOut(tk5), Indicate(n5, color=FLAT)], 0.5)])

        a30 = chip_m("30", ANS, 26, h=0.54).next_to(n30, DOWN, buff=0.25)
        a29 = VGroup(M("10,000 x 2.9% =", 24, GREY_B), chip_m("290", ANS, 26, h=0.54)).arrange(RIGHT, buff=0.2).next_to(n29, DOWN, buff=0.25)
        a5 = chip_m("5", ANS, 26, h=0.54).next_to(n5, DOWN, buff=0.25)
        self.seq("Leaves answer directly. Flat says 30. Percent says 2.9 percent of 10,000: 290. "
                 "Down in the inner group, Flat says 5.",
                 [(1, [FadeIn(a30, shift=DOWN * 0.15)], 0.6),
                  (2, [FadeIn(a29, shift=DOWN * 0.15)], 0.8),
                  (3, [FadeIn(a5, shift=DOWN * 0.15)], 0.6)])

        qq = T("What does the root return?", 34, ASK).move_to([-3.6, -2.4, 0])
        self.ask("So what does the root return?", FadeIn(qq, shift=UP * 0.1), pause=2.0)

        g5 = chip_m("5", ANS, 26, h=0.54).next_to(nin, LEFT, buff=0.25)
        sumt = VGroup(M("30 + 290 + 5 =", 28, GREY_A), chip_m("325", ANS, 30, h=0.62)).arrange(RIGHT, buff=0.2)
        sumt.next_to(root, RIGHT, buff=0.35)
        ups = [a30.copy(), a29[1].copy(), g5.copy()]
        self.seq("Each group adds up what its children return. The inner group returns 5. "
                 "The root returns 30, plus 290, plus 5: 325 cents.",
                 [(0, [FadeOut(qq)], 0.3),
                  (1, [TransformFromCopy(a5, g5, path_arc=-0.6)], 0.9),
                  (2, [*[gh.animate.move_to(sumt[0]).set_opacity(0) for gh in ups], FadeIn(sumt[0])], 1.4),
                  (2, [FadeIn(sumt[1], scale=1.3)], 0.6)])

        cap = T("Composite: the group answers the same question, by asking its children", 28, GREY_A).move_to([0, -3.05, 0])
        cap.scale(min(1, 12.4 / cap.width))
        self.seq("That is the Composite pattern. A group and a single rule answer the same question. "
                 "So the caller asks the root, and never checks whether it holds one rule or a whole tree.",
                 [(0, [FadeIn(cap, shift=UP * 0.1)], 0.7),
                  (2, [Indicate(root, color=GROUP, scale_factor=1.1), Indicate(sumt[1], color=ANS, scale_factor=1.15)], 1.0)])
        self.play(FadeOut(VGroup(root, n30, n29, nin, n5, edges, q, a30, a29, a5, g5, sumt, cap)), run_time=0.7)

        # ---------- the code: one recursive function ----------
        jv = code(["static long fee(Rule r, long amount) {",
                   "    return switch (r) {",
                   "        case Flat f -> f.minor();",
                   "        case Percent p -> amount * p.bps() / 10_000;",
                   "        case AllOf a -> a.rules().stream()",
                   "            .mapToLong(x -> fee(x, amount)).sum();",
                   "    };",
                   "}"], 24)
        kt = code(["fun fee(r: Rule, amount: Long): Long = when (r) {",
                   "    is Rule.Flat -> r.minor",
                   "    is Rule.Percent -> amount * r.bps / 10_000",
                   "    is Rule.AllOf -> r.rules.sumOf { fee(it, amount) }",
                   "}"], 24)
        for blk in (jv, kt):
            for ln in blk:
                for w, c in (("Flat", FLAT), ("Percent", PCT), ("AllOf", GROUP)):
                    if w in ln.src:
                        part(ln, w).set_color(c)
        rj = part(jv[5], "fee(x, amount)").set_color(ASK)
        rk = part(kt[3], "fee(it, amount)").set_color(ASK)
        jh, kh = T("Java", 26, GREY_B), T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.7).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        allc = VGroup(jv, kt, jh, kh)
        allc.scale(min(1, 12.4 / allc.width)).move_to(ORIGIN)
        self.seq("In code, one recursive function prices any plan. It has one case per kind of node. "
                 "The AllOf case calls fee again on each child: that call is the arrow down the tree.",
                 [(0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15)], 0.8),
                  (0, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 0.8),
                  (1, [Indicate(VGroup(jv[2], kt[1]), color=FLAT, scale_factor=1.03)], 0.7),
                  (1, [Indicate(VGroup(jv[3], kt[2]), color=PCT, scale_factor=1.03)], 0.7),
                  (2, [Circumscribe(rj, color=ASK, buff=0.06), Circumscribe(rk, color=ASK, buff=0.06)], 1.2)])
        self.seq("The switch has no default branch. Add a new kind of node, and the compiler flags every switch that does not handle it.",
                 [(0, [Circumscribe(jv[1], color=GREY_A, buff=0.06), Circumscribe(kt[0], color=GREY_A, buff=0.06)], 1.2)])
        self.play(FadeOut(allc), run_time=0.6)

        # ---------- the rule and a check ----------
        r1 = T("A group answers by asking its children and adding up.", 34).move_to(UP * 3.0)
        r2 = T("So one recursive function prices a tree of any depth.", 34, GROUP).next_to(r1, DOWN, buff=0.3)
        rule = VGroup(r1, r2)
        rule.scale(min(1, 12.4 / rule.width))
        self.beat("The rule: a group answers by asking its children and adding up, so one recursive function prices a tree of any depth.",
                  FadeIn(r1, shift=UP * 0.15), FadeIn(r2, shift=UP * 0.15), run_time=1.4)
        mroot = node("AllOf", GROUP, w=2.0, h=0.7, size=24).move_to([0, 1.15, 0])
        m30 = node("Flat(30)", FLAT, w=2.0, h=0.7, size=24).move_to([-4.0, -0.2, 0])
        m29 = node("Percent(290)", PCT, w=2.0, h=0.7, size=24).move_to([-0.6, -0.2, 0])
        min_ = node("AllOf", GROUP, w=2.0, h=0.7, size=24).move_to([3.4, -0.2, 0])
        m5 = node("Flat(5)", FLAT, w=2.0, h=0.7, size=24).move_to([2.0, -1.5, 0])
        m50 = node("Percent(50)", PCT, w=2.0, h=0.7, size=24).move_to([4.8, -1.5, 0])
        medges = VGroup(edge(mroot, m30), edge(mroot, m29), edge(mroot, min_), edge(min_, m5), edge(min_, m50))
        newt = T("new", 24, ASK).next_to(m50, DOWN, buff=0.18)
        cq = T("For the same 100.00, what does the root return now?", 30, GREY_A).move_to([0, -2.9, 0])
        self.seq("A quick check. The inner group gets a second rule: Percent of 50 basis points. "
                 "For the same 100.00, what does the root return now?",
                 [(0, [FadeIn(VGroup(mroot, m30, m29, min_, m5, medges[:4]))], 0.9),
                  (1, [FadeIn(m50, shift=DOWN * 0.15), Create(medges[4]), FadeIn(newt)], 0.8),
                  (2, [FadeIn(cq, shift=UP * 0.1)], 0.6)],
                 say="A quick check. The inner group gets a second rule: Percent of 50 basis points. "
                     "For the same one hundred, what does the root return now?")
        self.wait(2.5)
