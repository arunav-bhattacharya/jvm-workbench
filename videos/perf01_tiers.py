from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bkotlinc\b", "kotlin C"), (r"\bHotSpot\b", "Hot Spot"), (r"feeCents", "fee cents")]

INT_C, C1_C, C2_C, TRAP_C = WHITE, TEAL_M, GOLD_M, RED_M


def card(title, sub, color, w, h=1.3, tsize=30, ssize=20, mono_sub=False):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    white = ManimColor(color).to_hex().upper() == "#FFFFFF"
    r.set_fill(BLACK if white else interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = T(title, tsize)
    s = (M if mono_sub else T)(sub, ssize, GREY_B)
    VGroup(t, s).arrange(DOWN, buff=0.12).move_to(r)
    return VGroup(r, t, s)


def rows(lines, step=0.38):
    """Stack text lines at a fixed step, top-left aligned, so code lines sit evenly whatever their glyphs."""
    for k, l in enumerate(lines):
        l.move_to(ORIGIN, aligned_edge=UL).shift(DOWN * k * step)
    return lines


def listing(label, lines, size=22, color=WHITE, label_color=GREY_B, step=0.38):
    body = rows(VGroup(*[M(x, size, color) for x in lines]), step)
    head = T(label, 22, label_color)
    head.next_to(body, UP, buff=0.2).align_to(body, LEFT)
    return VGroup(head, body)


class Perf01Tiers(VoiceScene):
    """perf-01: interpreter, C1 with profiling, C2 with the profile's bets; perf-02: a lost bet deoptimizes."""

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
        self.title_card("From bytecode to machine code", "interpreter, C1, C2")

        # --- source and bytecode
        jl = listing("Java", ["long fee = methods[i].feeCents(amounts[i]);", "if (refund[i]) net -= amounts[i];",
                              "else net += amounts[i] - fee;"], color=BLUE_M)
        kl = listing("Kotlin", ["val fee = methods[i].feeCents(amounts[i])", "if (refund[i]) net -= amounts[i]",
                                "else net += amounts[i] - fee"], color=BLUE_M)
        jv = VGroup(jl[0], *jl[1])
        kv = VGroup(kl[0], *kl[1])
        src = VGroup(jv, kv).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(LEFT * 2.9 + UP * 0.3)
        bc_txt = ["12: aload_0", "13: iload 5", "15: aaload", "16: aload_1", "17: iload 5", "19: laload",
                  "20: invokeinterface feeCents", "25: lstore 6", "27: aload_2", "28: iload 5", "30: baload", "31: ifeq 44"]
        bcl = listing("its bytecode, from javap", bc_txt, step=0.37)
        bc_h, bc = bcl[0], bcl[1]
        bcg = bcl.move_to(RIGHT * 3.7 + DOWN * 0.1)
        self.say("javac and kotlinc don't produce machine code. "
                 "They produce bytecode: small instructions for the JVM, which HotSpot turns into machine code while the program runs.",
                 [(0, [FadeIn(jv, shift=UP * 0.2), FadeIn(kv, shift=UP * 0.2)], 1.2),
                  (1, [FadeIn(bc_h), LaggedStart(*[FadeIn(l, shift=LEFT * 0.15) for l in bc], lag_ratio=0.12)], 2.0)])
        self.say("This is the loop body of settle, which adds up a batch of payments. "
                 "Bytecode 20 is the call to feeCents. Bytecode 31 tests for a refund.",
                 [(1, [Indicate(bc[6], color=YELLOW_M, scale_factor=1.06), Indicate(jv[1], color=YELLOW_M, scale_factor=1.03)], 1.0),
                  (2, [Indicate(bc[11], color=YELLOW_M, scale_factor=1.06), Indicate(jv[2], color=YELLOW_M, scale_factor=1.03)], 1.0)])

        cursor = Triangle(color=YELLOW_M, fill_opacity=1, stroke_width=0).scale(0.1).rotate(-PI / 2)
        cursor.next_to(bc[0], LEFT, buff=0.15)
        steps = [cursor.animate(run_time=0.22).next_to(bc[k], LEFT, buff=0.15) for k in range(1, len(bc))]
        self.say("Nothing is compiled at first. Every method starts in the interpreter, "
                 "a loop inside the JVM that reads one bytecode instruction at a time and carries it out.",
                 [(1, [FadeIn(cursor)], 0.3), (1, [Succession(*steps)], 2.6)])

        vt = ValueTracker(0)
        anchor = Dot(radius=0.001).move_to(LEFT * 2.9 + DOWN * 3.0)
        counter = always_redraw(lambda: VGroup(T("calls", 24, GREY_B), M(f"{int(vt.get_value()):,}", 26)).arrange(RIGHT, buff=0.3).move_to(anchor))
        self.add(anchor, counter)
        self.say("Meanwhile the JVM counts the calls, and the jumps back to the top of each loop.",
                 [(0, [Succession(*[cursor.animate(run_time=0.2).next_to(bc[k % 12], LEFT, buff=0.15) for k in range(12)]),
                       vt.animate(run_time=2.4, rate_func=linear).set_value(120)], 2.4)])

        # --- the tier ladder
        t0 = card("interpreter", "tier 0, counts", INT_C, w=3.3).move_to(LEFT * 4.6 + UP * 1.9)
        t3 = card("C1 + profile", "tier 3, about 200 calls", C1_C, w=3.3).move_to(UP * 1.9)
        t4 = card("C2", "tier 4, 5,000 more calls", C2_C, w=3.3).move_to(RIGHT * 4.6 + UP * 1.9)
        a03 = arrow(t0.get_right(), t3.get_left(), GREY_B, buff=0.1)
        a34 = arrow(t3.get_right(), t4.get_left(), GREY_B, buff=0.1)
        meth = chip("settle", WHITE, 26, mono=True).next_to(t0, DOWN, buff=0.35)
        self.play(FadeOut(VGroup(src, bcg, cursor)), FadeIn(t0), FadeIn(meth),
                  anchor.animate.next_to(meth, DOWN, buff=0.35), run_time=0.8)

        self.say("At about 200, a compiler thread compiles the method with C1, in the background. "
                 "C1 is quick, and optimizes a little.",
                 [(0, [vt.animate(rate_func=linear).set_value(200)], 0.9),
                  (0, [GrowArrow(a03), FadeIn(t3), meth.animate.next_to(t3, DOWN, buff=0.35),
                       anchor.animate.move_to(t3.get_bottom() + DOWN * 1.27)], 1.0)])

        profg = listing("the profile, recorded by tier 3", ["call at 20:   Card, 100%", "branch at 31: refund never taken"],
                        label_color=C1_C).move_to(LEFT * 3.4 + DOWN * 2.2)
        prof_h, prof = profg[0], profg[1]
        self.say("Its code also records a profile: which way each branch went, and which receiver types reached each call.",
                 [(0, [FadeIn(prof_h)], 0.5), (0, [FadeIn(prof[1], shift=UP * 0.1)], 0.7), (0, [FadeIn(prof[0], shift=UP * 0.1)], 0.7)])

        self.say("About 5,000 calls later, C2 compiles it again, slowly and hard, from that profile. "
                 "The JVM raises these thresholds when the compile queues are long, so treat them as orders of magnitude.",
                 [(0, [vt.animate(rate_func=linear).set_value(5200)], 1.2),
                  (0, [GrowArrow(a34), FadeIn(t4), meth.animate.next_to(t4, DOWN, buff=0.35),
                       anchor.animate.move_to(t4.get_bottom() + DOWN * 1.27)], 1.0)])

        betsg = listing("C2's bets", ["Card?        inline Card.feeCents", "not a Card?  uncommon trap", "refund?      uncommon trap"],
                        label_color=C2_C).move_to(RIGHT * 3.5 + DOWN * 2.05)
        bets_h, bets = betsg[0], betsg[1]
        counter.clear_updaters()
        self.play(FadeOut(counter), run_time=0.3)
        self.say("C2 bets on the profile. Every receiver was a Card, so it inlines Card's feeCents behind a cheap class check. "
                 "The refund branch never ran, so C2 leaves it out, and puts an uncommon trap there.",
                 [(0, [FadeIn(bets_h)], 0.5), (1, [FadeIn(bets[0], shift=UP * 0.1)], 0.6), (1, [FadeIn(bets[1], shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(bets[2], shift=UP * 0.1)], 0.6)])

        # --- a lost bet (perf-02): deoptimize
        deopt = CurvedArrow(t4.get_bottom() + LEFT * 1.0 + DOWN * 0.05, t0.get_bottom() + RIGHT * 1.0 + DOWN * 0.05,
                            angle=-0.5, color=TRAP_C, stroke_width=4)
        d_lab = T("deoptimize", 26, TRAP_C).move_to(DOWN * 0.15)
        self.say("Then a refund arrives. The trap fires, and the JVM deoptimizes. "
                 "It rebuilds an interpreter frame from the compiled one, and carries on there.",
                 [(0, [bets[2].animate.set_color(TRAP_C), prof[1].animate.set_color(TRAP_C)], 0.6),
                  (1, [Flash(meth, color=TRAP_C, flash_radius=0.9)], 0.6),
                  (1, [Create(deopt), FadeIn(d_lab), meth.animate.next_to(t0, DOWN, buff=0.35)], 1.2)])

        logg = listing("the JDK 25 log, trimmed", ["settle(...)  trap_bci=31 unstable_if",
                                                   "settle (62 bytes)  made not entrant: uncommon trap"]).move_to(DOWN * 2.2)
        log_h, log = logg[0], logg[1]
        log[0].set_color(GREY_B)
        log[1].set_color(TRAP_C)
        self.say("The C2 code is made not entrant. The method profiles again, now with refunds, and gets compiled again.",
                 [(0, [FadeOut(profg), FadeOut(betsg), FadeOut(deopt), FadeOut(d_lab), t4.animate.set_opacity(0.4), FadeIn(logg)], 0.9),
                  (1, [meth.animate.next_to(t3, DOWN, buff=0.35)], 0.9),
                  (1, [meth.animate.next_to(t4, DOWN, buff=0.35), t4.animate.set_opacity(1)], 0.9)])
        self.say("A burst of this after a deploy is normal. A steady stream, hours after startup, is worth a look.",
                 [(0, [Indicate(log[1], color=TRAP_C, scale_factor=1.03)], 1.0)])
        self.wait(0.8)
