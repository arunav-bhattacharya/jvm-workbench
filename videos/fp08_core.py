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


def fill_of(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


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


def frame(w, h, color, k=0.10, sw=3):
    return RoundedRectangle(corner_radius=0.2, width=w, height=h, stroke_color=color, stroke_width=sw).set_fill(fill_of(color, k), 1)


def flash(r, color=YELLOW_M):
    return ShowPassingFlash(r.copy().set_fill(opacity=0).set_stroke(color, 7), time_width=0.6)


# one colour per meaning for the whole video
CORE_C, SHELL_C, VAL_C = TEAL_M, GOLD_M, BLUE_M
STEPS = [("read the clock", "io"), ("load payments", "io"), ("skip refunds", "d"), ("hold recent payments", "d"),
         ("sum per merchant", "d"), ("compute fees", "d"), ("call the payout API", "io"),
         ("save the ledger", "io"), ("println in between", "io")]
CORE_BOX = dict(w=4.4, h=3.0, c=[0, -0.15, 0])


class Fp08Core(Beat):
    """fp-08 section 3 (with section 0's read-only List): a functional core decides from plain values,
    a thin imperative shell reads the world and carries out the plan."""

    def construct(self):
        self.title_card("A functional core", "the core decides, the shell does the I/O")

        # ---------------- the problem: one loop that does everything ----------------
        rows = VGroup()
        for name, kind in STEPS:
            col = SHELL_C if kind == "io" else CORE_C
            rows.add(VGroup(Dot(radius=0.07, color=col), T(name, 24)).arrange(RIGHT, buff=0.2))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        job = frame(5.6, rows.height + 0.7, WHITE, 0.0).move_to([-3.3, -0.2, 0]).set_z_index(-1)
        rows.move_to(job).align_to(job.get_left() + RIGHT * 0.4, LEFT)
        job_t = M("LegacySettlementJob", 24, GREY_B).next_to(job, UP, buff=0.15).align_to(job, LEFT)
        self.seq("Here is a settlement job, written the usual way. One loop reads the clock, loads payments, "
                 "skips refunds, holds recent ones, sums per merchant, computes fees, calls the payout API, "
                 "and saves the ledger.",
                 [(0, [FadeIn(job), FadeIn(job_t)], 0.6),
                  (1, [LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rows], lag_ratio=0.35)], 5.0)])

        fakes = VGroup(*[frame(2.9, 0.75, SHELL_C).move_to([3.6, y, 0]) for y in (2.2, 1.0, -0.2)])
        fl = VGroup(*[T(t, 24).move_to(f) for t, f in zip(("fixed clock", "fake store", "fake payout API"), fakes)])
        wires = VGroup(*[DashedLine(rows[i].get_right() + RIGHT * 0.15, fakes[j].get_left(), dash_length=0.08, stroke_width=1.5,
                                    color=SHELL_C) for i, j in ((0, 0), (1, 1), (6, 2), (7, 1))])
        test = frame(3.4, 0.8, WHITE, 0.0).move_to([3.6, -1.9, 0])
        test_t = T("test: one fee rule", 24).move_to(test)
        tw = DashedLine(test.get_left(), rows[5].get_right() + RIGHT * 0.15, dash_length=0.08, stroke_width=1.5, color=WHITE)
        self.seq("It works. But to test one fee rule, you need a fixed clock, a fake store, a fake payout API, "
                 "and checks on what the fakes recorded.",
                 [(1, [FadeIn(test), FadeIn(test_t), Create(tw), Indicate(rows[5], color=CORE_C)], 0.8),
                  (1, [LaggedStart(*[FadeIn(VGroup(f, t)) for f, t in zip(fakes, fl)], lag_ratio=0.4), Create(wires)], 1.6)])

        # ---------------- pull it apart ----------------
        shell = frame(12.8, 6.2, SHELL_C, 0.05).move_to([0, -0.25, 0]).set_z_index(-2)
        shell_t = T("imperative shell: touches the world", 26, SHELL_C).move_to([-6.0, 2.45, 0], aligned_edge=LEFT)
        core = frame(CORE_BOX["w"], CORE_BOX["h"], CORE_C, 0.14).move_to(CORE_BOX["c"]).set_z_index(-1)
        core_t = T("functional core: decides", 26, CORE_C).next_to(core.get_top(), DOWN, buff=0.25)
        dec = [i for i, (_, k) in enumerate(STEPS) if k == "d"]
        reads, acts = [0, 1], [6, 7, 8]
        targets = {}
        for k, i in enumerate(dec):
            targets[i] = [0, core.get_top()[1] - 0.95 - 0.48 * k, 0]
        for k, i in enumerate(reads):
            targets[i] = ([-3.05, 1.0 - 0.6 * k, 0], RIGHT)
        for k, i in enumerate(acts):
            targets[i] = ([3.1, 1.0 - 0.6 * k, 0], LEFT)
        for i, r in enumerate(rows):
            r.generate_target()
            if i in acts:
                r.target.scale(22 / 24)
            if i in dec:
                r.target.move_to(targets[i])
            else:
                r.target.move_to(targets[i][0], aligned_edge=targets[i][1])
        self.seq("Look at the colours. The teal lines only decide. The gold lines touch the world. "
                 "Pull them apart: the decisions go into a core, and the I/O wraps around it.",
                 [(1, [*[Indicate(rows[i], color=CORE_C, scale_factor=1.05) for i in dec]], 0.9),
                  (2, [*[Indicate(rows[i], color=SHELL_C, scale_factor=1.05) for i in reads + acts]], 0.9),
                  (3, [FadeOut(VGroup(fakes, fl, wires, test, test_t, tw, job, job_t))], 0.6),
                  (3, [FadeIn(shell), FadeIn(core), *[MoveToTarget(r) for r in rows]], 1.4),
                  (3, [FadeIn(shell_t), FadeIn(core_t)], 0.5)])

        a_in = Arrow([-4.6, -0.45, 0], [core.get_left()[0], -0.45, 0], buff=0.08, stroke_width=3, color=VAL_C,
                     max_tip_length_to_length_ratio=0.12)
        a_out = Arrow([core.get_right()[0], -0.95, 0], [4.6, -0.95, 0], buff=0.08, stroke_width=3, color=VAL_C,
                      max_tip_length_to_length_ratio=0.12)
        l_in = T("plain values", 22, VAL_C).next_to(a_in, DOWN, buff=0.15)
        l_out = T("a plan", 22, VAL_C).next_to(a_out, DOWN, buff=0.15)
        self.seq("The core is a pure function. It takes plain values, today's date included, and returns a plan: "
                 "a value that says what should happen. This shape is called a functional core and an imperative shell.",
                 [(1, [GrowArrow(a_in), FadeIn(l_in)], 0.6),
                  (1, [GrowArrow(a_out), FadeIn(l_out)], 0.6),
                  (2, [flash(core, CORE_C), flash(shell, SHELL_C)], 1.2)])

        # ---------------- the smallest core: void old authorizations ----------------
        core_t2 = M("decideVoids(auths, now)", 24, CORE_C).move_to(core_t)
        rule = T("older than 7 days: void it", 24).move_to(core.get_center() + DOWN * 0.15)
        clock = VGroup(T("now", 22, GREY_B), M("2026-03-10 09:00", 22, VAL_C)).arrange(DOWN, buff=0.08).move_to([-4.4, 1.0, 0])
        a1 = chip("a1: 8 days old", VAL_C, size=22).move_to([-4.4, -0.2, 0])
        a2 = chip("a2: 30 hours old", VAL_C, size=22).move_to([-4.4, -0.95, 0])
        gw = frame(2.6, 0.85, WHITE, 0.0).move_to([4.4, 0.25, 0])
        gw_t = T("gateway", 24).move_to(gw)
        self.seq("Here is the smallest one, from the lesson. Card authorizations older than seven days get voided. "
                 "The shell reads the clock, and loads two: a1, eight days old, and a2, thirty hours old.",
                 [(0, [FadeOut(VGroup(*[rows[i] for i in reads + acts + dec], a_in, a_out, l_in, l_out)),
                       Transform(core_t, core_t2)], 0.8),
                  (1, [FadeIn(rule), FadeIn(gw), FadeIn(gw_t)], 0.7),
                  (2, [FadeIn(clock, shift=RIGHT * 0.1)], 0.5),
                  (2, [FadeIn(a1, shift=RIGHT * 0.1)], 0.5),
                  (2, [FadeIn(a2, shift=RIGHT * 0.1)], 0.5)],
                 say="Here is the smallest one, from the lesson. Card authorizations older than seven days get voided. "
                     "The shell reads the clock, and loads two: a one, eight days old, and a two, thirty hours old.")

        o1 = chip("VoidIt(authId=a1)", RED_M, size=22, mono=True).move_to([0, -2.25, 0])
        o2 = chip("Keep(authId=a2, expiresIn=PT138H)", GREEN_M, size=22, mono=True).move_to([0, -2.85, 0])
        ins = VGroup(clock.copy(), a1.copy(), a2.copy())
        self.seq("It hands them to the core as values. The core returns two decisions: void a1, and keep a2, "
                 "with 138 hours left. It called nothing, and read no clock.",
                 [(0, [*[m.animate.move_to(core.get_center() + LEFT * 0.4 + DOWN * 0.15).scale(0.6).set_opacity(0) for m in ins]], 1.0),
                  (1, [flash(core, CORE_C)], 0.6),
                  (1, [FadeIn(o1, shift=DOWN * 0.2)], 0.5),
                  (1, [FadeIn(o2, shift=DOWN * 0.2)], 0.5),
                  (2, [Indicate(core_t, color=CORE_C)], 0.8)],
                 say="It hands them to the core as values. The core returns two decisions: void a one, and keep a two, "
                     "with 138 hours left. It called nothing, and read no clock.")

        post = VGroup(M("POST", 22, SHELL_C), M("/authorizations/a1/void", 22, SHELL_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        post.next_to(gw, UP, buff=0.3).align_to([2.4, 0, 0], LEFT)
        o1c = o1.copy()
        self.seq("Then the shell carries out the plan: one call to the gateway.",
                 [(0, [MoveAlongPath(o1c, VMobject().set_points_as_corners(
                      [o1.get_center(), [gw.get_x(), o1.get_y(), 0], [gw.get_x(), gw.get_bottom()[1] - 0.4, 0]]))], 1.1),
                  (0, [FadeOut(o1c, shift=UP * 0.3), flash(gw, SHELL_C), FadeIn(post)], 0.6)])

        # testing the core: no shell needed
        clock2 = VGroup(T("now + 1 day", 22, GREY_B), M("2026-03-11 09:00", 22, VAL_C)).arrange(DOWN, buff=0.08).move_to(clock)
        o2b = chip("Keep(authId=a2, expiresIn=PT114H)", GREEN_M, size=22, mono=True).move_to(o2)
        no = T("no fakes, no clock: a list and a date", 24, CORE_C).move_to([3.0, 2.45, 0])
        self.seq("A test needs none of the shell. Call the core with a list and a date, one day later, "
                 "and compare the result. a2 is still kept, now with 114 hours left.",
                 [(0, [shell.animate.set_opacity(0.15), shell_t.animate.set_opacity(0.25), FadeOut(VGroup(gw, gw_t, post))], 0.7),
                  (1, [Transform(clock, clock2), FadeIn(no)], 0.7),
                  (2, [Indicate(o1, color=RED_M, scale_factor=1.05)], 0.6),
                  (2, [Transform(o2, o2b)], 0.7)],
                 say="A test needs none of the shell. Call the core with a list and a date, one day later, "
                     "and compare the result. a two is still kept, now with 114 hours left.")
        self.play(FadeOut(VGroup(shell, shell_t, core, core_t, rule, clock, a1, a2, o1, o2, no)), run_time=0.7)

        # ---------------- the inputs must hold still: read-only is not immutable ----------------
        lst = frame(2.6, 0.9, WHITE, 0.0).move_to([1.6, 0.0, 0])
        items = M("[p1]", 28).move_to(lst)
        batch = frame(4.8, 1.5, VAL_C).move_to([-3.6, 1.4, 0])
        b_t = VGroup(M('Batch("b-7")', 24, VAL_C), M("paymentIds: List", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        b_t.move_to(batch).align_to(batch.get_left() + RIGHT * 0.35, LEFT)
        buf = frame(4.8, 1.1, SHELL_C).move_to([-3.6, -1.4, 0])
        buf_t = VGroup(M("backing", 24, SHELL_C), T("the caller's MutableList", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        buf_t.move_to(buf).align_to(buf.get_left() + RIGHT * 0.35, LEFT)
        p_b = Arrow(batch.get_right() + DOWN * 0.3, lst.get_left() + UP * 0.2, buff=0.1, stroke_width=3, color=VAL_C,
                    max_tip_length_to_length_ratio=0.12)
        p_k = Arrow(buf.get_right(), lst.get_left() + DOWN * 0.2, buff=0.1, stroke_width=3, color=SHELL_C,
                    max_tip_length_to_length_ratio=0.12)
        one = T("one list, two names", 24, GREY_B).next_to(lst, DOWN, buff=0.3)
        self.seq("All of this needs inputs that hold still. A read-only List does not promise that. "
                 "Build a batch from the caller's list, and both point at the same list.",
                 [(0, [FadeIn(batch), FadeIn(b_t)], 0.6),
                  (1, [Indicate(b_t[1], color=VAL_C)], 0.8),
                  (2, [FadeIn(lst), FadeIn(items), GrowArrow(p_b)], 0.7),
                  (2, [FadeIn(buf), FadeIn(buf_t), GrowArrow(p_k), FadeIn(one)], 0.7)])

        items2 = M("[p1, p2]", 28).move_to(lst)
        cmd = M('backing += "p2"', 24, SHELL_C).next_to(buf, DOWN, buff=0.3).align_to(buf, LEFT)
        seen = VGroup(T("the batch now shows", 24, GREY_B), M("[p1, p2]", 24, RED_M)).arrange(RIGHT, buff=0.2)
        seen.next_to(batch, UP, buff=0.25).align_to(batch, LEFT)
        self.seq("The caller adds p2. The batch shows p1 and p2: it changed under your feet.",
                 [(0, [FadeIn(cmd, shift=UP * 0.1)], 0.5),
                  (0, [flash(p_k, SHELL_C), Transform(items, items2), lst.animate.stretch_to_fit_width(3.0)], 0.7),
                  (1, [flash(p_b, VAL_C), FadeIn(seen, shift=UP * 0.1)], 0.8)],
                 say="The caller adds p two. The batch shows p one and p two: it changed under your feet.")

        snap = frame(2.2, 0.9, VAL_C).move_to([1.6, 2.2, 0])
        snap_t = M("[p1]", 28).move_to(snap)
        p_b2 = Arrow(batch.get_right() + UP * 0.2, snap.get_left(), buff=0.1, stroke_width=3, color=VAL_C,
                     max_tip_length_to_length_ratio=0.12)
        fixk = VGroup(T("Kotlin", 22, GREY_B), M('Batch("b-7", backing.toList())', 22)).arrange(RIGHT, buff=0.3)
        fixj = VGroup(T("Java", 22, GREY_B), M('new Batch("b-7", List.copyOf(backing))', 22)).arrange(RIGHT, buff=0.3)
        fixes = VGroup(fixk, fixj).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0.2, -2.75, 0])
        fixj[1].align_to(fixk[1], LEFT)
        self.seq("Copy at the boundary. With toList in Kotlin, or List.copyOf in Java, the batch keeps its own snapshot.",
                 [(0, [FadeOut(seen), FadeOut(cmd), FadeOut(one)], 0.4),
                  (1, [FadeIn(fixes, shift=UP * 0.1)], 0.7),
                  (1, [ReplacementTransform(p_b, p_b2), FadeIn(snap), FadeIn(snap_t)], 0.8)],
                 say="Copy at the boundary. With to-list in Kotlin, or List dot copy-of in Java, the batch keeps its own snapshot.")
        self.play(FadeOut(VGroup(lst, items, batch, b_t, buf, buf_t, p_b2, p_k, snap, snap_t, fixes)), run_time=0.6)

        # ---------------- the shell in code ----------------
        kt = code(["val today = LocalDate.now(clock)",
                   "val plan = planSettlement(",
                   "    store.capturedPayments(), store.merchants(), today)",
                   "plan.payouts.forEach(payouts::send)"], 22)
        jv = code(["LocalDate today = LocalDate.now(clock);",
                   "SettlementPlan plan = planSettlement(",
                   "        store.capturedPayments(), store.merchants(), today);",
                   "plan.payouts().forEach(payouts::send);"], 22)
        kh, jh = T("Kotlin", 24, GREY_B), T("Java", 24, GREY_B)
        jv.next_to(kt, DOWN, buff=0.7).align_to(kt, LEFT)
        kh.next_to(kt[0], LEFT, buff=0.5)
        jh.next_to(jv[0], LEFT, buff=0.5).align_to(kh, LEFT)
        tags = VGroup()
        for c in (kt, jv):
            for idx, (word, col) in zip((0, 1, 3), (("1. read", SHELL_C), ("2. decide", CORE_C), ("3. act", SHELL_C))):
                tags.add(T(word, 22, col).move_to([5.6, c[idx].get_y(), 0]))
        cg = VGroup(kh, kt, jh, jv)
        cg.scale(min(1, 10.6 / cg.width)).move_to([-0.9, 0.2, 0])
        for c, base in ((kt, 0), (jv, 3)):
            for k, idx in enumerate((0, 1, 3)):
                tags[base + k].move_to([5.55, c[idx].get_y(), 0])
        self.seq("In code, the shell is three steps: read, decide, act. The same in Kotlin and in Java.",
                 [(0, [FadeIn(VGroup(kh, kt), shift=UP * 0.1), FadeIn(VGroup(jh, jv), shift=UP * 0.1)], 1.0),
                  (0, [LaggedStart(*[FadeIn(t) for t in tags], lag_ratio=0.12)], 1.2),
                  (0, [Indicate(VGroup(kt[1], kt[2], jv[1], jv[2]), color=CORE_C, scale_factor=1.02)], 1.0)])
        self.wait(1.0)
        self.play(FadeOut(VGroup(cg, tags)), run_time=0.6)

        # ---------------- the rule and a check ----------------
        shell = frame(9.0, 3.2, SHELL_C, 0.05).move_to([0, 1.2, 0])
        core = frame(4.0, 1.6, CORE_C, 0.14).move_to([0, 1.0, 0])
        rule = VGroup(T("The core decides from plain values.", 30, CORE_C),
                      T("The shell does the I/O around it.", 30, SHELL_C)).arrange(DOWN, buff=0.2)
        rule.move_to(core)
        core.stretch_to_fit_width(rule.width + 0.6).stretch_to_fit_height(rule.height + 0.5)
        shell.stretch_to_fit_width(core.width + 1.6)
        self.beat("So: the core decides from plain values, and the shell does the I/O around it.",
                  FadeIn(shell), FadeIn(core), FadeIn(rule), run_time=1.2)
        chk = M("val today = LocalDate.now()   // inside the core", 26).move_to([0, -1.4, 0])
        q = T("Is the core still pure?", 28, GREY_B).move_to([0, -2.2, 0])
        self.seq("A quick check. A teammate reads the clock inside the core. Is it still pure?",
                 [(1, [FadeIn(chk, shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(q)], 0.4)])
        self.wait(2.2)
        ans = VGroup(T("No:", 28, RED_M), T("the clock is a hidden input. Read it in the shell and pass today in.", 26)
                     ).arrange(RIGHT, buff=0.25).move_to([0, -2.2, 0])
        fit(ans, 12.6)
        self.seq("No. The clock is a hidden input, so the same arguments can give a different plan. "
                 "Read it in the shell, and pass today in.",
                 [(0, [ReplacementTransform(q, ans)], 0.7),
                  (1, [flash(shell, SHELL_C)], 0.8)])
        self.wait(1.0)
