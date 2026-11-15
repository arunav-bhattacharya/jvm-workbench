from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [
    (r"\bpay_(\d)", r"pay \1"), (r"\bsumOf\b", "sum of"), (r"\bmaxByOrNull\b", "max by or null"),
    (r"\bassociateBy\b", "associate by"), (r"\btoMap\b", "to map"),
]

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


STATUS = {"settled": GREEN_M, "pending": GREY_B, "failed": RED_M}
DAY = [("pay_1", "acme", "1,500", "settled", None), ("pay_2", "globex", "9,900", "pending", None),
       ("pay_3", "acme", "2,000", "settled", "500"), ("pay_4", "initech", "12,000", "failed", None),
       ("pay_5", "globex", "700", "settled", None)]
XS = [-5.2, -2.6, 0.0, 2.6, 5.2]
CY = -1.45


def pcard(pid, amt, status, refund=None, w=2.2, h=1.95):
    col = STATUS[status]
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=col, stroke_width=3).set_fill(fill_of(col, 0.12), 1)
    items = [M(pid, 22, GREY_A), M(amt, 28, WHITE), T(status, 22, col)]
    if refund:
        items.append(T("refund " + refund, 20, GOLD_M))
    VGroup(*items).arrange(DOWN, buff=0.13).move_to(r)
    g = VGroup(r, *items)
    g.amt = items[1]
    return g


class Fp04Fold(Beat):
    """fp-04 section 2: fold is the loop that carries one result (the accumulator) along the list;
    map and filter are the same walk with a list as the accumulator; closing beat on the empty-list
    and duplicate-key traps from sections 2 and 3."""

    def construct(self):
        self.title_card("fold, the general loop", "a start value, a step, and a walk down the list")

        cards = VGroup(*[pcard(p, a, s, r).move_to([x, CY, 0]) for (p, _, a, s, r), x in zip(DAY, XS)])
        NOTE = np.array([0, 1.55, 0])
        note = tok("10,000", GOLD_M, 32).move_to(NOTE)
        note_l = T("running balance", 24, GOLD_M).next_to(note, UP, buff=0.25)
        cur = Triangle(color=GOLD_M, fill_color=GOLD_M, fill_opacity=1).scale(0.16).rotate(PI).move_to([XS[0], 0.0, 0])
        self.seq("End of day. The account starts at 10,000 cents. "
                 "Walk down the day's payments with a note that holds the running balance.",
                 [(0, [LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cards], lag_ratio=0.15)], 1.4),
                  (1, [FadeIn(note, shift=DOWN * 0.15), FadeIn(note_l)], 0.8),
                  (2, [FadeIn(cur)], 0.5)])

        held = {"note": note}

        def fly(i, label, color):
            c = tok(label, color, 26).move_to(cards[i].get_center() + UP * 0.25).set_opacity(0)
            return c, chain(c, (lambda x: x.set_opacity(1), 0.2), (lambda x: x.move_to(NOTE), 0.7), (lambda x: x.set_opacity(0), 0.15))

        def renote(text, size=32, rt=0.35):
            """Cross-fade the note to a new value. The new token starts invisible, so it can sit in a Succession."""
            old = held["note"]
            new = tok(text, GOLD_M, size).move_to(NOTE).set_opacity(0)
            held["note"] = new
            return AnimationGroup(FadeOut(old), new.animate.set_opacity(1), run_time=rt)

        def move_cur(i, rt=None):
            a = moved(cur, [XS[i], 0.0, 0])
            if rt:
                a.run_time = rt
            return a

        def dim(i):
            return cards[i].animate.set_opacity(0.35)

        _, f1 = fly(0, "+1,500", GREEN_M)
        self.seq("pay_1 settled for 1,500, so the note goes to 11,500.",
                 [(0, [Indicate(cards[0], color=GREEN_M, scale_factor=1.05)], 0.7),
                  (0, [Succession(f1, renote("11,500"))], 1.3)])
        _, f2 = fly(1, "+0", GREY_B)
        self.seq("pay_2 is still pending, so the note stays.",
                 [(0, [dim(0), move_cur(1)], 0.5), (0, [Succession(f2, Indicate(note, color=GREY_B, scale_factor=1.0, run_time=0.35))], 1.3)])
        q = M("?", 34, GREY_B).next_to(NOTE, RIGHT, buff=1.15)
        self.ask("pay_3 settled for 2,000, but 500 of it was refunded. What does the note say now?",
                 dim(1), move_cur(2), Indicate(cards[2][4], color=GOLD_M, scale_factor=1.1), FadeIn(q), run_time=1.2)
        _, f3a = fly(2, "+2,000", GREEN_M)
        _, f3b = fly(2, "-500", RED_M)
        _, f4 = fly(3, "+0", GREY_B)
        _, f5 = fly(4, "+700", GREEN_M)
        self.seq("13,000. The failed payment changes nothing, and pay_5 adds 700. The balance is 13,700.",
                 [(0, [FadeOut(q), Succession(f3a, renote("12,000"), f3b, renote("13,000"))], 2.0),
                  (1, [dim(2), move_cur(3)], 0.4), (1, [f4], 1.1),
                  (1, [dim(3), move_cur(4)], 0.4), (1, [Succession(f5, renote("13,700"))], 1.1),
                  (2, [Indicate(held["note"], color=GOLD_M, scale_factor=1.12)], 0.8)])

        # the two parts you choose
        start_w = T("start", 26, GREY_B).move_to([-4.7, 2.9, 0])
        start_v = tok("10,000", GOLD_M, 26).next_to(start_w, RIGHT, buff=0.25)
        step_w = T("step", 26, GREY_B).move_to([0.6, 2.9, 0])
        step_v = T("note + payment  ->  new note", 26, WHITE).next_to(step_w, RIGHT, buff=0.25)
        self.seq("Each step took the note and one payment, and wrote a new note. "
                 "You choose only two things: where the note starts, and the step.",
                 [(0, [FadeOut(note_l), FadeIn(step_w, shift=DOWN * 0.1), FadeIn(step_v, shift=DOWN * 0.1)], 0.8),
                  (1, [FadeIn(start_w, shift=DOWN * 0.1), FadeIn(start_v, shift=DOWN * 0.1)], 0.7)])
        acc_l = T("the accumulator", 26, GOLD_M).next_to(held["note"], DOWN, buff=0.25)
        name = T("fold", 40, WHITE).next_to(held["note"], LEFT, buff=1.2)
        self.seq("This loop is called fold. The note it carries is the accumulator.",
                 [(0, [Write(name)], 0.8), (1, [FadeIn(acc_l, shift=UP * 0.1)], 0.6)])

        # map and filter are the same walk with a list as the note
        start_v2 = tok("[]", GOLD_M, 26).next_to(start_w, RIGHT, buff=0.25)
        step_v2 = T("add the amount", 26, WHITE).next_to(step_w, RIGHT, buff=0.25)
        empty = renote("[]", 28, rt=0.8)
        self.play(FadeOut(VGroup(name, acc_l)), cards.animate.set_opacity(1), move_cur(0),
                  empty, xfade(start_v, start_v2), xfade(step_v, step_v2), run_time=0.8)
        amounts = ["1,500", "9,900", "2,000", "12,000", "700"]
        walk = []
        for i in range(5):
            c = tok(amounts[i], BLUE_M, 24).move_to(cards[i].amt).set_opacity(0)
            lst = "[" + ", ".join(amounts[:i + 1]) + "]"
            walk.append(Succession(move_cur(i, 0.25),
                                   chain(c, (lambda x: x.set_opacity(1), 0.1), (lambda x: x.move_to(NOTE), 0.5), (lambda x: x.set_opacity(0), 0.05)),
                                   renote(lst, 28, rt=0.25)))
        map_l = M("map", 32, BLUE_M).next_to(NOTE, DOWN, buff=0.75)
        self.seq("Change what the note holds. Start with an empty list, and let the step add each amount. "
                 "The walk builds exactly what map gives you.",
                 [(1, [Succession(*walk)], 4.2), (2, [FadeIn(map_l, shift=UP * 0.1)], 0.6)])

        ids = [d[0] for d in DAY]
        keep = [d[3] == "settled" for d in DAY]
        step_v3 = T("add it if it settled", 26, WHITE).next_to(step_w, RIGHT, buff=0.25)
        empty2 = renote("[]", 28, rt=0.7)
        self.play(FadeOut(map_l), move_cur(0), empty2, xfade(step_v2, step_v3), run_time=0.7)
        walk, kept = [], []
        for i in range(5):
            if keep[i]:
                kept.append(ids[i])
                c = tok(ids[i], GREEN_M, 24).move_to(cards[i][1]).set_opacity(0)
                walk.append(Succession(move_cur(i, 0.25),
                                       chain(c, (lambda x: x.set_opacity(1), 0.1), (lambda x: x.move_to(NOTE), 0.5), (lambda x: x.set_opacity(0), 0.05)),
                                       renote("[" + ", ".join(kept) + "]", 28, rt=0.25)))
            else:
                walk.append(Succession(move_cur(i, 0.25), cards[i].animate(run_time=0.4).set_opacity(0.3)))
        filt_l = M("filter", 32, GREEN_M).next_to(NOTE, DOWN, buff=0.75)
        self.seq("Add a payment only when it settled, and the same walk gives you filter.",
                 [(0, [Succession(*walk)], 3.6), (0, [FadeIn(filt_l, shift=UP * 0.1)], 0.5)])

        named = VGroup(*[tok(n, GOLD_M, 26) for n in ("sumOf", "count", "maxByOrNull")]).arrange(RIGHT, buff=0.4)
        named.next_to(NOTE, DOWN, buff=0.6)
        self.seq("sumOf, count and maxByOrNull are folds too, already written and named. Use them when they fit.",
                 [(0, [FadeOut(filt_l), LaggedStart(*[FadeIn(n, shift=UP * 0.1) for n in named], lag_ratio=0.3)], 1.2)])
        self.play(FadeOut(VGroup(cards, cur, held["note"], start_w, start_v2, step_w, step_v3, named)), run_time=0.7)

        # ---------- code: Java and Kotlin ----------
        jv = code(["long balance = payments.stream().reduce(10_000L,",
                   "        (acc, p) -> p.status() == SETTLED",
                   "                ? acc + p.amountCents() - refundOf(p) : acc,",
                   "        Long::sum);             // only for parallel streams"], 22)
        kt = code(["val balance = payments.fold(10_000L) { acc, p ->",
                   "    when (p.status) {",
                   "        SETTLED -> acc + p.amountCents - (p.refundCents ?: 0L)",
                   "        PENDING, FAILED -> acc",
                   "    }",
                   "}"], 22)
        for ln in (jv[0], kt[0]):
            part(ln, "10_000L").set_color(GOLD_M)
        part(jv[3], "// only for parallel streams").set_color(GREY_B)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        pair = VGroup(jcol, kcol).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        pair.scale(min(1, 12.4 / pair.width, 6.7 / pair.height)).move_to(ORIGIN)
        self.seq("In code, the start and the step are the two arguments. Java's reduce takes a third, used only by parallel streams.",
                 [(0, [FadeIn(pair, shift=UP * 0.15)], 1.0),
                  (0, [mark(part(jv[0], "10_000L"), GOLD_M, 0.3), mark(part(kt[0], "10_000L"), GOLD_M, 0.3)], 1.1),
                  (0, [mark(VGroup(*jv[1][8:], *jv[2][16:]), WHITE, 0.3), mark(VGroup(*kt[0][37:]), WHITE, 0.3)], 1.1),
                  (1, [mark(part(jv[3], "Long::sum"), GREY_B, 0.6)], 1.4)])
        self.play(FadeOut(pair), run_time=0.6)

        # ---------- closing beat: the two traps ----------
        div = DashedLine([0, 2.9, 0], [0, -3.2, 0], dash_length=0.1, stroke_width=1.5, color=GREY_D)
        lh = T("an empty day", 30, WHITE).move_to([-3.5, 2.85, 0])
        rh = T("a repeated key", 30, WHITE).move_to([3.5, 2.85, 0])
        belt = DashedLine([-6.0, 1.0, 0], [-1.0, 1.0, 0], dash_length=0.12, stroke_width=2, color=GREY_B)
        belt_l = T("no payments", 22, GREY_B).next_to(belt, DOWN, buff=0.15)
        fold_row = VGroup(M("fold", 28, WHITE), tok("10,000", GOLD_M, 26)).arrange(RIGHT, buff=0.4)
        fold_row.move_to([-3.5, -0.35, 0])
        fold_ok = tick(True, 0.22).next_to(fold_row, RIGHT, buff=0.3)
        red_row = M("reduce", 28, WHITE).move_to([-3.5, -1.45, 0])
        red_q = M("?", 34, GREY_B).next_to(red_row, RIGHT, buff=0.4)
        self.seq("Two traps. On a quiet day the list is empty. fold just hands back its start value.",
                 [(0, [FadeIn(div), FadeIn(lh)], 0.6), (1, [Create(belt), FadeIn(belt_l)], 0.6),
                  (2, [FadeIn(fold_row[0]), FadeIn(fold_row[1], shift=RIGHT * 0.3), Create(fold_ok)], 1.0)])
        self.ask("reduce has no start value. It begins with the first element. What does it do when there is none?",
                 FadeIn(red_row), FadeIn(red_q), run_time=0.8)
        err = VGroup(M("UnsupportedOperationException:", 20, RED_M), M("Empty collection can't be reduced.", 20, RED_M))
        err.arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(red_row, DOWN, buff=0.3).align_to(belt, LEFT).shift(RIGHT * 0.2)
        self.seq("It throws.", [(0, [xfade(red_q, tick(False, 0.22).move_to(red_q)), FadeIn(err, shift=UP * 0.1)], 0.8)])

        slot_r = RoundedRectangle(corner_radius=0.1, width=2.0, height=0.9, stroke_color=GREY_B, stroke_width=2.5).set_fill(BLACK, 1)
        key = M("acme", 26, GREY_A).next_to(slot_r, LEFT, buff=0.3)
        slot = VGroup(slot_r, key).move_to([3.5, -1.1, 0])
        ab = M("associateBy { it.merchant }", 22, WHITE).move_to([3.5, -0.3, 0])
        slot.move_to([3.5, -1.35, 0])

        def small_card(pid, amt):
            r = RoundedRectangle(corner_radius=0.12, width=2.0, height=1.45, stroke_color=GREEN_M, stroke_width=3).set_fill(fill_of(GREEN_M, 0.12), 1)
            tk = tok(pid, GREEN_M, 24); a = M(amt, 26, WHITE)
            VGroup(tk, a).arrange(DOWN, buff=0.15).move_to(r)
            return VGroup(r, a), tk

        c1, t1 = small_card("pay_1", "1,500")
        c3, t3 = small_card("pay_3", "2,000")
        VGroup(c1, c3).arrange(RIGHT, buff=0.5).move_to([3.5, 1.5, 0])
        t1.move_to(c1[0].get_center() + UP * 0.32); t3.move_to(c3[0].get_center() + UP * 0.32)
        merch = T("both from acme", 22, GREY_B).next_to(VGroup(c1, c3), DOWN, buff=0.15)
        gone = T("pay_1 is gone, without a word", 22, RED_M).move_to([3.5, -2.3, 0])
        javaa = T("Java's toMap throws instead", 22, GREY_A).move_to([3.5, -2.9, 0])
        self.seq("And associateBy keeps one element per key. When a key repeats, the last one wins, without a word. Java's toMap throws instead.",
                 [(0, [FadeIn(rh), FadeIn(c1), FadeIn(c3), FadeIn(t1), FadeIn(t3), FadeIn(merch), FadeIn(ab), FadeIn(slot)], 0.9),
                  (1, [AnimationGroup(
                      chain(t1, (lambda x: x.move_to(slot_r), 0.6), (lambda x: x, 0.3),
                            (lambda x: x.shift(DOWN * 0.9 + LEFT * 0.4).set_opacity(0.0), 0.7)),
                      Succession(Wait(0.9), Transform(t3, t3.copy().move_to(slot_r), run_time=0.7)))], 1.6),
                  (1, [FadeIn(gone, shift=UP * 0.1)], 0.5),
                  (2, [FadeIn(javaa, shift=UP * 0.1)], 0.5)])
        self.play(FadeOut(VGroup(div, lh, rh, belt, belt_l, fold_row, fold_ok, red_row, red_q, err, slot, ab, c1, c3, t3, merch, gone, javaa)), run_time=0.7)
        self.remove(t1)

        # ---------- the rule, then a check ----------
        rule = VGroup(T("A loop that builds one result is a fold:", 32),
                      T("a start value, plus a step to the next result.", 32)).arrange(DOWN, buff=0.22).move_to([0, 2.55, 0])
        self.beat("The rule: a loop that builds one result is a fold. A start value, plus a step from one result to the next.",
                  FadeIn(rule, shift=UP * 0.1), run_time=1.2)
        small = VGroup(*[pcard(p, a, s, r, w=2.0, h=1.95).move_to([x, -1.9, 0]) for (p, _, a, s, r), x in zip(DAY[:3], (-2.6, 0.0, 2.6))])
        cnote = tok("0", GOLD_M, 30).move_to([0, 0.35, 0])
        cl = T("count", 26, GOLD_M).next_to(cnote, LEFT, buff=0.35)
        cq = M("step: ?", 26, GREY_B).next_to(cnote, RIGHT, buff=0.5)
        self.ask("Quick check. count is a fold that starts at zero. What does its step do?",
                 FadeIn(small), FadeIn(cnote), FadeIn(cl), FadeIn(cq), run_time=1.0)
        flies, counts = [], [cnote]
        for i in range(3):
            c = tok("+1", GOLD_M, 24).move_to(small[i].get_center() + UP * 0.3)
            c.set_opacity(0)
            nxt = tok(str(i + 1), GOLD_M, 30).move_to(cnote).set_opacity(0)
            flies.append(Succession(chain(c, (lambda x: x.set_opacity(1), 0.15), (lambda x: x.move_to(cnote), 0.5), (lambda x: x.set_opacity(0), 0.05)),
                                    AnimationGroup(FadeOut(counts[-1]), nxt.animate.set_opacity(1), run_time=0.2)))
            counts.append(nxt)
        self.seq("It adds one for each element.",
                 [(0, [xfade(cq, M("step: +1", 26, WHITE).move_to(cq).align_to(cq, LEFT)), Succession(*flies)], 2.6)])
        self.wait(1.0)
