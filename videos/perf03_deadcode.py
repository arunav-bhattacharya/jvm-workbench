from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"System\.nanoTime", "System dot nano time"), (r"Math\.sqrt", "Math dot square root"),
           (r"Math\.log", "Math dot log"), (r"\bsqrt\b", "square root"), (r"\bns\b", "nanoseconds"),
           (r"@Benchmark", "at Benchmark")]

CODE_C, DEAD_C, USED_C, C2_C, JMH_C, BH_C = BLUE_M, RED_M, GREEN_M, GOLD_M, TEAL_M, PURPLE_M


def code(text, size=22, color=CODE_C):
    return M(text, size, color)


def code_block(lines, size=22, color=CODE_C, ls=0.7):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def listing(label, lines, size=22, color=CODE_C, ls=0.7):
    body = code_block(lines, size, color, ls)
    head = T(label, 22, GREY_B)
    head.next_to(body, UP, buff=0.2).align_to(body, LEFT)
    return VGroup(head, body)


class Perf03DeadCode(VoiceScene):
    """perf-03 s0: a nanoTime loop measures dead-code elimination and constant folding; s1: JMH builds the loop."""

    def say(self, text, plan=(), after=0.25):
        """Speak text; plan is a list of (sentence index, [animations], run_time) started at that sentence."""
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
            self.play(*anims, run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def construct(self):
        self.title_card("Why a nanoTime loop lies", "dead-code elimination and constant folding")

        # --- the broken benchmark, Java and Kotlin
        jl = listing("Java", ["long t0 = System.nanoTime();", "for (int i = 0; i < 100_000_000; i++) {",
                              "    Math.sqrt(x);      // result discarded", "}", "long t1 = System.nanoTime();"])
        kl = listing("Kotlin", ["val t0 = System.nanoTime()", "for (i in 0 until 100_000_000) {",
                                "    sqrt(x)            // result discarded", "}", "val t1 = System.nanoTime()"])
        src = VGroup(jl, kl).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        src.move_to(LEFT * 3.15 + UP * 0.1)
        jb, kb = jl[1], kl[1]
        self.say("Here is the benchmark almost everyone writes first. "
                 "Read the clock, call Math.sqrt a hundred million times, and read the clock again.",
                 [(0, [FadeIn(jl, shift=UP * 0.2), FadeIn(kl, shift=UP * 0.2)], 1.2),
                  (1, [Indicate(VGroup(jb[0], kb[0]), color=YELLOW_M, scale_factor=1.04)], 0.8),
                  (1, [Indicate(VGroup(jb[1], jb[2], jb[3], kb[1], kb[2], kb[3]), color=YELLOW_M, scale_factor=1.03)], 1.0),
                  (1, [Indicate(VGroup(jb[4], kb[4]), color=YELLOW_M, scale_factor=1.04)], 0.8)])
        self.say("Each result is thrown away.",
                 [(0, [jb[2].animate.set_color(DEAD_C), kb[2].animate.set_color(DEAD_C)], 0.8)])

        # --- what it printed, round by round
        L = 2.45                     # bar length for 1.9 ns
        x0 = 2.35                    # where bars start
        head = T("ns per call, as printed", 26, GREY_B).move_to([3.6, 2.75, 0])
        vals = ["0.0301", "0.1299", "0.0000", "0.0000", "0.0000"]
        ys = [2.0, 1.4, 0.8, 0.2, -0.4]
        lab = VGroup(*[T(f"round {k + 1}", 24, GREY_B).move_to([1.45, y, 0]) for k, y in enumerate(ys)])
        bars = VGroup(*[Rectangle(width=max(0.02, L * float(v) / 1.9), height=0.36, stroke_width=0)
                        .set_fill(DEAD_C, 1).move_to([x0, y, 0], aligned_edge=LEFT) for v, y in zip(vals, ys)])
        nums = VGroup(*[M(v, 24, DEAD_C).next_to(b, RIGHT, buff=0.2) for v, b in zip(vals, bars)])
        sep = Line([0.85, -0.9, 0], [6.3, -0.9, 0], stroke_width=1.5, color=GREY_D)
        used_l = T("second loop, result used", 24, USED_C).move_to([0.85, -1.35, 0], aligned_edge=LEFT)
        used_b = Rectangle(width=L, height=0.36, stroke_width=0).set_fill(USED_C, 1).move_to([x0, -1.95, 0], aligned_edge=LEFT)
        used_n = T("about 1.9", 24, USED_C).next_to(used_b, RIGHT, buff=0.2)
        self.say("It runs five rounds. Round one printed 0.0301 nanoseconds per call. "
                 "Round two, 0.1299. Every later round printed zero.",
                 [(0, [FadeIn(head), FadeIn(lab)], 0.8),
                  (1, [GrowFromEdge(bars[0], LEFT), FadeIn(nums[0])], 0.8),
                  (2, [GrowFromEdge(bars[1], LEFT), FadeIn(nums[1])], 0.8),
                  (3, [*[FadeIn(b) for b in bars[2:]], LaggedStart(*[FadeIn(n) for n in nums[2:]], lag_ratio=0.3)], 1.0)])
        self.say("No CPU takes a square root in zero time. "
                 "A second loop adds each result to a sum, and prints the sum. It settles at about 1.9 nanoseconds per call.",
                 [(1, [Create(sep), FadeIn(used_l)], 0.7), (2, [GrowFromEdge(used_b, LEFT), FadeIn(used_n)], 1.0)])
        chart = VGroup(head, lab, bars, nums, sep, used_l, used_b, used_n)

        # --- dead-code elimination, on the code itself
        self.play(FadeOut(chart), FadeOut(kl), run_time=0.6)
        self.play(jl.animate.scale(1.18).move_to(LEFT * 2.6 + UP * 0.6), run_time=0.8)
        c2 = chip("C2 compiles the hot loop", C2_C, 26).move_to(UP * 3.0 + LEFT * 2.6)
        sq = jb[2]
        q_pt = np.array([3.9, sq.get_center()[1], 0])
        ask = VGroup(T("who reads", 26), T("the result?", 26)).arrange(DOWN, buff=0.08).move_to(q_pt + RIGHT * 0.4)
        ask_a = Arrow(sq.get_right() + RIGHT * 0.1, ask.get_left() + LEFT * 0.1, buff=0, stroke_width=3, color=GREY_B,
                      max_tip_length_to_length_ratio=0.15)
        nobody = T("nobody", 30, DEAD_C).move_to(ask)
        self.say("While the program runs, C2 compiles the hot loop. "
                 "It looks at the call to sqrt, and asks who reads the result.",
                 [(0, [FadeIn(c2, shift=DOWN * 0.15)], 0.7),
                  (1, [GrowArrow(ask_a), FadeIn(ask)], 0.9)])
        strike = Line(sq.get_left() + LEFT * 0.05, sq.get_right(), stroke_width=4, color=DEAD_C)
        dce = T("dead-code elimination", 30, DEAD_C).move_to(DOWN * 2.3 + LEFT * 2.6)
        self.say("Nobody does. Work whose result nobody uses can go. That's dead-code elimination.",
                 [(0, [ReplacementTransform(ask, nobody)], 0.6),
                  (1, [Create(strike)], 0.6),
                  (2, [FadeOut(VGroup(sq, strike, ask_a)), FadeIn(dce, shift=UP * 0.15)], 0.8)])
        t0l, forl, close, t1l = jb[0], jb[1], jb[3], jb[4]
        t1_to = t1l.copy().move_to(forl, aligned_edge=UL)
        gap_brace = Brace(VGroup(t0l, t1_to), RIGHT, buff=0.25, color=GREY_B)
        self.say("Now the loop has an empty body, so the loop can go too. "
                 "Between the two clock reads, nothing runs.",
                 [(0, [FadeOut(forl), FadeOut(close), FadeOut(nobody)], 0.7),
                  (0, [t1l.animate.move_to(t1_to)], 0.8),
                  (1, [FadeIn(gap_brace), FadeIn(T("nothing in between", 26, GREY_B).next_to(gap_brace, RIGHT, buff=0.2))], 0.8)])
        self.say("So the loop measured the optimizer, not your code.",
                 [(0, [Indicate(VGroup(t0l, t1l), color=C2_C, scale_factor=1.05)], 1.0)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # --- constant folding
        jc = listing("Java", ["static final double CONSTANT = 2.0;", "Math.sqrt(CONSTANT)"], size=24, ls=0.9)
        kc = listing("Kotlin", ["const val CONSTANT = 2.0", "sqrt(CONSTANT)"], size=24, ls=0.9)
        pair = VGroup(jc, kc).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        pair.scale(min(1, 12.2 / pair.width)).move_to(UP * 1.9)
        jcall, kcall = jc[1][1], kc[1][1]
        j2 = code("Math.sqrt(2.0)", 24).move_to(jcall, aligned_edge=LEFT)
        k2 = code("sqrt(2.0)", 24).move_to(kcall, aligned_edge=LEFT)
        copy_l = T("javac and kotlinc copy the value into the call", 24, GREY_B).move_to(UP * 0.35)
        self.say("Constant inputs are the second trap. Say the input is a static final constant, or a const val in Kotlin.",
                 [(1, [FadeIn(pair, shift=UP * 0.2)], 1.0)])
        answer = M("1.4142135623730951", 34, C2_C).move_to(DOWN * 1.3)
        a_from = VGroup(j2, k2)
        fold_a = Arrow(copy_l.get_bottom() + DOWN * 0.1, answer.get_top() + UP * 0.12, buff=0, stroke_width=3, color=C2_C,
                       max_tip_length_to_length_ratio=0.2)
        fold_l = T("C2 works it out while compiling", 24, C2_C).next_to(fold_a, RIGHT, buff=0.25)
        self.say("The compiler copies the 2.0 into the call. "
                 "Then C2 computes the square root while it compiles, and puts the answer in its place.",
                 [(0, [Transform(jcall, j2), Transform(kcall, k2), FadeIn(copy_l)], 1.0),
                  (1, [GrowArrow(fold_a), FadeIn(fold_l)], 0.8), (1, [FadeIn(answer, scale=0.8)], 0.8)])
        load_l = T("the benchmark times loading one number", 28).next_to(answer, DOWN, buff=0.5)
        self.say("Your benchmark now times the load of one number. That's constant folding.",
                 [(0, [FadeIn(load_l, shift=UP * 0.15)], 0.8),
                  (1, [Indicate(answer, color=C2_C, scale_factor=1.08)], 0.9)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # --- the plausible wrong number
        logl = listing("Java, JDK 21", ["Math.log(x);      // result discarded"], size=26).move_to(UP * 1.4)
        logl[1][0].set_color(DEAD_C)
        lnum = T("7 to 9 ns per call, drifting up each round", 30).move_to(DOWN * 0.1)
        lwarn = T("believable, and still not the cost of log", 28, DEAD_C).move_to(DOWN * 1.2)
        self.say("A broken loop can also print a number that looks fine. "
                 "With Math.log instead of sqrt, C2 on JDK 21 kept the call, and the loop reported 7 to 9 nanoseconds. "
                 "It still measures an accident of how C2 compiles log.",
                 [(0, [FadeIn(logl, shift=UP * 0.2)], 0.8), (1, [FadeIn(lnum)], 0.8), (2, [FadeIn(lwarn)], 0.8)])
        self.play(FadeOut(VGroup(logl, lnum, lwarn)), run_time=0.6)

        # --- JMH builds the loop
        meth = mbox("sqrtReturned()", WHITE, size=26, h=0.85)
        frame = RoundedRectangle(corner_radius=0.15, width=6.4, height=2.1, stroke_color=JMH_C, stroke_width=3)
        frame.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(JMH_C), 0.08), opacity=1)
        frame_t = T("the loop JMH generates", 24, JMH_C).next_to(frame, UP, buff=0.12).align_to(frame, LEFT).shift(RIGHT * 0.2)
        loopg = VGroup(frame, meth).move_to(LEFT * 2.3 + UP * 2.0)
        meth.move_to(frame)
        frame_t.next_to(frame, UP, buff=0.12).align_to(frame, LEFT).shift(RIGHT * 0.2)
        bh = VGroup(Circle(radius=0.62, stroke_color=BH_C, stroke_width=3).set_fill(BLACK, 1),
                    Circle(radius=0.36, stroke_width=0).set_fill(interpolate_color(ManimColor("#000000"), ManimColor(BH_C), 0.35), 1))
        bh.move_to(RIGHT * 4.3 + UP * 2.0)
        bh_t = T("Blackhole", 24, BH_C).next_to(bh, DOWN, buff=0.15)
        res_a = Arrow(meth.get_right(), bh.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        res_t = T("result", 22, GREY_B).next_to(res_a, UP, buff=0.08).shift(RIGHT * 0.9)
        steps = VGroup(chip("fresh JVM", GREY_B, 22), chip("warm-up: thrown away", GREY_B, 22),
                       chip("measurement: kept", JMH_C, 22)).arrange(RIGHT, buff=0.3).next_to(frame, DOWN, buff=0.3).align_to(frame, LEFT)

        jj = listing("Java", ["double x = 2.0;    // not final", "@Benchmark", "public double sqrtReturned() {",
                              "    return Math.sqrt(x);", "}"], size=24)
        kj = listing("Kotlin, in an open class", ["var x = 2.0    // not const", "@Benchmark",
                                                  "fun sqrtReturned(): Double =", "    sqrt(x)"], size=24)
        codes = VGroup(jj, kj).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        codes.scale(min(1, 12.2 / codes.width)).move_to(DOWN * 1.95)
        self.say("JMH, the OpenJDK benchmark harness, builds the measuring loop for you. "
                 "You write one method, and mark it @Benchmark.",
                 [(0, [FadeIn(frame), FadeIn(frame_t)], 0.8),
                  (1, [FadeIn(codes, shift=UP * 0.2)], 1.0), (1, [FadeIn(meth, scale=0.8)], 0.6)])
        self.say("At compile time, JMH generates the loop around your method, written to defeat these tricks. "
                 "It runs it in fresh JVMs, and throws away the warm-up rounds.",
                 [(0, [Indicate(frame, color=JMH_C, scale_factor=1.03)], 0.9),
                  (1, [LaggedStart(*[FadeIn(s, shift=RIGHT * 0.15) for s in steps], lag_ratio=0.35)], 1.4)])
        dot = Dot(radius=0.1, color=YELLOW_M).move_to(meth.get_right())
        self.say("Return the result, and JMH consumes it. "
                 "The JIT has to treat a consumed value as used, so the square root stays.",
                 [(0, [Indicate(VGroup(jj[1][3], kj[1][3]), color=YELLOW_M, scale_factor=1.05)], 0.8),
                  (0, [FadeIn(bh), FadeIn(bh_t), GrowArrow(res_a), FadeIn(res_t)], 0.8),
                  (1, [MoveAlongPath(dot, Line(meth.get_right(), bh.get_center()), rate_func=smooth)], 1.0),
                  (1, [dot.animate.scale(0.2).set_opacity(0)], 0.4)])
        # more than one result: an explicit Blackhole
        jb2 = listing("Java", ["bh.consume(Math.sqrt(x));"], size=24)
        kb2 = listing("Kotlin", ["bh.consume(sqrt(x))"], size=24)
        bhpair = VGroup(jb2, kb2).arrange(RIGHT, buff=1.2, aligned_edge=UP)
        bh_head = T("more than one result: pass each to a Blackhole parameter", 26, BH_C)
        bhg = VGroup(bh_head, bhpair).arrange(DOWN, buff=0.4).move_to(DOWN * 1.9)
        self.say("With more than one result, pass each one to a Blackhole.",
                 [(0, [FadeOut(codes), FadeIn(bhg, shift=UP * 0.2)], 1.0),
                  (0, [Indicate(bh, color=BH_C, scale_factor=1.15)], 0.7)])
        self.play(FadeOut(bhg), FadeIn(codes), run_time=0.6)
        self.say("And read the input from a field that isn't final, so C2 can't fold it into a constant.",
                 [(0, [Indicate(VGroup(jj[1][0], kj[1][0]), color=YELLOW_M, scale_factor=1.05)], 1.0)])
        self.wait(0.8)
