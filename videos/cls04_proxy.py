from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"Proxy\.newProxyInstance", "Proxy dot new proxy instance"), (r"\bFX\b", "F X")]


def card(title, sub, color, w, h=1.2, tsize=30, ssize=22, mono_sub=False):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = T(title, tsize)
    s = (M if mono_sub else T)(sub, ssize, GREY_B)
    VGroup(t, s).arrange(DOWN, buff=0.14).move_to(r)
    return VGroup(r, t, s)


def indent(line, n, size):
    """Text drops leading spaces, so shift an indented code line by n character widths."""
    cw = M("x" * 20, size).width / 20
    return line.shift(RIGHT * n * cw)


def back(a, color=GREEN_M, run_time=0.8):
    """A dot running backwards along arrow a (for return values)."""
    return travel(Line(a.get_end(), a.get_start()), color, run_time)


class Cls04Proxy(VoiceScene):
    """cls-04: a call on the interface goes to a generated class, which calls InvocationHandler.invoke."""

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
        self.title_card("A dynamic proxy", "one handler for every call")

        # --- the problem: the same wrapper code in forty methods
        names = ["FxQuotes", "Ledger", "Payouts", "Cards", "Refunds", "Fraud"]
        counts = [7, 7, 7, 7, 6, 6]
        cols = VGroup()
        for n, k in zip(names, counts):
            head = M(n, 22, BLUE_M)
            blocks = VGroup(*[RoundedRectangle(corner_radius=0.05, width=1.5, height=0.3, stroke_color=GREY_M, stroke_width=1.5)
                              .set_fill(GREY_M, opacity=0.25) for _ in range(k)]).arrange(DOWN, buff=0.1)
            cols.add(VGroup(head, blocks).arrange(DOWN, buff=0.25))
        cols.arrange(RIGHT, buff=0.32, aligned_edge=UP).move_to(UP * 0.5)
        allblocks = VGroup(*[c[1] for c in cols])
        cap = T("the same log-and-forward code, 40 times", 26, GREY_B).next_to(cols, DOWN, buff=0.45)
        self.say("Say you want to log every call your service makes to its FX quotes client. "
                 "A wrapper written by hand repeats the same log-and-forward code in every method. "
                 "Forty methods on six interfaces is tedious, and easy to get wrong.",
                 [(0, [FadeIn(cols[0][0]), LaggedStart(*[FadeIn(b) for b in cols[0][1]], lag_ratio=0.2)], 1.4),
                  (1, [FadeIn(VGroup(*[c[0] for c in cols[1:]])),
                       LaggedStart(*[FadeIn(b) for c in cols[1:] for b in c[1]], lag_ratio=0.05)], 2.0),
                  (2, [FadeIn(cap, shift=UP * 0.15)], 0.6)])

        handler = card("handler", "InvocationHandler", TEAL_M, w=3.0).move_to(DOWN * 0.2)
        self.say("The JDK can write that wrapper for you, while the program runs. You write one handler.",
                 [(0, [FadeOut(VGroup(*[c[0] for c in cols]), cap)], 0.6),
                  (1, [LaggedStart(*[b.animate.move_to(handler).scale(0.3).set_opacity(0) for b in allblocks.family_members_with_points()],
                                   lag_ratio=0.01), FadeIn(handler, scale=0.7)], 1.4)])
        self.remove(allblocks)

        # --- the path of one call
        caller = card("caller", "your code", WHITE, w=3.0).move_to(LEFT * 4.8 + UP * 1.9)
        proxy = card("proxy", "$Proxy0, generated", GOLD_M, w=3.2, ssize=20, mono_sub=True).move_to(UP * 1.9)
        target = card("target", "the real client", BLUE_M, w=3.0).move_to(RIGHT * 4.8 + DOWN * 1.5)
        call = M('q.quoteMicros("EURUSD")', 24, YELLOW_M).next_to(caller, UP, buff=0.3).align_to(caller, LEFT)
        a_cp = arrow(caller.get_right(), proxy.get_left(), YELLOW_M, buff=0.1, sw=4)
        self.play(handler.animate.move_to(RIGHT * 4.8 + UP * 1.9), run_time=0.8)
        a_ph = arrow(proxy.get_right(), handler.get_left(), YELLOW_M, buff=0.1, sw=4)
        a_ht = arrow(handler.get_bottom(), target.get_top(), YELLOW_M, buff=0.1, sw=4)
        self.say("Here is one call. Your code calls quoteMicros on what it thinks is an FxQuotes. "
                 "The object is really a proxy, an instance of a class the JDK generated.",
                 [(1, [FadeIn(caller), FadeIn(call, shift=DOWN * 0.15)], 0.8),
                  (2, [FadeIn(proxy), GrowArrow(a_cp)], 0.8), (2, [travel(a_cp, YELLOW_M, 0.8)], 0.8)])

        # inside the generated method
        inside = T("inside the proxy's quoteMicros", 24, GOLD_M).move_to(LEFT * 3.3 + DOWN * 0.25)
        steps = VGroup(
            M("1. m = the Method for quoteMicros", 24),
            M('2. args = new Object[]{ "EURUSD" }', 24),
            M("3. h.invoke(this, m, args)", 24, YELLOW_M),
            M("4. cast to Long, unbox to long", 24, GREEN_M),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        steps.next_to(inside, DOWN, buff=0.35).align_to(inside, LEFT)
        once = T("looked up once, when the class initializes", 20, GREY_B).next_to(steps[0], DOWN, buff=0.06).align_to(steps[0], LEFT).shift(RIGHT * 0.55)
        steps[1:].shift(DOWN * 0.25)
        self.say("The generated method takes the Method object for quoteMicros, which it looked up once. "
                 "It copies the arguments into a new Object array, boxing any primitives. "
                 "Then it calls invoke on your handler.",
                 [(0, [FadeIn(inside), FadeIn(steps[0], shift=RIGHT * 0.2)], 0.8), (0, [FadeIn(once)], 0.5),
                  (1, [FadeIn(steps[1], shift=RIGHT * 0.2)], 0.7),
                  (2, [FadeIn(steps[2], shift=RIGHT * 0.2), GrowArrow(a_ph)], 0.8), (2, [travel(a_ph, YELLOW_M, 0.8)], 0.8)])

        sig = M("invoke(proxy, method, args)", 22, TEAL_M).next_to(handler, DOWN, buff=0.25).shift(LEFT * 0.9)
        self.say("An InvocationHandler has one method, invoke. "
                 "It gets the proxy, the Method and the arguments, for every call on every method of the interface.",
                 [(0, [Indicate(handler, color=TEAL_M, scale_factor=1.05)], 0.8), (1, [FadeIn(sig, shift=UP * 0.1)], 0.7)])

        log = M("log: quoteMicros", 22, GREY_B).next_to(a_ht, LEFT, buff=0.3)
        self.play(FadeOut(sig), run_time=0.4)
        self.say("Your handler decides what happens. This one logs the call, then calls the same method on the real target.",
                 [(1, [FadeIn(log, shift=RIGHT * 0.15)], 0.6), (1, [FadeIn(target), GrowArrow(a_ht)], 0.8),
                  (1, [travel(a_ht, YELLOW_M, 0.8)], 0.8)])

        # the answer comes back
        r1 = M("1084250L", 22, GREEN_M).next_to(a_ht, RIGHT, buff=0.15)
        r2 = M("Object", 22, GREEN_M).next_to(a_ph, DOWN, buff=0.18)
        r3 = M("long 1084250", 22, GREEN_M).next_to(caller, DOWN, buff=0.2)
        self.say("The answer comes back as an Object. "
                 "The proxy casts it to Long and unboxes it, and the caller gets its plain long.",
                 [(0, [back(a_ht), FadeIn(r1)], 0.8), (0, [back(a_ph), FadeIn(r2)], 0.8),
                  (1, [FadeIn(steps[3], shift=RIGHT * 0.2)], 0.7), (1, [back(a_cp), FadeIn(r3)], 0.8)])

        # or not: no target at all
        cross = tick(False, 0.5).move_to(target)
        self_ans = T("answers by itself", 24, GREEN_M).next_to(handler, DOWN, buff=0.25).shift(LEFT * 1.4)
        self.say("A handler doesn't have to call a target at all. "
                 "In this section's demo there is no target. The handler returns 1,084,250 by itself.",
                 [(0, [target.animate.set_opacity(0.3), a_ht.animate.set_opacity(0.2), FadeOut(r1), FadeOut(log), FadeIn(cross)], 0.8),
                  (2, [FadeIn(self_ans)], 0.6), (2, [back(a_ph)], 0.7), (2, [back(a_cp)], 0.7)])
        self.play(FadeOut(VGroup(caller, proxy, handler, target, call, a_cp, a_ph, a_ht, inside, steps, once,
                                 r2, r3, cross, self_ans)), run_time=0.8)

        # --- the class is real
        head = T("What the proxy class says about itself", 34).to_edge(UP, buff=0.8)
        rows = [("class      public final jdk.proxy1.$Proxy0", {"public": WHITE, "final": GREEN_M, "jdk.proxy1.$Proxy0": GREY_B}),
                ("extends    java.lang.reflect.Proxy", {"java.lang.reflect.Proxy": GREEN_M}),
                ("implements FxQuotes", {"FxQuotes": GREEN_M}),
                ("fields     m0, m1, m2, m3, m4", {"m0, m1, m2, m3, m4": WHITE})]
        lines = VGroup(*[M(txt, 26, GREY_B, t2c=c) for txt, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        lines.move_to(UP * 0.6)
        fnote = T("hashCode, equals, toString, then your two methods", 22, GREY_B)
        fnote.next_to(lines[3], DOWN, buff=0.18).align_to(lines[3], LEFT).shift(RIGHT * 2.08)
        legend = VGroup(T("green: promised by the Javadoc", 24, GREEN_M), T("grey: a detail that may change", 24, GREY_B)).arrange(RIGHT, buff=0.8)
        legend.move_to(DOWN * 2.4)
        self.say("The proxy class is real, and you can ask it about itself. "
                 "It is final, it extends Proxy, and it implements exactly the interfaces you passed, in that order.",
                 [(0, [Write(head)], 1.0), (1, [LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in lines[:3]], lag_ratio=0.4)], 1.6)])
        self.say("It keeps one static Method field per method, looked up once. "
                 "The name and the module are details that may change.",
                 [(0, [FadeIn(lines[3], shift=RIGHT * 0.2), FadeIn(fnote)], 0.9), (1, [FadeIn(legend)], 0.8)])
        self.play(FadeOut(VGroup(head, lines, fnote, legend)), run_time=0.7)

        # --- creating one, Java and Kotlin
        title = T("Creating one", 40).to_edge(UP, buff=0.8)
        jv = VGroup(T("Java", 22, GREY_B),
                    M("FxQuotes q = (FxQuotes) Proxy.newProxyInstance(", 24, GOLD_M),
                    M("        loader, new Class<?>[]{FxQuotes.class}, handler);", 24, GOLD_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        kv = VGroup(T("Kotlin", 22, GREY_B),
                    M("val q = Proxy.newProxyInstance(", 24, GOLD_M),
                    M("    loader, arrayOf(FxQuotes::class.java), handler) as FxQuotes", 24, GOLD_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        indent(jv[2], 8, 24)
        indent(kv[2], 4, 24)
        code = VGroup(jv, kv).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        code.scale(min(1, 12.2 / code.width)).move_to(UP * 0.9)
        self.say("To get one, call Proxy.newProxyInstance with a class loader, the list of interfaces, and the handler. "
                 "From Kotlin it is the same call, because a Kotlin interface is an ordinary JVM interface.",
                 [(0, [Write(title), FadeIn(jv, shift=UP * 0.2)], 1.4), (1, [FadeIn(kv, shift=UP * 0.2)], 1.0)])

        q = T("Check: the handler returns null for quoteMicros. What does the caller get?", 26)
        a = T("A NullPointerException: the proxy unboxes null to a long.", 26, RED_M)
        qa = VGroup(q, a).arrange(DOWN, buff=0.3).move_to(DOWN * 2.2)
        qa.scale(min(1, 12.2 / qa.width))
        self.beat("Here is a check. Your handler returns null for quoteMicros. What does the caller get?",
                  FadeIn(q, shift=UP * 0.15), run_time=1.0, after=0.8)
        self.beat("A NullPointerException, thrown at the step where the proxy unboxes the answer to a long.",
                  FadeIn(a, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
