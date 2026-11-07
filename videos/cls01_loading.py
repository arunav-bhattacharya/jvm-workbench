from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"java\.base", "java dot base"), (r"java\.sql", "java dot S Q L"), (r"app\.jar", "app dot jar"),
           (r"Limits\.CAP", "Limits dot CAP"), (r"<clinit>", "clinit"), (r"\bMAX_MINOR\b", "max minor")]


def card(title, sub, color, w, h=1.1, tsize=30, ssize=22, mono_sub=False):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = T(title, tsize)
    s = (M if mono_sub else T)(sub, ssize, GREY_B)
    VGroup(t, s).arrange(DOWN, buff=0.14).move_to(r)
    return VGroup(r, t, s)


def recolor(c, color):
    """Animate a card's outline and fill to a new colour."""
    return c[0].animate.set_stroke(color).set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)


class Cls01Loading(VoiceScene):
    """cls-01: parent-first delegation, then loading, linking and initialization."""

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
        self.title_card("How a class gets in", "delegation, then load, link, initialize")

        # --- the problem: a first use of a class the JVM has never seen
        java = VGroup(T("Java", 22, GREY_B), M("Integer cap = Limits.CAP;", 30, YELLOW_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kt = VGroup(T("Kotlin", 22, GREY_B), M("val cap = Limits.CAP", 30, YELLOW_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        pair = VGroup(java, kt).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to(UP * 1.0)
        jar = card("app.jar", "com/acme/Limits.class", GREY_B, w=4.4, h=1.2, mono_sub=True).move_to(DOWN * 1.4)
        self.say("Your code reads Limits.CAP. The JVM has never seen this class. Its bytes sit unread in a jar.",
                 [(0, [FadeIn(pair, shift=UP * 0.2)], 1.2), (2, [FadeIn(jar, shift=UP * 0.2)], 0.8)])

        # --- three loaders, parent-first
        boot = card("bootstrap loader", "java.base", RED_M, w=4.4, mono_sub=True).move_to(LEFT * 3.2 + UP * 2.15)
        plat = card("platform loader", "java.sql, java.net.http", PURPLE_M, w=4.4, mono_sub=True).move_to(LEFT * 3.2 + UP * 0.15)
        app = card("app loader", "your class path", BLUE_M, w=4.4).move_to(LEFT * 3.2 + DOWN * 1.85)
        self.play(FadeOut(pair), jar.animate.move_to(RIGHT * 3.7 + DOWN * 1.85), run_time=0.7)
        self.say("A class loader finds a class's bytes and turns them into a Class. "
                 "The JDK has three. Bootstrap loads java.base. Platform loads the other JDK modules. "
                 "And the app loader loads your class path.",
                 [(0, [FadeIn(app, shift=UP * 0.2)], 0.8), (2, [FadeIn(boot, shift=UP * 0.2)], 0.8),
                  (3, [FadeIn(plat, shift=UP * 0.2)], 0.8), (4, [Indicate(app, color=WHITE, scale_factor=1.04)], 0.8)])

        up1 = arrow(app.get_top() + LEFT * 0.8, plat.get_bottom() + LEFT * 0.8, YELLOW_M, buff=0.08, sw=4)
        up2 = arrow(plat.get_top() + LEFT * 0.8, boot.get_bottom() + LEFT * 0.8, YELLOW_M, buff=0.08, sw=4)
        dn1 = arrow(boot.get_bottom() + RIGHT * 0.8, plat.get_top() + RIGHT * 0.8, GREY_B, buff=0.08, sw=3)
        dn2 = arrow(plat.get_bottom() + RIGHT * 0.8, app.get_top() + RIGHT * 0.8, GREY_B, buff=0.08, sw=3)
        req = chip("com.acme.Limits?", YELLOW_M, 24, mono=True).next_to(app, RIGHT, buff=0.3).shift(UP * 0.95)
        self.say("The app loader gets the request. Before it looks anywhere, it asks its parent. "
                 "So does the platform loader.",
                 [(0, [GrowArrow(up1), GrowArrow(up2), FadeIn(req, shift=LEFT * 0.2)], 0.8),
                  (1, [travel(up1, YELLOW_M, 0.9), req.animate.next_to(plat, RIGHT, buff=0.3)], 0.9),
                  (2, [travel(up2, YELLOW_M, 0.9), req.animate.next_to(boot, RIGHT, buff=0.3)], 0.9)])

        no_b = VGroup(tick(False), T("no Limits in java.base", 26, RED_M)).arrange(RIGHT, buff=0.25).next_to(boot, RIGHT, buff=0.35)
        no_p = VGroup(tick(False), T("not a platform module", 26, RED_M)).arrange(RIGHT, buff=0.25).next_to(plat, RIGHT, buff=0.35)
        find = arrow(app.get_right(), jar.get_left(), GREEN_M, buff=0.12, sw=4)
        find_l = T("findClass", 24, GREEN_M).next_to(find, UP, buff=0.12)
        found = VGroup(tick(True), T("found: defineClass", 26, GREEN_M)).arrange(RIGHT, buff=0.25).next_to(jar, UP, buff=0.3)
        self.say("Bootstrap has no Limits. Platform has none either. "
                 "Only then does the app loader search the class path. "
                 "It finds Limits in app.jar and defines the class.",
                 [(0, [FadeOut(req), FadeIn(no_b, shift=LEFT * 0.2)], 0.7),
                  (1, [GrowArrow(dn1), FadeIn(no_p, shift=LEFT * 0.2)], 0.8),
                  (2, [GrowArrow(dn2)], 0.7), (2, [GrowArrow(find), FadeIn(find_l)], 0.8),
                  (3, [recolor(jar, GREEN_M), FadeIn(found, shift=UP * 0.15)], 0.8)])

        # String always comes from the bootstrap loader
        self.play(FadeOut(VGroup(no_b, no_p, find, find_l, found, dn1, dn2)), recolor(jar, GREY_B), run_time=0.6)
        sreq = chip("java.lang.String?", YELLOW_M, 24, mono=True).next_to(app, RIGHT, buff=0.3).shift(UP * 0.95)
        yes_b = VGroup(tick(True), T("found in java.base", 26, GREEN_M)).arrange(RIGHT, buff=0.25).next_to(boot, RIGHT, buff=0.35)
        never = T("never asked", 24, GREY_B).next_to(jar, UP, buff=0.25)
        self.say("This is parent-first delegation. Ask for String, and bootstrap answers first. "
                 "So a stray jar can't replace a JDK class.",
                 [(0, [FadeIn(sreq)], 0.5),
                  (1, [Succession(AnimationGroup(travel(up1, YELLOW_M, 0.6), sreq.animate.next_to(plat, RIGHT, buff=0.3)),
                                  AnimationGroup(travel(up2, YELLOW_M, 0.6), sreq.animate.next_to(boot, RIGHT, buff=0.3)))], 1.4),
                  (1, [FadeOut(sreq), FadeIn(yes_b, shift=LEFT * 0.2)], 0.6),
                  (2, [jar.animate.set_opacity(0.35), FadeIn(never)], 0.8)])
        self.play(FadeOut(VGroup(boot, plat, up1, up2, yes_b, never, jar)), app.animate.move_to(LEFT * 4.0 + UP * 0.9), run_time=0.8)

        # --- identity: (name, defining loader)
        rule = T("a class = its name + its defining loader", 34).to_edge(UP, buff=0.8)
        app2 = card("plugin-1 loader", "a second loader", GOLD_M, w=4.4).move_to(LEFT * 4.0 + DOWN * 1.4)
        c_a = mbox("(com.acme.Limits, app)", BLUE_M, h=0.9, size=26).move_to(RIGHT * 2.6 + UP * 0.9)
        c_b = mbox("(com.acme.Limits, plugin-1)", GOLD_M, h=0.9, size=26).move_to(RIGHT * 2.6 + DOWN * 1.4)
        a_a = arrow(app.get_right(), c_a.get_left(), BLUE_M, buff=0.15)
        a_b = arrow(app2.get_right(), c_b.get_left(), GOLD_M, buff=0.15)
        neq = T("two different classes", 28, RED_M).move_to(RIGHT * 2.6 + DOWN * 0.25)
        self.say("The loader that defines a class is part of its identity. "
                 "At run time, a class is its name plus its defining loader. "
                 "So two loaders that define Limits from the same bytes make two different classes.",
                 [(0, [Write(rule)], 1.2), (1, [GrowArrow(a_a), FadeIn(c_a, shift=RIGHT * 0.2)], 0.9),
                  (2, [FadeIn(app2, shift=UP * 0.2)], 0.7), (2, [GrowArrow(a_b), FadeIn(c_b, shift=RIGHT * 0.2)], 0.9),
                  (2, [FadeIn(neq)], 0.6)])
        self.play(FadeOut(VGroup(rule, app, app2, c_a, c_b, a_a, a_b, neq)), run_time=0.7)

        # --- three phases
        load = card("Loading", "find the bytes", BLUE_M, w=2.9, h=1.6).move_to(LEFT * 4.8 + UP * 2.1)
        link_r = RoundedRectangle(corner_radius=0.12, width=4.8, height=1.6, stroke_color=PURPLE_M, stroke_width=3)
        link_r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(PURPLE_M), 0.10), opacity=1).move_to(LEFT * 0.2 + UP * 2.1)
        link_t = T("Linking", 30).move_to(link_r.get_top() + DOWN * 0.38)
        subs = VGroup(*[box(n, PURPLE_M, w=1.4, h=0.62, size=24) for n in ("verify", "prepare", "resolve")]).arrange(RIGHT, buff=0.12)
        subs.move_to(link_r.get_bottom() + UP * 0.48)
        link = VGroup(link_r, link_t, subs)
        init = card("Initialization", "runs <clinit>", GREEN_M, w=3.3, h=1.6, mono_sub=True).move_to(RIGHT * 4.6 + UP * 2.1)
        a1 = arrow(load.get_right(), link_r.get_left(), GREY_B, buff=0.06)
        a2 = arrow(link_r.get_right(), init.get_left(), GREY_B, buff=0.06)
        for c in (load, init):
            c[0].set_stroke(opacity=0.5)
        link_r.set_stroke(opacity=0.5)

        # what exists so far, under the pipeline
        cls_chip = chip("Class Limits", BLUE_M, 26, mono=True).move_to(LEFT * 4.8 + DOWN * 1.7)
        slot_l = M("static CAP", 26, GREY_B).move_to(LEFT * 0.2 + DOWN * 1.1)
        slot = mbox("no field yet", GREY_M, w=3.4, h=0.85, size=24).next_to(slot_l, DOWN, buff=0.2)
        slot[1].set_color(GREY_B)
        con_l = T("console", 22, GREY_B).move_to(RIGHT * 4.6 + DOWN * 1.1)
        con = RoundedRectangle(corner_radius=0.1, width=3.2, height=0.85, stroke_color=GREY_M, stroke_width=2).next_to(con_l, DOWN, buff=0.2)
        note = T("", 26)

        def set_note(text, color=WHITE):
            new = T(text, 26, WHITE).move_to(UP * 0.35)
            return new

        n1 = set_note("a Class object exists; none of your code has run", BLUE_M)
        self.say("Defining the class was loading, the first of three phases. "
                 "It made a Class object, and none of your code has run.",
                 [(0, [FadeIn(load), GrowArrow(a1), FadeIn(link), GrowArrow(a2), FadeIn(init)], 1.2),
                  (0, [FadeIn(slot_l), FadeIn(slot), FadeIn(con_l), FadeIn(con)], 0.5),
                  (1, [load[0].animate.set_stroke(opacity=1), FadeIn(cls_chip, shift=DOWN * 0.2), FadeIn(n1)], 1.0)])

        n2 = set_note("verify: the bytecode is type safe", PURPLE_M)
        self.say("Linking comes next. It verifies that the bytecode is type safe.",
                 [(0, [link_r.animate.set_stroke(opacity=1), FadeOut(n1)], 0.6), (1, [Indicate(subs[0], color=WHITE), FadeIn(n2)], 0.9)])

        n3 = set_note("prepare: statics exist, set to 0, false or null", PURPLE_M)
        slot_null = mbox("null", PURPLE_M, w=3.4, h=0.85, size=26).move_to(slot)
        self.say("It prepares the static fields with default values. So CAP exists now, and it holds null.",
                 [(0, [FadeOut(n2), Indicate(subs[1], color=WHITE), FadeIn(n3)], 0.9), (1, [Transform(slot, slot_null)], 0.7)])

        n4 = set_note("resolve: names in the constant pool become direct references", PURPLE_M)
        n4b = VGroup(M("Helper.class deleted", 22, GREY_B), M("main runs fine", 22, GREEN_M),
                     M("branch uses Helper -> NoClassDefFoundError", 22, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        n4b.next_to(n4, DOWN, buff=0.25)
        self.play(FadeOut(VGroup(slot_l, slot, con_l, con, cls_chip)), run_time=0.4)
        self.say("And it resolves names in the constant pool, lazily. "
                 "A class that uses a deleted Helper class runs fine. "
                 "It throws NoClassDefFoundError only when the branch that uses Helper runs.",
                 [(0, [FadeOut(n3), Indicate(subs[2], color=WHITE), FadeIn(n4)], 0.9),
                  (1, [FadeIn(n4b[0]), FadeIn(n4b[1])], 0.8), (2, [FadeIn(n4b[2], shift=UP * 0.1)], 0.7)])

        # back to the statics for initialization
        slot_l = M("static CAP", 26, GREY_B).move_to(LEFT * 0.2 + DOWN * 1.1)
        slot = mbox("null", PURPLE_M, w=3.4, h=0.85, size=26).next_to(slot_l, DOWN, buff=0.2)
        con_l = T("console", 22, GREY_B).move_to(RIGHT * 4.6 + DOWN * 1.1)
        con = RoundedRectangle(corner_radius=0.1, width=3.2, height=0.85, stroke_color=GREY_M, stroke_width=2).next_to(con_l, DOWN, buff=0.2)
        self.play(FadeOut(VGroup(n4, n4b)), FadeIn(VGroup(slot_l, slot, con_l, con)), run_time=0.6)

        n5 = set_note("initialization: static initializers and static blocks, in source order", GREEN_M)
        slot_v = mbox("500000", GREEN_M, w=3.4, h=0.85, size=26).move_to(slot)
        printed = M("Limits init", 24, GREEN_M).move_to(con)
        self.say("Initialization runs the static initializer, <clinit>. "
                 "That is every static field initializer and static block, in source order. "
                 "CAP becomes 500,000, and the static block prints.",
                 [(0, [init[0].animate.set_stroke(opacity=1), FadeIn(n5)], 0.9),
                  (2, [Transform(slot, slot_v)], 0.6), (2, [FadeIn(printed, shift=UP * 0.1)], 0.5)])
        self.say("Only this phase runs your code.",
                 [(0, [Indicate(init, color=GREEN_M, scale_factor=1.05)], 1.0)])
        self.play(FadeOut(VGroup(n5, slot_l, slot, con_l, con, printed)), run_time=0.6)

        # --- what triggers initialization
        go_t = T("these run <clinit>", 26, GREEN_M)
        go = VGroup(*[chip(x, GREEN_M, 24) for x in ("new Limits()", "a static method call", "a static field write",
                                                      "a non-constant static read")]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        gog = VGroup(go_t, go).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(RIGHT * 3.3 + DOWN * 1.25)
        no_t = T("these stop before it", 26, GREY_B)
        no = VGroup(*[chip(x, GREY_M, 24, mono=m) for x, m in (("a constant read", False), ("Limits.class", True),
                                                                ("new Limits[3]", True))]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        nog = VGroup(no_t, no).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(LEFT * 3.6 + DOWN * 1.05)
        g_arrow = arrow(np.array([init.get_x(), gog.get_top()[1], 0]), init.get_bottom(), GREEN_M, buff=0.12)
        n_line = DashedLine(nog.get_top() + UP * 0.1, link_r.get_bottom() + LEFT * 2.0 + DOWN * 0.08, dash_length=0.08, stroke_width=2, color=GREY_B)
        self.say("It starts on a new instance, a static method call, a static field write, "
                 "or a read of a static field that is not a constant.",
                 [(0, [FadeIn(go_t), GrowArrow(g_arrow)], 0.6),
                  (0, [LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in go], lag_ratio=0.5)], 2.6)])
        self.say("A constant read doesn't start it. Neither does Limits.class, or an array of Limits.",
                 [(0, [FadeIn(no_t), Create(n_line), FadeIn(no[0], shift=RIGHT * 0.2)], 0.8),
                  (1, [FadeIn(no[1], shift=RIGHT * 0.2)], 0.5), (1, [FadeIn(no[2], shift=RIGHT * 0.2)], 0.5)])
        self.play(FadeOut(VGroup(load, link, init, a1, a2, gog, nog, g_arrow, n_line)), run_time=0.7)

        # --- the check: constant or not
        title = T("Which read runs <clinit>?", 40).to_edge(UP, buff=0.8)
        jv = VGroup(T("Java", 22, GREY_B), M("static final int MAX_MINOR = 500_000;", 24, GREY_B),
                    M("static final Integer CAP = 500_000;", 24, GREEN_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        kv = VGroup(T("Kotlin", 22, GREY_B), M("const val MAX_MINOR = 500_000", 24, GREY_B),
                    M("val CAP: Int = 500_000", 24, GREEN_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        code = VGroup(jv, kv).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        code.scale(min(1, 12.2 / code.width)).move_to(UP * 0.7)
        v1 = T("MAX_MINOR: a constant. javac copied 500000 into your class. Nothing runs.", 26, GREY_B)
        v2 = T("CAP: boxed, not a constant. Reading it runs <clinit>.", 26, GREEN_M)
        verdict = VGroup(v1, v2).arrange(DOWN, buff=0.3).move_to(DOWN * 1.9)
        verdict.scale(min(1, 12.2 / verdict.width))
        self.beat("Check: which of these two reads runs the static initializer?",
                  Write(title), FadeIn(code, shift=UP * 0.2), run_time=1.6)
        self.beat("MAX_MINOR is a constant. javac copied its value into your class, so reading it runs nothing.",
                  FadeIn(v1, shift=UP * 0.15), run_time=1.0)
        self.beat("CAP is a boxed Integer, not a constant, so reading it runs <clinit>. "
                  "Kotlin's const val and plain val split the same way.",
                  FadeIn(v2, shift=UP * 0.15), Indicate(VGroup(jv[2], kv[2]), color=GREEN_M, scale_factor=1.04), run_time=1.6)
        self.wait(0.8)
