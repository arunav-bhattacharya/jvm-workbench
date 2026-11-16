from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bSEPA\b", "seepa"), (r"\bSepa\b", "seepa"), (r"\bvisitCard\b", "visit card"), (r"\bvisitSepa\b", "visit seepa"),
           (r"\bvisitWallet\b", "visit wallet"), (r"\bvisitVoucher\b", "visit voucher"), (r"\bASM's\b", "A S M's"),
           (r"\bClassVisitor\b", "class visitor")]

KIND_C = [BLUE_M, TEAL_M, PURPLE_M, GREEN_M]
KINDS = ["Card", "Sepa", "Wallet", "Voucher"]
VNAME = ["visitCard", "visitSepa", "visitWallet", "visitVoucher"]
JOBS = ["fee", "export", "report"]
JOB_C, BAD_C, SEAL_C = GOLD_M, RED_M, YELLOW_M

COLS = [-0.85, 1.5, 3.85]
ROWS = [1.15, 0.15, -0.85, -1.85]
CW, CH = 2.1, 0.72
CHIP_X, ACC_X, HEAD_Y = -5.0, -3.15, 2.05

N = {
    "p1": "A payment service has three kinds of instruction: card, SEPA transfer and wallet payout. They almost never change.",
    "p2": "But new jobs for them keep coming: a fee, a bank export. Each job needs its own code for each kind.",
    "p3": "So picture a grid: one row per kind, one column per job. Where should the cells live?",
    "r1": "The usual answer is by row: each class holds its own fee and export methods.",
    "r2": "Then someone asks for a report. A new column means editing all three classes.",
    "v1": "A visitor stores the grid by column. Each job is one class, with one method per kind, behind one visitor interface.",
    "v2": "A new report is one new class, and the instruction classes stay put. Each just needs one small method: accept.",
    "q1": "Your code holds a plain Instruction of unknown kind. One Java call can only choose by the class of the object it's called on. "
          "So how do you reach the right cell?",
    "d2": "Hop one: call accept on the instruction. It's a wallet payout, so Wallet's accept runs. That picks the row.",
    "d3": "Hop two: it calls visitWallet on the visitor, whose class picks the column. Fee visitor, fee cell. Export visitor, the next one.",
    "d4": "That's double dispatch: accept picks the kind, visit picks the job.",
    "n1": "The catch is a new row. A voucher needs an accept, and every visitor ever written needs a visitVoucher.",
    "n2": "That trade is the expression problem. Methods in the classes make kinds cheap to add. A visitor makes jobs cheap.",
    "s1": "Today a sealed interface gives you the visitor's side with less code. It lists all three kinds, so the compiler knows every row.",
    "s2": "Each job is one function with a switch. The switch checks the object's class itself. One hop, no accept, no visitor interface.",
    "s3": "Add a voucher, and every switch without a voucher case stops compiling, each one listed.",
    "k1": "In Java that's a switch, in Kotlin a when, with no default branch.",
    "r": "The rule: to add jobs to a closed set of types, write one function per job that switches over a sealed type.",
    "c": "Quick check. A new job every month, a new kind once a year. Should rows or columns be cheap to add?",
    "a": "Columns. So a visitor, or today, a sealed switch.",
}
PAUSE = {"p3": 1.0, "q1": 1.8, "c": 2.0}


def code_block(lines, size=24, color=WHITE):
    """Mono lines stacked, left aligned, keeping leading spaces (Text drops them)."""
    cw = M("0" * 20, size).width / 20
    ms = []
    for ln in lines:
        txt, col = (ln if isinstance(ln, tuple) else (ln, color))
        n = len(txt) - len(txt.lstrip(" "))
        ms.append((M(txt.strip(), size, col), n))
    g = VGroup(*[m for m, _ in ms]).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
    for m, n in ms:
        m.shift(RIGHT * n * cw)
    return g


def cell(r, c, text, color, dashed=False):
    rect = Rectangle(width=CW, height=CH, stroke_color=GREY_D if not dashed else BAD_C, stroke_width=2)
    rect.set_fill("#0E0E0E", 1)
    if dashed:
        rect = DashedVMobject(rect, num_dashes=30)
    g = VGroup(rect, M(text, 22, color))
    g.move_to([COLS[c], ROWS[r], 0])
    g[1].move_to(g[0])
    return g


def row_box(r, ncols, color):
    left, right = CHIP_X - 0.95, COLS[ncols - 1] + CW / 2 + 0.14
    b = RoundedRectangle(corner_radius=0.12, width=right - left, height=0.9, stroke_color=color, stroke_width=3)
    return b.move_to([(left + right) / 2, ROWS[r], 0])


def col_box(c, nrows, color=JOB_C):
    top, bottom = HEAD_Y + 0.42, ROWS[nrows - 1] - 0.47
    b = RoundedRectangle(corner_radius=0.12, width=CW + 0.18, height=top - bottom, stroke_color=color, stroke_width=3)
    return b.move_to([COLS[c], (top + bottom) / 2, 0])


class Pat10Visitor(VoiceScene):
    """pat-10 s0: Visitor stores the type-by-operation grid by column; double dispatch is two hops; a sealed switch does it in one."""

    def say(self, key, plan=(), after=0.25):
        """Speak N[key]; plan is a list of (sentence index, [animations] or a function returning them, run_time)."""
        text = N[key]
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
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))

    def construct(self):
        self.title_card("Visitor: new jobs for a fixed set of types", "double dispatch, and the sealed switch that replaces it")

        # --- the problem: three kinds that never change, jobs that keep coming
        kinds = [chip(k, c, 28).move_to([CHIP_X, y, 0]) for k, c, y in zip(KINDS, KIND_C, ROWS)]
        heads = [chip(j, JOB_C, 26).move_to([x, HEAD_Y, 0]) for j, x in zip(JOBS, COLS)]
        self.say("p1", [(0, [LaggedStart(*[FadeIn(k, shift=RIGHT * 0.2) for k in kinds[:3]], lag_ratio=0.35)], 1.6)])

        cells = {}
        for r in range(3):
            for c in range(3):
                cells[r, c] = cell(r, c, JOBS[c] + "()", KIND_C[r])
        self.say("p2", [(0, [FadeIn(heads[0], shift=DOWN * 0.15)], 0.6), (0, [FadeIn(heads[1], shift=DOWN * 0.15)], 0.6),
                        (1, [LaggedStart(*[FadeIn(cells[r, c]) for r in range(3) for c in range(2)], lag_ratio=0.15)], 1.6)])
        grid_t = VGroup(T("rows: kinds", 24, GREY_B), T("columns: jobs", 24, GREY_B)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        grid_t.move_to([5.1, 0.65, 0])
        where = T("Where should the cells live?", 30, WHITE).move_to([0.6, -2.3, 0])
        self.say("p3", [(0, [FadeIn(grid_t[0]), Indicate(VGroup(*kinds[:3]), color=WHITE, scale_factor=1.05)], 0.9),
                        (0, [FadeIn(grid_t[1]), Indicate(VGroup(heads[0], heads[1]), color=WHITE, scale_factor=1.05)], 0.9),
                        (1, [FadeIn(where, shift=UP * 0.1)], 0.6)])

        # --- by row: methods in each class
        rboxes = [row_box(r, 2, KIND_C[r]) for r in range(3)]
        cls_t = T("each class holds its row", 24, GREY_B).move_to([5.1, 0.65, 0])
        self.say("r1", [(0, [FadeOut(where), FadeOut(grid_t)], 0.4),
                        (0, [LaggedStart(*[Create(b) for b in rboxes], lag_ratio=0.3), FadeIn(cls_t)], 1.4),
                        (0, [Indicate(VGroup(cells[0, 0][1], cells[0, 1][1]), color=BLUE_M, scale_factor=1.15)], 0.9)])
        wide = [row_box(r, 3, KIND_C[r]) for r in range(3)]
        edited = T("one new job: 3 classes edited", 28, BAD_C).move_to([0.6, -2.2, 0])
        self.say("r2", [(0, [FadeOut(cls_t), FadeIn(heads[2], shift=DOWN * 0.15)], 0.6),
                        (1, [*[FadeIn(cells[r, 2]) for r in range(3)]], 0.6),
                        (1, [*[Transform(rboxes[r], wide[r]) for r in range(3)],
                             *[ShowPassingFlash(wide[r].copy().set_stroke(BAD_C, 7), time_width=0.6) for r in range(3)]], 1.2),
                        (1, [FadeIn(edited, shift=UP * 0.1)], 0.6)])

        # --- by column: the visitor
        vlabels = [M(n, 22, JOB_C).move_to([x, HEAD_Y + 0.72, 0]) for n, x in zip(["FeeVisitor", "ExportVisitor", "ReportVisitor"], COLS)]
        cboxes = [col_box(c, 3) for c in range(3)]
        report = VGroup(cboxes[2], vlabels[2], heads[2], *[cells[r, 2] for r in range(3)])
        self.say("v1", [(0, [FadeOut(edited), *[FadeOut(b) for b in rboxes], FadeOut(heads[2]), *[FadeOut(cells[r, 2]) for r in range(3)]], 0.7),
                        (0, [*[Create(cboxes[c]) for c in range(2)], *[FadeIn(vlabels[c]) for c in range(2)]], 0.9),
                        (1, [*[Transform(cells[r, c][1], M(VNAME[r], 22, JOB_C).move_to(cells[r, c][0])) for r in range(3) for c in range(2)]], 1.0)])
        for r in range(3):
            cells[r, 2][1].become(M(VNAME[r], 22, JOB_C).move_to(cells[r, 2][0]))
        same = T("Card, Sepa, Wallet: unchanged", 26, GREEN_M).move_to([0.6, -2.2, 0])
        accs = [chip("accept", KIND_C[r], 22, mono=True).move_to([ACC_X, ROWS[r], 0]) for r in range(3)]
        self.say("v2", [(0, [FadeIn(report, shift=LEFT * 0.8)], 1.1), (0, [FadeIn(same)], 0.5),
                        (1, [LaggedStart(*[FadeIn(a, shift=RIGHT * 0.15) for a in accs], lag_ratio=0.3)], 1.1)])

        # --- double dispatch: two hops
        code = M("i.accept(feeVisitor)", 24).move_to([ACC_X, -2.75, 0])
        which = T("which row?", 28, SEAL_C).move_to([ACC_X, -1.85, 0])
        rule1 = T("one call chooses by one object's class", 24, GREY_B).move_to([2.2, -2.75, 0])
        rule1.align_to(np.array([-0.6, 0, 0]), LEFT)
        self.say("q1", [(0, [FadeOut(same), FadeIn(code, shift=UP * 0.1)], 0.7), (1, [FadeIn(rule1)], 0.6), (2, [FadeIn(which)], 0.6)])
        hop1 = Arrow([ACC_X, -2.42, 0], [ACC_X, ROWS[2] - 0.33, 0], buff=0.05, stroke_width=4, color=WHITE, max_tip_length_to_length_ratio=0.2)
        n1 = M("1", 26).next_to(hop1, LEFT, buff=0.15)
        h1t = fit(T("1. accept: the instruction's class picks the row", 24, PURPLE_M), 7.0).move_to([2.2, -2.45, 0])
        h1t.align_to(np.array([-0.6, 0, 0]), LEFT)
        self.say("d2", [(0, [FadeOut(rule1), FadeOut(which)], 0.4), (0, [GrowArrow(hop1), FadeIn(n1)], 0.8),
                        (1, [Indicate(accs[2][1], color=PURPLE_M, scale_factor=1.2)], 0.8), (2, [FadeIn(h1t)], 0.6)])
        hop2 = Arrow([ACC_X + 0.66, ROWS[2], 0], [COLS[0] - CW / 2, ROWS[2], 0], buff=0.04, stroke_width=4, color=JOB_C,
                     max_tip_length_to_length_ratio=0.3)
        n2 = M("2", 26, JOB_C).next_to(hop2, UP, buff=0.1)
        h2t = fit(T("2. visitWallet: the visitor's class picks the column", 24, JOB_C), 7.0).next_to(h1t, DOWN, buff=0.22, aligned_edge=LEFT)
        hop2b = CurvedArrow([ACC_X + 0.5, ROWS[2] - 0.38, 0], [COLS[1] - 0.4, ROWS[2] - 0.38, 0], angle=PI / 4, color=JOB_C,
                            stroke_width=4, tip_length=0.2)
        code2 = M("i.accept(exportVisitor)", 24).move_to(code)
        hl0 = cells[2, 0][0].copy().set_stroke(JOB_C, 5).set_fill(opacity=0)
        hl1 = cells[2, 1][0].copy().set_stroke(JOB_C, 5).set_fill(opacity=0)
        self.say("d3", [(0, [GrowArrow(hop2), FadeIn(n2), FadeIn(h2t)], 0.9),
                        (1, [Create(hl0)], 0.6),
                        (2, [FadeOut(hop2), FadeOut(n2), FadeOut(hl0), Transform(code, code2)], 0.5),
                        (2, [Create(hop2b)], 0.8), (2, [Create(hl1)], 0.4)])
        dd = T("double dispatch", 30, WHITE).move_to([2.4, -1.85, 0])
        self.say("d4", [(0, [FadeIn(dd, shift=UP * 0.1)], 0.6), (0, [Indicate(h1t, color=WHITE, scale_factor=1.03)], 0.8),
                        (0, [Indicate(h2t, color=WHITE, scale_factor=1.03)], 0.8)])
        self.play(FadeOut(VGroup(hop1, n1, hop2b, hl1, code, h1t, h2t, dd)), run_time=0.6)

        # --- the catch: a new row
        vrow = kinds[3]
        vacc = VGroup(DashedVMobject(accs[0][0].copy().set_stroke(BAD_C).move_to([ACC_X, ROWS[3], 0]), num_dashes=24),
                      M("accept", 22, BAD_C).move_to([ACC_X, ROWS[3], 0]))
        vcells = [cell(3, c, "visitVoucher", BAD_C, dashed=True) for c in range(3)]
        tall = [col_box(c, 4) for c in range(3)]
        iface = T("+ visitVoucher on the interface and on every visitor", 26, BAD_C).move_to([0.2, -2.75, 0])
        self.say("n1", [(0, [FadeIn(vrow, shift=RIGHT * 0.2)], 0.6),
                        (1, [FadeIn(vacc)], 0.5), (1, [FadeIn(iface, shift=UP * 0.1)], 0.6),
                        (1, [*[Transform(cboxes[c], tall[c]) for c in range(3)], *[FadeIn(v) for v in vcells],
                             *[ShowPassingFlash(tall[c].copy().set_stroke(BAD_C, 7), time_width=0.6) for c in range(3)]], 1.2)])
        newv = VGroup(vrow, vacc, *vcells, iface)
        tbl = VGroup(
            T("methods in each class: new kind cheap, new job costly", 26),
            T("visitor: new job cheap, new kind costly", 26, JOB_C),
        ).arrange(DOWN, buff=0.18).move_to([0, -2.85, 0])
        ep = T("the expression problem", 30, WHITE).move_to([0.2, -2.0, 0])
        self.say("n2", [(0, [FadeOut(newv), *[Transform(cboxes[c], col_box(c, 3)) for c in range(3)]], 0.7),
                        (0, [FadeIn(ep, shift=UP * 0.1)], 0.6), (1, [FadeIn(tbl[0])], 0.6), (2, [FadeIn(tbl[1])], 0.6),
                        (2, [Indicate(VGroup(*heads), color=WHITE, scale_factor=1.08)], 0.9)])

        # --- today: sealed interface + switch
        seal = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=2.2, height=3.25, stroke_color=SEAL_C, stroke_width=3), num_dashes=44)
        seal.move_to([CHIP_X, (ROWS[0] + ROWS[2]) / 2, 0])
        seal_t = T("sealed: the full list", 24, SEAL_C).next_to(seal, UP, buff=0.12)
        self.say("s1", [(0, [FadeOut(ep), FadeOut(tbl)], 0.5), (1, [Create(seal), FadeIn(seal_t)], 1.0),
                        (1, [Indicate(VGroup(*kinds[:3]), color=SEAL_C, scale_factor=1.06)], 0.9)])
        flabels = [M(n, 22, JOB_C).move_to(vlabels[c]) for c, n in enumerate(["fee(i)", "export(i)", "report(i)"])]
        code3 = M("fee(i)", 24).move_to([COLS[0], -2.75, 0])
        hop = Arrow([COLS[0], -2.42, 0], [COLS[0], ROWS[2] - CH / 2, 0], buff=0.05, stroke_width=4, color=JOB_C, max_tip_length_to_length_ratio=0.2)
        one = T("one hop: the switch checks the class itself", 24, JOB_C).next_to(hop, RIGHT, buff=0.3)
        hl2 = cells[2, 0][0].copy().set_stroke(JOB_C, 5).set_fill(opacity=0)
        gone = [Line(a.get_corner(DL), a.get_corner(UR), color=BAD_C, stroke_width=4) for a in accs]
        self.say("s2", [(0, [*[Transform(vlabels[c], flabels[c]) for c in range(3)],
                             *[Transform(cells[r, c][1], M("case " + KINDS[r], 22, JOB_C).move_to(cells[r, c][0]))
                               for r in range(3) for c in range(3)]], 1.2),
                        (1, [FadeIn(code3, shift=UP * 0.1)], 0.5), (1, [GrowArrow(hop)], 0.6), (1, [Create(hl2), FadeIn(one)], 0.6),
                        (2, [*[Create(g) for g in gone]], 0.6), (2, [FadeOut(VGroup(*accs, *gone))], 0.6)])
        seal_big = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=2.2, height=4.25, stroke_color=SEAL_C, stroke_width=3), num_dashes=56)
        seal_big.move_to([CHIP_X, (ROWS[0] + ROWS[3]) / 2, 0])
        miss = [cell(3, c, "no case", BAD_C, dashed=True) for c in range(3)]
        err = T("3 switches, 3 compile errors, each one listed", 26, BAD_C).move_to([0.6, -2.75, 0])
        self.say("s3", [(0, [FadeOut(VGroup(code3, hop, one, hl2))], 0.4),
                        (0, [Transform(seal, seal_big), FadeIn(vrow, shift=RIGHT * 0.2)], 0.8),
                        (0, [*[Transform(cboxes[c], col_box(c, 4)) for c in range(3)], *[FadeIn(m) for m in miss]], 0.8),
                        (0, [FadeIn(err, shift=UP * 0.1), *[ShowPassingFlash(col_box(c, 4).set_stroke(BAD_C, 7), time_width=0.6) for c in range(3)]], 1.0)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # --- the code
        jt = T("Java", 24, GREY_B)
        jh = code_block([("sealed interface Instruction", SEAL_C), ("    permits Card, Sepa, Wallet {}", SEAL_C)])
        jb = code_block(["String export(Instruction i) {", "  return switch (i) {", '    case Card c   -> "CARD";',
                         '    case Sepa s   -> "SEPA";', '    case Wallet w -> "WALLET";', "  };", "}"])
        jl = VGroup(jt, jh, jb).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        jb.shift(DOWN * 0.3)
        kh = VGroup(T("Kotlin", 24, GREY_B), code_block([("sealed interface Instruction", SEAL_C)])).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        kb = code_block(["fun export(i: Instruction) = when (i) {", '  is Card   -> "CARD"', '  is Sepa   -> "SEPA"',
                         '  is Wallet -> "WALLET"', "}"])
        kh.next_to(jl, RIGHT, buff=0.8).align_to(jl, UP)
        kb.align_to(kh, LEFT).align_to(jb, UP)
        pair = VGroup(jl, kh, kb)
        fit(pair, 12.4).move_to([0, 0.55, 0])
        nodef = T("no default branch: the compiler checks the list", 26, GREY_B).move_to([0, -3.0, 0])
        keep = VGroup(T("keep a real visitor when other modules can add types,", 26),
                      T("or a library hands you one: ASM's ClassVisitor, javac's Tree API", 26)).arrange(DOWN, buff=0.12).move_to([0, -2.9, 0])
        fit(keep, 12.4)
        self.say("k1", [(0, [FadeIn(pair, shift=UP * 0.1)], 1.0), (0, [FadeIn(nodef)], 0.6)])
        self.play(FadeOut(nodef), FadeIn(keep), run_time=0.8)
        self.wait(1.8)
        self.play(FadeOut(VGroup(pair, keep)), run_time=0.5)

        # --- rule and check
        rule = VGroup(T("To add jobs to a closed set of types,", 34),
                      T("write one function per job that switches over a sealed type.", 34, JOB_C)).arrange(DOWN, buff=0.22).move_to([0, 1.5, 0])
        fit(rule, 12.4)
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (0, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        chk = VGroup(T("Check: a new job every month, a new kind once a year.", 28),
                     T("Should rows or columns be cheap to add?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.9, 0])
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("Columns: a visitor, or today a sealed switch.", 28, JOB_C).move_to([0, -2.4, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.6)
