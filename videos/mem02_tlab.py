from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"266 KB", "266 kilobytes"), (r"500 MB", "500 megabyte"), (r"1 GB", "1 gigabyte"), (r"\bMB\b", "megabytes"),
           (r"32-byte", "32 byte"), (r"\bp\b", "P"), (r"zeroes", "zeros")]

T1, T2, T3 = BLUE_M, PURPLE_M, GOLD_M          # one colour per thread; thread 1 is the one we follow
EDEN_C, REG_C, ESC_C = GREEN_M, YELLOW_M, RED_M

N = {
    "s1": "Many threads create objects at the same time. All of them go into eden, one area of the heap that every thread shares.",
    "s2": "If each new took memory straight from eden, every thread would need this one pointer. One thread moves it. The others wait.",
    "q1": "How would you stop them fighting over it?",
    "s3": "Give each thread its own piece of eden. Now no thread needs a lock.",
    "s4": "That piece is a TLAB: a thread-local allocation buffer.",
    "s5": "To allocate, the thread checks that the object fits before the end. Then it adds the size to top, and stores the new top.",
    "s6": "A compare, an add and a store. The JIT puts them right into your compiled method.",
    "q2": "What happens when the next object doesn't fit?",
    "s7": "The thread takes a fresh TLAB from eden, with one atomic update. That happens once per TLAB, not once per object.",
    "s9": "And sometimes new allocates nothing. This loop builds a million Points, and only adds up their fields. "
          "In the interpreter, each one is a real object.",
    "q3": "Can anything outside the method ever see p?",
    "s10": "No. p never goes into a field or a collection, it's never returned, and it never goes to a call that C2 doesn't inline.",
    "s11": "C2, the JIT for hot methods, checks exactly this. That's escape analysis.",
    "s12": "Then it skips the object, and keeps x and y in registers. That's scalar replacement.",
    "s13": "Count the bytes of each call. The first rounds allocate megabytes, while the interpreter and C1 run the code. "
           "From round 4 or so, zero.",
    "s14": "With escape analysis off, every round allocates 32,000,000 bytes: a million 32-byte points.",
    "s15": "So never assert that code allocates nothing in a unit test.",
    "s16": "Java and Kotlin compile to the same new, so both behave the same.",
    "r": "The rule: new is a pointer bump in your own TLAB, and an object that never leaves a hot method may never be allocated.",
    "c": "Quick check. The loop adds each Point to a list. Does C2 remove the allocation?",
    "a": "No. The list is a way out.",
}
PAUSE = {"q1": 2.0, "q2": 1.8, "q3": 2.0, "c": 2.4}


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def cell(x0, x1, y, h, color, label=None, size=22, k=0.4, mono=True):
    """A filled block from x0 to x1: one object in memory."""
    r = Rectangle(width=x1 - x0, height=h, stroke_color=color, stroke_width=2).set_fill(shade(color, k), 1)
    r.move_to([(x0 + x1) / 2, y, 0])
    if not label:
        return VGroup(r)
    t = (M if mono else T)(label, size)
    fit(t, r.width - 0.12).move_to(r)
    return VGroup(r, t)


def pointer(x, y_top, label, color, size=26, length=0.75):
    a = Arrow([x, y_top - length, 0], [x, y_top, 0], buff=0, stroke_width=4, color=color,
              max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10)
    t = T(label, size, color).next_to(a, DOWN, buff=0.1)
    return VGroup(a, t)


def code_block(lines, size=24, color=GREY_A, ls=0.75):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


class Mem02Tlab(VoiceScene):
    """mem-02: each thread bumps a pointer in its own TLAB; C2's escape analysis can remove an object entirely."""

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
        self.title_card("Why new is cheap", "a pointer bump, or nothing at all")

        # --- the problem: many threads, one shared eden, one pointer
        EY, EH = -0.5, 1.0
        eden = Rectangle(width=12, height=EH, stroke_color=EDEN_C, stroke_width=3).set_fill(shade(EDEN_C, 0.06), 1).move_to([0, EY, 0])
        eden_t = T("eden: every thread shares it", 26, EDEN_C).next_to(eden, UP, buff=0.18).align_to(eden, RIGHT)
        used = VGroup(*[cell(a, b, EY, EH - 0.16, GREY_M, k=0.35) for a, b in [(-6, -5.55), (-5.55, -5.15), (-5.15, -4.7), (-4.7, -4.3)]])
        threads = VGroup(*[box(f"thread {i + 1}", c, w=2.4, h=0.8, size=28).move_to([x, 2.5, 0])
                           for i, (c, x) in enumerate([(T1, -4.2), (T2, 0), (T3, 4.2)])])
        px = -4.3
        shared = pointer(px, EY - EH / 2 - 0.05, "next free byte", WHITE)
        self.say("s1", [(0, [LaggedStart(*[FadeIn(t, shift=DOWN * 0.2) for t in threads], lag_ratio=0.3)], 1.2),
                        (1, [FadeIn(eden), FadeIn(used), FadeIn(eden_t)], 1.0)])

        cols = [T1, T2, T3]
        dots = [Dot(radius=0.13, color=c).move_to(threads[i].get_bottom() + DOWN * 0.2) for i, c in enumerate(cols)]
        slots = [np.array([px + 0.25 + 0.5 * k, 0.45, 0]) for k in range(3)]
        wait_t = T("the others wait", 26, ESC_C).move_to([px + 1.6, 1.15, 0])
        drops, ptr_now = [], px
        for k in range(3):
            drops.append(cell(px + 0.5 * k, px + 0.5 * (k + 1), EY, EH - 0.16, cols[k], k=0.55))

        def drop(k):
            return [ReplacementTransform(dots[k], drops[k]), shared.animate.shift(RIGHT * 0.5)]

        self.say("s2", [(0, [FadeIn(shared)], 0.6),
                        (0, [*[FadeIn(d) for d in dots]], 0.3),
                        (0, [*[dots[k].animate.move_to(slots[k]) for k in range(3)]], 1.3),
                        (1, lambda: drop(0), 0.6), (2, [FadeIn(wait_t)], 0.4), (2, lambda: drop(1), 0.6), (2, lambda: drop(2), 0.6)])
        q1 = T("How would you stop them fighting?", 32, REG_C).move_to([0, 1.15, 0])
        self.play(FadeOut(wait_t), run_time=0.3)
        self.say("q1", [(0, [FadeIn(q1, shift=UP * 0.1)], 0.6)])

        # --- the fix: a private piece of eden per thread
        bounds = [(-2.8, 0.0), (0.0, 2.8), (2.8, 5.6)]
        chunks = VGroup(*[Rectangle(width=b - a, height=EH, stroke_color=c, stroke_width=4).set_fill(shade(c, 0.12), 1)
                          .move_to([(a + b) / 2, EY, 0]) for (a, b), c in zip(bounds, cols)])
        links = VGroup(*[arrow(threads[i].get_bottom(), chunks[i].get_top(), cols[i], buff=0.12) for i in range(3)])
        tops = [pointer(a, EY - EH / 2 - 0.05, "top", c, size=22, length=0.55) for (a, b), c in zip(bounds, cols)]
        objs = [[cell(a + 0.45 * j, a + 0.45 * (j + 1), EY, EH - 0.16, c, k=0.55) for j in range(3)] for (a, b), c in zip(bounds, cols)]
        nolock = T("no lock: nobody else allocates there", 28, EDEN_C).move_to([0, -2.55, 0])

        def alloc_round(j):
            return [*[FadeIn(objs[i][j], shift=DOWN * 0.3) for i in range(3)], *[tops[i].animate.shift(RIGHT * 0.45) for i in range(3)]]

        self.say("s3", [(0, [FadeOut(q1), FadeOut(shared), FadeOut(eden_t)], 0.4),
                        (0, [*[GrowFromEdge(ch, LEFT) for ch in chunks]], 1.0),
                        (0, [*[GrowArrow(l) for l in links], *[FadeIn(t) for t in tops]], 0.7),
                        (1, [FadeIn(nolock)], 0.5), (1, lambda: alloc_round(0), 0.55), (1, lambda: alloc_round(1), 0.55), (1, lambda: alloc_round(2), 0.55)])
        name = T("TLAB: thread-local allocation buffer", 32).move_to([0, -2.55, 0])
        size_n = T("about 266 KB each, in one JDK 21 trace", 24, GREY_B).move_to([0, -3.15, 0])
        self.say("s4", [(0, [ReplacementTransform(nolock, name)], 1.0), (0, [FadeIn(size_n)], 0.6)])

        # --- inside one TLAB: compare, add, store
        BY, BH = 0.5, 1.2
        bar = Rectangle(width=11, height=BH, stroke_color=T1, stroke_width=4).set_fill(shade(T1, 0.08), 1).move_to([0, BY, 0])
        old_spans = [(-5.5, -4.3, "Long"), (-4.3, -2.7, "Point"), (-2.7, -1.5, "Long")]
        old = [cell(a, b, BY, BH - 0.2, T1, lab, k=0.45) for a, b, lab in old_spans]
        top_p = pointer(-1.5, BY - BH / 2 - 0.05, "top", T1)
        start_p = pointer(-5.5, BY - BH / 2 - 0.05, "start", GREY_B)
        end_p = pointer(5.5, BY - BH / 2 - 0.05, "end", GREY_B)
        t1_lab = T("thread 1's TLAB", 28, T1).next_to(bar, UP, buff=0.2).align_to(bar, LEFT)
        zoom_src = VGroup(chunks[0], *objs[0], tops[0])
        zoom_dst = VGroup(bar, *old, top_p)
        rest = VGroup(eden, used, *drops, chunks[1], chunks[2], *objs[1], *objs[2], tops[1], tops[2], links, threads[1], threads[2],
                      name, size_n)
        self.play(FadeOut(rest), run_time=0.6)
        self.play(ReplacementTransform(zoom_src, zoom_dst), ReplacementTransform(threads[0], t1_lab),
                  run_time=1.2)
        steps = VGroup(chip("1  compare: does it fit?", GREY_B, 26), chip("2  add: top + size", GREY_B, 26),
                       chip("3  store the new top", GREY_B, 26)).arrange(RIGHT, buff=0.3).move_to([0, -2.55, 0])
        fit(steps, 12.4)
        newp = cell(-1.5, 0.1, 2.45, BH - 0.2, T1, "Point", k=0.45)
        free = DoubleArrow([-1.4, BY, 0], [5.4, BY, 0], buff=0, stroke_width=3, color=GREY_B, tip_length=0.2)
        free_t = T("free space", 24, GREY_B).next_to(free, UP, buff=0.08)

        def light(i):
            return steps[i][0].animate.set_stroke(REG_C).set_fill(REG_C, 0.25)

        self.say("s5", [(0, [FadeIn(start_p), FadeIn(end_p), FadeIn(newp, shift=DOWN * 0.2)], 0.8),
                        (0, [FadeIn(steps[0]), GrowFromCenter(free), FadeIn(free_t)], 0.7), (0, [light(0)], 0.5),
                        (1, [FadeOut(free), FadeOut(free_t), FadeIn(steps[1]), FadeIn(steps[2])], 0.4),
                        (1, [newp.animate.move_to([-0.7, BY, 0]), light(1)], 0.7),
                        (1, [top_p.animate.shift(RIGHT * 1.6)], 0.6), (1, [light(2), Indicate(top_p, color=REG_C)], 0.7)])
        jit_n = T("the JIT inlines these into your method", 26, GREY_B).next_to(bar, UP, buff=0.2).align_to(bar, RIGHT)
        self.say("s6", [(0, [Indicate(steps, color=REG_C, scale_factor=1.04)], 0.9), (1, [FadeIn(jit_n)], 0.6)])
        more = [cell(a, b, BY, BH - 0.2, T1, lab, k=0.45) for a, b, lab in [(0.1, 1.3, "Long"), (1.3, 2.9, "Point"), (2.9, 4.5, "Point")]]
        self.play(LaggedStart(*[FadeIn(m, shift=DOWN * 0.3) for m in more], lag_ratio=0.6),
                  top_p.animate.shift(RIGHT * 4.4), run_time=1.6)

        # --- the slow path
        big = cell(4.5, 6.1, 2.45, BH - 0.2, T1, "Point", k=0.45)
        endline = DashedLine([5.5, BY - 0.9, 0], [5.5, 3.0, 0], dash_length=0.1, stroke_width=3, color=ESC_C)
        self.say("q2", [(0, [FadeOut(jit_n), FadeIn(big, shift=DOWN * 0.2)], 0.6), (0, [Create(endline), big[0].animate.set_stroke(ESC_C)], 0.6)])
        self.play(FadeOut(VGroup(steps, start_p, end_p, top_p, endline)), run_time=0.5)
        nbar = Rectangle(width=11, height=BH, stroke_color=T1, stroke_width=4).set_fill(shade(T1, 0.08), 1).move_to([0, -1.5, 0])
        nb_lab = T("a fresh TLAB, taken from eden with one atomic update", 26, T1).next_to(nbar, DOWN, buff=0.22)
        left = Rectangle(width=1.0, height=BH - 0.2, stroke_width=0).set_fill(GREY_D, 1).move_to([5.0, BY, 0])
        once = T("once per TLAB, not once per object", 26, GREY_B).move_to([0, -3.15, 0])
        big.set_z_index(2)                         # stays in front of the new TLAB it drops into
        self.say("s7", [(0, [GrowFromEdge(nbar, LEFT), FadeIn(nb_lab)], 0.9),
                        (0, [big.animate.move_to([-4.7, -1.5, 0]).set_stroke(T1), FadeIn(left)], 0.9),
                        (1, [FadeIn(once)], 0.6), (1, [Indicate(nbar, color=T1, scale_factor=1.02)], 0.8)])
        self.play(FadeOut(VGroup(bar, *old, newp, *more, big, nbar, nb_lab, left, once, t1_lab)), run_time=0.6)

        # --- escape analysis: a Point that never leaves the method
        MC = np.array([-3.0, 0.3, 0])
        mbox = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=6.2, height=4.2, stroke_color=WHITE, stroke_width=3),
                              num_dashes=60).move_to(MC)
        mname = M("sumPoints(n)", 28).move_to([-5.75, 2.0, 0], aligned_edge=LEFT)
        mloop = T("a loop, n = 1,000,000 times", 24, GREY_B).next_to(mname, DOWN, buff=0.15).align_to(mname, LEFT)
        PY = 0.35
        pt = VGroup(Rectangle(width=2.6, height=0.9, stroke_color=T1, stroke_width=3).set_fill(shade(T1, 0.3), 1).move_to([-2.8, PY, 0]))
        pt.add(Rectangle(width=0.5, height=0.9, stroke_width=0).set_fill(GREY_M, 1).move_to([-3.85, PY, 0]))
        xs = VGroup(Rectangle(width=1.05, height=0.9, stroke_width=0).move_to([-3.05, PY, 0]), M("x", 30).move_to([-3.05, PY, 0]))
        ys = VGroup(Rectangle(width=1.05, height=0.9, stroke_width=0).move_to([-2.0, PY, 0]), M("y", 30).move_to([-2.0, PY, 0]))
        pt.add(xs, ys)
        p_lab = M("p", 30, T1).next_to(pt, LEFT, buff=0.25)
        sbox = VGroup(M("s += p.x + p.y", 26))
        sbox.move_to([-3.0, -1.05, 0])
        s_ar = VGroup(arrow(xs.get_bottom(), sbox.get_top() + LEFT * 0.4, GREY_B, buff=0.1),
                      arrow(ys.get_bottom(), sbox.get_top() + RIGHT * 0.6, GREY_B, buff=0.1))
        tb = Rectangle(width=5.2, height=0.7, stroke_color=T1, stroke_width=3).set_fill(shade(T1, 0.08), 1).move_to([3.6, -2.35, 0])
        tb_l = T("thread 1's TLAB", 24, T1).next_to(tb, UP, buff=0.15).align_to(tb, LEFT)
        tb_n = T("interpreter: every Point is real", 24, GREY_B).next_to(tb, DOWN, buff=0.15)
        fl = [cell(1.0 + 0.5 * i + 0.03, 1.0 + 0.5 * (i + 1) - 0.03, -2.35, 0.54, T1, k=0.55) for i in range(8)]
        flights = [FadeIn(fl[i], target_position=pt.get_center(), scale=0.6) for i in range(8)]
        self.say("s9", [(1, [Create(mbox), FadeIn(mname), FadeIn(mloop)], 1.0), (1, [FadeIn(pt, shift=DOWN * 0.15), FadeIn(p_lab)], 0.6),
                        (1, [GrowArrow(s_ar[0]), GrowArrow(s_ar[1]), FadeIn(sbox)], 0.7),
                        (2, [FadeIn(tb), FadeIn(tb_l), FadeIn(tb_n)], 0.6),
                        (2, [LaggedStart(*flights, lag_ratio=0.35)], 2.6)])


        doors_txt = ["stored in a field", "put in an array or collection", "returned", "passed to a call C2 doesn't inline"]
        doors = VGroup(*[T(d, 26, GREY_B).move_to([1.1, 2.15 - 0.72 * i, 0], aligned_edge=LEFT) for i, d in enumerate(doors_txt)])
        d_ar = VGroup(*[DashedLine(pt.get_right() + RIGHT * 0.1, d.get_left() + LEFT * 0.15, dash_length=0.1, stroke_width=2.5, color=GREY_B)
                        .add_tip(tip_length=0.18) for d in doors])
        q3 = T("Can p get out?", 32, REG_C).move_to([-3.0, 2.95, 0])
        self.say("q3", [(0, [FadeIn(q3)], 0.5), (0, [LaggedStart(*[Create(a) for a in d_ar], lag_ratio=0.2), FadeIn(doors)], 1.2)])
        crosses = VGroup(*[tick(False, 0.2).move_to(d.get_left() + LEFT * 0.45) for d in doors])
        self.say("s10", [(0, [FadeOut(q3)], 0.3), (1, [LaggedStart(*[Create(c) for c in crosses], lag_ratio=0.35)], 1.6),
                         (1, [d_ar.animate.set_opacity(0.3), doors.animate.set_opacity(0.45)], 0.6)])
        ea = T("escape analysis", 36, REG_C).move_to([-3.0, 2.95, 0])
        self.say("s11", [(0, [Indicate(mbox, color=REG_C, scale_factor=1.02)], 1.0), (1, [Write(ea)], 1.0)])

        regs = VGroup(chip("x", REG_C, 30, mono=True), chip("y", REG_C, 30, mono=True)).arrange(RIGHT, buff=0.6).move_to([-2.8, PY, 0])
        regs_l = T("registers", 24, REG_C).next_to(regs, RIGHT, buff=0.3)
        sr = T("scalar replacement", 30, REG_C).move_to([-3.0, -2.35, 0])
        tb_n2 = T("C2's code: nothing new here", 24, EDEN_C).next_to(tb, DOWN, buff=0.15)
        self.say("s12", [(0, [FadeOut(VGroup(d_ar, doors, crosses)), FadeOut(pt[0]), FadeOut(pt[1]), FadeOut(xs[0]), FadeOut(ys[0]),
                              ReplacementTransform(xs[1], regs[0][1]), ReplacementTransform(ys[1], regs[1][1]), FadeIn(regs[0][0]), FadeIn(regs[1][0])], 1.0),
                              (0, [FadeIn(regs_l), Transform(tb_n, tb_n2)], 0.6),
                              (1, [FadeIn(sr, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(mbox, mname, mloop, p_lab, sbox, s_ar, regs, regs_l, ea, sr, tb, tb_l, tb_n, *fl)), run_time=0.7)

        # --- the bytes per call, round by round
        head = T("bytes allocated by each call of sumPoints", 30).move_to([0, 3.0, 0])
        XS = [-3.6 + 0.95 * i for i in range(10)]
        HMAX = 1.8
        def bars(base_y, vals, color):
            g = VGroup()
            for x, v in zip(XS, vals):
                h = max(0.02, HMAX * v / 32.0)
                g.add(Rectangle(width=0.6, height=h, stroke_width=0).set_fill(color, 1).move_to([x, base_y + h / 2, 0]))
            return g

        B1, B2 = 0.55, -2.75
        axis1 = Line([XS[0] - 0.5, B1, 0], [XS[-1] + 0.5, B1, 0], stroke_width=2, color=GREY_D)
        axis2 = Line([XS[0] - 0.5, B2, 0], [XS[-1] + 0.5, B2, 0], stroke_width=2, color=GREY_D)
        rn1 = VGroup(*[M(str(i), 20, GREY_B).move_to([x, B1 - 0.25, 0]) for i, x in enumerate(XS)])
        rn2 = VGroup(*[M(str(i), 20, GREY_B).move_to([x, B2 - 0.25, 0]) for i, x in enumerate(XS)])
        lab1 = T("default", 26).move_to([-5.6, B1 + 0.2, 0])
        lab1r = T("round", 20, GREY_B).move_to([-5.6, B1 - 0.25, 0])
        lab2r = T("round", 20, GREY_B).move_to([-5.6, B2 - 0.25, 0])
        early = bars(B1, [8.0, 1.57, 0.26, 0.26, 0, 0, 0, 0, 0, 0], T1)
        zeros = VGroup(*[M("0", 24, EDEN_C).move_to([x, B1 + 0.25, 0]) for x in XS[4:]])
        br_e = BraceBetweenPoints([XS[0] - 0.35, B1 + 0.75, 0], [XS[3] + 0.35, B1 + 0.75, 0], UP, color=GREY_B)
        br_e_t = T("megabytes: interpreter and C1", 24, GREY_B).next_to(br_e, UP, buff=0.1)
        br_z = BraceBetweenPoints([XS[4] - 0.35, B1 + 0.75, 0], [XS[9] + 0.35, B1 + 0.75, 0], UP, color=EDEN_C)
        br_z_t = T("0 bytes: C2 compiled it", 24, EDEN_C).next_to(br_z, UP, buff=0.1)
        self.say("s13", [(0, [FadeIn(head), Create(axis1), FadeIn(rn1), FadeIn(lab1), FadeIn(lab1r)], 0.8),
                         (1, [LaggedStart(*[GrowFromEdge(b, DOWN) for b in early[:4]], lag_ratio=0.3)], 1.0),
                         (1, [GrowFromCenter(br_e), FadeIn(br_e_t)], 0.6),
                         (2, [LaggedStart(*[FadeIn(z, shift=DOWN * 0.1) for z in zeros], lag_ratio=0.2)], 1.0),
                         (2, [GrowFromCenter(br_z), FadeIn(br_z_t)], 0.6)])
        off = bars(B2, [32] * 10, ESC_C)
        lab2 = M("-XX:-DoEscapeAnalysis", 24, ESC_C).move_to([XS[0] - 0.3, B2 + HMAX + 0.4, 0], aligned_edge=LEFT)
        off_t = T("32,000,000 bytes every round", 26, ESC_C).next_to(lab2, RIGHT, buff=0.5)
        self.say("s14", [(0, [Create(axis2), FadeIn(rn2), FadeIn(lab2r), FadeIn(lab2)], 0.7),
                         (0, [LaggedStart(*[GrowFromEdge(b, DOWN) for b in off], lag_ratio=0.12)], 1.2),
                         (0, [FadeIn(off_t)], 0.5)])
        warn = T("never assert \"allocates nothing\" in a unit test", 28, ESC_C)
        chart = VGroup(head, axis1, axis2, rn1, rn2, lab1, lab1r, lab2r, early, zeros, br_e, br_e_t, br_z, br_z_t, off, lab2, off_t)
        self.say("s15", [(0, [FadeOut(chart)], 0.6), (0, [FadeIn(warn.move_to([0, 0.3, 0]), shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(warn), run_time=0.5)

        # --- the code, as a check of the picture
        jl = code_block(["record Point(long x, long y) {}",
                         "for (int i = 0; i < n; i++) {",
                         "    Point p = new Point(i, i + 1);",
                         "    s += p.x() + p.y();",
                         "}"], 24)
        kl = code_block(["data class Point(val x: Long, val y: Long)",
                         "for (i in 0 until n) {",
                         "    val p = Point(i.toLong(), i + 1L)",
                         "    s += p.x + p.y",
                         "}"], 24)
        for l in (jl, kl):
            l[2].set_color(T1)
        jh = T("Java", 24, GREY_B)
        kh = T("Kotlin", 24, GREY_B)
        jg = VGroup(jh, jl).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        kg = VGroup(kh, kl).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        code = VGroup(jg, kg).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, 0.1, 0])
        fit(code, 12)
        self.say("s16", [(0, [FadeIn(jg, shift=UP * 0.15)], 0.8), (0, [FadeIn(kg, shift=UP * 0.15)], 0.8),
                         (0, [Indicate(VGroup(jl[2], kl[2]), color=T1, scale_factor=1.04)], 1.0)])
        self.play(FadeOut(code), run_time=0.6)

        # --- the rule and a check
        rule = VGroup(T("new is a pointer bump in your own TLAB.", 34),
                      T("An object that never leaves a hot method", 34, REG_C),
                      T("may never be allocated.", 34, REG_C)).arrange(DOWN, buff=0.25).move_to([0, 1.3, 0])
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.8), (0, [FadeIn(rule[1:], shift=UP * 0.1)], 0.8)])
        chk = VGroup(T("Check: the loop adds each Point to a list.", 28),
                     T("Does C2 remove the allocation?", 28)).arrange(DOWN, buff=0.2).move_to([0, -1.3, 0])
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("No: the list is a way out.", 30, ESC_C).move_to([0, -2.75, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
