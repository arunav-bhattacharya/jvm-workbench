from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Builder", "at Builder"), (r"\.kt\b", " dot K T"), (r"\bkctfork\b", "K C T fork"), (r"\bTypeName\b", "Type Name"),
    (r"\bUPDATE_GOLDEN\b", "update golden"), (r"2\.4\.0", "2.4"), (r"\bLampBuilder\b", "Lamp Builder"),
]

# every spoken line, in order
N = {
    "open": "Before moving day, a careful family does a practice pack. One empty room, a few boxes, the helper with "
            "his clipboard, and a good look at the cards he writes. If he labels the lamp wrong, they want to know "
            "today, not at the new house.",
    "room": "A processor test is that practice pack. A library called kctfork compiles a few lines of Kotlin in "
            "memory, runs KSP and your processor on them, and hands back what happened. No Gradle project, and a "
            "fresh room every time.",
    "shyq": "Here's a question many of us never ask out loud. My test compiles the code, and finds the class the "
            "processor should write. It's green. So the processor works, right?",
    "lamp": "Let's find out with the smallest example there is. A lamp has a name, a number of bulbs, and a shade. "
            "The shade is a String with a question mark, because some lamps have no shade.",
    "builder": "The @Builder processor writes LampBuilder: a small class that collects a lamp's values one call at a "
               "time, then builds the lamp. Line 18 sets the shade, and it keeps the question mark.",
    "bug": "Now let's plant a bug. The processor turns each type into KotlinPoet's TypeName through one small "
           "function. The demo hands it a broken one, copy with nullable equals false, which drops every question "
           "mark.",
    "one": "So line 18 loses one character. The smallest mark on the line, doing the heaviest lifting: it's the only "
           "thing that says a lamp may have no shade.",
    "four": "Every processor test makes some of four checks: the exit code, the generated text, the messages, and a "
            "call into the generated code. Messages matter when a processor refuses bad input, and this builder "
            "refuses nothing. So the demo reads the text two ways, a quick one and a strict one. Four checks, "
            "weakest first.",
    "c1": "One, the exit code: how the compile ended. OK, a compilation error, or an internal error when a "
          "processor throws. Call it the glance: did the helper finish?",
    "c2": "Two, does the generated text contain class LampBuilder? The skim: is there a card with the right name?",
    "c3": "Three, a golden file: a stored copy of the output you expect, compared with the real output on every "
          "run. The proofreader.",
    "c4": "Four, call the code. kctfork's class loader, the JVM object that loads compiled classes, can see "
          "LampBuilder, even though the test was compiled long before LampBuilder existed. So the test can call "
          "it, with a lamp that has no shade. The try out.",
    "pred": "Same broken builder, four checks. Which ones notice the missing question mark? Pause and guess.",
    "v12": "The glance: passes, the exit code is OK. The skim: passes, the text does contain class LampBuilder.",
    "v3": "The proofreader: fails, at line 18. Expected: shade, String, question mark. Actual: shade, String.",
    "v4": "And the try out: fails. Calling shade with null throws a NullPointerException: parameter specified as "
          "non null is null.",
    "honest": "Notice the first two passed honestly. The broken builder is valid Kotlin, so it compiles, and it does "
              "contain the class. A test made of those two proves one thing: the processor didn't crash.",
    "van": "It's like checking moving day by confirming that a van showed up, with the right name painted on the "
           "side. True, and it tells you nothing about your lamp. The bug would reach the first family with a lamp "
           "that has no shade.",
    "golden": "So, the golden file. It has good habits. When the file is missing, the check writes it and fails once, "
              "so a person reads the new text before it becomes the standard. It reports the first line that "
              "differs. And UPDATE_GOLDEN equals true rewrites them, on purpose.",
    "proof": "But it's a proofreader with no sense of proportion. A moved space fails as loudly as a lost question "
             "mark. An upgrade that changes the formatting fails every golden file you have, as KotlinPoet 2.4.0 "
             "did when it changed how annotation arrays are written. No bug in sight.",
    "pair": "That's why the try out matters. The golden file catches any change. The call tells you whether the "
            "change matters. Keep both.",
    "rule": "So here's the rule. A test that only compiles proves the processor didn't crash. Call the code it wrote.",
    "code": "Here are the four checks in one Kotlin test: the exit code, the text against a golden file, no messages, "
            "and a call into the builder, with null for the shade.",
    "code_j": "Java's annotation processors have the same kind of library, Google's compile-testing. It checks the "
              "compile and the generated file. To call the code, you test from a module whose own build runs the "
              "processor.",
    "moral": "So, does a green test mean a working processor? Only if it calls the code. The glance and the skim say "
             "the helper finished. The proofreader says the card changed. The try out says whether the lamp still "
             "works.",
    "room2": "One more thing about the practice room: it's fresh every time. A second, incremental build never "
             "happens there, so lesson 7's wrong Dependencies pass every test. Those need a real build.",
    "check": "Quick check. Fix the bug with copy and no arguments, so the question marks stay. What do the four "
             "checks say now?",
    "check_a": "The exit code is OK, the text has the class, the golden file says Matches, and shade with null works. "
               "All four pass.",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at()/at_text() wait for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole KSP track (moving house), as in ksp01
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
PAPER, INK = "#EDE6D6", "#161616"
POET = GREEN_M        # KotlinPoet, as in ksp04
GOLD = GOLD_M         # the stored golden file


def person(color=HELPER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def clipboard(s=1.0):
    board = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.56).set_stroke(GREY_A, 2).set_fill("#262626", 1)
    clip = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.08).set_stroke(HELPER, 2).set_fill(dim(HELPER, 0.6), 1)
    clip.move_to(board.get_top())
    lines = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=GREY_B).move_to(board.get_center() + UP * (0.12 - 0.11 * i))
                     for i in range(3)])
    return VGroup(board, clip, lines).scale(s)


def helper(s=1.0):
    p = person(HELPER, s)
    cb = clipboard(0.9 * s).next_to(p[0], RIGHT, buff=0.03 * s).shift(UP * 0.08 * s)
    return VGroup(p, cb)


def code_block(src, size=22, hl=None, color=WHITE, buff=0.15):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def mini_card(color=CARD, w=0.62, h=0.42):
    r = RoundedRectangle(corner_radius=0.04, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=1.5, color=color) for _ in range(2)]).arrange(DOWN, buff=0.1)
    return VGroup(r, ls.move_to(r))


def rule_card(text, color=YELLOW_M, size=28, w=12.4):
    t = VGroup(*[T(x, size, color) for x in text.split("\n")]).arrange(DOWN, buff=0.14)
    fit(t, w - 0.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.6, height=t.height + 0.45).set_stroke(color, 2).set_fill(dim(color, 0.1), 1)
    return VGroup(r, t.move_to(r))


def sticky(s=0.36):
    r = Square(s).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    ls = VGroup(*[Line(LEFT * s * 0.3, RIGHT * s * 0.3, stroke_width=1.5, color=INK) for _ in range(2)]).arrange(DOWN, buff=s * 0.2)
    return VGroup(r, ls.move_to(r)).rotate(8 * DEGREES)


def fbox(name=None, w=1.75, h=1.05, noted=True):
    color = BOX
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.18).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.09)
    tape = Rectangle(width=0.28, height=0.3).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.15)
    g = VGroup(body, lid, tape)
    if name:
        t = M(name, 22, INK)
        r = Rectangle(width=t.width + 0.2, height=t.height + 0.22).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
        g.add(VGroup(r, t.move_to(r)).move_to(body.get_center() + DOWN * 0.1))
    if noted:
        g.add(sticky().move_to(body.get_corner(UL) + RIGHT * 0.2 + DOWN * 0.02))
    return g


def panel(m, color=GREY_B, buff=0.22):
    return SurroundingRectangle(m, buff=buff, color=color, stroke_width=2, corner_radius=0.1).set_fill(dim(color, 0.07), 1)


def lamp_icon(shade=True, s=1.0):
    base = RoundedRectangle(corner_radius=0.05, width=0.7, height=0.14).set_stroke(GREY_A, 2.5).set_fill("#2a2a2a", 1)
    stem = Line(base.get_top(), base.get_top() + UP * 0.95, stroke_width=4, color=GREY_A)
    bulb = Circle(radius=0.14).set_stroke(NOTE, 2).set_fill(NOTE, 0.85).move_to(stem.get_end() + UP * 0.08)
    g = VGroup(base, stem, bulb)
    if shade:
        sh = Polygon([-0.26, 0.24, 0], [0.26, 0.24, 0], [0.48, -0.26, 0], [-0.48, -0.26, 0])
        sh.set_stroke(BOX, 3).set_fill(dim(BOX, 0.45), 1).move_to(bulb.get_center() + UP * 0.06)
        g.add(sh)
    return g.scale(s)


def van(s=1.0):
    body = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.15).set_stroke(VAN, 3).set_fill(dim(VAN, 0.22), 1)
    cab = RoundedRectangle(corner_radius=0.12, width=0.8, height=0.8).set_stroke(VAN, 3).set_fill(dim(VAN, 0.3), 1)
    cab.next_to(body, RIGHT, buff=0).align_to(body, DOWN)
    win = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.3).set_stroke(VAN, 2).set_fill(BLACK, 1)
    win.move_to(cab.get_center() + UP * 0.12 + RIGHT * 0.08)
    wheels = VGroup(*[Circle(radius=0.19).set_stroke(GREY_A, 3).set_fill(BLACK, 1) for _ in range(2)])
    wheels[0].move_to(body.get_bottom() + LEFT * 0.6)
    wheels[1].move_to(cab.get_bottom() + LEFT * 0.05)
    name = T("MoveMate", 22, WHITE).move_to(body.get_center() + UP * 0.08)
    return VGroup(body, cab, win, wheels, name).scale(s)


def stripes(n=25, w=2.4, bad=None, color=GOLD):
    """A file drawn as n short text lines; line `bad` (1-based) can be picked out later."""
    ls = VGroup()
    rng = [0.55, 0.9, 0.0, 0.5, 0.5, 0.0, 0.62, 0.7, 0.0, 0.7, 0.0, 0.7, 0.0, 0.95, 0.0, 0.95, 0.0, 0.98, 0.0, 0.6, 0.8, 0.8,
           0.6, 0.2, 0.1]
    for i in range(n):
        f = rng[i % len(rng)]
        ln = Line(LEFT * w / 2, LEFT * w / 2 + RIGHT * max(f, 0.001) * w, stroke_width=3, color=color)
        if f == 0.0:
            ln.set_opacity(0)
        ls.add(ln)
    ls.arrange(DOWN, buff=0.07, aligned_edge=LEFT)
    return ls


# the four checks: one row each
ROWY = [1.75, 0.85, -0.05, -0.95]
X_NUM, X_WHAT, X_WHO, X_VERD = -6.1, -5.6, -0.25, 2.0
BOT = -2.55


class Ksp08Testing(Narrated):
    """ksp-08, section 1: four checks, weakest first. A practice pack in an empty room (kctfork in memory); the shy
    question (green means it works?); Lamp with shade: String?, the generated LampBuilder line 18; the planted bug
    (typeOf = copy(nullable = false), WeakTestsDemo); the four checks named with personalities (glance, skim,
    proofreader, try out); predict; the real verdicts (passes, passes, FAILS at line 18, FAILS with NPE); why two pass;
    the van; golden file habits and its flaw (KotlinPoet 2.4.0); pair it with a call; the rule; the four checks in Kotlin
    and Java's compile-testing; moral, the room's limit (lesson 7), and a check."""

    def construct(self):
        self.title_card("Four checks, weakest first", "a planted bug that two of them miss")

        # ================= the practice pack =================
        room = Rectangle(width=7.6, height=4.2).set_stroke(GREY_B, 3).move_to([-2.2, 0.0, 0])
        door = Line(room.get_corner(DR) + UP * 0.5, room.get_corner(DR) + UP * 1.6, stroke_width=8, color=BLACK)
        room_l = T("an empty room", 24, GREY_B).next_to(room, UP, buff=0.15).align_to(room, LEFT)
        bxs = VGroup(fbox("Lamp"), fbox("Box")).arrange(RIGHT, buff=0.4).move_to([-4.0, -1.1, 0])
        hp = helper(1.3).move_to([-1.2, -1.15, 0])
        cd = mini_card(CARD, 0.9, 0.6).move_to([0.4, -0.2, 0])
        cdl = T("a card to inspect", 22, CARD).next_to(cd, UP, buff=0.15)
        self.say("open")
        self.play(Create(room), FadeIn(door), FadeIn(room_l), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in bxs], lag_ratio=0.3), FadeIn(hp), run_time=1.0)
        self.at_text("a good look", lead=0.2)
        self.play(FadeIn(cd, shift=RIGHT * 0.2), FadeIn(cdl), run_time=0.7)
        self.at(2)
        self.play(Indicate(bxs[0], color=BOX, scale_factor=1.06), run_time=0.8)
        self.hold()

        src = VGroup(M("Source(\"Lamp.kt\", ...)", 22, BOX), T("a few lines, in a string", 20, GREY_A)).arrange(DOWN, buff=0.1)
        kc = VGroup(M("kctfork", 26, HELPER), T("KSP and the Kotlin compiler,", 20, GREY_A), T("in memory", 20, GREY_A)).arrange(DOWN, buff=0.08)
        res = VGroup(T("what happened", 24, WHITE), T("exit code, generated files,", 20, GREY_A),
                     T("messages, a class loader", 20, GREY_A)).arrange(DOWN, buff=0.08)
        pipe = VGroup(src, kc, res).arrange(DOWN, buff=0.55).move_to([4.6, 0.1, 0])
        pa1 = Arrow(src.get_bottom(), kc.get_top(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        pa2 = Arrow(kc.get_bottom(), res.get_top(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        fresh = T("no Gradle project, a fresh room every time", 24, NOTE).move_to([0, -3.15, 0])
        self.say("room")
        self.play(Indicate(room, color=WHITE, scale_factor=1.01), run_time=0.6)
        self.at(1)
        self.play(FadeIn(src, shift=DOWN * 0.1), run_time=0.5)
        self.play(GrowArrow(pa1), FadeIn(kc), run_time=0.6)
        self.at_text("and hands back", lead=0.2)
        self.play(GrowArrow(pa2), FadeIn(res), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fresh, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        qs = VGroup(VGroup(T("My test compiles the code", 32), tick(True, 0.18)).arrange(RIGHT, buff=0.25),
                    VGroup(T("and finds the class it should write", 32), tick(True, 0.18)).arrange(RIGHT, buff=0.25),
                    T("It's green. So the processor works... right?", 34, NOTE)).arrange(DOWN, buff=0.35)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(qs[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("and finds", lead=0.2)
        self.play(FadeIn(qs[1], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qs[2], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.6)
        self.play(FadeOut(qs), run_time=0.5)

        # ================= the smallest example: Lamp and its builder =================
        lsrc = M("data class Lamp(val name: String, val bulbs: Int, val shade: String?)", 24, WHITE,
                 t2c={"String?": NOTE})
        fit(lsrc, 12.4)
        lnote = VGroup(M("@Builder", 24, NOTE)).next_to(lsrc, UP, buff=0.15).align_to(lsrc, LEFT)
        lg = VGroup(lnote, lsrc).move_to([0, 2.6, 0])
        l1 = lamp_icon(True, 1.0)
        l2 = lamp_icon(False, 1.0)
        lamps = VGroup(l1, l2).arrange(RIGHT, buff=1.2).move_to([0, 0.6, 0])
        l2t = T("no shade: null", 22, NOTE).next_to(l2, DOWN, buff=0.2)
        l1t = T("a shade", 22, GREY_A).next_to(l1, DOWN, buff=0.2)
        self.say("lamp")
        self.play(FadeIn(lg, shift=DOWN * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(l1), FadeIn(l1t), run_time=0.6)
        self.at(2)
        self.play(Indicate(part(lsrc, "String?"), color=NOTE, scale_factor=1.2), FadeIn(l2), FadeIn(l2t), run_time=0.9)
        self.hold()

        gen = code_block(["14   public fun name(name: String): LampBuilder = apply { this.name = name }",
                          "16   public fun bulbs(bulbs: Int): LampBuilder = apply { this.bulbs = bulbs }",
                          "18   public fun shade(shade: String?): LampBuilder = apply { this.shade = shade }"], 22, buff=0.2)
        for g in gen:
            g[:2].set_color(GREY_B)
        gh = T("LampBuilder.kt, generated (excerpt)", 22, CARD)
        genp = panel(gen, CARD, 0.22)
        gg = VGroup(genp, gen)
        gh.next_to(genp, UP, buff=0.1).align_to(genp, LEFT)
        VGroup(gg, gh).move_to([0, -1.75, 0])
        fit(VGroup(gg, gh), 12.6)
        q18 = part(gen[2], "String?")[-1]
        self.say("builder")
        self.play(FadeIn(gh), FadeIn(genp), FadeIn(gen[0]), FadeIn(gen[1]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(gen[2], shift=RIGHT * 0.1), run_time=0.6)
        self.play(Indicate(q18, color=NOTE, scale_factor=1.6), run_time=0.8)
        self.hold()

        # ================= the planted bug =================
        bugc = M("typeOf = { it.toTypeName().copy(nullable = false) }", 24, WHITE, t2c={"nullable = false": BAD})
        bugh = T("WeakTestsDemo hands the processor a broken type function:", 22, GREY_A)
        bg = VGroup(bugh, bugc).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, 0.75, 0])
        fit(bg, 12.4)
        self.say("bug")
        self.play(FadeOut(VGroup(lamps, l1t, l2t)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(bugh), FadeIn(bugc, shift=UP * 0.1), run_time=0.8)
        self.at_text("copy with", lead=0.2)
        self.play(Indicate(part(bugc, "nullable = false"), color=BAD, scale_factor=1.12), run_time=0.9)
        self.hold()

        self.say("one")
        k = list(gen[2].submobjects).index(q18)
        rest = gen[2][k + 1:]
        dx = rest[0].get_center()[0] - q18.get_center()[0]
        self.play(q18.animate.set_color(BAD), run_time=0.3)
        self.play(q18.animate.shift(DOWN * 0.6).rotate(0.6).set_opacity(0), run_time=1.0)
        self.play(rest.animate.shift(LEFT * dx), part(gen[2], "String")[-6:].animate.set_color(BAD), run_time=0.5)
        self.at(1)
        self.play(Indicate(part(lsrc, "String?"), color=NOTE, scale_factor=1.2), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the four checks, weakest first =================
        top18 = M("18   public fun shade(shade: String): LampBuilder = apply { this.shade = shade }", 22, WHITE,
                  t2c={"String)": BAD})
        top18[:2].set_color(GREY_B)
        toph = T("the planted bug, line 18:", 20, BAD)
        topg = VGroup(toph, top18).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to([0, 3.05, 0])
        fit(topg, 12.6)

        def row(i, what, who):
            y = ROWY[i]
            num = VGroup(Circle(radius=0.24).set_stroke(GREY_A, 2.5), T(str(i + 1), 26)).move_to([X_NUM, y, 0])
            num[1].move_to(num[0])
            w = what.move_to([X_WHAT, y, 0], aligned_edge=LEFT)
            p = T(who, 26, GREY_A).move_to([X_WHO, y, 0], aligned_edge=LEFT)
            return VGroup(num, w, p)

        rows = [row(0, VGroup(T("the exit code is", 26), M("OK", 24, OK)).arrange(RIGHT, buff=0.15), "the glance"),
                row(1, VGroup(T("the text contains", 26), M("class LampBuilder", 24, CARD)).arrange(RIGHT, buff=0.15), "the skim"),
                row(2, T("the golden file matches", 26), "the proofreader"),
                row(3, VGroup(T("a call:", 26), M("shade(null)", 24, NOTE)).arrange(RIGHT, buff=0.15), "the try out")]
        for r in rows:
            r[1].align_to([X_WHAT, 0, 0], LEFT)
        kinds = VGroup(T("exit code", 24), T("generated text", 24), T("messages", 24, GREY_B), T("a call", 24)).arrange(RIGHT, buff=0.7)
        kinds.move_to([0, BOT + 0.35, 0])
        kh = T("the four kinds of check", 22, GREY_B).next_to(kinds, UP, buff=0.15)
        self.say("four")
        self.play(FadeIn(topg), run_time=0.6)
        self.play(FadeIn(kh), LaggedStart(*[FadeIn(k, shift=UP * 0.1) for k in kinds], lag_ratio=0.25), run_time=1.2)
        self.at(1)
        mx = Line(kinds[2].get_left(), kinds[2].get_right(), stroke_width=3, color=GREY_B)
        self.play(Create(mx), run_time=0.5)
        self.at(2)
        self.play(Indicate(kinds[1], color=CARD, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeOut(VGroup(kinds, kh, mx)), run_time=0.5)
        self.hold()

        def define(lines):
            g = VGroup(*lines).arrange(DOWN, buff=0.12).move_to([0, BOT, 0])
            fit(g, 12.6)
            return g

        d1 = define([VGroup(M("OK", 24, OK), M("COMPILATION_ERROR", 24, BAD), M("INTERNAL_ERROR", 24, BAD)).arrange(RIGHT, buff=0.6),
                     T("how the compile ended; an internal error means a processor threw", 22, GREY_A)])
        self.say("c1")
        self.play(FadeIn(rows[0][:2]), run_time=0.6)
        self.at_text("OK, a compilation", lead=0.2)
        self.play(FadeIn(d1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rows[0][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        self.say("c2")
        self.play(FadeOut(d1), FadeIn(rows[1][:2]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rows[1][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        d3 = define([T("golden file: a stored copy of the output you expect,", 24, GOLD),
                     T("compared with the real output on every run", 24, GREY_A)])
        self.say("c3")
        self.play(FadeIn(rows[2][:2]), run_time=0.6)
        self.at_text("a stored copy", lead=0.2)
        self.play(FadeIn(d3, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rows[2][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        d4 = define([VGroup(T("class loader:", 24, HELPER), T("the JVM object that finds compiled classes and loads them", 24, GREY_A)).arrange(RIGHT, buff=0.15),
                     T("kctfork's sees the generated LampBuilder, so the test can call it", 22, GREY_A)])
        self.say("c4")
        self.play(FadeOut(d3), FadeIn(rows[3][:2]), run_time=0.6)
        self.at_text("kctfork's class", lead=0.2)
        self.play(FadeIn(d4, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(rows[3][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        pq = T("Which ones notice the missing question mark?", 30, NOTE).move_to([0, BOT, 0])
        self.say("pred")
        self.play(FadeOut(d4), run_time=0.4)
        self.at(1)
        self.play(FadeIn(pq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.8, pos=(6.4, BOT - 0.75), edge=RIGHT)

        # ================= the verdicts (WeakTestsDemo, real output) =================
        def verdict(i, ok, detail=None, mono=False):
            v = T("passes" if ok else "FAILS", 26, OK if ok else BAD)
            g = VGroup(v)
            if detail:
                g.add((M if mono else T)(detail, 22 if mono else 24, GREY_A if ok else BAD))
                g.arrange(RIGHT, buff=0.2)
            return g.move_to([X_VERD, ROWY[i], 0], aligned_edge=LEFT)

        ve = [verdict(0, True, "(OK)", True), verdict(1, True), verdict(2, False, "at line 18"),
              verdict(3, False, "NullPointerException", True)]
        self.say("v12")
        self.play(FadeOut(pq), run_time=0.3)
        self.play(FadeIn(ve[0], shift=LEFT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ve[1], shift=LEFT * 0.1), run_time=0.6)
        self.hold()

        exp = code_block(["expected:", "  public fun shade(shade: String?): LampBuilder = apply { this.shade = shade }",
                          "actual:", "  public fun shade(shade: String): LampBuilder = apply { this.shade = shade }"], 22, buff=0.1)
        exp[0].set_color(GREY_B)
        exp[2].set_color(GREY_B)
        part(exp[1], "String?").set_color(OK)
        part(exp[3], "String)")[:-1].set_color(BAD)
        exp.move_to([0, BOT - 0.15, 0])
        fit(exp, 12.6)
        self.say("v3")
        self.play(FadeIn(ve[2], shift=LEFT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(exp[:2], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(exp[2:], shift=UP * 0.1), run_time=0.6)
        self.hold()

        npe = code_block(["NullPointerException: Parameter specified as non-null is null:",
                          "  method movemate.LampBuilder.shade, parameter shade"], 22, color=BAD, buff=0.12)
        npeh = T("check 4, real output", 20, GREY_B)
        npg = VGroup(npeh, npe).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([0, BOT - 0.1, 0])
        noshade = lamp_icon(False, 0.7).move_to([5.9, BOT - 0.1, 0])
        self.say("v4")
        self.play(FadeOut(exp), FadeIn(ve[3], shift=LEFT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(npg, shift=UP * 0.1), FadeIn(noshade), run_time=0.7)
        self.hold()

        # ================= why two pass =================
        hz = SurroundingRectangle(VGroup(rows[0], rows[1], ve[0], ve[1]), buff=0.15, color=OK, stroke_width=2.5, corner_radius=0.1)
        hon = VGroup(T("valid Kotlin: it compiles, and it contains the class", 26),
                     VGroup(T("proves one thing:", 26, GREY_A), T("the processor didn't crash", 26, NOTE)).arrange(RIGHT, buff=0.2)
                     ).arrange(DOWN, buff=0.18).move_to([0, BOT, 0])
        self.say("honest")
        self.play(FadeOut(VGroup(npg, noshade)), Create(hz), run_time=0.7)
        self.at(1)
        self.play(FadeIn(hon[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(hon[1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        vn = van(0.8).move_to([-3.9, BOT - 0.05, 0])
        vt = VGroup(tick(True, 0.15), T("a van showed up", 22, GREY_A)).arrange(RIGHT, buff=0.12).next_to(vn, RIGHT, buff=0.35).shift(UP * 0.25)
        vt2 = VGroup(tick(True, 0.15), T("the right name on the side", 22, GREY_A)).arrange(RIGHT, buff=0.12).next_to(vt, DOWN, buff=0.15).align_to(vt, LEFT)
        ln = lamp_icon(False, 0.7).move_to([4.6, BOT - 0.05, 0])
        lq = T("?", 40, BAD).next_to(ln, RIGHT, buff=0.2)
        self.say("van")
        self.play(FadeOut(hon), FadeIn(vn, shift=RIGHT * 0.4), run_time=0.8)
        self.at_text("with the right", lead=0.3)
        self.play(FadeIn(vt), run_time=0.4)
        self.play(FadeIn(vt2), run_time=0.4)
        self.at(1)
        self.play(FadeIn(ln), FadeIn(lq), run_time=0.6)
        self.at(2)
        self.play(Indicate(ln, color=NOTE, scale_factor=1.15), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the golden file: habits and its flaw =================
        fs = stripes(25, 2.6, color=GOLD)
        fa = stripes(25, 2.6, color=CARD)
        pf = panel(fs, GOLD, 0.2)
        pa = panel(fa, CARD, 0.2)
        gfile = VGroup(pf, fs)
        afile = VGroup(pa, fa)
        gfl = M("LampBuilder.kt.golden", 22, GOLD)
        afl = T("this run's LampBuilder.kt", 22, CARD)
        files = VGroup(VGroup(gfl, gfile).arrange(DOWN, buff=0.12), VGroup(afl, afile).arrange(DOWN, buff=0.12)).arrange(RIGHT, buff=1.4)
        files.move_to([-2.4, 1.15, 0])
        s18g = SurroundingRectangle(fs[17], buff=0.05, color=BAD, stroke_width=2.5)
        s18a = SurroundingRectangle(fa[17], buff=0.05, color=BAD, stroke_width=2.5)
        d18 = T("first difference: line 18", 24, BAD).next_to(files, RIGHT, buff=0.5).align_to(fa[17], DOWN).shift(DOWN * 0.1)
        habits = VGroup(
            VGroup(T("missing?", 26, NOTE), T("written, and the check fails once, so a person reads it", 26)).arrange(RIGHT, buff=0.2),
            VGroup(T("reports", 26, NOTE), T("the first line that differs, counting from 1", 26)).arrange(RIGHT, buff=0.2),
            VGroup(M("UPDATE_GOLDEN=true", 24, NOTE), T("rewrites them, on purpose", 26)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, -2.3, 0])
        fit(habits, 12.6)
        self.say("golden")
        self.play(FadeIn(files, shift=UP * 0.1), run_time=0.9)
        self.at(2)
        self.play(FadeIn(habits[0], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(habits[1], shift=UP * 0.1), Create(s18g), Create(s18a), FadeIn(d18), run_time=0.8)
        self.at(4)
        self.play(FadeIn(habits[2], shift=UP * 0.1), run_time=0.6)
        self.hold()

        sp = SurroundingRectangle(fa[6], buff=0.05, color=NOTE, stroke_width=2.5)
        sp_t = T("a moved space", 24, NOTE).next_to(files, RIGHT, buff=0.5).align_to(fa[6], UP)
        flaw = VGroup(T("no sense of proportion:", 26, GREY_A),
                      T("a moved space fails as loudly as a lost question mark", 26, NOTE)).arrange(DOWN, buff=0.12)
        flaw2 = T("a formatting change fails every golden file you have, as KotlinPoet 2.4.0 did with annotation arrays", 22, GREY_A)
        flg = VGroup(flaw, flaw2).arrange(DOWN, buff=0.22).move_to([0, -2.3, 0])
        fit(flg, 12.6)
        self.say("proof")
        self.play(FadeOut(habits), run_time=0.4)
        self.play(FadeIn(flaw[0]), run_time=0.5)
        self.at(1)
        self.play(fa[6].animate.shift(RIGHT * 0.12), Create(sp), FadeIn(sp_t), FadeIn(flaw[1]), run_time=0.8)
        self.at(2)
        self.play(FadeIn(flaw2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        pc1 = VGroup(T("the golden file", 26, GOLD), T("catches any change", 24, GREY_A)).arrange(DOWN, buff=0.1)
        pc2 = VGroup(T("a call", 26, NOTE), T("says whether it matters", 24, GREY_A)).arrange(DOWN, buff=0.1)
        for p in (pc1, pc2):
            p.add_to_back(RoundedRectangle(corner_radius=0.12, width=4.6, height=1.3).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.06), 1).move_to(p))
        plus = T("+", 40, WHITE)
        pg = VGroup(pc1, plus, pc2).arrange(RIGHT, buff=0.4).move_to([0, -2.3, 0])
        self.say("pair")
        self.play(FadeOut(flg), run_time=0.4)
        self.at(1)
        self.play(FadeIn(pc1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(plus), FadeIn(pc2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        rc = rule_card("A test that only compiles proves the processor didn't crash.\nCall the code it wrote.", NOTE, 32)
        self.say("rule")
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.9)
        self.hold(after=0.5)
        self.play(FadeOut(rc), run_time=0.5)

        # ================= the four checks in code =================
        kh2 = T("Kotlin: the four checks in one test (1 exit code, 2 text, 3 messages, 4 a call)", 22, HELPER)
        kc2 = code_block(["val run = bench.run(lamp, processors = listOf(BuilderProcessorProvider()))",
                          "assertThat(run.exitCode).isEqualTo(\"OK\")                          // 1",
                          "assertMatchesGolden(run.generated(\"movemate/LampBuilder.kt\"),    // 2",
                          "    goldenDir.resolve(\"LampBuilder.kt.golden\"))",
                          "assertThat(run.messages).isEmpty()                                // 3",
                          "val builder = run.newInstance(\"movemate.LampBuilder\")             // 4",
                          "run.call(builder, \"name\", \"desk lamp\")",
                          "run.call(builder, \"bulbs\", 1)",
                          "run.call(builder, \"shade\", null)",
                          "assertThat(run.call(builder, \"build\").toString())",
                          "    .isEqualTo(\"Lamp(name=desk lamp, bulbs=1, shade=null)\")"], 22, buff=0.13,
                         hl={"// 1": GREY_B, "// 2": GREY_B, "// 3": GREY_B, "// 4": GREY_B, "null": NOTE})
        kg = VGroup(kh2, kc2).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 0.2, 0])
        fit(kg, 12.6)
        self.say("code")
        self.play(FadeIn(kh2), FadeIn(kc2[0]), run_time=0.6)
        self.at_text("the exit code", lead=0.2)
        self.play(FadeIn(kc2[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("the text against", lead=0.2)
        self.play(FadeIn(kc2[2:4], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("no messages", lead=0.2)
        self.play(FadeIn(kc2[4], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("and a call", lead=0.2)
        self.play(FadeIn(kc2[5:], shift=RIGHT * 0.1), run_time=0.7)
        self.play(Circumscribe(kc2[8], color=NOTE, buff=0.06), run_time=0.9)
        self.hold()

        jh2 = T("Closest Java equivalent: Google's compile-testing and Truth", 22, GREY_A)
        jc2 = code_block(["Compilation compilation =",
                          "        javac().withProcessors(new BuilderProcessor()).compile(lamp);",
                          "assertThat(compilation).succeededWithoutWarnings();                 // 1 and 3",
                          "assertThat(compilation).generatedSourceFile(\"movemate.LampBuilder\") // 2",
                          "        .hasSourceEquivalentTo(",
                          "                JavaFileObjects.forResource(\"golden/LampBuilder.java\"));",
                          "// 4: compile-testing's checks stop at the compile; call the generated",
                          "//    builder from a test in a module whose own build runs the processor"], 22, buff=0.13,
                         hl={"// 1 and 3": GREY_B, "// 2": GREY_B})
        jc2[6].set_color(GREY_B)
        jc2[7].set_color(GREY_B)
        jg = VGroup(jh2, jc2).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 0.2, 0])
        fit(jg, 12.6)
        self.say("code_j")
        self.play(FadeOut(kg), run_time=0.5)
        self.play(FadeIn(jh2), FadeIn(jc2[:2]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(jc2[2:6], shift=RIGHT * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(jc2[6:], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral, the room's limit, and a check =================
        mq = T("Does a green test mean a working processor? Only if it calls the code.", 30)
        m1 = T("The glance and the skim: the helper finished.", 28, GREY_A)
        m2 = T("The proofreader: the card changed.", 28, GOLD)
        m3 = T("The try out: the lamp still works.", 28, NOTE)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.28).move_to(UP * 1.9)
        fit(mg, 12.6)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        lim = VGroup(T("The practice room is fresh every time:", 26, GREY_A),
                     T("lesson 7's wrong Dependencies pass every test. They need a real build.", 26, BAD)).arrange(DOWN, buff=0.12)
        lim.move_to(DOWN * 0.55)
        fit(lim, 12.6)
        self.say("room2")
        self.play(FadeIn(lim[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lim[1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, NOTE), T("fix it with", 28), M("copy()", 26, NOTE), T("so the question marks stay.", 28)).arrange(RIGHT, buff=0.15)
        qb = T("What do the four checks say now?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to(DOWN * 0.75)
        fit(qg2, 12.6)
        self.say("check")
        self.play(FadeOut(lim), run_time=0.4)
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.35), edge=RIGHT)
        ans = VGroup(VGroup(T("exit code OK, the class is there, the golden file says", 26, OK), M("Matches", 24, OK)).arrange(RIGHT, buff=0.15),
                     VGroup(M("shade(null)", 24, OK), T("works: all four pass", 26, OK)).arrange(RIGHT, buff=0.15)).arrange(DOWN, buff=0.15)
        ans.move_to(DOWN * 2.3)
        fit(ans, 12.6)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
