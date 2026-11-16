from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"Byte Buddy", "byte buddy"), (r"super\.settle", "super dot settle"), (r"all-open", "all open")]

GEN_C, YOUR_C, INT_C, LOAD_C, BAD_C = GOLD_M, BLUE_M, GREEN_M, TEAL_M, RED_M
LANES = {"settle": 1.0, "audit": 0.0, "region": -1.0}
GX, GW = -2.1, 2.8
BX, BW = 3.2, 2.6
COL_H = 3.1
IX, IY = 0.6, 2.65
TL_Y = -3.05
SEG = {"before": (-2.1, 1.6), "body": (-0.5, 2.8), "after": (2.3, 1.6)}

N = {
    "p1": "SettlementService has two methods you want timed: settle and audit. Pasting a timer into each one, in every service, gets old fast.",
    "p2": "So you write a subclass. Its settle starts a clock, calls super.settle, and logs the time in a finally block. "
          "super.settle runs your original body, on the same object.",
    "p3": "Every method a subclass overrides is a place to run code before and after yours.",
    "g1": "A framework does this without you writing the class. Byte Buddy builds the bytes of a new class at run time: "
          "a subclass of SettlementService that overrides settle and audit.",
    "g2": "A class loader defines it, with a random suffix in its name on every run. "
          "The framework makes an instance, and your code just sees a SettlementService.",
    "q1": "Now a caller calls settle. What runs first?",
    "c1": "The generated override. It calls an interceptor, and hands it the method being called and a handle to the original.",
    "c2": "The interceptor starts the clock, then calls the handle. That goes through an accessor method Byte Buddy added, "
          "into super.settle, and your body runs.",
    "c3": "When your body returns, the interceptor logs the time and passes your result back to the caller.",
    "f1": "Now call region. It's final, so the subclass couldn't override it. The call goes straight to your body, and nothing times it.",
    "f2": "A final class can't be subclassed at all. In Kotlin, classes and methods are final unless you write open, "
          "so Byte Buddy refuses a plain Kotlin class. The all-open compiler plugin opens the classes you mark.",
    "k1": "In code, you pick the class, the methods to override, and the interceptor. make writes the bytes, and load defines the class. "
          "Kotlin uses the same builder.",
    "r": "The rule: a generated proxy is a subclass written at run time. Its overrides run code before and after yours, "
         "and what it can't override, it can't intercept.",
    "c": "Quick check. A Kotlin class is open, but one of its methods isn't. Is that method timed?",
    "a": "No. It's final, so the subclass can't override it.",
}
PAUSE = {"q1": 1.8, "c": 2.2}


def col(x, w, color):
    return RoundedRectangle(corner_radius=0.15, width=w, height=COL_H, stroke_color=color, stroke_width=3).move_to([x, 0, 0])


def mchip(text, color, x, lane):
    return chip(text, color, 22, mono=True).move_to([x, LANES[lane], 0])


def seg(key, color, text):
    x, w = SEG[key]
    r = Rectangle(width=w, height=0.42, stroke_color=color, stroke_width=2).set_fill(color, 0.22).move_to([x + w / 2, TL_Y, 0])
    return VGroup(r, T(text, 22, color).move_to(r))


def code_block(lines, size=22, color=WHITE):
    """Mono lines stacked, left aligned, keeping leading spaces (Text drops them)."""
    cw = M("0" * 20, size).width / 20
    ms = []
    for ln in lines:
        txt, c = (ln if isinstance(ln, tuple) else (ln, color))
        n = len(txt) - len(txt.lstrip(" "))
        ms.append((M(txt.strip(), size, c), n))
    g = VGroup(*[m for m, _ in ms]).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    for m, n in ms:
        m.shift(RIGHT * n * cw)
    return g


class Cls05Bytebuddy(VoiceScene):
    """cls-05 s0: a framework writes a subclass at run time; its override runs code before and after your method."""

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
        self.title_card("Generated proxies", "a class written at run time, around your methods")

        # --- your class, and a caller
        bcol = col(BX, BW, YOUR_C)
        btit = M("SettlementService", 22, YOUR_C).move_to([BX, -1.95, 0])
        bch = {k: mchip(n, YOUR_C, BX, k) for k, n in [("settle", "settle"), ("audit", "audit"), ("region", "final region")]}
        caller = VGroup(RoundedRectangle(corner_radius=0.12, width=1.1, height=COL_H, stroke_color=WHITE, stroke_width=2.5),
                        T("caller", 26)).move_to([-5.75, 0, 0])
        caller[1].move_to(caller[0])
        tlab = T("time", 22, GREY_B).move_to([-2.8, TL_Y, 0])
        self.say("p1", [(0, [Create(bcol), FadeIn(btit), *[FadeIn(c) for c in bch.values()]], 1.0),
                        (0, [Indicate(bch["settle"][1], color=YOUR_C), Indicate(bch["audit"][1], color=YOUR_C)], 0.9),
                        (1, [FadeIn(caller)], 0.6)])

        # --- by hand: a subclass in front of it
        gcol = col(GX, GW, GEN_C)
        gtit = T("your subclass", 24, GEN_C).move_to([GX, -1.95, 0])
        gch = {k: mchip(k, GEN_C, GX, k) for k in ("settle", "audit")}
        a_in = Arrow([-5.15, LANES["settle"], 0], gch["settle"].get_left() + LEFT * 0.08, buff=0.0, stroke_width=3, color=WHITE,
                     max_tip_length_to_length_ratio=0.15)
        a_sup = Arrow(gch["settle"].get_right(), bch["settle"].get_left(), buff=0.1, stroke_width=3, color=GEN_C,
                      max_tip_length_to_length_ratio=0.12)
        sup_t = M("super.settle", 22, GEN_C).next_to(a_sup, UP, buff=0.12)
        sb, sy, sa = seg("before", GEN_C, "start clock"), seg("body", YOUR_C, "your settle body"), seg("after", GEN_C, "log time")
        self.say("p2", [(0, [Create(gcol), FadeIn(gtit), *[FadeIn(c) for c in gch.values()]], 1.0),
                        (1, [GrowArrow(a_in)], 0.5), (1, [FadeIn(tlab), GrowFromEdge(sb, LEFT)], 0.6),
                        (1, [GrowArrow(a_sup), FadeIn(sup_t)], 0.6), (1, [GrowFromEdge(sy, LEFT), Indicate(bch["settle"][1], color=YOUR_C)], 0.9),
                        (1, [GrowFromEdge(sa, LEFT)], 0.6)])
        one = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=8.5, height=4.4, stroke_color=GREY_B, stroke_width=2), num_dashes=80)
        one.move_to([0.5, -0.45, 0])
        one_t = T("one object", 24, GREY_B).move_to([3.9, 2.05, 0])
        self.say("p3", [(0, [Create(one), FadeIn(one_t)], 0.9), (0, [Indicate(VGroup(gch["settle"], gch["audit"]), color=GEN_C, scale_factor=1.08)], 0.9)])

        # --- Byte Buddy writes the class at run time
        bb = box("Byte Buddy", GEN_C, w=2.2, h=0.8, size=26).move_to([-5.2, 2.6, 0])
        gate = Line([GX - 1.3, 2.05, 0], [GX + 1.3, 2.05, 0], stroke_width=8, color=LOAD_C)
        gate_t = T("class loader", 22, LOAD_C).next_to(gate, RIGHT, buff=0.2)
        self.say("g1", [(0, [FadeOut(VGroup(gcol, gtit, *gch.values(), a_in, a_sup, sup_t, sb, sy, sa, tlab))], 0.7),
                        (1, [FadeIn(bb, shift=RIGHT * 0.2)], 0.6)])
        hexes = VGroup(*[M(h, 22, GEN_C) for h in ["CA", "FE", "BA", "BE", "00", "41"]]).arrange(RIGHT, buff=0.18).next_to(bb, RIGHT, buff=0.25)
        gname = VGroup(M("SettlementService", 22, GEN_C), M("$ByteBuddy$nsokwLlA", 22, GEN_C)).arrange(DOWN, buff=0.06).move_to([GX, -2.1, 0])
        gcol2 = col(GX, GW, GEN_C)
        gch2 = {k: mchip(k, GEN_C, GX, k) for k in ("settle", "audit")}
        self.say("g2", [(0, [LaggedStart(*[FadeIn(h, shift=RIGHT * 0.2) for h in hexes], lag_ratio=0.15), Create(gate), FadeIn(gate_t)], 1.0),
                        (0, [LaggedStart(*[h.animate.move_to(gate.get_center() + RIGHT * (i - 2.5) * 0.4).set_opacity(0) for i, h in enumerate(hexes)],
                                         lag_ratio=0.1)], 1.0),
                        (0, [FadeIn(gcol2, shift=DOWN * 0.3), *[FadeIn(c, shift=DOWN * 0.3) for c in gch2.values()]], 0.8),
                        (0, [FadeIn(gname)], 0.6),
                        (1, [Indicate(gname[1], color=WHITE, scale_factor=1.06)], 0.8)])
        self.play(FadeOut(VGroup(bb, gate, gate_t)), run_time=0.5)
        self.remove(hexes)

        # --- the call: override, interceptor, your body, back
        icpt = VGroup(RoundedRectangle(corner_radius=0.12, width=3.0, height=0.95, stroke_color=INT_C, stroke_width=3).set_fill("#0B160B", 1),
                      T("interceptor", 26, INT_C)).move_to([IX, IY, 0])
        a_in2 = Arrow([-5.15, LANES["settle"], 0], gch2["settle"].get_left() + LEFT * 0.08, buff=0.0, stroke_width=3, color=WHITE,
                      max_tip_length_to_length_ratio=0.15)
        call_t = M("settle()", 22).next_to(a_in2.get_start(), UP, buff=0.12).shift(RIGHT * 0.68)
        self.say("q1", [(0, [GrowArrow(a_in2), FadeIn(call_t)], 0.7)])
        up = CurvedArrow(gch2["settle"].get_right() + RIGHT * 0.05, icpt.get_bottom() + LEFT * 0.6 + DOWN * 0.05, angle=PI / 5, color=INT_C,
                         stroke_width=3, tip_length=0.2)
        hand = VGroup(M("m = settle", 22, INT_C), M("original", 22, INT_C)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        hand.next_to(icpt, LEFT, buff=0.3)
        self.say("c1", [(0, [Indicate(gch2["settle"][1], color=GEN_C, scale_factor=1.15)], 0.6),
                        (1, [FadeIn(icpt, shift=DOWN * 0.15)], 0.5), (1, [Create(up)], 0.7), (1, [FadeIn(hand)], 0.6)])
        tlab2 = T("time", 22, GREY_B).move_to([-2.8, TL_Y, 0])
        sb2, sy2, sa2 = seg("before", GEN_C, "start clock"), seg("body", YOUR_C, "your settle body"), seg("after", GEN_C, "log time")
        sb2[0].set_stroke(INT_C).set_fill(INT_C, 0.22); sb2[1].set_color(INT_C)
        sa2[0].set_stroke(INT_C).set_fill(INT_C, 0.22); sa2[1].set_color(INT_C)
        down = CurvedArrow(icpt.get_bottom() + RIGHT * 0.6 + DOWN * 0.05, bch["settle"].get_left() + LEFT * 0.05, angle=PI / 5, color=YOUR_C,
                           stroke_width=3, tip_length=0.2)
        acc = M("via settle$accessor$...", 22, YOUR_C).move_to([4.15, IY, 0])
        self.say("c2", [(0, [FadeIn(tlab2), GrowFromEdge(sb2, LEFT)], 0.7),
                        (1, [Create(down)], 0.8), (1, [FadeIn(acc)], 0.5),
                        (1, [Indicate(bch["settle"][1], color=YOUR_C, scale_factor=1.15), GrowFromEdge(sy2, LEFT)], 1.2)])
        back = Dot(radius=0.1, color=WHITE).move_to(down.get_end())
        ret_path = down.copy().reverse_points()
        res = M("result", 22).next_to(a_in2.get_start(), DOWN, buff=0.12).shift(RIGHT * 0.68)
        self.say("c3", [(0, [FadeIn(back, run_time=0.1)], 0.1), (0, [MoveAlongPath(back, ret_path)], 0.9),
                        (0, [GrowFromEdge(sa2, LEFT), Indicate(icpt[1], color=INT_C)], 0.8),
                        (0, [back.animate.move_to(a_in2.get_start()), FadeIn(res)], 0.9), (0, [FadeOut(back)], 0.2)])
        # poster moment is here: all three stages drawn

        # --- final members: no override, no interception
        self.play(FadeOut(VGroup(up, down, hand, acc, res, call_t, a_in2, sb2, sy2, sa2)), run_time=0.6)
        gap = DashedVMobject(Rectangle(width=2.2, height=0.44, stroke_color=GREY_B, stroke_width=2), num_dashes=26).move_to([GX, LANES["region"] - 0.05, 0])
        gap_t = T("no override", 22, GREY_B).move_to([GX, -0.58, 0])
        a_reg = Arrow([-5.15, LANES["region"], 0], bch["region"].get_left() + LEFT * 0.08, buff=0.0, stroke_width=3, color=WHITE,
                      max_tip_length_to_length_ratio=0.06)
        reg_t = M("region()", 22).next_to(a_reg.get_start(), UP, buff=0.12).shift(RIGHT * 0.68)
        only = seg("body", YOUR_C, "your region body")
        untimed = T("nothing timed", 22, GREY_B).move_to([2.6 + 0.0, TL_Y, 0]).shift(RIGHT * 0.15)
        untimed.next_to(only, RIGHT, buff=0.25)
        self.say("f1", [(0, [Indicate(bch["region"][1], color=YOUR_C, scale_factor=1.1)], 0.7),
                        (1, [FadeIn(gap), FadeIn(gap_t)], 0.6),
                        (2, [GrowArrow(a_reg), FadeIn(reg_t)], 0.9), (2, [GrowFromEdge(only, LEFT)], 0.8),
                        (2, [FadeIn(untimed)], 0.5)])

        # --- a final class: no subclass at all (Kotlin's default)
        self.play(FadeOut(VGroup(gap, gap_t, a_reg, reg_t, only, untimed, tlab2)), run_time=0.5)
        fin = VGroup(M("final class", 22, BAD_C), M("SettlementService", 22, BAD_C)).arrange(DOWN, buff=0.06).move_to([BX, -2.1, 0])
        cross = tick(False, 0.6).move_to([GX, 0, 0])
        err = M("Cannot subclass primitive, array or final types", 22, BAD_C).move_to([0.5, TL_Y, 0])
        kt = T("Kotlin: classes and methods are final unless you write open", 26).move_to([0.5, 2.65, 0])
        fit(kt, 12.0)
        ao = T("all-open compiler plugin: opens the classes you mark", 26, INT_C).move_to([0.5, 2.65, 0])
        fit(ao, 12.0)
        self.say("f2", [(0, [FadeOut(icpt), FadeOut(one_t), Transform(btit, fin)], 0.7),
                        (0, [gcol2.animate.set_stroke(BAD_C), *[c.animate.set_opacity(0.35) for c in gch2.values()], Create(cross)], 0.8),
                        (1, [FadeIn(kt, shift=DOWN * 0.1)], 0.7), (1, [FadeIn(err)], 0.6),
                        (2, [FadeOut(kt), FadeIn(ao, shift=DOWN * 0.1)], 0.7)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # --- the code (stacked: the builder lines are long)
        jl = VGroup(T("Java", 24, GREY_B), code_block([
            "Class<?> proxy = new ByteBuddy()",
            ("    .subclass(SettlementService.class)", GEN_C),
            ("    .method(isDeclaredBy(SettlementService.class))", GEN_C),
            ("    .intercept(MethodDelegation.to(new Timing()))", INT_C),
            "    .make().load(loader).getLoaded();"])).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        kl = VGroup(T("Kotlin", 24, GREY_B), code_block([
            "val proxy = ByteBuddy()",
            ("    .subclass(SettlementService::class.java)", GEN_C),
            ("    .method(isDeclaredBy(SettlementService::class.java))", GEN_C),
            ("    .intercept(MethodDelegation.to(Timing()))", INT_C),
            "    .make().load(loader).loaded"])).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        stack = VGroup(jl, kl).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(stack, 12.4).move_to([0, 0.15, 0])
        self.say("k1", [(0, [FadeIn(jl[0]), FadeIn(jl[1][0]), FadeIn(jl[1][1])], 0.7), (0, [FadeIn(jl[1][2])], 0.5), (0, [FadeIn(jl[1][3])], 0.5),
                        (1, [Indicate(jl[1][4], color=WHITE, scale_factor=1.04)], 0.8), (1, [FadeIn(kl, shift=UP * 0.1)], 0.8)])
        self.wait(1.2)
        self.play(FadeOut(stack), run_time=0.5)

        # --- rule and check
        rule = VGroup(T("A generated proxy is a subclass written at run time.", 32),
                      T("Its overrides run code before and after yours;", 32, GEN_C),
                      T("what it can't override, it can't intercept.", 32, GEN_C)).arrange(DOWN, buff=0.2).move_to([0, 1.6, 0])
        fit(rule, 12.4)
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1:], shift=UP * 0.1)], 0.8)])
        chk = T("Check: a Kotlin class is open, but one method isn't. Is it timed?", 28).move_to([0, -0.9, 0])
        fit(chk, 12.4)
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("No. It's final, so the subclass can't override it.", 28, GEN_C).move_to([0, -2.2, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)
