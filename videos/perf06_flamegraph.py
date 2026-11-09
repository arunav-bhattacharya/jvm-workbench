from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bfeeSlow\b", "fee slow"), (r"\bms\b", "milliseconds"), (r"flamegraph\.pl", "flame graph dot P L"),
           (r"String\.format", "String dot format"), (r"Pattern\.compile", "Pattern dot compile"),
           (r"\btoPlainString\b", "to plain string"), (r"Thread\.run", "Thread dot run"), (r"\bBigDecimal\b", "big decimal"),
           (r"x-axis", "x axis")]

# one colour per family of frames, the same in every picture
RUN_C, FEE_C, FMT_C, PAT_C, STR_C, BIG_C, HOT_C = GREY_M, BLUE_M, GOLD_M, PURPLE_M, TEAL_M, GREEN_M, RED_M
SMALL_C, OTHER_C = "#6A6A6A", "#3C3C3C"

FR = {"Thread.run": RUN_C, "feeSlow": FEE_C, "String.format": FMT_C, "Formatter.format": FMT_C,
      "Pattern.compile": PAT_C, "Pattern.<init>": PAT_C, "toPlainString": STR_C, "Long.toString": STR_C,
      "Long.getChars": STR_C}
S = ["Thread.run", "feeSlow", "String.format", "Formatter.format"]
P = ["Thread.run", "feeSlow", "Pattern.compile", "Pattern.<init>"]
L = ["Thread.run", "feeSlow", "toPlainString", "Long.toString", "Long.getChars"]
ORDER = [S, P, S, L, P, S, L, P, S]          # the samples, at 10, 20, ..., 90 ms
SORTED = [0, 2, 5, 8, 3, 6, 1, 4, 7]         # sample index at each position after sorting by full name


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def frect(w, h, color, k=0.3):
    r = RoundedRectangle(corner_radius=0.05, width=w, height=h, stroke_color=color, stroke_width=2.5)
    return r.set_fill(shade(color, k), opacity=1)


def fbox(label, color, w, h, size=22):
    r = frect(w, h, color)
    if not label:
        return VGroup(r)
    return VGroup(r, M(label, size).move_to(r))


def top_edge(m, color=HOT_C):
    return Line([m.get_left()[0] + 0.04, m.get_top()[1], 0], [m.get_right()[0] - 0.04, m.get_top()[1], 0]).set_stroke(color, 7)


# the live stack (left), the snapshots on a time axis (right), the flame graph (full width)
LW, LH, LSTEP, LX, LY0 = 2.9, 0.5, 0.58, -4.55, -1.95
MW, MH, MSTEP, MX0, MDX, MY0 = 0.74, 0.28, 0.32, -1.2, 0.9, -1.95
U, BX0, BY0, BH, BSTEP = 1.4, -6.3, -1.9, 0.56, 0.61


def live(name, d):
    return fbox(name, FR[name], LW, LH).move_to([LX, LY0 + LH / 2 + d * LSTEP, 0])


def mini_col(stack, i):
    return VGroup(*[frect(MW, MH, FR[n]).move_to([MX0 + i * MDX, MY0 + MH / 2 + d * MSTEP, 0]) for d, n in enumerate(stack)])


def big_col(stack, pos, gap=0.14):
    return VGroup(*[frect(U - gap, BH, FR[n]).move_to([BX0 + (pos + 0.5) * U, BY0 + BH / 2 + d * BSTEP, 0])
                    for d, n in enumerate(stack)])


def merged(name, d, a, b):
    return fbox(name, FR[name], (b - a) * U - 0.06, BH).move_to([BX0 + (a + b) / 2 * U, BY0 + BH / 2 + d * BSTEP, 0])


GROUPS = [("Thread.run", 0, 0, 9), ("feeSlow", 1, 0, 9), ("String.format", 2, 0, 4), ("toPlainString", 2, 4, 6),
          ("Pattern.compile", 2, 6, 9), ("Formatter.format", 3, 0, 4), ("Long.toString", 3, 4, 6),
          ("Pattern.<init>", 3, 6, 9), ("Long.getChars", 4, 4, 6)]

# the real profile, from the lesson's figure (feeSlow zoomed in: x 20..660 is all 5,747 of its samples)
RS = 12.4 / 640
RY = [-1.5, -0.88, -0.26]
REAL = [(0, 20, 640, "feeSlow: 5,747 of 8,005 samples, 71.8%", FEE_C),
        (1, 20, 206.6, "String.format", FMT_C), (1, 227.6, 69.6, None, BIG_C), (1, 298.2, 19.7, None, SMALL_C),
        (1, 318.9, 101.3, None, STR_C), (1, 421.2, 155.9, "Pattern.compile", PAT_C), (1, 578.1, 37.6, None, SMALL_C),
        (1, 616.8, 42.2, None, OTHER_C),
        (2, 20, 191.7, "Formatter.format", FMT_C), (2, 227.6, 14.9, None, BIG_C), (2, 243.5, 52.6, None, BIG_C),
        (2, 318.9, 34.5, None, STR_C), (2, 354.4, 62.8, None, STR_C), (2, 421.2, 152.8, "Pattern.<init>", PAT_C),
        (2, 578.1, 35.6, None, SMALL_C)]


def real_box(row, x, w, label, color):
    b = fbox(label, color, w * RS, BH)
    return b.move_to([-6.2 + (x - 20 + w / 2) * RS, RY[row], 0])


class Perf06FlameGraph(VoiceScene):
    """perf-06 s2: a sampling profiler counts stacks; sorted and merged they become a flame graph; read width, order, tops."""

    def say(self, text, plan=(), after=0.25):
        """Speak text; plan is a list of (sentence index, [animations] or a function returning them, run_time)."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def construct(self):
        self.title_card("Reading a flame graph", "width is samples, the x-axis is the alphabet")

        # --- the question
        q1 = M("SlowFees.feeSlow", 34, FEE_C)
        q2 = T("where does its CPU time go?", 34)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.4)
        self.say("You want to know where feeSlow spends its CPU time, without changing its code.",
                 [(0, [FadeIn(q1, shift=UP * 0.15)], 0.8), (0, [FadeIn(q2)], 0.8)])
        self.play(FadeOut(qg), run_time=0.5)

        # --- a call stack: root at the bottom, callees on top, the top frame is where the CPU is
        fr = [live(n, d) for d, n in enumerate(S)]
        root_t = T("the root", 24, GREY_B).next_to(fr[0], RIGHT, buff=0.3)
        hot = top_edge(fr[3][0]).set_z_index(5)
        hot_t = T("the CPU is here", 24, HOT_C).next_to(fr[3], RIGHT, buff=0.3)
        self.say("Here is the thread's call stack. Thread.run is the root, at the bottom. "
                 "Each method sits on top of the one that called it. The top frame is where the CPU is right now.",
                 [(0, [FadeIn(fr[0], shift=UP * 0.1), FadeIn(fr[1], shift=UP * 0.1)], 0.8),
                  (1, [Indicate(fr[0], color=WHITE, scale_factor=1.05), FadeIn(root_t)], 0.8),
                  (2, [FadeIn(fr[2], shift=DOWN * 0.15)], 0.6), (2, [FadeIn(fr[3], shift=DOWN * 0.15)], 0.6),
                  (3, [Create(hot), FadeIn(hot_t)], 0.8)])

        # --- the sampling loop: every 10 ms, copy the stack onto a time axis
        axis = Arrow([MX0 - 0.55, MY0 - 0.1, 0], [6.45, MY0 - 0.1, 0], buff=0, stroke_width=2.5, color=GREY_B,
                     max_tip_length_to_length_ratio=0.025, max_stroke_width_to_length_ratio=10)
        ax_t = T("time, ms", 22, GREY_B).next_to(axis, LEFT, buff=0.15)
        ticks = VGroup(*[M(str(10 * (i + 1)), 22, GREY_B).move_to([MX0 + i * MDX, MY0 - 0.42, 0]) for i in range(9)])
        minis = [mini_col(ORDER[i], i) for i in range(9)]
        plan = [(0, [FadeOut(root_t), FadeOut(hot_t), Create(axis), FadeIn(ax_t)], 0.7)]
        cur = list(S)
        for i, st in enumerate(ORDER):
            k = 0
            while k < min(len(cur), len(st)) and cur[k] == st[k]:
                k += 1
            if k < max(len(cur), len(st)):
                old = VGroup(*fr[k:])
                new = [live(n, d) for d, n in enumerate(st)][k:]
                fr = fr[:k] + new
                new_hot = top_edge(fr[-1][0]).set_z_index(5)
                plan.append((1, [Succession(AnimationGroup(FadeOut(old, shift=UP * 0.12), FadeOut(hot, shift=UP * 0.12)),
                                            AnimationGroup(FadeIn(VGroup(*new), shift=DOWN * 0.12), FadeIn(new_hot, shift=DOWN * 0.12)))],
                             0.4 if i > 1 else 0.6))
                hot = new_hot
            cur = list(st)
            snap = VGroup(*[f[0] for f in fr])
            plan.append((1, [TransformFromCopy(snap, minis[i]), FadeIn(ticks[i]),
                             Flash(hot.get_center(), color=WHITE, line_length=0.18, flash_radius=0.35)],
                         0.36 if i > 1 else 0.6))
        self.say("The stack changes all the time. A sampling profiler is a loop: every 10 ms, it takes a snapshot of the stack.",
                 plan)

        # --- counting identical stacks: collapsed stacks
        rows = [("Thread.run;feeSlow;String.format;Formatter.format", "4", 0),
                ("Thread.run;feeSlow;Pattern.compile;Pattern.<init>", "3", 1),
                ("Thread.run;feeSlow;toPlainString;Long.toString;Long.getChars", "2", 3)]
        lines = VGroup(*[VGroup(M(a, 22, GREY_A), M(n, 24, YELLOW_M)).arrange(RIGHT, buff=0.3) for a, n, _ in rows])
        lines.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        head = T("collapsed stacks: one line per stack, then how many samples had it", 22, GREY_B)
        cg = VGroup(head, lines).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([0.2, 2.35, 0])
        kinds = [VGroup(*[minis[i] for i in range(9) if ORDER[i] is ORDER[j]]) for _, _, j in rows]
        self.say("Then it counts identical stacks. One line per stack, with its count: this text is what every flame graph tool reads.",
                 [(0, [FadeOut(VGroup(*fr)), FadeOut(hot), FadeIn(head)], 0.6)] +
                 [(0, [Indicate(kinds[j], color=WHITE, scale_factor=1.08), FadeIn(lines[j], shift=RIGHT * 0.1)], 0.7) for j in range(3)])

        # --- sort by full name, not by time
        bigs = [big_col(ORDER[i], i) for i in range(9)]
        grow = [ReplacementTransform(minis[i], bigs[i]) for i in range(9)]
        grow += [ticks[i].animate.move_to([BX0 + (i + 0.5) * U, BY0 - 0.35, 0]) for i in range(9)]
        grow += [FadeOut(axis), FadeOut(ax_t), FadeOut(cg)]
        def sort():
            out = []
            for i in range(9):
                dx = (SORTED.index(i) - i) * U
                if dx:
                    out += [bigs[i].animate(path_arc=-0.9).shift(RIGHT * dx), ticks[i].animate(path_arc=-0.9).shift(RIGHT * dx)]
            return out
        note = VGroup(M("java.lang.String", 22, FMT_C), M("<", 22, GREY_B), M("java.math.BigDecimal", 22, STR_C),
                      M("<", 22, GREY_B), M("java.util.regex.Pattern", 22, PAT_C)).arrange(RIGHT, buff=0.3)
        note.move_to([0, -3.0, 0])
        self.say("To draw a flame graph, the tool first sorts the stacks alphabetically, by full class name. "
                 "Not by time: the sample from 20 ms ends up on the right.",
                 [(0, grow, 1.4), (0, sort, 1.8), (0, [FadeIn(note, shift=UP * 0.1)], 0.6),
                  (1, [Indicate(VGroup(ticks[1], bigs[1]), color=WHITE, scale_factor=1.06)], 1.0)])

        # --- merge identical frames
        boxes = {}
        merges = []
        for name, d, a, b in GROUPS:
            src = VGroup(*[bigs[SORTED[p]][d] for p in range(a, b)])
            mb = merged(name, d, a, b)
            boxes[name] = mb
            merges.append(ReplacementTransform(src, mb[0]))
        labels = [boxes[n][1] for n, _, _, _ in GROUPS]
        self.say("Then identical frames at the same depth, under the same parent, merge into one box. "
                 "When each sample was taken is gone.",
                 [(0, merges, 1.5), (0, [FadeIn(VGroup(*labels))], 0.6),
                  (1, [FadeOut(ticks), FadeOut(note)], 0.8)])

        # --- rule 1: width is samples
        def under(a, b, y=BY0 - 0.12):
            return BraceBetweenPoints([BX0 + a * U + 0.04, y, 0], [BX0 + b * U - 0.04, y, 0], DOWN, color=GREY_B)

        br = under(0, 4)
        br_t = T("String.format: on 4 of the 9 samples", 26, FMT_C).next_to(br, DOWN, buff=0.15)
        self.say("So each box is one frame, and its width is the number of samples with that frame on the stack. "
                 "String.format was on 4 of the 9.",
                 [(0, [Indicate(boxes["Long.toString"], color=WHITE, scale_factor=1.06)], 0.8),
                  (1, [GrowFromCenter(br), FadeIn(br_t), Indicate(boxes["String.format"], color=FMT_C, scale_factor=1.04)], 1.0)])
        br2 = under(0, 9)
        br2_t = T("feeSlow: on all 9 samples", 26, FEE_C).next_to(br2, DOWN, buff=0.15)
        self.say("feeSlow was on all 9, so it spans the whole width.",
                 [(0, [ReplacementTransform(br, br2), ReplacementTransform(br_t, br2_t)], 0.8),
                  (0, [Indicate(boxes["feeSlow"], color=FEE_C, scale_factor=1.03)], 0.8)])

        # --- rule 2: the x-axis is the alphabet
        quote = T('"The ordering on the x-axis has no meaning."', 30).move_to([0, 2.85, 0])
        q_src = T("flamegraph.pl, in its own header", 22, GREY_B).next_to(quote, DOWN, buff=0.2)
        az = Arrow([BX0 + 0.1, BY0 - 0.3, 0], [-BX0 - 0.1, BY0 - 0.3, 0], buff=0, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.02, max_stroke_width_to_length_ratio=10)
        az_t = T("left to right: alphabetical, not time", 26).next_to(az, DOWN, buff=0.2)
        self.say("And left to right is the alphabet, not a timeline. "
                 "flamegraph.pl's own header says it: the ordering on the x-axis has no meaning.",
                 [(0, [FadeOut(br2), FadeOut(br2_t)], 0.4), (0, [GrowArrow(az), FadeIn(az_t)], 0.9),
                  (1, [FadeIn(quote, shift=DOWN * 0.1), FadeIn(q_src)], 1.0)])

        # --- rule 3: the tops are where the CPU was
        tops = VGroup(top_edge(boxes["Formatter.format"][0]), top_edge(boxes["Long.getChars"][0]),
                      top_edge(boxes["Pattern.<init>"][0]))
        self_t = T("self time: the CPU was in this frame's own code", 26, HOT_C)
        self_t.move_to([0, 2.0, 0])
        self.say("Now look at the tops. The part of a box with nothing above it is self time: "
                 "the CPU was in that frame's own code. Wide tops are where to start.",
                 [(0, [FadeOut(quote), FadeOut(q_src), FadeOut(az), FadeOut(az_t)], 0.6),
                  (1, [Create(tops), FadeIn(self_t)], 1.2),
                  (2, [Indicate(VGroup(boxes["Formatter.format"], tops[0]), color=HOT_C, scale_factor=1.04)], 1.0)])
        kids = VGroup(boxes["String.format"], boxes["toPlainString"], boxes["Pattern.compile"])
        caller_t = T("a wide box covered by its children is a caller", 26, FEE_C).move_to([0, -2.6, 0])
        self.say("feeSlow is wide, but covered by its children. It does little itself and calls expensive things, "
                 "so the fix is usually in one of them.",
                 [(0, [Indicate(boxes["feeSlow"], color=FEE_C, scale_factor=1.03), FadeIn(caller_t)], 1.0),
                  (1, [Indicate(kids, color=WHITE, scale_factor=1.04)], 1.0)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # --- a real profile of the same code
        title = T("a real CPU profile of the same fee code, zoomed in on feeSlow", 26).move_to([0, 3.0, 0])
        sub = T("8,005 samples in 10 seconds; percentages are shares of all samples", 22, GREY_B).next_to(title, DOWN, buff=0.18)
        real = [real_box(*r) for r in REAL]
        fee = real[0]
        row1 = VGroup(*[b for r, b in zip(REAL, real) if r[0] == 1])
        row2 = VGroup(*[b for r, b in zip(REAL, real) if r[0] == 2])
        bd, tp = real[2], real[4]
        bd_t = M("BigDecimal.<init>", 22, BIG_C).move_to([bd.get_center()[0], 1.05, 0])
        tp_t = M("toPlainString", 22, STR_C).move_to([tp.get_center()[0], 0.5, 0])
        bd_l = Line(bd_t.get_bottom() + DOWN * 0.08, [bd.get_center()[0], real[9].get_top()[1] + 0.06, 0], stroke_width=2, color=BIG_C)
        tp_l = Line(tp_t.get_bottom() + DOWN * 0.08, [tp.get_center()[0], real[11].get_top()[1] + 0.06, 0], stroke_width=2, color=STR_C)
        self.say("This is feeSlow in a real CPU profile of the same fee code, zoomed in. "
                 "It covered 5,747 of 8,005 samples: 71.8%.",
                 [(0, [FadeIn(title), FadeIn(sub)], 0.8), (0, [FadeIn(fee, shift=UP * 0.1)], 0.7),
                  (0, [LaggedStart(FadeIn(row1, shift=DOWN * 0.1), FadeIn(row2, shift=DOWN * 0.1), lag_ratio=0.5)], 1.2),
                  (0, [FadeIn(bd_t), Create(bd_l), FadeIn(tp_t), Create(tp_l)], 0.7),
                  (1, [Indicate(fee, color=FEE_C, scale_factor=1.02)], 1.0)])

        def entry(name, pct, color):
            return VGroup(M(name, 24, color), M(pct, 24)).arrange(RIGHT, buff=0.35)

        leg = [entry("String.format", "23.3%", FMT_C), entry("Pattern.compile", "17.6%", PAT_C),
               entry("toPlainString", "11.5%", STR_C), entry("BigDecimal.<init>", "7.9%", BIG_C)]
        for e, (x, y) in zip(leg, [(-3.2, -2.35), (3.2, -2.35), (-3.2, -2.95), (3.2, -2.95)]):
            e.move_to([x, y, 0])
        fmt_tower = VGroup(real[1], real[8])
        pat_tower = VGroup(real[5], real[13])
        self.say("Walk up from that wide plateau. Its widest children are String.format, with 23.3% of all samples, "
                 "and Pattern.compile, with 17.6%.",
                 [(0, [Indicate(fee, color=FEE_C, scale_factor=1.02)], 0.6),
                  (0, [Indicate(real[1], color=FMT_C, scale_factor=1.05)], 0.6),
                  (0, [Indicate(real[8], color=FMT_C, scale_factor=1.05)], 0.6),
                  (1, [Circumscribe(fmt_tower, color=FMT_C, buff=0.06), FadeIn(leg[0], shift=UP * 0.1)], 1.0),
                  (1, [Circumscribe(pat_tower, color=PAT_C, buff=0.06), FadeIn(leg[1], shift=UP * 0.1)], 1.0)])
        self.say("Then toPlainString, with 11.5%, and the BigDecimal constructor, with 7.9%.",
                 [(0, [Indicate(VGroup(tp, real[11], real[12], tp_t), color=STR_C, scale_factor=1.05), FadeIn(leg[2], shift=UP * 0.1)], 1.0),
                  (0, [Indicate(VGroup(bd, real[9], real[10], bd_t), color=BIG_C, scale_factor=1.05), FadeIn(leg[3], shift=UP * 0.1)], 1.0)])

        # --- the fix the graph points at
        ghost = DashedVMobject(RoundedRectangle(corner_radius=0.05, width=pat_tower.width, height=pat_tower.height)
                               .move_to(pat_tower), num_dashes=60).set_stroke(PAT_C, 2.5)
        gone = VGroup(T("about 18%", 24, PAT_C), T("gone", 24, PAT_C)).arrange(DOWN, buff=0.12).move_to(pat_tower)
        self.say("Pattern.compile builds a regex on every call. Move it into a static final field, "
                 "and that whole tower, about 18% of the samples, goes away.",
                 [(0, [Circumscribe(pat_tower, color=PAT_C, buff=0.06)], 1.0),
                  (1, [FadeOut(pat_tower), FadeIn(ghost)], 1.0), (1, [FadeIn(gone)], 0.6)])

        rules = VGroup(T("width: samples with that frame on the stack", 28),
                       T("left to right: the alphabet, not time", 28),
                       T("the tops: where the CPU was", 28, HOT_C)).arrange(DOWN, buff=0.22).move_to([0, 2.55, 0])
        self.say("Width is samples. Left to right is the alphabet. And the tops are where the CPU was.",
                 [(0, [FadeOut(title), FadeOut(sub)], 0.5), (0, [FadeIn(rules[0], shift=UP * 0.1)], 0.6),
                  (1, [FadeIn(rules[1], shift=UP * 0.1)], 0.6), (2, [FadeIn(rules[2], shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
