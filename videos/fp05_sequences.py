from fg import *

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Za-z0-9\"'(])")


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
            if idx >= len(starts):
                print(f"SEQ WARNING: sentence {idx} of {len(starts)} in: {text[:60]}")
                idx = len(starts) - 1
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


def code(lines, size=24, color=WHITE, pitch=1.6, t2c=None):
    """Code lines, left aligned, indentation kept (a hidden '|' anchors each line)."""
    step = M("|", size).height * pitch
    g = VGroup()
    for i, ln in enumerate(lines):
        t = Text("|" + ln, font=MONO, font_size=size, color=color, t2c=t2c or {}, disable_ligatures=True)
        t.shift(np.array([0, -i * step, 0]) - t[0].get_center())
        t.remove(t[0])
        g.add(t)
    return g


def marble(n, color, r=0.3):
    c = Circle(radius=r, stroke_width=0).set_fill(color, opacity=1)
    return VGroup(c, T(str(n), 26, BLACK).move_to(c)).set_z_index(3)


def amount(v):
    return chip(str(v), YELLOW_M, size=24, mono=True).set_z_index(3)


def flash_line(a, b, color, rt=1.0):
    return ShowPassingFlash(Line(a, b, stroke_width=6, color=color), time_width=0.5, run_time=rt)


def dot_run(a, b, color, run_time):
    d = Dot(radius=0.08, color=color).move_to(a).set_z_index(30)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=run_time, rate_func=smooth).move_to(b),
                      FadeOut(d, run_time=0.12))


# the five payments from the lesson, one colour per status for the whole video
TXN = {1: (1500, "settled"), 2: (9900, "pending"), 3: (2000, "settled"), 4: (12000, "failed"), 5: (700, "settled")}
SCOL = {"settled": GREEN_M, "pending": GOLD_M, "failed": RED_M}
XS = [-2.6, -1.3, 0.0, 1.3, 2.6]
PAY_Y, FIL_Y, MAP_Y, TAKE_Y, RES_Y = 2.25, 0.85, -0.5, -1.85, -2.95
LAB_X, CON_X = -6.3, 4.1
FIL_C, MAP_C, TAKE_C = BLUE_M, TEAL_M, PURPLE_M


def stage(name, desc, color, y):
    return VGroup(M(name, 26, color), T(desc, 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1
                                                                   ).move_to([LAB_X, y, 0], aligned_edge=LEFT)


def guide(y):
    return DashedLine([XS[0] - 0.75, y, 0], [XS[-1] + 0.75, y, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)


def brackets(n, y):
    return VGroup(M("[", 40, GREY_B).move_to([XS[0] - 0.78, y, 0]), M("]", 40, GREY_B).move_to([XS[n - 1] + 0.78, y, 0]))


class Console:
    def __init__(self):
        self.lines = []
        self.head = T("printed", 24, GREY_B).move_to([CON_X, 2.75, 0], aligned_edge=LEFT)

    def add(self, text, color=WHITE):
        m = M(text, 22, color).move_to([CON_X, 2.3 - 0.37 * len(self.lines), 0], aligned_edge=LEFT)
        self.lines.append(m)
        return m

    def clear(self):
        g = VGroup(*self.lines)
        self.lines = []
        return g


class Fp05Sequences(Beat):
    """fp-05 section 1: a List chain runs each step over every element and builds a new list (horizontal);
    a Sequence pulls one element through the whole chain (vertical) and stops early; sorted() is a barrier."""

    def construct(self):
        self.title_card("Lists and sequences", "the order in which the steps run")

        # ---------------- the problem: a million authorizations ----------------
        BX0, BX1, BY = -6.0, 6.0, 0.2
        bar = Rectangle(width=BX1 - BX0, height=0.4, stroke_color=GREY_B, stroke_width=2).set_fill(BLACK, 1).move_to([0, BY, 0])
        bar_lab = T("1,000,000 authorizations", 28).next_to(bar, UP, buff=0.3).align_to(bar, LEFT)
        x518 = BX0 + 0.12
        bad = Line([x518, BY - 0.35, 0], [x518, BY + 0.35, 0], stroke_width=5, color=RED_M)
        bad_lab = T("the first bad one: number 518", 26, RED_M).move_to([x518 - 0.1, BY - 0.75, 0], aligned_edge=LEFT)
        tk = ValueTracker(0)
        sweep = always_redraw(lambda: Rectangle(width=max(0.001, (BX1 - BX0) * tk.get_value() / 1e6), height=0.4,
                                                stroke_width=0).set_fill(TEAL_M, 0.55).move_to([BX0, BY, 0], aligned_edge=LEFT))
        counter = always_redraw(lambda: VGroup(T("risk model calls:", 28, GREY_B), M(f"{int(tk.get_value()):,}", 30, TEAL_M)
                                               ).arrange(RIGHT, buff=0.25).move_to([0, -1.6, 0]))
        t33 = VGroup(T("2 ms each:", 28, GREY_B), T("33 minutes", 30, TEAL_M)).arrange(RIGHT, buff=0.25).move_to([0, -2.4, 0])
        t1 = T("the answer was there after about one second", 26, RED_M).move_to([0, -3.1, 0])
        self.seq("A fraud job wants the first bad authorization out of a million: number 518. "
                 "The risk model takes 2 milliseconds a call, yet a List chain calls it a million times. "
                 "33 minutes, for an answer that was there after one second.",
                 [(0, [FadeIn(bar), FadeIn(bar_lab)], 0.8),
                  (0, [Create(bad), FadeIn(bad_lab)], 0.7),
                  (1, [FadeIn(sweep), FadeIn(counter)], 0.3),
                  (1, [tk.animate.set_value(1_000_000)], 3.2),
                  (2, [FadeIn(t33, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(t1, shift=UP * 0.1), Indicate(bad, color=RED_M)], 0.8)],
                 say="A fraud job wants the first bad authorization out of a million: number five hundred eighteen. "
                     "The risk model takes 2 milliseconds a call, yet a List chain calls it a million times. "
                     "Thirty-three minutes, for an answer that was there after one second.")
        sweep.clear_updaters(); counter.clear_updaters()
        hook = VGroup(bar, bar_lab, bad, bad_lab, sweep, counter, t33, t1)
        self.play(FadeOut(hook), run_time=0.6)

        # ---------------- five payments, three steps ----------------
        src = {i: marble(i, SCOL[TXN[i][1]]).move_to([XS[i - 1], PAY_Y, 0]) for i in TXN}
        pay_lab = T("payments", 26).move_to([LAB_X, PAY_Y, 0], aligned_edge=LEFT)
        legend = VGroup(*[VGroup(Dot(radius=0.08, color=SCOL[s]), T(s, 22, GREY_B)).arrange(RIGHT, buff=0.12)
                          for s in ("settled", "pending", "failed")]).arrange(RIGHT, buff=0.35)
        legend.next_to(VGroup(*src.values()), UP, buff=0.3)
        st = {"f": stage("filter", "keep settled", FIL_C, FIL_Y), "m": stage("map", "to its amount", MAP_C, MAP_Y),
              "t": stage("take(2)", "the first two", TAKE_C, TAKE_Y)}
        guides = VGroup(guide(FIL_Y), guide(MAP_Y), guide(TAKE_Y))
        self.seq("To see why, shrink it to five payments. The green ones are settled. "
                 "The chain keeps the settled ones, turns each into its amount, and takes the first two.",
                 [(0, [FadeIn(pay_lab), LaggedStart(*[FadeIn(m, shift=DOWN * 0.15) for m in src.values()], lag_ratio=0.15)], 1.0),
                  (1, [FadeIn(legend)], 0.5),
                  (2, [FadeIn(st["f"]), Create(guides[0])], 0.6),
                  (2, [FadeIn(st["m"]), Create(guides[1])], 0.6),
                  (2, [FadeIn(st["t"]), Create(guides[2])], 0.6)])

        # ---------------- the List chain: horizontal ----------------
        con = Console()
        head = T("List: one step at a time, for every payment", 28).move_to([-1.0, 3.2, 0])
        self.play(FadeOut(legend), FadeIn(head), FadeIn(con.head), run_time=0.6)
        cp = {i: src[i].copy() for i in src}
        crosses = {}
        plan = [(0, [flash_line([XS[0] - 0.75, FIL_Y, 0], [XS[-1] + 0.75, FIL_Y, 0], FIL_C, 1.2)], 1.2)]
        for i in TXN:
            plan.append((1, [cp[i].animate.move_to([XS[i - 1], FIL_Y, 0]), src[i].animate.set_opacity(0.35),
                             FadeIn(con.add(f"filter {i}"))], 0.42))
            if TXN[i][1] != "settled":
                crosses[i] = tick(False, 0.2).move_to(cp[i]).set_z_index(5)
                plan.append((1, [FadeIn(crosses[i], scale=1.3), cp[i].animate.set_opacity(0.3)], 0.25))
        keep = [1, 3, 5]
        fb = brackets(3, FIL_Y)
        plan.append((1, [FadeOut(VGroup(*crosses.values(), cp[2], cp[4])),
                         *[cp[i].animate.move_to([XS[k], FIL_Y, 0]) for k, i in enumerate(keep)], FadeIn(fb)], 0.6))
        self.seq("On a List, each step runs over every payment, and builds a new list before the next step starts. "
                 "filter checks all five, and keeps 1, 3 and 5.", plan)

        am = {i: amount(TXN[i][0]).move_to([XS[k], MAP_Y, 0]) for k, i in enumerate(keep)}
        mb = brackets(3, MAP_Y)
        plan = []
        for k, i in enumerate(keep):
            c = cp[i].copy()
            plan.append((0, [c.animate.move_to([XS[k], MAP_Y, 0]), FadeIn(con.add(f"map {i}"))], 0.4))
            plan.append((0, [ReplacementTransform(c, am[i])], 0.3))
        plan.append((0, [FadeIn(mb)], 0.3))
        tk_am = [am[1].copy(), am[3].copy()]
        tb = brackets(2, TAKE_Y)
        res = VGroup(T("result", 24, GREY_B), M("[1500, 2000]", 26)).arrange(RIGHT, buff=0.25).move_to([LAB_X, RES_Y, 0], aligned_edge=LEFT)
        calls8 = T("8 calls", 28, WHITE).move_to([CON_X, -0.95, 0], aligned_edge=LEFT)
        plan += [(0, [tk_am[0].animate.move_to([XS[0], TAKE_Y, 0]), tk_am[1].animate.move_to([XS[1], TAKE_Y, 0]), FadeIn(tb)], 0.7),
                 (0, [FadeIn(res)], 0.5),
                 (1, [FadeIn(calls8, shift=UP * 0.1)], 0.5),
                 (2, [flash_line([XS[0] - 0.75, y, 0], [XS[-1] + 0.75, y, 0], c, 1.0) for y, c in
                      ((FIL_Y, FIL_C), (MAP_Y, MAP_C), (TAKE_Y, TAKE_C))], 1.0)]
        self.seq("Then map runs on all three, and take keeps the first two. "
                 "Eight calls, and a new list after every step. People call this horizontal.", plan)

        # ---------------- the Sequence: vertical ----------------
        list_stuff = VGroup(*[cp[i] for i in keep], fb, *am.values(), mb, *tk_am, tb, res, calls8)
        head2 = T("Sequence: one payment at a time, through every step", 28).move_to([-0.6, 3.2, 0])
        fit(head2, 9.4)
        self.play(FadeOut(list_stuff), FadeOut(con.clear()), *[src[i].animate.set_opacity(1) for i in src],
                  Transform(head, head2), run_time=0.8)
        built = M("built TakeSequence, nothing has run yet", 22, GREY_B).move_to([LAB_X, RES_Y, 0], aligned_edge=LEFT)
        ask = VGroup(M("toList()", 26, YELLOW_M), T("asks for the result", 24, GREY_B)).arrange(RIGHT, buff=0.25
                                                                                              ).move_to([LAB_X, RES_Y, 0], aligned_edge=LEFT)
        self.seq("Now put asSequence in front. Building the chain runs nothing. "
                 "The work starts when toList asks for a result. Which lines print now?",
                 [(1, [FadeIn(built)], 0.6),
                  (2, [ReplacementTransform(built, ask)], 0.7)],
                 say="Now put as-sequence in front. Building the chain runs nothing. "
                     "The work starts when to-list asks for a result. Which lines print now?")
        self.wait(2.2)

        def pull(i, rt=0.7):
            x = XS[i - 1] - 0.5
            return dot_run([x, TAKE_Y, 0], [x, PAY_Y, 0], YELLOW_M, rt)

        s = {i: src[i].copy() for i in src}
        a1, a3 = amount(1500), amount(2000)
        self.seq("take asks map, map asks filter, and filter reads payment 1. "
                 "It passes, goes straight on to map, and lands in take.",
                 [(0, [pull(1, 1.4)], 1.5),
                  (0, [s[1].animate.move_to([XS[0], FIL_Y, 0]), src[1].animate.set_opacity(0.35), FadeIn(con.add("filter 1"))], 0.5),
                  (1, [s[1].animate.move_to([XS[0], MAP_Y, 0]), FadeIn(con.add("map 1"))], 0.5),
                  (1, [ReplacementTransform(s[1], a1.move_to([XS[0], MAP_Y, 0]))], 0.35),
                  (1, [a1.animate.move_to([XS[0], TAKE_Y, 0])], 0.5)])

        x2 = tick(False, 0.2).move_to([XS[1], FIL_Y, 0]).set_z_index(5)
        nr = VGroup(*[T("not read", 22, GREY_B).move_to([XS[i - 1], PAY_Y - 0.6, 0]) for i in (4, 5)])
        full = SurroundingRectangle(VGroup(a1, a3.copy().move_to([XS[1], TAKE_Y, 0])), buff=0.15, color=TAKE_C, corner_radius=0.15)
        self.seq("Payment 2 fails the filter. Payment 3 passes, is mapped, and take now has its two. "
                 "So it stops. Payments 4 and 5 are never read.",
                 [(0, [pull(2, 0.5)], 0.55),
                  (0, [s[2].animate.move_to([XS[1], FIL_Y, 0]), src[2].animate.set_opacity(0.35), FadeIn(con.add("filter 2"))], 0.45),
                  (0, [FadeIn(x2, scale=1.3), s[2].animate.set_opacity(0.3)], 0.3),
                  (1, [FadeOut(VGroup(x2, s[2])), pull(3, 0.5)], 0.55),
                  (1, [s[3].animate.move_to([XS[2], FIL_Y, 0]), src[3].animate.set_opacity(0.35), FadeIn(con.add("filter 3"))], 0.45),
                  (1, [s[3].animate.move_to([XS[2], MAP_Y, 0]), FadeIn(con.add("map 3"))], 0.45),
                  (1, [ReplacementTransform(s[3], a3.move_to([XS[2], MAP_Y, 0]))], 0.35),
                  (1, [a3.animate.move_to([XS[1], TAKE_Y, 0])], 0.5),
                  (2, [Create(full)], 0.5),
                  (3, [FadeIn(nr), Indicate(VGroup(src[4], src[5]), color=WHITE, scale_factor=1.1)], 0.8)])

        res2 = VGroup(T("result", 24, GREY_B), M("[1500, 2000]", 26)).arrange(RIGHT, buff=0.25).move_to([LAB_X, RES_Y, 0], aligned_edge=LEFT)
        calls5 = VGroup(T("5 calls", 28), T("(List: 8)", 24, GREY_B)).arrange(RIGHT, buff=0.2).move_to([CON_X, -0.95, 0], aligned_edge=LEFT)
        self.seq("The same result, with five calls instead of eight, and no lists in between. "
                 "This is vertical: one payment through the whole chain.",
                 [(0, [ReplacementTransform(ask, res2)], 0.6),
                  (0, [FadeIn(calls5, shift=UP * 0.1)], 0.5),
                  (1, [flash_line([XS[0], PAY_Y - 0.35, 0], [XS[0], TAKE_Y, 0], YELLOW_M, 1.0),
                       flash_line([XS[2], PAY_Y - 0.35, 0], [XS[2], MAP_Y, 0], YELLOW_M, 1.0)], 1.0)])

        # the million again
        seq_stuff = VGroup(a1, a3, full, nr, res2, calls5, *src.values(), pay_lab, *st.values(), guides, head)
        self.play(FadeOut(seq_stuff), FadeOut(con.clear()), FadeOut(con.head), run_time=0.7)
        tk.set_value(0)
        bar2 = VGroup(bar, bar_lab, bad, bad_lab)
        sweep2 = always_redraw(lambda: Rectangle(width=max(0.001, (BX1 - BX0) * tk.get_value() / 1e6), height=0.4,
                                                 stroke_width=0).set_fill(TEAL_M, 0.55).move_to([BX0, BY, 0], aligned_edge=LEFT))
        cnt2 = VGroup(T("risk model calls:", 28, GREY_B), M("518", 30, TEAL_M), T("then it stops", 28, GREY_B)
                      ).arrange(RIGHT, buff=0.25).move_to([0, -1.6, 0])
        self.seq("Back on the million. The Sequence scores 518 and stops.",
                 [(0, [FadeIn(bar2), FadeIn(sweep2)], 0.7),
                  (1, [tk.animate.set_value(10_000)], 0.6),
                  (1, [FadeIn(cnt2, shift=UP * 0.1), Indicate(bad, color=RED_M)], 0.8)],
                 say="Back on the million. The Sequence scores five hundred eighteen, and stops.")
        sweep2.clear_updaters()
        self.play(FadeOut(VGroup(bar2, sweep2, cnt2)), run_time=0.6)

        # ---------------- sorted: the barrier ----------------
        src2 = {i: marble(i, SCOL[TXN[i][1]]).move_to([XS[i - 1], PAY_Y, 0]) for i in TXN}
        st2 = {"s": stage("sortedBy", "by amount", WHITE, FIL_Y), "f": stage("first()", "the smallest", TAKE_C, MAP_Y)}
        g2 = VGroup(guide(FIL_Y), guide(MAP_Y))
        con2 = Console()
        head3 = T("A Sequence with sortedBy", 28).move_to([-1.0, 3.2, 0])
        cps = {i: src2[i].copy() for i in src2}
        amt = {i: T(f"{TXN[i][0]:,}".replace(",", ""), 22, GREY_B) for i in TXN}
        order = sorted(TXN, key=lambda i: TXN[i][0])          # 5, 1, 3, 2, 4
        plan = [(0, [FadeIn(head3), FadeIn(pay_lab), *[FadeIn(m) for m in src2.values()], FadeIn(VGroup(*st2.values(), g2)),
                     FadeIn(con2.head)], 0.8)]
        plan.append((2, [dot_run([XS[0] - 0.5, MAP_Y, 0], [XS[0] - 0.5, PAY_Y, 0], YELLOW_M, 0.6)], 0.65))
        for i in TXN:
            plan.append((2, [cps[i].animate.move_to([XS[i - 1], FIL_Y, 0]), src2[i].animate.set_opacity(0.35),
                             FadeIn(con2.add(f"saw {i}"))], 0.38))
        for i in TXN:
            amt[i].move_to([XS[i - 1], FIL_Y - 0.55, 0])
        plan.append((2, [FadeIn(VGroup(*amt.values()))], 0.4))
        plan.append((2, [*[cps[i].animate.move_to([XS[k], FIL_Y, 0]) for k, i in enumerate(order)],
                         *[amt[i].animate.move_to([XS[k], FIL_Y - 0.55, 0]) for k, i in enumerate(order)]], 1.0))
        plan.append((2, [cps[5].animate.move_to([XS[0], MAP_Y, 0]), amt[5].animate.move_to([XS[0], MAP_Y - 0.55, 0])], 0.6))
        res3 = VGroup(T("result", 24, GREY_B), M("payment 5", 26)).arrange(RIGHT, buff=0.25).move_to([LAB_X, RES_Y + 0.8, 0], aligned_edge=LEFT)
        plan.append((2, [FadeIn(res3)], 0.5))
        self.seq("One kind of step breaks the vertical flow: sorting. It can't hand out the smallest until it has seen every payment. "
                 "So the first request pulls all five in, sorts them, and only then hands out payment 5.", plan)
        self.wait(0.8)
        self.play(FadeOut(VGroup(head3, pay_lab, *src2.values(), *st2.values(), g2, *cps.values(), *amt.values(), res3)),
                  FadeOut(con2.clear()), FadeOut(con2.head), run_time=0.7)

        # ---------------- code, Kotlin and Java ----------------
        def block(title, color, kt, jv, y):
            hd = T(title, 28, color)
            kc = code(kt, 24)
            jc = code(jv, 24)
            kh, jh = T("Kotlin", 24, GREY_B), T("Java", 24, GREY_B)
            jc.next_to(kc, DOWN, buff=0.38).align_to(kc, LEFT)
            kh.next_to(kc[0], LEFT, buff=0.5)
            jh.next_to(jc[0], LEFT, buff=0.5).align_to(kh, LEFT)
            body = VGroup(kh, kc, jh, jc)
            hd.next_to(body, UP, buff=0.3).align_to(kh, LEFT)
            return VGroup(hd, body).move_to([0, y, 0]).align_to([-6.2, 0, 0], LEFT)

        eager = block("one step at a time, a new list per step", WHITE,
                      ["txns.filter { … }.map { … }.take(2)"],
                      ["List<Txn> settled = txns.stream().filter(…).toList();",
                       "List<Long> amounts = settled.stream().map(…).toList();"], 1.75)
        lazy = block("one payment at a time, stops early", WHITE,
                     ["txns.asSequence().filter { … }.map { … }.take(2).toList()"],
                     ["txns.stream().filter(…).map(…).limit(2).toList()"], -1.55)
        self.seq("In Kotlin, the only change is asSequence. A Java Stream is lazy in the same way. "
                 "Java has no eager chain: you collect after every step.",
                 [(0, [FadeIn(eager[0]), FadeIn(eager[1][0:2]), FadeIn(lazy[0]), FadeIn(lazy[1][0:2])], 1.0),
                  (1, [FadeIn(lazy[1][2:4], shift=UP * 0.1)], 0.8),
                  (2, [FadeIn(eager[1][2:4], shift=UP * 0.1)], 0.8)],
                 say="In Kotlin, the only change is as-sequence. A Java Stream is lazy in the same way. "
                     "Java has no eager chain: you collect after every step.")
        self.wait(1.2)
        self.play(FadeOut(VGroup(eager, lazy)), run_time=0.6)

        # ---------------- the rule and a check ----------------
        rule = VGroup(T("A List finishes each step for every element.", 32),
                      T("A Sequence moves one element through every step,", 32),
                      T("and only as far as the end asks.", 32)).arrange(DOWN, buff=0.22).move_to([0, 1.8, 0])
        self.beat("So: a List finishes each step for every element. "
                  "A Sequence moves one element through every step, and only as far as the end asks.",
                  LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in rule], lag_ratio=0.5), run_time=3.0)
        chk = M("txns.take(2).filter { … }.map { … }", 28).move_to([0, -0.35, 0])
        q = T("On a List: how many filter lines print?", 26, GREY_B).move_to([0, -1.2, 0])
        self.seq("A quick check. On the List, move take(2) to the front. How many filter lines print?",
                 [(1, [FadeIn(chk, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(q)], 0.5)],
                 say="A quick check. On the List, move take two to the front. How many filter lines print?")
        self.wait(2.2)
        ans = VGroup(T("two:", 28, YELLOW_M), M("filter 1, filter 2", 26), T("and the result is", 26, GREY_B), M("[1500]", 26)
                     ).arrange(RIGHT, buff=0.25).move_to([0, -2.1, 0])
        self.beat("Two: filter 1 and filter 2. take cut the list first, so the result is just 1500.",
                  FadeIn(ans, shift=UP * 0.1), run_time=0.8,
                  say="Two: filter one and filter two. take cut the list first, so the result is just fifteen hundred.")
        self.wait(1.0)
