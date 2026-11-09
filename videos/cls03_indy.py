from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\binvokedynamic\b", "invoke dynamic"), (r"\bLambdaMetafactory\b", "Lambda Meta Factory"),
           (r"\bIntUnaryOperator\b", "Int Unary Operator"), (r"\bConstantCallSite\b", "Constant Call Site"),
           (r"\bFunction1\b", "Function One"), (r"\bnestmate\b", "nest mate"), (r"\bmetafactory\b", "meta factory")]

INDY, BODY, BOOT, HID, LINK, CAPT = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREEN_M, YELLOW_M


class Planned(VoiceScene):
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


def card(lines, color, w, h=None, buff=0.12):
    """A filled rounded box holding a column of already-made text lines."""
    col = VGroup(*lines).arrange(DOWN, buff=buff)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h or col.height + 0.45, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    col.move_to(r)
    return VGroup(r, col)


def part(mob, sub):
    """The glyphs of substring sub in Text mob (Text drops spaces and newlines from its glyph list)."""
    s = mob.text if " " not in mob.text else mob.text.replace(" ", "")
    s = s.replace("\n", "")
    i = s.find(sub.replace(" ", ""))
    return mob[i:i + len(sub.replace(" ", ""))]


def dot_trip(a, color, run_time=0.8):
    """A dot running along arrow a."""
    return travel(Line(a.get_start(), a.get_end()), color, run_time)


class Cls03Indy(Planned):
    """cls-03 sections 0 and 1: a lambda is a body method plus an invokedynamic, linked once by LambdaMetafactory."""

    def construct(self):
        self.title_card("invokedynamic", "how a lambda gets its class")

        # ---------------- the lambda, Java and Kotlin ----------------
        java = M("static IntUnaryOperator plus(int fee) {\n"
                 "    return x -> x + fee;\n"
                 "}", 25, t2c={"fee": CAPT})
        kt = M("fun plus(fee: Int): (Int) -> Int =\n"
               "    { x -> x + fee }", 25, t2c={"fee": CAPT})
        jg = VGroup(T("Java", 22, GREY_B), java).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kg = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        src = VGroup(jg, kg).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        src.scale(min(1, 12.4 / src.width)).move_to([0, 0.4, 0])
        self.say("Here is one lambda, in Java and in Kotlin. It captures fee and adds it to x. "
                 "You get an object that implements an interface, yet the compiler writes no class file for it.",
                 [(0, [FadeIn(jg, shift=UP * 0.15)], 0.8), (0, [FadeIn(kg, shift=UP * 0.15)], 0.8),
                  (1, [Indicate(VGroup(java, kt), color=CAPT, scale_factor=1.03)], 0.9)])

        # ---------------- what javac wrote ----------------
        x0 = -6.0
        jl = T("javac output, read with javap", 22, GREY_B).move_to([x0, 1.0, 0], aligned_edge=LEFT)
        la = M("invokedynamic #1:applyAsInt:(I)Ljava/util/function/IntUnaryOperator;", 22, INDY,
               t2c={"(I)": CAPT, "IntUnaryOperator": WHITE}).move_to([x0, 0.45, 0], aligned_edge=LEFT)
        lb = M("private static int lambda$plus$1(int, int)   // (fee, x)", 22, BODY,
               t2c={"// (fee, x)": GREY_B}).move_to([x0, -0.05, 0], aligned_edge=LEFT)
        self.say("javac turns the lambda into two things: an invokedynamic instruction where the lambda was, "
                 "and a private static method that holds its body.",
                 [(0, [src.animate.move_to([0, 2.4, 0])], 0.7),
                  (0, [FadeIn(jl), FadeIn(la, shift=RIGHT * 0.2)], 0.9), (0, [FadeIn(lb, shift=RIGHT * 0.2)], 0.8)])

        self.say("The body method takes the captured fee first, then the lambda's own x.",
                 [(0, [Indicate(part(lb, "(int, int)   // (fee, x)"), color=CAPT, scale_factor=1.1)], 1.0)])

        fac = T("call site type: give it the captured int, get back an IntUnaryOperator", 24, CAPT)
        fac.move_to([0, -0.75, 0])
        fit(fac, 12.4)
        self.say("Read the call site type as a factory. Give it the captured int, and it gives you an IntUnaryOperator.",
                 [(0, [Indicate(part(la, "(I)"), color=CAPT, scale_factor=1.3)], 0.6),
                  (0, [Indicate(part(la, "IntUnaryOperator"), color=CAPT, scale_factor=1.1)], 0.7),
                  (1, [FadeIn(fac, shift=UP * 0.1)], 0.7)])

        other = VGroup(M("invokestatic StackDemo.feeMinor:(JI)J", 22, GREY_B), T("names its target", 22, GREY_B)).arrange(RIGHT, buff=0.4)
        other.move_to([x0, -0.75, 0], aligned_edge=LEFT)
        lc = M("bootstrap: LambdaMetafactory.metafactory", 22, BOOT).move_to([x0, -1.55, 0], aligned_edge=LEFT)
        ld = M("bootstrap args: (I)I, lambda$plus$1:(II)I, (I)I", 22, BOOT).move_to([x0, -2.05, 0], aligned_edge=LEFT)
        dnote = T("the interface method's erased type, the body, the type this lambda uses", 22, GREY_B)
        dnote.move_to([x0, -2.55, 0], aligned_edge=LEFT)
        self.say("Other invoke instructions name the method they call. "
                 "invokedynamic names only a name, a type, and a bootstrap method that will choose the target. "
                 "For a lambda, that is LambdaMetafactory, with three static arguments.",
                 [(0, [FadeOut(fac), FadeIn(other, shift=RIGHT * 0.2)], 0.8),
                  (1, [Indicate(part(la, "invokedynamic"), color=INDY, scale_factor=1.1)], 0.8),
                  (2, [FadeIn(lc, shift=RIGHT * 0.2)], 0.7), (2, [FadeIn(ld, shift=RIGHT * 0.2), FadeIn(dnote)], 0.8)])
        self.play(FadeOut(VGroup(src, jl, la, lb, other, lc, ld, dnote)), run_time=0.6)

        # ---------------- linking, once ----------------
        cs = card([M("invokedynamic #1", 26, INDY), M("(I)IntUnaryOperator", 22, GREY_B)], INDY, w=4.0).move_to([-4.3, 2.2, 0])
        bs = card([T("bootstrap method, runs once", 22, GREY_B), M("LambdaMetafactory.metafactory", 24, BOOT)], BOOT, w=6.4)
        bs.move_to([2.9, 2.2, 0])
        gets = T("gets a Lookup, the name, the type, the static args", 22).next_to(bs, DOWN, buff=0.15)
        hc = card([T("defines a hidden class", 22, GREY_B), M("IndyTour$$Lambda/0x...", 24, HID),
                   T("nestmate: may call lambda$plus$1", 22, GREY_B)], HID, w=6.4).move_to([2.9, -0.15, 0])
        cc = card([T("returns", 22, GREY_B), M("ConstantCallSite(target)", 24, LINK)], LINK, w=6.4).move_to([2.9, -2.3, 0])
        lk = card([T("call site", 24), T("linked for good", 24, LINK)], LINK, w=4.0).move_to([-4.3, -2.3, 0])
        a1 = arrow(cs[0].get_right(), bs[0].get_left(), BOOT, buff=0.1, sw=4)
        first = T("1st run", 22, BOOT).next_to(a1, UP, buff=0.12)
        a2 = arrow(bs[0].get_bottom(), hc[0].get_top(), GREY_B, buff=0.1)
        a3 = arrow(hc[0].get_bottom(), cc[0].get_top(), GREY_B, buff=0.1)
        a4 = arrow(cc[0].get_left(), lk[0].get_right(), LINK, buff=0.1, sw=4)
        later = DashedLine(cs[0].get_bottom() + DOWN * 0.1, lk[0].get_top() + UP * 0.1, dash_length=0.12, stroke_width=3, color=LINK)
        later_tip = Triangle(fill_opacity=1, stroke_width=0, color=LINK).scale(0.1).rotate(PI).move_to(lk[0].get_top() + UP * 0.17)
        later_l = VGroup(T("every later run:", 22, LINK), T("call the target", 22, LINK)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        later_l.next_to(later, RIGHT, buff=0.2)

        self.say("The first time the instruction runs, the JVM calls the bootstrap method. "
                 "It passes a Lookup, which carries your class's access rights, plus the name, the type and the static arguments.",
                 [(0, [FadeIn(cs)], 0.6), (0, [GrowArrow(a1), FadeIn(first), FadeIn(bs)], 0.8), (0, [dot_trip(a1, BOOT, 0.8)], 0.8),
                  (1, [FadeIn(gets, shift=UP * 0.1)], 0.7)])

        self.say("LambdaMetafactory spins a hidden class that implements IntUnaryOperator. "
                 "It's a nestmate of your class, so it may call the private body method.",
                 [(0, [FadeOut(gets), GrowArrow(a2), FadeIn(hc[0]), FadeIn(hc[1][:2])], 0.9),
                  (1, [FadeIn(hc[1][2], shift=UP * 0.1)], 0.7)])

        self.say("It returns a ConstantCallSite holding a method handle, a typed reference to a method that the JVM can call directly. "
                 "The JVM links the instruction to it.",
                 [(0, [GrowArrow(a3), FadeIn(cc)], 0.9),
                  (1, [GrowArrow(a4), FadeIn(lk)], 0.8), (1, [dot_trip(a4, LINK, 0.7)], 0.7),
                  (1, [cs[0].animate.set_stroke(LINK)], 0.5)])

        self.say("Every later run calls that target directly, and the bootstrap method never runs again. "
                 "The target can't change, so the JIT can inline straight through it.",
                 [(0, [Create(later), FadeIn(later_tip), FadeIn(later_l)], 0.8),
                  (0, [VGroup(bs, hc, a1, a2, a3, first).animate.set_opacity(0.3)], 0.6),
                  (0, [travel(Line(later.get_start(), later.get_end()), LINK, 0.7)], 0.7),
                  (0, [travel(Line(later.get_start(), later.get_end()), LINK, 0.7)], 0.7),
                  (1, [Indicate(cc[1][1], color=LINK, scale_factor=1.1)], 0.8)])
        self.play(FadeOut(VGroup(cs, bs, hc, cc, lk, a1, a2, a3, a4, first, later, later_tip, later_l)), run_time=0.6)

        # ---------------- what the target returns ----------------
        cls = card([T("one class", 22, GREY_B), M("IndyTour$$Lambda/0x...", 24, HID)], HID, w=5.0).move_to([3.0, 0.9, 0])
        o1 = card([M("plus(30)", 24), T("fee = 30", 24, CAPT)], WHITE, w=2.6).move_to([-2.8, 2.0, 0])
        o2 = card([M("plus(45)", 24), T("fee = 45", 24, CAPT)], WHITE, w=2.6).move_to([-2.8, -0.2, 0])
        b1 = arrow(o1[0].get_right(), cls[0].get_left() + UP * 0.2, HID, buff=0.1)
        b2 = arrow(o2[0].get_right(), cls[0].get_left() + DOWN * 0.2, HID, buff=0.1)
        two = T("two objects", 24, GREY_B).next_to(VGroup(o1, o2), LEFT, buff=0.3)
        nocap = VGroup(T("captures nothing:", 26), T("one shared instance, so greeter() == greeter() is true", 26, LINK)).arrange(RIGHT, buff=0.2)
        fit(nocap, 12.4).move_to([0, -2.5, 0])
        self.say("This lambda captures fee, so each time the expression runs you get a new small object. "
                 "All of them share one class. A lambda that captures nothing gets one shared instance.",
                 [(0, [FadeIn(o1, shift=RIGHT * 0.2)], 0.6), (0, [FadeIn(o2, shift=RIGHT * 0.2), FadeIn(two)], 0.6),
                  (1, [FadeIn(cls), GrowArrow(b1), GrowArrow(b2)], 0.9),
                  (2, [FadeIn(nocap, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(VGroup(cls, o1, o2, b1, b2, two, nocap)), run_time=0.6)

        # ---------------- Kotlin compiles it the same way ----------------
        def block(label, lines):
            return VGroup(T(label, 22, GREY_B), *lines).arrange(DOWN, aligned_edge=LEFT, buff=0.14)

        jb = block("javac", [M("invokedynamic #1:applyAsInt:(I)Ljava/util/function/IntUnaryOperator;", 22, INDY),
                             M("private static int lambda$plus$1(int, int)", 22, BODY),
                             M("bootstrap args: (I)I, lambda$plus$1:(II)I, (I)I", 22, BOOT)])
        kb = block("kotlinc (Kotlin 2.0 and later)", [M("invokedynamic #1:invoke:(I)Lkotlin/jvm/functions/Function1;", 22, INDY, t2c={"Function1": WHITE}),
                               M("private static final int plus$lambda$0(int, int)", 22, BODY),
                               M("bootstrap args: (Object)Object, plus$lambda$0:(II)I, (Integer)Integer", 22, BOOT,
                                 t2c={"(Integer)Integer": WHITE})])
        both = VGroup(jb, kb).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(both, 12.4).move_to([0, 0.75, 0])
        knote = VGroup(T("Function1.invoke is erased to (Object)Object,", 26),
                       T("so the metafactory inserts boxing and casts", 26, BOOT)).arrange(DOWN, buff=0.15).move_to([0, -2.55, 0])
        self.say("Kotlin compiles a lambda the same way, by default since Kotlin 2.0. "
                 "Its interface is Function1, whose invoke is erased to Object. "
                 "So the third bootstrap argument tells the metafactory to insert boxing and casts.",
                 [(0, [FadeIn(jb, shift=UP * 0.15)], 0.8), (0, [FadeIn(kb, shift=UP * 0.15)], 0.8),
                  (1, [Indicate(kb[1], color=WHITE, scale_factor=1.03), FadeIn(knote[0])], 0.9),
                  (2, [Indicate(kb[3], color=WHITE, scale_factor=1.03), FadeIn(knote[1])], 0.9)])

        fref = VGroup(T("a function reference,", 24, GREY_B), M("::addMinor", 24, BODY),
                      T("still compiled to an ordinary class", 24, GREY_B)).arrange(RIGHT, buff=0.2)
        fit(fref, 12.4).move_to([0, -3.15, 0])
        self.say("A Kotlin function reference is different. In the lesson's demo it still compiled to an ordinary generated class.",
                 [(0, [knote.animate.shift(UP * 0.45)], 0.5), (0, [FadeIn(fref, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(jb, kb, knote, fref)), run_time=0.6)

        # ---------------- a check ----------------
        q = VGroup(M("plus(fee)", 30, BODY), T("is called 1,000 times with 1,000 different fees.", 30)).arrange(RIGHT, buff=0.25)
        q2 = T("How many lambda classes, and how many objects?", 30)
        a = VGroup(T("One class, linked once, and 1,000 objects:", 30, LINK),
                   T("one per evaluation, because each captures its own fee", 30, LINK)).arrange(DOWN, buff=0.15)
        qa = VGroup(q, q2, a).arrange(DOWN, buff=0.35)
        a.shift(DOWN * 0.4)
        fit(qa, 12.4).move_to(ORIGIN)
        self.say("Here is a check. plus is called 1,000 times with 1,000 different fees. "
                 "How many lambda classes, and how many objects?",
                 [(0, [FadeIn(q, shift=UP * 0.15)], 0.8), (2, [FadeIn(q2, shift=UP * 0.15)], 0.7)], after=0.8)
        self.say("One class, linked once at that call site, and 1,000 objects, because each one captures its own fee.",
                 [(0, [FadeIn(a, shift=UP * 0.15)], 0.9)])
        self.wait(0.8)
