from fg import *
import fg

fg.SAY[:0] = [(r"\bVarHandles?\b", lambda m: "var handle" + ("s" if m.group(0).endswith("s") else "")),
              (r"\bsetRelease\b", "set release"), (r"\bgetAcquire\b", "get acquire"),
              (r"\bjcstress\b", "J C stress"), (r"\b1,250,000\b", "one million two hundred fifty thousand"),
              (r"\bx86\b", "x eighty-six"), (r"\bARM\b", "arm"), (r"\bREADY\b", "ready")]


# ---- helpers for this file ----
def code(lines, size=26, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def tag(text, color, size=24):
    t = M(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=t.height + 0.26, stroke_color=color, stroke_width=2)
    r.set_fill(BLACK, 1)
    return VGroup(r, t)


class Jmm06Varhandles(VoiceScene):
    """jmm-06, section 1: a VarHandle puts the memory mode on each access instead of on the field; the four
    modes as a ladder (plain, opaque, acquire/release, volatile), shown on one writer/board/reader handoff;
    release/acquire hands over everything written before the release to the acquire that sees it."""

    def construct(self):
        self.title_card("VarHandles and memory modes", "the rules go on each access, not on the field")

        # ---------------- the hook: rules on the field ----------------
        fld = box("ready", WHITE, w=2.4, h=0.9, size=32).move_to([0, -0.3, 0])
        prod = VGroup(Dot(radius=0.13, color=BLUE_M), T("producer", 30, BLUE_M)).arrange(DOWN, buff=0.2).move_to([-4.7, -0.3, 0])
        cons = VGroup(Dot(radius=0.13, color=TEAL_M), T("consumer", 30, TEAL_M)).arrange(DOWN, buff=0.2).move_to([4.7, -0.3, 0])
        vtag = tag("volatile", RED_M, 28).next_to(fld, UP, buff=0.12)
        w_ar = Arrow(prod.get_right() + RIGHT * 0.1, fld.get_left(), buff=0.15, stroke_width=3, color=BLUE_M,
                     max_tip_length_to_length_ratio=0.08)
        r_ar = Arrow(fld.get_right(), cons.get_left() + LEFT * 0.1, buff=0.15, stroke_width=3, color=TEAL_M,
                     max_tip_length_to_length_ratio=0.08)
        self.beat("A producer hands millions of messages a second to a consumer through a volatile field.",
                  FadeIn(prod), FadeIn(cons), FadeIn(fld), FadeIn(vtag), GrowArrow(w_ar), GrowArrow(r_ar), run_time=1.6)

        pulses = [(Dot(radius=0.09, color=BLUE_M).move_to(w_ar.get_start()),
                   T("store buffer drain", 24, RED_M).move_to([-2.45, -1.15, 0])) for _ in range(3)]
        steps = []
        for d, dr in pulses:
            steps.append(([FadeIn(d, run_time=0.1)], 0.1))
            steps.append(([d.animate.move_to(w_ar.get_end()), FadeIn(dr, shift=DOWN * 0.15)], 0.6))
            steps.append(([FadeOut(d), FadeOut(dr), Flash(fld, color=RED_M, flash_radius=1.4)], 0.5))
        seq(self, "Marking it volatile puts the rules on the field. Every write pays for the strongest rules: "
                  "on x86, a drain of the store buffer.",
            1.4, *steps)
        ptag = T("plain field", 24, GREY_B).next_to(fld, DOWN, buff=0.2)
        wt = tag("setRelease", GOLD_M).next_to(w_ar, UP, buff=0.15)
        rt = tag("getAcquire", GOLD_M).next_to(r_ar, UP, buff=0.15)
        seq(self, "A VarHandle moves the rules onto each access. The field stays plain, "
                  "and each read or write picks its own mode.",
            ([FadeOut(vtag, shift=UP * 0.3)], 0.6), ([FadeIn(ptag)], 0.5), 1.0,
            ([FadeIn(wt, shift=DOWN * 0.2), FadeIn(rt, shift=DOWN * 0.2)], 0.9))
        self.play(FadeOut(VGroup(fld, prod, cons, w_ar, r_ar, ptag, wt, rt)), run_time=0.6)

        # ---------------- the handoff: writer, shared memory, reader ----------------
        ROWS = {"total": 1.05, "count": 0.1, "ready": -0.85}
        WX, BX, RX = -4.5, 0.0, 4.5
        FS, BY, BH = 26, 0.1, 3.1
        pad = RoundedRectangle(corner_radius=0.12, width=3.8, height=BH, stroke_color=BLUE_M, stroke_width=2.5)
        pad.set_fill(dark(BLUE_M, 0.08), 1).move_to([WX, BY, 0])
        pad_l = T("writer", 32, BLUE_M).move_to([WX, 2.1, 0])
        wl = {k: M(f"{k} = {v}", FS, BLUE_M).move_to([WX, y, 0])
              for (k, y), v in zip(ROWS.items(), ("1,250,000", "42", "true"))}
        for k in wl:
            wl[k].align_to(pad, LEFT).shift(RIGHT * 0.26)
        board = RoundedRectangle(corner_radius=0.12, width=3.8, height=BH, stroke_color=WHITE, stroke_width=2.5)
        board.set_fill(BLACK, 1).move_to([BX, BY, 0])
        board_l = T("shared memory", 32).move_to([BX, 2.1, 0])
        cells, cvals, clabs = {}, {}, {}
        for k, y in ROWS.items():
            clabs[k] = M(k, FS, GREY_A).move_to([BX - 1.15, y, 0])
            cells[k] = RoundedRectangle(corner_radius=0.06, width=2.2, height=0.62, stroke_color=GREY_D, stroke_width=2).move_to([BX + 0.65, y, 0])
            cvals[k] = M("false" if k == "ready" else "0", FS).move_to(cells[k])
        rbox = RoundedRectangle(corner_radius=0.12, width=3.8, height=BH, stroke_color=TEAL_M, stroke_width=2.5)
        rbox.set_fill(dark(TEAL_M, 0.08), 1).move_to([RX, BY, 0])
        rbox_l = T("reader", 32, TEAL_M).move_to([RX, 2.1, 0])
        rd_note = T("waits for ready, then reads total", 24, GREY_B).move_to([RX, -1.85, 0])

        def rline(k, v, col=TEAL_M):
            return M(f"{k}: {v}", FS, col).move_to([RX, ROWS[k], 0]).align_to(rbox, LEFT).shift(RIGHT * 0.25)

        self.beat("Take one handoff. The writer sets total and count, then ready.",
                  FadeIn(pad), FadeIn(pad_l), FadeIn(board), FadeIn(board_l), *[FadeIn(c) for c in cells.values()],
                  *[FadeIn(c) for c in cvals.values()], *[FadeIn(c) for c in clabs.values()],
                  LaggedStart(*[FadeIn(wl[k], shift=RIGHT * 0.2) for k in ROWS], lag_ratio=0.5), run_time=2.4)
        self.beat("The reader waits for ready, then reads total.",
                  FadeIn(rbox), FadeIn(rbox_l), FadeIn(rd_note), run_time=1.0)

        head = T("plain", 36, GREY_B).move_to([0, 2.85, 0])

        def set_head(text, col):
            return Transform(head, T(text, 36, col).move_to([0, 2.85, 0]))

        def chip_for(k):
            v = {"total": "1,250,000", "count": "42", "ready": "true"}[k]
            return M(v, FS, BLUE_M).move_to([wl[k].get_right()[0] - M(v, FS).width / 2, ROWS[k], 0])

        def land(k, val, col=BLUE_M):
            return Transform(cvals[k], M(val, FS, col).move_to(cells[k]))

        # plain
        r_ready = rline("ready", "false")
        loop = Arc(radius=0.22, start_angle=0, angle=1.6 * PI, color=TEAL_M, stroke_width=3).add_tip(tip_length=0.12)
        loop.next_to(r_ready, RIGHT, buff=0.3)
        self.beat("Plain mode promises nothing about what the other thread sees, or when.",
                  FadeIn(head), FadeIn(r_ready), run_time=1.0)
        stuck = T("stuck", 28, RED_M).next_to(loop, UP, buff=0.15)
        seq(self, "The JIT may read ready once for the whole loop. The reader spins forever.",
            ([FadeIn(loop)], 0.4), ([Rotate(loop, angle=-4 * PI, about_point=loop.get_center(), rate_func=linear)], 2.4),
            ([FadeIn(stuck)], 0.5))
        self.play(FadeOut(VGroup(r_ready, loop, stuck)), run_time=0.4)

        # opaque
        ch = {k: chip_for(k) for k in ROWS}
        r_ready = rline("ready", "true")
        r_total = rline("total", "0", RED_M)
        seq(self, "Opaque makes every access really happen, so the reader does see ready turn true.",
            ([set_head("opaque", PURPLE_M)], 0.6), 1.2,
            ([ch["ready"].animate.move_to(cells["ready"]), cvals["ready"].animate.set_opacity(0)], 0.9),
            ([FadeOut(ch["ready"]), land("ready", "true"), FadeIn(r_ready)], 0.5))
        seq(self, "But it orders nothing else. ready can arrive before total, and the reader reads a total of zero.",
            1.6, ([Indicate(cvals["total"], color=RED_M, scale_factor=1.3)], 0.8), ([FadeIn(r_total, shift=RIGHT * 0.2)], 0.6))
        arm = VGroup(T("jcstress on ARM:", 24, PURPLE_M), T("0.68% of samples", 24, PURPLE_M)).arrange(DOWN, buff=0.1).move_to([RX, -2.0, 0])
        seq(self, "On ARM, jcstress caught this in 0.68 percent of samples.",
            ([FadeOut(rd_note), FadeIn(arm)], 0.6))
        self.play(FadeOut(VGroup(r_ready, r_total, arm)), land("ready", "false", WHITE), run_time=0.6)

        # release / acquire
        env = RoundedRectangle(corner_radius=0.12, width=3.62, height=2.85, stroke_color=GOLD_M, stroke_width=3.5)
        env.move_to([WX, BY, 0])
        rel = M("ready: setRelease", 24, GOLD_M).next_to(pad, DOWN, buff=0.18)
        bar = Line([WX - 1.7, -0.38, 0], [WX + 1.7, -0.38, 0], stroke_width=4, color=GOLD_M)
        seq(self, "Now make the last write a release. Nothing written before it may move after it, "
                  "like a sealed envelope that holds all of it.",
            ([set_head("release / acquire", GOLD_M), wl["ready"].animate.set_color(GOLD_M), Create(bar), FadeIn(rel)], 1.4),
            1.0, ([Create(env)], 1.0))
        acq = M("ready: getAcquire", 24, GOLD_M).next_to(rbox, DOWN, buff=0.18)
        r_ready = rline("ready", "true")
        chips = VGroup(*[chip_for(k) for k in ROWS])
        env2 = env.copy().set_fill(BLACK, 1)
        moving = VGroup(env2, chips)
        seq(self, "The release lands. The reader reads ready with an acquire, and sees true. What total can it read now?",
            ([FadeIn(chips)], 0.2), ([moving.animate.move_to([BX, BY, 0])], 1.2), 0.6,
            ([FadeIn(acq), FadeIn(r_ready)], 0.6))
        self.wait(1.3)
        r_total = rline("total", "1,250,000", GREEN_M)
        r_count = rline("count", "42", GREEN_M)
        for k in ROWS:
            cvals[k].set_opacity(0)
        seq(self, "Only 1,250,000. Everything the writer did before the release is visible after the acquire that sees it.",
            ([FadeOut(moving), land("total", "1,250,000"), land("count", "42"), land("ready", "true")], 0.6),
            ([FadeIn(r_total, shift=RIGHT * 0.2), FadeIn(r_count, shift=RIGHT * 0.2)], 0.7))
        self.play(FadeOut(VGroup(pad, pad_l, *wl.values(), board, board_l, *cells.values(), *cvals.values(),
                                 *clabs.values(), rbox, rbox_l, env, rel, bar, acq, r_ready, r_total, r_count, head)),
                  run_time=0.7)

        # ---------------- volatile: one order for everyone ----------------
        head = T("volatile", 36, RED_M).move_to([0, 2.85, 0])
        ta = VGroup(T("thread A", 34, BLUE_M), M("x = 1", 34, BLUE_M), M("read y", 34, BLUE_M)).arrange(DOWN, buff=0.35)
        tb = VGroup(T("thread B", 34, TEAL_M), M("y = 1", 34, TEAL_M), M("read x", 34, TEAL_M)).arrange(DOWN, buff=0.35)
        ta.move_to([-3.0, 1.0, 0]); tb.move_to([3.0, 1.0, 0])
        both = T("both read 0?", 36, WHITE).move_to([0, -0.6, 0])
        self.beat("Release and acquire still allow one odd result: each thread writes its own flag, "
                  "reads the other's, and both read zero.",
                  FadeIn(head), FadeIn(ta), FadeIn(tb), FadeIn(both), run_time=1.6)
        ra_r = VGroup(T("release / acquire:", 32, GOLD_M), T("allowed (6.18% in one run)", 32, GOLD_M)).arrange(RIGHT, buff=0.2)
        vo_r = VGroup(T("volatile:", 32, RED_M), T("never", 32, RED_M)).arrange(RIGHT, buff=0.2)
        ra_r.move_to([0, -1.55, 0]); vo_r.move_to([0, -2.35, 0])
        self.play(FadeIn(ra_r, shift=UP * 0.15), run_time=0.6)
        self.beat("Volatile forbids it. All threads agree on one order of every volatile access, "
                  "so at least one of them sees the other's write.", FadeIn(vo_r, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(head, ta, tb, both, ra_r, vo_r)), run_time=0.6)

        # ---------------- the ladder ----------------
        rungs = [("plain", GREY_B, "no promise to other threads", "ordinary store"),
                 ("opaque", PURPLE_M, "+ each access really happens", "ordinary store"),
                 ("release / acquire", GOLD_M, "+ hands over earlier writes", "ordinary store"),
                 ("volatile", RED_M, "+ one order for all threads", "store + drain")]
        lad = VGroup()
        for j, (nm, col, pr, cost) in enumerate(rungs):
            y = -2.0 + j * 1.1
            row = VGroup(T(nm, 30, col).move_to([-6.2, y, 0], aligned_edge=LEFT),
                         T(pr, 28, WHITE).move_to([-2.4, y, 0], aligned_edge=LEFT),
                         T(cost, 28, RED_M if j == 3 else GREY_B).move_to([6.3, y, 0], aligned_edge=RIGHT))
            lad.add(row)
        lines = VGroup(*[Line([-6.3, -2.55 + j * 1.1, 0], [6.4, -2.55 + j * 1.1, 0], stroke_width=1.5, color=GREY_D)
                         for j in range(5)])
        x86 = T("x86 write", 26, GREY_B).move_to([5.2, 2.3, 0])
        self.beat("So the modes form a ladder. Each one keeps everything below it, and adds one promise.",
                  Create(lines), LaggedStart(*[FadeIn(VGroup(r[0], r[1]), shift=UP * 0.15) for r in lad], lag_ratio=0.35),
                  run_time=2.6)
        self.beat("On x86, only the volatile write costs extra: it drains the store buffer. "
                  "So a release write is cheaper.",
                  FadeIn(x86), LaggedStart(*[FadeIn(r[2]) for r in lad], lag_ratio=0.3), run_time=2.0)
        self.play(FadeOut(VGroup(lad, lines, x86)), run_time=0.6)

        # ---------------- code ----------------
        jc = code(["report.total = 1_250_000;",
                   "READY.setRelease(report, true);",
                   "",
                   "if ((boolean) READY.getAcquire(report))",
                   "    publish(report.total);"], 24)
        kc = code(["report.total = 1_250_000",
                   "READY.setRelease(report, true)",
                   "",
                   "if (READY.getAcquire(report) as Boolean)",
                   "    publish(report.total)"], 24)
        for b in (jc, kc):
            b[0].set_color(BLUE_M); b[1].set_color(GOLD_M)
            b[3].set_color(GOLD_M); b[4].set_color(TEAL_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin: the same JDK class", kc)).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.3, 0])
        note = T("READY: a static final VarHandle for the plain field ready", 22, GREY_B).move_to([0, -3.05, 0])
        self.beat("In code, READY is a VarHandle for the field ready. "
                  "The writer calls setRelease. The reader calls getAcquire.",
                  FadeIn(cg, shift=UP * 0.2), FadeIn(note), run_time=1.6)
        self.play(FadeOut(VGroup(cg, note)), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = T("A release hands over everything written before it", 34).move_to([0, 2.3, 0])
        rule2 = T("to the acquire that sees it, on the same variable.", 34, GOLD_M).move_to([0, 1.65, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule2.width))
        self.beat("The rule. A release write hands over everything written before it, to the acquire read that sees it, "
                  "on the same variable.", FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("A field is declared volatile. A hot loop reads it with", 28).move_to([0, 0.2, 0])
        chk2 = M("ITEM.get(this)", 28, GREY_B).move_to([0, -0.4, 0])
        chk3 = T("Is that read volatile?", 28).move_to([0, -1.0, 0])
        VGroup(chk, chk2, chk3).scale(min(1, 12 / chk.width))
        self.beat("Check yourself. A volatile field is read in a hot loop, with a plain get on a VarHandle. "
                  "Is that read volatile?", FadeIn(chk), FadeIn(chk2), FadeIn(chk3), run_time=1.2)
        self.wait(2.5)
        ans = T("No. The mode at the access wins: it is a plain read, and the JIT may read it once.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -2.2, 0])
        self.beat("No. The mode at the access wins. It is a plain read, and the JIT may read it once for the whole loop.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.5)
