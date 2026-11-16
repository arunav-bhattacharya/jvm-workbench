from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"\bByte Buddy\b", "byte buddy"), (r"\bbyte-buddy\.jar\b", "the byte buddy jar"),
              (r"@Retry's", "at Retry's"), (r"\b1,029\b", "one thousand and twenty-nine"),
              (r"\b2,207\b", "two thousand two hundred and seven"), (r"\b1,216\b", "twelve hundred and sixteen")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it.
    A number is a pause; a (anims, run_time) pair is one play; anims may be a callable."""
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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=22, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def step(label, col, size=24):
    t = T(label, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.45, height=0.66, stroke_color=col, stroke_width=2.5)
    r.set_fill(dark(col, 0.1), 1)
    return VGroup(r, t.move_to(r))


def chain(items, y, x0, x1):
    """Lay chips out evenly between x0 and x1 on row y, with small arrows between them."""
    g = VGroup(*items)
    gap = (x1 - x0 - sum(m.width for m in items)) / max(1, len(items) - 1)
    x = x0
    for m in items:
        m.move_to([x + m.width / 2, y, 0]); x += m.width + gap
    ars = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.06, stroke_width=2.5, color=GREY_B,
                         max_tip_length_to_length_ratio=0.35) for a, b in zip(items, items[1:])])
    return g, ars


RUN, GEN, BB, HID, PRX, WR, BLD = RED_M, GREEN_M, PURPLE_M, TEAL_M, GOLD_M, YELLOW_M, BLUE_M
X0, U = -3.3, 0.0088                    # time axis: x of 0 ms, units per ms
Y1, Y2, YAX = -0.55, -1.75, -2.75       # run-time bar, build-time bar, axis


def xt(ms):
    return X0 + U * ms


class Cap4BuildTime(VoiceScene):
    """cap4-03 sections 1 and 2: one start from main to the first payment. The reflective container finds its
    components, reads annotations, orders the graph and has Byte Buddy write a subclass on every start: 2,207 classes,
    ready at 1,029 ms. 1,216 of them are machinery (814 from byte-buddy.jar, 3 written, 30 JDK proxies, 123 hidden),
    each found, parsed, verified and interpreted. The same steps moved to the build machine leave only holder
    initializers: 991 classes, ready at 266 ms. Numbers from the lesson (JDK 21, a busy machine)."""

    def construct(self):
        self.title_card("Wire it at build time", "what a start does, and what it doesn't have to")

        # ---------------- the timeline: one reflective start ----------------
        axis = Line([X0, YAX, 0], [xt(1100), YAX, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[Line([xt(ms), YAX - 0.08, 0], [xt(ms), YAX + 0.08, 0], stroke_width=2, color=GREY_B)
                         for ms in (0, 250, 500, 750, 1000)])
        tl = VGroup(*[T(f"{ms:,} ms" if ms else "0", 20, GREY_B).move_to([xt(ms), YAX - 0.32, 0])
                      for ms in (0, 250, 500, 750, 1000)])
        ax_l = T("from the first line of main to the first payment done", 22, GREY_B).move_to([1.4, 3.05, 0])
        lab1 = VGroup(T("run-time wiring", 24, RUN), T("on every start", 20, GREY_B)).arrange(DOWN, buff=0.08)
        lab1.move_to([0, Y1, 0]).align_to(np.array([X0 - 0.3, 0, 0]), RIGHT)
        self.beat("A deploy starts fresh JVMs. Until the container has wired its components, no payment goes through.",
                  Create(axis), FadeIn(ticks), FadeIn(tl), run_time=1.6)
        self.beat("Here is one start, timed from the first line of main to the first payment done.",
                  FadeIn(ax_l), FadeIn(lab1), run_time=1.2)

        steps1 = [step("find components", RUN), step("reflection", RUN), step("graph", RUN), step("Byte Buddy", BB)]
        row1, ars1 = chain(steps1, 0.55, X0 + 0.1, xt(1029))
        for s_ in steps1:
            s_.set_opacity(0.25)
        ars1.set_opacity(0.25)
        note1 = T("steps in order; only the total was measured", 20, GREY_B).move_to([1.4, 1.35, 0])
        bar1 = Rectangle(width=0.01, height=0.5, stroke_width=0).set_fill(RUN, 0.85).move_to([X0, Y1, 0], aligned_edge=LEFT)
        t1 = ValueTracker(0)

        def grow(bar, tr, y, col):
            def f(m):
                w = max(0.01, U * tr.get_value())
                m.become(Rectangle(width=w, height=0.5, stroke_width=0).set_fill(col, 0.85).move_to([X0, y, 0],
                                                                                                    aligned_edge=LEFT))
            return f
        bar1.add_updater(grow(bar1, t1, Y1, RUN))
        self.add(bar1)

        def light(k):
            return [steps1[k].animate.set_opacity(1)] + ([ars1[k - 1].animate.set_opacity(1)] if k else [])
        seq(self, "The reflective container does everything now. It finds the components, reads their annotations, "
                  "orders the graph, and has Byte Buddy write a subclass.",
            ([FadeIn(VGroup(row1, ars1)), FadeIn(note1)], 0.6),
            (lambda: [*light(0), t1.animate(rate_func=linear).set_value(250)], 1.6),
            (lambda: [*light(1), t1.animate(rate_func=linear).set_value(500)], 1.6),
            (lambda: [*light(2), t1.animate(rate_func=linear).set_value(750)], 1.4),
            (lambda: [*light(3), t1.animate(rate_func=linear).set_value(1029)], 2.4))
        bar1.clear_updaters()
        flag1 = VGroup(Line([xt(1029), Y1 - 0.35, 0], [xt(1029), Y1 + 0.35, 0], stroke_width=4, color=WHITE),
                       T("ready: 1,029 ms, 2,207 classes loaded", 22, WHITE))
        flag1[1].move_to([0, Y1 - 0.55, 0]).align_to(np.array([xt(1029), 0, 0]), RIGHT)
        self.beat("Ready after 1,029 milliseconds. It loaded 2,207 classes.", Create(flag1[0]), FadeIn(flag1[1]),
                  run_time=1.0)
        self.play(FadeOut(VGroup(row1, ars1, note1, ax_l)), run_time=0.5)
        self.play(FadeOut(VGroup(axis, ticks, tl, lab1, bar1, flag1)), run_time=0.5)

        # ---------------- where 2,207 classes come from ----------------
        CU, BX = 0.00498, -5.6                 # class bar: units per class, left edge

        def seg(n0, n, col, y, op=0.85):
            return Rectangle(width=max(0.05, CU * n), height=0.55, stroke_width=0).set_fill(col, op).move_to(
                [BX + CU * n0, y, 0], aligned_edge=LEFT)
        YB1, YB2 = 0.85, -0.85
        parts = [(0, 953, GREY_C), (953, 284, GREY_D), (1237, 123, HID), (1360, 30, PRX), (1390, 3, WR), (1393, 814, BB)]
        big = VGroup(*[seg(a, n, c, YB1) for a, n, c in parts])
        small = seg(0, 991, GREEN_M, YB2, 0.7)
        bt1 = T("reflective + Byte Buddy: 2,207 classes", 24, RUN).next_to(big, UP, buff=0.18).align_to(big, LEFT)
        bt2 = T("generated registry: 991 classes", 24, GEN).next_to(small, UP, buff=0.18).align_to(small, LEFT)
        self.beat("The same app, wired by generated code, loads 991 classes.",
                  FadeIn(big), FadeIn(bt1), FadeIn(small), FadeIn(bt2), run_time=1.4)
        brace = BraceBetweenPoints([BX + CU * 991, YB1 - 0.32, 0], [BX + CU * 2207, YB1 - 0.32, 0], DOWN, color=GREY_A)
        br_l = T("1,216 extra: all machinery", 24, GREY_A).next_to(brace, DOWN, buff=0.1)
        dl = DashedLine([BX + CU * 991, YB2 + 0.3, 0], [BX + CU * 991, YB1 - 0.3, 0], dash_length=0.06,
                        stroke_width=1.5, color=GREY_B)
        self.beat("So 1,216 classes are pure machinery.", GrowFromCenter(brace), FadeIn(br_l), Create(dl), run_time=1.0)
        bb_l = T("814 from byte-buddy.jar", 24, BB).move_to(big[5]).shift(UP * 0.62)
        seq(self, "814 come from byte-buddy.jar. Byte Buddy loads its own type model, matchers and class writer before "
                  "it can write one subclass.",
            ([FadeIn(bb_l), Indicate(big[5], color=BB, scale_factor=1.04)], 1.2))
        callouts = VGroup()
        for k, (txt, col) in enumerate((("3 that Byte Buddy wrote", WR), ("30 JDK proxies: the issuer, annotations", PRX),
                                         ("123 hidden: lambdas, method handles", HID))):
            sgm = big[4 - k]
            lbl = T(txt, 22, col).move_to([0, 3.05 - 0.45 * k, 0]).align_to(np.array([BX + CU * 1300, 0, 0]), RIGHT)
            ln = Line(lbl.get_right() + RIGHT * 0.08, [sgm.get_center()[0], YB1 + 0.3, 0], stroke_width=1.5, color=col)
            callouts.add(VGroup(lbl, ln))
        seq(self, "Then the 3 classes it writes. 30 JDK proxy classes: one is the issuer proxy, and annotations read by "
                  "reflection are proxies too. And 123 hidden classes for lambdas and method handles.",
            ([FadeIn(callouts[0])], 0.6), 1.3, ([FadeIn(callouts[1])], 0.6), 2.2, ([FadeIn(callouts[2])], 0.6))

        # one level down: what each class costs
        pipe = [step(s_, GREY_A, 22) for s_ in ("find", "parse", "verify", "interpret")]
        prow, pars = chain(pipe, -2.55, -4.2, 4.2)
        chip = Square(0.32, stroke_width=0).set_fill(BB, 0.95).set_z_index(5).move_to(pipe[0].get_top() + UP * 0.32)
        seq(self, "Each one is found, parsed and verified, then run in the interpreter, because nothing is hot yet.",
            ([FadeIn(prow), FadeIn(pars), FadeIn(chip)], 0.6),
            (lambda: [chip.animate.move_to(pipe[1].get_top() + UP * 0.32)], 0.9),
            (lambda: [chip.animate.move_to(pipe[2].get_top() + UP * 0.32)], 0.9),
            (lambda: [chip.animate.move_to(pipe[3].get_top() + UP * 0.32)], 0.9))
        self.play(FadeOut(VGroup(big, small, bt1, bt2, brace, br_l, dl, bb_l, callouts, prow, pars, chip)), run_time=0.6)

        # ---------------- move the work to the build machine ----------------
        bld_l = T("build machine: once per build", 24, BLD).move_to([0, 3.1, 0])
        steps2 = [step("find components", BLD), step("graph", BLD), step("write Java source", BLD), step("javac, jar", BLD)]
        row2, ars2 = chain(steps2, 2.35, -5.6, 5.6)
        self.add(axis, ticks, tl, lab1, bar1, flag1[0])
        for m in (bar1, flag1):
            m.set_opacity(0.45)
        old = VGroup(axis, ticks, tl, lab1, bar1, flag1)
        self.remove(old)
        seq(self, "None of this depends on anything but the classes, and those are fixed when you build. So run the "
                  "same steps on the build machine, once.",
            ([FadeIn(old)], 0.8), 2.6, ([FadeIn(bld_l), LaggedStart(*[FadeIn(s_) for s_ in steps2], lag_ratio=0.4),
                                       Create(ars2)], 2.0))
        cyc = T("a cycle in the graph fails the build instead of the deploy", 22, BLD).move_to([0, 1.55, 0])
        self.beat("A cycle in the graph now fails the build instead of the deploy.", FadeIn(cyc), run_time=0.8)
        src = M("INTERCEPTION.chain(true, 3, IssuerUnavailableException.class)", 22, WR).move_to([0, 1.55, 0])
        src_l = T("an interceptor, as source, with @Retry's values written in", 20, GREY_B).next_to(src, DOWN, buff=0.12)
        seq(self, "The generator writes plain Java: a holder class for each singleton, and the interceptors as source, "
                  "with the annotation values written in.",
            ([Indicate(steps2[2][1], color=WR, scale_factor=1.15)], 1.0), 2.2,
            ([FadeOut(cyc), FadeIn(src), FadeIn(src_l)], 0.8))

        lab2 = VGroup(T("build-time wiring", 24, GEN), T("each start", 20, GREY_B)).arrange(DOWN, buff=0.08)
        lab2.move_to([0, Y2, 0]).align_to(np.array([X0 - 0.3, 0, 0]), RIGHT)
        self.beat("Predict. What is left for each start to do?", FadeIn(lab2), run_time=0.6)
        self.wait(1.5)
        bar2 = Rectangle(width=0.01, height=0.5, stroke_width=0).set_fill(GEN, 0.85).move_to([X0, Y2, 0], aligned_edge=LEFT)
        t2 = ValueTracker(0)
        bar2.add_updater(grow(bar2, t2, Y2, GEN))
        hold = step("holders", GEN, 22).move_to([xt(133), Y2 + 0.62, 0])
        self.add(bar2)
        seq(self, "Only the holders. The JVM initializes each one the first time get touches it, once, under the class "
                  "initialization lock.",
            ([FadeIn(hold)], 0.6), ([t2.animate.set_value(266)], 2.2))
        bar2.clear_updaters()
        flag2 = VGroup(Line([xt(266), Y2 - 0.35, 0], [xt(266), Y2 + 0.35, 0], stroke_width=4, color=WHITE),
                       T("ready: 266 ms, 991 classes, no reflection", 22, WHITE))
        flag2[1].next_to(flag2[0], RIGHT, buff=0.2)
        self.beat("Ready after 266 milliseconds, with 991 classes, and no reflection.", Create(flag2[0]),
                  FadeIn(flag2[1]), run_time=1.0)
        var = T("JDK 21, a busy machine: times moved by a factor of two between runs; class counts barely moved", 20, GREY_B)
        var.scale(min(1, 12.4 / var.width)).move_to([0, -3.4, 0])
        self.play(FadeOut(tl), run_time=0.3)
        self.beat("On a busy machine, the times moved by a factor of two between runs. The reflective start was always "
                  "several times slower, and the class counts barely moved.", FadeIn(var), run_time=1.0)
        self.play(FadeOut(VGroup(axis, ticks, lab1, bar1, flag1, bld_l, row2, ars2, src, src_l, lab2, bar2, hold, flag2,
                                 var)), run_time=0.6)

        # ---------------- the code: one holder ----------------
        jc = code(["private static final class FeeCalculator_Holder {",
                   "    static final FeeCalculator INSTANCE =",
                   "            new FeeCalculator(FxRates_Holder.INSTANCE);",
                   "}"], 24)
        kc = code(["private object FeeCalculatorHolder {",
                   "    val INSTANCE = FeeCalculator(FxRatesHolder.INSTANCE)",
                   "}"], 24)
        jc[2].set_color(GEN); kc[1].set_color(GEN)
        cg = VGroup(titled("Java: written by the generator", jc), titled("Kotlin: a Kotlin object is a holder class too", kc)
                    ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        cg.scale(min(1, 12.4 / cg.width)).move_to([0, 0.75, 0])
        price = VGroup(T("The price: the set of components is fixed when you build,", 24, GREY_A),
                       T("and a holder whose constructor throws stays failed until a restart.", 24, GREY_A)
                       ).arrange(DOWN, buff=0.12).next_to(cg, DOWN, buff=0.55)
        self.beat("Here is one holder, in Java and Kotlin. A plain new call, with its dependency's holder inside.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.2)
        self.beat("The price. The set of components is fixed when you build. And a holder whose constructor throws "
                  "stays failed until you restart.", FadeIn(price, shift=UP * 0.1), run_time=1.2)
        self.play(FadeOut(VGroup(cg, price)), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Work that depends only on the classes belongs at build time.", 30),
                      T("A start should run only ordinary code.", 30)).arrange(DOWN, buff=0.22)
        rule.scale(min(1, 12.2 / rule.width)).move_to([0, 2.3, 0])
        self.beat("The rule. Work that depends only on the classes belongs at build time. A start should run only "
                  "ordinary code.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("In the generated container, where does @Retry's 3", 28),
                     T("come from at run time?", 28)).arrange(DOWN, buff=0.16).move_to([0, 0.1, 0])
        self.beat("Check yourself. In the generated container, where does @Retry's 3 come from at run time?",
                  FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = VGroup(T("From the generated source: the generator read the annotation", 28, GOLD_M),
                     T("at build time. Nothing reads an annotation at run time.", 28, GOLD_M)).arrange(DOWN, buff=0.14)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.9, 0])
        self.beat("From the generated source. The generator read the annotation at build time and wrote 3 into the "
                  "code. Nothing reads an annotation at run time.", FadeIn(ans, shift=UP * 0.15), run_time=1.2)
        self.wait(0.8)
