from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\brequireAmount\b", "require amount"), (r"Long\.bitCount", "Long dot bit count"), (r"\bcountOneBits\b", "count one bits"),
           (r"\bPOPCNT\b", "pop count"), (r"inline \(hot\)", "inline hot"), (r"\bx86\b", "x 86"), (r"\b1200\b", "twelve hundred"),
           (r"\bbytecode\b", "byte code")]

_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

CALLER, CALLEE, C2_C = BLUE_M, PURPLE_M, GOLD_M     # settle, the helper it calls, what C2 sees
HOT_C, COLD_C, BAD_C, OK_C, INTR_C = GOLD_M, TEAL_M, RED_M, GREEN_M, YELLOW_M

N = {
    "s1": "C2 is compiling a hot method, settle. It calls a small helper, requireAmount.",
    "s2": "To C2, a call is a wall: it can't see what happens inside.",
    "q1": "Say settle always passes 1200, and the helper checks that the amount is in range. Can C2 skip the check?",
    "s3": "Not through the wall. The check runs on every call.",
    "s4": "Inlining removes the wall. C2 pastes the helper's body into settle, and compiles them as one piece.",
    "s5": "Now C2 sees 1200 meet the range check, and drops the check at compile time. That's constant folding.",
    "s6": "Saving the call is the small win. The big one: escape analysis and loop unrolling now see both sides. "
          "That's why inlining comes first.",
    "s8": "But each call site gets a budget, in bytes of bytecode. A site that runs on a quarter or more of the caller's calls "
          "is hot: 325 bytes. Any other site gets 35.",
    "q2": "This guard checks a refund amount, and builds its error message inline: 49 bytes. Its site runs on 1 call in 8. "
          "Will C2 inline it?",
    "s9": "No. 49 is over 35, and the budget counts the message bytes, though they almost never run.",
    "s10": "Move the message into its own method. The guard drops to 21 bytes, and fits.",
    "s11": "Here is C2's real log. inline (hot) is just how it says yes.",
    "s12": "Some JDK methods skip the budget. Long.bitCount is 61 bytes of shifts and masks, but on x86 C2 uses one POPCNT instruction.",
    "s13": "These are intrinsics: JDK methods the JIT swaps for hand-written code, so their bytecode size doesn't matter.",
    "s14": "In code, the guard calls out for its message. And Kotlin's countOneBits calls Long.bitCount, the same intrinsic.",
    "r": "The rule. Inlining lets C2 see through calls, within 35 bytes, or 325 at a hot site. Keep cold paths out, and call the JDK method.",
    "c": "Quick check. A 40-byte method: is it inlined from a site that runs on half the caller's calls? From one that runs on 1 call in 10?",
    "a": "Yes at the hot site: 40 is under 325. No at the other: 40 is over 35.",
}
PAUSE = {"q1": 1.5, "q2": 1.5, "c": 2.2}


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
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


def shade(c, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def frame_box(w, h, color, k=0.1):
    return RoundedRectangle(corner_radius=0.16, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(shade(color, k), 1)


def bar(x0, x1, y, h, color, k=0.45):
    return Rectangle(width=max(0.02, x1 - x0), height=h, stroke_color=color, stroke_width=2).set_fill(shade(color, k), 1).move_to([(x0 + x1) / 2, y, 0])


class Perf02Inlining(VoiceScene):
    """perf-02 section 0 (with section 3): a call is a wall to C2; inlining removes it so the other optimizations see both
    sides; a bytecode budget (35 / 325 bytes) decides which calls get inlined; intrinsics replace JDK methods outright."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def say(self, key, plan=(), after=0.25):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        now = 0.0
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
        self.title_card("Why inlining comes first", "the JIT's size budget, and intrinsics")

        # ---------- a call is a wall
        cb = frame_box(5.3, 3.2, CALLER).move_to([-3.45, -0.1, 0])
        ct = M("settle", 30, CALLER).move_to(cb.get_top() + DOWN * 0.42)
        RY = [0.4, -0.35, -1.1]
        r1 = T("load a payment", 28, GREY_A).move_to([-3.45, RY[0], 0])
        r2 = one("requireAmount(1200)", 26, CALLEE).move_to([-3.45, RY[1], 0])
        r3 = T("add it to net", 28, GREY_A).move_to([-3.45, RY[2], 0])
        hb = frame_box(5.0, 3.2, CALLEE).move_to([3.6, -0.1, 0])
        ht = M("requireAmount", 30, CALLEE).move_to(hb.get_top() + DOWN * 0.42)
        c1 = T("is cents in range?", 28).move_to([3.6, RY[0], 0])
        c2 = T("no: throw", 28, GREY_A).move_to([3.6, RY[1], 0])
        c3 = T("yes: return cents", 28, GREY_A).move_to([3.6, RY[2], 0])
        self.say("s1", [(0, [FadeIn(cb), FadeIn(ct), FadeIn(r1), FadeIn(r3)], 0.8),
                        (1, [FadeIn(r2)], 0.5), (1, [FadeIn(hb), FadeIn(ht), FadeIn(VGroup(c1, c2, c3))], 0.8)])

        wall = Rectangle(width=0.28, height=3.9, stroke_width=0).set_fill(GREY_D, 1).move_to([0.2, -0.1, 0]).set_z_index(2)
        wall_l = T("a call: C2 can't see inside", 28, GREY_B).move_to([0.2, 2.45, 0])
        call = DashedLine(r2.get_right() + RIGHT * 0.12, [hb.get_left()[0] - 0.05, RY[1], 0], dash_length=0.12, stroke_width=3,
                          color=CALLEE).add_tip(tip_length=0.18, tip_width=0.18)
        self.say("s2", [(0, [Create(call)], 0.6), (0, [GrowFromEdge(wall, DOWN), FadeIn(wall_l)], 0.8),
                        (0, [Indicate(c1, color=CALLEE, scale_factor=1.06)], 0.8)])

        amt = chip("1200", CALLEE, 26, mono=True).move_to(part(r2, "1200"))
        self.say("q1", [(0, [FadeIn(amt, scale=0.7)], 0.5), (0, [Indicate(c1, color=WHITE, scale_factor=1.08)], 0.8),
                        (1, [amt.animate.move_to([-0.45, RY[1], 0])], 0.9)])
        self.say("s3", [(0, [amt.animate.shift(LEFT * 0.35), Flash([0.0, RY[1], 0], color=BAD_C, flash_radius=0.45)], 0.5),
                        (1, [c1.animate.set_color(BAD_C)], 0.4), (1, [Circumscribe(c1, color=BAD_C, buff=0.12)], 1.0)])

        # ---------- inlining: the wall goes, the body moves in
        big = frame_box(6.6, 4.3, C2_C, 0.08).move_to([0, -0.35, 0])
        big_t = M("settle", 30, CALLER).move_to(big.get_top() + DOWN * 0.42)
        NY = [0.75, 0.1, -0.55, -1.2, -1.85]
        one_l = T("one piece for C2", 26, C2_C).next_to(big, UP, buff=0.15).align_to(big, RIGHT)
        self.say("s4", [(0, [FadeOut(wall), FadeOut(wall_l), FadeOut(call), FadeOut(amt), c1.animate.set_color(WHITE)], 0.6),
                        (1, [ReplacementTransform(cb, big), ReplacementTransform(ct, big_t), FadeOut(hb), FadeOut(ht), FadeOut(r2),
                             r1.animate.move_to([0, NY[0], 0]), c1.animate.move_to([0, NY[1], 0]).set_color(CALLEE),
                             c2.animate.move_to([0, NY[2], 0]).set_color(CALLEE), c3.animate.move_to([0, NY[3], 0]).set_color(CALLEE),
                             r3.animate.move_to([0, NY[4], 0])], 1.6),
                        (1, [FadeIn(one_l)], 0.5)])

        c1b = T("is 1200 in range? always yes", 28, OK_C).move_to([0, NY[1], 0])
        c3b = M("1200", 30, CALLEE).move_to([0, NY[3], 0])
        fold = T("constant folding", 34, INTR_C).move_to([0, 2.75, 0])
        self.say("s5", [(0, [Transform(c1, c1b)], 0.8),
                        (0, [c2.animate.set_opacity(0.25), Transform(c3, c3b)], 0.7),
                        (0, lambda: [FadeOut(c1), FadeOut(c2), r1.animate.move_to([0, 0.35, 0]), c3.animate.move_to([0, -0.5, 0]),
                                     r3.animate.move_to([0, -1.35, 0])], 0.9),
                        (1, [Write(fold)], 0.9)])

        opts = VGroup(chip("constant folding", INTR_C, 26), chip("escape analysis", INTR_C, 26), chip("loop unrolling", INTR_C, 26)
                      ).arrange(RIGHT, buff=0.35).move_to([0, 2.75, 0])
        first = T("inlining comes first", 36, C2_C).move_to([0, -3.0, 0])
        self.say("s6", [(1, [ReplacementTransform(fold, opts[0]), FadeIn(opts[1:], shift=DOWN * 0.1)], 0.9),
                        (1, [Indicate(big, color=C2_C, scale_factor=1.02)], 0.8),
                        (2, [FadeIn(first, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(big, big_t, r1, c3, r3, one_l, opts, first)), run_time=0.6)

        # ---------- the budget, on one scale: 0 .. 350 bytes
        X0 = -5.6
        k1 = 11.2 / 350
        head = T("budget per call site, in bytes of bytecode", 32).move_to([0, 2.8, 0])
        base = Line([X0, 2.1, 0], [X0, -2.4, 0], stroke_width=2, color=GREY_D)
        HY, CY = 0.9, -0.75
        hot_b = bar(X0, X0 + 325 * k1, HY, 0.55, HOT_C)
        hot_v = M("325", 30, HOT_C).next_to(hot_b, RIGHT, buff=0.15)
        hot_l = T("hot site: runs on 25% or more of the caller's calls", 26, HOT_C).next_to(hot_b, UP, buff=0.18).align_to(hot_b, LEFT)
        cold_b = bar(X0, X0 + 35 * k1, CY, 0.55, COLD_C)
        cold_v = M("35", 30, COLD_C).next_to(cold_b, RIGHT, buff=0.15)
        cold_l = T("any other call site", 26, COLD_C).next_to(cold_b, UP, buff=0.18).align_to(cold_b, LEFT)
        self.say("s8", [(0, [FadeIn(head, shift=DOWN * 0.1), Create(base)], 0.8),
                        (1, [FadeIn(hot_l), GrowFromEdge(hot_b, LEFT)], 1.2), (1, [FadeIn(hot_v)], 0.4),
                        (2, [FadeIn(cold_l), GrowFromEdge(cold_b, LEFT)], 0.7), (2, [FadeIn(cold_v)], 0.4)])

        # zoom in: 0 .. 70 bytes
        k2 = 11.2 / 70
        LIM = X0 + 35 * k2
        CY2, GY = 1.25, -0.35
        cold2 = bar(X0, LIM, CY2, 0.55, COLD_C)
        cold_l2 = T("this call site: 1 call in 8, limit 35", 26, COLD_C).next_to(cold2, UP, buff=0.18).align_to(cold2, LEFT)
        lim = DashedLine([LIM, 1.55, 0], [LIM, -1.3, 0], dash_length=0.12, stroke_width=3, color=COLD_C)
        lim_v = M("35", 28, COLD_C).next_to(cold2, RIGHT, buff=0.15)
        g49 = bar(X0, X0 + 49 * k2, GY, 0.7, CALLEE)
        g49_l = T("the guard, with its message inline: 49 bytes", 26, CALLEE).next_to(g49, UP, buff=0.18).align_to(g49, LEFT)
        g49_l.add_background_rectangle(color=BLACK, opacity=1, buff=0.06).set_z_index(2)
        self.play(FadeOut(VGroup(hot_b, hot_v, hot_l, head)), ReplacementTransform(cold_b, cold2), ReplacementTransform(cold_l, cold_l2),
                  ReplacementTransform(cold_v, lim_v), run_time=1.0)
        self.say("q2", [(0, [Create(lim)], 0.5), (0, [FadeIn(g49_l), GrowFromEdge(g49, LEFT)], 1.0),
                        (1, [Indicate(cold_l2, color=COLD_C, scale_factor=1.04)], 0.8)])

        over = bar(LIM, X0 + 49 * k2, GY, 0.7, BAD_C, 0.5).set_z_index(1)
        big_l = T("too big", 30, BAD_C).next_to(g49, RIGHT, buff=0.3)
        self.say("s9", [(0, [FadeIn(over), FadeIn(big_l)], 0.6)])

        g21 = bar(X0, X0 + 21 * k2, GY, 0.7, CALLEE)
        g21_l = T("the guard, message moved out: 21 bytes", 26, CALLEE).next_to(g21, UP, buff=0.18).align_to(g21, LEFT)
        g21_l.add_background_rectangle(color=BLACK, opacity=1, buff=0.06).set_z_index(2)
        fits = VGroup(tick(True, 0.22), T("inlined", 28, OK_C)).arrange(RIGHT, buff=0.15).next_to(g21, RIGHT, buff=0.2)
        cold_m = VGroup(frame_box(4.6, 1.1, GREY_M), M("badAmount(cents)", 26, GREY_A))
        cold_m[1].move_to(cold_m[0])
        cold_m.move_to([3.6, -1.75, 0])
        cold_n = T("its own method, rarely runs", 24, GREY_B).next_to(cold_m, UP, buff=0.12)
        self.say("s10", [(0, [FadeOut(over), FadeOut(big_l), ReplacementTransform(g49, g21), ReplacementTransform(g49_l, g21_l),
                              FadeIn(cold_m, shift=DOWN * 0.2), FadeIn(cold_n)], 1.2),
                         (1, [FadeIn(fits, shift=LEFT * 0.1)], 0.6)])

        log = VGroup(one("@ 15   ...InliningDemo::requireAmountInline (49 bytes)   too big", 22, GREY_A),
                     one("@ 30   ...InliningDemo::requireAmountSplit (21 bytes)   inline (hot)", 22, GREY_A)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        part(log[0], "too big").set_color(BAD_C)
        part(log[1], "inline (hot)").set_color(OK_C)
        fit(log, 12.4).move_to([0, -3.0, 0])
        self.say("s11", [(0, [cold_m.animate.shift(UP * 0.15), cold_n.animate.shift(UP * 0.15), FadeIn(log, shift=UP * 0.1)], 0.8),
                         (1, [mark(part(log[1], "inline (hot)"), OK_C, 0.6)], 1.3)])
        self.play(FadeOut(VGroup(base, cold2, cold_l2, lim, lim_v, g21, g21_l, fits, cold_m, cold_n, log)), run_time=0.6)

        # ---------- intrinsics: the Java code is not what runs
        jb = frame_box(5.0, 3.3, GREY_B, 0.06).move_to([-3.4, 0.3, 0])
        jt = M("Long.bitCount", 30).move_to(jb.get_top() + DOWN * 0.42)
        widths = [3.6, 4.1, 3.3, 2.6, 2.6, 2.6, 2.0]
        lines = VGroup(*[Rectangle(width=w, height=0.16, stroke_width=0).set_fill(GREY_M, 0.8) for w in widths]
                       ).arrange(DOWN, buff=0.17, aligned_edge=LEFT).move_to(jb.get_center() + DOWN * 0.3).align_to(jb, LEFT).shift(RIGHT * 0.45)
        jn = T("Java: 61 bytes of shifts and masks", 26, GREY_B).next_to(jb, DOWN, buff=0.25)
        pop = chip("POPCNT", INTR_C, 40, mono=True).move_to([3.4, 0.3, 0])
        pn = T("one x86 instruction", 26, INTR_C).next_to(pop, DOWN, buff=0.3)
        sw = Arrow(jb.get_right() + RIGHT * 0.15, pop.get_left() + LEFT * 0.15, buff=0, stroke_width=4, color=INTR_C,
                   max_tip_length_to_length_ratio=0.12)
        sw_l = T("C2 swaps it", 26, INTR_C).next_to(sw, UP, buff=0.15)
        self.say("s12", [(0, [FadeIn(jb), FadeIn(jt)], 0.6),
                         (1, [LaggedStart(*[GrowFromEdge(l, LEFT) for l in lines], lag_ratio=0.15), FadeIn(jn)], 1.2),
                         (1, [GrowArrow(sw), FadeIn(sw_l)], 0.6),
                         (1, [ReplacementTransform(lines.copy(), pop), FadeIn(pn)], 1.0)])

        name = T("intrinsic: a JDK method the JIT swaps for hand-written code", 30, INTR_C).move_to([0, 2.75, 0])
        fit(name, 12.4)
        ilog = VGroup(one("java.lang.Long::bitCount (61 bytes)   (intrinsic)", 24, GREY_A),
                      one("java.lang.Math::addExact (32 bytes)   (intrinsic)", 24, GREY_A),
                      one("java.util.Arrays::equals (43 bytes)   (intrinsic)", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        for l in ilog:
            part(l, "(intrinsic)").set_color(INTR_C)
        ilog.move_to([0, -2.55, 0])
        self.say("s13", [(0, [FadeIn(name, shift=DOWN * 0.1)], 0.8),
                         (0, [FadeIn(ilog, shift=UP * 0.1)], 0.8), (0, [lines.animate.set_opacity(0.25)], 0.6)])
        self.play(FadeOut(VGroup(jb, jt, lines, jn, pop, pn, sw, sw_l, name, ilog)), run_time=0.6)

        # ---------- the code, as a check of the picture
        jl = code(["if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents);",
                   "int flags = Long.bitCount(riskMask);"], 24)
        kl = code(["if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents)",
                   "val flags = riskMask.countOneBits()"], 24)
        for l in (jl, kl):
            part(l[0], "badAmount(cents)").set_color(GREY_B)
        part(jl[1], "Long.bitCount").set_color(INTR_C)
        part(kl[1], "countOneBits()").set_color(INTR_C)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.7, aligned_edge=LEFT).move_to([0, 0.1, 0])
        fit(both, 12.4)
        self.say("s14", [(0, [FadeIn(jg, shift=UP * 0.15), FadeIn(kg, shift=UP * 0.15)], 0.8),
                         (0, [mark(part(jl[0], "throw badAmount(cents)"), GREY_B, 0.4), mark(part(kl[0], "throw badAmount(cents)"), GREY_B, 0.4)], 1.2),
                         (1, [mark(part(kl[1], "countOneBits()"), INTR_C, 0.4), mark(part(jl[1], "Long.bitCount"), INTR_C, 0.4)], 1.2)])
        self.play(FadeOut(both), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("Inlining lets C2 see through a call.", 32),
                      T("Budget: 35 bytes, or 325 at a hot call site.", 32, HOT_C),
                      T("Keep cold paths out. Call the JDK method.", 32, INTR_C)).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7),
                       (2, [FadeIn(rule[2], shift=UP * 0.1)], 0.7)])
        chk = VGroup(T("Check: a 40-byte method. Inlined from a site that runs on half", 28),
                     T("the caller's calls? From one that runs on 1 call in 10?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.85, 0])
        fit(chk, 12.4)
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = VGroup(T("hot site: yes, 40 < 325", 30, OK_C), T("other site: no, 40 > 35", 30, BAD_C)).arrange(RIGHT, buff=1.2).move_to([0, -2.6, 0])
        self.say("a", [(0, [FadeIn(ans[0], shift=UP * 0.1)], 0.6), (1, [FadeIn(ans[1], shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
