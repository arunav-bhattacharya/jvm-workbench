from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bAArch64\b", "A arch sixty-four"), (r"\bx86\b", "x eighty-six"),
              (r"\bjcstress\b", "J C stress"), (r"\bBIN\b", "bin"), (r"\bbinTable\b", "bin table"),
              (r"\bDCL\b", "D C L")]


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
            if callable(anims):
                anims = anims()
            if rt is None:                       # stretch this step to the end of the line
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def padlock(color=GREY_B, s=1.0):
    body = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.32, stroke_color=color, stroke_width=3)
    body.set_fill(dark(color, 0.3), 1)
    shackle = Arc(radius=0.14, start_angle=0, angle=PI, stroke_color=color, stroke_width=3).next_to(body, UP, buff=0)
    return VGroup(shackle, body).scale(s)


A_COL, B_COL, REF, OK_C, BAD, JVM = BLUE_M, TEAL_M, YELLOW_M, GREEN_M, RED_M, PURPLE_M


class Jmm05Dcl(VoiceScene):
    """jmm-05, section 0: double-checked locking without volatile lets a reader on the lock-free fast path see the
    reference before the constructor's write (a half-built table); volatile adds the release/acquire edge; the holder
    idiom lets class initialization do the locking."""

    def construct(self):
        self.title_card("Double-checked locking", "how a lazy singleton hands out a half-built object")

        # =============== the shared memory: one static field, later one object ===============
        fld = RoundedRectangle(corner_radius=0.1, width=2.9, height=0.75, stroke_color=REF, stroke_width=3)
        fld.set_fill(dark(REF, 0.1), 1).move_to([0, 2.2, 0])
        fld_t = M("table: null", 24, REF).move_to(fld)
        fld_lab = T("static field", 22, GREY_B).next_to(fld, UP, buff=0.12)

        lk = padlock(GREY_B, 1.1).next_to(fld, LEFT, buff=0.35)
        lk_t = T("every call takes the lock", 24, GREY_B).next_to(fld, DOWN, buff=0.35)
        self.beat("A BIN table takes 50 ms to load, so you build it on first use.",
                  FadeIn(fld), FadeIn(fld_t), FadeIn(fld_lab), run_time=1.2)
        self.beat("A synchronized getter is safe, but then every call takes the lock, forever.",
                  FadeIn(lk, scale=0.7), FadeIn(lk_t), run_time=1.2)
        self.play(FadeOut(lk), FadeOut(lk_t), run_time=0.5)

        # =============== thread A's steps, with the lock region ===============
        R = [2.2, 1.45, 0.75, 0.05, -0.65, -1.35]
        AX, BX = -5.95, 2.45
        a_txt = ["1. check: table is null", "takes the lock", "2. check again: still null",
                 "allocate: ranges = null", "constructor writes ranges", "publish: write table"]
        rows = [T(s_, 24, GREY_A if i == 1 else WHITE) for i, s_ in enumerate(a_txt)]
        for r_, y in zip(rows, R):
            r_.scale(min(1, 3.6 / r_.width)).move_to([AX, y, 0], aligned_edge=LEFT)
        lockbox = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=4.2, height=3.7, stroke_color=GREY_B, stroke_width=2),
                                 num_dashes=70).move_to([-4.2, -0.05, 0])
        lk2 = padlock(GREY_B, 0.8).move_to([-2.45, 1.75, 0])
        a_head = T("Thread A", 30, A_COL).move_to([-4.2, 3.05, 0])
        b_head = T("Thread B", 30, B_COL).move_to([4.3, 3.05, 0])
        ptr_a = Triangle(color=A_COL, fill_opacity=1, stroke_width=0).scale(0.11).rotate(-PI / 2).move_to([AX - 0.22, R[0], 0])
        self.beat("Double-checked locking skips the lock once the table exists. Check without the lock. "
                  "If it is null, lock, check again, and build.",
                  FadeIn(a_head), FadeIn(rows[0]), FadeIn(lockbox), FadeIn(lk2), FadeIn(VGroup(*rows[1:])), run_time=2.4)

        # ---- A runs: check, lock, check, allocate ----
        obj = RoundedRectangle(corner_radius=0.12, width=3.2, height=1.45, stroke_color=GOLD_M, stroke_width=3)
        obj.set_fill(dark(GOLD_M, 0.08), 1).move_to([0, -0.15, 0])
        obj_t = T("a BinTable", 24, GOLD_M).move_to(obj.get_top() + DOWN * 0.32)
        rng = M("ranges = null", 24, GREY_A).move_to(obj.get_center() + DOWN * 0.22)

        def point(p, i, x=AX):
            return p.animate.move_to([x - 0.22, R[i], 0])
        seq(self, "Thread A finds null, takes the lock, checks again, and allocates the table, with ranges still null. "
                  "In the code, the constructor fills ranges, then the reference goes into table.",
            ([FadeIn(ptr_a)], 0.3), 0.7, ([point(ptr_a, 1), lk2.animate.set_color(A_COL), lockbox.animate.set_stroke(A_COL)], 0.6),
            0.5, ([point(ptr_a, 2)], 0.5), 0.6, ([point(ptr_a, 3), FadeIn(obj), FadeIn(obj_t), FadeIn(rng)], 0.8), 2.4,
            ([Indicate(rows[4], color=GOLD_M, scale_factor=1.06)], 0.9), 0.3, ([Indicate(rows[5], color=REF, scale_factor=1.06)], 0.9))

        # ---- the reorder ----
        swap_l = T("the JIT and the CPU may swap these", 22, BAD).move_to([-4.2, -2.15, 0])
        y4, y5 = R[4], R[5]
        seq(self, "But B will read table outside the lock, with a plain read. That read has no happens-before edge "
                  "to anything A wrote. So the JIT and the CPU may let the reference out first.",
            4.6,
            ([rows[4].animate(path_arc=-PI * 0.6).move_to([AX, y5, 0], aligned_edge=LEFT).set_color(BAD),
              rows[5].animate(path_arc=-PI * 0.6).move_to([AX, y4, 0], aligned_edge=LEFT).set_color(BAD), FadeIn(swap_l)], 1.2))
        # now rows[5] (publish) is at y4 and rows[4] (constructor) at y5
        ref_dot = Dot(radius=0.09, color=REF).move_to(fld.get_center() + RIGHT * 0.6)
        fld_t2 = M("table:", 24, REF).move_to(fld.get_center() + LEFT * 0.35)
        ref_ar = Arrow(ref_dot.get_center(), obj.get_top() + RIGHT * 0.6, buff=0.05, stroke_width=3, color=REF,
                       max_tip_length_to_length_ratio=0.2)
        ptr_b = Triangle(color=B_COL, fill_opacity=1, stroke_width=0).scale(0.11).rotate(-PI / 2).move_to([BX - 0.22, R[0], 0])
        b_txt = ["1. check: table not null", "skips the lock", "reads table.ranges"]
        brows = [T(s_, 24) for s_ in b_txt]
        for r_, y in zip(brows, R):
            r_.scale(min(1, 3.7 / r_.width)).move_to([BX, y, 0], aligned_edge=LEFT)
        seq(self, "A writes table. Right then, thread B calls binTable. table is not null, so B skips the lock, "
                  "and reads ranges. What does it see?",
            ([point(ptr_a, 4), Transform(fld_t, fld_t2), FadeIn(ref_dot), GrowArrow(ref_ar)], 0.8), 0.8,
            ([FadeIn(b_head), FadeIn(ptr_b), FadeIn(brows[0])], 0.6), 1.0,
            ([point(ptr_b, 1, BX), FadeIn(brows[1])], 0.5), 0.8, ([point(ptr_b, 2, BX), FadeIn(brows[2])], 0.5))
        self.wait(2.0)
        half = T("null: a half-built table", 26, BAD).move_to([BX, R[3], 0], aligned_edge=LEFT)
        rd = Arrow(brows[2].get_left() + LEFT * 0.1, rng.get_right() + RIGHT * 0.05, buff=0.05, stroke_width=3, color=B_COL,
                   max_tip_length_to_length_ratio=0.15)
        rng_full = M("ranges = 40 MB", 24, GOLD_M).move_to(rng)
        seq(self, "null. A table that is not null, and still empty. A's write lands a moment later, too late for B.",
            ([GrowArrow(rd), rng.animate.set_color(BAD)], 0.6), ([FadeIn(half, shift=RIGHT * 0.15)], 0.5), 2.6,
            ([point(ptr_a, 5), Transform(rng, rng_full)], 0.8))
        meas = T("jcstress on AArch64: about 1.8 million half-built results in 2.3 billion samples", 24, GREY_A).move_to([0, -2.85, 0])
        meas.scale(min(1, 12.6 / meas.width))
        self.beat("A jcstress test on AArch64 saw this 1.8 million times in 2.3 billion samples. "
                  "On x86 it rarely shows, so it seems to work.", FadeIn(meas), run_time=1.0)

        # =============== the fix: volatile ===============
        vol = T("static volatile field", 22, OK_C).move_to(fld_lab)
        fld_t0 = M("table: null", 24, REF).move_to(fld)
        rng0 = M("ranges = null", 24, GREY_A).move_to(rng)
        self.play(FadeOut(VGroup(meas, swap_l, half, rd, ref_dot, ref_ar, obj, obj_t, rng, ptr_b, *brows, ptr_a)),
                  Transform(fld_t, fld_t0),
                  rows[4].animate.move_to([AX, y4, 0], aligned_edge=LEFT).set_color(WHITE),
                  rows[5].animate.move_to([AX, y5, 0], aligned_edge=LEFT).set_color(WHITE),
                  lk2.animate.set_color(GREY_B), lockbox.animate.set_stroke(GREY_B), run_time=0.9)
        rel_t = T("release", 24, OK_C).move_to([-1.55, -1.75, 0])
        acq_t = T("acquire", 22, OK_C).move_to([1.95, 2.5, 0])
        seq(self, "The fix is one word: make table volatile. Now writing table is a release: "
                  "everything A wrote before it is visible first.",
            ([Transform(fld_lab, vol), fld.animate.set_stroke(OK_C)], 0.8), 2.0,
            ([FadeIn(rel_t, scale=0.7)], 0.8))
        obj = RoundedRectangle(corner_radius=0.12, width=3.2, height=1.45, stroke_color=GOLD_M, stroke_width=3)
        obj.set_fill(dark(GOLD_M, 0.08), 1).move_to([0, -0.15, 0])
        obj_t = T("a BinTable", 24, GOLD_M).move_to(obj.get_top() + DOWN * 0.32)
        rng = M("ranges = null", 24, GREY_A).move_to(obj.get_center() + DOWN * 0.22)
        rng_full = M("ranges = 40 MB", 24, GOLD_M).move_to(rng)
        ref_dot = Dot(radius=0.09, color=REF).move_to(fld.get_center() + RIGHT * 0.6)
        fld_t2 = M("table:", 24, REF).move_to(fld.get_center() + LEFT * 0.35)
        ref_ar = Arrow(ref_dot.get_center(), obj.get_top() + RIGHT * 0.6, buff=0.05, stroke_width=3, color=REF,
                       max_tip_length_to_length_ratio=0.2)
        ptr_a = Triangle(color=A_COL, fill_opacity=1, stroke_width=0).scale(0.11).rotate(-PI / 2).move_to([AX - 0.22, R[3], 0])
        ptr_b = Triangle(color=B_COL, fill_opacity=1, stroke_width=0).scale(0.11).rotate(-PI / 2).move_to([BX - 0.22, R[0], 0])
        brows = [T(s_, 24) for s_ in b_txt]
        for r_, y in zip(brows, R):
            r_.scale(min(1, 3.7 / r_.width)).move_to([BX, y, 0], aligned_edge=LEFT)
        e1 = Arrow([-2.05, R[5], 0], fld.get_left() + LEFT * 0.05 + DOWN * 0.1, buff=0.05, stroke_width=3, color=OK_C,
                   max_tip_length_to_length_ratio=0.08)
        e2 = Arrow(fld.get_right() + RIGHT * 0.05, [BX - 0.4, R[0], 0], buff=0.05, stroke_width=3, color=OK_C,
                   max_tip_length_to_length_ratio=0.15)
        good = T("sees the whole table", 26, OK_C).move_to([BX, R[3], 0], aligned_edge=LEFT)
        seq(self, "And B's volatile read is an acquire: if it sees the reference, it sees ranges too.",
            ([FadeIn(b_head)], 0.6),
            ([FadeIn(ptr_a), FadeIn(obj), FadeIn(obj_t), FadeIn(rng)], 0.5),
            ([ptr_a.animate.move_to([AX - 0.22, R[4], 0]), Transform(rng, rng_full)], 0.6),
            ([ptr_a.animate.move_to([AX - 0.22, R[5], 0]), Transform(fld_t, fld_t2), FadeIn(ref_dot), GrowArrow(ref_ar), GrowArrow(e1)], 0.7),
            ([GrowArrow(e2), FadeIn(acq_t), FadeIn(ptr_b), FadeIn(brows[0])], 0.6),
            ([ptr_b.animate.move_to([BX - 0.22, R[2], 0]), FadeIn(brows[1]), FadeIn(brows[2])], 0.5),
            ([FadeIn(good, shift=RIGHT * 0.15)], 0.5))
        self.play(*[FadeOut(m) for m in list(self.mobjects)], run_time=0.8)

        # =============== the holder idiom: class initialization does the locking ===============
        cls = RoundedRectangle(corner_radius=0.15, width=5.4, height=1.5, stroke_color=JVM, stroke_width=3)
        cls.set_fill(dark(JVM, 0.1), 1).move_to([0, 1.3, 0])
        cls_t = M("class Holder", 24, JVM).move_to(cls.get_corner(UL) + np.array([1.2, -0.3, 0]))
        cls_f = M("static final BinTable INSTANCE", 22).move_to(cls.get_center() + DOWN * 0.2)
        state = T("not initialized", 24, GREY_B).next_to(cls, DOWN, buff=0.2)
        ca = chip("A", A_COL, size=28).move_to([-5.4, 1.3, 0])
        cb = chip("B", B_COL, size=28).move_to([5.4, 1.3, 0])
        jl = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=6.2, height=2.7, stroke_color=JVM, stroke_width=2.5),
                            num_dashes=80).move_to([0, 1.0, 0])
        jl_t = T("the JVM's class init lock", 24, JVM).next_to(jl, UP, buff=0.12)
        self.beat("For a static field there is a simpler way. Let the JVM do the locking.",
                  FadeIn(cls), FadeIn(cls_t), FadeIn(cls_f), FadeIn(state), FadeIn(ca), FadeIn(cb), run_time=1.4)
        obj = RoundedRectangle(corner_radius=0.12, width=3.2, height=1.2, stroke_color=GOLD_M, stroke_width=3)
        obj.set_fill(dark(GOLD_M, 0.08), 1).move_to([0, -1.55, 0])
        obj_t = T("a BinTable", 24, GOLD_M).move_to(obj.get_top() + DOWN * 0.3)
        rng = M("ranges = 40 MB", 24, GOLD_M).move_to(obj.get_center() + DOWN * 0.18)
        st2 = T("initializing, by A", 24, A_COL).move_to(state)
        inst = Arrow(cls.get_bottom() + RIGHT * 1.6, obj.get_top() + RIGHT * 1.0, buff=0.05, stroke_width=3, color=REF,
                     max_tip_length_to_length_ratio=0.25)
        wait_b = T("waits", 24, B_COL).move_to([3.55, 0.75, 0])
        seq(self, "The JVM initializes a class right before its first use, once, under its own lock. "
                  "A's first call touches Holder, so the JVM builds the table right then. B has to wait.",
            ([FadeIn(jl), FadeIn(jl_t)], 0.8), 2.6,
            ([ca.animate.move_to([-3.55, 1.3, 0]), Transform(state, st2)], 0.8), 0.4,
            ([FadeIn(obj), FadeIn(obj_t), FadeIn(rng), GrowArrow(inst)], 0.9), 0.8,
            ([cb.animate.move_to([3.55, 1.3, 0])], 0.6), ([FadeIn(wait_b)], 0.4))
        st3 = T("initialized", 24, OK_C).move_to(state)
        rb = Arrow(cb.get_bottom() + DOWN * 0.05, obj.get_right() + RIGHT * 0.05, buff=0.05, stroke_width=3, color=B_COL,
                   max_tip_length_to_length_ratio=0.15)
        got = T("sees the whole table", 24, OK_C).move_to([4.6, -1.0, 0])
        seq(self, "Then every thread that uses the class sees what the initializer wrote. "
                  "Your code needs no volatile and no lock.",
            ([Transform(state, st3), FadeOut(jl), FadeOut(jl_t), FadeOut(wait_b)], 0.8), 0.6,
            ([GrowArrow(rb), FadeIn(got)], 0.8))
        self.play(*[FadeOut(m) for m in list(self.mobjects)], run_time=0.8)

        # =============== code, rule, check ===============
        jc = code(["private static final class Holder {",
                   "    static final BinTable INSTANCE = new BinTable();",
                   "}",
                   "static BinTable binTable() { return Holder.INSTANCE; }"], 24)
        kc = code(["private object Holder {",
                   "    val INSTANCE = BinTable()",
                   "}",
                   "fun binTable(): BinTable = Holder.INSTANCE"], 24)
        cg = VGroup(titled("Java", jc), titled("Kotlin: an object is built on first access", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.2, 0])
        self.beat("In Java it is a nested class. In Kotlin, an object, built on first access.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(cg), run_time=0.6)
        rule = T("A thread that skips the lock needs its own edge to the writes.", 32).move_to([0, 2.2, 0])
        rule2 = T("volatile gives it one. So does class initialization.", 30, OK_C).move_to([0, 1.5, 0])
        VGroup(rule, rule2).scale(min(1, 12 / rule.width))
        self.beat("The rule. A thread that skips the lock needs its own edge to the writes. "
                  "A volatile field gives it one, and so does class initialization.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        chk = T("Thread B reads a non-null table without taking the lock.", 30).move_to([0, -0.1, 0])
        chk2 = T("Is it sure to see ranges with a plain field? With a volatile one?", 30).move_to([0, -0.7, 0])
        VGroup(chk, chk2).scale(min(1, 12 / chk2.width))
        self.beat("Check yourself. Thread B reads a non-null table without taking the lock. "
                  "Is it sure to see ranges with a plain field? With a volatile one?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("plain: no, it can see null.  volatile: yes, always.", 30, GOLD_M).move_to([0, -1.8, 0])
        self.beat("Plain: no, it can see null. Volatile: yes, always.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
