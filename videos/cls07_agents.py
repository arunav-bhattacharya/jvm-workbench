from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"-javaagent", "dash java agent"), (r"\bpremain\b", "pre-main"), (r"\bagentmain\b", "agent main"),
           (r"ClassFileTransformer", "class file transformer"), (r"retransformClasses", "re-transform classes"),
           (r"[Rr]etransformation", lambda m: m.group(0)[0] + "e-transformation"), (r"\bretransforms\b", "re-transforms"),
           (r"IssuerClient", "issuer client"), (r"120 ms", "120 milliseconds"), (r"card-issuer", "card issuer")]

AG_C, LOAD_C, JVM_C, OBJ_C, BAD_C = GOLD_M, TEAL_M, BLUE_M, PURPLE_M, RED_M

N = {
    "p1": "The card-issuer API takes 120 ms, and you want to time the client method that calls it. "
          "But that client lives in a library jar you can't recompile.",
    "p2": "A proxy won't do. It needs an interface or an open class, and it only wraps objects you create.",
    "m1": "Every class reaches the JVM as bytes from a jar. A class loader hands them over, and the JVM defines the class.",
    "m2": "Start the JVM with -javaagent, and before your main runs, it calls the agent's premain method.",
    "m3": "premain registers a ClassFileTransformer. From then on, the JVM passes it the bytes of every class it's about to define.",
    "m4": "It returns new bytes, or null for no change. Here it adds timing code to IssuerClient, and leaves the rest alone.",
    "q1": "Now take a service that has run for an hour. A tool attaches an agent, and the JVM calls its agentmain. "
          "IssuerClient loaded long ago. Will the new transformer ever see it?",
    "a1": "No. A transformer only sees classes defined after it's registered, and nothing defines IssuerClient again.",
    "r1": "So the agent calls retransformClasses. The JVM runs the transformers again on the class's current bytes, "
          "and puts the new method bodies into the same Class object.",
    "r2": "Objects made at startup run the new code on their next call. A call that was already running finishes on the old code.",
    "l1": "One limit: only method bodies may change. Retransformation must not add, remove or rename fields or methods, "
          "or change signatures, modifiers or inheritance. So a call counter can't be a new field. It lives in another class.",
    "k1": "In code, that's two calls, the same in Java and in Kotlin, and the agent's manifest must allow it.",
    "r": "The rule: a transformer sees each class's bytes as the JVM defines it. "
         "Retransformation swaps method bodies in place, for every object, but never the class's shape.",
    "c": "Quick check. An agent retransforms IssuerClient while a thread is inside its method. Which code does that thread finish on?",
    "a": "The old code. Its next call runs the new one.",
}
PAUSE = {"q1": 2.2, "c": 2.4}

BELT_Y = -0.1
SLOTS = [0.9, -0.1, -1.1]
GATE_X = 0.4


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def cls_chip(name, color=WHITE):
    return chip(name, color, 22, mono=True)


class Cls07Agents(VoiceScene):
    """cls-07 s0-s1: an agent's ClassFileTransformer sees class bytes as they are defined; retransformation swaps bodies in place."""

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
        self.title_card("Changing classes you can't recompile", "Java agents and class file transformers")

        # --- the problem: a slow method in a jar you can't rebuild
        jar = RoundedRectangle(corner_radius=0.15, width=5.0, height=2.6, stroke_color=GREY_B, stroke_width=2.5).set_fill("#101010", 1)
        jar.move_to([1.2, 0.2, 0])
        jar_t = T("issuer-client.jar: a library", 26, GREY_B).next_to(jar, UP, buff=0.15).align_to(jar, LEFT)
        ic = VGroup(M("IssuerClient", 30), T("calls the card-issuer API", 24, GREY_B)).arrange(DOWN, buff=0.2).move_to(jar)
        api = box("120 ms", BAD_C, w=1.8, h=0.8, size=28).move_to([5.4, 0.2, 0])
        mine = box("your code", WHITE, w=2.4, h=0.8, size=28).move_to([-4.6, 0.2, 0])
        a1 = arrow(mine.get_right(), jar.get_left(), GREY_B, buff=0.1)
        a2 = arrow(jar.get_right(), api.get_left(), GREY_B, buff=0.1)
        lock = T("no source, no rebuild", 26, BAD_C).next_to(jar, DOWN, buff=0.3)
        self.say("p1", [(0, [FadeIn(mine), FadeIn(jar), FadeIn(jar_t), FadeIn(ic)], 0.9), (0, [GrowArrow(a1), GrowArrow(a2), FadeIn(api)], 0.8),
                        (1, [FadeIn(lock, shift=UP * 0.1)], 0.6)])
        prox = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=5.6, height=3.9, stroke_color=PURPLE_M, stroke_width=3), num_dashes=50)
        prox.move_to(jar)
        prox_t = T("a proxy around it?", 26, PURPLE_M).next_to(prox, DOWN, buff=0.2)
        pn = VGroup(T("needs an interface or an open class", 24, GREY_B), T("wraps only objects you create", 24, GREY_B)).arrange(DOWN, buff=0.12)
        pn.move_to([1.2, -2.95, 0])
        x = tick(False, 0.35).move_to(prox.get_corner(UR))
        self.say("p2", [(0, [FadeOut(lock), Create(prox), FadeIn(prox_t)], 0.9), (1, [FadeIn(pn)], 0.7), (1, [Create(x)], 0.5)])
        self.play(FadeOut(VGroup(jar, jar_t, ic, api, mine, a1, a2, prox, prox_t, pn, x)), run_time=0.6)

        # --- the path every class takes: jar, class loader, JVM
        appjar = box("app.jar", GREY_B, w=1.7, h=1.0, size=26).move_to([-5.55, BELT_Y, 0])
        belt = Line([-4.7, BELT_Y, 0], [2.8, BELT_Y, 0], stroke_width=3, color=GREY_D)
        tunnel = Rectangle(width=2.6, height=1.0, stroke_color=LOAD_C, stroke_width=3).move_to([-3.0, BELT_Y, 0])
        tunnel_t = T("class loader", 26, LOAD_C).next_to(tunnel, UP, buff=0.15)
        jvm = RoundedRectangle(corner_radius=0.15, width=3.6, height=3.8, stroke_color=JVM_C, stroke_width=3).set_fill(shade(JVM_C, 0.06), 1)
        jvm.move_to([4.6, -0.2, 0])
        jvm_t = T("JVM: defined classes", 26, JVM_C).next_to(jvm, UP, buff=0.15)
        names = ["Clock", "SettlementJob", "IssuerClient"]
        chips = [cls_chip(n).move_to([-3.0, BELT_Y, 0]) for n in names]
        for c in chips:
            c.set_z_index(3)
        tunnel.set_z_index(4)
        shelf = [cls_chip(n).move_to([4.6, y, 0]) for n, y in zip(names, SLOTS)]

        def flow(i, through_gate=None):
            """Chip i rides from the jar to its shelf slot (optionally changed at the gate)."""
            c = chips[i]
            steps = [FadeIn(c, target_position=appjar.get_right(), scale=0.3, run_time=0.5), c.animate(run_time=0.8).move_to([GATE_X - 1.3, BELT_Y, 0])]
            if through_gate is not None:
                steps += through_gate
            steps.append(c.animate(run_time=0.7).move_to([4.6, SLOTS[i], 0]))
            return Succession(*steps)

        self.say("m1", [(0, [FadeIn(appjar), Create(belt), FadeIn(jvm), FadeIn(jvm_t)], 0.9),
                        (1, [FadeIn(tunnel), FadeIn(tunnel_t)], 0.5), (1, [flow(0)], 1.9)])

        cmd = M("java -javaagent:agent.jar -jar app.jar", 24, AG_C).move_to([-2.4, 2.85, 0])
        pre = chip("premain(args, inst)", AG_C, 24, mono=True).move_to([-2.4, 1.9, 0])
        mainc = chip("main(args)", GREY_B, 24, mono=True).move_to([1.4, 1.9, 0])
        pm = arrow(pre.get_right(), mainc.get_left(), GREY_B, buff=0.12)
        self.say("m2", [(0, [FadeIn(cmd, shift=DOWN * 0.1)], 0.7), (0, [FadeIn(pre, shift=DOWN * 0.1)], 0.6),
                        (0, [GrowArrow(pm), FadeIn(mainc)], 0.7)])

        gate = Line([GATE_X, BELT_Y - 0.75, 0], [GATE_X, BELT_Y + 0.75, 0], stroke_width=8, color=AG_C)
        gate_t = M("transform(bytes)", 22, AG_C).next_to(gate, DOWN, buff=0.15)
        reg = Arrow(pre.get_bottom(), gate.get_top(), buff=0.1, stroke_width=3, color=AG_C, max_tip_length_to_length_ratio=0.15)
        cft = T("ClassFileTransformer", 24, AG_C).next_to(gate_t, DOWN, buff=0.15)
        gold_ic = cls_chip("IssuerClient", AG_C)
        null_t = M("null", 22, GREY_B).move_to([GATE_X, BELT_Y + 1.0, 0])
        new_t = T("new bytes", 24, AG_C).move_to([GATE_X, BELT_Y + 1.0, 0])
        self.say("m3", [(0, [GrowArrow(reg)], 0.6), (0, [Create(gate), FadeIn(cft)], 0.6), (1, [FadeIn(gate_t)], 0.4),
                        (1, [flow(1, [chips[1].animate(run_time=0.5).move_to([GATE_X, BELT_Y, 0])])], 2.5)])
        self.say("m4", [(0, [Indicate(gate_t, color=AG_C)], 0.6),
                        (0, [FadeOut(reg)], 0.3),
                        (1, [Succession(FadeIn(chips[2], target_position=appjar.get_right(), scale=0.3, run_time=0.5),
                                        chips[2].animate(run_time=0.7).move_to([GATE_X - 1.3, BELT_Y, 0]),
                                        chips[2].animate(run_time=0.4).move_to([GATE_X, BELT_Y, 0]))], 1.6),
                        (1, [Transform(chips[2], gold_ic.move_to([GATE_X, BELT_Y, 0])), FadeIn(new_t)], 0.6),
                        (1, lambda: [chips[2].animate.move_to([4.6, SLOTS[2], 0])], 0.7),
                        (1, [FadeOut(new_t), FadeIn(null_t), Indicate(chips[1], color=WHITE, scale_factor=1.08)], 0.7)])
        self.play(FadeOut(VGroup(cmd, pre, mainc, pm, gate, gate_t, cft, null_t)), run_time=0.6)

        # --- an hour later: an agent attached to a running JVM
        later = T("another run: no agent at startup, an hour in", 26, GREY_B).move_to([-2.0, 2.85, 0])
        plain_ic = cls_chip("IssuerClient").move_to(chips[2])
        agm = chip("agentmain(args, inst)", AG_C, 24, mono=True).move_to([-2.4, 1.9, 0])
        gate2 = Line([GATE_X, BELT_Y - 0.75, 0], [GATE_X, BELT_Y + 0.75, 0], stroke_width=8, color=AG_C)
        reg2 = Arrow(agm.get_bottom(), gate2.get_top(), buff=0.1, stroke_width=3, color=AG_C, max_tip_length_to_length_ratio=0.15)
        q = T("Will the new transformer see IssuerClient?", 30, YELLOW_M).move_to([-1.2, -2.6, 0])
        self.say("q1", [(0, [FadeIn(later), Transform(chips[2], plain_ic)], 0.8),
                        (1, [FadeIn(agm, shift=DOWN * 0.1)], 0.6), (1, [GrowArrow(reg2), Create(gate2)], 0.7),
                        (2, [Indicate(chips[2], color=WHITE, scale_factor=1.1)], 0.8), (3, [FadeIn(q, shift=UP * 0.1)], 0.6)])
        only = T("it sees only classes defined from now on", 26, GREY_B).move_to([-1.2, -1.6, 0])
        idle = Cross(stroke_color=BAD_C, stroke_width=5).scale(0.14).next_to(chips[2], LEFT, buff=0.08)
        self.say("a1", [(0, [FadeOut(q)], 0.3), (1, [FadeIn(only)], 0.6), (1, [Create(idle)], 0.5)])

        arc = ArcBetweenPoints(chips[2].get_left() + LEFT * 0.05, np.array([GATE_X, BELT_Y - 0.8, 0]), angle=-PI / 2.2)
        arc_t = M("retransformClasses", 22, AG_C).move_to([1.0, -1.95, 0])
        ret = CurvedArrow(chips[2].get_left() + LEFT * 0.05, np.array([GATE_X + 0.05, BELT_Y - 0.8, 0]), angle=-PI / 2.2, color=AG_C,
                          stroke_width=3, tip_length=0.2)
        trav = cls_chip("IssuerClient").scale(0.8).move_to(chips[2])
        trav.set_z_index(5)
        new_ic = cls_chip("IssuerClient", AG_C).move_to(chips[2])
        same = VGroup(T("same Class object,", 24, AG_C), T("new method bodies", 24, AG_C)).arrange(DOWN, buff=0.08).move_to([4.6, -2.75, 0])
        self.say("r1", [(0, [FadeOut(only), FadeOut(idle), Create(ret), FadeIn(arc_t)], 0.8),
                        (1, [MoveAlongPath(trav, arc)], 1.2),
                        (1, [trav.animate.set_color(AG_C), Flash(gate2, color=AG_C, flash_radius=0.8)], 0.5),
                        (1, lambda: [trav.animate.move_to(chips[2]).set_opacity(0)], 0.9),
                        (1, [Transform(chips[2], new_ic), FadeIn(same)], 0.6)])
        self.remove(trav)

        # --- zoom on the class: old objects, running calls
        rest = VGroup(appjar, belt, tunnel, tunnel_t, jvm_t, later, agm, gate2, reg2, ret, arc_t, chips[0], chips[1], same)
        CB = np.array([0, 1.4, 0])
        cbox = RoundedRectangle(corner_radius=0.15, width=4.8, height=1.9, stroke_color=JVM_C, stroke_width=3).set_fill(shade(JVM_C, 0.06), 1)
        cbox.move_to(CB)
        c_name = M("IssuerClient", 28).move_to(CB + UP * 0.5)
        body = VGroup(Rectangle(width=4.0, height=0.6, stroke_color=AG_C, stroke_width=2).set_fill(shade(AG_C, 0.35), 1),
                      T("method body + timing", 24))
        body[1].move_to(body[0])
        body.move_to(CB + DOWN * 0.35)
        clsg = VGroup(cbox, c_name, body)
        self.play(FadeOut(rest), ReplacementTransform(VGroup(jvm, chips[2]), clsg), run_time=1.0)
        objs = VGroup(*[Circle(0.3, stroke_color=OBJ_C, stroke_width=3).set_fill(shade(OBJ_C, 0.4), 1).move_to([4.4, y, 0]) for y in (2.0, 0.85)])
        o_l = T("made at startup", 24, OBJ_C).next_to(objs, UP, buff=0.15)
        o_ar = VGroup(*[arrow(o.get_left(), cbox.get_right() + UP * (0.45 if i == 0 else -0.35), OBJ_C, buff=0.1) for i, o in enumerate(objs)])
        # timeline: two threads, the swap moment
        LA, LB = -1.35, -2.4
        swap = DashedLine([0, -0.75, 0], [0, -2.95, 0], dash_length=0.1, stroke_width=3, color=AG_C)
        swap_t = T("retransformed", 24, AG_C).next_to(swap, UP, buff=0.08)
        lanes = VGroup(T("thread A", 24, GREY_B).move_to([-5.6, LA, 0]), T("thread B", 24, GREY_B).move_to([-5.6, LB, 0]),
                       Line([-4.8, LA, 0], [6.2, LA, 0], stroke_width=2, color=GREY_D), Line([-4.8, LB, 0], [6.2, LB, 0], stroke_width=2, color=GREY_D))
        oldbar = VGroup(Rectangle(width=4.6, height=0.5, stroke_color=GREY_B, stroke_width=2).set_fill("#2A2A2A", 1), T("already running: old code", 24))
        oldbar[1].move_to(oldbar[0])
        oldbar.move_to([-0.7, LA, 0])
        newbar = VGroup(Rectangle(width=4.2, height=0.5, stroke_color=AG_C, stroke_width=2).set_fill(shade(AG_C, 0.35), 1), T("next call: new code", 24))
        newbar[1].move_to(newbar[0])
        newbar.move_to([3.0, LB, 0])
        self.say("r2", [(0, [FadeIn(objs), FadeIn(o_l), *[GrowArrow(a) for a in o_ar]], 0.8),
                        (0, [FadeIn(lanes), Create(swap), FadeIn(swap_t)], 0.7), (0, [GrowFromEdge(newbar, LEFT)], 0.9),
                        (1, [GrowFromEdge(oldbar, LEFT)], 1.2)])
        self.play(FadeOut(VGroup(lanes, swap, swap_t, oldbar, newbar)), run_time=0.5)

        # --- the limit: bodies only
        ghost = VGroup(DashedVMobject(Rectangle(width=4.0, height=0.6, stroke_color=BAD_C, stroke_width=2.5), num_dashes=36),
                       M("+ long calls;", 24, BAD_C))
        ghost[1].move_to(ghost[0])
        ghost.move_to([0, -0.25, 0])
        gx = tick(False, 0.22).next_to(ghost, RIGHT, buff=0.25)
        rules = VGroup(T("no new, removed or renamed fields or methods", 26),
                       T("no changes to signatures, modifiers or inheritance", 26)).arrange(DOWN, buff=0.15).move_to([0, -1.45, 0])
        cc = box("CallCounts", AG_C, w=2.8, h=0.8, size=26).move_to([0, -2.85, 0])
        cc[1].become(M("CallCounts", 26).move_to(cc[0]))
        cc.move_to([-4.4, -0.25, 0])
        cc_ar = arrow(body.get_left(), cc.get_top(), AG_C, buff=0.1)
        self.say("l1", [(0, [Indicate(body, color=AG_C, scale_factor=1.04)], 0.8),
                        (1, [FadeIn(ghost, shift=UP * 0.1)], 0.6), (1, [Create(gx), FadeIn(rules)], 0.8),
                        (3, [FadeIn(cc), GrowArrow(cc_ar)], 0.9)])
        self.play(FadeOut(VGroup(clsg, objs, o_l, o_ar, rules, cc, cc_ar, ghost, gx)), run_time=0.6)

        # --- the code
        jl = VGroup(T("Java", 24, GREY_B), M("inst.addTransformer(t, true);", 26), M("inst.retransformClasses(c);", 26)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        kl = VGroup(T("Kotlin", 24, GREY_B), M("inst.addTransformer(t, true)", 26), M("inst.retransformClasses(c)", 26)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        pair = VGroup(jl, kl).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(pair, 12.2).move_to([0, 1.0, 0])
        notes = VGroup(T("true: this transformer may run again on loaded classes", 24, GREY_B).next_to(pair, DOWN, buff=0.45))
        mf = VGroup(T("agent jar's manifest:", 24, GREY_B), M("Can-Retransform-Classes: true", 26, AG_C)).arrange(RIGHT, buff=0.3)
        mf.next_to(notes, DOWN, buff=0.45)
        self.say("k1", [(0, [FadeIn(pair, shift=UP * 0.1)], 0.8), (0, [FadeIn(notes)], 0.5), (0, [FadeIn(mf, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(pair, notes, mf)), run_time=0.5)

        # --- the rule and a check
        rule = VGroup(T("A transformer sees each class's bytes as the JVM defines it.", 32),
                      T("Retransformation swaps method bodies in place,", 32, AG_C),
                      T("for every object, never the class's shape.", 32, AG_C)).arrange(DOWN, buff=0.22).move_to([0, 1.55, 0])
        fit(rule, 12.4)
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.8), (1, [FadeIn(rule[1:], shift=UP * 0.1)], 0.8)])
        chk = VGroup(T("Check: an agent retransforms IssuerClient while a thread", 28),
                     T("is inside its method. Which code does it finish on?", 28)).arrange(DOWN, buff=0.2).move_to([0, -1.2, 0])
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("The old code. Its next call runs the new one.", 28, AG_C).move_to([0, -2.65, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
